"""
Helper class to parse & create SparkplugB messages
@see Tahu Project{https://github.com/eclipse/tahu/blob/master/python/core/sparkplug_b.py}
Extending that based on the specs in
https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf
"""
import base64
import logging
import time
from types import SimpleNamespace
from typing import ClassVar, Optional

from google.protobuf.json_format import MessageToDict

from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload
from uns_sparkplugb.uns_spb_enums import (
    SPBArrayDataTypes,
    SPBBasicDataTypes,
    SPBDataSetDataTypes,
    SPBMetricDataTypes,
    SPBParameterTypes,
    SPBPropertyValueTypes,
    SPBValueFieldName,
)

LOGGER = logging.getLogger(__name__)


@staticmethod
def convert_spb_bytes_payload_to_dict(raw_payload: bytes) -> dict:
    """
    Takes raw bytes input and converts it into a dict
    Merges all placeholders like int_value , long_value etc. to a single field value
    """
    spb_payload = Payload()
    spb_payload.ParseFromString(raw_payload)
    # FIXME What float precision should we use?
    spb_to_dict: dict = MessageToDict(spb_payload, preserving_proto_field_name=True, float_precision=5)

    return _fix_keys_and_value_types(spb_to_dict)


@staticmethod
def _fix_keys_and_value_types(spb_dict: dict) -> dict:
    """
    converts string to int for relevant fields
    """
    if not isinstance(spb_dict, dict):
        # this is not a dict. return raw value
        return spb_dict
    value_key_dict: dict = {}

    for key, value in spb_dict.items():
        # First fix the value type
        if key == SPBValueFieldName.BYTES:
            # bytes have been base64 encoded into strings and we need to decode it
            value = base64.b64decode(value)

        elif key in [SPBValueFieldName.INT, SPBValueFieldName.LONG, "timestamp", "alias", "seq", "num_of_columns", "size"]:
            # FIXME Need to do this as these int fields are converted to str in the dict conversion by #MessageToDict
            value = int(value)

        # Then fix field name
        if key in SPBValueFieldName:
            # handle conversion for Array type
            if key == SPBValueFieldName.BYTES and "datatype" in spb_dict:
                # Arrays are only in Metrics which have the datatype field too
                if spb_dict["datatype"] in SPBArrayDataTypes:
                    # Hack to mock a SPB object by converting the dict to a name space
                    spb_dict[key] = value
                    value = SPBArrayDataTypes(spb_dict["datatype"]).get_value_from_sparkplug(SimpleNamespace(**spb_dict))

            # then rename the key
            key = "value"

        # handle composite value objects
        if isinstance(value, dict):
            # Recursively process nested dictionaries
            value_key_dict[key] = _fix_keys_and_value_types(value)
        elif isinstance(value, list):
            value_key_dict[key] = [_fix_keys_and_value_types(x) for x in value]
        else:
            value_key_dict[key] = value

    return value_key_dict


def convert_dict_to_payload(spb_dict: dict) -> Payload:
    """
    converts dict representing a SPB Payload to a Payload Object
    """
    spb_payload = Payload()

    for key, value in spb_dict.items():
        if value is not None:
            if key == "metrics":
                for metric_dict in value:
                    spb_payload.metrics.append(convert_dict_to_metric(metric_dict))
            else:
                setattr(spb_payload, key, value)
    return spb_payload


def convert_dict_to_metric(metric_dict: dict) -> Payload.Metric:
    metric: Payload.Metric = Payload.Metric()
    for key, value in metric_dict.items():
        match key:
            # Handle the various attributes of Metric
            case "value":
                datatype: SPBMetricDataTypes = SPBMetricDataTypes(metric_dict["datatype"])
                match datatype:
                    # Set value based on datatype and special handling to get template and dataset
                    case SPBMetricDataTypes.DataSet:
                        SPBMetricDataTypes.DataSet.set_value_in_sparkplug(convert_dict_to_dataset(value), metric)

                    case SPBMetricDataTypes.Template:
                        SPBMetricDataTypes.Template.set_value_in_sparkplug(convert_dict_to_template(value), metric)

                    case _:
                        # All other value types
                        SPBMetricDataTypes(datatype).set_value_in_sparkplug(value, metric)
                # end of match for value
            case "properties":
                metric.properties.CopyFrom(convert_dict_to_propertyset(value))

            case "metadata":
                # Handle Metadata dict
                for metadata_key, metadata_val in value.items():
                    setattr(metric.metadata, metadata_key, metadata_val)
            case _:
                setattr(metric, key, value)
    return metric


def convert_dict_to_dataset(dataset_dict: dict) -> Payload.DataSet:
    dataset = Payload.DataSet()
    for key, value in dataset_dict.items():
        match key:
            case "rows":
                for row_dict in value:
                    row = Payload.DataSet.Row()
                    for ds_val_dict, datatype in zip(row_dict["elements"], dataset_dict["types"]):
                        ds_val = row.elements.add()
                        SPBDataSetDataTypes(datatype).set_value_in_sparkplug(ds_val_dict["value"], ds_val)

                    dataset.rows.append(row)
            case "columns":
                for col in value:
                    dataset.columns.append(col)

            case "types":
                for datatype in value:
                    dataset.types.append(datatype)

            case "num_of_columns":
                dataset.num_of_columns = value

    return dataset


