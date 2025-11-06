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

Representation of the sPB payload
"""

import logging
import typing
from datetime import UTC, datetime

import strawberry
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload
from uns_sparkplugb.uns_spb_enums import SPBParameterTypes
from uns_sparkplugb.uns_spb_helper import (
    SPBDataSetDataTypes,
    SPBMetricDataTypes,
    SPBPropertyValueTypes,
    convert_dict_to_payload,
)

from uns_graphql.type.basetype import BytesPayload

LOGGER = logging.getLogger(__name__)


@strawberry.type(
    description="""Wrapper for primitive types in Sparkplug.: int, float, str, bool, list
                 Needed because GraphQL does not support str for unions.
                 Data is converted to its String representation for convenience.
                 Use the datatype to convert to actual type if needed """
)
class SPBPrimitive:
    data: str

    def __init__(self, data: int | float | bool | str | list[int, float, bool, str]):
        self.data = str(data)


@strawberry.type
class SPBMetadata:
    """
    Model of Metadata in SPBv1.0 payload
    """

    is_multi_part: bool | None
    content_type: str | None
    size: int | None
    seq: int | None
    file_name: str | None
    file_type: str | None
    md5: str | None
    description: str | None

    def __init__(self, metadata: Payload.MetaData):
        self.is_multi_part = metadata.is_multi_part if metadata.HasField(
            "is_multi_part") else None
        self.content_type = metadata.content_type if metadata.HasField(
            "content_type") else None
        self.size = metadata.size if metadata.HasField("size") else None
        self.seq = metadata.seq if metadata.HasField("seq") else None
        self.file_name = metadata.file_name if metadata.HasField(
            "file_name") else None
        self.file_type = metadata.file_type if metadata.HasField(
            "file_type") else None
        self.md5 = metadata.md5 if metadata.HasField("md5") else None
        self.description = metadata.description if metadata.HasField(
            "description") else None


@strawberry.type
class SPBPropertySet:
    """
    Model of PropertySet in SPBv1.0 payload
    """

    keys: list[str]
    # trunk-ignore(ruff/UP037)
    values: list[typing.Annotated["SPBPropertyValue",  # This needs to be a string hence quotes
                                  strawberry.lazy(".sparkplugb_node")]]

    def __init__(self, propertyset: Payload.PropertySet) -> None:
        self.keys = propertyset.keys
        self.values = [SPBPropertyValue(value) for value in propertyset.values]


@strawberry.type
class SPBPropertySetList:
    """
    Model of PropertySetList in SPBv1.0 payload
    Wrapper needed because graphQl doesn't support list in Unions
    """

    propertysets: list[typing.Annotated[SPBPropertySet,
                                        strawberry.lazy(".sparkplugb_node")]]


@strawberry.type
class SPBPropertyValue:
    """
    Model of PropertyValue in SPBv1.0 payload
    """

    is_null: bool | None
    datatype: str
    value: SPBPrimitive | typing.Annotated[SPBPropertySet, strawberry.lazy(
        ".sparkplugb_node")] | typing.Annotated[SPBPropertySetList, strawberry.lazy(".sparkplugb_node")]

    def __init__(self, property_value: Payload.PropertyValue):
        self.is_null = property_value.is_null if property_value.HasField(
            "is_null") else None
        self.datatype = SPBPropertyValueTypes(property_value.type).name
        if self.is_null:
            self.value = None
        else:
            match property_value.type:
                case SPBPropertyValueTypes.PropertySet:
                    self.value = SPBPropertySet(
                        property_value.propertyset_value)

                case SPBPropertyValueTypes.PropertySetList:
                    self.value = SPBPropertySetList(
                        propertysets=[
                            SPBPropertySet(propertyset) for propertyset in property_value.propertysets_value.propertyset
                        ]
                    )
                case _:
                    self.value = SPBPrimitive(
                        SPBPropertyValueTypes(
                            property_value.type).get_value_from_sparkplug(property_value)
                    )


@strawberry.type
class SPBDataSetValue:
    """
    Model of DataSet->Row->Value in SPBv1.0 payload
    """

    datatype: strawberry.Private[SPBDataSetDataTypes]  # type: ignore
    # graphql doesn't support Unions
    value: SPBPrimitive

    def __init__(self, datatype: int, dataset_value: Payload.DataSet.DataSetValue):
        self.datatype = SPBDataSetDataTypes(datatype)
        self.value = SPBPrimitive(
            self.datatype.get_value_from_sparkplug(dataset_value))


@strawberry.type
class SPBDataSetRow:
    """
    Model of DataSet->Row in SPBv1.0 payload
    """

    elements: list[SPBDataSetValue]

    def __init__(self, datatypes: list[int], row: Payload.DataSet.Row):
        self.elements = [
            SPBDataSetValue(datatype=datatype, dataset_value=dataset_value)
            for datatype, dataset_value in zip(datatypes, row.elements, strict=True)
        ]


@strawberry.type
class SPBDataSet:
    """
    Model of DataSet in SPBv1.0 payload
    """

    num_of_columns: int
    columns: list[str]
    # maps to spb data types
    types: list[str]
    rows: list[SPBDataSetRow]

    def __init__(self, dataset: Payload.DataSet):
        self.types = [SPBDataSetDataTypes(
            datatype).name for datatype in dataset.types]
        self.num_of_columns = dataset.num_of_columns
        self.columns = dataset.columns
        self.rows = [SPBDataSetRow(datatypes=dataset.types, row=row)
                     for row in dataset.rows]


@strawberry.type
class SPBTemplateParameter:
    """
    Model of a SPB Template Parameter,
    """

    name: str
    datatype: str
    # graphql doesn't support Unions
    value: SPBPrimitive

    def __init__(self, parameter: Payload.Template.Parameter) -> None:
        self.name = parameter.name
        self.datatype = SPBParameterTypes(parameter.type).name
        self.value = SPBPrimitive(SPBParameterTypes(
            parameter.type).get_value_from_sparkplug(parameter))


@strawberry.type
class SPBTemplate:
    """
    Model of Template in SPBv1.0 payload
    """

    version: str | None
    # trunk-ignore(ruff/UP037)
    metrics: list[typing.Annotated["SPBMetric",  # This needs to be a string hence needs quotes
                                   strawberry.lazy(".sparkplugb_node")]]
    parameters: list[SPBTemplateParameter] | None
    template_ref: str | None
    is_definition: bool | None

    def __init__(self, template: Payload.Template):
        self.version = template.version if template.HasField(
            "version") else None
        self.metrics = [SPBMetric(metric) for metric in template.metrics]
        self.template_ref = template.template_ref if template.HasField(
            "template_ref") else None
        self.is_definition = template.is_definition if template.HasField(
            "is_definition") else None
        self.parameters = [SPBTemplateParameter(
            parameter) for parameter in template.parameters]


@strawberry.type
class SPBMetric:
    """
    Model of a SPB Metric, which is within a SPBNode
    """

    name: str
    alias: int | None
    timestamp: datetime
    datatype: str
    is_historical: bool | None
    is_transient: bool | None
    is_null: bool | None
    metadata: SPBMetadata | None
    properties: SPBPropertySet | None
    value: SPBPrimitive | BytesPayload | SPBDataSet | typing.Annotated[SPBTemplate, strawberry.lazy(
        ".sparkplugb_node")]

    def __init__(self, metric: Payload.Metric):
        self.name = metric.name
        self.alias = metric.alias if metric.HasField("alias") else None
        # Timestamp is normally in milliseconds and needs to be converted to microsecond
        self.timestamp = datetime.fromtimestamp(metric.timestamp / 1000, UTC)
        self.datatype = SPBMetricDataTypes(metric.datatype).name
        self.is_historical = metric.is_historical if metric.HasField(
            "is_historical") else None
        self.is_transient = metric.is_transient if metric.HasField(
            "is_transient") else None
        self.is_null = metric.is_null if metric.HasField("is_null") else None
        self.metadata = SPBMetadata(
            metric.metadata) if metric.HasField("metadata") else None
        self.properties = SPBPropertySet(
            metric.properties) if metric.HasField("properties") else None

        if self.is_null:
            self.value = None
        else:
            match metric.datatype:
                case SPBMetricDataTypes.Bytes | SPBMetricDataTypes.File:
                    self.value = BytesPayload(data=SPBMetricDataTypes(
                        metric.datatype).get_value_from_sparkplug(metric))

                case SPBMetricDataTypes.DataSet:
                    self.value = SPBDataSet(
                        SPBMetricDataTypes.DataSet.get_value_from_sparkplug(metric))

                case SPBMetricDataTypes.Template:
                    self.value = SPBTemplate(
                        SPBMetricDataTypes.Template.get_value_from_sparkplug(metric))

                case _:
                    self.value = SPBPrimitive(SPBMetricDataTypes(
                        metric.datatype).get_value_from_sparkplug(metric))


@strawberry.type
class SPBNode:
    """
    Model of a SPB Node representing the Payload Object
    """

    # Fully qualified path of the namespace including current name
    # Usually maps to the topic where the messages were published
    # e.g. spBv1.0/[GROUP]/[MESSAGE_TYPE]/[EDGE_NODE]/[DEVICE]
    topic: str

    # Merged Composite of all Metric published to this node

    # Timestamp of when this node was last modified in milliseconds
    timestamp: datetime

    # Metrics published to the spBv1.0 namespace using protobuf payloads
    metrics: list[SPBMetric]

    # sequence
    seq: int

    # UUID for this message
    uuid: strawberry.ID | None

    # array of bytes used for any custom binary encoded data.
    body: strawberry.scalars.Base64 | None

    def __init__(self, topic: str, payload: Payload | bytes | dict):
        """
        Creates the SPBNode
        topic: The MQTT Topic / namespace to which the SPBPayload was published
        payload: The SparkPlugB Payload. Can be either the Payload object or a bytes/dict representation.
                 In case of dict or bytes the payload will be parsed and transformed in a Payload object
        """
        self.topic = topic

        if isinstance(payload, bytes):
            parsed_payload = Payload()
            parsed_payload.ParseFromString(payload)
            payload = parsed_payload
        elif isinstance(payload, dict):
            payload = convert_dict_to_payload(payload)
        # Timestamp is normally in milliseconds and needs to be converted to microsecond
        # All payloads have a timestamp
        self.timestamp = datetime.fromtimestamp(payload.timestamp / 1000, UTC)
        # Set other fields only if they were initialized in the payload
        self.seq = payload.seq if payload.HasField("seq") else None
        self.uuid = strawberry.ID(
            payload.uuid) if payload.HasField("uuid") else None
        self.body = strawberry.scalars.Base64(
            payload.body) if payload.HasField("body") else None
        # The HasField method does not work for repeated fields
        self.metrics = [SPBMetric(metric) for metric in payload.metrics]
