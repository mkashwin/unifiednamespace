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
    def __new__(cls, value: int, field_name: SPBValueFieldName, add_value_function=None, get_value_function=None):
        """
        Override creation of subclass enum
        Added meta data to the value type
        - field_name: maps to proto specs as one of the SPBValueFieldName types
        - add_value_function: to add data to the sparkplugB object
                              function take these two parameters
                              - value -> what needs to be stored,
                              - spb_object -> the object in which it is to be stored
        - get_value_function: to retrieve data from the sparkplugB object
                              function take only one parameter
                              - spb_object -> the object in which the value is to be extracted
        """
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.field_name = field_name
        obj._name_ = str(field_name)
        if add_value_function is None:
            obj.add_value_function = lambda spb_object, value: setattr(spb_object, obj.field_name, value)
        else:
            obj.add_value_function = add_value_function

        if get_value_function is None:
            obj.get_value_function = lambda spb_object: getattr(spb_object, obj.field_name)
        else:
            obj.get_value_function = get_value_function

        return obj

    def get_field_name(self):
        return self.field_name

    def set_value_in_sparkplug(self, value, spb_object):
        """
        Set the value in the correct slot of the spb_object
        spb_object is one of type
            - Payload.Metric
            - Payload.PropertyValue
            - Payload.DataSet.DataSetValue
            - Payload.Template.Parameter
        """
        self.add_value_function(value=value, spb_object=spb_object)

    def get_value_from_sparkplug(
        self, spb_object
    ) -> int | float | str | bool | bytes | list | Payload.DataSet | Payload.Template:
        """
        Retrieves the value from the correct slot of the spb_object
        spb_object is one of type
            - Payload.Metric
            - Payload.PropertyValue
            - Payload.DataSet.DataSetValue
            - Payload.Template.Parameter"""
        return self.get_value_function(spb_object=spb_object)

    @staticmethod
    def _combine_enums(name: str, *enums):
        """
        Private Utility function to merge Enums because Enums cannot be extended
        """
        # combined_enum = _SPBAbstractDataTypes(name, {item.name: item.value for enum in enums for item in enum})
        combined_enum_members = {}
        for enum in enums:
            for item in enum:
                combined_enum_members[item.name] = (
                    item.value,
                    item.field_name,
                    item.add_value_function,
                    item.get_value_function,
                )

        combined_enum = _SPBAbstractDataTypes(name, combined_enum_members)
        return combined_enum


