"""
Test class for uns_sparkplugb.uns_spb_helper
"""
from typing import Optional

import pytest
from google.protobuf.json_format import MessageToDict
from uns_sparkplugb import uns_spb_helper
from uns_sparkplugb.uns_spb_enums import SPBMetricDataTypes


def test_get_seq_num():
    """
    Test case for uns_spb_helper.Spb_Message_Generator#get_seq_num()
    """
    sparkplug_message = uns_spb_helper.SpBMessageGenerator()
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
    Test case for uns_spb_helper.Spb_Message_Generator#get_birth_seq_num()
    """
    # Test sequence
    sparkplug_message = uns_spb_helper.SpBMessageGenerator()
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
    Test case for uns_spb_helper.Spb_Message_Generator#get_node_death_payload()
    """
    sparkplug_message = uns_spb_helper.SpBMessageGenerator()
    payload = sparkplug_message.get_node_death_payload()
    payload_dict = MessageToDict(payload)
    metric = payload_dict.get("metrics")[0]
    assert metric.get("name") == "bdSeq"
    assert metric.get("timestamp") is not None
    assert metric.get("datatype") == uns_spb_helper.SPBMetricDataTypes.Int64
    assert int(metric.get("longValue")) == 0


def test_get_node_birth_payload():
    """
    Test case for uns_spb_helper.Spb_Message_Generator#get_node_birth_payload()
    """
    sparkplug_message = uns_spb_helper.SpBMessageGenerator()
    sparkplug_message.get_node_death_payload()
    payload = sparkplug_message.get_node_birth_payload()
    payload_dict: dict = MessageToDict(payload)
    metric = payload_dict.get("metrics")[0]

    assert payload.seq == 0
    assert metric.get("name") == "bdSeq"
    assert metric.get("timestamp") is not None
    assert metric.get("datatype") == SPBMetricDataTypes.Int64
    assert int(metric.get("longValue")) == 1


@pytest.mark.parametrize(
    "timestamp, metrics",
    [
        (
            1671554024644,
            [
                {
                    "name": "Inputs/A",
                    "timestamp": 1486144502122,
                    "datatype": 11,
                    "value": False,
                },
                {
                    "name": "Inputs/B",
                    "timestamp": 1486144502122,
                    "datatype": 11,
                    "value": False,
                },
                {
                    "name": "Outputs/E",
                    "timestamp": 1486144502122,
                    "datatype": 11,
                    "value": False,
                },
                {
                    "name": "Outputs/F",
                    "timestamp": 1486144502122,
                    "datatype": 11,
                    "value": False,
                },
                {
                    "name": "Properties/Hardware Make",
                    "timestamp": 1486144502122,
                    "datatype": 12,
                    "value": "Sony",
                },
                {
                    "name": "Properties/Weight",
                    "timestamp": 1486144502122,
                    "datatype": 3,
                    "value": 200,
                },
            ],
        )
    ],
)
def test_create_ddata_payload_with_data(timestamp: float, metrics: list[dict]):
    """
    Test converting a JSON dict into a SPB DDATA payload
    """
    sparkplug_message = uns_spb_helper.SpBMessageGenerator()
    payload = sparkplug_message.get_device_data_payload(timestamp=timestamp)
    alias = 0
    for metric in metrics:
        name: Optional[str] = metric["name"]
        datatype: int = metric["datatype"]
        value = metric.get("value", None)
        metric_timestamp = metric.get("timestamp", None)
        if metric_timestamp is None:
            metric_timestamp = timestamp
        sparkplug_message.add_metric(
            payload=payload, name=name, alias=alias, datatype=datatype, value=value, timestamp=metric_timestamp
        )
        alias = alias + 1

    parsed_payload: dict = MessageToDict(payload)

    if timestamp is not None:
        assert int(parsed_payload["timestamp"]) == int(timestamp)

    parsed_payload_metrics: list[dict] = parsed_payload["metrics"]
    assert len(parsed_payload_metrics) == len(metrics)

    for parsed_metric, metric in zip(parsed_payload_metrics, metrics):
        assert parsed_metric["name"] == metric["name"]
        metric_timestamp = metric.get("timestamp", None)
        if metric_timestamp is None:
            metric_timestamp = timestamp
        # FIXME for some reason the timestamp attribute is being returned as a string instead of float
        assert int(parsed_metric["timestamp"]) == int(metric_timestamp)
        assert parsed_metric["datatype"] == metric["datatype"]
        parsed_value = None
        match parsed_metric["datatype"]:
            case SPBMetricDataTypes.Int8:
                parsed_value = parsed_metric["intValue"]
            case SPBMetricDataTypes.Int16:
                parsed_value = parsed_metric["intValue"]
            case SPBMetricDataTypes.Int32:
                parsed_value = parsed_metric["intValue"]
            case SPBMetricDataTypes.Int64:
                parsed_value = parsed_metric["longValue"]
            case SPBMetricDataTypes.UInt8:
                parsed_value = parsed_metric["intValue"]
            case SPBMetricDataTypes.UInt16:
                parsed_value = parsed_metric["intValue"]
            case SPBMetricDataTypes.UInt32:
                parsed_value = parsed_metric["intValue"]
            case SPBMetricDataTypes.UInt64:
                parsed_value = parsed_metric["longValue"]
            case SPBMetricDataTypes.Float:
                parsed_value = parsed_metric["floatValue"]
            case SPBMetricDataTypes.Double:
                parsed_value = parsed_metric["doubleValue"]
            case SPBMetricDataTypes.Boolean:
                parsed_value = parsed_metric["booleanValue"]
            case SPBMetricDataTypes.String:
                parsed_value = parsed_metric["stringValue"]
            case SPBMetricDataTypes.DateTime:
                parsed_value = parsed_metric["longValue"]
            case SPBMetricDataTypes.Text:
                parsed_value = parsed_metric["stringValue"]
            case SPBMetricDataTypes.UUID:
                parsed_value = parsed_metric["stringValue"]
            case SPBMetricDataTypes.Bytes:
                parsed_value = parsed_metric["bytesValue"]
            case SPBMetricDataTypes.File:
                parsed_value = parsed_metric["bytesValue"]
            case SPBMetricDataTypes.DataSet:
                assert pytest.fail(), "DataSet not yet supported"
            case SPBMetricDataTypes.Template:
                assert pytest.fail(), "Template not yet supported"

        assert parsed_value == metric["value"]
