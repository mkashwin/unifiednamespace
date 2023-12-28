"""
Helper class to parse & create SparkplugB messages
@see Tahu Project{https://github.com/eclipse/tahu/blob/master/python/core/sparkplug_b.py}
Extending that based on the specs in
https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf
"""
import logging
import time
from enum import IntEnum, unique
from typing import Literal, Optional

from google.protobuf.json_format import MessageToDict

from uns_sparkplugb.generated import sparkplug_b_pb2
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload as spbPayload

LOGGER = logging.getLogger(__name__)


@unique
class SPBBasicDataTypes(IntEnum):
    """
    Enumeration of basic datatypes as per sparkplugB specifications
    """

    Unknown = sparkplug_b_pb2.Unknown
    Int8 = sparkplug_b_pb2.Int8
    Int16 = sparkplug_b_pb2.Int16
    Int32 = sparkplug_b_pb2.Int32
    Int64 = sparkplug_b_pb2.Int64
    UInt8 = sparkplug_b_pb2.UInt8
    UInt16 = sparkplug_b_pb2.UInt16
    UInt32 = sparkplug_b_pb2.UInt32
    UInt64 = sparkplug_b_pb2.UInt64
    Float = sparkplug_b_pb2.Float
    Double = sparkplug_b_pb2.Double
    Boolean = sparkplug_b_pb2.Boolean
    String = sparkplug_b_pb2.String
    DateTime = sparkplug_b_pb2.DateTime
    Text = sparkplug_b_pb2.Text


@unique
class SPBAdditionalDataTypes(IntEnum):
    """
    Enumeration of additional datatypes as per sparkplugB specifications
    """

    UUID = sparkplug_b_pb2.UUID
    DataSet = sparkplug_b_pb2.DataSet
    Bytes = sparkplug_b_pb2.Bytes
    File = sparkplug_b_pb2.File
    Template = sparkplug_b_pb2.Template


@unique
class SPBArrayDataTypes(IntEnum):
    Int8Array = sparkplug_b_pb2.Int8Array
    Int16Array = sparkplug_b_pb2.Int16Array
    Int32Array = sparkplug_b_pb2.Int32Array
    Int64Array = sparkplug_b_pb2.Int64Array
    UInt8Array = sparkplug_b_pb2.UInt8Array
    UInt16Array = sparkplug_b_pb2.UInt16Array
    UInt32Array = sparkplug_b_pb2.UInt32Array
    UInt64Array = sparkplug_b_pb2.UInt64Array
    FloatArray = sparkplug_b_pb2.FloatArray
    DoubleArray = sparkplug_b_pb2.DoubleArray
    BooleanArray = sparkplug_b_pb2.BooleanArray
    StringArray = sparkplug_b_pb2.StringArray
    DateTimeArray = sparkplug_b_pb2.DateTimeArray


@staticmethod
def __combine_enums(name: str, *enums: IntEnum):
    """
    Private Utility function to merge Enums because Enums cannot be extended
    """
    combined_enum = IntEnum(name, {item.name: item.value for enum in enums for item in enum})
    return combined_enum


# Enumeration of datatypes possible in a Metric.
# Combine  basic datatypes, additional datatypes and array datatypes
SPBMetricDataTypes: IntEnum = __combine_enums(
    "SPBMetricDataTypes", SPBBasicDataTypes, SPBAdditionalDataTypes, SPBArrayDataTypes
)


# Enumeration of datatypes possible for PropertyTypes
# Extend basic datatypes with PropertySet & PropertySetList types
SPBPropertyValueTypes = __combine_enums(
    "SPBPropertyValueTypes",
    SPBBasicDataTypes,
    IntEnum("SPBPropertySetTypes", {"PropertySet": sparkplug_b_pb2.PropertySet}),
    IntEnum("SPBPropertySetListTypes", {"PropertySetList": sparkplug_b_pb2.PropertySetList}),
)


# Enumeration of datatypes possible for DataSetValue
SPBDataSetDataTypes = SPBBasicDataTypes


