import inspect
import logging
import os
import sys
from typing import Dict
from uns_sparkplugb.generated import sparkplug_b_pb2

# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            '..', '..', '02_mqtt-cluster', 'src')))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

from mqtt_listener import Uns_MQTT_ClientWrapper

LOGGER = logging.getLogger(__name__)

SPB_NAME: str = "name"
SPB_ALIAS: str = "alias"
SPB_TIMESTAMP: str = "timestamp"
SPB_DATATYPE: str = "datatype"
SPB_IS_NULL = "is_null"

# TODO currently not yet handled correctly. need to figure how to handle this

SPB_IS_HISTORICAL = "is_historical"
SPB_METADATA = "metadata"
SPB_PROPERTIES = "properties"

SPB_DATATYPE_KEYS: Dict(int, str) = {
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
    sparkplug_b_pb2.Bytes: "bytes_value",
    sparkplug_b_pb2.File: "bytes_value",
    sparkplug_b_pb2.Boolean: "boolean_value",
    sparkplug_b_pb2.Template: "template_value",
    # sparkplug_b_pb2.PropertySet
    # sparkplug_b_pb2.PropertySetList
    # sparkplug_b_pb2.Int8Array
    # sparkplug_b_pb2.Int16Array
    # sparkplug_b_pb2.Int32Array
    # sparkplug_b_pb2.Int64Array
    # sparkplug_b_pb2.UInt8Array
    # sparkplug_b_pb2.UInt16Array
    # sparkplug_b_pb2.UInt32Array
    # sparkplug_b_pb2.UInt64Array
    # sparkplug_b_pb2.FloatArray
    # sparkplug_b_pb2.DoubleArray
    # sparkplug_b_pb2.BooleanArray
    # sparkplug_b_pb2.StringArray
    # sparkplug_b_pb2.DateTimeArray
}


class Spb2UNSPublisher:
    """
        Class to parse the metric array extracted from the SPB payload and published to the respective UNS topics
        Create only one instance of this class per uns_sparkplugb_listener
        This is a stateful class and stores the mappings of the alias to topic (if MQTTv5 is used)
        This also temporarily stores the mapping of SparkPlugB Metric aliases
    """
    # stores the message aliases as uses in the SparkPlugB message payload
    message_alias_map: Dict(int, str) = dict()
    # Flag indicating this an MQTTv5 connection
    isMQTTv5: bool = False
    # stores the topic aliases to be used if the protocol is MQTTv5
    topic_alias: Dict(str, int) = dict()
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
        self.message_alias_map.clear()

    def extractUNSMsgFromSpbPayload(self,
                                    message,
                                    group_id: str,
                                    message_type: str,
                                    edge_node_id: str,
                                    device_id: str = None) -> dict(str, dict):

        # collate all metrics to the same topic and send them as one payload
        all_uns_messages: dict(str, dict) = {}
        inboundPayload = sparkplug_b_pb2.Payload()
        inboundPayload.ParseFromString(message.payload)
        # stores the metric alias
        metric_alias: Dict(str, int) = dict()
        for metric in inboundPayload.metrics:
            name: str = metric.get(SPB_NAME)
            metric_alias: str = metric.get(SPB_ALIAS)
            if (name is None or name == ""):
                name = self.message_alias_map.get(metric_alias)
                if (name is None or name == ""):
                    LOGGER.error(
                        f"Skipping as metric Name is null and alias not yet provided: {metric}"
                    )
                    next(metric)
            else:
                self.message_alias_map[metric_alias] = name
            name: list[str] = metric.get(SPB_NAME)
            uns_topic = name.rsplit("/", 1)[0]
            tag_name = name.rsplit("/", 1)[1]

            metric_timestamp = metric.get(SPB_TIMESTAMP)
            datatype = metric.get(SPB_DATATYPE)
            metric_value = metric.get(SPB_DATATYPE_KEYS.get(datatype))

            if (bool(metric.get(SPB_IS_NULL))):
                metric_value = None

            uns_message = all_uns_messages.get(uns_topic)
            # check if there were any tags  already parsed for this uns topic
            if (uns_message is None):
                uns_message = dict(tag_name, (metric_value, metric_timestamp))
                uns_message[SPB_TIMESTAMP] = metric_timestamp
                # add this metric to the map
                all_uns_messages[uns_topic] = uns_message
            else:
                # check if there were there was any a already parsed metric for this tag and UNS topic
                old_metric_value = uns_message.get(tag_name)
                old_metric_timestamp = uns_message.get(SPB_TIMESTAMP)
                if (not isinstance(old_metric_value, list)):
                    # replace current metric value with array of values if it is a singe value
                    old_metric_value = list(old_metric_value)
                    # If the value for the metric name already exists then we will have a list
                if (old_metric_timestamp > metric_timestamp):
                    # if the metric in the uns_message is newer than the metric received add the new value at the end
                    #  TODO currently for simplicity have not yet ordered all old values
                    old_metric_value.append(metric_value)
                else:
                    # if the metric in the uns_message is older than the metric received
                    old_metric_value.append(0,
                                            (metric_value, metric_timestamp))
                    uns_message[SPB_TIMESTAMP] = metric_timestamp
                uns_message[tag_name] = old_metric_value
                all_uns_messages[uns_topic] = uns_message

            return all_uns_messages
