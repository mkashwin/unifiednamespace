import inspect
import json
import os
import sys
import pytest
from neo4j import exceptions, Session
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes

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
        })
    ])
def test_Uns_MQTT_GraphDb_UNS_Persistance(topic: str, message: dict):
    uns_mqtt_graphdb = None
    try:
        uns_mqtt_graphdb = Uns_MQTT_GraphDb()
        uns_mqtt_graphdb.uns_client.loop()
        publish_properties = None

        def on_publish(client, userdata, result):
            try:
                with uns_mqtt_graphdb.graph_db_handler.connect().session(
                        database=uns_mqtt_graphdb.graph_db_handler.database
                ) as session:
                    session.execute_read(readNodes,
                                         uns_mqtt_graphdb.graphdb_node_types,
                                         topic, message)
            except (exceptions.TransientError,
                    exceptions.TransactionError) as ex:
                pytest.fail(
                    f"Connection to either the MQTT Broker or the Graph DB did not happen: Exception {ex}"
                )
            finally:
                uns_mqtt_graphdb.uns_client.disconnect()

        if (uns_mqtt_graphdb.uns_client.protocol ==
                Uns_MQTT_ClientWrapper.MQTTv5):
            publish_properties = Properties(PacketTypes.PUBLISH)

        payload = getMessageToPublish(topic=topic, message=message)

        uns_mqtt_graphdb.uns_client.on_publish = on_publish

        uns_mqtt_graphdb.uns_client.publish(
            topic=topic,
            payload=payload,
            qos=uns_mqtt_graphdb.uns_client.qos,
            retain=True,
            properties=publish_properties)

        uns_mqtt_graphdb.uns_client.loop_forever()

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


def getMessageToPublish(topic, message):
    if (topic.startswith("spBv1.0")):
        pytest.fail, "currently not able to test spB Payloads"
    return json.dumps(message)


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
            for attr_keys in message.keys():
                assert records[0].values()[0].get(attr_keys) == message.get(
                    attr_keys)
        index = index + 1

    return records
