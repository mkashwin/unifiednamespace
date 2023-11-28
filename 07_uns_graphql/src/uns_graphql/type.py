"""
Type of data to be retrieved from the UNS
"""

import logging

import graphene
from uns_sparkplugb.generated import sparkplug_b_pb2

LOGGER = logging.getLogger(__name__)


class UNSNode(graphene.ObjectType):
    """
    Model of a UNS Node,
    """

    # pylint: disable=too-few-public-methods
    # Name of the node. Also present as part of the namespace
    node_name = graphene.NonNull(graphene.String)
    # Type of the Node depending on the topic hierarchy in accordance with ISA-95 Part 2
    # ["ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE", "NESTED_ATTRIBUTE"]
    node_type = graphene.NonNull(graphene.String)

    # Fully qualified path of the namespace including current name
    # Usually maps to the topic where multiple messages were published e.g. ent1/fac1/area5
    namespace: graphene.String = graphene.NonNull(graphene.String)

    # Merged Composite of all properties published to this node
    payload: graphene.JSONString = graphene.JSONString()

    # Timestamp of when this node was last modified
    last_updated: graphene.BigInt = graphene.BigInt()


class SPBDataTypeEnum(graphene.Enum):
    """
    Enumeration of datatypes possible
    """

    Unknown = sparkplug_b_pb2.Unknown
    Int8 = sparkplug_b_pb2.Int8
    Int16 = sparkplug_b_pb2.Int16
    Int32 = sparkplug_b_pb2.Int32
    Int64 = sparkplug_b_pb2.Int64
    UInt8 = sparkplug_b_pb2.UInt16
    UInt16 = sparkplug_b_pb2.UInt16
    UInt32 = sparkplug_b_pb2.UInt32
    UInt64 = sparkplug_b_pb2.UInt64
    Float = sparkplug_b_pb2.Float
    Double = sparkplug_b_pb2.Double
    Boolean = sparkplug_b_pb2.Boolean
    String = sparkplug_b_pb2.String
    DateTime = sparkplug_b_pb2.DateTime
    Text = sparkplug_b_pb2.Text
    UUID = sparkplug_b_pb2.UUID
    DataSet = sparkplug_b_pb2.DataSet
    Bytes = sparkplug_b_pb2.Bytes
    File = sparkplug_b_pb2.File
    Template = sparkplug_b_pb2.Template
    PropertySet = sparkplug_b_pb2.PropertySet
    PropertySetList = sparkplug_b_pb2.PropertySetList
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


class SPBPropertyTypeEnum(graphene.Enum):
    """
    Enumeration of datatypes possible for PropertyTypes
    """

    UInt32 = sparkplug_b_pb2.UInt32
    Uint64 = sparkplug_b_pb2.UInt64
    Float = sparkplug_b_pb2.Float
    Double = sparkplug_b_pb2.Double
    Boolean = sparkplug_b_pb2.Boolean
    String = sparkplug_b_pb2.String
    PropertySet = sparkplug_b_pb2.PropertySet
    PropertySetList = sparkplug_b_pb2.PropertySetList


class SPBMetadata(graphene.ObjectType):
    """
    Model of Metadata in SPBv1.0 payload
    """

    # pylint: disable=too-few-public-methods
    is_multi_part = graphene.Boolean()
    content_type = graphene.String()
    size = graphene.Int()
    seq = graphene.Int()
    file_name = graphene.String()
    file_type = graphene.String()
    md5 = graphene.String()
    description = graphene.String()


class SPBPropertyValue(graphene.ObjectType):
    """
    Model of PropertyValue in SPBv1.0 payload
    """

    is_null = graphene.Boolean()
    datatype = graphene.NonNull(graphene.Int)
    value = graphene.Field(graphene.Union, resolver="resolve_value")

    def resolve_value(self, info):  # noqa: ARG002
        """
        Resolve value based on type
        """
        datatype: int = self.datatype
        if self.is_null:
            return None
        match datatype:
            case sparkplug_b_pb2.UInt32:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.UInt64:
                return graphene.BigInt(value=int(self.value))
            case sparkplug_b_pb2.Float:
                return graphene.Float(value=float(self.value))
            case sparkplug_b_pb2.Double:
                return graphene.Float(value=float(self.value))
            case sparkplug_b_pb2.String:
                return graphene.String(value=str(self.value))
            case sparkplug_b_pb2.PropertySet:
                return SPBPropertySet(value=self.value)
            case sparkplug_b_pb2.PropertySetList:
                return graphene.List(SPBPropertySet(value=self.value))


