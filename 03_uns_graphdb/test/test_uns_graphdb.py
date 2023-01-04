import inspect
import json
import os
import sys
import warnings

import pytest
from google.protobuf.json_format import MessageToDict
from neo4j import Session, exceptions
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            'src')))
uns_mqtt_folder = os.path.realpath(
    os.path.abspath(
        os.path.join(cmd_subfolder, '..', '..', '02_mqtt-cluster', 'src')))

if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)
    sys.path.insert(1, os.path.join(cmd_subfolder, "uns_graphdb"))
if uns_mqtt_folder not in sys.path:
    sys.path.insert(2, uns_mqtt_folder)

from uns_graphdb.uns_mqtt_graphdb import Uns_MQTT_GraphDb
from uns_mqtt.mqtt_listener import Uns_MQTT_ClientWrapper
from uns_sparkplugb.generated import sparkplug_b_pb2

is_configs_provided: bool = (os.path.exists(
    os.path.join(cmd_subfolder, "../conf/.secrets.yaml")) and os.path.exists(
        os.path.join(cmd_subfolder, "../conf/settings.yaml"))) or (bool(
            os.getenv("UNS_graphdb.username")))


@pytest.mark.integrationtest
@pytest.mark.xfail(
    not is_configs_provided,
    reason="Configurations absent, or these are not integration tests")
def test_Uns_MQTT_GraphDb():
    uns_mqtt_graphdb = None
    try:
        uns_mqtt_graphdb = Uns_MQTT_GraphDb()
        uns_mqtt_graphdb.uns_client.loop()
        assert uns_mqtt_graphdb is not None, "Connection to either the MQTT Broker or the Graph DB did not happen"
    except Exception as ex:
        pytest.fail(
            f"Connection to either the MQTT Broker or the Graph DB did not happen: Exception {ex}"
        )
    finally:
        if (uns_mqtt_graphdb is not None):
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
            "TestMetric2": "TestUNS"
        }),
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
            b'\xa0+ \x03P\xc8\x01\x18\x00')
    ])
def test_MQTT_GraphDb_UNS_Persistance(topic: str, message):
    uns_mqtt_graphdb = None
    try:
        uns_mqtt_graphdb = Uns_MQTT_GraphDb()
        uns_mqtt_graphdb.uns_client.loop()

        def on_message_decorator(client, userdata, msg):
            old_on_message(client, userdata, msg)
            if topic.startswith("spBv1.0/"):
                inboundPayload = sparkplug_b_pb2.Payload()
                inboundPayload.ParseFromString(message)
                message_dict = MessageToDict(inboundPayload)
                node_type = uns_mqtt_graphdb.graphdb_spb_node_types
            else:
                message_dict = message
                node_type = uns_mqtt_graphdb.graphdb_node_types
            try:
                with uns_mqtt_graphdb.graph_db_handler.connect().session(
                        database=uns_mqtt_graphdb.graph_db_handler.database
                ) as session:
                    session.execute_read(readNodes, node_type, topic,
                                         message_dict)
            except (exceptions.TransientError,
                    exceptions.TransactionError) as ex:
                pytest.fail(
                    f"Connection to either the MQTT Broker or the Graph DB did not happen: Exception {ex}"
                )
            finally:
                uns_mqtt_graphdb.uns_client.disconnect()

        # --- end of function

        publish_properties = None
        if (uns_mqtt_graphdb.uns_client.protocol ==
                Uns_MQTT_ClientWrapper.MQTTv5):
            publish_properties = Properties(PacketTypes.PUBLISH)

        if (topic.startswith("spBv1.0/")):
            payload = message
        else:
            payload = json.dumps(message)

        # Overriding on_message is more reliable that on_publish because some times on_publish was called before on_message
        old_on_message = uns_mqtt_graphdb.uns_client.on_message
        uns_mqtt_graphdb.uns_client.on_message = on_message_decorator

        # publish the messages as non-persistent to allow the tests to be idempotent across multiple runs
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
        if (uns_mqtt_graphdb is not None):
            uns_mqtt_graphdb.uns_client.disconnect()

        if ((uns_mqtt_graphdb is not None)
                and (uns_mqtt_graphdb.graph_db_handler is not None)):
            uns_mqtt_graphdb.graph_db_handler.close()


def readNodes(session: Session, node_type: tuple, topic: str, message: dict):
    """
        Helper function to read the database and compare the persisted data
    """
    topic_list: list = topic.split("/")
    records: list = []
    index = 0
    for node, node_type in zip(topic_list, node_type):
        query = f"MATCH (n:{node_type}{{ node_name: $node_name }})\n"
        query = query + "RETURN n"

        print(f"CQL statement to be executed: {query}")

        result = session.run(query, node_name=node)
        records = list(result)
        assert result is not None and len(records) == 1
        # check node_name
        assert records[0].values()[0].get("node_name") == node
        # labels is a frozen set
        assert node_type in records[0].values()[0].labels

        if index == len(topic_list) - 1:
            # this is a leaf node and the message attributes must match
            for attr_key in message.keys():
                value = message.get(attr_key)
                if isinstance(value, dict):
                    # Need to enhance test to handle nested dicts
                    warnings.warn(
                        message="Need to enhance test to handle nested dicts")
                else:
                    assert records[0].values()[0].get(attr_key) == message.get(
                        attr_key)
        index = index + 1

    return records
