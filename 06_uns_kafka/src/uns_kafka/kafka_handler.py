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

    def __init__(self):
        """
        Constructor

        """
