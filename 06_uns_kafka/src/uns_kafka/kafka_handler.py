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

Manages connectivity to Kafka broker and publishes message
"""

import logging

from confluent_kafka import Producer

LOGGER = logging.getLogger(__name__)


class KafkaHandler:
    """
    Class to handle the connection to the Kafka broker as well as publishing the message to the correct kafka topics
    derived from the mqtt topics
    """

    def __init__(self, config: dict):
        """
        Constructor
        config: Configuration for the Kafka producer
        """
        self.config: dict = config
        self.producer: Producer = Producer(config)

    def publish(self, topic: str, message: str):
        """
        Publishes the message to the correct kafka topic
        topic: Topic to publish the message to
        message: Message to be published
        """
        # Check if Kafka Producer is valid else try creating new Producer to connect to Kafka.
        # Configure Retry
        if self.producer is None:
            self.producer = Producer(self.config)
        else:
            self.producer.produce(KafkaHandler.convert_mqtt_kafka_topic(topic), message, callback=self.delivery_callback)
            self.producer.poll(0)

    def delivery_callback(self, err: Exception, msg: dict):
        """
        Callback for the kafka producer to deliver the message
        err: Error message
        msg: Message to be delivered
        """
        if err:
            LOGGER.error("Failed to deliver message: %s: %s", err, msg)
        else:
            LOGGER.info("Message delivered to topic: %s", msg.topic())

    def flush(self) -> int:
        """
        Flush the publisher queue to the broker
        """
        self.producer.flush()

    @staticmethod
    def convert_mqtt_kafka_topic(mqtt_topic: str) -> str:
        """
        Converts the MQTT topic to the correct kafka topic
        topic: MQTT topic
        Does not handle wild cards as that is not expected here
        """
        return mqtt_topic.replace("/", ".")
