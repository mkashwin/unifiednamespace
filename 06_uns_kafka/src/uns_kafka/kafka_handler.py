"""
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
        self.config = config
        self.producer = Producer(config)

    def publish(self, topic: str, message: str):
        """
        Publishes the message to the correct kafka topic
        topic: Topic to publish the message to
        message: Message to be published
        """
        self.producer.produce(topic, message, callback=self.delivery_callback)
        self.producer.flush()

    def delivery_callback(err, msg):
        """
        Callback for the kafka producer to deliver the message
        err: Error message
        msg: Message to be delivered
        """
        if err:
            LOGGER.error("Failed to deliver message: %s: %s", err, msg)
        else:
            LOGGER.info("Message delivered to topic: %s", msg.topic())