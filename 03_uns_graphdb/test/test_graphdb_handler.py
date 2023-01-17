"""
Tests for GraphDBHandler
"""
import inspect
import os

import pytest
from uns_mqtt.mqtt_listener import UnsMQTTClient
from neo4j import Session, exceptions
from uns_graphdb.graphdb_config import settings
from uns_graphdb.graphdb_handler import GraphDBHandler
from uns_graphdb.graphdb_handler import NODE_RELATION_NAME

cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            'src')))

is_configs_provided: bool = (os.path.exists(
    os.path.join(cmd_subfolder, "../conf/.secrets.yaml")) and os.path.exists(
        os.path.join(cmd_subfolder, "../conf/settings.yaml"))) or (bool(
            os.getenv("UNS_graphdb.username")))


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
    result = GraphDBHandler.get_topic_node_type(current_depth, node_types)
    assert result == expected_result, f"""
            Get Node name for Depth:{current_depth},
            From Node Types : {node_types}
            Expected Result:{expected_result},
            Actual Result: {result}"""


@pytest.mark.parametrize(
    "message, plain, composite",
    [
        ({
            "a": "value1",
            "b": "value2"
        }, {
            "a": "value1",
            "b": "value2"
        }, {}),  # test only plain
        ({
            "node_name": "value1",
            "b": "value2"
        }, {
            "node_name": "value1",
            "b": "value2"
        }, {}),  # test only plain with node name
        ({
            "a": "value1",
            "b": [10, 23],
            "c": {
                "k1": "v1",
                "k2": 100
            }
        }, {
            "a": "value1",
            "b": [10, 23]
        }, {
            "c": {
                "k1": "v1",
                "k2": 100
            }
        }),  # test composite
        ({
            "a": "value1",
            "b": [10, 23],
            "c": [{
                "name": "v1",
                "k2": 100
            }, {
                "name": "v2",
                "k2": 200
            }]
        }, {
            "a": "value1",
            "b": [10, 23]
        }, {
            "v1": {
                "name": "v1",
                "k2": 100
            },
            "v2": {
                "name": "v2",
                "k2": 200
            }
        }),  # test composite with name
        ({}, {}, {}),  # test empty
        (None, {}, {}),  # test None
    ])
def test_separate_plain_composite_attributes(message: dict, plain: dict,
                                             composite: dict):
    """
    Testcase for GraphDBHandler.separate_plain_composite_attributes.
    Validate that the nested dict object is properly split
    """
    result_plain, result_composite = GraphDBHandler.separate_plain_composite_attributes(
        message)
    assert result_plain == plain
    assert result_composite == composite


@pytest.mark.integrationtest
@pytest.mark.xfail(
    not is_configs_provided,
    reason="Configurations absent, or these are not integration tests")
@pytest.mark.parametrize(
    "topic, message",  # Test spB message persistance
    [
        ("test/uns/ar1/ln2", {
            "timestamp": 1486144502122,
            "TestMetric2": "TestUNS",
        }),
        ("test/uns/ar2/ln3", {
            "timestamp": 1486144502144,
            "TestMetric2": "TestUNSwithLists",
            "list": [1, 2, 3, 4, 5]
        }),
        ("test/uns/ar2/ln4", {
            "timestamp": 1486144500000,
            "TestMetric2": "TestUNSwithNestedLists",
            "dict_list": [
                {
                    "a": "b"
                },
                {
                    "x": "y"
                },
            ]
        }),
    ])
