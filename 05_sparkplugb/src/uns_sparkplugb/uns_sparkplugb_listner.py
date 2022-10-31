import inspect
import random
import logging
import time
import os
import sys
from sparkplugb_enc_config import settings
# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            '..', '..', '02_mqtt-cluster', 'src')))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

from uns_mqtt.mqtt_listener import Uns_MQTT_ClientWrapper

LOGGER = logging.getLogger(__name__)


# listens to SparkplugB name space for
class Uns_SparkPlugB_Mapper:

    def __init__(self):
        self.graph_db_handler = None
        self.uns_client: Uns_MQTT_ClientWrapper = None
        self.load_mqtt_configs()
        self.load_sparkplugb_configs()
        self.uns_client: Uns_MQTT_ClientWrapper = Uns_MQTT_ClientWrapper(
            client_id=self.client_id,
            clean_session=self.clean_session,
            userdata=None,
            protocol=self.mqtt_mqtt_version_code,
            transport=self.mqtt_transport,
            reconnect_on_failure=self.reconnect_on_failure)

        self.uns_client.on_message = self.on_message
        self.uns_client.on_disconnect = self.on_disconnect

    def load_mqtt_configs(self):
        # generate client ID with pub prefix randomly
        self.client_id = f'uns_sparkplugb_listener-{time.time()}-{random.randint(0, 1000)}'

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
        self.topic: str = settings.get("mqtt.topic", "spBv1.0/#")
        self.mqtt_keepalive: int = settings.get("mqtt.keep_alive", 60)
        self.mqtt_ignored_attributes: dict = settings.get(
            "mqtt.ignored_attributes", None)
        self.mqtt_timestamp_key = settings.get("mqtt.timestamp_attribute",
                                               "timestamp")
        if (self.mqtt_host is None):
            raise ValueError(
                "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'"
            )

    def load_sparkplugb_configs(self):
        """
        Load the configurations which give the mapping of SparkplugB name space :
        spBv1.0/<group_id>/<message_type>/<edge_node_id>/[<device_id>]
        to
        UNS Namespace under ISA-95:
        <enterprise>/<facility>/<area>/<line>/<device>
        """
        self.sparkplugb_mappings = settings.sparkplugb

    def on_message(self, client, userdata, msg):
        """
        Callback function executed every time a message is received by the subscriber
        """
        LOGGER.debug()

    def on_disconnect(self, client, userdata, rc, properties=None):
        # Close the database connection when the MQTT broker gets disconnected
        LOGGER.debug()


def main():
    try:
        uns_spb_mapper = Uns_SparkPlugB_Mapper()
        uns_spb_mapper.uns_client.loop_forever()
    finally:
        if (uns_spb_mapper is not None):
            uns_spb_mapper.uns_client.disconnect()


if __name__ == '__main__':
    main()
