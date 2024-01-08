"""
Test class for uns_sparkplugb.uns_spb_helper
"""
from typing import Literal, Optional

import pytest
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload
from uns_sparkplugb.uns_spb_enums import SPBDataSetDataTypes, SPBMetricDataTypes
from uns_sparkplugb.uns_spb_helper import SpBMessageGenerator


def create_dummy_dataset() -> Payload.DataSet:
    """
    utility method to create a dataset
    """

    row1 = Payload.DataSet.Row(
        elements=[
            Payload.DataSet.DataSetValue(int_value=10),
            Payload.DataSet.DataSetValue(double_value=100.0),
            Payload.DataSet.DataSetValue(long_value=100000),
            Payload.DataSet.DataSetValue(string_value="I am dataset row1"),
            Payload.DataSet.DataSetValue(boolean_value=False),
        ]
    )
    row2 = Payload.DataSet.Row(
        elements=[
            Payload.DataSet.DataSetValue(int_value=20),
            Payload.DataSet.DataSetValue(double_value=200.0),
            Payload.DataSet.DataSetValue(long_value=200000),
            Payload.DataSet.DataSetValue(string_value="I am dataset row2"),
            Payload.DataSet.DataSetValue(boolean_value=True),
        ]
    )
    row3 = Payload.DataSet.Row(
        elements=[
            Payload.DataSet.DataSetValue(int_value=30),
            Payload.DataSet.DataSetValue(double_value=300.0),
            Payload.DataSet.DataSetValue(long_value=300000),
            Payload.DataSet.DataSetValue(string_value="I am dataset row3"),
            Payload.DataSet.DataSetValue(boolean_value=False),
        ]
    )

    data_set: Payload.DataSet = Payload.DataSet(
        num_of_columns=5,
        columns=["uint32", "double", "int64", "string", "boolean"],
        rows=[row1, row2, row3],
        types=[
            SPBDataSetDataTypes.UInt32,
            SPBDataSetDataTypes.Double,
            SPBDataSetDataTypes.UInt64,
            SPBDataSetDataTypes.String,
            SPBDataSetDataTypes.Boolean,
        ],
    )
    return data_set


def _convert_to_unsigned_int(value: int, factor: Literal[0, 8, 16, 32, 64]) -> int:
    """
    Utility method to manage signed int
    """
    if value is not None and value < 0:
        value = value + (0 if factor == 0 else 2**factor)
    return value


