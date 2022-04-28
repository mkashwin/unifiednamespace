import inspect
import json
import random
import logging
import time
import os
import sys
from graphdb_config import settings
from graphdb_handler import GraphDBHandler
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


class Uns_MQTT_GraphDb:

    def __init__(self):
        self.graph_db_handler = None
        self.uns_client: Uns_MQTT_ClientWrapper = None

        self.load_mqtt_configs()
        self.load_graphdb_config()
        self.uns_client: Uns_MQTT_ClientWrapper = Uns_MQTT_ClientWrapper(
            client_id=self.client_id,
            clean_session=self.clean_session,
            userdata=None,
            protocol=self.mqtt_mqtt_version_code,
            transport=self.mqtt_transport,
            reconnect_on_failure=self.reconnect_on_failure)

        self.uns_client.on_message = self.on_message
        self.uns_client.on_disconnect = self.on_disconnect

        # Connect to the database
        self.graph_db_handler = GraphDBHandler(
            uri=self.graphdb_url,
            user=self.graphdb_user,
            password=self.graphdb_password,
            database=self.graphdb_database,
            node_types=self.graphdb_node_types)

        self.uns_client.run(host=self.mqtt_host,
                            port=self.mqtt_port,
                            username=self.mqtt_username,
                            password=self.mqtt_password,
                            tls=self.mqtt_tls,
                            keepalive=self.mqtt_keepalive,
                            topic=self.topic,
                            qos=self.mqtt_qos)

    # end of init

    def load_mqtt_configs(self):
        # generate client ID with pub prefix randomly
        self.client_id = f'graphdb-{time.time()}-{random.randint(0, 1000)}'

        self.mqtt_transport: str = settings.get("mqtt.transport", "tcp")
        self.mqtt_mqtt_version_code: int = settings.get(
            "mqtt.version", Uns_MQTT_ClientWrapper.MQTTv5)
        self.mqtt_qos: int = settings.get("mqtt.qos", 1)
        self.reconnect_on_failure: bool = settings.get(
            "mqtt.reconnect_on_failure", True)
        self.clean_session: bool = settings.get("mqtt.clean_session", None)

        self.mqtt_host: str = settings.mqtt["host"]
        self.mqtt_port: int = settings.get("mqtt.port", 1883)
        self.mqtt_username: str = settings.mqtt["username"]
        self.mqtt_password: str = settings.mqtt["password"]
        self.mqtt_tls: dict = settings.get("mqtt.tls", None)
        self.topic: str = settings.get("mqtt.topic", "#")
        self.mqtt_keepalive: int = settings.get("mqtt.keep_alive", 60)
        self.mqtt_ignored_attributes: dict = settings.get(
            "mqtt.ignored_attributes", None)
        self.mqtt_timestamp_key = settings.get("mqtt.timestamp_attribute",
                                               "timestamp")
        if (self.mqtt_host is None):
            raise ValueError(
                "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'"
            )

    # -------------------------------------------------------------------------------------------------------

    def load_graphdb_config(self):
        """
        Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'"
        """
        self.graphdb_url: str = settings.graphdb["url"]
        self.graphdb_user: str = settings.graphdb["username"]

        self.graphdb_password: str = settings.graphdb["password"]
        # if we want to use a database different from the default
        self.graphdb_database: str = settings.get("graphdb.database", None)

        self.graphdb_node_types: tuple = tuple(
            settings.get("graphdb.node_types",
                         ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE")))

        if (self.graphdb_url is None):
            raise ValueError(
                "GraphDB Url not provided. Update key 'graphdb.url' in '../../conf/settings.yaml'"
            )

        if ((self.graphdb_user is None) or (self.graphdb_password is None)):
            raise ValueError(
                "GraphDB Username & Password not provided."
                "Update keys 'graphdb.username' and 'graphdb.password' in '../../conf/.secrets.yaml'"
            )

    # -------------------------------------------------------------------------------------------------------
    def on_message(self, client, userdata, msg):
        LOGGER.debug("{"
                     f"Client: {client},"
                     f"Userdata: {userdata},"
                     f"Message: {msg},"
                     "}")
        try:

            filtered_message = Uns_MQTT_ClientWrapper.filter_ignored_attributes(
                msg.topic, json.loads(msg.payload.decode("utf-8")),
                self.mqtt_ignored_attributes)
            # save message
            self.graph_db_handler.persistMQTTmsg(topic=msg.topic,
                                                 message=filtered_message,
                                                 timestamp=getattr(
                                                     filtered_message,
                                                     self.mqtt_timestamp_key,
                                                     time.time()))
        except Exception as ex:
            LOGGER.error("Error persisting the message to the Graph DB: %s",
                         str(ex),
                         stack_info=True,
                         exc_info=True)
            raise ex

    # end of on_message----------------------------------------------------------------------------

    def on_disconnect(self, client, userdata, rc, properties=None):
        # Close the database connection when the MQTT broker gets disconnected
        if self.graph_db_handler is not None:
            self.graph_db_handler.close()
            self.graph_db_handler = None
        if (rc != 0):
            LOGGER.error("Unexpected disconnection.:%s",
                         str(rc),
                         stack_info=True,
                         exc_info=True)

    # end of on_disconnect-------------------------------------------------------------------------


# end of class ------------------------------------------------------------------------------------
def main():
    uns_mqtt_graphdb = None
    try:
        uns_mqtt_graphdb = Uns_MQTT_GraphDb()
        uns_mqtt_graphdb.uns_client.loop_forever()
    finally:
        if (uns_mqtt_graphdb is not None):
            uns_mqtt_graphdb.uns_client.disconnect()

        if ((uns_mqtt_graphdb is not None)
                and (uns_mqtt_graphdb.graph_db_handler is not None)):
            uns_mqtt_graphdb.graph_db_handler.close()


# end of main()------------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
