import logging
import typing
from datetime import datetime
from enum import Enum

import strawberry
from strawberry.types import Info
from uns_sparkplugb.uns_spb_helper import SPBDataSetDataTypes, SPBMetricDataTypes, SPBPropertyValueTypes

from uns_graphql.type.basetype import BytesPayload, JSONPayload

LOGGER = logging.getLogger(__name__)


@strawberry.enum
class SPBDataTypeEnum(Enum):
    SPBMetricDataTypes = SPBMetricDataTypes


@strawberry.enum
class SPBPropertyTypeEnum(Enum):
    SPBPropertyValueTypeEnum = SPBPropertyValueTypes


@strawberry.type
class SPBDataSetTypeEnum(Enum):
    SPBDataSetDataType = SPBDataSetDataTypes
    pass


@strawberry.type
class SPBMetadata:
    """
    Model of Metadata in SPBv1.0 payload
    """

    is_multi_part: bool
    content_type: str
    size: int
    seq: int
    file_name: str
    file_type: str
    md5: str
    description: str


@strawberry.lazy_type
class SPBPropertySet:
    """
    Model of PropertySet in SPBv1.0 payload
    """

    keys: list[str]
    values: list["SPBPropertyValue"]


@strawberry.lazy_type
class SPBPropertyValue:
    """
    Model of PropertyValue in SPBv1.0 payload
    """

    is_null: bool
    datatype: SPBPropertyTypeEnum
    value: [int, float, str, SPBPropertySet, list[SPBPropertySet]]

    @strawberry.field(name="value")
    def resolve_value(self, info: Info):  # noqa: ARG002
        """
        Resolve value based on type
        """
        datatype: int = self.datatype
        if self.is_null:
            return None
        match datatype:
            case SPBPropertyTypeEnum.UInt32 | SPBPropertyTypeEnum.UInt64:
                return int(self.value)
            case SPBPropertyTypeEnum.Float | SPBPropertyTypeEnum.Double:
                return float(self.value)
            case SPBPropertyTypeEnum.String:
                return str(self.value)
            case SPBPropertyTypeEnum.PropertySet:
                return SPBPropertySet(value=self.value)
            case SPBPropertyTypeEnum.PropertySetList:
                return list(SPBPropertySet(self.value))


@strawberry.type
class SPBDataSetValue:
    """
    Model of DataSet->Row->Value in SPBv1.0 payload
    """

    datatype: strawberry.Private[SPBDataSetTypeEnum]
    value: typing.Union(int, float, bool, str)

    @strawberry.field(name="value")
    def resolve_value(self, info: Info):  # noqa: ARG002
        datatype = self.datatype
        match datatype:
            case SPBDataSetTypeEnum.UInt32 | SPBDataSetTypeEnum.UInt64:
                return int(self.value)

            case SPBDataSetTypeEnum.Float | SPBDataSetTypeEnum.Double:
                return float(self.value)

            case SPBDataSetTypeEnum.Boolean:
                return bool(self.value)

            case SPBDataSetTypeEnum.String:
                return str(self.value)


@strawberry.type
class SPBDataSetRow:
    """
    Model of DataSet->Row in SPBv1.0 payload
    """

    elements = list[SPBDataSetValue]

    def __init__(self, datatypes: list[SPBDataSetTypeEnum], elements: list[int | float | bool | str]):
        if len(datatypes) == len(elements):
            self.elements = list[SPBDataSetValue]
            for datatype, value in zip(datatypes, elements):
                self.elements.append(SPBDataSetValue(datatype=datatype, value=value))
        else:
            raise ValueError(f"length of datatypes: {len(datatypes)} should match length of  elements: {len(elements)}")


@strawberry.type
class SPBDataSet:
    """
    Model of DataSet in SPBv1.0 payload
    """

    num_of_columns: int
    columns: list[str]
    # maps to spb data types
    types: list[SPBDataTypeEnum]
    rows: list[SPBDataSetRow(SPBDataSetValue())]

    def __init__(self, columns: list[str], types: list[SPBDataTypeEnum], rows: list[int, float, bool, str]):
        if len(types) == len(columns):
            self.types = types
            self.num_of_columns = len(types)
            self.columns = columns
            self.rows = list[SPBDataSetRow]
            for row in rows:
                self.rows.append(SPBDataSetRow(datatypes=types, elements=row))
        else:
            raise ValueError(f"Length of types array: {len(types)} should be same as length of values:{len(rows)}")


