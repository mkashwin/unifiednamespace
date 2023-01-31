"""
 Helper class to parse & create SparkplugB messages
 @see Tahu Project{https://github.com/eclipse/tahu/blob/master/python/core/sparkplug_b.py}
"""
import logging
import time

from uns_sparkplugb.generated import sparkplug_b_pb2
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload as spbPayload

LOGGER = logging.getLogger(__name__)


class SpBMessageGenerator:
    """
    Helper class to parse & create SparkplugB messages
    """
    # sequence number for messages
    msg_seq_number: int = 0
    # birth/death sequence number
    birth_death_seq_num: int = 0

    # map of  metric names to alias.
    # While adding metrics, if an alias exists for that name it will be used instead
    alias_map: dict[str, str] = {}

    def __init__(self) -> None:
        self.alias_map = dict()

    def get_seq_num(self):
        """
        Helper method for getting the next sequence number
        """
        ret_val = self.msg_seq_number
        LOGGER.debug("Sequence Number:%s", str(ret_val))
        self.msg_seq_number += 1
        if self.msg_seq_number == 256:
            self.msg_seq_number = 0
        return ret_val

    def get_birth_seq_num(self):
        """
        Helper method for getting the next birth/death sequence number
        """
        ret_val = self.birth_death_seq_num
        LOGGER.debug("Birth/Death Sequence Number:%s", str(ret_val))
        self.birth_death_seq_num += 1
        if self.birth_death_seq_num == 256:
            self.birth_death_seq_num = 0
        return ret_val

    def get_node_death_payload(self, payload: spbPayload = None) -> spbPayload:
        """
        Helper to get the Death Node Payload
        Always request this before requesting the Node Birth Payload
        Parameters
        ----------
        payload:  Can be None if blank message is being created
        """
        if payload is None:
            payload = spbPayload()
        self.add_metric(payload, "bdSeq", sparkplug_b_pb2.Int64,
                        self.get_birth_seq_num(), None)
        return payload

    def get_node_birth_payload(self, payload: spbPayload = None,  timestamp: float = None) -> spbPayload:
        """
        Helper to get the Node Birth Payload
        Always request this after requesting the Node Death Payload
        Parameters
        ----------
        payload:  Can be None if blank message is being created
        timestamp: Optional, if None then current time will be used for metric else provided timestamp
        """
        self.msg_seq_number = 0
        if payload is None:
            payload = spbPayload()
        if timestamp is None:
            payload.timestamp = int(round(time.time() * 1000))
        else:
            payload.timestamp = timestamp
        payload.seq = self.get_seq_num()
        # FIXME why was there --self.bdSeq over here ??
        self.add_metric(payload, "bdSeq", sparkplug_b_pb2.Int64,
                        self.get_birth_seq_num(), None, payload.timestamp)
        return payload

    def get_device_birth_payload(self,
                                 payload: spbPayload = None,
                                 timestamp: float = None) -> spbPayload:
        """
        Get the DBIRTH payload
        Parameters
        ----------
        payload:  Can be None if blank message is being created
        timestamp: Optional, if None then current time will be used for metric else provided timestamp
        """
        if payload is None:
            payload = spbPayload()
        if timestamp is None:
            payload.timestamp = int(round(time.time() * 1000))
        else:
            payload.timestamp = timestamp
        payload.seq = self.get_seq_num()
        return payload

    ######################################################################
    def get_device_data_payload(self,
                                payload: spbPayload = None,
                                timestamp: float = None) -> spbPayload:
        """
        Get a DDATA payload
        Parameters
        ----------
        payload:  Can be None if blank message is being created
        timestamp: if None then current time will be used for metric else provided timestamp
        @TODO review this
        """
        return self.get_device_birth_payload(payload, timestamp)

    ######################################################################
    def get_node_data_payload(self,
                              payload: spbPayload = None) -> spbPayload:
        """
        Get a NDATA payload
        Parameters
        ----------
        payload:  Can be none if blank message is being created
        @TODO review this
        """
        return self.get_node_birth_payload(payload)

    ######################################################################

    def get_metric_wrapper(self,
                           payload: spbPayload,
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

        if self.alias_map.get(name) is None:
            self.alias_map[name] = alias
        elif self.alias_map.get(name) == alias:
            metric.name = None
        else:
            raise ValueError(f"Alias:{alias} provided for Name:{name} not matching"
                             + f"to previously provided alias:{self.alias_map.get(name)}")
        metric.timestamp = timestamp
        return metric

    ######################################################################
    def init_dataset_metric(self, payload: spbPayload, name: str,
                            columns: list[str], types: list[int], alias: int = None,
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
        metric = self.get_metric_wrapper(payload=payload,
                                         name=name, alias=alias, timestamp=timestamp)

        metric.datatype = sparkplug_b_pb2.DataSet
        # Set up the dataset
        metric.dataset_value.num_of_columns = len(types)
        metric.dataset_value.columns.extend(columns)
        metric.dataset_value.types.extend(types)
        return metric.dataset_value

    ######################################################################
    def init_template_metric(self, payload: spbPayload, name: str,
                             template_ref: str, alias: int = None):
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
        template_ref:
            Represents reference to a Template name if this is a Template instance.
            If this is a Template definition this field must be null
        """
        metric = self.get_metric_wrapper(payload=payload, name=name, alias=alias)
        metric.datatype = sparkplug_b_pb2.Template

        # Set up the template
        if template_ref is not None:
            metric.template_value.template_ref = template_ref
            metric.template_value.is_definition = False
        else:
            metric.template_value.is_definition = True

        return metric.template_value

    ######################################################################
    #
    ######################################################################
    def add_metric(self,
                   payload: spbPayload,
                   name: str,
                   datatype: int,
                   value=None,
                   alias: int = None,
                   timestamp=int(round(time.time() * 1000))):
        """
        Helper method for adding metrics to a container which can be a payload or a template.
        Parameters
        ----------
        payload:
            the Payload object
        name:
            Name of the metric.May be hierarchical to build out proper folder structures
            for applications consuming the metric values
        datatype:
            Unsigned int depicting the data type
        value:
            Value of the metric
        alias:
            unsigned 64-bit integer representing an optional alias for a Sparkplug B payload
        timestamp:
            timestamp associated with this metric. If not provided current system time will be used
        """
        metric = self.get_metric_wrapper(payload=payload, name=name,
                                         alias=alias, timestamp=timestamp)
        if value is None:
            metric.is_null = True
        metric.datatype = datatype

        match datatype:
            case sparkplug_b_pb2.Int8: value = set_int_value_in_metric(value, metric, 8)
            case sparkplug_b_pb2.Int16: value = set_int_value_in_metric(value, metric, 16)
            case sparkplug_b_pb2.Int32: value = set_int_value_in_metric(value, metric, 32)
            case sparkplug_b_pb2.Int64: value = set_long_value_in_metric(value, metric, 64)
            case sparkplug_b_pb2.UInt8: value = set_int_value_in_metric(value, metric, 0)
            case sparkplug_b_pb2.UInt16: value = set_int_value_in_metric(value, metric, 0)
            case sparkplug_b_pb2.UInt32: value = set_int_value_in_metric(value, metric, 0)
            case sparkplug_b_pb2.UInt64: value = set_long_value_in_metric(value, metric, 0)
            case sparkplug_b_pb2.Float: value = set_float_value_in_metric(value, metric)
            case sparkplug_b_pb2.Double: value = set_double_value_in_metric(value, metric)
            case sparkplug_b_pb2.Boolean: value = set_boolean_value_in_metric(value, metric)
            case sparkplug_b_pb2.String: value = set_string_value_in_metric(value, metric)
            case sparkplug_b_pb2.DateTime: value = set_long_value_in_metric(value, metric, 0)
            case sparkplug_b_pb2.Text: value = set_string_value_in_metric(value, metric)
            case sparkplug_b_pb2.UUID: value = set_string_value_in_metric(value, metric)
            case sparkplug_b_pb2.DataSet:
                # FIXME how to support this?
                raise ValueError(f"MetricType:{sparkplug_b_pb2.DataSet}"
                                 + " Not supported by #add_metric(). Use #init_dataset_metric()")
            case sparkplug_b_pb2.Bytes: value = set_bytes_value_in_metric(value, metric)
            case sparkplug_b_pb2.File: value = set_bytes_value_in_metric(value, metric)
            case sparkplug_b_pb2.Template: value = set_templates_value_in_metric(value, metric)
            case _: unknown_value_in_metric(datatype, value, metric)

        # Return the metric
        return metric

    ######################################################################

    def add_historical_metric(self, container, name: str, 
                              datatype: int, value, timestamp, alias: int = None,):
        """
        Helper method for adding metrics to a container which can be a
        payload or a template
        Parameters
        ----------
        container:
            the Parent Payload or Template object to which a historical metric is to be added
        name:
            Name of the metric. May be hierarchical to build out proper folder structures
            for applications consuming the metric values
        alias:
            unsigned 64-bit integer representing an optional alias for a Sparkplug B payload
        datatype:
            Unsigned int depicting the data type
        value:
            Value of the metric
        timestamp:
            timestamp associated with this metric. If not provided current system time will be used
        """
        metric = self.add_metric(container, name=name, alias=alias, datatype=datatype,
                                 value=value, timestamp=timestamp)
        metric.is_historical = True
        # Return the metric
        return metric

    ######################################################################
    def add_null_metric(self, container, name: str, datatype: int, alias: int = None):
        """
        Helper method for adding null metrics  to a container which can be a payload or a template
        Parameters
        ----------
        container:
            the Parent Payload or Template object to which a historical metric is to be added
        name:
            Name of the metric.May be hierarchical to build out proper folder structures
            for applications consuming the metric values
        alias:
            unsigned 64-bit integer representing an optional alias for a Sparkplug B payload
        datatype:
            Unsigned int depicting the data type
        """
        metric = self.add_metric(payload=container, name=name, alias=alias, datatype=datatype)
        metric.is_null = True
        return metric
# class end


######################################################################
@staticmethod
def set_int_value_in_metric(value: int, metric, factor: int):
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
def set_long_value_in_metric(value: int, metric, factor=0):
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
def set_float_value_in_metric(value: float, metric):
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
def set_double_value_in_metric(value: float, metric):
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
def set_string_value_in_metric(value: str, metric):
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
def set_bytes_value_in_metric(value: bytes, metric):
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
def set_templates_value_in_metric(value, metric):
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
def set_boolean_value_in_metric(value: bool, metric):
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
def unknown_value_in_metric(datatype, value, metric):
    """
    Helper method handling values of unknown type in metric
    Parameters
    ----------
    datatype: int but not matching the sparkplugB specifications for data types
    value: value to stored. will be ignored
    metric: Metric object
    """
    metric.datatype = None
    LOGGER.error(
        "Invalid type: %s.\n Value: %s not added to %s",
        str(datatype),
        str(value),
        str(metric),
        stack_info=True,
        exc_info=True)
