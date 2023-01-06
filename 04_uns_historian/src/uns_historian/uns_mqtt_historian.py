"""
MQTT listener that listens to ISA-95 UNS and SparkplugB and persists all messages to the Historian
"""
import inspect
import json
import logging
import os
import random
import sys
import time

from google.protobuf.json_format import MessageToDict
from historian_config import settings
from historian_handler import HistorianHandler

# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            '..', '..', '02_mqtt-cluster', 'src')))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)
from uns_mqtt.mqtt_listener import Uns_MQTT_ClientWrapper
from uns_sparkplugb.generated import sparkplug_b_pb2

LOGGER = logging.getLogger(__name__)

SPARKPLUG_NS = "spBv1.0/"


class Uns_Mqtt_Historian:
    """
    MQTT listener that listens to ISA-95 UNS and SparkplugB and persists all messages to the Historian
    """

    def __init__(self):
        self.load_mqtt_configs()
        self.load_historian_config()
        self.uns_client: Uns_MQTT_ClientWrapper = Uns_MQTT_ClientWrapper(
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
        # generate client ID with pub prefix randomly
        self.client_id = f'historian-{time.time()}-{random.randint(0, 1000)}'

        self.mqtt_transport: str = settings.get("mqtt.transport", "tcp")
        self.mqtt_mqtt_version_code: int = settings.get(
            "mqtt.version", Uns_MQTT_ClientWrapper.MQTTv5)
        self.mqtt_qos: int = settings.get("mqtt.qos", 2)
        self.reconnect_on_failure: bool = settings.get(
            "mqtt.reconnect_on_failure", True)
        self.clean_session: bool = settings.get("mqtt.clean_session", None)

        self.mqtt_host: str = settings.mqtt["host"]
        self.mqtt_port: int = settings.get("mqtt.port", 1883)
        self.mqtt_username: str = settings.mqtt["username"]
        self.mqtt_password: str = settings.mqtt["password"]
        self.mqtt_tls: dict = settings.get("mqtt.tls", None)
        self.topics: str = settings.get("mqtt.topics", ["#"])
        self.mqtt_keepalive: int = settings.get("mqtt.keep_alive", 60)
        self.mqtt_ignored_attributes: dict = settings.get(
            "mqtt.ignored_attributes", None)
        self.mqtt_timestamp_key = settings.get("mqtt.timestamp_attribute",
                                               "timestamp")
        if self.mqtt_host is None:
            raise ValueError(
                "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'"
            )

    def load_historian_config(self):
        """
        Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'
        """
        self.historian_hostname: str = settings.historian["hostname"]
        self.historian_port: int = settings.get("historian.port", None)
        self.historian_user: str = settings.historian["username"]
        self.historian_password: str = settings.historian["password"]
        self.historian_sslmode: str = settings.get("historian.sslmode", None)

        self.historian_database: str = settings.historian["database"]

        self.historian_table: str = settings.historian["table"]

        if self.historian_hostname is None:
            raise ValueError(
                "Historian Url not provided. Update key 'historian.hostname' in '../../conf/settings.yaml'"
            )
        if self.historian_database is None:
            raise ValueError(
                "Historian Database name  not provided. Update key 'historian.database' in '../../conf/settings.yaml'"
            )
        if self.historian_table is None:
            raise ValueError(
                f"""Table in Historian Database {self.historian_database} not provided.
                Update key 'historian.table' in '../../conf/settings.yaml'""")
        if ((self.historian_user is None)
                or (self.historian_password is None)):
            raise ValueError(
                "Historian DB  Username & Password not provided."
                "Update keys 'historian.username' and 'historian.password' in '../../conf/.secrets.yaml'"
            )

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
            if msg.topic.startswith(SPARKPLUG_NS):
                # This message was to the sparkplugB namespace in protobuf format
                inboundPayload = sparkplug_b_pb2.Payload()
                inboundPayload.ParseFromString(msg.payload)
                decoded_payload = MessageToDict(inboundPayload)
            else:
                # TODO Assuming all messages to UNS are json hence convertible to dict
                decoded_payload = json.loads(msg.payload.decode("utf-8"))
            filtered_message = Uns_MQTT_ClientWrapper.filter_ignored_attributes(
                msg.topic, decoded_payload, self.mqtt_ignored_attributes)
            # save message
            self.uns_historian_handler.persistMQTTmsg(
                client_id=client._client_id.decode(),
                topic=msg.topic,
                timestamp=float(
                    filtered_message.get(self.mqtt_timestamp_key,
                                         time.time())),
                message=filtered_message)
        except Exception as ex:
            LOGGER.error(
                "Error persisting the message to the Historian DB: %s",
                str(ex),
                stack_info=True,
                exc_info=True)
            raise ex

    def on_disconnect(self, client, userdata, rc, properties=None):
        """
        Callback function executed every time the client is disconnected from the MQTT broker
        """
        # Close the database connection when the MQTT broker gets disconnected
        if self.uns_historian_handler is not None:
            self.uns_historian_handler.close()
            self.uns_historian_handler = None
        if rc != 0:
            LOGGER.error("Unexpected disconnection.:%s",
                         str(rc),
                         stack_info=True,
                         exc_info=True)


def main():
    """
    Main function invoked from command line
    """
    try:
        uns_mqtt_historian = Uns_Mqtt_Historian()
        uns_mqtt_historian.uns_client.loop_forever()
    finally:
        if uns_mqtt_historian is not None:
            uns_mqtt_historian.uns_client.disconnect()
        if (uns_mqtt_historian
                is not None) and (uns_mqtt_historian.uns_historian_handler
                                  is not None):
            # incase the on_disconnect message is not called
            uns_mqtt_historian.uns_historian_handler.close()


if __name__ == '__main__':
    main()