class SpBMessageGenerator:
    """
    Helper class to parse & create SparkplugB messages.
    Each instance of the generator maintains state of alias map and sequence flags
    """

    def __init__(self) -> None:
        # sequence number for messages
        self.msg_seq_number: int = 0
        # birth/death sequence number
        self.birth_death_seq_num: int = 0

        # map of  metric names to alias.
        # While adding metrics, if an alias exists for that name it will be used instead
        self.alias_map: dict[str, int] = {}

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
        self.add_metric(payload, "bdSeq", SPBBasicDataTypes.Int64, self.get_birth_seq_num(), None)
        return payload

    def get_node_birth_payload(self, payload: spbPayload = None, timestamp: Optional[float] = None) -> spbPayload:
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
            # timestamp in seconds being converted to milliseconds
            payload.timestamp = int(round(time.time() * 1000))
        else:
            payload.timestamp = timestamp
        payload.seq = self.get_seq_num()

        self.add_metric(payload, "bdSeq", SPBBasicDataTypes.Int64, self.get_birth_seq_num(), None, payload.timestamp)
        return payload

    def get_device_birth_payload(self, payload: spbPayload = None, timestamp: Optional[float] = None) -> spbPayload:
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
            # timestamp in seconds being converted to milliseconds
            payload.timestamp = int(round(time.time() * 1000))
        else:
            payload.timestamp = timestamp
        payload.seq = self.get_seq_num()
        return payload

    def get_device_data_payload(self, payload: spbPayload = None, timestamp: Optional[float] = None) -> spbPayload:
        """
        Get a DDATA payload

        Parameters
        ----------
        payload:  Can be None if blank message is being created
        timestamp: if None then current time will be used for metric else provided timestamp
        @TODO review this
        """
        return self.get_device_birth_payload(payload, timestamp)

    def get_node_data_payload(self, payload: spbPayload = None) -> spbPayload:
        """
        Get a NDATA payload

        Parameters
        ----------
        payload:  Can be none if blank message is being created
        @TODO review this
        """
        return self.get_node_birth_payload(payload)

    def get_metric_wrapper(
        self,
        payload: spbPayload,
        name: str,
        alias: Optional[int] = None,
        timestamp: Optional[float] = int(round(time.time() * 1000)),
    ) -> spbPayload.Metric:
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
        metric: spbPayload.Metric = payload.metrics.add()
        if alias is not None:
            metric.alias = alias

        if name is not None:
            metric.name = name

        if self.alias_map.get(name) is None:
            self.alias_map[name] = alias
        elif self.alias_map.get(name) == alias:
            metric.name = None
        else:
            raise ValueError(
                f"Alias:{alias} provided for Name:{name} not matching"
                + f"to previously provided alias:{self.alias_map.get(name)}"
            )
        metric.timestamp = timestamp
        return metric

    def get_dataset_metric(
        self,
        payload: spbPayload,
        name: str,
        columns: list[str],  # column headers
        types: list[SPBDataSetDataTypes],  # type of the value in the inner list of rows
        rows: Optional[
            list[list[int | float | bool | str]]
        ],  # list of row values . row value can be of type int, float, bool or str
        alias: Optional[int] = None,
        timestamp: Optional[float] = int(round(time.time() * 1000)),
    ) -> spbPayload.DataSet:
        """
        Helper method for initializing a dataset metric to a payload

        Parameters
        ----------
        payload:
            SparkplugB Payload
        name: str
            Name of the metric. First time a metric is added Name is mandatory
        columns: list[str]
            array of strings representing the column headers of this DataSet.
            It must have the same number of elements that the types array
        types: list[int]
            array of unsigned 32 bit integers representing the datatypes of the column
        rows: Optional list of list[int | float | bool | str]
              outer list mapping to all rows
              inner list mapping to the values of a row
              length of inner list must match length of types
              order of elements in inner list must adhere to the datatype in types
              if not provided, rows can be added
        alias: int
            alias for metric name. Either Name or Alias must be provided
        timestamp:
            timestamp associated with this metric. If not provided current system time will be used
        """
        if len(columns) != len(types):
            raise ValueError("Length of columns and types should match")
        metric: spbPayload.Metric = self.get_metric_wrapper(payload=payload, name=name, alias=alias, timestamp=timestamp)

        metric.datatype = SPBMetricDataTypes.DataSet
        # Set up the dataset
        metric.dataset_value.num_of_columns = len(types)
        metric.dataset_value.columns.extend(columns)
        metric.dataset_value.types.extend(types)
        for row in rows:
            self.add_row_to_dataset(dataset_value=metric.dataset_value, values=row)

        return metric.dataset_value

    def add_row_to_dataset(self, dataset_value: spbPayload.DataSet, values: list[int | float | bool | str]):
        ds_row = dataset_value.rows.add()
        types = dataset_value.types
        for cell, cell_type in zip(values, types):
            ds_element = ds_row.elements.add()
            match cell_type:
                case SPBDataSetDataTypes.Int8:
                    set_int_value_in_spb_object(cell, ds_element, 8)
                case SPBDataSetDataTypes.Int16:
                    set_int_value_in_spb_object(cell, ds_element, 16)
                case SPBDataSetDataTypes.Int32:
                    set_int_value_in_spb_object(cell, ds_element, 32)
                case SPBDataSetDataTypes.Int64:
                    set_long_value_in_spb_object(cell, ds_element, 64)
                case SPBDataSetDataTypes.UInt8 | SPBDataSetDataTypes.UInt16 | SPBDataSetDataTypes.UInt32:
                    set_int_value_in_spb_object(cell, ds_element, 0)
                case SPBDataSetDataTypes.UInt64 | SPBDataSetDataTypes.DateTime:
                    set_long_value_in_spb_object(cell, ds_element, 0)
                case SPBDataSetDataTypes.Float:
                    set_float_value_in_spb_object(cell, ds_element)
                case SPBDataSetDataTypes.Double:
                    set_double_value_in_spb_object(cell, ds_element)
                case SPBDataSetDataTypes.Boolean:
                    set_boolean_value_in_spb_object(cell, ds_element)
                case SPBDataSetDataTypes.String | SPBDataSetDataTypes.Text:
                    set_string_value_in_spb_object(cell, ds_element)
                case _:
                    unknown_value_in_spb_object(SPBDataSetDataTypes.Unknown, cell, ds_element)

    def init_template_metric(
        self,
        payload: spbPayload,
        name: str,
        metrics: list[spbPayload.Metric],
        version: Optional[str] = None,
        template_ref: Optional[str] = None,
        parameters: Optional[list[tuple[str, SPBBasicDataTypes, int | float | bool | str]]] = None,
        alias: Optional[int] = None,
    ) -> spbPayload.Template:
        """
        Helper method for adding template metrics to a payload

        Parameters
        ----------
        payload:
            SparkplugB Payload
        name: str
            Name of the metric. First time a metric is added Name is mandatory
        metrics:
            An array of metrics representing the members of the Template.
            These can be primitive datatypes or other Templates as required.
        version:
            An optional field and can be included in a Template Definition or Template Instance
        alias: int
            alias for metric name. Either Name or Alias must be provided
        template_ref:
            Represents reference to a Template name if this is a Template instance.
            If this is a Template definition this field must be null
        parameters:
            Optional array of tuples representing parameters associated with the Template
            parameter.name; str, parameter.type = SPBBasicDataTypes, parameter.value = int| float| bool | str
        """
        metric: spbPayload.Metric = self.get_metric_wrapper(payload=payload, name=name, alias=alias)
        metric.datatype = SPBMetricDataTypes.Template

        # Set up the template
        if template_ref is not None:
            metric.template_value.template_ref = template_ref
            metric.template_value.is_definition = False
        else:
            metric.template_value.is_definition = True

        if parameters is not None:
            for param in parameters:
                parameter: spbPayload.Template.Parameter = metric.template_value.parameters.add()
                parameter.name = param[0]
                parameter.type = param[1]
                match parameter.type:
                    case SPBBasicDataTypes.Int8:
                        set_int_value_in_spb_object(param[2], parameter, 8)
                    case SPBBasicDataTypes.Int16:
                        set_int_value_in_spb_object(param[2], parameter, 16)
                    case SPBBasicDataTypes.Int32:
                        set_int_value_in_spb_object(param[2], parameter, 32)
                    case SPBBasicDataTypes.Int64:
                        set_long_value_in_spb_object(param[2], parameter, 64)
                    case SPBBasicDataTypes.UInt8 | SPBBasicDataTypes.UInt16 | SPBBasicDataTypes.UInt32:
                        set_int_value_in_spb_object(param[2], parameter, 0)
                    case SPBBasicDataTypes.UInt64 | SPBBasicDataTypes.DateTime:
                        set_long_value_in_spb_object(param[2], metric, 0)
                    case SPBBasicDataTypes.Float:
                        set_float_value_in_spb_object(param[2], parameter)
                    case SPBBasicDataTypes.Double:
                        set_double_value_in_spb_object(param[2], parameter)
                    case SPBBasicDataTypes.Boolean:
                        set_boolean_value_in_spb_object(param[2], parameter)
                    case SPBBasicDataTypes.String | SPBBasicDataTypes.Text:
                        set_string_value_in_spb_object(param[2], parameter)
                    case _:
                        unknown_value_in_spb_object(SPBBasicDataTypes.Unknown, param[2], parameter)

        metric.template_value.version = version
        metric.template_value.metrics = metrics

        return metric.template_value

    def add_metric(
        self,
        payload: spbPayload | spbPayload.Template,
        name: str,
        datatype: int,
        value=None,
        alias: Optional[int] = None,
        timestamp: Optional[int] = None,
    ) -> spbPayload.Metric:
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
        if timestamp is None:
            # SparkplugB works with milliseconds
            timestamp = int(round(time.time() * 1000))
        metric: spbPayload.Metric = self.get_metric_wrapper(payload=payload, name=name, alias=alias, timestamp=timestamp)
        if value is None:
            metric.is_null = True
        metric.datatype = datatype

        match datatype:
            case SPBMetricDataTypes.Int8:
                # check if the value is less than zero. If yes,convert it to an unsigned value
                # while preserving its representation in the given number of bits
                value = set_int_value_in_spb_object(value, metric, 8)
            case SPBMetricDataTypes.Int16:
                value = set_int_value_in_spb_object(value, metric, 16)
            case SPBMetricDataTypes.Int32:
                value = set_int_value_in_spb_object(value, metric, 32)
            case SPBMetricDataTypes.Int64:
                value = set_long_value_in_spb_object(value, metric, 64)
            case SPBMetricDataTypes.UInt8 | SPBMetricDataTypes.UInt16 | SPBMetricDataTypes.UInt32:
                value = set_int_value_in_spb_object(value, metric, 0)
            case SPBMetricDataTypes.UInt64 | SPBMetricDataTypes.DateTime:
                value = set_long_value_in_spb_object(value, metric, 0)
            case SPBMetricDataTypes.Float:
                value = set_float_value_in_spb_object(value, metric)
            case SPBMetricDataTypes.Double:
                value = set_double_value_in_spb_object(value, metric)
            case SPBMetricDataTypes.Boolean:
                value = set_boolean_value_in_spb_object(value, metric)
            case SPBMetricDataTypes.String | SPBMetricDataTypes.Text | SPBMetricDataTypes.UUID:
                value = set_string_value_in_spb_object(value, metric)
            case SPBMetricDataTypes.Bytes | SPBMetricDataTypes.File:
                value = set_bytes_value_in_spb_object(value, metric)
            case SPBMetricDataTypes.Template:
                value = set_templates_value_in_spb_object(value, metric)
            case SPBMetricDataTypes.DataSet:
                raise (
                    f"MetricType:{SPBMetricDataTypes.DataSet}" + " Not supported by #add_metric(). Use #get_dataset_metric()",
                )
            case SPBMetricDataTypes.Int8Array:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.Int8Array}" + " Not supported by #add_metric()",
                )
            case SPBMetricDataTypes.Int16Array:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.Int16Array}" + " Not supported by #add_metric()",
                )
            case SPBMetricDataTypes.Int32Array:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.Int32Array}" + " Not supported by #add_metric()",
                )
            case SPBMetricDataTypes.Int64Array:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.Int64Array}" + " Not supported by #add_metric()",
                )
            case SPBMetricDataTypes.UInt8Array:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.UInt8Array}" + " Not supported by #add_metric()",
                )
            case SPBMetricDataTypes.UInt16Array:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.UInt16Array}" + " Not supported by #add_metric()",
                )
            case SPBMetricDataTypes.UInt32Array:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.UInt32Array}" + " Not supported by #add_metric()",
                )
            case SPBMetricDataTypes.UInt64Array:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.UInt64Array}" + " Not supported by #add_metric()",
                )
            case SPBMetricDataTypes.FloatArray:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.FloatArray}" + " Not supported by #add_metric()",
                )
            case SPBMetricDataTypes.DoubleArray:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.DoubleArray}" + " Not supported by #add_metric()",
                )
            case SPBMetricDataTypes.BooleanArray:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.BooleanArray}" + " Not supported by #add_metric()",
                )
            case SPBMetricDataTypes.StringArray:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.StringArray}" + " Not supported by #add_metric()",
                )
            case SPBMetricDataTypes.DateTimeArray:
                # FIXME how to support this?
                raise NotImplementedError(
                    f"MetricType:{SPBMetricDataTypes.DateTimeArray}" + " Not supported by #add_metric()",
                )
            case _:
                unknown_value_in_spb_object(SPBMetricDataTypes.Unknown, value, metric)

        # Return the metric
        return metric

    def add_historical_metric(
        self,
        container,
        name: str,
        datatype: int,
        value,
        timestamp,
        alias: Optional[int] = None,
    ):
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
        metric = self.add_metric(container, name=name, alias=alias, datatype=datatype, value=value, timestamp=timestamp)
        metric.is_historical = True
        # Return the metric
        return metric

    def add_null_metric(
        self, container: spbPayload | spbPayload.Template, name: str, datatype: int, alias: Optional[int] = None
    ):
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
        metric: spbPayload.Metric = self.add_metric(payload=container, name=name, alias=alias, datatype=datatype)
        metric.is_null = True
        return metric

    def add_metadata_to_metric(
        self,
        metric: spbPayload.Metric,
        is_multi_part: Optional[bool],
        content_type: Optional[str],
        size: Optional[int],
        seq: Optional[int],
        file_name: Optional[str],
        file_type: Optional[str],
        md5: Optional[str],
        description: Optional[str],
    ) -> spbPayload.MetaData:
        """
        Sets the MetaData object in a Metric and is used to describe different types of binary data in the metric

        Parameters
        ----------
        is_multi_part:
            A Boolean representing whether this metric contains part of a multi-part message.
        content_type:
            UTF-8 string which represents the content type of a given metric value if applicable.
        size:
            unsigned 64-bit integer representing the size of the metric value. e.g. file size.
        seq:
            For multipart metric, this is an unsigned 64-bit integer representing the
            sequence number of this part of a multipart metric.
        file_name:
            For file metric, this is a UTF-8 string representing the filename of the file.
        file_type
            For file metric, this is a UTF-8 string representing the type of the file.
        md5
            For byte array or file metric that can have a md5sum,
            this field can be used as a UTF-8 string to represent it.
        description
            Freeform field with a UTF-8 string to represent any other pertinent metadata for this
            metric. It can contain JSON, XML, text, or anything else that can be understood by both the
            publisher and the subscriber.
        """
        metric.metadata.is_multi_part = is_multi_part
        metric.metadata.content_type = content_type
        metric.metadata.size = size

        metric.metadata.seq = seq
        metric.metadata.file_name = file_name
        metric.metadata.file_type = file_type
        metric.metadata.md5 = md5
        metric.metadata.description = description