class SPBPropertySet(graphene.ObjectType):
    """
    Model of PropertySet in SPBv1.0 payload
    """

    # pylint: disable=too-few-public-methods
    keys: graphene.List = graphene.List(graphene.String)
    values: graphene.List = graphene.List("SPBPropertyValue")


# GraphQL type for Payload -> DataSetValue
class SPBDataSetValue(graphene.Union):
    """
    Model of DataSet->Row->Value in SPBv1.0 payload
    """

    class Meta:
        """
        Dynamically set the type of dataset value
        """

        # pylint: disable=too-few-public-methods
        types = (graphene.Int, graphene.Float, graphene.Boolean,
                 graphene.String)


class SPBDataSetRow(graphene.ObjectType):
    """
    Model of DataSet->Row in SPBv1.0 payload
    """

    # pylint: disable=too-few-public-methods
    elements = graphene.List(SPBDataSetValue)


class SPBDataSet(graphene.ObjectType):
    """
    Model of DataSet in SPBv1.0 payload
    """

    # pylint: disable=too-few-public-methods
    num_of_columns: graphene.Int = graphene.Int()
    columns: graphene.Int = graphene.Int()
    # maps to spb data types
    types: graphene.List = graphene.List(graphene.Int)
    rows: graphene.List = graphene.List(SPBDataSetRow)


class SPBMetric(graphene.ObjectType):
    """
    Model of a SPB Metric, which is within a SPBNode
    """

    # pylint: disable=too-few-public-methods
    name = graphene.NonNull(graphene.String)
    alias = graphene.Int()
    timestamp = graphene.NonNull(graphene.BigInt)
    datatype = graphene.NonNull(SPBDataTypeEnum)
    is_historical = graphene.Boolean()
    is_transient = graphene.Boolean()
    is_null = graphene.Boolean()
    metadata = SPBMetadata()
    properties = SPBPropertySet()
    value = graphene.Field(graphene.Union, resolver="resolve_value")

    def resolve_value(self, info):  # noqa: ARG002
        """
        Resolve value based on datatype
        """
        # pylint: disable=too-many-return-statements
        # pylint: disable=unused-argument

        # Logic to dynamically resolve 'value' based on 'datatype'

        datatype: int = self.datatype
        if self.is_null:
            return None
        match datatype:
            case sparkplug_b_pb2.Int8:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.Int16:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.Int32:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.Int64:
                return graphene.BigInt(value=int(self.value))
            case sparkplug_b_pb2.UInt8:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.UInt16:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.UInt32:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.UInt64:
                return graphene.BigInt(value=int(self.value))
            case sparkplug_b_pb2.Float:
                return graphene.Float(value=float(self.value))
            case sparkplug_b_pb2.Double:
                return graphene.Float(value=float(self.value))
            case sparkplug_b_pb2.Boolean:
                return graphene.Boolean(value=bool(self.value))
            case sparkplug_b_pb2.String:
                return graphene.String(value=str(self.value))
            case sparkplug_b_pb2.DateTime:
                return graphene.BigInt(value=int(self.value))
            case sparkplug_b_pb2.Text:
                return graphene.String(value=str(self.value))
            case sparkplug_b_pb2.UUID:
                return graphene.UUID(value=str(self.value))
            case sparkplug_b_pb2.Bytes:
                return graphene.Base64(value=bytes(self.value))
            case sparkplug_b_pb2.File:
                return graphene.Base64(value=bytes(self.value))
            case sparkplug_b_pb2.DataSet:
                return SPBDataSet(value=self.value)
            case sparkplug_b_pb2.Template:
                return SPBTemplate(value=self.value)
            case _:
                LOGGER.error("Invalid type: %s.\n Trying Value: %s as String",
                             str(self.datatype),
                             str(self.value),
                             stack_info=True,
                             exc_info=True)
                return graphene.String(value=str(self.value))


