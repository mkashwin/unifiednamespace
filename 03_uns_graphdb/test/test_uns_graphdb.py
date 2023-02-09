"""
Tests for Uns_MQTT_GraphDb
"""
import inspect
import json
import os
from test.test_graphdb_handler import read_nodes

import pytest
from google.protobuf.json_format import MessageToDict
from neo4j import exceptions
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
            "dict_list": [{
                "a": "b"
            }, {
                "x": "y"
            }, {}],
        }),
        # ("test/uns/ar2/ln4", { # currently failing. validate if such a structure needs to be supported
        #     "timestamp": 1486144500000,
        #     "TestMetric2": "TestUNSwithNestedLists",
        #     "dict_list": [{"a": "b"}, {"x": "y"}, ],
        #     "nested_dict": [[1, 2, 3], ["q", "w", "r"], ["a", "b", "d"]]
        # }),
        ("spBv1.0/uns_group/NBIRTH/eon1",
         b'\x08\xc4\x89\x89\x83\xd30\x12\x17\n\x08Inputs/A\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ '
         b'\x0bp\x00\x12\x17\n\x08Inputs/B\x10\x01\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\t'
         b'Outputs/E\x10\x02\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\tOutputs/F\x10\x03\x18\xea\xf2\xf5\xa8\xa0+ '
         b'\x0bp\x00\x12+\n\x18Properties/Hardware Make\x10\x04\x18\xea\xf2\xf5\xa8\xa0+ \x0cz\x04Sony\x12!\n\x11'
         b'Properties/Weight\x10\x05\x18\xea\xf2\xf5\xa8\xa0+ \x03P\xc8\x01\x18\x00'
         ),
        ("spBv1.0/uns_group/NDATA/eon1",
         b'\x08\xc4\x89\x89\x83\xd30\x12\x17\n\x08Inputs/A\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ '
         b'\x0bp\x00\x12\x17\n\x08Inputs/B\x10\x01\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\t'
         b'Outputs/E\x10\x02\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\tOutputs/F\x10\x03\x18\xea\xf2\xf5\xa8\xa0+ '
         b'\x0bp\x00\x12+\n\x18Properties/Hardware Make\x10\x04\x18\xea\xf2\xf5\xa8\xa0+ \x0cz\x04Sony\x12!\n\x11'
         b'Properties/Weight\x10\x05\x18\xea\xf2\xf5\xa8\xa0+ \x03P\xc8\x01\x18\x00'
         )
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