@pytest.mark.parametrize(
    "timestamp, metrics",
    [
        (  # Test for SPBBasicDataTypes
            10000000014,
            [
                {
                    "name": "Inputs/int8",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Int8,
                    "value": 10,
                },
                {
                    "name": "Inputs/int8.Neg",
                    "timestamp": 1486144502123,
                    "datatype": SPBMetricDataTypes.Int8,
                    "value": -10,
                },
                {
                    "name": "Inputs/uint8",
                    "timestamp": 1486144502123,
                    "datatype": SPBMetricDataTypes.UInt8,
                    "value": 10,
                },
                {
                    "name": "Inputs/int16.neg",
                    "timestamp": 1486144502123,
                    "datatype": SPBMetricDataTypes.Int16,
                    "value": -100,
                },
                {
                    "name": "Inputs/uint16",
                    "timestamp": 1486144502123,
                    "datatype": SPBMetricDataTypes.UInt16,
                    "value": 100,
                },
                {
                    "name": "Properties/int32",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Int32,
                    "value": 200,
                },
                {
                    "name": "Properties/int32.neg",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Int32,
                    "value": -200,
                },
                {
                    "name": "Properties/Uint32",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.UInt32,
                    "value": 200,
                },
                {
                    "name": "Outputs/DateTime",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.DateTime,
                    "value": 1486144502122,
                },
                {
                    "name": "Outputs/Uint64",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.UInt64,
                    "value": 123456,
                },
                {
                    "name": "Outputs/int64.Neg",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Int64,
                    "value": -123456,
                },
                {
                    "name": "Outputs/Bool",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Boolean,
                    "value": False,
                },
                {
                    "name": "Outputs/Float",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Float,
                    "value": 1.1234,
                },
                {
                    "name": "Outputs/Double",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Double,
                    "value": 122341.1234,
                },
                {
                    "name": "Properties/String",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.String,
                    "value": "Sony",
                },
                {
                    "name": "Properties/Text",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Text,
                    "value": "Sony made this device in 1986",
                },
            ],
        ),
        (  # Test for SPBArrayDataTypes
            2200000034,
            [
                {
                    "name": "Inputs/int8",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Int8Array,
                    "value": [10, 11, -23],
                },
                {
                    "name": "Inputs/int16",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Int16Array,
                    "value": [-30000, 30000],
                },
                {
                    "name": "Inputs/int32",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Int32Array,
                    "value": [-1, 315338746],
                },
                {
                    "name": "Inputs/int64",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Int64Array,
                    "value": [-4270929666821191986, -3601064768563266876],
                },
                {
                    "name": "Inputs/uint8",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.UInt8Array,
                    "value": [23, 250],
                },
                {
                    "name": "Inputs/uint16",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.UInt16Array,
                    "value": [30, 52360],
                },
                {
                    "name": "Inputs/uint32",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.UInt32Array,
                    "value": [52, 3293969225],
                },
                {
                    "name": "Inputs/uint64",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.UInt64Array,
                    "value": [5245, 16444743074749521625],
                },
                {
                    "name": "Inputs/datetime",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.UInt64Array,
                    "value": [1486144502122, 1486144505122],
                },
                {
                    "name": "Inputs/boolean",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.BooleanArray,
                    "value": [True, False, True],
                },
                {
                    "name": "Inputs/string",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.StringArray,
                    "value": ["I am a string", "I too am a string"],
                },
            ],
        ),
        (  # Test for SPBAdditionalDataTypes
            1500000019,
            [
                {
                    "name": "Inputs/UUID",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.UUID,
                    "value": "unique_id_123456789",
                },
                {
                    "name": "Inputs/bytes",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.Bytes,
                    "value": bytes([0x0C, 0x00, 0x00, 0x00, 0x34, 0xD0]),
                },
                {
                    "name": "Inputs/file",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.File,
                    "value": bytes(
                        [0xC7, 0xD0, 0x90, 0x75, 0x24, 0x01, 0x00, 0x00, 0xB8, 0xBA, 0xB8, 0x97, 0x81, 0x01, 0x00, 0x00]
                    ),
                    # TODO DataSet and Template
                },
                {
                    "name": "Inputs/dataset",
                    "timestamp": 1486144502122,
                    "datatype": SPBMetricDataTypes.DataSet,
                    "value": create_dummy_dataset(),
                    # TODO DataSet and Template
                },
            ],
        ),
    ],
)
def test_add_metric_and_ddata_msg(timestamp: float, metrics: list[dict]):
    """
    Test adding metrics to a DDATA msg
    SpBMessageGenerator#get_device_data_payload
    SpBMessageGenerator#add_metric
    """
    sparkplug_message = SpBMessageGenerator()
    payload = sparkplug_message.get_device_data_payload(timestamp=timestamp)
    alias = 0
    for metric in metrics:
        name: str = metric["name"]
        datatype: int = metric["datatype"]
        value = metric.get("value", None)
        metric_timestamp = metric.get("timestamp", None)
        if metric_timestamp is None:
            metric_timestamp = timestamp
        sparkplug_message.add_metric(
            payload_or_template=payload, name=name, alias=alias, datatype=datatype, value=value, timestamp=metric_timestamp
        )
        alias = alias + 1

    if timestamp is not None:
        assert payload.timestamp == int(timestamp)

    payload_metrics: list[Payload.Metric] = payload.metrics
    assert len(payload_metrics) == len(metrics)

    for payload_metric, metric in zip(payload_metrics, metrics):
        assert payload_metric.name == metric["name"]
        metric_timestamp = metric.get("timestamp", None)
        if metric_timestamp is None:
            metric_timestamp = int(timestamp)

        assert payload_metric.timestamp == metric_timestamp
        assert payload_metric.datatype == metric["datatype"]
        parsed_value = SPBMetricDataTypes(payload_metric.datatype).get_value_function(payload_metric)
        expected_value = metric["value"]

        match metric["datatype"]:
            # special considerations for signed ints
            case SPBMetricDataTypes.Int8:
                assert payload_metric.int_value == _convert_to_unsigned_int(expected_value, 8)

            case SPBMetricDataTypes.Int16:
                assert payload_metric.int_value == _convert_to_unsigned_int(expected_value, 16)

            case SPBMetricDataTypes.Int32:
                assert payload_metric.int_value == _convert_to_unsigned_int(expected_value, 32)

            case SPBMetricDataTypes.Int64 | SPBMetricDataTypes.DateTime:
                assert payload_metric.long_value == _convert_to_unsigned_int(expected_value, 64)

            case SPBMetricDataTypes.Float:
                # Manage decimal precision issues
                float_precision = 5
                expected_value = round(expected_value, float_precision)
                parsed_value = round(parsed_value, float_precision)

            case SPBMetricDataTypes.FloatArray:
                # Manage decimal precision issues
                float_precision = 5
                expected_value = [round(val, float_precision) for val in expected_value]
                parsed_value = [round(val, float_precision) for val in parsed_value]

            case _:  # All other cases
                pass

        assert parsed_value == expected_value