class _GetAndSetValueInSparkPlugObject:
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
            "Invalid datatype.\n Value: %s not added to %s", str(value), str(spb_object), stack_info=True
        )

    @staticmethod
    def get_unsigned_int_or_long(
        value: int,
        attr_name: Literal[SPBValueFieldName.INT, SPBValueFieldName.LONG],
        spb_object: Payload.Metric | Payload.PropertyValue | Payload.DataSet.DataSetValue | Payload.Template.Parameter,
        factor: Literal[0, 8, 16, 32, 64] = 0,
    ) -> int:
        """
        Helper method for setting Int value or Long Value in metric/property value/dataset value / template parameter
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
                    Int64: 64 <- for long
                    UInt: 0 <- for UInt8, UInt16, UInt32, UInt64
        """
        if value is not None and value < 0:
            value = value + (0 if factor == 0 else 2**factor)
        setattr(spb_object, attr_name, value)
        return value

    @staticmethod
    def get_signed_int_or_long(
        spb_object: Payload.Metric | Payload.PropertyValue | Payload.DataSet.DataSetValue | Payload.Template.Parameter,
        attr_name: Literal[SPBValueFieldName.INT, SPBValueFieldName.LONG],
        factor: Literal[0, 8, 16, 32, 64] = 0,
    ):
        unsigned_value: int = getattr(spb_object, attr_name)

        if unsigned_value >= 2 ** (factor - 1):
            signed_value = unsigned_value - 2**factor
        else:
            signed_value = unsigned_value
        return signed_value

    @staticmethod
    def boolean_array_to_bytes(
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
    def bytes_to_boolean_array(
        spb_object: Payload.Metric,
    ) -> list[bool]:
        bytes_value = getattr(spb_object, SPBValueFieldName.BYTES)
        # unpack the 4-byte integer representing the number of boolean values
        boolean_count = struct.unpack("<I", bytes_value[:4])[0]

        # Unpack the packed bytes into a list of booleans
        boolean_array = [
            bool(bytes_value[4 + bool_byte // 8] & (1 << (7 - bool_byte % 8))) for bool_byte in range(boolean_count)
        ]

        return boolean_array

    @staticmethod
    def string_array_to_bytes(
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
    def bytes_to_string_array(spb_object: Payload.Metric) -> list[str]:
        bytes_value: bytes = getattr(spb_object, SPBValueFieldName.BYTES)
        return [bytes.fromhex(s.decode("utf-8")).decode() for s in bytes_value.split(b"\x00")[:-1]]
        # Split by null terminator and remove the last empty entry and the encode

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
        - Payload.PropertyValue (only valid types)
        - Payload.DataSet.DataSetValue (only valid types)
        - Payload.Template.Parameter (only valid types)

    """

    Unknown = (
        sparkplug_b_pb2.Unknown,
        None,
        lambda spb_object, value: _GetAndSetValueInSparkPlugObject.unknown_value(spb_object=spb_object, value=value),
        lambda spb_object: None,  # noqa: ARG005
    )

    Int8 = (
        sparkplug_b_pb2.Int8,
        SPBValueFieldName.INT,
        lambda spb_object, value: _GetAndSetValueInSparkPlugObject.get_unsigned_int_or_long(
            value=value, attr_name=SPBValueFieldName.INT, spb_object=spb_object, factor=8
        ),
        lambda spb_object: _GetAndSetValueInSparkPlugObject.get_signed_int_or_long(
            spb_object=spb_object, attr_name=SPBValueFieldName.INT, factor=8
        ),
    )

    Int16 = (
        sparkplug_b_pb2.Int16,
        SPBValueFieldName.INT,
        lambda spb_object, value: _GetAndSetValueInSparkPlugObject.get_unsigned_int_or_long(
            value=value, attr_name=SPBValueFieldName.INT, spb_object=spb_object, factor=16
        ),
        lambda spb_object: _GetAndSetValueInSparkPlugObject.get_signed_int_or_long(
            spb_object=spb_object, attr_name=SPBValueFieldName.INT, factor=16
        ),
    )

    Int32 = (
        sparkplug_b_pb2.Int32,
        SPBValueFieldName.INT,
        lambda spb_object, value: _GetAndSetValueInSparkPlugObject.get_unsigned_int_or_long(
            value=value, attr_name=SPBValueFieldName.INT, spb_object=spb_object, factor=32
        ),
        lambda spb_object: _GetAndSetValueInSparkPlugObject.get_signed_int_or_long(
            spb_object=spb_object, attr_name=SPBValueFieldName.INT, factor=32
        ),
    )

    Int64 = (
        sparkplug_b_pb2.Int64,
        SPBValueFieldName.LONG,
        lambda spb_object, value: _GetAndSetValueInSparkPlugObject.get_unsigned_int_or_long(
            value=value, attr_name=SPBValueFieldName.LONG, spb_object=spb_object, factor=64
        ),
        lambda spb_object: _GetAndSetValueInSparkPlugObject.get_signed_int_or_long(
            spb_object=spb_object, attr_name=SPBValueFieldName.LONG, factor=64
        ),
    )

    UInt8 = (
        sparkplug_b_pb2.UInt8,
        SPBValueFieldName.INT,
    )

    UInt16 = (
        sparkplug_b_pb2.UInt16,
        SPBValueFieldName.INT,
    )

    UInt32 = (
        sparkplug_b_pb2.UInt32,
        SPBValueFieldName.INT,
    )

    UInt64 = (
        sparkplug_b_pb2.UInt64,
        SPBValueFieldName.LONG,
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
    )

    String = (
        sparkplug_b_pb2.String,
        SPBValueFieldName.STRING,
    )

    DateTime = (
        sparkplug_b_pb2.DateTime,
        SPBValueFieldName.LONG,
        lambda spb_object, value: _GetAndSetValueInSparkPlugObject.get_unsigned_int_or_long(
            value=value, attr_name=SPBValueFieldName.LONG, spb_object=spb_object, factor=64
        ),
        lambda spb_object: _GetAndSetValueInSparkPlugObject.get_signed_int_or_long(
            spb_object=spb_object, attr_name=SPBValueFieldName.LONG, factor=64
        ),
    )

    Text = (
        sparkplug_b_pb2.Text,
        SPBValueFieldName.STRING,
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
    )

    DataSet = (
        sparkplug_b_pb2.DataSet,
        SPBValueFieldName.DATASET,
        lambda spb_object, value: spb_object.dataset_value.CopyFrom(value)
        if isinstance(value, Payload.DataSet)
        else _GetAndSetValueInSparkPlugObject.raise_in_lambda(
            ValueError(f"Expecting object of type Payload.DataSet, got of type {type(value)}")
        ),
    )

    Bytes = (
        sparkplug_b_pb2.Bytes,
        SPBValueFieldName.BYTES,
    )

    File = (
        sparkplug_b_pb2.File,
        SPBValueFieldName.BYTES,
    )

    Template = (
        sparkplug_b_pb2.Template,
        SPBValueFieldName.TEMPLATE,
        lambda spb_object, value: spb_object.template_value.CopyFrom(value)
        if isinstance(value, Payload.Template)
        else _GetAndSetValueInSparkPlugObject.raise_in_lambda(
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
            spb_object,
            SPBValueFieldName.BYTES,
            struct.pack(f"<{len(value)}b", *value),
        ),
        lambda spb_object: list(
            struct.unpack(
                f"<{len(getattr(spb_object, SPBValueFieldName.BYTES))}b", getattr(spb_object, SPBValueFieldName.BYTES)
            )
        ),
        # Format "b" maps to  "signed char" C Type and integer Python type
    )

    Int16Array = (
        sparkplug_b_pb2.Int16Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}h", *value)),
        lambda spb_object: list(
            struct.unpack(
                f"<{len(getattr(spb_object, SPBValueFieldName.BYTES)) // 2}h", getattr(spb_object, SPBValueFieldName.BYTES)
            )
        ),
        # Format "h" maps to  "short" C Type and integer Python type
    )

    Int32Array = (
        sparkplug_b_pb2.Int32Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}i", *value)),
        lambda spb_object: list(
            struct.unpack(
                f"<{len(getattr(spb_object, SPBValueFieldName.BYTES)) // 4 }i", getattr(spb_object, SPBValueFieldName.BYTES)
            )
        ),
        # Format "i" maps to  "int" C Type and integer Python type
    )

    Int64Array = (
        sparkplug_b_pb2.Int64Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}q", *value)),
        lambda spb_object: list(
            struct.unpack(
                f"<{len(getattr(spb_object, SPBValueFieldName.BYTES)) // 8}q", getattr(spb_object, SPBValueFieldName.BYTES)
            )
        ),
        # Format "q" maps to  "long long" C Type and integer Python type
    )

    UInt8Array = (
        sparkplug_b_pb2.UInt8Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}B", *value)),
        lambda spb_object: list(
            struct.unpack(
                f"<{len(getattr(spb_object, SPBValueFieldName.BYTES))}B", getattr(spb_object, SPBValueFieldName.BYTES)
            )
        ),
        # Format "B" maps to  "unsigned char" C Type and integer Python type
    )

    UInt16Array = (
        sparkplug_b_pb2.UInt16Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}H", *value)),
        lambda spb_object: list(
            struct.unpack(
                f"<{len(getattr(spb_object, SPBValueFieldName.BYTES)) // 2}H", getattr(spb_object, SPBValueFieldName.BYTES)
            )
        ),
        # Format "H" maps to  "unsigned short" C Type and integer Python type
    )

    UInt32Array = (
        sparkplug_b_pb2.UInt32Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}I", *value)),
        lambda spb_object: list(
            struct.unpack(
                f"<{len(getattr(spb_object, SPBValueFieldName.BYTES)) // 4}I", getattr(spb_object, SPBValueFieldName.BYTES)
            )
        ),
        # Format "I" maps to  "unsigned int" C Type and integer Python type
    )

    UInt64Array = (
        sparkplug_b_pb2.UInt64Array,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}Q", *value)),
        lambda spb_object: list(
            struct.unpack(
                f"<{len(getattr(spb_object, SPBValueFieldName.BYTES)) // 8}Q", getattr(spb_object, SPBValueFieldName.BYTES)
            )
        ),
        # Format "Q" maps to  "unsigned long long" C Type and integer Python type
    )

    FloatArray = (
        sparkplug_b_pb2.FloatArray,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}f", *value)),
        lambda spb_object: list(
            struct.unpack(
                f"<{len(getattr(spb_object, SPBValueFieldName.BYTES)) // 4}f", getattr(spb_object, SPBValueFieldName.BYTES)
            )
        ),
        # Format "f" maps to  "float" C Type and float Python type
    )

    DoubleArray = (
        sparkplug_b_pb2.DoubleArray,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}d", *value)),
        lambda spb_object: list(
            struct.unpack(
                f"<{len(getattr(spb_object, SPBValueFieldName.BYTES)) // 8}d", getattr(spb_object, SPBValueFieldName.BYTES)
            )
        ),
        # Format "d" maps to  "double" C Type and float Python type
    )

    BooleanArray = (
        sparkplug_b_pb2.BooleanArray,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: _GetAndSetValueInSparkPlugObject.boolean_array_to_bytes(values=value, spb_object=spb_object),
        lambda spb_object: _GetAndSetValueInSparkPlugObject.bytes_to_boolean_array(spb_object=spb_object),
    )

    StringArray = (
        sparkplug_b_pb2.StringArray,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: _GetAndSetValueInSparkPlugObject.string_array_to_bytes(values=value, spb_object=spb_object),
        lambda spb_object: _GetAndSetValueInSparkPlugObject.bytes_to_string_array(spb_object=spb_object),
    )

    DateTimeArray = (
        sparkplug_b_pb2.DateTimeArray,
        SPBValueFieldName.BYTES,
        lambda spb_object, value: setattr(spb_object, SPBValueFieldName.BYTES, struct.pack(f"<{len(value)}q", *value)),
        lambda spb_object: list(
            struct.unpack(
                f"<{len(getattr(spb_object, SPBValueFieldName.BYTES)) // 8}q", getattr(spb_object, SPBValueFieldName.BYTES)
            )
        ),
    )  # Format "q" maps to  "long long" C Type and integer Python type.since Datetime is a long value


# Enumeration of datatypes possible in Payload.Metric
# Combine  basic datatypes, additional datatypes and array datatypes
SPBMetricDataTypes: _SPBAbstractDataTypes = _SPBAbstractDataTypes._combine_enums(
    "SPBMetricDataTypes", SPBBasicDataTypes, SPBAdditionalDataTypes, SPBArrayDataTypes
)


# Enumeration of datatypes possible for Payload.Template.Parameters and Payload.DataSet.DataSetValue
SPBParameterTypes: _SPBAbstractDataTypes = SPBBasicDataTypes


# Enumeration of datatypes possible for Payload.PropertyValue
# Extend basic datatypes with PropertySet & PropertySetList types
SPBPropertyValueTypes: _SPBAbstractDataTypes = _SPBAbstractDataTypes._combine_enums(
    "SPBPropertyValueTypes",
    SPBParameterTypes,
    _SPBAbstractDataTypes(
        "SPBPropertySet",
        {
            "PropertySet": (
                sparkplug_b_pb2.PropertySet,
                SPBValueFieldName.PROPERTY_SET,
                lambda spb_object, value: spb_object.propertyset_value.CopyFrom(value)
                if isinstance(value, Payload.PropertySet) and isinstance(spb_object, Payload.PropertyValue)
                else _GetAndSetValueInSparkPlugObject.raise_in_lambda(
                    ValueError(
                        f"Expecting object of type Payload.PropertySet, got of type {type(value)}"
                        f"to set in Payload.PropertyValue but got {type(spb_object)}"
                    )
                ),
            )
        },
    ),
    _SPBAbstractDataTypes(
        "SPBPropertySetList",
        {
            "PropertySetList": (
                sparkplug_b_pb2.PropertySetList,
                SPBValueFieldName.PROPERTY_SET_LIST,
                lambda spb_object, value: spb_object.propertysets_value.CopyFrom(value)
                if isinstance(value, Payload.PropertySetList) and isinstance(spb_object, Payload.PropertyValue)
                else _GetAndSetValueInSparkPlugObject.raise_in_lambda(
                    ValueError(
                        f"Expecting object of type Payload.PropertySetList, got of type {type(value)}"
                        f"to set in Payload.PropertyValue but got {type(spb_object)}"
                    )
                ),
            )
        },
    ),
)


# Enumeration of datatypes possible for Payload.DataSet.DataSetValue
# As this is same as that for Payload.Template.Parameter creating an alias
# If the spec changes for DataSetValue we just need to adapt the value
SPBDataSetDataTypes: _SPBAbstractDataTypes = SPBParameterTypes
