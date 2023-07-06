"""
Test cases for uns_kafka.kafka_handler#KafkaHandler
"""

import json
import pytest

from confluent_kafka.admin import AdminClient
from confluent_kafka import Producer
from confluent_kafka import Consumer
from confluent_kafka import OFFSET_BEGINNING
from uns_kafka.uns_kafka_config import settings

from uns_kafka.kafka_handler import KafkaHandler

KAFKA_CONFIG: dict = settings.kafka["config"]
is_configs_provided: bool = "bootstrap.servers" in KAFKA_CONFIG

# json.loads(
#     os.environ.get(
#         "UNS_kafka__config",
#         '{"client.id": "uns_kafka_client", "bootstrap.servers": "localhost:9092"}'
#     ))


@pytest.mark.xfail(not is_configs_provided,
                   reason="Configurations have not been provided")
def test_kafka_handler_init():
    """
    KafkaHandler#init
    """
    kafka_handler: KafkaHandler = KafkaHandler(KAFKA_CONFIG)
    assert (kafka_handler.config == KAFKA_CONFIG
            ), f"""The kafka configuration was not properly initialized.\n
            Expected config:{KAFKA_CONFIG}, received {kafka_handler.config}"""
    assert kafka_handler.producer is not None and isinstance(
        kafka_handler.producer, Producer)


@pytest.mark.parametrize("mqtt_topic, kafka_topic", [(
    "a/b/c",
    "a_b_c",
), (
    "abc",
    "abc",
)])
def test_convert_mqtt_kafka_topic(mqtt_topic: str, kafka_topic: str):
    """
    Test conversion of MQTT Topics to Kafka
    """
    assert KafkaHandler.convert_mqtt_kafka_topic(
        mqtt_topic
    ) == kafka_topic, "Topic name in Kafka shouldn't have any '/'"


@pytest.mark.xfail(not is_configs_provided,
                   reason="Configurations have not been provided")
@pytest.mark.integrationtest
@pytest.mark.parametrize(
    "mqtt_topic, message", [(
        "a/b/c",
        '{"timestamp": 12345678, "message": "test message1"}',
    ), (
        "abc",
        '{"timestamp": 12345678, "message": "test message2"}',
    ),
                            ("spBv1.0/uns_group/NBIRTH/eon1", """{
         "timestamp":"1671554024644",
         "metrics": [{
             "name": "Inputs/A",
             "timestamp": "1486144502122",
             "alias": "0",
             "datatype": "11",
             "booleanValue": "False"
         }, {
             "name": "Inputs/B",
             "timestamp": "1486144502122",
             "alias": "1",
             "datatype": "11",
             "booleanValue": "False"
         }, {
             "name": "Outputs/E",
             "timestamp": "1486144502122",
             "alias": "2",
             "datatype": "11",
             "booleanValue": "False"
         }, {
             "name": "Outputs/F",
             "timestamp": "1486144502122",
             "alias": "3",
             "datatype": "11",
             "booleanValue": "False"
         }, {
             "name": "Properties/Hardware Make",
             "timestamp": "1486144502122",
             "alias": "4",
             "datatype": "12",
             "stringValue": "Sony"
         }, {
             "name": "Properties/Weight",
             "timestamp": "1486144502122",
             "alias": "5",
             "datatype": "3",
             "intValue": "200"
         }],
         "seq":"0" }""")])
def test_publish(mqtt_topic: str, message):
    """
    KafkaHandler#publish
    """
    kafka_handler: KafkaHandler = KafkaHandler(KAFKA_CONFIG)

    admin_client = AdminClient(KAFKA_CONFIG)

    consumer_config: dict = {}
    consumer_config["bootstrap.servers"] = KAFKA_CONFIG.get(
        "bootstrap.servers")
    consumer_config["client.id"] = "uns_kafka_test_consumer"
    consumer_config["group.id"] = "uns_kafka_test_consumers"
    consumer_config["auto.offset.reset"] = "latest"
    kafka_handler.publish(mqtt_topic, message)
    kafka_handler.flush()

    kafka_listener: Consumer = Consumer(consumer_config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(consumer, partitions):
        for part in partitions:
            part.offset = OFFSET_BEGINNING
        consumer.assign(partitions)

    kafka_topic = KafkaHandler.convert_mqtt_kafka_topic(mqtt_topic)
    kafka_listener.subscribe([kafka_topic], on_assign=reset_offset)
    try:
        while True:
            msg = kafka_listener.poll(1.0)
            if msg is None:
                # wait
                print("Waiting...")
            elif msg.error():
                assert pytest.fail(), msg.error()
            else:
                assert json.loads(
                    msg.value().decode("utf-8")) == json.loads(message)
                break

    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        admin_client.delete_topics([kafka_topic])
        kafka_listener.close()