@pytest.mark.parametrize(
    "metrics",
    [
        # Test for SPBBasicDataTypes
        [
            {
                "name": "Inputs/int8",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Int8,
                "value": 10,
            },
            {
                "name": "Inputs/int8.Neg",
                "timestamp": 1486144502123,
                "datatype": SPBMetricDataTypes.Int8,
                "value": -10,
            },
            {
                "name": "Inputs/uint8",
                "timestamp": 1486144502123,
                "datatype": SPBMetricDataTypes.UInt8,
                "value": 10,
            },
            {
                "name": "Inputs/int16.neg",
                "timestamp": 1486144502123,
                "datatype": SPBMetricDataTypes.Int16,
                "value": -100,
            },
            {
                "name": "Inputs/uint16",
                "timestamp": 1486144502123,
                "datatype": SPBMetricDataTypes.UInt16,
                "value": 100,
            },
            {
                "name": "Properties/int32",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Int32,
                "value": 200,
            },
            {
                "name": "Properties/int32.neg",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Int32,
                "value": -200,
            },
            {
                "name": "Properties/Uint32",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UInt32,
                "value": 200,
            },
            {
                "name": "Outputs/DateTime",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.DateTime,
                "value": 1486144502122,
            },
            {
                "name": "Outputs/Uint64",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UInt64,
                "value": 123456,
            },
            {
                "name": "Outputs/int64.Neg",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Int64,
                "value": -123456,
            },
            {
                "name": "Outputs/Bool",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Boolean,
                "value": False,
            },
            {
                "name": "Outputs/Float",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Float,
                "value": 1.1234,
            },
            {
                "name": "Outputs/Double",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Double,
                "value": 122341.1234,
            },
            {
                "name": "Properties/String",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.String,
                "value": "Sony",
            },
            {
                "name": "Properties/Text",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Text,
                "value": "Sony made this device in 1986",
            },
        ],
        # Test for SPBArrayDataTypes
        [
            {
                "name": "Inputs/int8",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Int8Array,
                "value": [10, 11, -23],
            },
            {
                "name": "Inputs/int16",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Int16Array,
                "value": [-30000, 30000],
            },
            {
                "name": "Inputs/int32",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Int32Array,
                "value": [-1, 315338746],
            },
            {
                "name": "Inputs/int64",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Int64Array,
                "value": [-4270929666821191986, -3601064768563266876],
            },
            {
                "name": "Inputs/uint8",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UInt8Array,
                "value": [23, 250],
            },
            {
                "name": "Inputs/uint16",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UInt16Array,
                "value": [30, 52360],
            },
            {
                "name": "Inputs/uint32",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UInt32Array,
                "value": [52, 3293969225],
            },
            {
                "name": "Inputs/uint64",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UInt64Array,
                "value": [5245, 16444743074749521625],
            },
            {
                "name": "Inputs/datetime",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UInt64Array,
                "value": [1486144502122, 1486144505122],
            },
            {
                "name": "Inputs/boolean",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.BooleanArray,
                "value": [True, False, True],
            },
            {
                "name": "Inputs/string",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.StringArray,
                "value": ["I am a string", "I too am a string"],
            },
        ],
        # Test for SPBAdditionalDataTypes
        [
            {
                "name": "Inputs/UUID",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UUID,
                "value": "unique_id_123456789",
            },
            {
                "name": "Inputs/bytes",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Bytes,
                "value": bytes([0x0C, 0x00, 0x00, 0x00, 0x34, 0xD0]),
            },
            {
                "name": "Inputs/file",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.File,
                "value": bytes(
                    [0xC7, 0xD0, 0x90, 0x75, 0x24, 0x01, 0x00, 0x00, 0xB8, 0xBA, 0xB8, 0x97, 0x81, 0x01, 0x00, 0x00]
                ),
            },
            {
                "name": "Inputs/dataset",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.DataSet,
                "value": create_dummy_dataset(),
                # TODO Template
            },
        ],
    ],
)
def test_add_historical_metric_and_ddata_msg(metrics: list[dict]):
    """
    Test adding historic metrics to a DDATA msg
    SpBMessageGenerator#get_device_data_payload
    SpBMessageGenerator#add_historic_metric
    """
    sparkplug_message = SpBMessageGenerator()
    # prefer using device DData instead of Node
    payload = sparkplug_message.get_device_data_payload()
    timestamp = payload.timestamp
    for metric in metrics:
        name: str = metric["name"]
        datatype: int = metric["datatype"]
        value = metric.get("value", None)
        metric_timestamp = metric.get("timestamp", None)
        if metric_timestamp is None:
            metric_timestamp = timestamp
        sparkplug_message.add_historical_metric(
            payload=payload, name=name, datatype=datatype, value=value, timestamp=metric_timestamp
        )

    payload_metrics: list[Payload.Metric] = payload.metrics
    assert len(payload_metrics) == len(metrics)

    for payload_metric, metric in zip(payload_metrics, metrics):
        assert payload_metric.name == metric["name"]
        assert payload_metric.is_historical is True
        metric_timestamp = metric.get("timestamp", None)
        if metric_timestamp is None:
            metric_timestamp = int(timestamp)

        assert payload_metric.timestamp == metric_timestamp
        assert payload_metric.datatype == metric["datatype"]
        parsed_value = SPBMetricDataTypes(payload_metric.datatype).get_value_function(payload_metric)
        expected_value = metric["value"]
        match metric["datatype"]:
            # special considerations for signed ints
            case SPBMetricDataTypes.Int8:
                assert payload_metric.int_value == _convert_to_unsigned_int(expected_value, 8)

            case SPBMetricDataTypes.Int16:
                assert payload_metric.int_value == _convert_to_unsigned_int(expected_value, 16)

            case SPBMetricDataTypes.Int32:
                assert payload_metric.int_value == _convert_to_unsigned_int(expected_value, 32)

            case SPBMetricDataTypes.Int64 | SPBMetricDataTypes.DateTime:
                assert payload_metric.long_value == _convert_to_unsigned_int(expected_value, 64)

            case SPBMetricDataTypes.Float:
                # Manage decimal precision issues
                float_precision = 5
                expected_value = round(expected_value, float_precision)
                parsed_value = round(parsed_value, float_precision)

            case SPBMetricDataTypes.FloatArray:
                # Manage decimal precision issues
                float_precision = 5
                expected_value = [round(val, float_precision) for val in expected_value]
                parsed_value = [round(val, float_precision) for val in parsed_value]

            case _:  # All other cases
                pass

        assert parsed_value == expected_value


