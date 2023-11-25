"""
MQTT listener that listens to ISA-95 UNS and SparkplugB and persists all messages to the Historian
"""
import logging
import random
import time
from typing import Optional

from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_historian.historian_config import settings
from uns_historian.historian_handler import HistorianHandler

LOGGER = logging.getLogger(__name__)


class UnsMqttHistorian:
    # pylint: disable=too-many-instance-attributes
    """
    MQTT listener that listens to ISA-95 UNS and SparkplugB and
    persists all messages to the Historian
    """

    def __init__(self):
        self.load_mqtt_configs()
        self.load_historian_config()
        self.uns_client: UnsMQTTClient = UnsMQTTClient(
            client_id=self.client_id,
            clean_session=self.clean_session,
            userdata=None,
            protocol=self.mqtt_mqtt_version_code,
            transport=self.mqtt_transport,
            reconnect_on_failure=self.reconnect_on_failure)
        # Connect to the database
        self.uns_historian_handler = HistorianHandler(
            hostname=self.historian_hostname,
            port=self.historian_port,
            database=self.historian_database,
            table=self.historian_table,
            user=self.historian_user,
            password=self.historian_password,
            sslmode=self.historian_sslmode)
        self.uns_client.on_message = self.on_message
        self.uns_client.on_disconnect = self.on_disconnect

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
        self.client_id = f"historian-{time.time()}-{random.randint(0, 1000)}"  # noqa: S311

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
        self.topics: Optional[str] = settings.get("mqtt.topics", ["#"])
        self.mqtt_keepalive: int = settings.get("mqtt.keep_alive", 60)
        self.mqtt_ignored_attributes: dict = settings.get(
            "mqtt.ignored_attributes", None)
        self.mqtt_timestamp_key = settings.get("mqtt.timestamp_attribute",
                                               "timestamp")
        if self.mqtt_host is None:
            raise SystemError(
                "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
            )

    def load_historian_config(self):
        """
        Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'
        """
        self.historian_hostname: Optional[str] = settings.historian["hostname"]
        self.historian_port: int = settings.get("historian.port", None)
        self.historian_user: Optional[str] = settings.historian["username"]
        self.historian_password: Optional[str] = settings.historian["password"]
        self.historian_sslmode: Optional[str] = settings.get(
            "historian.sslmode", None)

        self.historian_database: Optional[str] = settings.historian["database"]

        self.historian_table: Optional[str] = settings.historian["table"]

        if self.historian_hostname is None:
            raise SystemError(
                "Historian Url not provided. "
                "Update key 'historian.hostname' in '../../conf/settings.yaml'",
            )
        if self.historian_database is None:
            raise SystemError(
                "Historian Database name  not provided. "
                "Update key 'historian.database' in '../../conf/settings.yaml'",
            )
        if self.historian_table is None:
            raise SystemError(
                f"""Table in Historian Database {self.historian_database} not provided.
                Update key 'historian.table' in '../../conf/settings.yaml'""")
        if ((self.historian_user is None)
                or (self.historian_password is None)):
            raise SystemError(
                "Historian DB  Username & Password not provided."
                "Update keys 'historian.username' and 'historian.password' "
                "in '../../conf/.secrets.yaml'")

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
                mqtt_ignored_attributes=self.mqtt_ignored_attributes)
            # save message
            self.uns_historian_handler.persist_mqtt_msg(
                client_id=client._client_id.decode(),
                topic=msg.topic,
                timestamp=float(
                    filtered_message.get(self.mqtt_timestamp_key,
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
