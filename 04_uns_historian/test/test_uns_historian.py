"""
Tests for uns_historian.uns_mqtt_historian
"""
import datetime
import json

import psycopg2
import pytest
import pytz
from google.protobuf.json_format import MessageToDict
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
from uns_historian.historian_config import MQTTConfig
from uns_historian.uns_mqtt_historian import UnsMqttHistorian
from uns_mqtt.mqtt_listener import UnsMQTTClient
from uns_sparkplugb.generated import sparkplug_b_pb2


@pytest.mark.integrationtest()
def test_uns_mqtt_historian():
    """
    Test case for UnsMqttHistorian#init()
    """
    uns_mqtt_historian = None
    try:
        uns_mqtt_historian = UnsMqttHistorian()
        assert uns_mqtt_historian is not None, (
            "Connection to either the MQTT Broker or the Historian DB did not happen"
        )
    except Exception as ex:
        pytest.fail(
            "Connection to either the MQTT Broker or the Historian DB did not happen:"
            f" Exception {ex}")
    finally:
        if uns_mqtt_historian is not None:
            uns_mqtt_historian.uns_client.disconnect()
        if (uns_mqtt_historian
                is not None) and (uns_mqtt_historian.uns_historian_handler
                                  is not None):

            uns_mqtt_historian.uns_historian_handler.close()


@pytest.mark.integrationtest()
@pytest.mark.parametrize(
    "topic, message",  # Test spB message persistance
    [

        # Test UNS message persistance
        ("test/uns/ar1/ln2", {
            "timestamp": 1486144502122,
            "TestMetric2": "TestUNS",
        }),
        (
            "spBv1.0/uns_group/NBIRTH/eon1",
            b"\x08\xc4\x89\x89\x83\xd30\x12\x17\n\x08Inputs/A\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ "
            b"\x0bp\x00\x12\x17\n\x08Inputs/B\x10\x01\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\t"
            b"Outputs/E\x10\x02\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\tOutputs/F\x10\x03\x18\xea\xf2\xf5\xa8\xa0+ "
            b"\x0bp\x00\x12+\n\x18Properties/Hardware Make\x10\x04\x18\xea\xf2\xf5\xa8\xa0+ \x0cz\x04Sony\x12!\n\x11"
            b"Properties/Weight\x10\x05\x18\xea\xf2\xf5\xa8\xa0+ \x03P\xc8\x01\x18\x00",
        ),
    ])
def test_uns_mqtt_historian_persistance(topic: str, message):
    """
    Test the persistance of message (UNS & SpB) to the database
    """
    uns_mqtt_historian = None
    try:
        uns_mqtt_historian = UnsMqttHistorian()
        uns_mqtt_historian.uns_client.loop()

        def on_message_decorator(client, userdata, msg):
            """
            Override / wrap the existing on_message callback so that
            on_publish is asleep until the message was received
            """
            old_on_message(client, userdata, msg)
            if topic.startswith("spBv1.0/"):
                inbound_payload = sparkplug_b_pb2.Payload()
                inbound_payload.ParseFromString(message)
                message_dict = MessageToDict(inbound_payload)

            else:
                message_dict = message

            try:
                cursor = uns_mqtt_historian.uns_historian_handler.get_cursor()
                query_timestamp: datetime = datetime.datetime.fromtimestamp(
                    float(message_dict.get(MQTTConfig.mqtt_timestamp_key)) /
                    1000)
                compare_with_historian(
                    cursor, uns_mqtt_historian.uns_historian_handler.table,
                    query_timestamp, topic, uns_mqtt_historian.client_id,
                    message_dict)
            finally:
                uns_mqtt_historian.uns_client.disconnect()

        # --- end of function

        publish_properties = None
        if uns_mqtt_historian.uns_client.protocol == UnsMQTTClient.MQTTv5:
            publish_properties = Properties(PacketTypes.PUBLISH)

        if topic.startswith("spBv1.0/"):
            payload = message
        else:
            payload = json.dumps(message)

        # Overriding on_message is more reliable that on_publish because some times
        # on_publish was called before on_message
        old_on_message = uns_mqtt_historian.uns_client.on_message
        uns_mqtt_historian.uns_client.on_message = on_message_decorator

        # publish the messages as non-persistent
        # to allow the tests to be idempotent across multiple runs
        uns_mqtt_historian.uns_client.publish(
            topic=topic,
            payload=payload,
            qos=uns_mqtt_historian.uns_client.qos,
            retain=False,
            properties=publish_properties)

        uns_mqtt_historian.uns_client.loop_forever()

    except Exception as ex:
        pytest.fail(
            "Connection to either the MQTT Broker or the Historian DB did not happen:"
            f" Exception {ex}")

    finally:
        if uns_mqtt_historian is not None:
            uns_mqtt_historian.uns_client.disconnect()
        if (uns_mqtt_historian
                is not None) and (uns_mqtt_historian.uns_historian_handler
                                  is not None):
            # incase the on_disconnect message is not called
            uns_mqtt_historian.uns_historian_handler.close()


def compare_with_historian(cursor, db_table: str, query_timestamp: datetime,
                           topic: str, client_id: str, message_dict: dict):
    # pylint: disable=too-many-arguments
    """
    Utility method for test case to compare data in the database with the data sent
    """
    try:
        # Read the database for the published data.

        sql_command = f"""SELECT *
                      FROM {db_table}
                      WHERE
                        time = %s AND
                        topic = %s AND
                        client_id=%s;"""  # noqa: S608

        with cursor:
            cursor.execute(sql_command, (query_timestamp, topic, client_id))
            data = cursor.fetchone()
            assert data is not None, "No data found in the database"
            db_msg = data[3]
            db_client = data[2]
            db_topic = data[1]
            assert db_msg == message_dict, "Message payload is not matching"
            assert db_client == client_id, "client_id are not matching"
            assert db_topic == topic, "Topic are not matching"  # topic
            # Need to localize the value in order to be able to compare with the info from db
            assert data[0] == pytz.utc.localize(
                query_timestamp), "Timestamp are not matching"  # timestamp

    except (psycopg2.DataError, psycopg2.OperationalError) as ex:
        pytest.fail(
            f"Connection to either the MQTT Broker or the Graph DB did not happen: Exception {ex}",
        )
    except AssertionError as ex:
        pytest.fail(f"Assertions did not pass: Exception {ex}")
