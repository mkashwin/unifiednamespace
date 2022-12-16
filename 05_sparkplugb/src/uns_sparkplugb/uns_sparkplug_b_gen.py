# /**
# * Helper class to parse & create SparkplugB messages
# * @see Tahu Project{https://github.com/eclipse/tahu/blob/master/python/core/sparkplug_b.py}
# */
import logging
from uns_sparkplugb.generated import sparkplug_b_pb2
import time

LOGGER = logging.getLogger(__name__)


class Spb_Message_Generator:
    # sequence number for messages
    seqNum: int = 0
    # birth/death sequence number
    bdSeq: int = 0

    # map of  metric names to alias. While adding metrics, if an alias exists for that name it will be used instead
    aliasMap: dict[str, str] = {}
    def __init__(self) -> None:
        self.aliasMap = dict()

    def getSeqNum(self):
        """
        Helper method for getting the next sequence number
        """
        retVal = self.seqNum
        LOGGER.debug(f"Sequence Number: {str(retVal)}")
        self.seqNum += 1
        if self.seqNum == 256:
            self.seqNum = 0
        return retVal

    def getBdSeqNum(self):
        """
        Helper method for getting the next birth/death sequence number
        """
        retVal = self.bdSeq
        LOGGER.debug(f"Birth/Death Sequence Number:  {str(retVal)}")
        self.bdSeq += 1
        if self.bdSeq == 256:
            self.bdSeq = 0
        return retVal

    def getNodeDeathPayload(self, payload=None):
        """
        Helper to get the Death Node Payload
        Always request this before requesting the Node Birth Payload
        """
        if (payload is None):
            payload = sparkplug_b_pb2.Payload()
        self.addMetric(payload, "bdSeq", None, sparkplug_b_pb2.Int64,
                       self.getBdSeqNum())
        return payload

    def getNodeBirthPayload(self, payload=None):
        """
        Helper to get the Node Birth Payload
        Always request this after requesting the Node Death Payload
        """
        self.seqNum = 0
        if (payload is None):
            payload = sparkplug_b_pb2.Payload()
        payload.timestamp = int(round(time.time() * 1000))
        payload.seq = self.getSeqNum()
        self.addMetric(payload, "bdSeq", None, sparkplug_b_pb2.Int64,
                       --self.bdSeq, payload.timestamp)
        return payload

    def getDeviceBirthPayload(self, payload=None):
        """
        Get the DBIRTH payload
        """
        if (payload is None):
            payload = sparkplug_b_pb2.Payload()
        payload.timestamp = int(round(time.time() * 1000))
        payload.seq = self.getSeqNum()
        return payload

    ######################################################################
    # Get a DDATA payload
    ######################################################################
    def getDeviceDataPayload(self, payload=None):
        """
        @TODO review this
        """
        return self.getDeviceBirthPayload(payload)

    ######################################################################
    # Get a NDATA payload
    ######################################################################
    def getNodeDataPayload(self, payload=None):
        """
        @TODO review this
        """
        return self.getNodeBirthPayload(payload)

    ######################################################################
    # Refactored common code of obtaining metrics and initializing
    # common attributes
    ######################################################################
    def getMetricWrapper(self,
                         payload,
                         name,
                         alias,
                         timestamp=int(round(time.time() * 1000))):
        metric = payload.metrics.add()
        if alias is not None:
            metric.alias = alias

        if name is not None:
            metric.name = name

        if self.aliasMap.get(name) is None:
            self.aliasMap[name] = alias
        elif self.aliasMap.get(name) == alias:
            metric.name = None
        else:
            raise ValueError(f"Alias:{alias} provided for Name:{name} not matching to previously provided alias:{self.aliasMap.get(name)}  ")
        metric.timestamp = timestamp
        return metric

    ######################################################################
    # Helper method for adding dataset metrics to a payload
    ######################################################################
    def initDatasetMetric(self, payload, name, alias, columns, types):
        metric = self.getMetricWrapper(payload, name, alias)

        metric.datatype = sparkplug_b_pb2.DataSet
        # Set up the dataset
        metric.dataset_value.num_of_columns = len(types)
        metric.dataset_value.columns.extend(columns)
        metric.dataset_value.types.extend(types)
        return metric.dataset_value

    ######################################################################
    # Helper method for adding dataset metrics to a payload
    ######################################################################
    def initTemplateMetric(self, payload, name, alias, templateRef):
        metric = self.getMetricWrapper(payload, name, alias)
        metric.datatype = sparkplug_b_pb2.Template

        # Set up the template
        if templateRef is not None:
            metric.template_value.template_ref = templateRef
            metric.template_value.is_definition = False
        else:
            metric.template_value.is_definition = True

        return metric.template_value

    ######################################################################
    #
    ######################################################################
    def addMetric(self,
                  payload,
                  name,
                  alias,
                  type,
                  value=None,
                  timestamp=int(round(time.time() * 1000))):
        """
        Helper method for adding metrics to a container which can be a payload or a template.
        Parameters
        ----------
        payload: the Payload object
        name: Name of the metric.May be hierarchical to build out proper folder structures for applications
              consuming the metric values
        alias: Alias. unsigned 64-bit integer representing an optional alias for a Sparkplug B payload
        type,
        value,
        timestamp
        """
        metric = self.getMetricWrapper(payload, name, alias, timestamp)
        if value is None:
            metric.is_null = True
        metric.datatype = type

        match type:
            case sparkplug_b_pb2.Int8: setIntValueInMetric(value, metric, 8),
            case sparkplug_b_pb2.Int16: setIntValueInMetric(value, metric, 16),
            case sparkplug_b_pb2.Int32: setIntValueInMetric(value, metric, 32),
            case sparkplug_b_pb2.Int64: setLongValueInMetric(value, metric, 64),
            case sparkplug_b_pb2.UInt8: setIntValueInMetric(value, metric, 0),
            case sparkplug_b_pb2.UInt16: setIntValueInMetric(value, metric, 0),
            case sparkplug_b_pb2.UInt32: setIntValueInMetric(value, metric, 0),
            case sparkplug_b_pb2.UInt64: setLongValueInMetric(value, metric, 0),
            case sparkplug_b_pb2.Float: setFloatValueInMetric(value, metric),
            case sparkplug_b_pb2.Double: setDoubleValueInMetric(value, metric),
            case sparkplug_b_pb2.Boolean: setBooleanValueInMetric(value, metric),
            case sparkplug_b_pb2.String: setStringValueInMetric(value, metric),
            case sparkplug_b_pb2.DateTime: setLongValueInMetric(value, metric, 0),
            case sparkplug_b_pb2.Text: setStringValueInMetric(value, metric),
            case sparkplug_b_pb2.UUID: setStringValueInMetric(value, metric),
            case sparkplug_b_pb2.DataSet: 
                raise ValueError(f"MetricType:{sparkplug_b_pb2.DataSet} Not supported by #addMetric(). Use #initDatasetMetric()")
            case sparkplug_b_pb2.Bytes: setBytesValueInMetric(value, metric),
            case sparkplug_b_pb2.File: setBytesValueInMetric(value, metric),
            case sparkplug_b_pb2.Template: setTemplatesValueInMetric(value, metric)
            case _: unknownValueTypeInMetric(value, metric)

        # Return the metric
        return metric

    ######################################################################
    # Helper method for adding metrics to a container which can be a
    # payload or a template
    ######################################################################
    def addHistoricalMetric(self, container, name, alias, type, value):
        metric = self.addMetric(container, name, alias, type, value)
        metric.is_historical = True
        # Return the metric
        return metric

    #####################################################################
    # Helper method for adding metrics to a container which can be a
    # payload or a template
    ######################################################################
    def addNullMetric(self, container, name, alias, type):
        metric = self.addMetric(container, name, alias, type)
        metric.is_null = True
        return metric


