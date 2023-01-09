"""
Tests for GraphDBHandler
"""
import pytest
from uns_graphdb.graphdb_handler import GraphDBHandler


@pytest.mark.parametrize(
    "nested_dict, expected_result",
    [
        # blank
        ({}, {}),
        # test for existing flat dict
        ({
            "a": "value1",
            "b": "value2"
        }, {
            "a": "value1",
            "b": "value2"
        }),
        # test attribute node_name
        ({
            "a": "value1",
            "node_name": "toUpper(*)"
        }, {
            "a": "value1",
            "NODE_NAME": "toUpper(*)"
        }),
        # test for existing  dict containing a list
        ({
            "a": "value1",
            "b": [10, 23, 23, 34]
        }, {
            "a": "value1",
            "b_0": 10,
            "b_1": 23,
            "b_2": 23,
            "b_3": 34
        }),
        # test for existing  dict containing dict and list
        ({
            "a": "value1",
            "b": [10, 23, 23, 34],
            "c": {
                "k1": "v1",
                "k2": 100
            }
        }, {
            "a": "value1",
            "b_0": 10,
            "b_1": 23,
            "b_2": 23,
            "b_3": 34,
            "c_k1": "v1",
            "c_k2": 100
        }),
        # test for 3 level nested
        ({
            "a": "value1",
            "l1": {
                "l2": {
                    "l3k1": "va1",
                    "l3k2": [10, 12],
                    "l3k3": 3.141
                },
                "l2kb": 100
            }
        }, {
            "a": "value1",
            "l1_l2_l3k1": "va1",
            "l1_l2_l3k2_0": 10,
            "l1_l2_l3k2_1": 12,
            "l1_l2_l3k3": 3.141,
            "l1_l2kb": 100
        }),
        (None, {}),
    ])
def test_flatten_json_for_neo4j(nested_dict: dict, expected_result: dict):
    """
    Testcase for GraphDBHandler.flatten_json_for_neo4j.
    Validate that the nested dict object is properly flattened
    """
    result = GraphDBHandler.flatten_json_for_neo4j(nested_dict)
    assert result == expected_result, f"""
            Json/dict to flatten:{nested_dict},
            Expected Result:{expected_result},
            Actual Result: {result}"""


@pytest.mark.parametrize("current_depth, expected_result", [
    (0, "ENTERPRISE"),
    (1, "FACILITY"),
    (2, "AREA"),
    (3, "LINE"),
    (4, "DEVICE"),
    (5, "DEVICE_depth_1"),
    (6, "DEVICE_depth_2"),
    (9, "DEVICE_depth_5"),
])
def test_get_node_name(current_depth: int, expected_result):
    """
    Test case for GraphDBHandler#get_node_name
    """
    node_types: tuple = ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE")
    result = GraphDBHandler.get_node_name(current_depth, node_types)
    assert result == expected_result, f"""
            Get Node name for Depth:{current_depth},
            From Node Types : {node_types}
            Expected Result:{expected_result},
            Actual Result: {result}"""