# class end


@staticmethod
def set_int_value_in_spb_object(
    value: int,
    metric: spbPayload.Metric | spbPayload.PropertyValue | spbPayload.DataSet.DataSetValue | spbPayload.Template.Parameter,
    factor: Literal[0, 8, 16, 32] = 0,
) -> int:
    """
    Helper method for setting Int value in metric/property value/dataset value / template parameter
    check if the value is less than zero. If yes,convert it to an unsigned value
    while preserving its representation in the given number of bits
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


@staticmethod
def set_long_value_in_spb_object(
    value: int,
    metric: spbPayload.Metric | spbPayload.PropertyValue | spbPayload.DataSet.DataSetValue | spbPayload.Template.Parameter,
    factor: Literal[0, 64] = 0,
) -> int:
    """
    Helper method for setting Long value in metric/property value/dataset value / template parameter
    Check if the value is less than zero. If yes,convert it to an unsigned value
    while preserving its representation in the given number of bits
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


@staticmethod
def set_float_value_in_spb_object(
    value: float,
    metric: spbPayload.Metric | spbPayload.PropertyValue | spbPayload.DataSet.DataSetValue | spbPayload.Template.Parameter,
) -> float:
    """
    Helper method for setting float value in metric/property value/dataset value / template parameter

    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.float_value = value
    return value


@staticmethod
def set_double_value_in_spb_object(
    value: float,
    metric: spbPayload.Metric | spbPayload.PropertyValue | spbPayload.DataSet.DataSetValue | spbPayload.Template.Parameter,
) -> float:
    """
    Helper method for setting double value in metric/property value/dataset value / template parameter

    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.double_value = value
    return value


