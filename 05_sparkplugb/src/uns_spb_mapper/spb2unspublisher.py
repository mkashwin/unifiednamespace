"""*******************************************************************************
* Copyright (c) 2021 Ashwin Krishnan
*
* All rights reserved. This program and the accompanying materials
* are made available under the terms of MIT and  is provided "as is",
* without warranty of any kind, express or implied, including but
* not limited to the warranties of merchantability, fitness for a
* particular purpose and noninfringement. In no event shall the
* authors, contributors or copyright holders be liable for any claim,
* damages or other liability, whether in an action of contract,
* tort or otherwise, arising from, out of or in connection with the software
* or the use or other dealings in the software.
*
* Contributors:
*    -
*******************************************************************************

Publish messages received on the spbV1.0 name space to the UNS
after correctly decoding the protobuf payloads
"""

import json
import logging
from typing import Any, Final

from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
from uns_mqtt.mqtt_listener import MQTTVersion, UnsMQTTClient
from uns_sparkplugb.generated import sparkplug_b_pb2
from uns_sparkplugb.uns_spb_enums import SPBMetricDataTypes

LOGGER = logging.getLogger(__name__)


class Spb2UNSPublisher:
    """
    Class to parse the metric array extracted from the SPB payload and
    published to the respective UNS topics.
    Create only one instance of this class per uns_sparkplugb_listener
    This is a stateful class and stores the mappings of the alias to topic (if MQTTv5 is used)
    This also temporarily stores the mapping of SparkPlugB Metric aliases
    """

    SPB_NAME: Final[str] = "name"
    SPB_ALIAS: Final[str] = "alias"
    SPB_TIMESTAMP: Final[str] = "timestamp"
    SPB_DATATYPE: Final[str] = "datatype"
    SPB_IS_NULL: Final[str] = "is_null"
    SPB_IS_HISTORICAL: Final[str] = "is_historical"
    SPB_METADATA: Final[str] = "metadata"
    SPB_PROPERTIES: Final[str] = "properties"

    def __init__(self, mqtt_client: UnsMQTTClient):
        # stores the message aliases as uses in the SparkPlugB message payload
        # NBIRTH and DBIRTH messages MUST include both a metric name and alias.
        # NDATA, DDATA, NCMD, and DCMD messages MUST only include an alias and the metric name MUST be excluded
        # alias_map needs to be maintained per node and per device, to be cleared on DDEATH & NDEATH for a specific group_id
        # dict[<group_id_node_id_device_id>,dict[<alias>, <metric name>] ]
        self.node_device_metric_alias_map: dict[str, dict[int, str]] = {}

        # stores the topic aliases to be used if the protocol is MQTTv5
        self.topic_alias: dict[str, str] = {}

        # the Mqtt client used to publish the messages
        self.mqtt_client = mqtt_client

        # Flag indicating this an MQTTv5 connection
        self.is_mqtt_v5 = mqtt_client.protocol == MQTTVersion.MQTTv5

    def clear_metric_alias(self, cache_key: str):
        """
        Clear all metric aliases stored for the provided cache key
        Typically called if a node or device rebirth / death message is received.
        cache_key: created from the sparkplug topic "<edge_node_id>/<device_id>"
        """
        cache = self.node_device_metric_alias_map.pop(
            cache_key, None)  # metric_name_alias_map
        LOGGER.debug(
            f"Clears alias cache for key: {cache_key}. Cache value: {cache}")

    def get_name_for_alias(self, cache_key: str, alias: int):
        if cache_key not in self.node_device_metric_alias_map:
            LOGGER.error(
                f"Trying to get an alias for a cache which has not been set:{cache_key}")
            return None
        return self.node_device_metric_alias_map[cache_key][alias]

    def save_name_for_alias(self, cache_key: str, name: str, alias: int):
        if cache_key not in self.node_device_metric_alias_map:
            # create the cache
            self.node_device_metric_alias_map[cache_key] = {}
        self.node_device_metric_alias_map[cache_key][alias] = name

    def transform_spb_and_publish_to_uns(
        self,
        spb_payload,
        group_id: str,
        message_type: str,
        edge_node_id: str,
        device_id: str | None = None,
    ) -> dict:
        """
        Parses the SPB payload and depending on message type
        will appropriately publish the message to the UNS

        Message types supported
        - NBIRTH
        - DBIRTH
        - NDATA
        - DDATA
        - NCMD
        - DCMD
        - NDEATH

        Currently not supporting
        - DDEATH : no metrics published at device death
        - STATE:  no metrics published with STATE message
        """
        all_uns_messages: dict = {}
        metric_alias_cache_key: str = group_id + "/" + edge_node_id + \
            "/" + str(device_id)  # as device_id may be None
        match message_type:
            case "NBIRTH" | "NDEATH" | "DBIRTH":
                LOGGER.debug("Received message type : %s", message_type)
                # reset all metric aliases on node birth
                self.clear_metric_alias(metric_alias_cache_key)

                all_uns_messages = self.handle_spb_messages(
                    spb_payload=spb_payload,
                    group_id=group_id,
                    message_type=message_type,
                    edge_node_id=edge_node_id,
                    device_id=device_id,
                )

            case "DDEATH":  # Death certificate for Devices.
                # clear any alias cache
                self.clear_metric_alias(metric_alias_cache_key)

                LOGGER.debug("Received message type : %s", message_type)
                # at device death there are no metrics published

            case "NDATA" | "NCMD" | "DDATA" | "DCMD":  # Node data message.
                all_uns_messages = self.handle_spb_messages(
                    spb_payload=spb_payload,
                    group_id=group_id,
                    message_type=message_type,
                    edge_node_id=edge_node_id,
                    device_id=device_id,
                )

            case "STATE":  # Critical application state message.
                LOGGER.info("Received message type : %s", message_type)

            case _:
                LOGGER.error("Unknown message_type received: %s",
                             message_type)
                raise ValueError(
                    f"Unknown message_type received: {message_type}")
        if len(all_uns_messages) > 0:
            self.publish_to_uns(all_uns_messages)

    def handle_spb_messages(
        self,
        spb_payload,
        group_id: str,
        message_type: str,
        edge_node_id: str,
        device_id: str | None = None,
    ) -> dict:
        """
        Parse the SPBPayload for message types
        """
        # convert spb payload and extract metrics array
        metrics_list: list = self.get_metrics_from_payload(payload=spb_payload)
        metric_alias_cache_key: str = group_id + "/" + edge_node_id + \
            "/" + str(device_id)  # as device_id may be None

        # collate all metrics to the same topic and send them as one payload
        all_uns_messages: dict = {}
        spb_context = self.get_spb_context(
            group_id, message_type, edge_node_id, device_id)
        for metric in metrics_list:
            name = self.get_metric_name(
                cache_key=metric_alias_cache_key, metric=metric)
            name_list = name.rsplit("/", 1)
            uns_topic = name_list[0]
            tag_name = name_list[1]

            metric_timestamp: float = float(
                getattr(metric, Spb2UNSPublisher.SPB_TIMESTAMP))
            datatype: int = getattr(metric, Spb2UNSPublisher.SPB_DATATYPE)

            is_historical: bool = getattr(
                metric, Spb2UNSPublisher.SPB_IS_HISTORICAL, False)
            metric_value = None
            if not getattr(metric, Spb2UNSPublisher.SPB_IS_NULL):
                metric_value = SPBMetricDataTypes(
                    datatype).get_value_from_sparkplug(metric)

            uns_message: dict[str, Any] = Spb2UNSPublisher.extract_uns_message_for_topic(
                parsed_message=all_uns_messages.get(uns_topic),
                tag_name=tag_name,
                metric_value=metric_value,
                metric_timestamp=metric_timestamp,
                is_historical=is_historical,
                spb_context=spb_context,
            )

            all_uns_messages[uns_topic] = uns_message
        # Publish all messages to the respective UNS topics

        return all_uns_messages

    def get_metric_name(self, cache_key, metric):
        """
        Extract metric name from metric payload
        Encapsulate metric name alias handling
        """
        metric_name: str | None = getattr(
            metric, Spb2UNSPublisher.SPB_NAME, None)
        try:
            metric_alias: int = int(
                getattr(metric, Spb2UNSPublisher.SPB_ALIAS))
        except (AttributeError, TypeError, ValueError):
            metric_alias = None

        if metric_name is None or metric_name == "":
            if metric_alias is not None:
                metric_name = self.get_name_for_alias(cache_key, metric_alias)
            if metric_name is None or metric_name == "":
                LOGGER.error(
                    "Skipping as metric Name is null and alias not yet provided: %s", metric)
        elif metric_alias is not None:
            # if metric_alias was provided then store it in the map
            self.save_name_for_alias(
                cache_key=cache_key, name=metric_name, alias=metric_alias)

        return metric_name

    @staticmethod
    def get_spb_context(group_id: str, message_type: str, edge_node_id: str, device_id: str) -> dict[str, str]:
        """
        Returns a dict of key value pair of the SPB parsed topic
        """
        spb_context = {
            "spBv1.0_group_id": group_id,
            "spBv1.0_message_type": message_type,
            "spBv1.0_edge_node_id": edge_node_id,
        }
        if device_id is not None:
            spb_context["spBv1.0_device_id"] = device_id
        return spb_context

    @staticmethod
    def get_metrics_from_payload(payload: sparkplug_b_pb2.Payload) -> list:
        """
        Extracts metrics list  from the SparkplugB payload
        """
        return Spb2UNSPublisher.get_payload(payload).metrics

    @staticmethod
    def get_payload(payload: sparkplug_b_pb2.Payload) -> sparkplug_b_pb2.Payload:
        """
        Converts SparkplugB payload to a dict
        """
        inbound_payload = sparkplug_b_pb2.Payload()
        inbound_payload.ParseFromString(payload)
        return inbound_payload

    @staticmethod
    def extract_uns_message_for_topic(
        parsed_message: dict,
        tag_name: str,
        metric_value: Any,
        metric_timestamp: float,
        is_historical: bool = False,
        spb_context: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Returns a dictionary where the key is the target topic name and value is the
        message payload in dict format
        """
        # check if there were any tags  already parsed for this uns topic
        if parsed_message is None:
            parsed_message = {tag_name: (
                metric_value, metric_timestamp, is_historical)}
            parsed_message[Spb2UNSPublisher.SPB_TIMESTAMP] = metric_timestamp
            # enrich the message to add SpB related information
            if spb_context is not None:
                parsed_message.update(spb_context)
        else:
            # check if there were there was any already parsed metric for this tag and UNS topic
            old_metric_tuple_list = parsed_message.get(tag_name)
            old_metric_timestamp = parsed_message.get(
                Spb2UNSPublisher.SPB_TIMESTAMP)
            if not isinstance(old_metric_tuple_list, list):
                # replace current metric value with array of values if it is a single value
                old_metric_tuple_list = [old_metric_tuple_list]

            # If the value for the metric name already exists then we will have a list of tuples
            if old_metric_timestamp > metric_timestamp:
                # if the metric in the uns_message is newer than the metric received
                # add the new value at the end

                # TODO currently for simplicity have not yet ordered all old values,
                # just the newest is at 0

                # TODO storing value, timestamp and isHistorical flag as a tuple.

                # If needed might need to convert this into a dict to have attribute keys
                # for identification
                old_metric_tuple_list.append(
                    (metric_value, metric_timestamp, is_historical))
            else:
                # if the metric in the uns_message is older than the metric received
                old_metric_tuple_list.insert(
                    0, (metric_value, metric_timestamp, is_historical))
                parsed_message[Spb2UNSPublisher.SPB_TIMESTAMP] = metric_timestamp
            parsed_message[tag_name] = old_metric_tuple_list
            # end of inner if & else
        # end of outer if
        return parsed_message

    def publish_to_uns(self, all_uns_messages: dict):
        """
        Publishes all the messages based on the metric name to the appropriate UNS topic
        """
        if self.mqtt_client.is_connected():
            for topic in all_uns_messages:
                message = all_uns_messages.get(topic)
                publish_properties = None
                if self.is_mqtt_v5:
                    publish_properties = Properties(PacketTypes.PUBLISH)

                self.mqtt_client.publish(
                    topic=topic,
                    payload=json.dumps(message),
                    qos=self.mqtt_client.qos,
                    retain=True,
                    properties=publish_properties,
                )
        else:
            LOGGER.error("MQTT Client is not connected. Cannot publish to UNS: %s",
                         self.mqtt_client)
            raise ConnectionError(f"{self.mqtt_client}")