def test_add_null_metric():
    """
    Test case for  SpBMessageGenerator#add_null_metric
    """
    spb_mgs_gen = SpBMessageGenerator()
    payload = Payload()
    for datatype in SPBMetricDataTypes:
        if datatype != SPBMetricDataTypes.Unknown:  # skip Unknown
            metric = spb_mgs_gen.add_null_metric(
                payload_or_template=payload, name="test null" + datatype.field_name, datatype=datatype
            )
            assert metric.is_null is True
            assert metric.datatype == datatype
            assert metric.name == "test null" + datatype.field_name
            assert metric.timestamp is not None


@pytest.mark.parametrize(
    "name, columns, types, rows, float_precision",
    [
        (
            "Test DataSet - All datatypes",
            ["UInt32", "UInt64", "Float", "Double", "Boolean", "String"],
            [
                SPBDataSetDataTypes.UInt32,
                SPBDataSetDataTypes.UInt64,
                SPBDataSetDataTypes.Float,
                SPBDataSetDataTypes.Double,
                SPBDataSetDataTypes.Boolean,
                SPBDataSetDataTypes.String,
            ],
            [
                [10, 10000, 10.10, 1000.1234, True, "This is row 1"],  # row 1
                [20, 20000, 20.20, 2000.1234, False, "This is row 2"],  # row 2
            ],
            5,
        ),
        (
            "Test Only Boolean",
            ["Boolean", "Boolean"],
            [
                SPBDataSetDataTypes.Boolean,
                SPBDataSetDataTypes.Boolean,
            ],
            [
                [True, False],  # row 1
                [True, True],  # row 2
                [False, True],  # row 3
                [False, False],  # row 4
            ],
            0,
        ),
    ],
)
def test_get_dataset_metric(
    name: str,
    columns: list[str],
    types: list[SPBDataSetDataTypes],
    rows: Optional[list[list[int | float | bool | str]]],
    float_precision,
):
    """
    Test case for  SpBMessageGenerator#get_dataset_metric
    """
    spb_mgs_generator = SpBMessageGenerator()
    payload = Payload()

    data_set = spb_mgs_generator.get_dataset_metric(payload=payload, name=name, columns=columns, types=types, rows=rows)

    assert len(payload.metrics) == 1  # only the newly added dataset is in the metric
    assert payload.metrics[0].datatype == SPBMetricDataTypes.DataSet
    assert payload.metrics[0].dataset_value == data_set

    assert data_set.num_of_columns == len(columns)  # check num_of_columns was correctly set
    assert data_set.columns == columns
    assert data_set.types == types
    assert len(data_set.types) == len(data_set.columns) == data_set.num_of_columns

    for input_data_row, data_set_row in zip(rows, data_set.rows):
        for datatype, input_cell, element in zip(types, input_data_row, data_set_row.elements):
            if datatype == SPBDataSetDataTypes.Float:
                assert round(input_cell, float_precision) == round(
                    SPBDataSetDataTypes(datatype).get_value_from_sparkplug(element), float_precision
                )
            else:
                assert input_cell == SPBDataSetDataTypes(datatype).get_value_from_sparkplug(element)


