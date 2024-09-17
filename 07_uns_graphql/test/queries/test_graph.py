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
Test cases for uns_graphql.queries.graph.Query
"""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
import strawberry
from neo4j import Record
from neo4j.graph import Node, Relationship
from uns_graphql.backend.graphdb import GraphDB
from uns_graphql.graphql_config import GraphDBConfig
from uns_graphql.input.mqtt import MQTTTopic, MQTTTopicInput
from uns_graphql.queries.graph import NODE_NAME_KEY, NODE_RELATION_NAME, REL_ATTR_KEY, REL_ATTR_TYPE, REL_INDEX
from uns_graphql.queries.graph import Query as GraphQuery
from uns_graphql.type.isa95_node import UNSNode
from uns_graphql.type.sparkplugb_node import SPBNode

main_node = MagicMock(spec=Node, autospec=True)
main_node.element_id = "main_node_id"
main_node.labels = frozenset({"LINE"})
main_node.items.return_value = {
    "node_name": "ln4",
    "_created_timestamp": 1486144500000,
    "_modified_timestamp": 1486144510000,
    "TestMetric2": "Test_UNS_with_NestedLists",
    "timestamp": 1486144510000,
}.items()
main_node.__getitem__.side_effect = (
    lambda key: "ln4"
    if key == NODE_NAME_KEY
    else 1486144500000
    if key == "_created_timestamp" or key == "_modified_timestamp" or key == "timestamp"
    else "Test_UNS_with_NestedLists"
    if key == "TestMetric2"
    else None
)


uns_child_1 = MagicMock(spec=Node, autospec=True)
uns_child_1.element_id = "nested_child_1"
uns_child_1.labels = frozenset({"NESTED_ATTRIBUTE", "TEST_MULTIPLE_LABELS"})
uns_child_1.items.return_value = {"node_name": "dict_list_1", "_created_timestamp": 1486144500000, "x": "y"}.items()
uns_child_1.__getitem__.side_effect = (
    lambda key: "dict_list_1"
    if key == NODE_NAME_KEY
    else 1486144500000
    if key == "_created_timestamp"
    else "y"
    if key == "x"
    else None
)


uns_child_2 = MagicMock(spec=Node, autospec=True)
uns_child_2.element_id = "nested_child_2"
uns_child_2.labels = frozenset({"NESTED_ATTRIBUTE"})
uns_child_2.items.return_value = {"node_name": "dict_list_0", "_created_timestamp": 1486144500000, "a": "b"}.items()
uns_child_2.__getitem__.side_effect = (
    lambda key: "dict_list_0"
    if key == NODE_NAME_KEY
    else 1486144500000
    if key == "_created_timestamp"
    else "b"
    if key == "a"
    else None
)

uns_child_3 = MagicMock(spec=Node, autospec=True)
uns_child_3.element_id = "nested_child_3"
uns_child_3.labels = frozenset({"NESTED_ATTRIBUTE"})
uns_child_3.items.return_value = {
    "node_name": "nested",
    "_created_timestamp": 1486144500000,
    "nest 1": "nest val 1",
}.items()
uns_child_3.__getitem__.side_effect = (
    lambda key: "nested"
    if key == NODE_NAME_KEY
    else 1486144500000
    if key == "_created_timestamp"
    else "nest val 1"
    if key == "nest 1"
    else None
)

uns_rel_1 = MagicMock(spec=Relationship, autospec=True)
uns_rel_1.element_id = "relationship_1 main_node->nested_child_1"
uns_rel_1.nodes = [main_node, uns_child_1]
uns_rel_1.type = NODE_RELATION_NAME
uns_rel_1.__getitem__.side_effect = (
    lambda key: "dict_list" if key == REL_ATTR_KEY else "1" if key == REL_INDEX else "list" if key == REL_ATTR_TYPE else None
)

uns_rel_2 = MagicMock(spec=Relationship, autospec=True)
uns_rel_2.element_id = "relationship_1 main_node->nested_child_2"
uns_rel_2.nodes = [main_node, uns_child_2]
uns_rel_2.type = NODE_RELATION_NAME
uns_rel_2.__getitem__.side_effect = (
    lambda key: "dict_list" if key == REL_ATTR_KEY else "0" if key == REL_INDEX else "list" if key == REL_ATTR_TYPE else None
)

uns_rel_3 = MagicMock(spec=Relationship, autospec=True)
uns_rel_3.element_id = "relationship_1 main_node->nested_child_3"
uns_rel_3.nodes = [main_node, uns_child_3]
uns_rel_3.type = NODE_RELATION_NAME
uns_rel_3.__getitem__.side_effect = (
    lambda key: "nested_dict" if key == REL_ATTR_KEY else "dict" if key == REL_ATTR_TYPE else None
)
uns_result: list[Record] = [
    Record(
        {
            "fullName": "test/uns/ar2/ln4",
            "resultNode": main_node,
            "nestedChildren": [uns_child_1, uns_child_2, uns_child_3],
            "relationships": [uns_rel_1, uns_rel_2, uns_rel_3],
        }
    )
]
uns_dict_result = {
    "TestMetric2": "Test_UNS_with_NestedLists",
    "timestamp": 1486144510000,
    "nested_dict": {"nest 1": "nest val 1"},
    "dict_list": [{"a": "b"}, {"x": "y"}],
}

sbp_node = MagicMock(spec=Node, autospec=True)
sbp_node.element_id = "4:957eb9e7-0a52-4e69-975c-087ce8dcb4c4:657"
sbp_node.labels = frozenset({"EDGE_NODE"})
sbp_node.items.return_value = {
    "_created_timestamp": 1671554024644,
    "node_name": "eon1",
    "seq": 0,
    "timestamp": 1671554024644,
}.items()
sbp_node.__getitem__.side_effect = (
    lambda key: "eon1"
    if key == NODE_NAME_KEY
    else 1486144500000
    if key == "_created_timestamp" or key == "timestamp"
    else 0
    if key == "seq"
    else None
)

spb_child_1 = MagicMock(spec=Node, autospec=True)
spb_child_1.element_id = "4:957eb9e7-0a52-4e69-975c-087ce8dcb4c4:800"
spb_child_1.labels = frozenset({"NESTED_ATTRIBUTE"})
spb_child_1.items.return_value = {
    "datatype": 11,
    "_created_timestamp": 1671554024644,
    "node_name": "Outputs/F",
    "name": "Outputs/F",
    "alias": 3,
    "value": False,
    "timestamp": 1486144502122,
}.items()
spb_child_1.__getitem__.side_effect = (
    lambda key: "Outputs/F"
    if key == NODE_NAME_KEY or key == "name"
    else 11
    if key == "datatype"
    else False
    if key == "value"
    else 3
    if key == "alias"
    else 1671554024644
    if key == "_created_timestamp"
    else 1486144502122
    if key == "timestamp"
    else None
)

spb_child_2 = MagicMock(spec=Node, autospec=True)
spb_child_2.element_id = "4:957eb9e7-0a52-4e69-975c-087ce8dcb4c4:900"
spb_child_2.labels = frozenset({"NESTED_ATTRIBUTE"})
spb_child_2.items.return_value = {
    "datatype": 11,
    "_created_timestamp": 1671554024644,
    "node_name": "Inputs/B",
    "name": "Inputs/B",
    "alias": 1,
    "value": False,
    "timestamp": 1486144502122,
}.items()
spb_child_2.__getitem__.side_effect = (
    lambda key: "Inputs/B"
    if key == NODE_NAME_KEY or key == "name"
    else 11
    if key == "datatype"
    else False
    if key == "value"
    else 1
    if key == "alias"
    else 1671554024644
    if key == "_created_timestamp"
    else 1486144502122
    if key == "timestamp"
    else None
)

spb_child_3 = MagicMock(spec=Node, autospec=True)
spb_child_3.element_id = "4:957eb9e7-0a52-4e69-975c-087ce8dcb4c4:950"
spb_child_3.labels = frozenset({"NESTED_ATTRIBUTE"})
spb_child_3.items.return_value = {
    "datatype": 11,
    "_created_timestamp": 1671554024644,
    "node_name": "Inputs/A",
    "name": "Inputs/A",
    "alias": 0,
    "value": False,
    "timestamp": 1486144502122,
}.items()
spb_child_3.__getitem__.side_effect = (
    lambda key: "Inputs/A"
    if key == NODE_NAME_KEY or key == "name"
    else 11
    if key == "datatype"
    else False
    if key == "value"
    else 0
    if key == "alias"
    else 1671554024644
    if key == "_created_timestamp"
    else 1486144502122
    if key == "timestamp"
    else None
)

spb_rel_1 = MagicMock(spec=Relationship, autospec=True)
spb_rel_1.element_id = "4:957eb9e7-0a52-4e69-975c-087ce8dcb4c4:703"
spb_rel_1.nodes = [sbp_node, spb_child_1]
spb_rel_1.type = NODE_RELATION_NAME
spb_rel_1.__getitem__.side_effect = (
    lambda key: "metrics" if key == REL_ATTR_KEY else "2" if key == REL_INDEX else "list" if key == REL_ATTR_TYPE else None
)

spb_rel_2 = MagicMock(spec=Relationship, autospec=True)
spb_rel_2.element_id = "4:957eb9e7-0a52-4e69-975c-087ce8dcb4c4:702"
spb_rel_2.nodes = [sbp_node, spb_child_2]
spb_rel_2.type = NODE_RELATION_NAME
spb_rel_2.__getitem__.side_effect = (
    lambda key: "metrics" if key == REL_ATTR_KEY else "1" if key == REL_INDEX else "list" if key == REL_ATTR_TYPE else None
)
spb_rel_3 = MagicMock(spec=Relationship, autospec=True)
spb_rel_3.element_id = "4:957eb9e7-0a52-4e69-975c-087ce8dcb4c4:701"
spb_rel_3.nodes = [sbp_node, spb_child_3]
spb_rel_3.type = NODE_RELATION_NAME
spb_rel_3.__getitem__.side_effect = (
    lambda key: "metrics" if key == REL_ATTR_KEY else "0" if key == REL_INDEX else "list" if key == REL_ATTR_TYPE else None
)

spb_result: list[Record] = [
    Record(
        {
            "fullName": "spBv1.0/uns_group/NDATA/eon1",
            "resultNode": sbp_node,
            "nestedChildren": [spb_child_1, spb_child_2, spb_child_3],
            "relationships": [spb_rel_1, spb_rel_2, spb_rel_3],
        }
    )
]
spb_result_dict: dict = {
    "seq": 0,
    "timestamp": 1671554024644,
    "metrics": [
        {
            "datatype": 11,
            "name": "Inputs/A",
            "alias": 0,
            "value": False,
            "timestamp": 1486144502122,
        },
        {
            "datatype": 11,
            "name": "Inputs/B",
            "alias": 1,
            "value": False,
            "timestamp": 1486144502122,
        },
        {
            "datatype": 11,
            "name": "Outputs/F",
            "alias": 3,
            "value": False,
            "timestamp": 1486144502122,
        },
    ],
}

# Mock the datahandler for UNS queries
mocked_uns_graphdb = MagicMock(spec=GraphDB, autospec=True)
# Mocking all the query functions to give the same result
mocked_uns_graphdb.execute_query.return_value = uns_result

# Mock the datahandler for SPB queries
mocked_spb_graphdb = MagicMock(spec=GraphDB, autospec=True)
# Mocking all the query functions to give the same result
mocked_spb_graphdb.execute_query.return_value = spb_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "topics,has_result_errors",
    [
        (["topic1/#"], False),
        (["topic1/+"], False),
        (["topic1/testString"], False),
        (["#"], False),
        (["topic1/#", "topic3"], False),
        (["topic1/subtopic1", "topic2/topic3"], False),
        (["+"], False),
    ],
)
async def test_get_uns_nodes(
    topics: list[str],
    has_result_errors: bool,
):
    mqtt_topic_list = [MQTTTopicInput.from_pydantic(MQTTTopic(topic=topic)) for topic in topics]
    with patch("uns_graphql.queries.graph.GraphDB", return_value=mocked_uns_graphdb):
        graph_query = GraphQuery()
        try:
            result = await graph_query.get_uns_nodes(mqtt_topics=mqtt_topic_list)
        except Exception as ex:
            assert has_result_errors, f"Should not throw any exceptions. Got {ex}"
        assert result is not None  # test was successful


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "property_keys, topics, exclude_topics, has_result_errors",
    [
        (["prop1"], ["topic1/#"], False, False),
        ("prop1", ["topic1/#"], False, False),
        (["prop1", "prop2"], ["topic1/+"], True, False),
        (["124"], None, None, False),
        (["prop1", "prop2"], ["topic1/subtopic"], True, False),
        (["prop1", "prop2"], ["topic1/#", "topic3"], True, False),
        (["prop1", "prop2"], ["+"], True, False),
    ],
)
async def test_get_uns_nodes_by_property(
    property_keys,
    topics: list[str],
    exclude_topics,
    has_result_errors: bool,
):
    mqtt_topic_list = None
    if topics is not None:
        mqtt_topic_list = [MQTTTopicInput.from_pydantic(MQTTTopic(topic=topic)) for topic in topics]
    with patch("uns_graphql.queries.graph.GraphDB", return_value=mocked_uns_graphdb):
        graph_query = GraphQuery()
        try:
            result = await graph_query.get_uns_nodes_by_property(
                property_keys=property_keys, topics=mqtt_topic_list, exclude_topics=exclude_topics
            )
        except Exception as ex:
            assert has_result_errors, f"Should not throw any exceptions. Got {ex}"
        assert result is not None  # test was successful


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "metric_names",
    [(["Inputs/A"]), ("Inputs/A"), (["Inputs/A", "Inputs/B"]), (["Output/F"]), ([]), (None)],
)
async def test_get_spb_nodes_by_metric(metric_names: list[str]):
    with patch("uns_graphql.queries.graph.GraphDB", return_value=mocked_spb_graphdb):
        graph_query = GraphQuery()
        try:
            result = await graph_query.get_spb_nodes_by_metric(metric_names=metric_names)
        except Exception as ex:
            pytest.fail(f"Should not throw any exceptions. Got {ex}")
        assert result is not None  # test was successful


@pytest.mark.parametrize(
    "labels, valid_labels, expected_result ",
    [
        (["ENTERPRISE", "test1"], GraphDBConfig.uns_node_types, "ENTERPRISE"),
        (["FACILITY", "test1"], GraphDBConfig.uns_node_types, "FACILITY"),
        (["AREA", "test1"], GraphDBConfig.uns_node_types, "AREA"),
        (["LINE", "test1"], GraphDBConfig.uns_node_types, "LINE"),
        (["DEVICE", "test1"], GraphDBConfig.uns_node_types, "DEVICE"),
        (["NOT_LISTED_1", "NOT_LISTED_2"], GraphDBConfig.uns_node_types, None),
        (["ENTERPRISE"], GraphDBConfig.uns_node_types, "ENTERPRISE"),
        (["FACILITY"], GraphDBConfig.uns_node_types, "FACILITY"),
        (["AREA"], GraphDBConfig.uns_node_types, "AREA"),
        (["LINE"], GraphDBConfig.uns_node_types, "LINE"),
        (["DEVICE"], GraphDBConfig.uns_node_types, "DEVICE"),
        (["NOT_LISTED"], GraphDBConfig.uns_node_types, None),
        (["spBv1_0"], (*GraphDBConfig.spb_node_types, "STATE"), "spBv1_0"),
        (["GROUP"], (*GraphDBConfig.spb_node_types, "STATE"), "GROUP"),
        (["MESSAGE_TYPE"], (*GraphDBConfig.spb_node_types, "STATE"), "MESSAGE_TYPE"),
        (["EDGE_NODE"], (*GraphDBConfig.spb_node_types, "STATE"), "EDGE_NODE"),
        (["DEVICE"], (*GraphDBConfig.spb_node_types, "STATE"), "DEVICE"),
    ],
)
def test_get_node_type(labels: list[str], valid_labels: tuple[str], expected_result: str):
    """
    Test GraphQuery.get_node_type()
    """
    result = GraphQuery.get_node_type(labels=labels, valid_labels=valid_labels)
    assert result == expected_result


@pytest.mark.parametrize(
    "parent, nested_children, relationships, expected_result, is_error",
    [
        (main_node, [uns_child_1, uns_child_2, uns_child_3], [uns_rel_1, uns_rel_2, uns_rel_3], uns_dict_result, False),
        (sbp_node, [spb_child_1, spb_child_2, spb_child_3], [spb_rel_1, spb_rel_2, spb_rel_3], spb_result_dict, False),
        (None, [spb_child_1, spb_child_2, spb_child_3], [spb_rel_1, spb_rel_2, spb_rel_3], None, True),
        (main_node, None, None, {"TestMetric2": "Test_UNS_with_NestedLists", "timestamp": 1486144510000}, False),
    ],
)
def test_get_nested_properties(
    parent: Node, nested_children: list[Node], relationships: list[Relationship], expected_result: dict, is_error: bool
):
    """
    Test GraphQuery.get_nested_properties()
    """
    try:
        result = GraphQuery.get_nested_properties(parent=parent, nested_children=nested_children, relationships=relationships)
        assert result == expected_result
    except Exception as ex:
        assert is_error, f"Should not throw any exceptions. Got {ex}"


@pytest_asyncio.fixture(scope="module")
async def setup_graphdb_data():
    """Fixture to set up data in the GraphDB from the test_data.cypher file."""
    # Read the Cypher script as read only
    with open(file=Path(__file__).resolve().parent / "test_data.cypher") as file:
        cypher_script = file.read()
    # Filter out lines that are not valid Cypher queries
    valid_queries = cypher_script.replace(":begin\n", "").replace(":commit\n", "").split(";")
    # Initialize the GraphDB
    graph_db = GraphDB()

    # Execute each query separately
    for query in valid_queries:
        if query.strip():  # Make sure the query is not empty
            await graph_db.execute_query(query=query)

    # Yield control to the test
    yield

    # Teardown code i.e. clearing the database)
    await graph_db.execute_query("MATCH (n) DETACH DELETE n;")
    # Release the driver
    await graph_db.release_graphdb_driver()


@pytest.mark.asyncio
@pytest.mark.integrationtest
@pytest.mark.parametrize(
    "topics, expected_result",
    [
        (
            ["+", "test/uns/ar2/ln4"],
            [
                UNSNode(
                    namespace="test",
                    node_name="test",
                    node_type="ENTERPRISE",
                    payload={},
                    created=datetime.fromtimestamp(1486144500, UTC),
                    last_updated=datetime.fromtimestamp(1486144500, UTC),
                ),
                UNSNode(
                    namespace="test/uns/ar2/ln4",
                    node_name="ln4",
                    node_type="LINE",
                    payload={
                        "TestMetric2": "TestUNSwithNestedLists",
                        "timestamp": 1486144500000,
                        "dict_list": [{"a": "b"}, {"x": "y"}],
                    },
                    created=datetime.fromtimestamp(1486144500, UTC),
                    last_updated=datetime.fromtimestamp(1486144500, UTC),
                ),
            ],
        ),
        (
            ["test/uns/ar2/#"],
            [
                UNSNode(
                    namespace="test/uns/ar2/ln4",
                    node_name="ln4",
                    node_type="LINE",
                    payload={
                        "TestMetric2": "TestUNSwithNestedLists",
                        "timestamp": 1486144500000,
                        "dict_list": [{"a": "b"}, {"x": "y"}],
                    },
                    created=datetime.fromtimestamp(1486144500, UTC),
                    last_updated=datetime.fromtimestamp(1486144500, UTC),
                ),
                UNSNode(
                    namespace="test/uns/ar2/ln3",
                    node_name="ln3",
                    node_type="LINE",
                    payload={
                        "TestMetric2": "TestUNSwithLists",
                        "list": [1, 2, 3, 4, 5],
                        "timestamp": 1486144502144,
                        "dict_list": [{"a": "b"}, {"x": "y"}],
                    },
                    created=datetime.fromtimestamp(1486144502.144, UTC),
                    last_updated=datetime.fromtimestamp(1486144502.144, UTC),
                ),
            ],
        ),
        (
            ["test"],
            [
                UNSNode(
                    namespace="test",
                    node_name="test",
                    node_type="ENTERPRISE",
                    payload={},
                    created=datetime.fromtimestamp(1486144500, UTC),
                    last_updated=datetime.fromtimestamp(1486144500, UTC),
                )
            ],
        ),
    ],
)
async def test_get_uns_nodes_integration(setup_graphdb_data, topics: list[str], expected_result: list[UNSNode]):  # noqa: ARG001
    mqtt_topic_list = [MQTTTopicInput.from_pydantic(MQTTTopic(topic=topic)) for topic in topics]
    graph_query = GraphQuery()
    try:
        result = await graph_query.get_uns_nodes(mqtt_topics=mqtt_topic_list)
    except Exception as ex:
        pytest.fail(f"Should not throw any exceptions. Got {ex}")
    assert result == expected_result  # Ensure the result matches the expected result


@pytest.mark.asyncio
@pytest.mark.integrationtest
@pytest.mark.parametrize(
    "property_keys, topics, exclude_topics,expected_result",
    [
        (
            ["dict_list"],
            None,
            None,
            [
                UNSNode(
                    namespace="test/uns/ar2/ln4",
                    node_name="ln4",
                    node_type="LINE",
                    payload={
                        "TestMetric2": "TestUNSwithNestedLists",
                        "timestamp": 1486144500000,
                        "dict_list": [{"a": "b"}, {"x": "y"}],
                    },
                    created=datetime.fromtimestamp(1486144500, UTC),
                    last_updated=datetime.fromtimestamp(1486144500, UTC),
                ),
            ],
        ),
        (
            ["node_name"],
            ["test/uns/ar1"],
            False,
            [
                UNSNode(
                    namespace="test/uns/ar1",
                    node_name="ar1",
                    node_type="AREA",
                    payload={},
                    created=datetime.fromtimestamp(1486144502.122, UTC),
                    last_updated=datetime.fromtimestamp(1486144502.122, UTC),
                )
            ],
        ),
        (
            ["TestMetric2"],
            ["test/uns/ar1/#"],
            False,
            [
                UNSNode(
                    namespace="test/uns/ar1/ln2",
                    node_name="ln2",
                    node_type="LINE",
                    payload={"TestMetric2": "TestUNS", "timestamp": 1486144502122},
                    created=datetime.fromtimestamp(1486144502.122, UTC),
                    last_updated=datetime.fromtimestamp(1486144502.122, UTC),
                )
            ],
        ),
        (
            ["TestMetric2"],
            ["test/uns/ar1/#"],
            True,
            [
                UNSNode(
                    namespace="test/uns/ar2/ln4",
                    node_name="ln4",
                    node_type="LINE",
                    payload={
                        "TestMetric2": "TestUNSwithNestedLists",
                        "timestamp": 1486144500000,
                        "dict_list": [{"a": "b"}, {"x": "y"}],
                    },
                    created=datetime.fromtimestamp(1486144500, UTC),
                    last_updated=datetime.fromtimestamp(1486144500, UTC),
                ),
                UNSNode(
                    namespace="test/uns/ar2/ln3",
                    node_name="ln3",
                    node_type="LINE",
                    payload={
                        "TestMetric2": "TestUNSwithLists",
                        "list": [1, 2, 3, 4, 5],
                        "timestamp": 1486144502144,
                        "dict_list": [{"a": "b"}, {"x": "y"}],
                    },
                    created=datetime.fromtimestamp(1486144502.144, UTC),
                    last_updated=datetime.fromtimestamp(1486144502.144, UTC),
                ),
            ],
        ),
    ],
)
async def test_get_uns_nodes_by_property_integration(
    setup_graphdb_data,  # noqa: ARG001
    property_keys,
    topics: list[str],
    exclude_topics: bool,
    expected_result: dict,
):
    mqtt_topic_list = None
    if topics is not None:
        mqtt_topic_list = [MQTTTopicInput.from_pydantic(MQTTTopic(topic=topic)) for topic in topics]

    graph_query = GraphQuery()
    try:
        result = await graph_query.get_uns_nodes_by_property(
            property_keys=property_keys, topics=mqtt_topic_list, exclude_topics=exclude_topics
        )
    except Exception as ex:
        pytest.fail(f"Should not throw any exceptions. Got {ex}")
    assert result == expected_result  # Ensure the result matches the expected result


@pytest.mark.asyncio
@pytest.mark.integrationtest
@pytest.mark.parametrize(
    "metric_names, expected_result",
    [
        (["Inputs/A"], [SPBNode(topic="", payload={})]),
        ("Inputs/A", [SPBNode(topic="", payload={})]),
        (["Inputs/A", "Inputs/B"], [SPBNode(topic="", payload={})]),
        (["Output/F"], [SPBNode(topic="", payload={})]),
        ([], []),
        (None, []),
    ],
)
async def test_get_spb_nodes_integration(
    setup_graphdb_data,  # noqa: ARG001
    metric_names: list[str],
    expected_result: list[SPBNode],
):
    graph_query = GraphQuery()
    try:
        result = await graph_query.get_spb_nodes_by_metric(metric_names=metric_names)
    except Exception as ex:
        pytest.fail(f"Should not throw any exceptions. Got {ex}")
    assert result == expected_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "topics,has_result_errors",
    [
        (["topic1/#"], False),
        (["topic1/+"], False),
        (["topic1/testString"], False),
        (["#"], False),
        (["topic1/#", "topic3"], False),
        (["topic1/subtopic1", "topic2/topic3"], False),
        (["+"], False),
    ],
)
async def test_strawberry_get_uns_nodes(topics: list[str], has_result_errors: bool):
    query: str = """query TestQuery($mqtt_topics:[MQTTTopicInput!]!){
                getUnsNodes(topics: $mqtt_topics){
                    nodeName
                    nodeType
                    namespace
                    payload {
                        data
                    }
                    created
                    lastUpdated
                }
            }
    """
    mqtt_topics: list[dict[str, str]] = [{"topic": x} for x in topics]
    schema = strawberry.Schema(query=GraphQuery)
    with patch("uns_graphql.queries.graph.GraphDB", return_value=mocked_uns_graphdb):
        result = await schema.execute(query=query, variable_values={"mqtt_topics": mqtt_topics})
        if not has_result_errors:
            assert not result.errors
        else:
            assert result.errors


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "property_keys, topics, exclude_topics, has_result_errors",
    [
        (["prop1"], ["topic1/#"], False, False),
        ("prop1", ["topic1/#"], False, False),
        (["prop1", "prop2"], ["topic1/+"], True, False),
        (["124"], None, None, False),
        (["prop1", "prop2"], ["topic1/subtopic"], True, False),
        (["prop1", "prop2"], ["topic1/#", "topic3"], True, False),
        (["prop1", "prop2"], ["+"], True, False),
    ],
)
async def test_strawberry_get_uns_nodes_by_property(
    property_keys,
    topics: list[str],
    exclude_topics: bool,
    has_result_errors: bool,
):
    query: str = """query TestQuery($property_keys:[String!]!, $mqtt_topics:[MQTTTopicInput!], $exclude_topics:Boolean){
                getUnsNodesByProperty(propertyKeys: $property_keys,
                    topics: $mqtt_topics,
                    excludeTopics: $exclude_topics

                    ){
                        nodeName
                        nodeType
                        namespace
                        payload {
                            data
                        }
                        created
                        lastUpdated
                }
            }
    """
    mqtt_topics = None
    if topics is not None:
        mqtt_topics: list[dict[str, str]] = [{"topic": x} for x in topics]
    schema = strawberry.Schema(query=GraphQuery)
    with patch("uns_graphql.queries.graph.GraphDB", return_value=mocked_uns_graphdb):
        result = await schema.execute(
            query=query,
            variable_values={"property_keys": property_keys, "mqtt_topics": mqtt_topics, "exclude_topics": exclude_topics},
        )
        if not has_result_errors:
            assert not result.errors
        else:
            assert result.errors


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "metric_names,has_result_errors",
    [
        (["Inputs/A"], False),
        ("Inputs/A", False),
        (["Inputs/A", "Inputs/B"], False),
        (["Output/F"], False),
        ([], False),
        (None, True),
    ],
)
async def test_strawberry_get_spb_nodes_by_metric(metric_names: list[str], has_result_errors: bool):
    query: str = """query TestQuery($metric_names:[String!]!){
        getSpbNodesByMetric(metricNames:$metric_names ){
            topic
            nodeTimestamp: timestamp
            seq
            uuid
            body
            metrics {
                name
                alias
                datatype
                isNull
                metricTimestamp: timestamp
                value {
                    ... on SPBPrimitive { data: data }
                    ... on BytesPayload { bytes_data: data}
                    ... on SPBDataSet {
                                numOfColumns
                                columns
                                types
                                rows {
                                    elements {
                                        value { data}
                                    }
                                }
                        }
                }
            }
        }

    }
    """
    schema = strawberry.Schema(query=GraphQuery)
    with patch("uns_graphql.queries.graph.GraphDB", return_value=mocked_spb_graphdb):
        result = await schema.execute(
            query=query,
            variable_values={
                "metric_names": metric_names,
            },
        )
        if not has_result_errors:
            assert not result.errors
        else:
            assert result.errors
