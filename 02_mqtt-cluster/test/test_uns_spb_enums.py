"""
Test class for uns_sparkplugb.uns_spb_helper
"""
from types import SimpleNamespace
from typing import Literal
from unittest.mock import MagicMock

import pytest
from uns_sparkplugb.generated import sparkplug_b_pb2
from uns_sparkplugb.uns_spb_enums import (
    SPBBasicDataTypes,
    SPBDataSetDataTypes,
    SPBMetricDataTypes,
    SPBPropertyValueTypes,
    SPBValueFieldName,
)

# Dict containing value types as key value pair.
# Convert this to a SimpleNamespace to be able to access the attributes via dot notation
# Mocks various SPB Object types
spb_obj_dict = {
    SPBValueFieldName.INT: None,
    SPBValueFieldName.LONG: None,
    SPBValueFieldName.FLOAT: None,
    SPBValueFieldName.DOUBLE: None,
    SPBValueFieldName.STRING: None,
    SPBValueFieldName.BYTES: None,
    SPBValueFieldName.BOOLEAN: None,
    SPBValueFieldName.TEMPLATE: None,
    SPBValueFieldName.DATASET: None,
    SPBValueFieldName.PROPERTY_SET: None,
    SPBValueFieldName.PROPERTY_SET_LIST: None,
}

template: sparkplug_b_pb2.Payload.Template = MagicMock(spec=sparkplug_b_pb2.Payload.Template)
dataset: sparkplug_b_pb2.Payload.DataSet = MagicMock(spec=sparkplug_b_pb2.Payload.DataSet)
property_set: sparkplug_b_pb2.Payload.PropertySet = MagicMock(spec=sparkplug_b_pb2.Payload.PropertySet)
property_set_list: sparkplug_b_pb2.Payload.PropertySet = MagicMock(spec=sparkplug_b_pb2.Payload.PropertySetList())


@pytest.mark.parametrize(
    "value, spb_obj, metric_value, spb_datatype",
    [
        (10, SimpleNamespace(**spb_obj_dict), 10, sparkplug_b_pb2.UInt8),
        (10, SimpleNamespace(**spb_obj_dict), 10, sparkplug_b_pb2.Int8),
        (-10, SimpleNamespace(**spb_obj_dict), -10 + 2**8, sparkplug_b_pb2.Int8),
        (10, SimpleNamespace(**spb_obj_dict), 10, sparkplug_b_pb2.UInt16),
        (10, SimpleNamespace(**spb_obj_dict), 10, sparkplug_b_pb2.Int16),
        (-10, SimpleNamespace(**spb_obj_dict), -10 + 2**16, sparkplug_b_pb2.Int16),
        (10, SimpleNamespace(**spb_obj_dict), 10, sparkplug_b_pb2.UInt32),
        (10, SimpleNamespace(**spb_obj_dict), 10, sparkplug_b_pb2.Int32),
        (-10, SimpleNamespace(**spb_obj_dict), -10 + 2**32, sparkplug_b_pb2.Int32),
    ],
)
def test_int_value_via_enum(value: int, spb_obj, metric_value: int, spb_datatype: int):
    """
    Test case for uns_spb_helper#set_int_value_in_spb_object
    """
    for my_enum_type in [SPBBasicDataTypes, SPBMetricDataTypes, SPBPropertyValueTypes, SPBDataSetDataTypes]:
        my_enum_type(spb_datatype).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        assert spb_obj.int_value == metric_value, f"Expecting metric value to be: {metric_value}, but got {spb_obj.int_value} "
        for datatype in spb_obj_dict:
            if datatype != SPBValueFieldName.INT:
                assert (
                    spb_obj.__dict__[datatype] is None
                ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.INT}"

        assert my_enum_type(spb_datatype).get_value_function(spb_obj) == metric_value


