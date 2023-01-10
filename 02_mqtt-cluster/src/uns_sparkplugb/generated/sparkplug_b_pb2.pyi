from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf.internal import python_message as _python_message
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

Boolean: DataType
BooleanArray: DataType
Bytes: DataType
DESCRIPTOR: _descriptor.FileDescriptor
DataSet: DataType
DateTime: DataType
DateTimeArray: DataType
Double: DataType
DoubleArray: DataType
File: DataType
Float: DataType
FloatArray: DataType
Int16: DataType
Int16Array: DataType
Int32: DataType
Int32Array: DataType
Int64: DataType
Int64Array: DataType
Int8: DataType
Int8Array: DataType
PropertySet: DataType
PropertySetList: DataType
String: DataType
StringArray: DataType
Template: DataType
Text: DataType
UInt16: DataType
UInt16Array: DataType
UInt32: DataType
UInt32Array: DataType
UInt64: DataType
UInt64Array: DataType
UInt8: DataType
UInt8Array: DataType
UUID: DataType
Unknown: DataType

class Payload(_message.Message):
    __slots__ = ["body", "metrics", "seq", "timestamp", "uuid"]
    class DataSet(_message.Message):
        __slots__ = ["columns", "num_of_columns", "rows", "types"]
        class DataSetValue(_message.Message):
            __slots__ = ["boolean_value", "double_value", "extension_value", "float_value", "int_value", "long_value", "string_value"]
            class DataSetValueExtension(_message.Message):
                __slots__ = []
                Extensions: _python_message._ExtensionDict
                def __init__(self) -> None: ...
            BOOLEAN_VALUE_FIELD_NUMBER: _ClassVar[int]
            DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
            EXTENSION_VALUE_FIELD_NUMBER: _ClassVar[int]
            FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
            INT_VALUE_FIELD_NUMBER: _ClassVar[int]
            LONG_VALUE_FIELD_NUMBER: _ClassVar[int]
            STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
            boolean_value: bool
            double_value: float
            extension_value: Payload.DataSet.DataSetValue.DataSetValueExtension
            float_value: float
            int_value: int
            long_value: int
            string_value: str
            def __init__(self, int_value: _Optional[int] = ..., long_value: _Optional[int] = ..., float_value: _Optional[float] = ..., double_value: _Optional[float] = ..., boolean_value: bool = ..., string_value: _Optional[str] = ..., extension_value: _Optional[_Union[Payload.DataSet.DataSetValue.DataSetValueExtension, _Mapping]] = ...) -> None: ...
        class Row(_message.Message):
            __slots__ = ["elements"]
            ELEMENTS_FIELD_NUMBER: _ClassVar[int]
            Extensions: _python_message._ExtensionDict
            elements: _containers.RepeatedCompositeFieldContainer[Payload.DataSet.DataSetValue]
            def __init__(self, elements: _Optional[_Iterable[_Union[Payload.DataSet.DataSetValue, _Mapping]]] = ...) -> None: ...
        COLUMNS_FIELD_NUMBER: _ClassVar[int]
        Extensions: _python_message._ExtensionDict
        NUM_OF_COLUMNS_FIELD_NUMBER: _ClassVar[int]
        ROWS_FIELD_NUMBER: _ClassVar[int]
        TYPES_FIELD_NUMBER: _ClassVar[int]
        columns: _containers.RepeatedScalarFieldContainer[str]
        num_of_columns: int
        rows: _containers.RepeatedCompositeFieldContainer[Payload.DataSet.Row]
        types: _containers.RepeatedScalarFieldContainer[int]
        def __init__(self, num_of_columns: _Optional[int] = ..., columns: _Optional[_Iterable[str]] = ..., types: _Optional[_Iterable[int]] = ..., rows: _Optional[_Iterable[_Union[Payload.DataSet.Row, _Mapping]]] = ...) -> None: ...
    class MetaData(_message.Message):
        __slots__ = ["content_type", "description", "file_name", "file_type", "is_multi_part", "md5", "seq", "size"]
        CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        Extensions: _python_message._ExtensionDict
        FILE_NAME_FIELD_NUMBER: _ClassVar[int]
        FILE_TYPE_FIELD_NUMBER: _ClassVar[int]
        IS_MULTI_PART_FIELD_NUMBER: _ClassVar[int]
        MD5_FIELD_NUMBER: _ClassVar[int]
        SEQ_FIELD_NUMBER: _ClassVar[int]
        SIZE_FIELD_NUMBER: _ClassVar[int]
        content_type: str
        description: str
        file_name: str
        file_type: str
        is_multi_part: bool
        md5: str
        seq: int
        size: int
        def __init__(self, is_multi_part: bool = ..., content_type: _Optional[str] = ..., size: _Optional[int] = ..., seq: _Optional[int] = ..., file_name: _Optional[str] = ..., file_type: _Optional[str] = ..., md5: _Optional[str] = ..., description: _Optional[str] = ...) -> None: ...
    class Metric(_message.Message):
        __slots__ = ["alias", "boolean_value", "bytes_value", "dataset_value", "datatype", "double_value", "extension_value", "float_value", "int_value", "is_historical", "is_null", "is_transient", "long_value", "metadata", "name", "properties", "string_value", "template_value", "timestamp"]
        class MetricValueExtension(_message.Message):
            __slots__ = []
            Extensions: _python_message._ExtensionDict
            def __init__(self) -> None: ...
        ALIAS_FIELD_NUMBER: _ClassVar[int]
        BOOLEAN_VALUE_FIELD_NUMBER: _ClassVar[int]
        BYTES_VALUE_FIELD_NUMBER: _ClassVar[int]
        DATASET_VALUE_FIELD_NUMBER: _ClassVar[int]
        DATATYPE_FIELD_NUMBER: _ClassVar[int]
        DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
        EXTENSION_VALUE_FIELD_NUMBER: _ClassVar[int]
        FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
        INT_VALUE_FIELD_NUMBER: _ClassVar[int]
        IS_HISTORICAL_FIELD_NUMBER: _ClassVar[int]
        IS_NULL_FIELD_NUMBER: _ClassVar[int]
        IS_TRANSIENT_FIELD_NUMBER: _ClassVar[int]
        LONG_VALUE_FIELD_NUMBER: _ClassVar[int]
        METADATA_FIELD_NUMBER: _ClassVar[int]
        NAME_FIELD_NUMBER: _ClassVar[int]
        PROPERTIES_FIELD_NUMBER: _ClassVar[int]
        STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
        TEMPLATE_VALUE_FIELD_NUMBER: _ClassVar[int]
        TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
        alias: int
        boolean_value: bool
        bytes_value: bytes
        dataset_value: Payload.DataSet
        datatype: int
        double_value: float
        extension_value: Payload.Metric.MetricValueExtension
        float_value: float
        int_value: int
        is_historical: bool
        is_null: bool
        is_transient: bool
        long_value: int
        metadata: Payload.MetaData
        name: str
        properties: Payload.PropertySet
        string_value: str
        template_value: Payload.Template
        timestamp: int
        def __init__(self, name: _Optional[str] = ..., alias: _Optional[int] = ..., timestamp: _Optional[int] = ..., datatype: _Optional[int] = ..., is_historical: bool = ..., is_transient: bool = ..., is_null: bool = ..., metadata: _Optional[_Union[Payload.MetaData, _Mapping]] = ..., properties: _Optional[_Union[Payload.PropertySet, _Mapping]] = ..., int_value: _Optional[int] = ..., long_value: _Optional[int] = ..., float_value: _Optional[float] = ..., double_value: _Optional[float] = ..., boolean_value: bool = ..., string_value: _Optional[str] = ..., bytes_value: _Optional[bytes] = ..., dataset_value: _Optional[_Union[Payload.DataSet, _Mapping]] = ..., template_value: _Optional[_Union[Payload.Template, _Mapping]] = ..., extension_value: _Optional[_Union[Payload.Metric.MetricValueExtension, _Mapping]] = ...) -> None: ...
    class PropertySet(_message.Message):
        __slots__ = ["keys", "values"]
        Extensions: _python_message._ExtensionDict
        KEYS_FIELD_NUMBER: _ClassVar[int]
        VALUES_FIELD_NUMBER: _ClassVar[int]
        keys: _containers.RepeatedScalarFieldContainer[str]
        values: _containers.RepeatedCompositeFieldContainer[Payload.PropertyValue]
        def __init__(self, keys: _Optional[_Iterable[str]] = ..., values: _Optional[_Iterable[_Union[Payload.PropertyValue, _Mapping]]] = ...) -> None: ...
    class PropertySetList(_message.Message):
        __slots__ = ["propertyset"]
        Extensions: _python_message._ExtensionDict
        PROPERTYSET_FIELD_NUMBER: _ClassVar[int]
        propertyset: _containers.RepeatedCompositeFieldContainer[Payload.PropertySet]
        def __init__(self, propertyset: _Optional[_Iterable[_Union[Payload.PropertySet, _Mapping]]] = ...) -> None: ...
    class PropertyValue(_message.Message):
        __slots__ = ["boolean_value", "double_value", "extension_value", "float_value", "int_value", "is_null", "long_value", "propertyset_value", "propertysets_value", "string_value", "type"]
        class PropertyValueExtension(_message.Message):
            __slots__ = []
            Extensions: _python_message._ExtensionDict
            def __init__(self) -> None: ...
        BOOLEAN_VALUE_FIELD_NUMBER: _ClassVar[int]
        DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
        EXTENSION_VALUE_FIELD_NUMBER: _ClassVar[int]
        FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
        INT_VALUE_FIELD_NUMBER: _ClassVar[int]
        IS_NULL_FIELD_NUMBER: _ClassVar[int]
        LONG_VALUE_FIELD_NUMBER: _ClassVar[int]
        PROPERTYSETS_VALUE_FIELD_NUMBER: _ClassVar[int]
        PROPERTYSET_VALUE_FIELD_NUMBER: _ClassVar[int]
        STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
        TYPE_FIELD_NUMBER: _ClassVar[int]
        boolean_value: bool
        double_value: float
        extension_value: Payload.PropertyValue.PropertyValueExtension
        float_value: float
        int_value: int
        is_null: bool
        long_value: int
        propertyset_value: Payload.PropertySet
        propertysets_value: Payload.PropertySetList
        string_value: str
        type: int
        def __init__(self, type: _Optional[int] = ..., is_null: bool = ..., int_value: _Optional[int] = ..., long_value: _Optional[int] = ..., float_value: _Optional[float] = ..., double_value: _Optional[float] = ..., boolean_value: bool = ..., string_value: _Optional[str] = ..., propertyset_value: _Optional[_Union[Payload.PropertySet, _Mapping]] = ..., propertysets_value: _Optional[_Union[Payload.PropertySetList, _Mapping]] = ..., extension_value: _Optional[_Union[Payload.PropertyValue.PropertyValueExtension, _Mapping]] = ...) -> None: ...
    class Template(_message.Message):
        __slots__ = ["is_definition", "metrics", "parameters", "template_ref", "version"]
        class Parameter(_message.Message):
            __slots__ = ["boolean_value", "double_value", "extension_value", "float_value", "int_value", "long_value", "name", "string_value", "type"]
            class ParameterValueExtension(_message.Message):
                __slots__ = []
                Extensions: _python_message._ExtensionDict
                def __init__(self) -> None: ...
            BOOLEAN_VALUE_FIELD_NUMBER: _ClassVar[int]
            DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
            EXTENSION_VALUE_FIELD_NUMBER: _ClassVar[int]
            FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
            INT_VALUE_FIELD_NUMBER: _ClassVar[int]
            LONG_VALUE_FIELD_NUMBER: _ClassVar[int]
            NAME_FIELD_NUMBER: _ClassVar[int]
            STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
            TYPE_FIELD_NUMBER: _ClassVar[int]
            boolean_value: bool
            double_value: float
            extension_value: Payload.Template.Parameter.ParameterValueExtension
            float_value: float
            int_value: int
            long_value: int
            name: str
            string_value: str
            type: int
            def __init__(self, name: _Optional[str] = ..., type: _Optional[int] = ..., int_value: _Optional[int] = ..., long_value: _Optional[int] = ..., float_value: _Optional[float] = ..., double_value: _Optional[float] = ..., boolean_value: bool = ..., string_value: _Optional[str] = ..., extension_value: _Optional[_Union[Payload.Template.Parameter.ParameterValueExtension, _Mapping]] = ...) -> None: ...
        Extensions: _python_message._ExtensionDict
        IS_DEFINITION_FIELD_NUMBER: _ClassVar[int]
        METRICS_FIELD_NUMBER: _ClassVar[int]
        PARAMETERS_FIELD_NUMBER: _ClassVar[int]
        TEMPLATE_REF_FIELD_NUMBER: _ClassVar[int]
        VERSION_FIELD_NUMBER: _ClassVar[int]
        is_definition: bool
        metrics: _containers.RepeatedCompositeFieldContainer[Payload.Metric]
        parameters: _containers.RepeatedCompositeFieldContainer[Payload.Template.Parameter]
        template_ref: str
        version: str
        def __init__(self, version: _Optional[str] = ..., metrics: _Optional[_Iterable[_Union[Payload.Metric, _Mapping]]] = ..., parameters: _Optional[_Iterable[_Union[Payload.Template.Parameter, _Mapping]]] = ..., template_ref: _Optional[str] = ..., is_definition: bool = ...) -> None: ...
    BODY_FIELD_NUMBER: _ClassVar[int]
    Extensions: _python_message._ExtensionDict
    METRICS_FIELD_NUMBER: _ClassVar[int]
    SEQ_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    UUID_FIELD_NUMBER: _ClassVar[int]
    body: bytes
    metrics: _containers.RepeatedCompositeFieldContainer[Payload.Metric]
    seq: int
    timestamp: int
    uuid: str
    def __init__(self, timestamp: _Optional[int] = ..., metrics: _Optional[_Iterable[_Union[Payload.Metric, _Mapping]]] = ..., seq: _Optional[int] = ..., uuid: _Optional[str] = ..., body: _Optional[bytes] = ...) -> None: ...

class DataType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
