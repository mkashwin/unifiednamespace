"""
Helper class to parse & create SparkplugB messages
@see Tahu Project{https://github.com/eclipse/tahu/blob/master/python/core/sparkplug_b.py}
Extending that based on the specs in
https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf
"""
import logging
import struct
from enum import Enum, StrEnum, unique
from typing import Literal

from uns_sparkplugb.generated import sparkplug_b_pb2
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload

LOGGER = logging.getLogger(__name__)


@unique
class SPBValueFieldName(StrEnum):
    INT = "int_value"
    LONG = "long_value"
    FLOAT = "float_value"
    DOUBLE = "double_value"
    STRING = "string_value"
    BYTES = "bytes_value"
    BOOLEAN = "boolean_value"
    TEMPLATE = "template_value"
    DATASET = "dataset_value"
    PROPERTY_SET = "propertyset_value"
    PROPERTY_SET_LIST = "propertysets_value"


class _SPBAbstractDataTypes(int, Enum):
    def __new__(cls, value: int, field_name: str, add_value_function):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.field_name = field_name
        obj._name_ = str(field_name)
        obj.add_value_function = add_value_function
        return obj

    def get_field_name(self):
        return self.field_name

    def set_value_in_sparkplug(self, value, spb_object):
        self.add_value_function(value=value, spb_object=spb_object)

    @staticmethod
    def _combine_enums(name: str, *enums):
        """
        Private Utility function to merge Enums because Enums cannot be extended
        """
        # combined_enum = _SPBAbstractDataTypes(name, {item.name: item.value for enum in enums for item in enum})
        combined_enum_members = {}
        for enum in enums:
            for item in enum:
                combined_enum_members[item.name] = (item.value, item.field_name, item.add_value_function)

        combined_enum = _SPBAbstractDataTypes(name, combined_enum_members)
        return combined_enum