@pytest.mark.parametrize(
    "value, spb_obj, metric_value,spb_datatype",
    [
        (10, SimpleNamespace(**spb_obj_dict), 10, sparkplug_b_pb2.UInt64),
        (10, SimpleNamespace(**spb_obj_dict), 10, sparkplug_b_pb2.Int64),
        (-10, SimpleNamespace(**spb_obj_dict), -10 + 2**64, sparkplug_b_pb2.Int64),
        (123456, SimpleNamespace(**spb_obj_dict), 123456, sparkplug_b_pb2.DateTime),
    ],
)
def test_long_value_via_enum(value: int, spb_obj, metric_value: int, spb_datatype: int):
    """
    Test case for uns_spb_helper#set_long_value_in_spb_object
    """
    # In python all long values are int
    for my_enum_type in [SPBBasicDataTypes, SPBMetricDataTypes, SPBPropertyValueTypes, SPBDataSetDataTypes]:
        my_enum_type(spb_datatype).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        assert (
            spb_obj.long_value == metric_value
        ), f"Expecting metric value to be: {metric_value}, but got {spb_obj.long_value} "
        for datatype in spb_obj_dict:
            if datatype != SPBValueFieldName.LONG:
                assert (
                    spb_obj.__dict__[datatype] is None
                ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.LONG}"

        assert my_enum_type(spb_datatype).get_value_function(spb_obj) == metric_value


@pytest.mark.parametrize(
    "value, spb_obj, metric_value",
    [
        (10.0, SimpleNamespace(**spb_obj_dict), 10.0),
        (-10.0, SimpleNamespace(**spb_obj_dict), -10.0),
    ],
)
def test_float_value_via_enum(value: float, spb_obj, metric_value: float):
    """
    Test case for setting float value via the ENUMs
    """
    for my_enum_type in [SPBBasicDataTypes, SPBMetricDataTypes, SPBPropertyValueTypes, SPBDataSetDataTypes]:
        my_enum_type(sparkplug_b_pb2.Float).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        assert (
            spb_obj.float_value == metric_value
        ), f"Expecting metric value to be: {metric_value}, but got {spb_obj.float_value} "
        for datatype in spb_obj_dict:
            if datatype != SPBValueFieldName.FLOAT:
                assert (
                    spb_obj.__dict__[datatype] is None
                ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.FLOAT}"

        assert my_enum_type(sparkplug_b_pb2.Float).get_value_function(spb_obj) == metric_value


@pytest.mark.parametrize(
    "value, spb_obj, metric_value",
    [
        (10.0, SimpleNamespace(**spb_obj_dict), 10.0),
        (-10.0, SimpleNamespace(**spb_obj_dict), -10.0),
    ],
)
def test_double_value_via_enum(value: float, spb_obj, metric_value: float):
    """
    Test case for value setting double via the ENUMs
    """
    for my_enum_type in [SPBBasicDataTypes, SPBMetricDataTypes, SPBPropertyValueTypes, SPBDataSetDataTypes]:
        my_enum_type(sparkplug_b_pb2.Double).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        assert (
            spb_obj.double_value == metric_value
        ), f"Expecting metric value to be: {metric_value}, but got {spb_obj.double_value} "
        for datatype in spb_obj_dict:
            if datatype != SPBValueFieldName.DOUBLE:
                assert (
                    spb_obj.__dict__[datatype] is None
                ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.DOUBLE}"

        assert my_enum_type(sparkplug_b_pb2.Double).get_value_function(spb_obj) == metric_value


@pytest.mark.parametrize(
    "value, spb_obj, metric_value",
    [
        (True, SimpleNamespace(**spb_obj_dict), True),
        (False, SimpleNamespace(**spb_obj_dict), False),
    ],
)
def test_boolean_value_via_enum(value: bool, spb_obj, metric_value: bool):
    """
    Test case for value setting boolean via the ENUMs
    """
    for my_enum_type in [SPBBasicDataTypes, SPBMetricDataTypes, SPBPropertyValueTypes, SPBDataSetDataTypes]:
        my_enum_type(sparkplug_b_pb2.Boolean).set_value_in_sparkplug(value=value, spb_object=spb_obj)

        assert (
            spb_obj.boolean_value == metric_value
        ), f"Expecting metric value to be:{metric_value}, got:{spb_obj.boolean_value}"
        for datatype in spb_obj_dict:
            if datatype != SPBValueFieldName.BOOLEAN:
                assert (
                    spb_obj.__dict__[datatype] is None
                ), f"Datatype: {datatype} must be null in {spb_obj} for all types except {SPBValueFieldName.BOOLEAN}"

        assert my_enum_type(sparkplug_b_pb2.Boolean).get_value_function(spb_obj) == metric_value


