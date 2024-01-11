"""
MQTT listener that listens to SparkplugB name space for messages and publishes to ISA-95 UNS
"""
import logging
import random
import time

from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_spb_mapper.sparkplugb_enc_config import MQTTConfig
from uns_spb_mapper.spb2unspublisher import Spb2UNSPublisher

LOGGER = logging.getLogger(__name__)


# listens to SparkplugB name space for messages and publishes to ISA-95
# https://www.hivemq.com/solutions/manufacturing/smart-manufacturing-using-isa95-mqtt-sparkplug-and-uns/
class UNSSparkPlugBMapper:

    """
    MQTT listener that listens to SparkplugB name space for messages and publishes to ISA-95 UNS
    """

    def __init__(self):
        """
        Constructor
        """
        self.uns_client: UnsMQTTClient = None

        self.client_id = f"uns_sparkplugb_listener-{time.time()}-{random.randint(0, 1000)}"  # noqa: S311

        self.uns_client: UnsMQTTClient = UnsMQTTClient(
            client_id=self.client_id,
            clean_session=MQTTConfig.clean_session,
            userdata=None,
            protocol=MQTTConfig.version_code,
            transport=MQTTConfig.transport,
            reconnect_on_failure=MQTTConfig.reconnect_on_failure,
        )

        self.uns_client.on_message = self.on_message
        self.uns_client.on_disconnect = self.on_disconnect

        self.spb_2_uns_pub: Spb2UNSPublisher = Spb2UNSPublisher(self.uns_client)
        self.uns_client.run(
            host=MQTTConfig.host,
            port=MQTTConfig.port,
            username=MQTTConfig.username,
            password=MQTTConfig.password,
            tls=MQTTConfig.tls,
            keepalive=MQTTConfig.keepalive,
            topics=MQTTConfig.topics,
            qos=MQTTConfig.qos,
        )

    def on_message(self, client, userdata, msg):
        """
        Callback function executed every time a message is received by the subscriber
        """
        LOGGER.debug("{" "Client: %s," "Userdata: %s," "Message: %s," "}", str(client), str(userdata), str(msg))
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
                            + f"Depth of tree should not be more than 5, got {len(topic_path)}",
                        )
                    self.spb_2_uns_pub.transform_spb_and_publish_to_uns(
                        msg.payload, group_id, message_type, edge_node_id, device_id
                    )
                else:
                    LOGGER.error("Message received on an Unknown/non compliant SparkplugB topic: %s", msg.topic)
            else:
                LOGGER.debug("Subscribed to a  non SparkplugB topic: %s. Message ignored", msg.topic)
        except SystemError as system_error:
            LOGGER.error("Fatal Error while parsing Message: %s. Exiting", str(system_error), stack_info=True, exc_info=True)
            # raise system_error
        except Exception as ex:
            # pylint: disable=broad-exception-caught
            LOGGER.error("Error parsing SparkplugB message payload: %s", str(ex), stack_info=True, exc_info=True)

    def on_disconnect(
        self,
        client,  # noqa: ARG002
        userdata,  # noqa: ARG002
        result_code,
        properties=None,  # noqa: ARG002
    ):
        """
        Callback function executed every time the client is disconnected from the MQTT broker
        """
        # Cleanup when the MQTT broker gets disconnected
        LOGGER.debug("SparkplugB listener got disconnected")
        if result_code != 0:
            LOGGER.error("Unexpected disconnection.:%s", str(result_code), stack_info=True, exc_info=True)


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