class _SetValueInSparkPlugObject:
    """
    Class encapsulating the setting logic for the values depending on datatype
    """

    @staticmethod
    def unknown_value(
        value,
        spb_object: Payload.Metric | Payload.PropertyValue | Payload.DataSet.DataSetValue | Payload.Template.Parameter,
    ):
        """
        Helper method handling values of unknown type in metric

        Parameters
        ----------
        datatype: int but not matching the sparkplugB specifications for data types
        value: value to stored. will be ignored
        metric: Metric object/ PropertyValue/ DataSetValue/ Template.Parameter
        """

        match type(spb_object):
            case Payload.Metric:
                spb_object.datatype = sparkplug_b_pb2.Unknown  # attribute name is different for Metric
            case Payload.PropertyValue | Payload.Template.Parameter:
                spb_object.type = sparkplug_b_pb2.Unknown
            case Payload.DataSet.DataSetValue:
                pass  # object doesn't have type attribute

        LOGGER.error(
            "Invalid datatype.\n Value: %s not added to %s", str(value), str(spb_object), stack_info=True, exc_info=True
        )

    @staticmethod
    def int_value(
        value: int,
        spb_object: Payload.Metric | Payload.PropertyValue | Payload.DataSet.DataSetValue | Payload.Template.Parameter,
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
                    UInt: 0
        """
        if value is not None and value < 0:
            value = value + (0 if factor == 0 else 2**factor)
        spb_object.int_value = value
        return value

    @staticmethod
    def long_value(
        value: int,
        spb_object: Payload.Metric | Payload.PropertyValue | Payload.DataSet.DataSetValue | Payload.Template.Parameter,
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
        spb_object.long_value = value
        return value

    @staticmethod
    def boolean_array(
        values: list[bool],
        spb_object: Payload.Metric,
    ) -> bytes:
        # Calculate the number of packed bytes required
        packed_bytes_count = (len(values) + 7) // 8
        # Create a byte array to hold the packed bits
        packed_bytes = bytearray(packed_bytes_count)

        # Iterate through the boolean array
        for i, value in enumerate(values):
            # Calculate the bit position in the packed byte
            bit_position = 7 - (i % 8)
            # Set the bit in the appropriate position within the byte
            packed_bytes[i // 8] |= value << bit_position

        # Prepend the packed bytes with a 4-byte integer representing the number of boolean values
        bytes_value = struct.pack("<I", len(values)) + packed_bytes
        spb_object.bytes_value = bytes_value
        return bytes_value

    @staticmethod
    def string_array(
        values: list[str],
        spb_object: Payload.Metric,
    ) -> bytes:
        # convert strings to bytes and encode to hex
        hex_string_array = [string.encode().hex() for string in values]
        # convert hex string to bytes and terminate with null character
        packed_bytes = [bytes(hex_string, "utf-8") + b"\x00" for hex_string in hex_string_array]
        # joining the bytes to form a null terminated byte string
        bytes_value = b"".join(packed_bytes)
        spb_object.bytes_value = bytes_value
        return bytes_value

    @staticmethod
    def raise_in_lambda(ex):
        """
        Hack to raise exceptions in lambda
        """
        raise ex


@unique
class SPBBasicDataTypes(_SPBAbstractDataTypes):
    """
    Enumeration of basic datatypes as per sparkplugB specifications
    Enhancing the ENUM with logic to set value in the right attribute of the SparkplugB Object
    Each of the Datatype ENUMs has the following
    - The datatype field
    - the name of the value field under the key "value_field"
    - a lambda function under key "add_value" which has the logic of setting the value to the  "value_field"
      for the provided SparkplugB Object
    The SparkplugB objects must be of type
        - Payload.Metric
        - Payload.PropertyValue
        - Payload.DataSet.DataSetValue
        - Payload.Template.Parameter

    """

    Unknown = (
        sparkplug_b_pb2.Unknown,
        None,
        lambda spb_object, value: _SetValueInSparkPlugObject.unknown_value(spb_object=spb_object, value=value),
    )

    Int8 = (
        sparkplug_b_pb2.Int8,
        SPBValueFieldName.INT,
        lambda spb_object, value: _SetValueInSparkPlugObject.int_value(value=value, spb_object=spb_object, factor=8),
    )

    Int16 = (
        sparkplug_b_pb2.Int16,
        SPBValueFieldName.INT,
        lambda spb_object, value: _SetValueInSparkPlugObject.int_value(value=value, spb_object=spb_object, factor=16),
    )

    Int32 = (
        sparkplug_b_pb2.Int32,
        SPBValueFieldName.INT,
        lambda spb_object, value: _SetValueInSparkPlugObject.int_value(value=value, spb_object=spb_object, factor=32),
    )
    Int64 = (
        sparkplug_b_pb2.Int64,
        SPBValueFieldName.LONG,
        lambda spb_object, value: _SetValueInSparkPlugObject.long_value(value=value, spb_object=spb_object, factor=64),
    )

    UInt8 = (
        sparkplug_b_pb2.UInt8,
        SPBValueFieldName.INT,
        lambda spb_object, value: _SetValueInSparkPlugObject.int_value(value=value, spb_object=spb_object, factor=0),
    )
    UInt16 = (
        sparkplug_b_pb2.UInt16,
        SPBValueFieldName.INT,
        lambda spb_object, value: _SetValueInSparkPlugObject.int_value(value=value, spb_object=spb_object, factor=0),
    )
    UInt32 = (
        sparkplug_b_pb2.UInt32,
        SPBValueFieldName.INT,
        lambda spb_object, value: _SetValueInSparkPlugObject.int_value(value=value, spb_object=spb_object, factor=0),
    )
    UInt64 = (
        sparkplug_b_pb2.UInt64,
        SPBValueFieldName.LONG,
        lambda spb_object, value: _SetValueInSparkPlugObject.long_value(value=value, spb_object=spb_object, factor=0),
    )
    Float = (
        sparkplug_b_pb2.Float,
        SPBValueFieldName.FLOAT,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.FLOAT, float(value)),
    )
    Double = (
        sparkplug_b_pb2.Double,
        SPBValueFieldName.DOUBLE,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.DOUBLE, float(value)),
    )
    Boolean = (
        sparkplug_b_pb2.Boolean,
        SPBValueFieldName.BOOLEAN,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BOOLEAN, bool(value)),
    )
    String = (
        sparkplug_b_pb2.String,
        SPBValueFieldName.STRING,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.STRING, str(value)),
    )
    DateTime = (
        sparkplug_b_pb2.DateTime,
        SPBValueFieldName.LONG,
        lambda spb_object, value: _SetValueInSparkPlugObject.long_value(value=value, spb_object=spb_object, factor=64),
    )
    Text = (
        sparkplug_b_pb2.Text,
        SPBValueFieldName.STRING,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.STRING, str(value)),
    )


@unique
class SPBAdditionalDataTypes(_SPBAbstractDataTypes):
    """
    Enumeration of additional datatypes as per sparkplugB specifications
    Enhancing the ENUM with logic to set value in the right attribute of the SparkplugB Object
    Each of the Datatype ENUMs has the following
    - The datatype field
    - the name of the value field under the key "value_field"
    - a lambda function under key "add_value" which has the logic of setting the value to the  "value_field"
      for the provided SparkplugB Object
    """

    UUID = (
        sparkplug_b_pb2.UUID,
        SPBValueFieldName.STRING,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.STRING, str(value)),
    )

    DataSet = (
        sparkplug_b_pb2.DataSet,
        SPBValueFieldName.DATASET,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.DATASET, value)
        if isinstance(value, Payload.DataSet)
        else _SetValueInSparkPlugObject.raise_in_lambda(
            ValueError(f"Expecting object of type Payload.DataSet, got of type {type(value)}")
        ),
    )
    Bytes = (
        sparkplug_b_pb2.Bytes,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, value),
    )
    File = (
        sparkplug_b_pb2.File,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, value),
    )
    Template = (
        sparkplug_b_pb2.Template,
        SPBValueFieldName.TEMPLATE,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.TEMPLATE, value)
        if isinstance(value, Payload.Template)
        else _SetValueInSparkPlugObject.raise_in_lambda(
            ValueError(f"Expecting object of type Payload.DataSet, got of type {type(value)}")
        ),
    )


@unique
class SPBArrayDataTypes(_SPBAbstractDataTypes):
    """

    Enhancing the ENUM with logic to set value in the right attribute of the SparkplugB Object
    Refer Section 6.4.16 https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf
    and https://docs.python.org/3/library/struct.html

    Each of the Datatype ENUMs has the following
    - The datatype field
    - the name of the value field under the key "value_field"
    - a lambda function under key "add_value" which has the logic of setting the value to the  "value_field"
      for the provided SparkplugB Object


    """

    Int8Array = (
        sparkplug_b_pb2.Int8Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(
            spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}b", *value)
        ),  # Format "b" maps to  "signed char" C Type and integer Python type
    )

    Int16Array = (
        sparkplug_b_pb2.Int16Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(
            spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}h", *value)
        ),  # Format "h" maps to  "short" C Type and integer Python type
    )

    Int32Array = (
        sparkplug_b_pb2.Int32Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}i", *value)),
        # Format "i" maps to  "int" C Type and integer Python type
    )

    Int64Array = (
        sparkplug_b_pb2.Int64Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}q", *value)),
        # Format "q" maps to  "long long" C Type and integer Python type
    )

    UInt8Array = (
        sparkplug_b_pb2.UInt8Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}B", *value)),
        # Format "B" maps to  "unsigned char" C Type and integer Python type
    )

    UInt16Array = (
        sparkplug_b_pb2.UInt16Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}H", *value)),
        # Format "H" maps to  "unsigned short" C Type and integer Python type
    )

    UInt32Array = (
        sparkplug_b_pb2.UInt32Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}I", *value)),
        # Format "I" maps to  "unsigned int" C Type and integer Python type
    )

    UInt64Array = (
        sparkplug_b_pb2.UInt64Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}Q", *value)),
        # Format "Q" maps to  "unsigned long long" C Type and integer Python type
    )

    FloatArray = (
        sparkplug_b_pb2.FloatArray,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}f", *value)),
        # Format "f" maps to  "float" C Type and float Python type
    )

    DoubleArray = (
        sparkplug_b_pb2.DoubleArray,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}d", *value)),
        # Format "d" maps to  "double" C Type and float Python type
    )

    BooleanArray = (
        sparkplug_b_pb2.BooleanArray,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: _SetValueInSparkPlugObject.boolean_array(values=value, spb_object=spb_object),
        # @FIXME
    )
    StringArray = (
        sparkplug_b_pb2.StringArray,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: _SetValueInSparkPlugObject.string_array(values=value, spb_object=spb_object),
    )

    DateTimeArray = (
        sparkplug_b_pb2.DateTimeArray,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}q", *value)),
    )  # Format "q" maps to  "long long" C Type and integer Python type.since Datetime is a long value


# Enumeration of datatypes possible in a Metric.
# Combine  basic datatypes, additional datatypes and array datatypes
SPBMetricDataTypes: Enum = _SPBAbstractDataTypes._combine_enums(
    "SPBMetricDataTypes", SPBBasicDataTypes, SPBAdditionalDataTypes, SPBArrayDataTypes
)


# Enumeration of datatypes possible for PropertyTypes
# Extend basic datatypes with PropertySet & PropertySetList types
SPBPropertyValueTypes = _SPBAbstractDataTypes._combine_enums(
    "SPBPropertyValueTypes",
    SPBBasicDataTypes,
    _SPBAbstractDataTypes(
        "SPBPropertySet",
        {
            "PropertySet": (
                sparkplug_b_pb2.PropertySet,  # @FIXME need to handle PropertySet
                SPBValueFieldName.PROPERTY_SET,
                lambda spb_object, value: setattr(spb_object, SPBValueFieldName.PROPERTY_SET, value)
                if isinstance(value, Payload.PropertySet)
                else _SetValueInSparkPlugObject.raise_in_lambda(
                    ValueError(f"Expecting object of type Payload.PropertySet, got of type {type(value)}")
                ),
            )
        },
    ),
    _SPBAbstractDataTypes(
        "SPBPropertySetList",
        {
            "PropertySetList": (
                sparkplug_b_pb2.PropertySetList,  # @FIXME need to handle PropertySet
                SPBValueFieldName.PROPERTY_SET_LIST,
                lambda spb_object, value: setattr(spb_object, SPBValueFieldName.PROPERTY_SET_LIST, value)
                if isinstance(value, Payload.PropertySetList)
                else _SetValueInSparkPlugObject.raise_in_lambda(
                    ValueError(f"Expecting object of type Payload.PropertySetList, got of type {type(value)}")
                ),
            )
        },
    ),
)


# Enumeration of datatypes possible for DataSetValue
SPBDataSetDataTypes = SPBBasicDataTypes