@pytest.mark.parametrize(
    "value, spb_obj, metric_value",
    [
        ("Test String1", SimpleNamespace(**spb_obj_dict), "Test String1"),
        ("""Test String2\nLine2""", SimpleNamespace(**spb_obj_dict), """Test String2\nLine2"""),
    ],
)
def test_string_value_via_enum(value: str, spb_obj, metric_value: str):
    """
    Test case for value setting String via the ENUMs
    """
    for my_enum_type in [SPBBasicDataTypes, SPBMetricDataTypes, SPBPropertyValueTypes, SPBDataSetDataTypes]:
        my_enum_type(sparkplug_b_pb2.String).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        assert (
            spb_obj.string_value == metric_value
        ), f"Expecting metric value to be: {metric_value}, but got {spb_obj.string_value}"
        for datatype in spb_obj_dict:
            if datatype != SPBValueFieldName.STRING:
                assert (
                    spb_obj.__dict__[datatype] is None
                ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.STRING}"

        assert my_enum_type(sparkplug_b_pb2.String).get_value_function(spb_obj) == metric_value


@pytest.mark.parametrize(
    "value, spb_obj, metric_value",
    [
        (bytes("Test String1", "utf-8"), SimpleNamespace(**spb_obj_dict), bytes("Test String1", "utf-8")),
        (
            bytes("""Test String2\nLine2""", "utf-8"),
            SimpleNamespace(**spb_obj_dict),
            bytes("""Test String2\nLine2""", "utf-8"),
        ),
    ],
)
def test_bytes_value_via_enum(value: bytes, spb_obj, metric_value: bytes):
    """
    Test case for value setting boolean via the ENUMs
    """
    SPBMetricDataTypes(sparkplug_b_pb2.Bytes).set_value_in_sparkplug(value=value, spb_object=spb_obj)
    assert spb_obj.bytes_value == metric_value, f"Expecting metric value to be: {metric_value}, but got {spb_obj.bytes_value}"
    for datatype in spb_obj_dict:
        if datatype != SPBValueFieldName.BYTES:
            assert (
                spb_obj.__dict__[datatype] is None
            ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.BYTES}"

    assert SPBMetricDataTypes(sparkplug_b_pb2.Bytes).get_value_function(spb_obj) == metric_value


@pytest.mark.parametrize(
    "value, spb_obj",
    [
        (dataset, SimpleNamespace(**spb_obj_dict)),  # positive test case
        ("String", SimpleNamespace(**spb_obj_dict)),  # negative test case
    ],
)
def test_dataset_via_enum(value: sparkplug_b_pb2.Payload.DataSet, spb_obj):
    """
    Test case for value setting Template via the ENUMs
    """
    if isinstance(value, sparkplug_b_pb2.Payload.DataSet):
        SPBMetricDataTypes(sparkplug_b_pb2.DataSet).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        assert spb_obj.dataset_value == value
        for datatype in spb_obj_dict:
            if datatype != SPBValueFieldName.DATASET:
                assert (
                    spb_obj.__dict__[datatype] is None
                ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.TEMPLATE}"

        assert SPBMetricDataTypes(sparkplug_b_pb2.DataSet).get_value_function(spb_obj) == value
    else:
        with pytest.raises(ValueError):
            SPBMetricDataTypes(sparkplug_b_pb2.DataSet).set_value_in_sparkplug(value=value, spb_object=spb_obj)


@pytest.mark.parametrize(
    "value, spb_obj",
    [
        (template, SimpleNamespace(**spb_obj_dict)),  # positive test case
        ("String", SimpleNamespace(**spb_obj_dict)),  # negative test case
    ],
)
def test_template_via_enum(value: sparkplug_b_pb2.Template, spb_obj):
    """
    Test case for value setting Template via the ENUMs
    """
    if isinstance(value, sparkplug_b_pb2.Payload.Template):
        SPBMetricDataTypes(sparkplug_b_pb2.Template).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        assert spb_obj.template_value == value
        for datatype in spb_obj_dict:
            if datatype != SPBValueFieldName.TEMPLATE:
                assert (
                    spb_obj.__dict__[datatype] is None
                ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.TEMPLATE}"

        assert SPBMetricDataTypes(sparkplug_b_pb2.Template).get_value_function(spb_obj) == value
    else:
        with pytest.raises(ValueError):
            SPBMetricDataTypes(sparkplug_b_pb2.Template).set_value_in_sparkplug(value=value, spb_object=spb_obj)


