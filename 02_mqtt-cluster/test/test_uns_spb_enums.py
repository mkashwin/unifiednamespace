"""
Test class for uns_sparkplugb.uns_spb_helper
"""
from types import SimpleNamespace
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
def test_set_int_value_via_enum(value: int, spb_obj, metric_value: int, spb_datatype: int):
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


@pytest.mark.parametrize(
    "value, spb_obj, metric_value,spb_datatype",
    [
        (10, SimpleNamespace(**spb_obj_dict), 10, sparkplug_b_pb2.UInt64),
        (10, SimpleNamespace(**spb_obj_dict), 10, sparkplug_b_pb2.Int64),
        (-10, SimpleNamespace(**spb_obj_dict), -10 + 2**64, sparkplug_b_pb2.Int64),
        (123456, SimpleNamespace(**spb_obj_dict), 123456, sparkplug_b_pb2.DateTime),
    ],
)
def test_set_long_value_via_enum(value: int, spb_obj, metric_value: int, spb_datatype: int):
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


@pytest.mark.parametrize(
    "value, spb_obj, metric_value",
    [
        (10.0, SimpleNamespace(**spb_obj_dict), 10.0),
        (-10.0, SimpleNamespace(**spb_obj_dict), -10.0),
    ],
)
def test_set_float_value_via_enum(value: float, spb_obj, metric_value: float):
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


@pytest.mark.parametrize(
    "value, spb_obj, metric_value",
    [
        (10.0, SimpleNamespace(**spb_obj_dict), 10.0),
        (-10.0, SimpleNamespace(**spb_obj_dict), -10.0),
    ],
)
def test_set_double_value_via_enum(value: float, spb_obj, metric_value: float):
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


@pytest.mark.parametrize(
    "value, spb_obj, metric_value",
    [
        (True, SimpleNamespace(**spb_obj_dict), True),
        (False, SimpleNamespace(**spb_obj_dict), False),
    ],
)
def test_set_boolean_value_via_enum(value: bool, spb_obj, metric_value: bool):
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


@pytest.mark.parametrize(
    "value, spb_obj, metric_value",
    [
        ("Test String1", SimpleNamespace(**spb_obj_dict), "Test String1"),
        ("""Test String2\nLine2""", SimpleNamespace(**spb_obj_dict), """Test String2\nLine2"""),
    ],
)
def test_set_string_value_via_enum(value: str, spb_obj, metric_value: str):
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
def test_set_bytes_value_via_enum(value: bytes, spb_obj, metric_value: bytes):
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


@pytest.mark.parametrize(
    "value, spb_obj",
    [
        (dataset, SimpleNamespace(**spb_obj_dict)),  # positive test case
        ("String", SimpleNamespace(**spb_obj_dict)),  # negative test case
    ],
)
def test_set_dataset_via_enum(value: sparkplug_b_pb2.Payload.DataSet, spb_obj):
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
def test_set_template_via_enum(value: sparkplug_b_pb2.Template, spb_obj):
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
def test_set_propertyset_via_enum(value: sparkplug_b_pb2.Payload.PropertySet, spb_obj):
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
                ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.TEMPLATE}"
    else:
        with pytest.raises(ValueError):
            SPBMetricDataTypes(sparkplug_b_pb2.PropertySet).set_value_in_sparkplug(value=value, spb_object=spb_obj)


@pytest.mark.parametrize(
    "value, spb_obj",
    [
        (property_set_list, SimpleNamespace(**spb_obj_dict)),  # positive test case
        ("String", SimpleNamespace(**spb_obj_dict)),  # negative test case
    ],
)
def test_set_propertyset_list_via_enum(value: sparkplug_b_pb2.Payload.PropertySetList, spb_obj):
    """
    Test case for value setting Template via the ENUMs
    """
    if isinstance(value, sparkplug_b_pb2.Payload.PropertySetList):
        SPBPropertyValueTypes(sparkplug_b_pb2.PropertySetList).set_value_in_sparkplug(value=value, spb_object=spb_obj)
        assert spb_obj.propertysets_value == value
        for datatype in spb_obj_dict:
            if datatype != SPBValueFieldName.PROPERTY_SET_LIST:
                assert (
                    spb_obj.__dict__[datatype] is None
                ), f"Datatype: {datatype} should be null in  {spb_obj} for all types except {SPBValueFieldName.TEMPLATE}"
    else:
        with pytest.raises(ValueError):
            SPBMetricDataTypes(sparkplug_b_pb2.PropertySetList).set_value_in_sparkplug(value=value, spb_object=spb_obj)
