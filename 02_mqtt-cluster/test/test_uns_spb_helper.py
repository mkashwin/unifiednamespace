"""
Test class for uns_sparkplugb.uns_spb_helper
"""
from types import SimpleNamespace

import pytest
from google.protobuf.json_format import MessageToDict
import uns_sparkplugb.uns_spb_helper as uns_spb_helper
from uns_sparkplugb.generated import sparkplug_b_pb2

# Dict containing value types as key value pair.
# Convert this to a SimpleNamespace to be able to access the attributes via dot notation
metric_dict = {
    "int_value": None,
    "long_value": None,
    "float_value": None,
    "double_value": None,
    "string_value": None,
    "bytes_value": None,
    "boolean_value": None,
    "template_value": None,
    "datatype": None
}


@pytest.mark.parametrize(
    "value,metric,factor, metric_value",
    [(10, SimpleNamespace(**metric_dict), 0, 10),
     (10, SimpleNamespace(**metric_dict), 8, 10),
     (-10, SimpleNamespace(**metric_dict), 8, -10 + 2**8),
     (10, SimpleNamespace(**metric_dict), 16, 10),
     (-10, SimpleNamespace(**metric_dict), 16, -10 + 2**16),
     (10, SimpleNamespace(**metric_dict), 32, 10),
     (-10, SimpleNamespace(**metric_dict), 32, -10 + 2**32)])
def test_set_int_value_in_metric(value: int, metric: dict, factor: int,
                                 metric_value: int):
    """
    Test case for uns_spb_helper#set_int_value_in_metric
    """
    uns_spb_helper.set_int_value_in_metric(value, metric, factor)
    assert (
        metric.int_value == metric_value
    ), f"Expecting metric value to be: {metric_value}, but got {metric.int_value} "
    for datatype in metric_dict:
        if datatype != "int_value":
            assert (
                metric.__dict__[datatype] is None
            ), f"Datatype: {datatype} should be null in  {metric} for all types except int_value"


@pytest.mark.parametrize(
    "value,metric,factor, metric_value",
    [(10, SimpleNamespace(**metric_dict), 0, 10),
     (-10, SimpleNamespace(**metric_dict), 64, -10 + 2**64),
     (10, SimpleNamespace(**metric_dict), 64, 10)])
def test_set_long_value_in_metric(value: int, metric: dict, factor: int,
                                  metric_value: int):
    """
    Test case for uns_spb_helper#set_long_value_in_metric
    """
    # In python all long values are int
    uns_spb_helper.set_long_value_in_metric(value, metric, factor)
    assert (
        metric.long_value == metric_value
    ), f"Expecting metric value to be: {metric_value}, but got {metric.long_value} "
    for datatype in metric_dict:
        if datatype != "long_value":
            assert (
                metric.__dict__[datatype] is None
            ), f"Datatype: {datatype} should be null in  {metric} for all types except long_value"


@pytest.mark.parametrize("value,metric, metric_value", [
    (10.0, SimpleNamespace(**metric_dict), 10.0),
    (-10.0, SimpleNamespace(**metric_dict), -10.0),
])
def test_set_float_value_in_metric(value: float, metric: dict,
                                   metric_value: float):
    """
    Test case for uns_spb_helper#set_float_value_in_metric
    """
    uns_spb_helper.set_float_value_in_metric(value, metric)
    assert (
        metric.float_value == metric_value
    ), f"Expecting metric value to be: {metric_value}, but got {metric.float_value} "
    for datatype in metric_dict:
        if datatype != "float_value":
            assert (
                metric.__dict__[datatype] is None
            ), f"Datatype: {datatype} should be null in  {metric} for all types except float_value"


@pytest.mark.parametrize("value,metric, metric_value", [
    (10.0, SimpleNamespace(**metric_dict), 10.0),
    (-10.0, SimpleNamespace(**metric_dict), -10.0),
])
def test_set_double_value_in_metric(value: float, metric: dict,
                                    metric_value: float):
    """
    Test case for uns_spb_helper#set_double_value_in_metric
    """
    uns_spb_helper.set_double_value_in_metric(value, metric)
    assert (
        metric.double_value == metric_value
    ), f"Expecting metric value to be: {metric_value}, but got {metric.double_value} "
    for datatype in metric_dict:
        if datatype != "double_value":
            assert (
                metric.__dict__[datatype] is None
            ), f"Datatype: {datatype} should be null in  {metric} for all types except double_value"


