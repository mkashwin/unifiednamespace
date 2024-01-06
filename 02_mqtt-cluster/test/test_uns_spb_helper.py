"""
Test class for uns_sparkplugb.uns_spb_helper
"""
from typing import Literal

import pytest
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload
from uns_sparkplugb.uns_spb_enums import SPBDataSetDataTypes, SPBMetricDataTypes
from uns_sparkplugb.uns_spb_helper import SpBMessageGenerator


def test_get_seq_num():
    """
    Test case for Spb_Message_Generator#get_seq_num()
    """
    sparkplug_message = SpBMessageGenerator()
    # Test sequence
    old_sequence = sparkplug_message.get_seq_num()
    assert old_sequence == 0, f"Sequence number should start with 0 but stated with {old_sequence}"

    for count in range(270):  # choose a number greater than 256 to test the counter reset
        new_sequence = sparkplug_message.get_seq_num()
        if old_sequence < 255:
            assert old_sequence == new_sequence - 1, f"Loop {count}: Sequence not incrementing-> {old_sequence}:{new_sequence}"
        else:
            assert new_sequence == 0, f"Loop {count}: Sequence number should reset to 0 after 256 but got  {new_sequence}"
        old_sequence = new_sequence


def test_get_birth_seq_num():
    """
    Test case for Spb_Message_Generator#get_birth_seq_num()
    """
    # Test sequence
    sparkplug_message = SpBMessageGenerator()
    old_sequence = sparkplug_message.get_birth_seq_num()
    assert old_sequence == 0, f"Sequence number should start with 0 but stated with {old_sequence}"

    for count in range(260):  # choose a number greater than 256 to test the counter reset
        new_sequence = sparkplug_message.get_birth_seq_num()
        if old_sequence < 255:
            assert old_sequence == new_sequence - 1, f"Loop {count}: Sequence not incrementing-> {old_sequence}:{new_sequence}"
        else:
            assert new_sequence == 0, f"Loop {count}: Sequence number should reset to 0 after 256 but got  {new_sequence}"
        old_sequence = new_sequence


def test_get_node_death_payload():
    """
    Test case for Spb_Message_Generator#get_node_death_payload()
    """
    sparkplug_message = SpBMessageGenerator()
    payload = sparkplug_message.get_node_death_payload()

    assert isinstance(payload, Payload)
    metrics = payload.metrics
    assert len(metrics) == 1

    assert metrics[0].name == "bdSeq"
    assert metrics[0].timestamp is not None
    assert metrics[0].datatype == SPBMetricDataTypes.Int64
    assert metrics[0].long_value == 0


def test_get_node_birth_payload():
    """
    Test case for Spb_Message_Generator#get_node_birth_payload()
    """
    sparkplug_message = SpBMessageGenerator()
    sparkplug_message.get_node_death_payload()
    payload = sparkplug_message.get_node_birth_payload()
    assert isinstance(payload, Payload)
    assert payload.seq == 0

    metrics = payload.metrics
    assert len(metrics) == 1

    assert metrics[0].name == "bdSeq"
    assert metrics[0].timestamp is not None
    assert metrics[0].datatype == SPBMetricDataTypes.Int64
    assert metrics[0].long_value == 1


def create_dataset() -> Payload.DataSet:
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


def convert_to_unsigned_int(value: int, factor: Literal[0, 8, 16, 32, 64]) -> int:
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
                    "value": create_dataset(),
                    # TODO DataSet and Template
                },
            ],
        ),
    ],
)
def test_create_ddata_payload_with_data(timestamp: float, metrics: list[dict]):
    """
    Test converting a JSON dict into a SPB DDATA payload
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
            payload=payload, name=name, alias=alias, datatype=datatype, value=value, timestamp=metric_timestamp
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
                assert payload_metric.int_value == convert_to_unsigned_int(expected_value, 8)

            case SPBMetricDataTypes.Int16:
                assert payload_metric.int_value == convert_to_unsigned_int(expected_value, 16)

            case SPBMetricDataTypes.Int32:
                assert payload_metric.int_value == convert_to_unsigned_int(expected_value, 32)

            case SPBMetricDataTypes.Int64 | SPBMetricDataTypes.DateTime:
                assert payload_metric.long_value == convert_to_unsigned_int(expected_value, 64)

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
