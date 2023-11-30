"""
MQTT listener that listens to UNS namespace for messages and publishes to corresponding Kafka topic
"""
import logging
import random
import time

from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_kafka.kafka_handler import KafkaHandler
from uns_kafka.uns_kafka_config import KAFKAConfig, MQTTConfig

LOGGER = logging.getLogger(__name__)


class UNSKafkaMapper:
    # pylint: disable=too-many-instance-attributes
    """
    MQTT listener that listens UNS namespace for messages and publishes to corresponding Kafka topic
    """

    def __init__(self):
        """
        Constructor
        """
        self.uns_client: UnsMQTTClient = None
        # generate client ID with pub prefix randomly
        self.client_id = f"uns_kafka_listener-{time.time()}-{random.randint(0, 1000)}"  # noqa: S311

        self.uns_client: UnsMQTTClient = UnsMQTTClient(
            client_id=self.client_id,
            clean_session=MQTTConfig.clean_session,
            userdata=None,
            protocol=MQTTConfig.mqtt_version_code,
            transport=MQTTConfig.mqtt_transport,
            reconnect_on_failure=MQTTConfig.reconnect_on_failure)

        self.uns_client.on_message = self.on_message
        self.uns_client.on_disconnect = self.on_disconnect

        self.kafka_handler: KafkaHandler = KafkaHandler(
            KAFKAConfig.kafka_config_map)

        self.uns_client.run(host=MQTTConfig.mqtt_host,
                            port=MQTTConfig.mqtt_port,
                            username=MQTTConfig.mqtt_username,
                            password=MQTTConfig.mqtt_password,
                            tls=MQTTConfig.mqtt_tls,
                            keepalive=MQTTConfig.mqtt_keepalive,
                            topics=MQTTConfig.topics,
                            qos=MQTTConfig.mqtt_qos)

    def on_message(self, client, userdata, msg):
        """
        Callback function executed every time a message is received by the subscriber
        """
        LOGGER.debug("{"
                     "Client: %s,"
                     "Userdata: %s,"
                     "Message: %s,"
                     "}", str(client), str(userdata), str(msg))

        # Connect to Kafka, convert the MQTT topic to Kafka topic and send the message
        self.kafka_handler.publish(
            msg.topic,
            self.uns_client.get_payload_as_dict(
                topic=msg.topic,
                payload=msg.payload,
                mqtt_ignored_attributes=self.mqtt_ignored_attributes))

    def on_disconnect(
            self,
            client,  # noqa: ARG002
            userdata,  # noqa: ARG002
            result_code,
            properties=None):  # noqa: ARG002
        """
        Callback function executed every time the client is disconnected from the MQTT broker
        """
        # pylint: disable=unused-argument
        # Cleanup when the MQTT broker gets disconnected
        LOGGER.debug("MQTT to Kafka connector got disconnected")
        if result_code != 0:
            LOGGER.error("Unexpected disconnection.:%s",
                         str(result_code),
                         stack_info=True,
                         exc_info=True)
        # force flushing the kafka connection
        self.kafka_handler.flush()


def main():
    """
    Main function invoked from command line
    """
    try:
        uns_kafka_mapper = None
        uns_kafka_mapper = UNSKafkaMapper()
        uns_kafka_mapper.uns_client.loop_forever()
    finally:
        if uns_kafka_mapper is not None:
            uns_kafka_mapper.uns_client.disconnect()


if __name__ == "__main__":
    main()