@pytest.mark.parametrize("value,metric, metric_value", [
    (True, SimpleNamespace(**metric_dict), True),
    (False, SimpleNamespace(**metric_dict), False),
])
def test_set_boolean_value_in_metric(value: bool, metric: dict,
                                     metric_value: bool):
    """
    Test case for uns_spb_helper#set_boolean_value_in_metric
    """
    uns_spb_helper.set_boolean_value_in_metric(value, metric)
    assert (
        metric.boolean_value == metric_value
    ), f"Expecting metric value to be:{metric_value}, got:{metric.boolean_value}"
    for datatype in metric_dict:
        if datatype != "boolean_value":
            assert (
                metric.__dict__[datatype] is None
            ), f"Datatype: {datatype} must be null in {metric} for all types except boolean_value"


@pytest.mark.parametrize("value,metric, metric_value", [
    ("Test String1", SimpleNamespace(**metric_dict), "Test String1"),
    ("""Test String2\nLine2""", SimpleNamespace(**metric_dict),
     """Test String2\nLine2"""),
])
def test_set_string_value_in_metric(value: str, metric: dict,
                                    metric_value: str):
    """
    Test case for uns_spb_helper#set_string_value_in_metric
    """
    uns_spb_helper.set_string_value_in_metric(value, metric)
    assert (
        metric.string_value == metric_value
    ), f"Expecting metric value to be: {metric_value}, but got {metric.string_value}"
    for datatype in metric_dict:
        if datatype != "string_value":
            assert (
                metric.__dict__[datatype] is None
            ), f"Datatype: {datatype} should be null in  {metric} for all types except string_value"


@pytest.mark.parametrize("value,metric, metric_value", [
    (bytes("Test String1", "utf-8"), SimpleNamespace(**metric_dict),
     bytes("Test String1", "utf-8")),
    (bytes("""Test String2\nLine2""", "utf-8"), SimpleNamespace(**metric_dict),
     bytes("""Test String2\nLine2""", "utf-8")),
])
def test_set_bytes_value_in_metric(value: bytes, metric: dict,
                                   metric_value: bytes):
    """
    Test case for uns_spb_helper#set_bytes_value_in_metric
    """
    uns_spb_helper.set_bytes_value_in_metric(value, metric)
    assert (
        metric.bytes_value == metric_value
    ), f"Expecting metric value to be: {metric_value}, but got {metric.string_value}"
    for datatype in metric_dict:
        if datatype != "bytes_value":
            assert (
                metric.__dict__[datatype] is None
            ), f"Datatype: {datatype} should be null in  {metric} for all types except bytes_value"


def test_get_seq_num():
    """
    Test case for uns_spb_helper.Spb_Message_Generator#get_seq_num()
    """
    sparkplug_message = uns_spb_helper.SpBMessageGenerator()
    # Test sequence
    old_sequence = sparkplug_message.get_seq_num()
    assert old_sequence == 0, f"Sequence number should start with 0 but stated with {old_sequence}"

    for count in range(
            270):  # choose a number greater than 256 to test the counter reset
        new_sequence = sparkplug_message.get_seq_num()
        if old_sequence < 255:
            assert (
                old_sequence == new_sequence - 1
            ), f"Loop {count}: Sequence not incrementing-> {old_sequence}:{new_sequence}"
        else:
            assert (
                new_sequence == 0
            ), f"Loop {count}: Sequence number should reset to 0 after 256 but got  {new_sequence}"
        old_sequence = new_sequence


