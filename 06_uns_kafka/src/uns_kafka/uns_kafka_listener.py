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
            protocol=MQTTConfig.version,
            transport=MQTTConfig.transport,
            reconnect_on_failure=MQTTConfig.reconnect_on_failure,
        )

        self.uns_client.on_message = self.on_message
        self.uns_client.on_disconnect = self.on_disconnect

        self.kafka_handler: KafkaHandler = KafkaHandler(KAFKAConfig.kafka_config_map)

        self.uns_client.run(
            host=MQTTConfig.host,
            port=MQTTConfig.port,
            username=MQTTConfig.username,
            password=MQTTConfig.password,
            tls=MQTTConfig.tls,
            keepalive=MQTTConfig.keep_alive,
            topics=MQTTConfig.topics,
            qos=MQTTConfig.qos,
        )

    def on_message(self, client, userdata, msg):
        """
        Callback function executed every time a message is received by the subscriber
        """
        LOGGER.debug("{" "Client: %s," "Userdata: %s," "Message: %s," "}", str(client), str(userdata), str(msg))

        # Connect to Kafka, convert the MQTT topic to Kafka topic and send the message
        self.kafka_handler.publish(
            msg.topic,
            self.uns_client.get_payload_as_dict(
                topic=msg.topic, payload=msg.payload, mqtt_ignored_attributes=self.mqtt_ignored_attributes
            ),
        )

    def on_disconnect(
        self,
        client,  # noqa: ARG002
        userdata,  # noqa: ARG002
        flags,  # noqa: ARG002
        reason_codes,
        properties=None,  # noqa: ARG002
    ):
        """
        Callback function executed every time the client is disconnected from the MQTT broker
        """
        # Cleanup when the MQTT broker gets disconnected
        LOGGER.debug("MQTT to Kafka connector got disconnected")
        if reason_codes != 0:
            LOGGER.error("Unexpected disconnection.:%s", str(reason_codes), stack_info=True, exc_info=True)
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
