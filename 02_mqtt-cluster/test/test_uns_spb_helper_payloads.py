import pytest
from uns_sparkplugb import uns_spb_helper
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload
from uns_sparkplugb.uns_spb_enums import SPBMetricDataTypes
from uns_sparkplugb.uns_spb_helper import SpBMessageGenerator


@pytest.fixture(autouse=True)
def setup_alias_map():
    # clear the alias map for each test
    spb_mgs_gen = SpBMessageGenerator()
    spb_mgs_gen.alias_name_map.clear()


@pytest.mark.parametrize(
    "spb_dict,renamed_dict",
    [
        ({"test": "value"}, {"test": "value"}),  # no int_value, long_value etc.. attributes
        (
            {
                "timestamp": "1671554024644",
                "metrics": [
                    {
                        "name": "Inputs/A",
                        "timestamp": "1486144502122",
                        "alias": "0",
                        "datatype": 11,
                        "booleanValue": False,
                    },
                    {
                        "name": "Inputs/B",
                        "timestamp": "1486144502122",
                        "alias": "1",
                        "datatype": 11,
                        "booleanValue": False,
                    },
                    {
                        "name": "Outputs/E",
                        "timestamp": "1486144502122",
                        "alias": "2",
                        "datatype": 11,
                        "booleanValue": False,
                    },
                    {
                        "name": "Outputs/F",
                        "timestamp": "1486144502122",
                        "alias": "3",
                        "datatype": 11,
                        "booleanValue": False,
                    },
                    {
                        "name": "Properties/Hardware Make",
                        "timestamp": "1486144502122",
                        "alias": "4",
                        "datatype": 12,
                        "stringValue": "Sony",
                    },
                    {
                        "name": "Properties/Weight",
                        "timestamp": "1486144502122",
                        "alias": "5",
                        "datatype": 3,
                        "intValue": 200,
                    },
                ],
                "seq": "0",
            },
            {
                "timestamp": "1671554024644",
                "metrics": [
                    {
                        "name": "Inputs/A",
                        "timestamp": "1486144502122",
                        "alias": "0",
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Inputs/B",
                        "timestamp": "1486144502122",
                        "alias": "1",
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Outputs/E",
                        "timestamp": "1486144502122",
                        "alias": "2",
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Outputs/F",
                        "timestamp": "1486144502122",
                        "alias": "3",
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Properties/Hardware Make",
                        "timestamp": "1486144502122",
                        "alias": "4",
                        "datatype": 12,
                        "value": "Sony",
                    },
                    {
                        "name": "Properties/Weight",
                        "timestamp": "1486144502122",
                        "alias": "5",
                        "datatype": 3,
                        "value": 200,
                    },
                ],
                "seq": "0",
            },
        ),
        ("not a dict", "not a dict"),
    ],
)
def test__rename_dict(spb_dict: dict, renamed_dict: dict):
    assert uns_spb_helper._rename_keys(spb_dict) == renamed_dict


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


@pytest.mark.parametrize(
    "alias, timestamp, expected_exception",
    [
        (None, None, ValueError),  # Missing required parameters
        (2000, None, ValueError),  # Alias without name set
        (1, 173476070, ValueError),  # Alias without a mapped name
    ],
)
def test__get_metric_wrapper_exception(alias, timestamp, expected_exception):
    spb_mgs_generator = SpBMessageGenerator()
    with pytest.raises(expected_exception):
        spb_mgs_generator._get_metric_wrapper(Payload(), name=None, alias=alias, timestamp=timestamp)
    # test negative if alias was provided
    if alias is not None:
        spb_mgs_generator._get_metric_wrapper(Payload(), name="Name 1", alias=alias, timestamp=timestamp)
        with pytest.raises(expected_exception):
            spb_mgs_generator._get_metric_wrapper(Payload(), name="Name 2", alias=alias, timestamp=timestamp)


@pytest.mark.parametrize(
    "name, alias, timestamp",
    [
        ("SomeName", 123, None),
        ("SomeName", 123, 123345),
        ("SomeName", None, 123345),
    ],
)
def test__get_metric_wrapper(name, alias, timestamp):
    spb_mgs_generator = SpBMessageGenerator()
    payload = Payload()
    metric_1 = spb_mgs_generator._get_metric_wrapper(payload, name=name, alias=alias, timestamp=timestamp)
    assert metric_1.name == name
    assert metric_1.timestamp is not None

    if alias is not None:
        assert metric_1.alias == alias
        # check for ability to create a metric with alias and name
        metric_2 = spb_mgs_generator._get_metric_wrapper(payload, name=name, alias=alias, timestamp=timestamp)
        assert metric_2.name == name
        assert metric_2.alias == alias
        assert metric_2.timestamp is not None

        # check for ability to create a metric with alias and without name
        metric_3 = spb_mgs_generator._get_metric_wrapper(payload, name=None, alias=alias, timestamp=timestamp)
        assert metric_3.alias == alias
        assert spb_mgs_generator.alias_name_map[alias] == name


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
    spb_mgs_generator = SpBMessageGenerator()
    spb_mgs_generator.get_node_death_payload()
    payload_node1 = spb_mgs_generator.get_node_birth_payload()
    assert isinstance(payload_node1, Payload)
    assert payload_node1.seq == 0

    metrics = payload_node1.metrics
    assert len(metrics) == 1

    assert metrics[0].name == "bdSeq"
    assert metrics[0].timestamp is not None
    assert metrics[0].datatype == SPBMetricDataTypes.Int64
    assert metrics[0].long_value == 1


def test_get_node_data_payload():
    """
    Test case for Spb_Message_Generator#get_node_data_payload()
    """
    sparkplug_message = SpBMessageGenerator()
    sparkplug_message.get_node_death_payload()
    payload = sparkplug_message.get_node_data_payload()
    assert isinstance(payload, Payload)
    assert payload.seq == 0

    metrics = payload.metrics
    assert len(metrics) == 1

    assert metrics[0].name == "bdSeq"
    assert metrics[0].timestamp is not None
    assert metrics[0].datatype == SPBMetricDataTypes.Int64
    assert metrics[0].long_value == 1


def test_get_device_birth_payload():
    """
    Test case for Spb_Message_Generator#get_device_birth_payload()
    """
    sparkplug_message = SpBMessageGenerator()
    payload_device_1 = sparkplug_message.get_device_birth_payload()

    assert payload_device_1.timestamp is not None
    assert payload_device_1.seq == 0
    # create second message to check sequence is correct
    payload_device_2 = sparkplug_message.get_device_birth_payload()
    assert payload_device_2.timestamp is not None
    assert payload_device_2.seq == 1
