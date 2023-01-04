# /**
# * Helper class to parse & create SparkplugB messages
# * @see Tahu Project{https://github.com/eclipse/tahu/blob/master/python/core/sparkplug_b.py}
# */
import logging
import time

from uns_sparkplugb.generated import sparkplug_b_pb2

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
        Parameters
        ----------
        payload:  Can be None if blank message is being created
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
        Parameters
        ----------
        payload:  Can be None if blank message is being created
        """
        self.seqNum = 0
        if (payload is None):
            payload = sparkplug_b_pb2.Payload()
        payload.timestamp = int(round(time.time() * 1000))
        payload.seq = self.getSeqNum()
        ## why was there --self.bdSeq over here ?? 
        self.addMetric(payload, "bdSeq", None, sparkplug_b_pb2.Int64,
                       self.getBdSeqNum(), payload.timestamp)
        return payload

    def getDeviceBirthPayload(self, payload=None):
        """
        Get the DBIRTH payload
        Parameters
        ----------
        payload:  Can be None if blank message is being created
        """
        if (payload is None):
            payload = sparkplug_b_pb2.Payload()
        payload.timestamp = int(round(time.time() * 1000))
        payload.seq = self.getSeqNum()
        return payload

    ######################################################################
    def getDeviceDataPayload(self, payload=None):
        """
        Get a DDATA payload
        Parameters
        ----------
        payload:  Can be None if blank message is being created
        @TODO review this
        """
        return self.getDeviceBirthPayload(payload)

    ######################################################################
    def getNodeDataPayload(self, payload=None):
        """
        Get a NDATA payload
        Parameters
        ----------
        payload:  Can be none if blank message is being created
        @TODO review this
        """
        return self.getNodeBirthPayload(payload)

    ######################################################################

    def getMetricWrapper(self,
                         payload,
                         name: str,
                         alias: int = None,
                         timestamp: float = int(round(time.time() * 1000))):
        """
        Refactored common code of obtaining metrics and initializing common attributes
        Parameters
        ----------
        payload:
            SparkplugB Payload
        name: str
            Name of the metric. First time a metric is added Name is mandatory
        alias: int
            alias for metric name. Either Name or Alias must be provided
        timestamp:
            timestamp associated with this metric. If not provided current system time will be used

        """
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
            raise ValueError(f"Alias:{alias} provided for Name:{name} not matching"
                             + f"to previously provided alias:{self.aliasMap.get(name)}")
        metric.timestamp = timestamp
        return metric

    ######################################################################
    def initDatasetMetric(self, payload, name: str, alias: int, columns: list[str], types: list[int],
                          timestamp: float = int(round(time.time() * 1000))):
        """
        Helper method for initializing a dataset metric to a payload
        FIXME Need to enhance to add Row and Elements (DataSet.Row and  DataSet.DataSetValue )
        Parameters
        ----------
        payload:
            SparkplugB Payload
        name: str
            Name of the metric. First time a metric is added Name is mandatory
        alias: int
            alias for metric name. Either Name or Alias must be provided
        columns: list[str]
            array of strings representing the column headers of this DataSet.
            It must have the same number of elements that the types array
        types: list[int]
            array of unsigned 32 bit integers representing the datatypes of the column
        timestamp:
            timestamp associated with this metric. If not provided current system time will be used
        """
        metric = self.getMetricWrapper(payload=payload, name=name, alias=alias, timestamp=timestamp)

        metric.datatype = sparkplug_b_pb2.DataSet
        # Set up the dataset
        metric.dataset_value.num_of_columns = len(types)
        metric.dataset_value.columns.extend(columns)
        metric.dataset_value.types.extend(types)
        return metric.dataset_value

    ######################################################################
    def initTemplateMetric(self, payload, name: str, alias: int, templateRef: str):
        """
        Helper method for adding template metrics to a payload
        Parameters
        ----------
        payload:
            SparkplugB Payload
        name: str
            Name of the metric. First time a metric is added Name is mandatory
        alias: int
            alias for metric name. Either Name or Alias must be provided
        templateRef:
            Represents reference to a Template name if this is a Template instance.
            If this is a Template definition this field must be null
        """
        metric = self.getMetricWrapper(payload=payload, name=name, alias=alias)
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
                  name: str,
                  alias: int,
                  type: int,
                  value=None,
                  timestamp=int(round(time.time() * 1000))):
        """
        Helper method for adding metrics to a container which can be a payload or a template.
        Parameters
        ----------
        payload:
            the Payload object
        name:
            Name of the metric.May be hierarchical to build out proper folder structures for applications
            consuming the metric values
        alias:
            unsigned 64-bit integer representing an optional alias for a Sparkplug B payload
        type:
            Unsigned int depicting the data type
        value:
            Value of the metric
        timestamp:
            timestamp associated with this metric. If not provided current system time will be used
        """
        metric = self.getMetricWrapper(payload=payload, name=name, alias=alias, timestamp=timestamp)
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
                raise ValueError(f"MetricType:{sparkplug_b_pb2.DataSet}"
                                 + " Not supported by #addMetric(). Use #initDatasetMetric()")
            case sparkplug_b_pb2.Bytes: setBytesValueInMetric(value, metric),
            case sparkplug_b_pb2.File: setBytesValueInMetric(value, metric),
            case sparkplug_b_pb2.Template: setTemplatesValueInMetric(value, metric)
            case _: unknownValueTypeInMetric(value, metric)

        # Return the metric
        return metric

    ######################################################################

    def addHistoricalMetric(self, container, name: str, alias: int, type: int, value, timestamp):
        """
        Helper method for adding metrics to a container which can be a
        payload or a template
        Parameters
        ----------
        container:
            the Parent Payload or Template object to which a historical metric is to be added
        name:
            Name of the metric.May be hierarchical to build out proper folder structures for applications
            consuming the metric values
        alias:
            unsigned 64-bit integer representing an optional alias for a Sparkplug B payload
        type:
            Unsigned int depicting the data type
        value:
            Value of the metric
        timestamp:
            timestamp associated with this metric. If not provided current system time will be used
        """
        metric = self.addMetric(container, name=name, alias=alias, type=type, value=value, timestamp=timestamp)
        metric.is_historical = True
        # Return the metric
        return metric

    ######################################################################
    def addNullMetric(self, container, name: str, alias: int, type: int):
        """
        Helper method for adding null metrics  to a container which can be a payload or a template
        Parameters
        ----------
        container:
            the Parent Payload or Template object to which a historical metric is to be added
        name:
            Name of the metric.May be hierarchical to build out proper folder structures for applications
            consuming the metric values
        alias:
            unsigned 64-bit integer representing an optional alias for a Sparkplug B payload
        type:
            Unsigned int depicting the data type
        """
        metric = self.addMetric(payload=container, name=name, alias=alias, type=type)
        metric.is_null = True
        return metric
# class end


######################################################################
@staticmethod
def setIntValueInMetric(value: int, metric, factor: int):
    """
    Helper method for setting Int value in metric
    Parameters
    ----------
    value:
    metric: Metric object
    factor: Depending on datatype used to mask negative integers
                Int8:  8
                Int16: 16
                Int32: 32
    """
    if value is not None and value < 0:
        value = value + (0 if factor == 0 else 2**factor)
    metric.int_value = value
    return value


######################################################################
@staticmethod
def setLongValueInMetric(value: int, metric, factor=0):
    """
    Helper method for setting Long value in metric
    Parameters
    ----------
    value:
    metric: Metric object
    factor: Depending on datatype used to mask negative integers
                Int64:  64
                all others: 0
    """
    if value is not None and value < 0:
        value = value + (2**factor if factor != 0 else 0)
    metric.long_value = value
    return value


######################################################################
@staticmethod
def setFloatValueInMetric(value: float, metric):
    """
    Helper method for setting float value in metric
    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.float_value = value
    return value


######################################################################
@staticmethod
def setDoubleValueInMetric(value: float, metric):
    """
    Helper method for setting double value in metric
    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.double_value = value
    return value


######################################################################
@staticmethod
def setStringValueInMetric(value: str, metric):
    """
    Helper method for setting string value in metric
    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.string_value = value
    return value


######################################################################
@staticmethod
def setBytesValueInMetric(value: bytes, metric):
    """
    Helper method for setting bytes value in metric
    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.bytes_value = value
    return value


######################################################################
@staticmethod
def setTemplatesValueInMetric(value, metric):
    """
    Helper method for setting template value in metric
    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.template_value = value
    return value


######################################################################
@staticmethod
def setBooleanValueInMetric(value: bool, metric):
    """
    Helper method for setting boolean value in metric
    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.boolean_value = value
    return value


######################################################################
@staticmethod
def unknownValueTypeInMetric(value, metric):
    """
    Helper method handling values of unknown type in metric
    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.datatype = None
    LOGGER.error(
        f"Invalid type:  {type}.\n Value:{value} not added to {metric}",
        stack_info=True,
        exc_info=True)
