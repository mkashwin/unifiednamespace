"""
Publish messages received on the spbV1.0 name space to the UNS
after correctly decoding the protobuf payloads
"""
import json
import logging
from typing import Any

from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
from uns_mqtt.mqtt_listener import UnsMQTTClient
from uns_sparkplugb.generated import sparkplug_b_pb2

LOGGER = logging.getLogger(__name__)


class Spb2UNSPublisher:
    """
    Class to parse the metric array extracted from the SPB payload and
    published to the respective UNS topics.
    Create only one instance of this class per uns_sparkplugb_listener
    This is a stateful class and stores the mappings of the alias to topic (if MQTTv5 is used)
    This also temporarily stores the mapping of SparkPlugB Metric aliases
    """

    SPB_NAME: str = "name"
    SPB_ALIAS: str = "alias"
    SPB_TIMESTAMP: str = "timestamp"
    SPB_DATATYPE: str = "datatype"
    SPB_IS_NULL = "is_null"
    SPB_IS_HISTORICAL = "is_historical"

    # TODO currently not yet handled correctly. need to figure how to handle this
    SPB_METADATA = "metadata"
    SPB_PROPERTIES = "properties"

    SPB_DATATYPE_KEYS = {
        sparkplug_b_pb2.Unknown: "Unknown",
        sparkplug_b_pb2.Int8: "int_value",
        sparkplug_b_pb2.Int16: "int_value",
        sparkplug_b_pb2.Int32: "int_value",
        sparkplug_b_pb2.UInt8: "int_value",
        sparkplug_b_pb2.UInt16: "int_value",
        sparkplug_b_pb2.UInt32: "int_value",
        sparkplug_b_pb2.Int64: "long_value",
        sparkplug_b_pb2.UInt64: "long_value",
        sparkplug_b_pb2.DateTime: "long_value",
        sparkplug_b_pb2.Float: "float_value",
        sparkplug_b_pb2.Double: "double_value",
        sparkplug_b_pb2.String: "string_value",
        sparkplug_b_pb2.Text: "string_value",
        sparkplug_b_pb2.UUID: "string_value",
        sparkplug_b_pb2.DataSet: "dataset_value",
        sparkplug_b_pb2.Bytes: "bytes_value",
        sparkplug_b_pb2.File: "bytes_value",
        sparkplug_b_pb2.Boolean: "boolean_value",
        sparkplug_b_pb2.Template: "template_value",
    }

    # stores the message aliases as uses in the SparkPlugB message payload
    metric_name_alias_map: dict[int, str] = {}
    # Flag indicating this an MQTTv5 connection
    is_mqtt_v5: bool = False
    # stores the topic aliases to be used if the protocol is MQTTv5
    topic_alias: dict[str, str] = {}
    # the Mqtt client used to publish the messages
    mqtt_client: UnsMQTTClient = None
    # maximum topic alias
    max_topic_alias: int = 0

    def __init__(self, mqtt_client: UnsMQTTClient):
        self.mqtt_client = mqtt_client
        self.is_mqtt_v5 = mqtt_client.protocol == UnsMQTTClient.MQTTv5

    def clear_metric_alias(self):
        """
        Clear all metric aliases stored.
        Typically called if a node rebirth / death message is received.
        """
        self.metric_name_alias_map.clear()

    def transform_spb_and_publish_to_uns(
        self,
        spb_payload,
        group_id: str,
        message_type: str,
        edge_node_id: str,
        device_id: str = None,
    ) -> dict:
        # pylint: disable=too-many-arguments
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

        Currently not supporting
        - DDEATH : no metrics published at device death
        - NDEATH: no metrics published at node death
        - STATE:  no metrics published with STATE message
        """
        all_uns_messages: dict = {}
        match message_type:
            case "NBIRTH":  # Birth certificate for MQTT EoN nodes.
                LOGGER.debug("Received message type : %s", str(message_type))
                # payload = self.getPayload(spBPayload)
                # reset all metric aliases on node birth
                self.clear_metric_alias()
                all_uns_messages = self.handle_spb_messages(
                    spb_payload=spb_payload,
                    group_id=group_id,
                    message_type=message_type,
                    edge_node_id=edge_node_id,
                    device_id=device_id,
                )

            case "NDEATH":  # Death certificate for MQTT EoN nodes.
                LOGGER.debug("Received message type : %s", str(message_type))
                # reset all metric aliases on node death
                self.clear_metric_alias()
                all_uns_messages = self.handle_spb_messages(
                    spb_payload=spb_payload,
                    group_id=group_id,
                    message_type=message_type,
                    edge_node_id=edge_node_id,
                    device_id=device_id,
                )

            case "DBIRTH":  # Birth certificate for Devices.
                LOGGER.debug("Received message type : %s", str(message_type))
                # at device birth and death there are no metrics published

            case "DDEATH":  # Death certificate for Devices.
                LOGGER.debug("Received message type : %s", str(message_type))
                # at device birth and death there are no metrics published

            case "NDATA":  # Node data message.
                all_uns_messages = self.handle_spb_messages(
                    spb_payload=spb_payload,
                    group_id=group_id,
                    message_type=message_type,
                    edge_node_id=edge_node_id,
                    device_id=device_id,
                )

            case "DDATA":  # Device data message.
                all_uns_messages = self.handle_spb_messages(
                    spb_payload=spb_payload,
                    group_id=group_id,
                    message_type=message_type,
                    edge_node_id=edge_node_id,
                    device_id=device_id,
                )

            case "NCMD":  # Node command message.
                all_uns_messages = self.handle_spb_messages(
                    spb_payload=spb_payload,
                    group_id=group_id,
                    message_type=message_type,
                    edge_node_id=edge_node_id,
                    device_id=device_id,
                )

            case "DCMD":  # device command message.
                all_uns_messages = self.handle_spb_messages(
                    spb_payload=spb_payload,
                    group_id=group_id,
                    message_type=message_type,
                    edge_node_id=edge_node_id,
                    device_id=device_id,
                )

            case "STATE":  # Critical application state message.
                LOGGER.info("Received message type : %s", str(message_type))

            case _:
                LOGGER.error("Unknown message_type received: %s",
                             str(message_type))
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
        device_id: str = None,
    ) -> dict:
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
        """
        Parse the SPBPayload for message types
        """
        # convert spb payload and extract metrics array
        metrics_list: list = self.get_metrics_from_payload(spb_payload)

        # collate all metrics to the same topic and send them as one payload
        all_uns_messages: dict = {}
        spb_context = self.get_spb_context(group_id, message_type,
                                           edge_node_id, device_id)
        for metric in metrics_list:
            name = self.get_metric_name(metric)
            name_list = name.rsplit("/", 1)
            uns_topic = name_list[0]
            tag_name = name_list[1]

            metric_timestamp: float = float(
                getattr(metric, Spb2UNSPublisher.SPB_TIMESTAMP))
            datatype: int = getattr(metric, Spb2UNSPublisher.SPB_DATATYPE)

            is_historical: bool = getattr(metric,
                                          Spb2UNSPublisher.SPB_IS_HISTORICAL,
                                          False)
            metric_value = None
            if not getattr(metric, Spb2UNSPublisher.SPB_IS_NULL):
                metric_value = getattr(
                    metric, Spb2UNSPublisher.SPB_DATATYPE_KEYS.get(datatype))

            uns_message: dict[
                str, Any] = Spb2UNSPublisher.extract_uns_message_for_topic(
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

    def get_metric_name(self, metric):
        """
        Extract metric name from metric payload
        Encapsulate metric name alias handling
        """
        name: str = getattr(metric, Spb2UNSPublisher.SPB_NAME, None)
        try:
            metric_alias: int = int(getattr(metric,
                                            Spb2UNSPublisher.SPB_ALIAS))
        except (AttributeError, TypeError, ValueError):
            metric_alias = None

        if name is None or name == "":
            if metric_alias is not None:
                name = self.metric_name_alias_map.get(metric_alias)
            if name is None or name == "":
                LOGGER.error(
                    "Skipping as metric Name is null and alias not yet provided: %s",
                    str(metric))
        elif metric_alias is not None:
            # if metric_alias was provided then store it in the map
            self.metric_name_alias_map[metric_alias] = name
        return name

    @staticmethod
    def get_spb_context(group_id: str, message_type: str, edge_node_id: str,
                        device_id: str) -> dict[str, str]:
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
    def get_payload(payload: sparkplug_b_pb2.Payload) -> dict:
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
        spb_context: dict[str, str] = None,
    ) -> dict[str, Any]:
        # pylint: disable=too-many-arguments
        """
        Returns a dictionary where the key is the target topic name and value is the
        message payload in dict format
        """
        # check if there were any tags  already parsed for this uns topic
        if parsed_message is None:
            parsed_message = {
                tag_name: (metric_value, metric_timestamp, is_historical)
            }
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
                # replace current metric value with array of values if it is a singe value
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
                parsed_message[
                    Spb2UNSPublisher.SPB_TIMESTAMP] = metric_timestamp
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
            LOGGER.error(
                "MQTT Client is not connected. Cannot publish to UNS: %s",
                str(self.mqtt_client))
            raise ConnectionError(f"{self.mqtt_client}")