def convert_dict_to_template(template_dict: dict) -> Payload.Template:
    template = Payload.Template()
    for key, value in template_dict.items():
        match key:
            case "metrics":
                for metric_dict in value:
                    template.metrics.append(convert_dict_to_metric(metric_dict))
            case "parameters":
                for param_dict in value:
                    param_template = Payload.Template.Parameter()
                    param_template.name = param_dict["name"]
                    param_template.type = param_dict["type"]
                    SPBParameterTypes(param_template.type).set_value_in_sparkplug(param_dict["value"], param_template)
                    template.parameters.append(param_template)
            case _:
                setattr(template, key, value)

    return template


def convert_dict_to_propertyset(property_dict: dict) -> Payload.PropertySet:
    property_values: list[Payload.PropertyValue] = []
    for prop_val_dict in property_dict["values"]:
        property_value: Payload.PropertyValue = Payload.PropertyValue()
        property_value.type = prop_val_dict["type"]

        if "is_null" in prop_val_dict:
            property_value.is_null = prop_val_dict["is_null"]

        if not property_value.is_null:
            match property_value.type:
                case SPBPropertyValueTypes.PropertySet:
                    SPBPropertyValueTypes.PropertySet.set_value_in_sparkplug(
                        convert_dict_to_propertyset(prop_val_dict["value"]), property_value
                    )

                case SPBPropertyValueTypes.PropertySetList:
                    SPBPropertyValueTypes.PropertySetList.set_value_in_sparkplug(
                        Payload.PropertySetList(
                            propertyset=[
                                convert_dict_to_propertyset(sub_prop_set)
                                for sub_prop_set in prop_val_dict["value"]["propertyset"]
                            ]
                        ),
                        property_value,
                    )
                case _:
                    SPBPropertyValueTypes(property_value.type).set_value_in_sparkplug(prop_val_dict["value"], property_value)

        property_values.append(property_value)

    propertyset: Payload.PropertySet = Payload.PropertySet(keys=property_dict["keys"], values=property_values)
    return propertyset


