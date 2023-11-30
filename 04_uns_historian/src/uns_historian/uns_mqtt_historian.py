"""
MQTT listener that listens to ISA-95 UNS and SparkplugB and persists all messages to the Historian
"""
import logging
import random
import time

from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_historian.historian_config import HistorianConfig, MQTTConfig
from uns_historian.historian_handler import HistorianHandler

LOGGER = logging.getLogger(__name__)


class UnsMqttHistorian:
    """
    MQTT listener that listens to ISA-95 UNS and SparkplugB and
    persists all messages to the Historian
    """

    def __init__(self):
        """
        Constructor
        """
        self.client_id = f"historian-{time.time()}-{random.randint(0, 1000)}"  # noqa: S311
        self.uns_client: UnsMQTTClient = UnsMQTTClient(
            client_id=self.client_id,
            clean_session=MQTTConfig.clean_session,
            userdata=None,
            protocol=MQTTConfig.mqtt_version_code,
            transport=MQTTConfig.mqtt_transport,
            reconnect_on_failure=MQTTConfig.reconnect_on_failure)

        # Connect to the database
        self.uns_historian_handler = HistorianHandler(
            hostname=HistorianConfig.historian_hostname,
            port=HistorianConfig.historian_port,
            database=HistorianConfig.historian_database,
            table=HistorianConfig.historian_table,
            user=HistorianConfig.historian_user,
            password=HistorianConfig.historian_password,
            sslmode=HistorianConfig.historian_sslmode)

        # Callback messages
        self.uns_client.on_message = self.on_message
        self.uns_client.on_disconnect = self.on_disconnect

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

        try:
            # get the payload as a dict object
            filtered_message = self.uns_client.get_payload_as_dict(
                topic=msg.topic,
                payload=msg.payload,
                mqtt_ignored_attributes=MQTTConfig.mqtt_ignored_attributes)
            # save message
            self.uns_historian_handler.persist_mqtt_msg(
                client_id=client._client_id.decode(),
                topic=msg.topic,
                timestamp=float(
                    filtered_message.get(MQTTConfig.mqtt_timestamp_key,
                                         time.time())),
                message=filtered_message)
        except SystemError as system_error:
            LOGGER.error(
                "Fatal Error while parsing Message: %s\nTopic: %s \nMessage:%s\nExiting.........",
                str(system_error),
                msg.topic,
                msg.payload,
                stack_info=True,
                exc_info=True)
        except Exception as ex:
            # pylint: disable=broad-exception-caught
            LOGGER.error(
                "Error persisting the message to the Historian DB: %s\nTopic: %s \nMessage:%s",
                str(ex),
                msg.topic,
                msg.payload,
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
        uns_mqtt_historian = None
        uns_mqtt_historian = UnsMqttHistorian()
        uns_mqtt_historian.uns_client.loop_forever()
    finally:
        if uns_mqtt_historian is not None:
            uns_mqtt_historian.uns_client.disconnect()
        if (uns_mqtt_historian
                is not None) and (uns_mqtt_historian.uns_historian_handler
                                  is not None):
            # incase the on_disconnect message is not called
            uns_mqtt_historian.uns_historian_handler.close()


if __name__ == "__main__":
    main()