@pytest.mark.parametrize(
    "value, spb_obj",
    [
        (property_set, SimpleNamespace(**spb_obj_dict)),  # positive test case
        ("String", SimpleNamespace(**spb_obj_dict)),  # negative test case
    ],
)
def test_propertyset_via_enum(value: sparkplug_b_pb2.Payload.PropertySet, spb_obj):
    """
    Test case for value setting Template via the ENUMs
    """
    if isinstance(value, sparkplug_b_pb2.Payload.PropertySet):
        SPBPropertyValueTypes(sparkplug_b_pb2.PropertySet).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        assert spb_obj.propertyset_value == value
        for datatype in spb_obj_dict:
            if datatype != SPBValueFieldName.PROPERTY_SET:
                assert (
                    spb_obj.__dict__[datatype] is None
                ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.PROPERTY_SET}"

        assert SPBPropertyValueTypes(sparkplug_b_pb2.PropertySet).get_value_function(spb_obj) == value
    else:
        with pytest.raises(ValueError):
            SPBPropertyValueTypes(sparkplug_b_pb2.PropertySet).set_value_in_sparkplug(value=value, spb_object=spb_obj)


@pytest.mark.parametrize(
    "value, spb_obj",
    [
        (property_set_list, SimpleNamespace(**spb_obj_dict)),  # positive test case
        ("String", SimpleNamespace(**spb_obj_dict)),  # negative test case
    ],
)
def test_propertyset_list_via_enum(value: sparkplug_b_pb2.Payload.PropertySetList, spb_obj):
    """
    Test case for value setting Template via the ENUMs
    """
    if isinstance(value, sparkplug_b_pb2.Payload.PropertySetList):
        SPBPropertyValueTypes(sparkplug_b_pb2.PropertySetList).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        assert spb_obj.propertysets_value == value
        for datatype in spb_obj_dict:
            if datatype != SPBValueFieldName.PROPERTY_SET_LIST:
                assert spb_obj.__dict__[datatype] is None, (
                    f"Datatype: {datatype} should be null in  {spb_obj} for all types "
                    f"except {SPBValueFieldName.PROPERTY_SET_LIST}"
                )

        assert SPBPropertyValueTypes(sparkplug_b_pb2.PropertySetList).get_value_function(spb_obj) == value
    else:
        with pytest.raises(ValueError):
            SPBPropertyValueTypes(sparkplug_b_pb2.PropertySetList).set_value_in_sparkplug(value=value, spb_object=spb_obj)


@pytest.mark.parametrize(
    "value, spb_obj",
    [
        (1234, SimpleNamespace(**spb_obj_dict)),
        ("UNKNOWN VALUE", SimpleNamespace(**spb_obj_dict)),
    ],
)
def test_unknown_via_enum(value, spb_obj):
    for my_enum_type in [SPBBasicDataTypes, SPBMetricDataTypes, SPBPropertyValueTypes, SPBDataSetDataTypes]:
        my_enum_type(sparkplug_b_pb2.Unknown).set_value_in_sparkplug(value, spb_object=spb_obj)
        for datatype in spb_obj_dict:
            assert (
                spb_obj.__dict__[datatype] is None
            ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.TEMPLATE}"
        assert my_enum_type(sparkplug_b_pb2.Unknown).get_value_from_sparkplug(spb_obj) is None


def little_to_big_endian(byte_list: list[float], factor: Literal[4, 8]) -> bytes:
    rearranged_list = [
        x for chunk in [byte_list[i : i + factor][::-1] for i in range(0, len(byte_list), factor)] for x in chunk
    ]
    return bytes(rearranged_list)