@pytest.mark.parametrize(
    "is_multi_part, content_type, size, seq, file_name, file_type, md5, description",
    [
        (None, None, None, None, None, None, None, None),
        (False, "utf-8", 57, 1, "test.txt", "txt", "a8a42d159d5c815a80629c7ce443d404", "description"),
    ],
)
def test_add_metadata_to_metric(
    is_multi_part: Optional[bool],
    content_type: Optional[str],
    size: Optional[int],
    seq: Optional[int],
    file_name: Optional[str],
    file_type: Optional[str],
    md5: Optional[str],
    description: Optional[str],
):
    spb_mgs_generator = SpBMessageGenerator()
    payload = Payload()

    metric = spb_mgs_generator.add_metric(
        payload_or_template=payload,
        name="test metadata",
        datatype=SPBMetricDataTypes.File,
        value=bytes("I am a text file", "utf-8"),
    )

    spb_mgs_generator.add_metadata_to_metric(
        metric=metric,
        is_multi_part=is_multi_part,
        content_type=content_type,
        size=size,
        seq=seq,
        file_name=file_name,
        file_type=file_type,
        md5=md5,
        description=description,
    )
    if is_multi_part is not None:
        assert metric.metadata.is_multi_part == is_multi_part

    if content_type:
        assert metric.metadata.content_type == content_type

    if size is not None:
        assert metric.metadata.size == size

    if seq is not None:
        assert metric.metadata.seq == seq

    if file_name is not None:
        assert metric.metadata.file_name == file_name

    if file_type is not None:
        assert metric.metadata.file_type == file_type

    if md5 is not None:
        assert metric.metadata.md5 == md5

    if description is not None:
        assert metric.metadata.description == description


# def test_add_properties_to_metric():
#     pass


# def test_add_propertyset_to_metric():
#     pass


# def test_add_propertysets_to_metric():
#     pass
