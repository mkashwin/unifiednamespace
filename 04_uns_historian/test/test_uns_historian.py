import datetime
import inspect
import json
import os
import sys
import pytz

import psycopg2
import pytest
from google.protobuf.json_format import MessageToDict
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
    sys.path.insert(1, os.path.join(cmd_subfolder, "uns_historian"))
if uns_mqtt_folder not in sys.path:
    sys.path.insert(2, uns_mqtt_folder)

from uns_historian.uns_mqtt_historian import Uns_Mqtt_Historian
from uns_mqtt.mqtt_listener import Uns_MQTT_ClientWrapper
from uns_sparkplugb.generated import sparkplug_b_pb2

is_configs_provided: bool = (os.path.exists(
    os.path.join(cmd_subfolder, "../conf/.secrets.yaml")) and os.path.exists(
        os.path.join(cmd_subfolder, "../conf/settings.yaml"))) or (bool(
            os.getenv("UNS_historian.username")))


@pytest.mark.integrationtest
@pytest.mark.xfail(
    not is_configs_provided,
    reason="Configurations absent, or these are not integration tests")
def test_Uns_Mqtt_Historian():
    uns_mqtt_historian = None
    try:
        uns_mqtt_historian = Uns_Mqtt_Historian()
        assert uns_mqtt_historian is not None, "Connection to either the MQTT Broker or the Historian DB did not happen"
    except Exception as ex:
        pytest.fail(
            f"Connection to either the MQTT Broker or the Historian DB did not happen: Exception {ex}"
        )
    finally:
        if (uns_mqtt_historian is not None):
            uns_mqtt_historian.uns_client.disconnect()
        if (uns_mqtt_historian
                is not None) and (uns_mqtt_historian.uns_historian_handler
                                  is not None):

            uns_mqtt_historian.uns_historian_handler.close()


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
def test_MQTT_Historian_UNS_Persistance(topic: str, message):
    uns_mqtt_historian = None
    try:
        uns_mqtt_historian = Uns_Mqtt_Historian()
        uns_mqtt_historian.uns_client.loop()

        def on_publish(client, userdata, result):
            if topic.startswith("spBv1.0/"):
                inboundPayload = sparkplug_b_pb2.Payload()
                inboundPayload.ParseFromString(message)
                message_dict = MessageToDict(inboundPayload)

            else:
                message_dict = message

            try:
                # Read the database for the published data.
                query_timestamp = datetime.datetime.fromtimestamp(
                    float(
                        message_dict.get(
                            uns_mqtt_historian.mqtt_timestamp_key)) / 1000)
                SQL_CMD = f"""SELECT *
                              FROM {uns_mqtt_historian.uns_historian_handler.table}
                              WHERE
                                time = %s AND
                                topic = %s AND
                                client_id=%s;
                            """

                with uns_mqtt_historian.uns_historian_handler.getCursor(
                ) as cursor:
                    cursor.execute(
                        SQL_CMD,
                        (query_timestamp, topic, uns_mqtt_historian.client_id))
                    data = cursor.fetchone()
                    db_msg = data[3]
                    db_client = data[2]
                    db_topic = data[1]
                    assert db_msg == message_dict, "Message payload is not matching"
                    assert db_client == uns_mqtt_historian.client_id, "client_id are not matching"
                    assert db_topic == topic, "Topic are not matching"  # topic
                    # Need to localize the value in order to be able to compare with the info from db
                    assert data[0] == pytz.utc.localize(
                        query_timestamp
                    ), "Timestamp are not matching"  # timestamp

            except (psycopg2.DataError, psycopg2.OperationalError) as ex:
                pytest.fail(
                    f"Connection to either the MQTT Broker or the Graph DB did not happen: Exception {ex}"
                )
            except AssertionError as ex:
                pytest.fail(f"Assertions did not pass: Exception {ex}")
            finally:
                uns_mqtt_historian.uns_client.disconnect()

        # --- end of function

        publish_properties = None
        if (uns_mqtt_historian.uns_client.protocol ==
                Uns_MQTT_ClientWrapper.MQTTv5):
            publish_properties = Properties(PacketTypes.PUBLISH)

        if (topic.startswith("spBv1.0/")):
            payload = message
        else:
            payload = json.dumps(message)

        uns_mqtt_historian.uns_client.on_publish = on_publish
        # publish the messages as non-persistent to allow the tests to be idempotent across multiple runs
        uns_mqtt_historian.uns_client.publish(
            topic=topic,
            payload=payload,
            qos=uns_mqtt_historian.uns_client.qos,
            retain=False,
            properties=publish_properties)

        uns_mqtt_historian.uns_client.loop_forever()
    except AssertionError as ex:
        print(f"Assertion failure in the test, {ex}")
    except Exception as ex:
        pytest.fail(
            f"Connection to either the MQTT Broker or the Historian DB did not happen: Exception {ex}"
        )

    finally:
        if (uns_mqtt_historian is not None):
            uns_mqtt_historian.uns_client.disconnect()
        if (uns_mqtt_historian
                is not None) and (uns_mqtt_historian.uns_historian_handler
                                  is not None):
            # incase the on_disconnect message is not called
            uns_mqtt_historian.uns_historian_handler.close()