@pytest.mark.parametrize(
    "array_type, value, spb_obj, encoded_bytes",
    [  # test data taken from https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf
        # FIXME  document mentioned [0xEF, 0x7B] but appears wrong, should have been [0xE9, 0x7B]
        (sparkplug_b_pb2.Int8Array, [-23, 123], SimpleNamespace(**spb_obj_dict), bytes([0xE9, 0x7B])),
        (sparkplug_b_pb2.Int16Array, [-30000, 30000], SimpleNamespace(**spb_obj_dict), bytes([0xD0, 0x8A, 0x30, 0x75])),
        (
            sparkplug_b_pb2.Int32Array,
            [-1, 315338746],
            SimpleNamespace(**spb_obj_dict),
            bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFA, 0xAF, 0xCB, 0x12]),
        ),
        (
            sparkplug_b_pb2.Int64Array,
            [-4270929666821191986, -3601064768563266876],
            SimpleNamespace(**spb_obj_dict),
            bytes([0xCE, 0x06, 0x72, 0xAC, 0x18, 0x9C, 0xBA, 0xC4, 0xC4, 0xBA, 0x9C, 0x18, 0xAC, 0x72, 0x06, 0xCE]),
        ),
        (sparkplug_b_pb2.UInt8Array, [23, 250], SimpleNamespace(**spb_obj_dict), bytes([0x17, 0xFA])),
        (sparkplug_b_pb2.UInt16Array, [30, 52360], SimpleNamespace(**spb_obj_dict), bytes([0x1E, 0x00, 0x88, 0xCC])),
        (
            sparkplug_b_pb2.UInt32Array,
            [52, 3293969225],
            SimpleNamespace(**spb_obj_dict),
            bytes([0x34, 0x00, 0x00, 0x00, 0x49, 0xFB, 0x55, 0xC4]),
        ),
        (
            sparkplug_b_pb2.UInt64Array,
            [52, 16444743074749521625],
            SimpleNamespace(**spb_obj_dict),
            bytes([0x34, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xD9, 0x9E, 0x02, 0xD1, 0xB2, 0x76, 0x37, 0xE4]),
        ),
        # Float and Double may have floating point precision issues which need a separate test
        (
            sparkplug_b_pb2.DateTimeArray,
            [1256102875335, 1656107875000],
            SimpleNamespace(**spb_obj_dict),
            bytes([0xC7, 0xD0, 0x90, 0x75, 0x24, 0x01, 0x00, 0x00, 0xB8, 0xBA, 0xB8, 0x97, 0x81, 0x01, 0x00, 0x00]),
            # Needed to add 0x00, 0x00 to each date value to convert it to 8 bytes representation
        ),
        (
            sparkplug_b_pb2.BooleanArray,
            [False, False, True, True, False, True, False, False, True, True, False, True],
            SimpleNamespace(**spb_obj_dict),
            bytes([0x0C, 0x00, 0x00, 0x00, 0x34, 0xD0]),
        ),
        (
            sparkplug_b_pb2.StringArray,
            ["ABC", "hello"],
            SimpleNamespace(**spb_obj_dict),
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
    for datatype in spb_obj_dict:
        if datatype != SPBValueFieldName.BYTES:
            # Check that no other field was set
            assert (
                spb_obj.__dict__[datatype] is None
            ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.BYTES}"
    #  check if the array is correctly decoded back from the byte array
    assert SPBMetricDataTypes(array_type).get_value_from_sparkplug(spb_obj) == value


@pytest.mark.parametrize(
    "array_type, value, spb_obj, encoded_bytes, decimal_precision",
    [  # test data taken from https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf
        (
            sparkplug_b_pb2.FloatArray,
            [1.23, 89.341],
            SimpleNamespace(**spb_obj_dict),
            # reverse the byte order in groups of 4 bytes to change from little-endian to big-endian,
            little_to_big_endian([0x3F, 0x9D, 0x70, 0xA4, 0x42, 0xB2, 0xAE, 0x98], 4),
            5,
        ),
        (
            sparkplug_b_pb2.DoubleArray,
            [12.354213, 1022.9123213],
            SimpleNamespace(**spb_obj_dict),
            little_to_big_endian(
                [0x40, 0x28, 0xB5, 0x5B, 0x68, 0x05, 0xA2, 0xD7, 0x40, 0x8F, 0xF7, 0x4C, 0x6F, 0x1C, 0x17, 0x8E], 8
            ),
            12,
        ),
    ],
)
def test_set_float_arrays(array_type, value: list[float], spb_obj, encoded_bytes: bytes, decimal_precision: int):
    """
    Need separate tests for decimal values due to floating point precision errors while converting to bytes and back from bytes
    """
    SPBMetricDataTypes(array_type).set_value_in_sparkplug(value=value, spb_object=spb_obj)
    assert spb_obj.bytes_value == encoded_bytes
    for datatype in spb_obj_dict:
        if datatype != SPBValueFieldName.BYTES:
            # Check that no other field was set
            assert (
                spb_obj.__dict__[datatype] is None
            ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.BYTES}"
    #  check if the array is correctly decoded back from the byte array
    decoded_values = SPBMetricDataTypes(array_type).get_value_from_sparkplug(spb_obj)
    for original, decoded in zip(value, decoded_values):
        assert round(original, decimal_precision) == round(decoded, decimal_precision)
