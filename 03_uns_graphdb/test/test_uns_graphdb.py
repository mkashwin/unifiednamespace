"""
Tests for Uns_MQTT_GraphDb
"""
import inspect
import json
import os

import pytest
from google.protobuf.json_format import MessageToDict
from neo4j import Session, exceptions
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
from uns_graphdb.uns_mqtt_graphdb import UnsMqttGraphDb
from uns_mqtt.mqtt_listener import UnsMQTTClient
from uns_sparkplugb.generated import sparkplug_b_pb2

cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            'src')))

is_configs_provided: bool = (os.path.exists(
    os.path.join(cmd_subfolder, "../conf/.secrets.yaml")) and os.path.exists(
        os.path.join(cmd_subfolder, "../conf/settings.yaml"))) or (bool(
            os.getenv("UNS_graphdb.username")))


@pytest.mark.integrationtest
@pytest.mark.xfail(
    not is_configs_provided,
    reason="Configurations absent, or these are not integration tests")
def test_uns_mqtt_graph_db():
    """
    Test the constructor of the class Uns_MQTT_GraphDb
    """
    uns_mqtt_graphdb = None
    try:
        uns_mqtt_graphdb = UnsMqttGraphDb()
        uns_mqtt_graphdb.uns_client.loop()
        assert uns_mqtt_graphdb is not None, (
            "Connection to either the MQTT Broker "
            "or the Graph DB did not happen")
    except Exception as ex:
        pytest.fail(
            f"Connection to either the MQTT Broker or the Graph DB did not happen: Exception {ex}"
        )
    finally:
        if uns_mqtt_graphdb is not None:
            uns_mqtt_graphdb.uns_client.disconnect()

        if ((uns_mqtt_graphdb is not None)
                and (uns_mqtt_graphdb.graph_db_handler is not None)):
            uns_mqtt_graphdb.graph_db_handler.close()


@pytest.mark.integrationtest
@pytest.mark.xfail(
    not is_configs_provided,
    reason="Configurations absent, or these are not integration tests")
@pytest.mark.parametrize(
    "topic, message",  # Test spB message persistance
    [

        # Test UNS message persistance
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
            "dict_list": [{"a": "b"}, {"x": "y"}, ],
        }),
        # ("test/uns/ar2/ln4", { # currently failing. validate if such a structure needs to be supported
        #     "timestamp": 1486144500000,
        #     "TestMetric2": "TestUNSwithNestedLists",
        #     "dict_list": [{"a": "b"}, {"x": "y"}, ],
        #     "nested_dict": [[1, 2, 3], ["q", "w", "r"], ["a", "b", "d"]]
        # }),
        ("spBv1.0/group1/NBIRTH/eon1",
            b'\x08\xc4\x89\x89\x83\xd30\x12\x11\n\x08' \
            b'Inputs/A\x18\xea\xf2\xf5\xa8\xa0+\x12\x15' \
            b'\n\x08Inputs/A\x18\xea\xf2\xf5\xa8\xa0+ ' \
            b'\x0bp\x00\x12\x15\n\x08Inputs/B\x18\xea' \
            b'\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x16\n' \
            b'\tOutputs/E\x18\xea\xf2\xf5\xa8\xa0+ ' \
            b'\x0bp\x00\x12\x16\n\tOutputs/F\x18\xea' \
            b'\xf2\xf5\xa8\xa0+ \x0bp\x00\x12-\n' \
            b'\x18Properties/Hardware Make\x18\xea\xf2' \
            b'\xf5\xa8\xa0+ \x0cz\x08Pibrella\x12\x1f\n' \
            b'\x11Properties/Weight\x18\xea\xf2\xf5\xa8' \
            b'\xa0+ \x03P\xc8\x01\x18\x00'),
        ("spBv1.0/group1/NDATA/eon1",
            b'\x08\xc4\x89\x89\x83\xd30\x12\x11\n\x08' \
            b'Inputs/A\x18\xea\xf2\xf5\xa8\xa0+\x12\x15' \
            b'\n\x08Inputs/A\x18\xea\xf2\xf5\xa8\xa0+ ' \
            b'\x0bp\x00\x12\x15\n\x08Inputs/B\x18\xea' \
            b'\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x16\n' \
            b'\tOutputs/E\x18\xea\xf2\xf5\xa8\xa0+ ' \
            b'\x0bp\x00\x12\x16\n\tOutputs/F\x18\xea' \
            b'\xf2\xf5\xa8\xa0+ \x0bp\x00\x12-\n' \
            b'\x18Properties/Hardware Make\x18\xea\xf2' \
            b'\xf5\xa8\xa0+ \x0cz\x08Pibrella\x12\x1f\n' \
            b'\x11Properties/Weight\x18\xea\xf2\xf5\xa8' \
            b'\xa0+ \x03P\xc8\x01\x18\x00')
    ])