class SPBTemplateParameter:
    """
    Model of a SPB Template Parameter,
    """

    # pylint: disable=too-few-public-methods
    name = graphene.String()
    datatype = graphene.NonNull(SPBDataTypeEnum)
    value = graphene.Field(graphene.Union, resolver="resolve_value")

    def resolve_value(self, info):  # noqa: ARG002
        """
        Resolve value based on datatype
        """
        # pylint: disable=too-many-return-statements
        # pylint: disable=unused-argument

        # Logic to dynamically resolve 'value' based on 'datatype'

        datatype: int = self.datatype
        match datatype:
            case sparkplug_b_pb2.Int8:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.Int16:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.Int32:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.Int64:
                return graphene.BigInt(value=int(self.value))
            case sparkplug_b_pb2.UInt8:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.UInt16:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.UInt32:
                return graphene.Int(value=int(self.value))
            case sparkplug_b_pb2.UInt64:
                return graphene.BigInt(value=int(self.value))
            case sparkplug_b_pb2.Float:
                return graphene.Float(value=float(self.value))
            case sparkplug_b_pb2.Double:
                return graphene.Float(value=float(self.value))
            case sparkplug_b_pb2.Boolean:
                return graphene.Boolean(value=bool(self.value))
            case sparkplug_b_pb2.String:
                return graphene.String(value=str(self.value))
            case sparkplug_b_pb2.DateTime:
                return graphene.BigInt(value=int(self.value))
            case sparkplug_b_pb2.Text:
                return graphene.String(value=str(self.value))
            case sparkplug_b_pb2.UUID:
                return graphene.UUID(value=str(self.value))
            case sparkplug_b_pb2.Bytes:
                return graphene.Base64(value=bytes(self.value))
            case sparkplug_b_pb2.File:
                return graphene.Base64(value=bytes(self.value))
            case sparkplug_b_pb2.DataSet:
                return SPBDataSet(value=self.value)
            case sparkplug_b_pb2.Template:
                return SPBTemplate(value=self.value)
            case _:
                LOGGER.error("Invalid type: %s.\n Trying Value: %s as String",
                             str(self.datatype),
                             str(self.value),
                             stack_info=True,
                             exc_info=True)
                return graphene.String(value=str(self.value))


class SPBTemplate(graphene.ObjectType):
    """
    Model of Template in SPBv1.0 payload
    """

    # pylint: disable=too-few-public-methods
    version = graphene.String()
    metrics = graphene.List(SPBMetric)
    parameters = graphene.List("SPBTemplateParameter")
    template_ref = graphene.String()
    is_definition = graphene.Boolean()


class SPBNode(graphene.ObjectType):
    """
    Model of a SPB Node,
    """

    # pylint: disable=too-few-public-methods
    # Name of the node. Would also be the leaf of the topic hierarchy
    name: graphene.String = graphene.String()

    # Type of the Node depending on the topic hierarchy in accordance with spBv1.0 specification
    # ["spBv1_0", "GROUP", "MESSAGE_TYPE", "EDGE_NODE", "DEVICE"]
    node_type: graphene.String = graphene.String()

    # Fully qualified path of the namespace including current name
    # Usually maps to the topic where multiple messages were published
    # e.g. spBv1.0/[GROUP]/[MESSAGE_TYPE]/[EDGE_NODE]/[DEVICE]
    namespace: graphene.String = graphene.String()

    # Merged Composite of all Metric published to this node

    # Timestamp of when this node was last modified
    timestamp: graphene.BigInt = graphene.BigInt()

    # UUID for this message
    uuid: graphene.UUID = graphene.UUID()
    # Metrics published to the spBv1.0 namespace using protobuf payloads
    metrics: graphene.List = graphene.List(SPBMetric)
    # Properties / message payload for non protobuf messages e.g. STATE
    properties: graphene.JSONString = graphene.JSONString()
    # sequence
    seq: graphene.Int = graphene.Int()


class HistoricalUNSNode(graphene.ObjectType):
    """
    Model of a UNS Node,
    """
    # Fully qualified path of the namespace including current name
    # Usually maps to the topic where multiple messages were published e.g. ent1/fac1/area5
    namespace: graphene.String = graphene.NonNull(graphene.String)

    # The payload which was publishes
    payload: graphene.JSONString = graphene.JSONString()

    # Timestamp of when this payload was publishes
    timestamp: graphene.BigInt = graphene.BigInt()


class Node(graphene.Union):

    class Meta:
        types = (UNSNode, SPBNode, HistoricalUNSNode)

    @classmethod
    def resolve_type(cls, instance, info):  # noqa: ARG003
        if instance["type"] == "UnifiedNameSpace":
            return UNSNode
        if instance["type"] == "SparkplugBv1.0":
            return SPBNode
