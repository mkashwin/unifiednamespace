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

Test cases for uns_kafka.uns_kafka_listener
"""

import json

import pytest
from confluent_kafka import OFFSET_END, Consumer
from confluent_kafka.admin import AdminClient
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
from uns_mqtt.mqtt_listener import MQTTVersion

from uns_kafka.uns_kafka_config import KAFKAConfig
from uns_kafka.uns_kafka_listener import UNSKafkaMapper


@pytest.mark.integrationtest()
def test_uns_kafka_mapper_init():
    """
    Test case for UNSKafkaMapper#init()
    """
    uns_kafka_mapper: UNSKafkaMapper = None
    try:
        uns_kafka_mapper = UNSKafkaMapper()
        assert uns_kafka_mapper is not None, "Connection to either the MQTT Broker or Kafka broker did not happen"

        assert uns_kafka_mapper.kafka_handler.producer, "Connection to Kafka broker did not happen"
        assert uns_kafka_mapper.kafka_handler.producer.list_topics(), "Connection to Kafka broker did not happen"
        assert uns_kafka_mapper.uns_client, "Connection to MQTT broker did not happen"

    except Exception as ex:
        pytest.fail("Connection to either the MQTT Broker or Kafka broker did not happen" f" Exception {ex}")
    finally:
        if uns_kafka_mapper is not None:
            uns_kafka_mapper.uns_client.disconnect()


@pytest.mark.integrationtest()
@pytest.mark.parametrize(
    "mqtt_topic, mqtt_message,kafka_topic,expected_kafka_msg",
    [
        (
            "a/b/c",
            '{"timestamp": 12345678, "message": "test message1"}',
            "a_b_c",
            '{"timestamp": 12345678, "message": "test message1"}',
        ),
        (
            "abc",
            '{"timestamp": 12345678, "message": "test message1"}',
            "abc",
            '{"timestamp": 12345678, "message": "test message2"}',
        ),
        (
            "spBv1.0/uns_group/NBIRTH/eon1",
            b"\x08\xc4\x89\x89\x83\xd30\x12\x17\n\x08Inputs/A\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ "
            b"\x0bp\x00\x12\x17\n\x08Inputs/B\x10\x01\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\t"
            b"Outputs/E\x10\x02\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\tOutputs/F\x10\x03\x18\xea\xf2\xf5\xa8\xa0+ "
            b"\x0bp\x00\x12+\n\x18Properties/Hardware Make\x10\x04\x18\xea\xf2\xf5\xa8\xa0+ \x0cz\x04Sony\x12!\n\x11"
            b"Properties/Weight\x10\x05\x18\xea\xf2\xf5\xa8\xa0+ \x03P\xc8\x01\x18\x00",
            "spBv1.0_uns_group_NBIRTH_eon1",
            {
                "timestamp": 1671554024644,
                "metrics": [
                    {
                        "name": "Inputs/A",
                        "timestamp": 1486144502122,
                        "alias": 0,
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Inputs/B",
                        "timestamp": 1486144502122,
                        "alias": 1,
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Outputs/E",
                        "timestamp": 1486144502122,
                        "alias": 2,
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Outputs/F",
                        "timestamp": 1486144502122,
                        "alias": 3,
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Properties/Hardware Make",
                        "timestamp": 1486144502122,
                        "alias": 4,
                        "datatype": 12,
                        "value": "Sony",
                    },
                    {
                        "name": "Properties/Weight",
                        "timestamp": 1486144502122,
                        "alias": 5,
                        "datatype": 3,
                        "value": 200,
                    },
                ],
                "seq": 0,
            },
        ),
    ],
)
def test_uns_kafka_mapper_publishing(mqtt_topic: str, mqtt_message, kafka_topic: str, expected_kafka_msg):
    """
    End to End testing of the listener by publishing to MQTT and validating correct message on KAFKA
    """
    uns_kafka_mapper: UNSKafkaMapper = None
    admin_client = None

    try:
        uns_kafka_mapper = UNSKafkaMapper()
        admin_client = AdminClient(KAFKAConfig.kafka_config_map)

        publish_properties = None
        if uns_kafka_mapper.uns_client.protocol == MQTTVersion.MQTTv5:
            publish_properties = Properties(PacketTypes.PUBLISH)

        if mqtt_topic.startswith("spBv1.0/"):
            payload = mqtt_message
        else:
            payload = json.dumps(mqtt_message)

        def on_message_decorator(client, userdata, msg):
            """
            Inline method decorator over on_message callback
            """
            old_on_message(client, userdata, msg)
            # Flush the producer to force publishing to the broker
            uns_kafka_mapper.kafka_handler.flush()

            # Create a consumer to read the Kafka broker
            kafka_listener: Consumer = get_kafka_consumer(KAFKAConfig.kafka_config_map)

            # Set up a callback to handle the '--reset' flag.
            def reset_offset(consumer, partitions):
                for part in partitions:
                    part.offset = OFFSET_END
                consumer.assign(partitions)

            kafka_listener.subscribe([kafka_topic], on_assign=reset_offset)
            check_kafka_topics(uns_kafka_mapper.uns_client, kafka_listener, expected_kafka_msg)
            # ---------------- end of inline method

        # Overriding on_message is more reliable that on_publish because some times
        # on_publish was called before on_message
        old_on_message = uns_kafka_mapper.uns_client.on_message
        uns_kafka_mapper.uns_client.on_message = on_message_decorator

        uns_kafka_mapper.uns_client.publish(
            topic=mqtt_topic, payload=payload, qos=uns_kafka_mapper.uns_client.qos, retain=False, properties=publish_properties
        )

    except Exception as ex:
        pytest.fail(f"Connection to either the MQTT Broker or Kafka broker did not happen: Exception {ex}")
    finally:
        if uns_kafka_mapper is not None:
            uns_kafka_mapper.uns_client.disconnect()
        if admin_client is not None:
            admin_client.delete_topics([kafka_topic])


def get_kafka_consumer(kafka_producer_config: dict) -> Consumer:
    """
    Utility method to create a consumer based on producer config
    """
    consumer_config: dict = {}
    consumer_config["bootstrap.servers"] = kafka_producer_config.get("bootstrap.servers")
    consumer_config["client.id"] = "uns_kafka_mapper_test_consumer"
    consumer_config["group.id"] = "uns_kafka_mapper_test_consumers"
    consumer_config["auto.offset.reset"] = "earliest"
    return Consumer(consumer_config)


def check_kafka_topics(mqtt_client, kafka_listener, expected_kafka_msg):
    """
    Checks the kafka topic for teh expected message
    """
    try:
        while True:
            msg = kafka_listener.poll(1.0)
            if msg is None:
                # wait
                print("Waiting...")  # noqa: T201

            elif msg.error():
                assert pytest.fail(), msg.error()
            else:
                assert json.loads(msg.value().decode("utf-8")) == json.loads(expected_kafka_msg)
                break

    finally:
        # Leave group and commit final offsets to Kafka
        kafka_listener.close()

        # disconnect from MQTT
        mqtt_client.disconnect()
