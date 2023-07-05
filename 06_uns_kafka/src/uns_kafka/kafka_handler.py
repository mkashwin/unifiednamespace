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
            self.producer.produce(KafkaHandler.convert_MQTT_KAFKA_topic(topic),
                                  message,
                                  callback=self.delivery_callback)

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
    def convert_MQTT_KAFKA_topic(mqtt_topic: str) -> str:
        """
        Converts the MQTT topic to the correct kafka topic
        topic: MQTT topic
        """
        return mqtt_topic.replace("/", "_")