def test_persist_mqtt_msg(topic: str, message: dict):
    """
    Testcase for GraphDBHandler.persist_mqtt_msg.
    Validate that the nested dict object is properly split
    """
    graphdb_url: str = settings.graphdb["url"]
    graphdb_user: str = settings.graphdb["username"]

    graphdb_password: str = settings.graphdb["password"]
    graphdb_database: str = settings.get("graphdb.database", None)
    if topic.startswith(UnsMQTTClient.SPARKPLUG_NS):
        node_types = settings.get(
            "graphdb.spB_node_types",
            ("spBv1_0", "GROUP", "MESSAGE_TYPE", "EDGE_NODE", "DEVICE"))
    else:
        node_types: tuple = tuple(
            settings.get("graphdb.uns_node_types",
                         ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE")))

    attr_nd_typ: str = settings.get("graphdb.nested_attribute_node_type",
                                    "NESTED_ATTRIBUTE")
    try:
        graph_db_handler = GraphDBHandler(uri=graphdb_url,
                                          user=graphdb_user,
                                          password=graphdb_password,
                                          database=graphdb_database)
        # persist data
        graph_db_handler.persist_mqtt_msg(topic=topic,
                                          message=message,
                                          node_types=node_types,
                                          attr_node_type=attr_nd_typ)
        # validate data which was persisted
        with graph_db_handler.connect().session(
                database=graph_db_handler.database) as session:
            session.execute_read(read_nodes, node_types, attr_nd_typ, topic,
                                 message)
    except (exceptions.TransientError, exceptions.TransactionError) as ex:
        pytest.fail("Connection to either the MQTT Broker or "
                    f"the Graph DB did not happen: Exception {ex}")
    finally:
        if graph_db_handler is not None:
            graph_db_handler.close()


def read_nodes(session: Session, topic_node_types: tuple, attr_node_type: str,
               topic: str, message: dict):
    """
        Helper function to read the database and compare the persisted data
    """
    topic_list: list = topic.split("/")
    records: list = []
    index = 0
    last_node_id = None
    for node, topic_name in zip(topic_list, topic_node_types):
        if index == 0:
            query = f"MATCH (node:{topic_name}{{ node_name: $node_name }})\n"
        else:
            query = f"MATCH(parent) -[r:{NODE_RELATION_NAME}]->"
            query = query + f" (node:{topic_name}{{ node_name: $node_name }})"
            query = query + "WHERE elementId(parent) = $parent_id "
        query = query + " RETURN node"

        result = session.run(query, node_name=node, parent_id=last_node_id)
        records = list(result)
        assert result is not None and len(records) == 1

        db_node_properties = records[0].values()[0]
        last_node_id = getattr(records[0][0], "_element_id")
        # check node_name
        assert db_node_properties.get("node_name") == node
        # labels is a frozen set
        assert topic_name in db_node_properties.labels

        if index == len(topic_list) - 1:
            # this is a leaf node and the message attributes must match
            parent_id = getattr(db_node_properties, "_element_id")
            for attr_key in message:
                value = message[attr_key]

                is_only_primitive: bool = True
                if isinstance(value, dict):
                    is_only_primitive = False
                    read_dict_attr_node(session, attr_node_type, parent_id,
                                        attr_key, value)
                elif isinstance(value, list) or isinstance(value, tuple):
                    is_only_primitive = read_list_attr_nodes(
                        session, db_node_properties.get(attr_key),
                        attr_node_type, parent_id, attr_key, value)
                if is_only_primitive:
                    assert db_node_properties.get(attr_key) == value
        index = index + 1


def read_list_attr_nodes(session, db_attr_list, attr_node_type, parent_id,
                         attr_key, value):
    counter: int = 0
    is_only_primitive = True
    for item in value:
        name_key = attr_key + "_" + str(counter)
        if isinstance(item, list) or isinstance(item, tuple):
            is_only_primitive = False
            read_list_attr_nodes(session, attr_node_type, parent_id, name_key,
                                 item)
        elif isinstance(item, dict):
            is_only_primitive = False
            # special handling. if there is a sub attribute "name", use it for the node name
            if "name" in item:
                name_key = item["name"]
            read_dict_attr_node(session, attr_node_type, parent_id, name_key,
                                item)
        counter = counter + 1
    if is_only_primitive:
        assert db_attr_list == value
    return is_only_primitive


def read_dict_attr_node(session, attr_node_type: str, parent_id: str,
                        attr_key: str, value: dict):
    """
    Read and compare node created for nested dict attributes in the message
    """
    # Need to enhance test to handle nested dicts
    attr_node_query: str = f"""
                        MATCH (parent) -[r:PARENT_OF]-> (n:{attr_node_type}{{ node_name: $node_name }})
                        WHERE  elementId(parent)= $parent_id
                        RETURN n
                    """
    attr_nodes_result = session.run(attr_node_query,
                                    node_name=attr_key,
                                    parent_id=parent_id)
    attr_nodes = list(attr_nodes_result)
    assert attr_nodes is not None and len(attr_nodes) == 1
    for sub_items in value:
        assert value[sub_items] == attr_nodes[0].values(
        )[0][sub_items], "Attributes of child attribute not matching"
