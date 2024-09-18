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

Test class for uns_sparkplugb.uns_spb_helper
"""

import math
from typing import Literal

import pytest
from uns_sparkplugb.generated import sparkplug_b_pb2
from uns_sparkplugb.uns_spb_enums import (
    SPBAdditionalDataTypes,
    SPBBasicDataTypes,
    SPBDataSetDataTypes,
    SPBMetricDataTypes,
    SPBParameterTypes,
    SPBPropertyValueTypes,
)
from uns_sparkplugb.uns_spb_helper import FLOAT_PRECISION


def check_other_slots(value, spb_obj, enum_list, enum):
    """
    utility method to check value was not set accidentally in any other attribute/slot
    """
    for datatype in enum_list:
        if datatype != SPBBasicDataTypes.Unknown:
            retrieved_value = getattr(spb_obj, datatype.get_field_name())

            if (
                datatype.get_field_name() != enum.get_field_name() and type(retrieved_value) is type(value)
                # need to check type to handle bool checks because 0 == False evaluates to True
            ):
                assert retrieved_value != value, f"Datatype: {value} should be set in {spb_obj} for type {datatype}"


@pytest.mark.parametrize(
    "value, spb_obj, spb_enum_types, expected_value, spb_datatype",
    [
        (10, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, 10, sparkplug_b_pb2.UInt8),
        (10, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, 10, sparkplug_b_pb2.Int8),
        (-10, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, -10 + 2**8, sparkplug_b_pb2.Int8),
        (10, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, 10, sparkplug_b_pb2.UInt16),
        (10, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, 10, sparkplug_b_pb2.Int16),
        (-10, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, -10 + 2**16, sparkplug_b_pb2.Int16),
        (10, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, 10, sparkplug_b_pb2.UInt32),
        (10, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, 10, sparkplug_b_pb2.Int32),
        (-10, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, -10 + 2**32, sparkplug_b_pb2.Int32),
        (20, sparkplug_b_pb2.Payload.Template.Parameter(), SPBParameterTypes, 20, sparkplug_b_pb2.UInt32),
        (30, sparkplug_b_pb2.Payload.DataSet.DataSetValue(), SPBDataSetDataTypes, 30, sparkplug_b_pb2.UInt32),
        (40, sparkplug_b_pb2.Payload.PropertyValue(), SPBPropertyValueTypes, 40, sparkplug_b_pb2.UInt32),
    ],
)
def test_int_value_via_enum(value: int, spb_obj, spb_enum_types, expected_value: int, spb_datatype: int):
    """
    Test case for uns_spb_helper#set_int_value_in_spb_object
    """
    spb_enum_types(spb_datatype).set_value_in_sparkplug(value=value, spb_object=spb_obj)
    # check raw value in the slot
    assert spb_obj.int_value == expected_value, f"Expecting metric value to be: {expected_value}, but got {spb_obj.int_value} "
    check_other_slots(value, spb_obj, spb_enum_types, SPBBasicDataTypes(spb_datatype))
    # check encoded value matches original value
    assert spb_enum_types(spb_datatype).get_value_function(spb_obj) == value


@pytest.mark.parametrize(
    "value, spb_obj, spb_enum_types, expected_value,spb_datatype",
    [
        (10, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, 10, sparkplug_b_pb2.UInt64),
        (10, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, 10, sparkplug_b_pb2.Int64),
        (-10, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, -10 + 2**64, sparkplug_b_pb2.Int64),
        (123456, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, 123456, sparkplug_b_pb2.DateTime),
        (20, sparkplug_b_pb2.Payload.Template.Parameter(), SPBParameterTypes, 20, sparkplug_b_pb2.UInt64),
        (30, sparkplug_b_pb2.Payload.DataSet.DataSetValue(), SPBDataSetDataTypes, 30, sparkplug_b_pb2.UInt64),
        (40, sparkplug_b_pb2.Payload.PropertyValue(), SPBPropertyValueTypes, 40, sparkplug_b_pb2.UInt64),
    ],
)
def test_long_value_via_enum(value: int, spb_obj, spb_enum_types, expected_value: int, spb_datatype: int):
    """
    Test case for uns_spb_helper#set_long_value_in_spb_object
    """
    # In python all long values are int

    spb_enum_types(spb_datatype).set_value_in_sparkplug(value=value, spb_object=spb_obj)
    # check raw value in the slot
    assert (
        spb_obj.long_value == expected_value
    ), f"Expecting metric value to be: {expected_value}, but got {spb_obj.long_value}"
    check_other_slots(value, spb_obj, spb_enum_types, SPBBasicDataTypes(spb_datatype))
    # check encoded value matches original value
    assert spb_enum_types(spb_datatype).get_value_function(spb_obj) == value


@pytest.mark.parametrize(
    "value, spb_obj, spb_enum_types, expected_value",
    [
        (10.0, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, 10.0),
        (-10.0, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, -10.0),
        (20.0, sparkplug_b_pb2.Payload.Template.Parameter(), SPBParameterTypes, 20.0),
        (-20.0, sparkplug_b_pb2.Payload.Template.Parameter(), SPBParameterTypes, -20.0),
        (30.0, sparkplug_b_pb2.Payload.DataSet.DataSetValue(), SPBDataSetDataTypes, 30.0),
        (-30.0, sparkplug_b_pb2.Payload.DataSet.DataSetValue(), SPBDataSetDataTypes, -30.0),
        (40.0, sparkplug_b_pb2.Payload.PropertyValue(), SPBPropertyValueTypes, 40.0),
        (-40.0, sparkplug_b_pb2.Payload.PropertyValue(), SPBPropertyValueTypes, -40.0),
    ],
)
def test_float_value_via_enum(value: float, spb_obj, spb_enum_types, expected_value: float):
    """
    Test case for setting float value via the ENUMs
    """
    spb_enum_types(sparkplug_b_pb2.Float).set_value_in_sparkplug(value=value, spb_object=spb_obj)
    # check raw value in the slot
    assert (
        spb_obj.float_value == expected_value
    ), f"Expecting metric value to be: {expected_value}, but got {spb_obj.float_value} "
    check_other_slots(value, spb_obj, spb_enum_types, SPBBasicDataTypes.Float)
    # check encoded value matches original value
    assert spb_enum_types(sparkplug_b_pb2.Float).get_value_function(spb_obj) == expected_value


@pytest.mark.parametrize(
    "value, spb_obj, spb_enum_types, expected_value",
    [
        (10.0, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, 10.0),
        (-10.0, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, -10.0),
        (20.0, sparkplug_b_pb2.Payload.Template.Parameter(), SPBParameterTypes, 20.0),
        (-20.0, sparkplug_b_pb2.Payload.Template.Parameter(), SPBParameterTypes, -20.0),
        (30.0, sparkplug_b_pb2.Payload.DataSet.DataSetValue(), SPBDataSetDataTypes, 30.0),
        (-30.0, sparkplug_b_pb2.Payload.DataSet.DataSetValue(), SPBDataSetDataTypes, -30.0),
        (40.0, sparkplug_b_pb2.Payload.PropertyValue(), SPBPropertyValueTypes, 40.0),
        (-40.0, sparkplug_b_pb2.Payload.PropertyValue(), SPBPropertyValueTypes, -40.0),
    ],
)
def test_double_value_via_enum(value: float, spb_obj, spb_enum_types, expected_value: float):
    """
    Test case for value setting double via the ENUMs
    """
    spb_enum_types(sparkplug_b_pb2.Double).set_value_in_sparkplug(value=value, spb_object=spb_obj)
    # check raw value in the slot
    assert (
        spb_obj.double_value == expected_value
    ), f"Expecting metric value to be: {expected_value}, but got {spb_obj.double_value} "
    check_other_slots(value, spb_obj, spb_enum_types, SPBBasicDataTypes.Double)
    # check encoded value matches original value
    assert spb_enum_types(sparkplug_b_pb2.Double).get_value_function(spb_obj) == value


@pytest.mark.parametrize(
    "value, spb_obj, spb_enum_types, expected_value",
    [
        (True, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, True),
        (False, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, False),
        (True, sparkplug_b_pb2.Payload.Template.Parameter(), SPBParameterTypes, True),
        (False, sparkplug_b_pb2.Payload.Template.Parameter(), SPBParameterTypes, False),
        (True, sparkplug_b_pb2.Payload.DataSet.DataSetValue(), SPBDataSetDataTypes, True),
        (False, sparkplug_b_pb2.Payload.DataSet.DataSetValue(), SPBDataSetDataTypes, False),
        (True, sparkplug_b_pb2.Payload.PropertyValue(), SPBPropertyValueTypes, True),
        (False, sparkplug_b_pb2.Payload.PropertyValue(), SPBPropertyValueTypes, False),
    ],
)
def test_boolean_value_via_enum(value: bool, spb_obj, spb_enum_types, expected_value: bool):
    """
    Test case for value setting boolean via the ENUMs
    """

    spb_enum_types(sparkplug_b_pb2.Boolean).set_value_in_sparkplug(value=value, spb_object=spb_obj)

    assert (
        spb_obj.boolean_value == expected_value
    ), f"Expecting metric value to be:{expected_value}, got:{spb_obj.boolean_value}"
    check_other_slots(value, spb_obj, spb_enum_types, SPBBasicDataTypes.Boolean)
    # check encoded value matches original value

    assert spb_enum_types(sparkplug_b_pb2.Boolean).get_value_function(spb_obj) == expected_value


@pytest.mark.parametrize(
    "value, spb_obj, spb_enum_types,expected_value,spb_datatype",
    [
        ("Test String", sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, "Test String", sparkplug_b_pb2.String),
        (
            """Test Text\nLine2""",
            sparkplug_b_pb2.Payload.Metric(),
            SPBMetricDataTypes,
            """Test Text\nLine2""",
            sparkplug_b_pb2.Text,
        ),
        (
            "Test Template Parameter",
            sparkplug_b_pb2.Payload.Template.Parameter(),
            SPBParameterTypes,
            "Test Template Parameter",
            sparkplug_b_pb2.String,
        ),
        (
            "Test DataSetValue",
            sparkplug_b_pb2.Payload.DataSet.DataSetValue(),
            SPBDataSetDataTypes,
            "Test DataSetValue",
            sparkplug_b_pb2.String,
        ),
        (
            "Test PropertyValue",
            sparkplug_b_pb2.Payload.PropertyValue(),
            SPBPropertyValueTypes,
            "Test PropertyValue",
            sparkplug_b_pb2.String,
        ),
    ],
)
def test_string_value_via_enum(value: str, spb_obj, spb_enum_types, expected_value: str, spb_datatype):
    """
    Test case for value setting String via the ENUMs
    """
    spb_enum_types(spb_datatype).set_value_in_sparkplug(value=value, spb_object=spb_obj)
    assert (
        spb_obj.string_value == expected_value
    ), f"Expecting metric value to be: {expected_value}, but got {spb_obj.string_value}"
    check_other_slots(value, spb_obj, spb_enum_types, spb_enum_types(spb_datatype))
    # check encoded value matches original value
    assert spb_enum_types(sparkplug_b_pb2.String).get_value_function(spb_obj) == expected_value


@pytest.mark.parametrize(
    "value, spb_obj, spb_enum_types, expected_value",
    [
        (bytes("Test String1", "utf-8"), sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, bytes("Test String1", "utf-8")),
        (
            bytes("""Test String2\nLine2""", "utf-8"),
            sparkplug_b_pb2.Payload.Metric(),
            SPBMetricDataTypes,
            bytes("""Test String2\nLine2""", "utf-8"),
        ),
    ],
)
def test_bytes_value_via_enum(value: bytes, spb_obj, spb_enum_types, expected_value: bytes):
    """
    Test case for value setting boolean via the ENUMs
    """
    spb_enum_types(sparkplug_b_pb2.Bytes).set_value_in_sparkplug(value=value, spb_object=spb_obj)
    assert (
        spb_obj.bytes_value == expected_value
    ), f"Expecting metric value to be: {expected_value}, but got {spb_obj.bytes_value}"
    check_other_slots(value, spb_obj, spb_enum_types, SPBAdditionalDataTypes.Bytes)
    # check encoded value matches original value

    assert spb_enum_types(sparkplug_b_pb2.Bytes).get_value_function(spb_obj) == expected_value


@pytest.mark.parametrize(
    "value, spb_obj, spb_enum_types, expected_value",
    [
        (bytes("Test String1", "utf-8"), sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes, bytes("Test String1", "utf-8")),
        (
            bytes("""Test String2\nLine2""", "utf-8"),
            sparkplug_b_pb2.Payload.Metric(),
            SPBMetricDataTypes,
            bytes("""Test String2\nLine2""", "utf-8"),
        ),
    ],
)
def test_file_value_via_enum(value: bytes, spb_obj, spb_enum_types, expected_value: bytes):
    """
    Test case for value setting boolean via the ENUMs
    """
    spb_enum_types(sparkplug_b_pb2.File).set_value_in_sparkplug(value=value, spb_object=spb_obj)
    assert (
        spb_obj.bytes_value == expected_value
    ), f"Expecting metric value to be: {expected_value}, but got {spb_obj.bytes_value}"
    check_other_slots(value, spb_obj, spb_enum_types, SPBAdditionalDataTypes.File)
    # check encoded value matches original value

    assert spb_enum_types(sparkplug_b_pb2.File).get_value_function(spb_obj) == expected_value


@pytest.mark.parametrize(
    "value, spb_obj",
    [
        (sparkplug_b_pb2.Payload.DataSet(), sparkplug_b_pb2.Payload.Metric()),  # positive test case
        ("String", sparkplug_b_pb2.Payload.Metric()),  # negative test case
    ],
)
def test_dataset_via_enum(value: sparkplug_b_pb2.Payload.DataSet, spb_obj):
    """
    Test case for value setting Template via the ENUMs
    """
    if isinstance(value, sparkplug_b_pb2.Payload.DataSet):
        spb_obj.datatype: int = sparkplug_b_pb2.DataSet  # type: ignore
        SPBMetricDataTypes(sparkplug_b_pb2.DataSet).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        # check raw value in the slot
        assert spb_obj.dataset_value == value
        check_other_slots(value, spb_obj, SPBMetricDataTypes, SPBAdditionalDataTypes.DataSet)
        # check encoded value matches original value
        assert SPBMetricDataTypes(sparkplug_b_pb2.DataSet).get_value_function(spb_obj) == value
    else:
        with pytest.raises(ValueError):
            SPBMetricDataTypes(sparkplug_b_pb2.DataSet).set_value_in_sparkplug(value=value, spb_object=spb_obj)


@pytest.mark.parametrize(
    "value, spb_obj",
    [
        (sparkplug_b_pb2.Payload.Template(), sparkplug_b_pb2.Payload.Metric()),  # positive test case
        ("String", sparkplug_b_pb2.Payload.Metric()),  # negative test case
    ],
)
def test_template_via_enum(value, spb_obj):
    """
    Test case for value setting Template via the ENUMs  sparkplug_b_pb2.Template
    """
    if isinstance(value, sparkplug_b_pb2.Payload.Template):
        SPBMetricDataTypes(sparkplug_b_pb2.Template).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        # check raw value in the slot
        assert spb_obj.template_value == value
        check_other_slots(value, spb_obj, SPBMetricDataTypes, SPBAdditionalDataTypes.Template)
        # check encoded value matches original value
        assert SPBMetricDataTypes(sparkplug_b_pb2.Template).get_value_function(spb_obj) == value
    else:
        with pytest.raises(ValueError):
            SPBMetricDataTypes(sparkplug_b_pb2.Template).set_value_in_sparkplug(value=value, spb_object=spb_obj)


@pytest.mark.parametrize(
    "value, spb_obj",
    [
        (sparkplug_b_pb2.Payload.PropertySet(), sparkplug_b_pb2.Payload.PropertyValue()),  # positive test case
        ("String", sparkplug_b_pb2.Payload.PropertyValue()),  # negative test case
    ],
)
def test_propertyset_via_enum(value: sparkplug_b_pb2.Payload.PropertySet, spb_obj):
    """
    Test case for value setting Properties via the ENUMs
    """
    if isinstance(value, sparkplug_b_pb2.Payload.PropertySet):
        SPBPropertyValueTypes(sparkplug_b_pb2.PropertySet).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        # check raw value in the slot
        assert spb_obj.propertyset_value == value
        check_other_slots(value, spb_obj, SPBPropertyValueTypes, SPBPropertyValueTypes.PropertySet)
        # check encoded value matches original value
        assert SPBPropertyValueTypes(sparkplug_b_pb2.PropertySet).get_value_function(spb_obj) == value
    else:
        with pytest.raises(ValueError):
            SPBPropertyValueTypes(sparkplug_b_pb2.PropertySet).set_value_in_sparkplug(value=value, spb_object=spb_obj)


@pytest.mark.parametrize(
    "value, spb_obj",
    [
        (sparkplug_b_pb2.Payload.PropertySetList(), sparkplug_b_pb2.Payload.PropertyValue()),  # positive test case
        ("String", sparkplug_b_pb2.Payload.PropertyValue()),  # negative test case
    ],
)
def test_propertyset_list_via_enum(value: sparkplug_b_pb2.Payload.PropertySetList, spb_obj):
    """
    Test case for value setting Template via the ENUMs
    """
    if isinstance(value, sparkplug_b_pb2.Payload.PropertySetList):
        SPBPropertyValueTypes(sparkplug_b_pb2.PropertySetList).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        assert spb_obj.propertysets_value == value
        check_other_slots(value, spb_obj, SPBPropertyValueTypes, SPBPropertyValueTypes.PropertySetList)
        # check encoded value matches original value
        assert SPBPropertyValueTypes(sparkplug_b_pb2.PropertySetList).get_value_function(spb_obj) == value
    else:
        with pytest.raises(ValueError):
            SPBPropertyValueTypes(sparkplug_b_pb2.PropertySetList).set_value_in_sparkplug(value=value, spb_object=spb_obj)


@pytest.mark.parametrize(
    "value, spb_obj, spb_enum_types",
    [
        (1234, sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes),
        ("UNKNOWN VALUE", sparkplug_b_pb2.Payload.Metric(), SPBMetricDataTypes),
    ],
)
def test_unknown_via_enum(value, spb_obj, spb_enum_types):
    spb_enum_types(sparkplug_b_pb2.Unknown).set_value_in_sparkplug(value, spb_object=spb_obj)
    check_other_slots(value, spb_obj, spb_enum_types, SPBBasicDataTypes.Unknown)
    # check encoded value matches original value
    assert spb_enum_types(sparkplug_b_pb2.Unknown).get_value_from_sparkplug(spb_obj) is None
    if type(spb_obj) is sparkplug_b_pb2.Payload.Metric:
        assert spb_obj.datatype == sparkplug_b_pb2.Unknown
    if type(spb_obj) is sparkplug_b_pb2.Payload.PropertyValue | sparkplug_b_pb2.Payload.Template.Parameter:
        assert spb_obj.type == sparkplug_b_pb2.Unknown


def little_to_big_endian(byte_list: list[float], factor: Literal[4, 8]) -> bytes:
    rearranged_list = [
        x for chunk in [byte_list[i : i + factor][::-1] for i in range(0, len(byte_list), factor)] for x in chunk
    ]
    return bytes(rearranged_list)


@pytest.mark.parametrize(
    "array_type, value, spb_obj, encoded_bytes",
    [  # test data taken from https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf
        # FIXME  document mentioned [0xEF, 0x7B] but appears wrong, should have been [0xE9, 0x7B]
        (sparkplug_b_pb2.Int8Array, [-23, 123], sparkplug_b_pb2.Payload.Metric(), bytes([0xE9, 0x7B])),
        (sparkplug_b_pb2.Int16Array, [-30000, 30000], sparkplug_b_pb2.Payload.Metric(), bytes([0xD0, 0x8A, 0x30, 0x75])),
        (
            sparkplug_b_pb2.Int32Array,
            [-1, 315338746],
            sparkplug_b_pb2.Payload.Metric(),
            bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFA, 0xAF, 0xCB, 0x12]),
        ),
        (
            sparkplug_b_pb2.Int64Array,
            [-4270929666821191986, -3601064768563266876],
            sparkplug_b_pb2.Payload.Metric(),
            bytes([0xCE, 0x06, 0x72, 0xAC, 0x18, 0x9C, 0xBA, 0xC4, 0xC4, 0xBA, 0x9C, 0x18, 0xAC, 0x72, 0x06, 0xCE]),
        ),
        (sparkplug_b_pb2.UInt8Array, [23, 250], sparkplug_b_pb2.Payload.Metric(), bytes([0x17, 0xFA])),
        (sparkplug_b_pb2.UInt16Array, [30, 52360], sparkplug_b_pb2.Payload.Metric(), bytes([0x1E, 0x00, 0x88, 0xCC])),
        (
            sparkplug_b_pb2.UInt32Array,
            [52, 3293969225],
            sparkplug_b_pb2.Payload.Metric(),
            bytes([0x34, 0x00, 0x00, 0x00, 0x49, 0xFB, 0x55, 0xC4]),
        ),
        (
            sparkplug_b_pb2.UInt64Array,
            [52, 16444743074749521625],
            sparkplug_b_pb2.Payload.Metric(),
            bytes([0x34, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xD9, 0x9E, 0x02, 0xD1, 0xB2, 0x76, 0x37, 0xE4]),
        ),
        (
            sparkplug_b_pb2.DoubleArray,
            [12.354213, 1022.9123213],
            sparkplug_b_pb2.Payload.Metric(),
            little_to_big_endian(
                [0x40, 0x28, 0xB5, 0x5B, 0x68, 0x05, 0xA2, 0xD7, 0x40, 0x8F, 0xF7, 0x4C, 0x6F, 0x1C, 0x17, 0x8E], 8
            ),
        ),
        # Float have floating point precision issues which need a separate test
        (
            sparkplug_b_pb2.DateTimeArray,
            [1256102875335, 1656107875000],
            sparkplug_b_pb2.Payload.Metric(),
            bytes([0xC7, 0xD0, 0x90, 0x75, 0x24, 0x01, 0x00, 0x00, 0xB8, 0xBA, 0xB8, 0x97, 0x81, 0x01, 0x00, 0x00]),
            # Needed to add 0x00, 0x00 to each date value to convert it to 8 bytes representation
        ),
        (
            sparkplug_b_pb2.BooleanArray,
            [False, False, True, True, False, True, False, False, True, True, False, True],
            sparkplug_b_pb2.Payload.Metric(),
            bytes([0x0C, 0x00, 0x00, 0x00, 0x34, 0xD0]),
        ),
        (
            sparkplug_b_pb2.StringArray,
            ["ABC", "hello"],
            sparkplug_b_pb2.Payload.Metric(),
            bytes(
                "".join(
                    [
                        f"{x:02x}" if x != 0x00 else "\\x00"
                        for x in [0x41, 0x42, 0x43, 0x00, 0x68, 0x65, 0x6C, 0x6C, 0x6F, 0x00]
                    ]
                ),
                "utf-8",
            )
            .decode("unicode-escape")
            .encode("utf-8"),
            # convert byte/int into hex and then convert them to bytes
        ),
    ],
)
def test_set_arrays(array_type, value: list[int | str | bool | bytes], spb_obj, encoded_bytes: bytes):
    SPBMetricDataTypes(array_type).set_value_in_sparkplug(value=value, spb_object=spb_obj)
    assert spb_obj.bytes_value == encoded_bytes
    check_other_slots(encoded_bytes, spb_obj, SPBBasicDataTypes, SPBAdditionalDataTypes.Bytes)
    check_other_slots(encoded_bytes, spb_obj, SPBAdditionalDataTypes, SPBAdditionalDataTypes.Bytes)
    #  check if the array is correctly decoded back from the byte array
    assert SPBMetricDataTypes(array_type).get_value_from_sparkplug(spb_obj) == value


@pytest.mark.parametrize(
    "array_type, value, spb_obj, encoded_bytes",
    [  # test data taken from https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf
        (
            sparkplug_b_pb2.FloatArray,
            [1.23, 89.341],
            sparkplug_b_pb2.Payload.Metric(),
            # reverse the byte order in groups of 4 bytes to change from little-endian to big-endian,
            little_to_big_endian([0x3F, 0x9D, 0x70, 0xA4, 0x42, 0xB2, 0xAE, 0x98], 4),
        ),
    ],
)
def test_set_float_arrays(array_type, value: list[float], spb_obj, encoded_bytes: bytes):
    """
    Need separate tests for decimal values due to floating point precision errors while converting to bytes and back from bytes
    """
    SPBMetricDataTypes(array_type).set_value_in_sparkplug(value=value, spb_object=spb_obj)
    assert spb_obj.bytes_value == encoded_bytes

    check_other_slots(encoded_bytes, spb_obj, SPBBasicDataTypes, SPBAdditionalDataTypes.Bytes)
    check_other_slots(encoded_bytes, spb_obj, SPBAdditionalDataTypes, SPBAdditionalDataTypes.Bytes)
    #  check if the array is correctly decoded back from the byte array
    decoded_values = SPBMetricDataTypes(array_type).get_value_from_sparkplug(spb_obj)
    for original, decoded in zip(value, decoded_values):
        assert math.isclose(original, decoded, rel_tol=1 / 10**FLOAT_PRECISION)