class SpBMessageGenerator:
    """
    Helper class to parse & create SparkplugB messages.
    State of alias map and sequence flags maintained across instances of SpBMessageGenerator
    Create one instance of this per node/device
    """

    # sequence number for messages
    msg_seq_number: int = 0

    # birth/death sequence number
    birth_death_seq_num: int = 0

    # map of alias to names for metrics / templates.
    # While adding metrics, if an alias exists for that name it will be used instead
    alias_name_map: ClassVar[dict[str, int]] = {}

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
        Reset the message sequence number
        Sets the bdSeq counter in the metric for this payload.
        You can add additional metrics after calling this function
        Parameters
        ----------
        payload:  Can be None if blank message is being created
        timestamp: Optional, if None then current time will be used for metric else provided timestamp
        """
        # reset sequence number
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

    def _get_metric_wrapper(
        self,
        payload_or_template: Payload | Payload.Template,
        name: str,
        alias: Optional[int] = None,
        timestamp: Optional[float] = int(round(time.time() * 1000)),
    ) -> Payload.Metric:
        """
        Private method. Common code of obtaining metrics and initializing common attributes

        Parameters
        ----------
        payload_or_template:
            SparkplugB object containing the metric. either Payload or Template
        name: str
            Name of the metric. First time a metric is added Name is mandatory
        alias: int
            alias for metric name. Either Name or Alias must be provided
        timestamp:
            timestamp associated with this metric. If not provided current system time will be used
        """
        metric: Payload.Metric = payload_or_template.metrics.add()

        if name is None and alias is None:
            raise ValueError(f"Need either name:{name} or alias:{alias} to be provided.")

        if name is not None and alias is not None:
            # check if alias exists for the provided name, else set the alias mapping
            if self.alias_name_map.get(alias) is None:
                self.alias_name_map[alias] = name
            elif self.alias_name_map.get(alias) != name:
                raise ValueError(
                    f" Name:{name} provided for Alias:{alias} not matching"
                    + f"to previously provided value:{self.alias_name_map.get(alias)}"
                )
            metric.name = name
            metric.alias = alias

        elif name is None:
            if self.alias_name_map.get(alias) is None:
                raise ValueError(f" No name found  for Alias:{alias}. Alias has not yet been set")
            metric.alias = alias
        else:
            metric.name = name
        if timestamp is None:
            timestamp = int(round(time.time() * 1000))
        metric.timestamp = timestamp
        return metric

    def add_metric(
        self,
        payload_or_template: Payload | Payload.Template,
        name: str,
        datatype: SPBMetricDataTypes,
        value=None,
        alias: Optional[int] = None,
        timestamp: Optional[int] = None,
    ) -> Payload.Metric:
        """
        Helper method for adding metrics to a payload_or_template which can be a payload or a template.

        Parameters
        ----------
        payload_or_template:
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
        metric: Payload.Metric = self._get_metric_wrapper(
            payload_or_template=payload_or_template, name=name, alias=alias, timestamp=timestamp
        )
        metric.datatype = datatype
        if value is None:
            metric.is_null = True
        else:
            SPBMetricDataTypes(datatype).set_value_in_sparkplug(value=value, spb_object=metric)

        # Return the metric
        return metric

    def add_historical_metric(
        self,
        payload: Payload | Payload.Template,
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
        payload:
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
            payload_or_template=payload, name=name, alias=alias, datatype=datatype, value=value, timestamp=timestamp
        )
        metric.is_historical = True
        # Return the metric
        return metric

    def add_null_metric(
        self,
        payload_or_template: Payload | Payload.Template,
        name: str,
        datatype: SPBMetricDataTypes,
        alias: Optional[int] = None,
    ):
        """
        Helper method for adding null metrics  to a container which can be a payload or a template

        Parameters
        ----------
        payload_or_template:
            the Parent Payload or Template object to which a historical metric is to be added
        name:
            Name of the metric.May be hierarchical to build out proper folder structures
            for applications consuming the metric values
        alias:
            unsigned 64-bit integer representing an optional alias for a Sparkplug B payload
        datatype:
            Unsigned int depicting the data type SPBMetricDataTypes
        """
        metric: Payload.Metric = self.add_metric(
            payload_or_template=payload_or_template, name=name, alias=alias, datatype=datatype
        )
        metric.is_null = True
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
        metric: Payload.Metric = self._get_metric_wrapper(
            payload_or_template=payload, name=name, alias=alias, timestamp=timestamp
        )

        metric.datatype = SPBMetricDataTypes.DataSet
        # Set up the dataset
        metric.dataset_value.num_of_columns = len(types)
        metric.dataset_value.columns.extend(columns)
        metric.dataset_value.types.extend(types)
        for row in rows:
            self._add_row_to_dataset(dataset_value=metric.dataset_value, values=row)

        return metric.dataset_value

    def _add_row_to_dataset(self, dataset_value: Payload.DataSet, values: list[int | float | bool | str]):
        """
        Private Helper method to set the row in the the dataset
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
        metrics: Optional[list[Payload.Metric]],
        version: Optional[str] = None,
        template_ref: Optional[str] = None,
        parameters: Optional[list[tuple[str, SPBParameterTypes, int | float | bool | str]]] = None,
        alias: Optional[int] = None,
    ) -> Payload.Template:
        """
        Helper method for adding template metrics to a payload
        Additional metrics can  be added to the template after initialization
        using SpBMessageGenerator#add_metric and passing the template instance

        Parameters
        ----------
        payload:
            SparkplugB Payload
        name: str
            Name of the metric. First time a metric is added Name is mandatory
        metrics:
            An array of metrics representing the members of the Template.
            These can be primitive datatypes or other Templates as required.
            Can also be None
        version:
            An optional field and can be included in a Template Definition or Template Instance
        alias: int
            alias for metric name. Either Name or Alias must be provided
        template_ref:
            Represents reference to a Template name if this is a Template instance.
            If this is a Template definition this field must be null
        parameters:
            Optional array of tuples representing parameters associated with the Template
            parameter.name; str, parameter.type = SPBParameterTypes, parameter.value = int| float| bool | str
        """
        metric: Payload.Metric = self._get_metric_wrapper(payload_or_template=payload, name=name, alias=alias)
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
                SPBParameterTypes(parameter.type).set_value_in_sparkplug(value=param[2], spb_object=parameter)

        metric.template_value.version = version
        if metrics is not None and len(metrics) > 0:
            for inner_metric in metrics:
                metric.template_value.metrics.append(inner_metric)

        return metric.template_value

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
        if is_multi_part is not None:
            metric.metadata.is_multi_part = is_multi_part
        if content_type is not None:
            metric.metadata.content_type = content_type
        if size is not None:
            metric.metadata.size = size

        if seq is not None:
            metric.metadata.seq = seq
        if file_name is not None:
            metric.metadata.file_name = file_name
        if file_type is not None:
            metric.metadata.file_type = file_type
        if md5 is not None:
            metric.metadata.md5 = md5
        if description is not None:
            metric.metadata.description = description

    def add_properties_to_metric(
        self,
        metric: Payload.Metric,
        keys: list[str],
        datatypes: list[SPBPropertyValueTypes],
        values: list[str | float | bool | int | Payload.PropertySet | Payload.PropertySetList],
    ) -> Payload.PropertySet:
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
    ) -> Payload.PropertySet:
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

    def create_propertyset_list(self, propertysets: list[Payload.PropertySet]) -> Payload.PropertySetList:
        """
        Helper method to create a PropertySetList object.
        Create the required PropertySet Objects first with SpBMessageGenerator#create_propertyset
        Create the PropertySetList object with this function
        Lastly set the created object in the Metric with SpBMessageGenerator#add_properties_to_metric
        """
        return Payload.PropertySetList(propertyset=propertysets)


# class end