######################################################################
#
######################################################################
@staticmethod
def setIntValueInMetric(value, metric, factor):
    if value is not None and value < 0:
        value = value + (0 if factor == 0 else 2**factor)
    metric.int_value = value
    return value


######################################################################
#
######################################################################
@staticmethod
def setLongValueInMetric(value, metric, factor=0):
    if value is not None and value < 0:
        value = value + (2**factor if factor != 0 else 0)
    metric.long_value = value
    return value


######################################################################
#
######################################################################
@staticmethod
def setFloatValueInMetric(value, metric):
    metric.float_value = value
    return value


######################################################################
#
######################################################################
@staticmethod
def setDoubleValueInMetric(value, metric):
    metric.double_value = value
    return value


######################################################################
#
######################################################################
@staticmethod
def setStringValueInMetric(value, metric):
    metric.string_value = value
    return value


######################################################################
#
######################################################################
@staticmethod
def setBytesValueInMetric(value, metric):
    metric.bytes_value = value
    return value


######################################################################
#
######################################################################
@staticmethod
def setTemplatesValueInMetric(value, metric):
    metric.template_value = value
    return value


######################################################################
#
######################################################################
@staticmethod
def setBooleanValueInMetric(value: bool, metric):
    metric.boolean_value = value
    return value


######################################################################
#
######################################################################
@staticmethod
def unknownValueTypeInMetric(value, metric):
    metric.datatype = None
    LOGGER.error(
        f"Invalid type:  {type}.\n Value:{value} not added to {metric}",
        stack_info=True,
        exc_info=True)
