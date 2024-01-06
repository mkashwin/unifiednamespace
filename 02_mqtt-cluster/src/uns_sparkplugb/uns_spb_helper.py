"""
Helper class to parse & create SparkplugB messages
@see Tahu Project{https://github.com/eclipse/tahu/blob/master/python/core/sparkplug_b.py}
Extending that based on the specs in
https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf
"""
import logging
import time
from typing import Optional

from google.protobuf.json_format import MessageToDict

from uns_sparkplugb.generated import sparkplug_b_pb2
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload, PropertySet, PropertySetList
from uns_sparkplugb.uns_spb_enums import (
    SPBBasicDataTypes,
    SPBDataSetDataTypes,
    SPBMetricDataTypes,
    SPBParameterTypes,
    SPBPropertyValueTypes,
)

LOGGER = logging.getLogger(__name__)


@staticmethod
def convert_spb_bytes_payload_to_dict(payload: bytes) -> dict:
    """
    Takes raw bytes input and converts it into a dict
    """
    inbound_payload = sparkplug_b_pb2.Payload()
    inbound_payload.ParseFromString(payload)
    return MessageToDict(inbound_payload)


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

    def get_node_death_payload(self, payload: Payload = None) -> Payload:
        """
        Helper to get the Death Node Payload.
        Sets the bdSeq counter in the metric for this payload.
        You can add additional metrics after calling this function
        Always request this before requesting the Node Birth Payload

        Parameters
        ----------
        payload:  Can be None if blank message is being created
        """
        if payload is None:
            payload = Payload()
        self.add_metric(payload, "bdSeq", SPBMetricDataTypes.Int64, self.get_birth_seq_num(), None)
        return payload

    def get_node_birth_payload(self, payload: Payload = None, timestamp: Optional[float] = None) -> Payload:
        """
        Helper to get the Node Birth Payload
        Always request this after requesting the Node Death Payload
        Sets the bdSeq counter in the metric for this payload.
        You can add additional metrics after calling this function
        Parameters
        ----------
        payload:  Can be None if blank message is being created
        timestamp: Optional, if None then current time will be used for metric else provided timestamp
        """
        self.msg_seq_number = 0
        if payload is None:
            payload = Payload()
        if timestamp is None:
            # timestamp in seconds being converted to milliseconds
            payload.timestamp = int(round(time.time() * 1000))
        else:
            payload.timestamp = timestamp
        payload.seq = self.get_seq_num()

        self.add_metric(payload, "bdSeq", SPBBasicDataTypes.Int64, self.get_birth_seq_num(), None, payload.timestamp)
        return payload

    def get_device_birth_payload(self, payload: Payload = None, timestamp: Optional[float] = None) -> Payload:
        """
        Get the DBIRTH payload
        You can add additional metrics after calling this function

        Parameters
        ----------
        payload:  Can be None if blank message is being created
        timestamp: Optional, if None then current time will be used for metric else provided timestamp
        """
        if payload is None:
            payload = Payload()
        if timestamp is None:
            # timestamp in seconds being converted to milliseconds
            payload.timestamp = int(round(time.time() * 1000))
        else:
            payload.timestamp = timestamp
        payload.seq = self.get_seq_num()
        return payload

    def get_device_data_payload(self, payload: Payload = None, timestamp: Optional[float] = None) -> Payload:
        """
        Get a DDATA payload
        You can add additional metrics after calling this function

        Parameters
        ----------
        payload:  Can be None if blank message is being created
        timestamp: if None then current time will be used for metric else provided timestamp
        """
        return self.get_device_birth_payload(payload, timestamp)

    def get_node_data_payload(self, payload: Payload = None) -> Payload:
        """
        Get a NDATA payload
        Always request this after requesting the Node Death Payload
        You can add additional metrics after calling this function

        Parameters
        ----------
        payload:  Can be none if blank message is being created
        """
        return self.get_node_birth_payload(payload)

    def get_metric_wrapper(
        self,
        container: Payload | Payload.Template,
        name: str,
        alias: Optional[int] = None,
        timestamp: Optional[float] = int(round(time.time() * 1000)),
    ) -> Payload.Metric:
        """
        Refactored common code of obtaining metrics and initializing common attributes

        Parameters
        ----------
        container:
            SparkplugB object containing the metric. either Payload or Template
        name: str
            Name of the metric. First time a metric is added Name is mandatory
        alias: int
            alias for metric name. Either Name or Alias must be provided
        timestamp:
            timestamp associated with this metric. If not provided current system time will be used
        """
        metric: Payload.Metric = container.metrics.add()
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
        payload: Payload,
        name: str,
        columns: list[str],  # column headers
        types: list[SPBDataSetDataTypes],  # type of the value in the inner list of rows
        rows: Optional[
            list[list[int | float | bool | str]]
        ],  # list of row values . row value can be of type int, float, bool or str
        alias: Optional[int] = None,
        timestamp: Optional[float] = int(round(time.time() * 1000)),
    ) -> Payload.DataSet:
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
        metric: Payload.Metric = self.get_metric_wrapper(container=payload, name=name, alias=alias, timestamp=timestamp)

        metric.datatype = SPBMetricDataTypes.DataSet
        # Set up the dataset
        metric.dataset_value.num_of_columns = len(types)
        metric.dataset_value.columns.extend(columns)
        metric.dataset_value.types.extend(types)
        for row in rows:
            self.add_row_to_dataset(dataset_value=metric.dataset_value, values=row)

        return metric.dataset_value

    def add_row_to_dataset(self, dataset_value: Payload.DataSet, values: list[int | float | bool | str]):
        """
        Helper method to set the row in the the dataset
        """
        ds_row = dataset_value.rows.add()
        types = dataset_value.types
        for cell_value, cell_type in zip(values, types):
            ds_element = ds_row.elements.add()
            SPBDataSetDataTypes(cell_type).set_value_in_sparkplug(value=cell_value, spb_object=ds_element)

    def init_template_metric(
        self,
        payload: Payload | Payload.Template,
        name: str,
        metrics: list[Payload.Metric],
        version: Optional[str] = None,
        template_ref: Optional[str] = None,
        parameters: Optional[list[tuple[str, SPBParameterTypes, int | float | bool | str]]] = None,
        alias: Optional[int] = None,
    ) -> Payload.Template:
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
        metric: Payload.Metric = self.get_metric_wrapper(container=payload, name=name, alias=alias)
        metric.datatype = SPBMetricDataTypes.Template

        # Set up the template
        if template_ref is not None:
            metric.template_value.template_ref = template_ref
            metric.template_value.is_definition = False
        else:
            metric.template_value.is_definition = True

        if parameters is not None:
            for param in parameters:
                parameter: Payload.Template.Parameter = metric.template_value.parameters.add()
                parameter.name = param[0]
                parameter.type = param[1]
                SPBBasicDataTypes(parameter.type).set_value_in_sparkplug(value=param[2], spb_object=parameter)

        metric.template_value.version = version
        metric.template_value.metrics = metrics

        return metric.template_value

    def add_metric(
        self,
        payload: Payload | Payload.Template,
        name: str,
        datatype: SPBMetricDataTypes,
        value=None,
        alias: Optional[int] = None,
        timestamp: Optional[int] = None,
    ) -> Payload.Metric:
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
            Unsigned int depicting the data type SPBMetricDataTypes
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
        metric: Payload.Metric = self.get_metric_wrapper(container=payload, name=name, alias=alias, timestamp=timestamp)
        metric.datatype = datatype
        if value is None:
            metric.is_null = True
        else:
            SPBMetricDataTypes(datatype).set_value_in_sparkplug(value=value, spb_object=metric)

        # Return the metric
        return metric

    def add_historical_metric(
        self,
        container,
        name: str,
        datatype: SPBMetricDataTypes,
        value,
        timestamp,
        alias: Optional[int] = None,
    ) -> Payload.Metric:
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
            Unsigned int depicting the data type SPBMetricDataTypes
        value:
            Value of the metric
        timestamp:
            timestamp associated with this metric. If not provided current system time will be used
        """
        metric: Payload.Metric = self.add_metric(
            container, name=name, alias=alias, datatype=datatype, value=value, timestamp=timestamp
        )
        metric.is_historical = True
        # Return the metric
        return metric

    def add_null_metric(
        self, container: Payload | Payload.Template, name: str, datatype: SPBMetricDataTypes, alias: Optional[int] = None
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
            Unsigned int depicting the data type SPBMetricDataTypes
        """
        metric: Payload.Metric = self.add_metric(payload=container, name=name, alias=alias, datatype=datatype)
        metric.is_null = True
        return metric

    def add_metadata_to_metric(
        self,
        metric: Payload.Metric,
        is_multi_part: Optional[bool],
        content_type: Optional[str],
        size: Optional[int],
        seq: Optional[int],
        file_name: Optional[str],
        file_type: Optional[str],
        md5: Optional[str],
        description: Optional[str],
    ) -> Payload.MetaData:
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

    def add_properties_to_metric(
        self,
        metric: Payload.Metric,
        keys: list[str],
        datatypes: list[int],
        values: list[str | float | bool | int | Payload.PropertySet | Payload.PropertySetList],
    ) -> PropertySet:
        """
        Helper method to add properties to a Metric
        """
        if len(keys) == len(datatypes) == len(values):
            metric.properties.CopyFrom(self.create_propertyset(keys, datatypes, values))
            return metric.properties
        else:
            raise LookupError(
                f"Length of keys list:{len(keys)},"
                f"Length of datatype list:{len(datatypes)},"
                f"Length of values list:{len(values)}"
                "must be equal"
            )

    def create_propertyset(
        self,
        ps_keys: list[str],
        ps_datatypes: list[int],
        ps_values: list[str | float | bool | int],
    ) -> PropertySet:
        """
        Helper method to create a PropertySet object.
        You will need to set the created object in the Metric via SpBMessageGenerator#add_properties_to_metric
        Use the method Metric.properties.CopyFrom() to set this object in your Metric
        """
        if len(ps_keys) == len(ps_datatypes) == len(ps_values):
            property_value_array: list[Payload.PropertyValue] = []
            for datatype, value in zip(ps_datatypes, ps_values):
                property_value: Payload.PropertyValue = Payload.PropertyValue()
                property_value.type = datatype
                if value is None:
                    property_value.is_null = True
                else:
                    SPBPropertyValueTypes(datatype).set_value_in_sparkplug(value=value, spb_object=property_value)

                property_value_array.append(property_value)

            propertyset: Payload.PropertySet = Payload.PropertySet(keys=ps_keys, values=property_value_array)
            return propertyset
        else:
            raise LookupError(
                f"Length of keys list:{len(ps_keys)},"
                f"Length of datatype list:{len(ps_datatypes)},"
                f"Length of values list:{len(ps_values)}"
                "must be equal"
            )

    def create_propertyset_list(self, propertysets: list[PropertySet]) -> PropertySetList:
        """
        Helper method to create a PropertySetList object.
        Create the required PropertySet Objects first with SpBMessageGenerator#create_propertyset
        Create the PropertySetList object with this function
        Lastly set the created object in the Metric with SpBMessageGenerator#add_properties_to_metric
        """
        return PropertySetList(propertysets)


# class end