def test_get_birth_seq_num():
    """
    Test case for uns_spb_helper.Spb_Message_Generator#get_birth_seq_num()
    """
    # Test sequence
    sparkplug_message = uns_spb_helper.SpBMessageGenerator()
    old_sequence = sparkplug_message.get_birth_seq_num()
    assert old_sequence == 0, f"Sequence number should start with 0 but stated with {old_sequence}"

    for count in range(
            260):  # choose a number greater than 256 to test the counter reset
        new_sequence = sparkplug_message.get_birth_seq_num()
        if old_sequence < 255:
            assert (
                old_sequence == new_sequence - 1
            ), f"Loop {count}: Sequence not incrementing-> {old_sequence}:{new_sequence}"
        else:
            assert (
                new_sequence == 0
            ), f"Loop {count}: Sequence number should reset to 0 after 256 but got  {new_sequence}"
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
    assert metric.get("datatype") == sparkplug_b_pb2.Int64
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

    assert getattr(payload, "seq") == 0
    assert metric.get("name") == "bdSeq"
    assert metric.get("timestamp") is not None
    assert metric.get("datatype") == sparkplug_b_pb2.Int64
    assert int(metric.get("longValue")) == 1


@pytest.mark.parametrize(
    "timestamp, metrics", [(
        1671554024644, [
            {
                'name': 'Inputs/A', 'timestamp': 1486144502122,
                'datatype': 11, 'value': False
            }, {
                'name': 'Inputs/B', 'timestamp': 1486144502122,
                'datatype': 11, 'value': False
            }, {
                'name': 'Outputs/E', 'timestamp': 1486144502122,
                'datatype': 11, 'value': False
            }, {
                'name': 'Outputs/F', 'timestamp': 1486144502122,
                'datatype': 11, 'value': False
            }, {
                'name': 'Properties/Hardware Make', 'timestamp': 1486144502122,
                'datatype': 12, 'value': 'Sony'
            }, {
                'name': 'Properties/Weight', 'timestamp': 1486144502122,
                'datatype': 3, 'value': 200
            }]
    )]
    )
def test_create_ddata_payload_withData(timestamp: float, metrics: list[dict]):
    """
    Test converting a JSON dict into a SPB DDATA payload
    """
    sparkplug_message = uns_spb_helper.SpBMessageGenerator()
    payload = sparkplug_message.get_device_data_payload(timestamp=timestamp)
    alias = 0
    for metric in metrics:
        name: str = metric["name"]
        datatype: int = metric["datatype"]
        value = metric.get("value", None)
        metric_timestamp = metric.get("timestamp", None)
        if metric_timestamp is None:
            metric_timestamp = timestamp
        sparkplug_message.add_metric(payload=payload, name=name,
                                     alias=alias, datatype=datatype,
                                     value=value, timestamp=metric_timestamp)
        alias = alias + 1

    print(payload.SerializeToString())
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
            case sparkplug_b_pb2.Int8: parsed_value = parsed_metric["intValue"]
            case sparkplug_b_pb2.Int16: parsed_value = parsed_metric["intValue"]
            case sparkplug_b_pb2.Int32: parsed_value = parsed_metric["intValue"]
            case sparkplug_b_pb2.Int64: parsed_value = parsed_metric["longValue"]
            case sparkplug_b_pb2.UInt8: parsed_value = parsed_metric["intValue"]
            case sparkplug_b_pb2.UInt16: parsed_value = parsed_metric["intValue"]
            case sparkplug_b_pb2.UInt32: parsed_value = parsed_metric["intValue"]
            case sparkplug_b_pb2.UInt64: parsed_value = parsed_metric["longValue"]
            case sparkplug_b_pb2.Float: parsed_value = parsed_metric["floatValue"]
            case sparkplug_b_pb2.Double: parsed_value = parsed_metric["doubleValue"]
            case sparkplug_b_pb2.Boolean: parsed_value = parsed_metric["booleanValue"]
            case sparkplug_b_pb2.String: parsed_value = parsed_metric["stringValue"]
            case sparkplug_b_pb2.DateTime: parsed_value = parsed_metric["longValue"]
            case sparkplug_b_pb2.Text: parsed_value = parsed_metric["stringValue"]
            case sparkplug_b_pb2.UUID: parsed_value = parsed_metric["stringValue"]
            case sparkplug_b_pb2.Bytes: parsed_value = parsed_metric["bytesValue"]
            case sparkplug_b_pb2.File: parsed_value = parsed_metric["bytesValue"]
            case sparkplug_b_pb2.DataSet:
                continue
            case sparkplug_b_pb2.Template:
                continue

        assert parsed_value == metric["value"]
