"""
MQTT listener that listens to SparkplugB name space for messages and publishes to ISA-95 UNS
"""
import logging
import random
import time
from typing import Optional

from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_spb_mapper.sparkplugb_enc_config import settings
from uns_spb_mapper.spb2unspublisher import Spb2UNSPublisher

LOGGER = logging.getLogger(__name__)


# listens to SparkplugB name space for messages and publishes to ISA-95
# https://www.hivemq.com/solutions/manufacturing/smart-manufacturing-using-isa95-mqtt-sparkplug-and-uns/
class UNSSparkPlugBMapper:
    # pylint: disable=too-many-instance-attributes
    """
    MQTT listener that listens to SparkplugB name space for messages and publishes to ISA-95 UNS
    """

    def __init__(self):
        """
        Constructor
        """
        self.uns_client: UnsMQTTClient = None
        self.load_mqtt_configs()
        self.load_sparkplugb_configs()
        self.uns_client: UnsMQTTClient = UnsMQTTClient(
            client_id=self.client_id,
            clean_session=self.clean_session,
            userdata=None,
            protocol=self.mqtt_mqtt_version_code,
            transport=self.mqtt_transport,
            reconnect_on_failure=self.reconnect_on_failure)

        self.uns_client.on_message = self.on_message
        self.uns_client.on_disconnect = self.on_disconnect

        self.spb_2_uns_pub: Spb2UNSPublisher = Spb2UNSPublisher(
            self.uns_client)
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
        self.client_id = f"uns_sparkplugb_listener-{time.time()}-{random.randint(0, 1000)}"  # noqa: S311

        self.mqtt_transport: Optional[str] = settings.get(
            "mqtt.transport", "tcp")
        self.mqtt_mqtt_version_code: int = settings.get(
            "mqtt.version", UnsMQTTClient.MQTTv5)
        self.mqtt_qos: int = settings.get("mqtt.qos", 2)
        self.reconnect_on_failure: bool = settings.get(
            "mqtt.reconnect_on_failure", True)
        self.clean_session: bool = settings.get("mqtt.clean_session", None)

        self.mqtt_host: Optional[str] = settings.mqtt["host"]
        self.mqtt_port: int = settings.get("mqtt.port", 1883)
        self.mqtt_username: Optional[str] = settings.get("mqtt.username")
        self.mqtt_password: Optional[str] = settings.get("mqtt.password")
        self.mqtt_tls: dict = settings.get("mqtt.tls", None)
        self.topics: list = settings.get("mqtt.topics", ["spBv1.0/#"])
        self.mqtt_keepalive: int = settings.get("mqtt.keep_alive", 60)
        self.mqtt_ignored_attributes: dict = settings.get(
            "mqtt.ignored_attributes", None)
        self.mqtt_timestamp_key = settings.get("mqtt.timestamp_attribute",
                                               "timestamp")
        if self.mqtt_host is None:
            raise SystemError(
                "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
            )

    def load_sparkplugb_configs(self):
        """
        Load the SparkplugB configurations
        """
        # Currently no configurations

    def on_message(self, client, userdata, msg):
        """
        Callback function executed every time a message is received by the subscriber
        """
        LOGGER.debug("{"
                     "Client: %s,"
                     "Userdata: %s,"
                     "Message: %s,"
                     "}", str(client), str(userdata), str(msg))
        try:
            if msg.topic.startswith(UnsMQTTClient.SPARKPLUG_NS):
                topic_path: list[str] = msg.topic.split("/")
                # sPB topic structure spBv1.0/<group_id>/<message_type>/<edge_node_id>/<[device_id]>
                # device_id is optional. all others are mandatory
                if len(topic_path) >= 4:
                    group_id = topic_path[1]
                    message_type = topic_path[2]
                    edge_node_id = topic_path[3]
                    device_id = None
                    if len(topic_path) == 5:
                        device_id = topic_path[4]
                    else:
                        raise ValueError(
                            f"Unknown SparkplugB topic received: {msg.topic}."
                            +
                            f"Depth of tree should not be more than 5, got {len(topic_path)}",
                        )
                    self.spb_2_uns_pub.transform_spb_and_publish_to_uns(
                        msg.payload, group_id, message_type, edge_node_id,
                        device_id)
                else:
                    LOGGER.error(
                        "Message received on an Unknown/non compliant SparkplugB topic: %s",
                        msg.topic)
            else:
                LOGGER.debug(
                    "Subscribed to a  non SparkplugB topic: %s. Message ignored",
                    msg.topic)
        except SystemError as system_error:
            LOGGER.error("Fatal Error while parsing Message: %s. Exiting",
                         str(system_error),
                         stack_info=True,
                         exc_info=True)
            # raise system_error
        except Exception as ex:
            # pylint: disable=broad-exception-caught
            LOGGER.error("Error parsing SparkplugB message payload: %s",
                         str(ex),
                         stack_info=True,
                         exc_info=True)

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
        LOGGER.debug("SparkplugB listener got disconnected")
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
        uns_spb_mapper = None
        uns_spb_mapper = UNSSparkPlugBMapper()
        uns_spb_mapper.uns_client.loop_forever()
    finally:
        if uns_spb_mapper is not None:
            uns_spb_mapper.uns_client.disconnect()


if __name__ == "__main__":
    main()