class SPBTemplateParameter:
    """
    Model of a SPB Template Parameter,
    """

    name: str
    datatype: SPBDataTypeEnum
    value: any

    @strawberry.field(name="value")
    def resolve_value(self, info: Info):  # noqa: ARG002
        """
        Resolve value based on datatype
        """
        # Logic to dynamically resolve 'value' based on 'datatype'

        datatype: int = self.datatype
        match datatype:
            case SPBDataTypeEnum.Float | SPBDataTypeEnum.Double:
                return float(self.value)

            case SPBDataTypeEnum.Boolean:
                return bool(self.value)

            case SPBDataTypeEnum.String | SPBDataTypeEnum.Text:
                return str(self.value)

            case SPBDataTypeEnum.ID:
                return strawberry.ID(value=str(self.value))

            case SPBDataTypeEnum.Bytes | SPBDataTypeEnum.File:
                return bytes(self.value)

            case SPBDataTypeEnum.DataSet:
                return SPBDataSet(value=self.value)

            case SPBDataTypeEnum.Template:
                return SPBTemplate(value=self.value)
            case _:
                LOGGER.error(
                    "Invalid type: %s.\n Trying Value: %s as String",
                    str(self.datatype),
                    str(self.value),
                    stack_info=True,
                    exc_info=True,
                )
                return str(self.value)


@strawberry.lazy_type
class SPBTemplate:
    """
    Model of Template in SPBv1.0 payload
    """

    version: str
    metrics: list["SPBMetric"]
    parameters: list[SPBTemplateParameter]
    template_ref: str
    is_definition: bool


@strawberry.type
class SPBMetric:
    """
    Model of a SPB Metric, which is within a SPBNode
    """

    name: str
    alias: int
    timestamp: datetime
    datatype: SPBDataTypeEnum
    is_historical: bool
    is_transient: bool
    is_null: bool
    metadata: SPBMetadata
    properties: SPBPropertySet
    value: strawberry.union[int, float, bool, str, strawberry.ID, bytes, SPBDataSet, SPBTemplate]

    @strawberry.field(name="value")
    def resolve_value(self, info: Info):  # noqa: ARG002
        """
        Resolve value based on datatype
        """
        # Logic to dynamically resolve 'value' based on 'datatype'

        datatype: int = self.datatype
        if self.is_null:
            return None
        match datatype:
            case (
                SPBDataTypeEnum.Int8
                | SPBDataTypeEnum.Int16
                | SPBDataTypeEnum.Int32
                | SPBDataTypeEnum.Int64
                | SPBDataTypeEnum.UInt8
                | SPBDataTypeEnum.UInt16
                | SPBDataTypeEnum.UInt32
                | SPBDataTypeEnum.UInt64
                | SPBDataTypeEnum.DateTime
            ):
                return int(self.value)

            case SPBDataTypeEnum.Float | SPBDataTypeEnum.Double:
                return float(self.value)

            case SPBDataTypeEnum.Boolean:
                return bool(self.value)

            case SPBDataTypeEnum.String | SPBDataTypeEnum.Text:
                return str(self.value)

            case SPBDataTypeEnum.ID:
                return strawberry.ID(value=str(self.value))

            case SPBDataTypeEnum.Bytes | SPBDataTypeEnum.File:
                return bytes(self.value)

            case SPBDataTypeEnum.DataSet:
                return SPBDataSet(value=self.value)

            case SPBDataTypeEnum.Template:
                return SPBTemplate(value=self.value)
            # FIXME enhance to support arrays also.
            case _:
                LOGGER.error(
                    "Invalid type: %s.\n Trying Value: %s as String",
                    str(self.datatype),
                    str(self.value),
                    stack_info=True,
                    exc_info=True,
                )
                return str(self.value)


@strawberry.type
class SPBNode:
    """
    Model of a SPB Node,
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

    # Properties / message payload for non protobuf messages e.g. STATE
    properties: JSONPayload

    # sequence
    seq: int

    # UUID for this message
    uuid: strawberry.ID

    body: list[BytesPayload]
