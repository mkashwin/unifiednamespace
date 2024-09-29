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

Tests for GraphDBHandler
"""

import sys
from typing import Optional

import pytest
from neo4j import Session, exceptions
from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_graphdb.graphdb_config import GraphDBConfig
from uns_graphdb.graphdb_handler import NODE_NAME_KEY, NODE_RELATION_NAME, REL_ATTR_KEY, GraphDBHandler


@pytest.mark.parametrize(
    "current_depth, expected_result",
    [
        (0, "ENTERPRISE"),
        (1, "FACILITY"),
        (2, "AREA"),
        (3, "LINE"),
        (4, "DEVICE"),
        (5, "DEVICE_depth_1"),
        (6, "DEVICE_depth_2"),
        (9, "DEVICE_depth_5"),
    ],
)
def test_get_node_name(current_depth: int, expected_result):
    """
    Test case for GraphDBHandler#get_node_name
    """
    node_types: tuple = ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE")
    result = GraphDBHandler.get_topic_node_type(current_depth, node_types)
    assert result == expected_result, f"""
            Get Node name for Depth:{current_depth},
            From Node Types : {node_types}
            Expected Result:{expected_result},
            Actual Result: {result}"""


@pytest.mark.parametrize(
    "message, plain, composite",
    [
        (
            {
                "a": "value1",
                "b": "value2",
            },
            {
                "a": "value1",
                "b": "value2",
            },
            {},
        ),  # test only plain
        (
            {
                "node_name": "value1",
                "b": "value2",
            },
            {
                "NODE_NAME": "value1",
                "b": "value2",
            },
            {},
        ),  # test for restricted property node_name
        (
            {
                "a": "value1",
                "b": [10, 23],
                "c": {
                    "k1": "v1",
                    "k2": 100,
                },
            },
            {
                "a": "value1",
                "b": [10, 23],
            },
            {
                "c": {
                    "k1": "v1",
                    "k2": 100,
                },
            },
        ),  # test composite dict
        (
            {
                "a": "value1",
                "b": [10, 23],
                "c": [
                    {
                        "name": "v1",
                        "k2": 100,
                    },
                    {
                        "name": "v2",
                        "k2": 200,
                    },
                ],
                "d": {
                    "k1": "v1",
                    "k2": 100,
                },
            },
            {
                "a": "value1",
                "b": [10, 23],
            },
            {
                "c": [
                    {
                        "name": "v1",
                        "k2": 100,
                    },
                    {
                        "name": "v2",
                        "k2": 200,
                    },
                ],
                "d": {
                    "k1": "v1",
                    "k2": 100,
                },
            },
        ),  # test composite with name
        ({}, {}, {}),  # test empty
        (None, {}, {}),  # test None
    ],
)
def test_separate_plain_composite_attributes(message: dict, plain: dict, composite: dict):
    """
    Testcase for GraphDBHandler.separate_plain_composite_attributes.
    Validate that the nested dict object is properly split
    """
    result_plain, result_composite = GraphDBHandler.separate_plain_composite_attributes(message)
    assert result_plain == plain
    assert result_composite == composite


@pytest.mark.integrationtest()
@pytest.mark.parametrize(
    "topic, message",  # Test spB message persistence
    [
        (
            "test/uns/ar1/ln2",
            {
                "timestamp": 1486144502122,
                "TestMetric2": "TestUNS",
            },
        ),
        (
            "test/uns/ar2/ln3",
            {
                "timestamp": 1486144502144,
                "TestMetric2": "TestUNSwithLists",
                "list": [1, 2, 3, 4, 5],
            },
        ),
        (
            "test/uns/ar2/ln4",
            {
                "timestamp": 1486144500000,
                "TestMetric2": "TestUNSwithNestedDict",
                "my_dict": {
                    "a": "b",
                },
                "my_other_dict": {
                    "x": "y",
                },
            },
        ),
        (
            "test/uns/ar2/ln5",
            {
                "timestamp": 1486144500000,
                "TestMetric2": "TestUNSwithNestedLists",
                "dict_list": [
                    {
                        "a": "b",
                    },
                    {
                        "x": "y",
                    },
                ],
            },
        ),
    ],
)
def test_persist_mqtt_msg(topic: str, message: dict):
    """
    Testcase for GraphDBHandler.persist_mqtt_msg.
    Validate that the nested dict object is properly split
    """
    graphdb_url: str = GraphDBConfig.db_url
    graphdb_user: str = GraphDBConfig.user

    graphdb_password: str = GraphDBConfig.password
    graphdb_database: Optional[str] = GraphDBConfig.database
    if topic.startswith(UnsMQTTClient.SPARKPLUG_NS):
        node_types: tuple = GraphDBConfig.spb_node_types
    else:
        node_types: tuple = GraphDBConfig.uns_node_types

    attr_nd_typ: str = GraphDBConfig.nested_attributes_node_type
    try:
        graph_db_handler = GraphDBHandler(
            uri=graphdb_url, user=graphdb_user, password=graphdb_password, database=graphdb_database
        )
        # persist data
        graph_db_handler.persist_mqtt_msg(topic=topic, message=message, node_types=node_types, attr_node_type=attr_nd_typ)
        # validate data which was persisted
        with graph_db_handler.connect().session(database=graph_db_handler.database) as session:
            session.execute_read(read_topic_nodes, node_types, attr_nd_typ, topic, message)

    except (exceptions.TransientError, exceptions.TransactionError) as ex:
        pytest.fail("Connection to either the MQTT Broker or " f"the Graph DB did not happen: Exception {ex}")
    finally:
        # After successfully validating the data run a new transaction to delete
        with graph_db_handler.connect().session(database=graph_db_handler.database) as session:
            session.execute_write(cleanup_test_data, topic.split("/")[0], node_types[0])

        if graph_db_handler is not None:
            graph_db_handler.close()


def read_topic_nodes(session: Session, topic_node_types: tuple, attr_node_type: str, topic: str, message: dict):
    """
    Helper function to read the database and compare the persisted data
    """
    topic_list: list = topic.split("/")
    records: list = []
    index = 0
    last_node_id = None
    for node, node_label in zip(topic_list, topic_node_types):
        if index == 0:
            query = f"MATCH (node:{node_label}{{ node_name: $node_name }})\n"
            query = query + " RETURN node"
        else:
            query = f"MATCH(parent) -[rel:{NODE_RELATION_NAME}]->"
            query = query + f" (node:{node_label}{{ node_name: $node_name }})"
            query = query + "WHERE elementId(parent) = $parent_id "
            query = query + " RETURN node, rel"

        result = session.run(query, node_name=node, parent_id=last_node_id)
        records = list(result)
        assert result is not None and len(records) == 1
        if index > 0:
            assert records[0].values()[1].type == NODE_RELATION_NAME

        db_node = records[0].values()[0]
        last_node_id = records[0][0].element_id
        # check node_name
        assert db_node.get("node_name") == node
        # labels is a frozen set
        assert node_label in db_node.labels

        if index == len(topic_list) - 1:
            # this is a leaf node and the message attributes must match
            parent_id = db_node.element_id
            primitive_props, compound_props = GraphDBHandler.separate_plain_composite_attributes(message)

            read_primitive_attr_nodes(db_node, primitive_props)

            for attr_key, value in compound_props.items():
                if isinstance(value, dict):
                    read_dict_attr_node(session, attr_node_type, parent_id, attr_key, value)

                elif isinstance(value, (list, tuple)):
                    read_list_attr_nodes(session, attr_node_type, parent_id, attr_key, value)

                else:
                    pytest.fail("compound properties should only be list of dict or dict ")
        index = index + 1


def read_primitive_attr_nodes(db_node, primitive_props: dict):
    """
    Validate teh that  graphDb node contains al the properties and the values match
    """
    for attr_key, value in primitive_props.items():
        if isinstance(value, int) and not (-sys.maxsize - 1) < value < sys.maxsize:
            assert isinstance(db_node.get(attr_key), str)
            assert int(db_node.get(attr_key)) == value

        elif isinstance(value, list):
            for db, expected in zip(db_node.get(attr_key), value):
                if isinstance(expected, int):
                    assert expected == int(db)
                else:
                    assert expected == db
        else:
            assert db_node.get(attr_key) == value


def read_list_attr_nodes(session: Session, attr_node_type: str, parent_id: str, attr_key: str, node_array: list[dict]):
    """
    Reads a list of attribute nodes to check values
    """
    list_query: str = f"""
    MATCH (parent) -[rel:{NODE_RELATION_NAME}]-> (child: {attr_node_type})
    where rel.type = 'list'
    AND rel.attribute_name=$attribute_name
    AND elementId(parent) = $parent_id
    return child, rel
    """
    list_query_result = session.run(query=list_query, parent_id=parent_id, attribute_name=attr_key)
    db_list_records = list(list_query_result)

    assert len(db_list_records) == len(node_array)

    # iterate through node_array, split into primitive and compound
    # iterate through db_list_records[i].values()[0] for matching node_name. then match primitive values
    matched_nodes = 0
    for record in db_list_records:
        db_node = record.values()[0]
        relation = record.values()[1]
        index = 0
        db_node_id = db_node.element_id

        assert relation.get(REL_ATTR_KEY) == attr_key

        # Need to do this as the order of array may not have been retained while saving.
        for node in node_array:
            node_name = node.get("name", attr_key + "_" + str(index))
            primitive_props, compound_props = GraphDBHandler.separate_plain_composite_attributes(node)
            if db_node.get(NODE_NAME_KEY) == node_name:
                matched_nodes = matched_nodes + 1
                read_primitive_attr_nodes(db_node, primitive_props)

                for child_key, child_value in compound_props.items():
                    if isinstance(child_value, dict):
                        read_dict_attr_node(session, attr_node_type, db_node_id, child_key, child_value)

                    elif isinstance(child_value, (list, tuple)):
                        read_list_attr_nodes(session, attr_node_type, db_node_id, child_key, child_value)

                    else:
                        pytest.fail("compound properties should only be list of dict or dict ")
                break  # since the node was matched, we can break out of the inner loop
            index = index + 1
    assert matched_nodes == len(node_array)


def read_dict_attr_node(session, attr_node_type: str, parent_id: str, attr_key: str, node: dict):
    """;
    Read and compare node created for nested dict attributes in the message
    """
    # Need to enhance test to handle nested dicts
    db_node_query: str = f"""
        MATCH (parent) -[r:{NODE_RELATION_NAME}]-> (n:{attr_node_type}{{ node_name: $node_name }})
        WHERE  elementId(parent)= $parent_id
        AND r.type='dict'
        AND r.attribute_name= $attribute_name
        RETURN n, r
        """
    db_result = session.run(db_node_query, node_name=attr_key, parent_id=parent_id, attribute_name=attr_key)
    db_nodes = list(db_result)

    assert db_nodes is not None and len(db_nodes) == 1
    assert db_nodes[0][1].get(REL_ATTR_KEY) == attr_key

    node_id = db_nodes[0][0].element_id

    primitive_props, compound_props = GraphDBHandler.separate_plain_composite_attributes(node)
    read_primitive_attr_nodes(db_nodes[0][0], primitive_props)
    for child_key, child_value in compound_props.items():
        if isinstance(child_value, dict):
            read_dict_attr_node(session, attr_node_type, node_id, child_key, child_value)

        elif isinstance(child_value, (list, tuple)):
            read_list_attr_nodes(session, attr_node_type, node_id, child_key, child_value)

        else:
            pytest.fail("compound properties should only be list of dict or dict ")


def cleanup_test_data(session: Session, node: str, node_type: str):
    """
    Cleans up the test data which was inserted in the test case
    recursively deleted provided node and all nodes in its child tree
    """
    delete_query = f"""
        MATCH (parent:{node_type}{{ node_name: $node_name }})-[*]->(child)
        DETACH DELETE parent, child;
        """
    session.run(query=delete_query, node_name=node)