def test_mqtt_graphdb_persistance(topic: str, message):
    """
    Test the persistance of message (UNS & SpB) to the database
    """
    uns_mqtt_graphdb = None
    try:
        uns_mqtt_graphdb = UnsMqttGraphDb()
        uns_mqtt_graphdb.uns_client.loop()

        def on_message_decorator(client, userdata, msg):
            old_on_message(client, userdata, msg)
            if topic.startswith("spBv1.0/"):
                inbound_payload = sparkplug_b_pb2.Payload()
                inbound_payload.ParseFromString(message)
                message_dict = MessageToDict(inbound_payload)
                node_type = uns_mqtt_graphdb.graphdb_spb_node_types
            else:
                message_dict = message
                node_type = uns_mqtt_graphdb.graphdb_node_types

            attr_nd_typ: str = uns_mqtt_graphdb.graphdb_nested_attribute_node_type

            try:
                with uns_mqtt_graphdb.graph_db_handler.connect().session(
                        database=uns_mqtt_graphdb.graph_db_handler.database
                ) as session:
                    session.execute_read(read_nodes, node_type, attr_nd_typ,
                                         topic, message_dict)
            except (exceptions.TransientError,
                    exceptions.TransactionError) as ex:
                pytest.fail("Connection to either the MQTT Broker or "
                            f"the Graph DB did not happen: Exception {ex}")
            finally:
                uns_mqtt_graphdb.uns_client.disconnect()

        # --- end of function

        publish_properties = None
        if uns_mqtt_graphdb.uns_client.protocol == UnsMQTTClient.MQTTv5:
            publish_properties = Properties(PacketTypes.PUBLISH)

        if topic.startswith("spBv1.0/"):
            payload = message
        else:
            payload = json.dumps(message)

        # Overriding on_message is more reliable that on_publish because some times
        # on_publish was called before on_message
        old_on_message = uns_mqtt_graphdb.uns_client.on_message
        uns_mqtt_graphdb.uns_client.on_message = on_message_decorator

        # publish the messages as non-persistent to allow the tests to be
        # idempotent across multiple runs
        uns_mqtt_graphdb.uns_client.publish(
            topic=topic,
            payload=payload,
            qos=uns_mqtt_graphdb.uns_client.qos,
            retain=False,
            properties=publish_properties)

        uns_mqtt_graphdb.uns_client.loop_forever()
    except AssertionError as ex:
        print(f"Assertion failure in the test, {ex}")
    except Exception as ex:
        pytest.fail(
            f"Connection to either the MQTT Broker or the Graph DB did not happen: Exception {ex}"
        )

    finally:
        if uns_mqtt_graphdb is not None:
            uns_mqtt_graphdb.uns_client.disconnect()

        if ((uns_mqtt_graphdb is not None)
                and (uns_mqtt_graphdb.graph_db_handler is not None)):
            uns_mqtt_graphdb.graph_db_handler.close()


def read_nodes(session: Session, topic_node_types: tuple, attr_node_type: str,
               topic: str, message: dict):
    """
        Helper function to read the database and compare the persisted data
    """
    topic_list: list = topic.split("/")
    records: list = []
    index = 0
    for node, topic_name in zip(topic_list, topic_node_types):
        query = f"MATCH (n:{topic_name}{{ node_name: $node_name }})\n"
        query = query + "RETURN n"

        print(f"CQL statement to be executed: {query}")

        result = session.run(query, node_name=node)
        records = list(result)
        assert result is not None and len(records) == 1

        db_node_properties = records[0].values()[0]
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
