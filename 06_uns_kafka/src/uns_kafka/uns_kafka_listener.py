"""
MQTT listener that listens to UNS namespace for messages and publishes to corresponding Kafka topic
"""
import logging
import random
import time

from uns_kafka.kafka_handler import KafkaHandler
from uns_kafka.uns_kafka_config import settings
from uns_mqtt.mqtt_listener import UnsMQTTClient

LOGGER = logging.getLogger(__name__)


class UNSKafkaMapper:
    """
    MQTT listener that listens UNS namespace for messages and publishes to corresponding Kafka topic
    """

    def __init__(self):
        """
        Constructor
        """
        self.uns_client: UnsMQTTClient = None
        self.load_mqtt_configs()
        self.load_kafka_configs()
        self.uns_client: UnsMQTTClient = UnsMQTTClient(
            client_id=self.client_id,
            clean_session=self.clean_session,
            userdata=None,
            protocol=self.mqtt_mqtt_version_code,
            transport=self.mqtt_transport,
            reconnect_on_failure=self.reconnect_on_failure)

        self.uns_client.on_message = self.on_message
        self.uns_client.on_disconnect = self.on_disconnect

        self.kafka_handler: KafkaHandler = KafkaHandler(self.kafka_config_map)

        self.uns_client.run(host=self.mqtt_host,
                            port=self.mqtt_port,
                            username=self.mqtt_username,
                            password=self.mqtt_password,
                            tls=self.mqtt_tls,
                            keepalive=self.mqtt_keepalive,
                            topics=self.topics,
                            qos=self.mqtt_qos)

    def load_mqtt_configs(self):
        """
        Read the MQTT configurations required to connect to the MQTT broker
        """
        # generate client ID with pub prefix randomly
        self.client_id = f'uns_kafka_listener-{time.time()}-{random.randint(0, 1000)}'

        self.mqtt_transport: str = settings.get("mqtt.transport", "tcp")
        self.mqtt_mqtt_version_code: int = settings.get(
            "mqtt.version", UnsMQTTClient.MQTTv5)
        self.mqtt_qos: int = settings.get("mqtt.qos", 2)
        self.reconnect_on_failure: bool = settings.get(
            "mqtt.reconnect_on_failure", True)
        self.clean_session: bool = settings.get("mqtt.clean_session", None)

        self.mqtt_host: str = settings.mqtt["mqtt.host"]
        self.mqtt_port: int = settings.get("mqtt.port", 1883)
        self.mqtt_username: str = settings.get("mqtt.username")
        self.mqtt_password: str = settings.get("mqtt.password")
        self.mqtt_tls: dict = settings.get("mqtt.tls", None)
        self.topics: list = settings.get("mqtt.topics", ["spBv1.0/#"])
        self.mqtt_keepalive: int = settings.get("mqtt.keep_alive", 60)
        self.mqtt_ignored_attributes: dict = settings.get(
            "mqtt.ignored_attributes", None)
        self.mqtt_timestamp_key: str = settings.get("mqtt.timestamp_attribute",
                                                    "timestamp")
        if self.mqtt_host is None:
            raise SystemError(
                "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'"
            )

    def load_kafka_configs(self):
        """
        Read the Kafka configurations required to connect to the Kafka broker
        """
        self.kafka_config_map: dict = settings.mqtt["kafka.config"]

    def on_message(self, client, userdata, msg):
        """
        Callback function executed every time a message is received by the subscriber
        """
        LOGGER.debug("{"
                     "Client: %s,"
                     "Userdata: %s,"
                     "Message: %s,"
                     "}", str(client), str(userdata), str(msg))
        # Connect to Kakfa, convert the MQTT topic to Kafka topic and send the message

    def on_disconnect(self, client, userdata, result_code, properties=None):
        """
        Callback function executed every time the client is disconnected from the MQTT broker
        """
        # Cleanup when the MQTT broker gets disconnected
        # Cleanup when the MQTT broker gets disconnected
        LOGGER.debug("Kafka connector got disconnected")
        if result_code != 0:
            LOGGER.error("Unexpected disconnection.:%s",
                         str(result_code),
                         stack_info=True,
                         exc_info=True)


def main():
    """
    Main function invoked from command line
    """
    try:
        uns_kafka_mapper = UNSKafkaMapper()
        uns_kafka_mapper.uns_client.loop_forever()
    finally:
        if uns_kafka_mapper is not None:
            uns_kafka_mapper.uns_client.disconnect()


if __name__ == '__main__':
    main()
