import inspect
import json
import logging
import os
import sys
from typing import Any
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes

# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            '..', 'src')))

uns_mqtt_folder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            '..', '..', '02_mqtt-cluster', 'src')))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

if uns_mqtt_folder not in sys.path:
    sys.path.insert(1, uns_mqtt_folder)

from uns_mqtt.mqtt_listener import Uns_MQTT_ClientWrapper
from uns_sparkplugb.generated import sparkplug_b_pb2

LOGGER = logging.getLogger(__name__)


class Spb2UNSPublisher:
    """
        Class to parse the metric array extracted from the SPB payload and published to the respective UNS topics
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
    isMQTTv5: bool = False
    # stores the topic aliases to be used if the protocol is MQTTv5
    topic_alias: dict[str, str] = {}
    # the Mqtt client used to publish the messages
    mqtt_client: Uns_MQTT_ClientWrapper = None
    # maximum topic alias
    max_topic_alias: int = 0

    def __init__(self, mqtt_client: Uns_MQTT_ClientWrapper):
        self.mqtt_client = mqtt_client
        self.isMQTTv5 = mqtt_client.protocol == Uns_MQTT_ClientWrapper.MQTTv5

    def clearMetricAlias(self):
        """
            Clear all metric aliases stored.
            Typically called if a node rebirth / death message is received.
        """
        self.metric_name_alias_map.clear()

    def transformSpbAndPublishToUNS(self,
                                    spBPayload,
                                    group_id: str,
                                    message_type: str,
                                    edge_node_id: str,
                                    device_id: str = None) -> dict:
        all_uns_messages: dict = {}
        match message_type:
            case "NBIRTH":  # Birth certificate for MQTT EoN nodes.
                LOGGER.debug(f"Received message type : {message_type}")
                # payload = self.getPayload(spBPayload)
                # reset all metric aliases on node birth
                self.clearMetricAlias()
                all_uns_messages = self.handleSpbMsgs(spBPayload=spBPayload,
                                                      group_id=group_id,
                                                      message_type=message_type,
                                                      edge_node_id=edge_node_id,
                                                      device_id=device_id)

            case "NDEATH":  # Death certificate for MQTT EoN nodes.
                LOGGER.debug(f"Received message type : {message_type}")
                # reset all metric aliases on node death
                self.clearMetricAlias()
                all_uns_messages = self.handleSpbMsgs(spBPayload=spBPayload,
                                                      group_id=group_id,
                                                      message_type=message_type,
                                                      edge_node_id=edge_node_id,
                                                      device_id=device_id)

            case "DBIRTH":  # Birth certificate for Devices.
                LOGGER.debug(f"Received message type : {message_type}")
                # at device birth and death there are no metrics published

            case "DDEATH":  # Death certificate for Devices.
                LOGGER.debug(f"Received message type : {message_type}")
                # at device birth and death there are no metrics published

            case "NDATA":  # Node data message.
                all_uns_messages = self.handleSpbMsgs(spBPayload=spBPayload,
                                                      group_id=group_id,
                                                      message_type=message_type,
                                                      edge_node_id=edge_node_id,
                                                      device_id=device_id)

            case "DDATA":  # Device data message.
                all_uns_messages = self.handleSpbMsgs(spBPayload=spBPayload,
                                                      group_id=group_id,
                                                      message_type=message_type,
                                                      edge_node_id=edge_node_id,
                                                      device_id=device_id)

            case "NCMD":  # Node command message.
                all_uns_messages = self.handleSpbMsgs(spBPayload=spBPayload,
                                                      group_id=group_id,
                                                      message_type=message_type,
                                                      edge_node_id=edge_node_id,
                                                      device_id=device_id)

            case "DCMD":  # device command message.
                all_uns_messages = self.handleSpbMsgs(spBPayload=spBPayload,
                                                      group_id=group_id,
                                                      message_type=message_type,
                                                      edge_node_id=edge_node_id,
                                                      device_id=device_id)

            case "STATE":  # Critical application state message.
                LOGGER.info(f"Received message type : {message_type}")

            case _:
                LOGGER.error(f"Unknown message_type received: {message_type}")
                raise ValueError(f"Unknown message_type received: {message_type}")
        if (len(all_uns_messages) > 0):
            self.publishToUNS(all_uns_messages)

    def handleSpbMsgs(self,
                      spBPayload,
                      group_id: str,
                      message_type: str,
                      edge_node_id: str,
                      device_id: str = None) -> dict:
        """
            Parse the SPBPayload for message types
        """
        # convert spb payload and extract metrics array
        metrics_list: list = self.getMetricsListFromPayload(spBPayload)

        # collate all metrics to the same topic and send them as one payload
        all_uns_messages: dict = {}
        spbContext = self.getSpbContext(group_id, message_type,
                                        edge_node_id, device_id)
        for metric in metrics_list:
            name = self.getMetricName(metric)
            name_list = name.rsplit("/", 1)
            uns_topic = name_list[0]
            tag_name = name_list[1]

            metric_timestamp: float = float(getattr(metric, Spb2UNSPublisher.SPB_TIMESTAMP))
            datatype: int = getattr(metric, Spb2UNSPublisher.SPB_DATATYPE)

            isHistorical: bool = getattr(metric, Spb2UNSPublisher.SPB_IS_HISTORICAL, False)
            metric_value = None
            if (not getattr(metric, Spb2UNSPublisher.SPB_IS_NULL)):
                metric_value = getattr(metric, Spb2UNSPublisher.SPB_DATATYPE_KEYS.get(datatype))

            uns_message: dict[str, Any] = Spb2UNSPublisher.extractUNSMessageForTopic(
                parsed_message=all_uns_messages.get(uns_topic),
                tag_name=tag_name,
                metric_value=metric_value,
                metric_timestamp=metric_timestamp,
                isHistorical=isHistorical,
                spbContext=spbContext)

            all_uns_messages[uns_topic] = uns_message
        # Publish all messages to the respective UNS topics

        return all_uns_messages

    def getMetricName(self, metric):
        """
        Extract metric name from metric payload
        Encapsulate metric name alias handling
        """
        name: str = getattr(metric, Spb2UNSPublisher.SPB_NAME, None)
        try:
            metric_alias: int = int(getattr(metric, Spb2UNSPublisher.SPB_ALIAS))
        except (AttributeError, TypeError, ValueError):
            metric_alias = None

        if (name is None or name == ""):
            if (metric_alias is not None):
                name = self.metric_name_alias_map.get(metric_alias)
            if (name is None or name == ""):
                LOGGER.error(
                    f"Skipping as metric Name is null and alias not yet provided: {metric}"
                )
        elif (metric_alias is not None):
            # if metric_alias was provided then store it in the map
            self.metric_name_alias_map[metric_alias] = name
        return name

    @staticmethod
    def getSpbContext(group_id: str, message_type: str, edge_node_id: str,
                      device_id: str) -> dict[str, str]:
        """
            returns a dict of key value pair of the SPB parsed topic
        """
        spbContext = {
            "spBv1.0_group_id": group_id,
            "spBv1.0_message_type": message_type,
            "spBv1.0_edge_node_id": edge_node_id
        }
        if (device_id is not None):
            spbContext["spBv1.0_device_id"] = device_id
        return spbContext

    @staticmethod
    def getMetricsListFromPayload(payload) -> list:
        """
        Extracts metrics list  from the SparkplugB payload
        """
        inboundPayload = sparkplug_b_pb2.Payload()
        inboundPayload.ParseFromString(payload)
        return inboundPayload.metrics

    @staticmethod
    def getPayload(payload) -> dict:
        """
        Converts SparkplugB payload to a dict
        """
        inboundPayload = sparkplug_b_pb2.Payload()
        inboundPayload.ParseFromString(payload)
        return inboundPayload

    @staticmethod
    def extractUNSMessageForTopic(
            parsed_message: dict,
            tag_name: str,
            metric_value: Any,
            metric_timestamp: float,
            isHistorical: bool = False,
            spbContext: dict[str, str] = None) -> dict[str, Any]:
        """
        Returns a dictionary where the key is the target topic name and value is the message payload in dict format
        """
        # check if there were any tags  already parsed for this uns topic
        if (parsed_message is None):
            parsed_message = {
                tag_name: (metric_value, metric_timestamp, isHistorical)
            }
            parsed_message[Spb2UNSPublisher.SPB_TIMESTAMP] = metric_timestamp
            # enrich the message to add SpB related information
            if (spbContext is not None):
                parsed_message.update(spbContext)
        else:
            # check if there were there was any already parsed metric for this tag and UNS topic
            old_metric_tuple_list = parsed_message.get(tag_name)
            old_metric_timestamp = parsed_message.get(Spb2UNSPublisher.SPB_TIMESTAMP)
            if (not isinstance(old_metric_tuple_list, list)):
                # replace current metric value with array of values if it is a singe value
                old_metric_tuple_list = [old_metric_tuple_list]

            # If the value for the metric name already exists then we will have a list of tuples
            if (old_metric_timestamp > metric_timestamp):
                # if the metric in the uns_message is newer than the metric received add the new value at the end
                # TODO currently for simplicity have not yet ordered all old values, just the newest is at 0
                # TODO storing value, timestamp and isHistorical flag as a tuple.
                # If needed might need to convert this into a dict to have attribute keys for identification
                old_metric_tuple_list.append(
                    (metric_value, metric_timestamp, isHistorical))
            else:
                # if the metric in the uns_message is older than the metric received
                old_metric_tuple_list.insert(
                    0, (metric_value, metric_timestamp, isHistorical))
                parsed_message[Spb2UNSPublisher.SPB_TIMESTAMP] = metric_timestamp
            parsed_message[tag_name] = old_metric_tuple_list
            # end of inner if & else
        # end of outer if
        return parsed_message

    def publishToUNS(self, all_uns_messages: dict):
        if (self.mqtt_client.is_connected()):
            for topic in all_uns_messages:
                message = all_uns_messages.get(topic)
                publish_properties = None
                if (self.isMQTTv5):
                    publish_properties = Properties(PacketTypes.PUBLISH)

                self.mqtt_client.publish(topic=topic, payload=json.dumps(message), qos=self.mqtt_client.qos,
                                         retain=True, properties=publish_properties)
        else:
            LOGGER.error(f"MQTT Client is not connected. Cannot publish to UNS. {self.mqtt_client}")
            raise ConnectionError(f"{self.mqtt_client}")
