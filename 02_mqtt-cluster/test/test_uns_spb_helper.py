"""
Test class for uns_sparkplugb.uns_spb_helper
"""
import pytest
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload
from uns_sparkplugb.uns_spb_enums import SPBMetricDataTypes
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

        assert parsed_value == metric["value"]
