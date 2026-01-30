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

Test cases for uns_kafka.kafka_handler#KafkaHandler
"""

import json
import uuid

import pytest
from confluent_kafka import OFFSET_BEGINNING, Consumer, Producer
from confluent_kafka.admin import AdminClient

from uns_kafka.kafka_handler import KafkaHandler
from uns_kafka.uns_kafka_config import settings

KAFKA_CONFIG: dict = settings.get("kafka.config")


@pytest.mark.integrationtest
def test_kafka_handler_init():
    """
    KafkaHandler#init
    """
    kafka_handler: KafkaHandler = KafkaHandler(KAFKA_CONFIG)
    assert kafka_handler.config == KAFKA_CONFIG, f"""The kafka configuration was not properly initialized.\n
            Expected config:{KAFKA_CONFIG}, received {kafka_handler.config}"""
    assert kafka_handler.producer is not None and isinstance(kafka_handler.producer, Producer)


@pytest.mark.parametrize(
    "mqtt_topic, kafka_topic",
    [
        (
            "a/b/c",
            "a.b.c",
        ),
        (
            "abc",
            "abc",
        ),
    ],
)
def test_convert_mqtt_kafka_topic(mqtt_topic: str, kafka_topic: str):
    """
    Test conversion of MQTT Topics to Kafka
    """
    assert (
        KafkaHandler.convert_mqtt_kafka_topic(
            mqtt_topic,
        )
        == kafka_topic
    ), "Topic name in Kafka shouldn't have any '/'"


@pytest.mark.integrationtest()
@pytest.mark.parametrize(
    "mqtt_topic, message",
    [
        (
            "a/b/c",
            '{"timestamp": 12345678, "message": "test message1"}',
        ),
        (
            "abc",
            '{"timestamp": 12345678, "message": "test message2"}',
        ),
        (
            "spBv1.0/uns_group/NBIRTH/eon1",
            """{
         "timestamp":1671554024644,
         "metrics": [{
             "name": "Inputs/A",
             "timestamp": 1486144502122,
             "alias": 0,
             "datatype": 11,
             "value": false
         }, {
             "name": "Inputs/B",
             "timestamp": 1486144502122,
             "alias": 1,
             "datatype": 11,
             "value": "false"
         }, {
             "name": "Outputs/E",
             "timestamp": 1486144502122,
             "alias": 2,
             "datatype": 11,
             "value": false
         }, {
             "name": "Outputs/F",
             "timestamp": 1486144502122,
             "alias": 3,
             "datatype": 11,
             "value": false
         }, {
             "name": "Properties/Hardware Make",
             "timestamp": 1486144502122,
             "alias": "4",
             "datatype": "12",
             "value": "Sony"
         }, {
             "name": "Properties/Weight",
             "timestamp": 1486144502122,
             "alias": 5,
             "datatype": 3,
             "value": 200
         }],
         "seq":0 }""",
        ),
    ],
)
def test_publish(mqtt_topic: str, message):
    """
    KafkaHandler#publish
    """
    # Make topic unique to avoid parallel test interference
    mqtt_topic = f"{mqtt_topic}/{uuid.uuid4()}"
    kafka_handler: KafkaHandler = KafkaHandler(KAFKA_CONFIG)
    assert kafka_handler is not None, f"Kafka configurations did not create a valid kafka producer: {KAFKA_CONFIG}"
    assert (
        kafka_handler.producer.list_topics(
            timeout=10,
        )
        is not None
    ), f"Kafka configurations did allow connectivity to broker: {KAFKA_CONFIG}"
    admin_client: AdminClient = AdminClient(KAFKA_CONFIG)

    consumer_config: dict = {}
    consumer_config["bootstrap.servers"] = KAFKA_CONFIG.get("bootstrap.servers")
    consumer_config["client.id"] = "uns_kafka_test_consumer"
    consumer_config["group.id"] = f"uns_kafka_test_consumers_{uuid.uuid4()}"
    consumer_config["auto.offset.reset"] = "earliest"
    kafka_handler.publish(mqtt_topic, message)
    kafka_handler.flush(timeout=10)

    kafka_listener: Consumer = Consumer(consumer_config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(consumer, partitions):
        for part in partitions:
            part.offset = OFFSET_BEGINNING
        consumer.assign(partitions)

    kafka_topic = KafkaHandler.convert_mqtt_kafka_topic(mqtt_topic)

    kafka_listener.subscribe([kafka_topic], on_assign=reset_offset)
    try:
        # Run tests only when connectivity to broker is there
        attempts = 0
        while True:
            msg = kafka_listener.poll(1.0)
            if msg is None:
                attempts += 1
                if attempts > 15:
                    pytest.fail("Timeout waiting for message")
                # wait
                print("Waiting...")  # noqa: T201
            elif msg.error():
                pytest.fail(f"Consumer error: {msg.error()}")
            else:
                assert json.loads(msg.value().decode("utf-8")) == json.loads(message)
                break

    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        kafka_listener.close()
        admin_client.delete_topics([kafka_topic])