@staticmethod
def set_string_value_in_spb_object(
    value: str,
    metric: spbPayload.Metric | spbPayload.PropertyValue | spbPayload.DataSet.DataSetValue | spbPayload.Template.Parameter,
) -> str:
    """
    Helper method for setting string value in metric/property value/dataset value / template parameter

    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.string_value = value
    return value


@staticmethod
def set_bytes_value_in_spb_object(
    value: bytes,
    metric: spbPayload.Metric | spbPayload.PropertyValue | spbPayload.DataSet.DataSetValue | spbPayload.Template.Parameter,
) -> bytes:
    """
    Helper method for setting bytes value in metric/property value/dataset value / template parameter

    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.bytes_value = value
    return value


@staticmethod
def set_templates_value_in_spb_object(
    value,
    metric: spbPayload.Metric | spbPayload.PropertyValue | spbPayload.DataSet.DataSetValue | spbPayload.Template.Parameter,
):
    """
    Helper method for setting template value in metric/property value/dataset value / template parameter

    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.template_value = value
    return value


@staticmethod
def set_boolean_value_in_spb_object(
    value: bool,
    metric: spbPayload.Metric | spbPayload.PropertyValue | spbPayload.DataSet.DataSetValue | spbPayload.Template.Parameter,
) -> bool:
    """
    Helper method for setting boolean value in metric/property value/dataset value / template parameter

    Parameters
    ----------
    value:
    metric: Metric object
    """
    metric.boolean_value = value
    return value


@staticmethod
def unknown_value_in_spb_object(
    datatype,
    value,
    metric: spbPayload.Metric | spbPayload.PropertyValue | spbPayload.DataSet.DataSetValue | spbPayload.Template.Parameter,
):
    """
    Helper method handling values of unknown type in metric

    Parameters
    ----------
    datatype: int but not matching the sparkplugB specifications for data types
    value: value to stored. will be ignored
    metric: Metric object/ PropertyValue/ DataSetValue/ Template.Parameter
    """

    match type(metric):
        case spbPayload.Metric:
            metric.datatype = None  # attribute name is different for Metric
        case spbPayload.PropertyValue | spbPayload.Template.Parameter:
            metric.type = None
        case spbPayload.DataSet.DataSetValue:
            pass  # object doesn't have type attribute

    LOGGER.error(
        "Invalid type: %s.\n Value: %s not added to %s", str(datatype), str(value), str(metric), stack_info=True, exc_info=True
    )


@staticmethod
def convert_spb_bytes_payload_to_dict(payload: bytes) -> dict:
    """
    Takes raw bytes input and converts it into a dict
    """
    inbound_payload = sparkplug_b_pb2.Payload()
    inbound_payload.ParseFromString(payload)
    return MessageToDict(inbound_payload)
