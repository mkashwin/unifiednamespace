"""
MQTT listener that listens to ISA-95 UNS and SparkplugB and persists all messages to the GraphDB
"""
import logging
import random
import time

from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_graphdb.graphdb_config import settings
from uns_graphdb.graphdb_handler import GraphDBHandler

LOGGER = logging.getLogger(__name__)


class UnsMqttGraphDb:
    # pylint: disable=too-many-instance-attributes
    """
    Class instantiating MQTT listener that listens to ISA-95 UNS and SparkplugB and
    persists all messages to the GraphDB
    """

    def __init__(self):
        self.graph_db_handler = None
        self.uns_client: UnsMQTTClient = None

        self.load_mqtt_configs()
        self.load_graphdb_config()
        self.uns_client: UnsMQTTClient = UnsMQTTClient(
            client_id=self.client_id,
            clean_session=self.clean_session,
            userdata=None,
            protocol=self.mqtt_mqtt_version_code,
            transport=self.mqtt_transport,
            reconnect_on_failure=self.reconnect_on_failure)

        self.uns_client.on_message = self.on_message
        self.uns_client.on_disconnect = self.on_disconnect

        # Connect to the database
        self.graph_db_handler = GraphDBHandler(uri=self.graphdb_url,
                                               user=self.graphdb_user,
                                               password=self.graphdb_password,
                                               database=self.graphdb_database)

        self.uns_client.run(host=self.mqtt_host,
                            port=self.mqtt_port,
                            username=self.mqtt_username,
                            password=self.mqtt_password,
                            tls=self.mqtt_tls,
                            keepalive=self.mqtt_keepalive,
                            topics=self.topics,
                            qos=self.mqtt_qos)

    # end of init

    def load_mqtt_configs(self):
        """
        Read the MQTT configurations required to connect to the MQTT broker
        """
        # generate client ID with pub prefix randomly
        self.client_id = f"graphdb-{time.time()}-{random.randint(0, 1000)}"

        self.mqtt_transport: str = settings.get("mqtt.transport", "tcp")
        self.mqtt_mqtt_version_code: int = settings.get(
            "mqtt.version", UnsMQTTClient.MQTTv5)
        self.mqtt_qos: int = settings.get("mqtt.qos", 1)
        self.reconnect_on_failure: bool = settings.get(
            "mqtt.reconnect_on_failure", True)
        self.clean_session: bool = settings.get("mqtt.clean_session", None)

        self.mqtt_host: str = settings.mqtt["host"]
        self.mqtt_port: int = settings.get("mqtt.port", 1883)
        self.mqtt_username: str = settings.get("mqtt.username")
        self.mqtt_password: str = settings.get("mqtt.password")
        self.mqtt_tls: dict = settings.get("mqtt.tls", None)
        self.topics: str = settings.get("mqtt.topics", ["#"])
        self.mqtt_keepalive: int = settings.get("mqtt.keep_alive", 60)
        self.mqtt_ignored_attributes: dict = settings.get(
            "mqtt.ignored_attributes", None)
        self.mqtt_timestamp_key = settings.get("mqtt.timestamp_attribute",
                                               "timestamp")
        if self.mqtt_host is None:
            raise SystemError(
                "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
            )

    # --------------------------------------------------------------------------------------------

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
            settings.get("graphdb.uns_node_types",
                         ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE")))

        self.graphdb_spb_node_types: tuple = tuple(
            settings.get(
                "graphdb.spB_node_types",
                ("spBv1_0", "GROUP", "MESSAGE_TYPE", "EDGE_NODE", "DEVICE")))
        self.graphdb_nested_attribute_node_type: str = settings.get(
            "graphdb.nested_attribute_node_type", "NESTED_ATTRIBUTE")
        if self.graphdb_url is None:
            raise SystemError(
                "GraphDB Url not provided. Update key 'graphdb.url' in '../../conf/settings.yaml'",
            )

        if (self.graphdb_user is None) or (self.graphdb_password is None):
            raise SystemError(
                "GraphDB Username & Password not provided."
                "Update keys 'graphdb.username' and 'graphdb.password' "
                "in '../../conf/.secrets.yaml'")

    # --------------------------------------------------------------------------------------------
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
                node_types = self.graphdb_spb_node_types
            else:
                node_types = self.graphdb_node_types
            # get the payload as a dict object
            filtered_message = self.uns_client.get_payload_as_dict(
                topic=msg.topic,
                payload=msg.payload,
                mqtt_ignored_attributes=self.mqtt_ignored_attributes)

            # save message
            self.graph_db_handler.persist_mqtt_msg(
                topic=msg.topic,
                message=filtered_message,
                timestamp=filtered_message.get(self.mqtt_timestamp_key,
                                               time.time()),
                node_types=node_types,
                attr_node_type=self.graphdb_nested_attribute_node_type)
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
                "Error persisting the message to the Graph DB: %s \nTopic: %s \nMessage:%s",
                str(ex),
                msg.topic,
                msg.payload,
                stack_info=True,
                exc_info=True)

    # end of on_message----------------------------------------------------------------------------

    def on_disconnect(self, client, userdata, result_code, properties=None):
        """
        Callback function executed every time the client is disconnected from the MQTT broker
        """
        # pylint: disable=unused-argument
        if result_code != 0:
            LOGGER.error("Unexpected disconnection.:%s",
                         str(result_code),
                         stack_info=True,
                         exc_info=True)

    # end of on_disconnect-------------------------------------------------------------------------


# end of class ------------------------------------------------------------------------------------
def main():
    """
    Main function invoked from command line
    """
    uns_mqtt_graphdb = None
    try:
        uns_mqtt_graphdb = UnsMqttGraphDb()
        uns_mqtt_graphdb.uns_client.loop_forever()
    finally:
        if uns_mqtt_graphdb is not None:
            uns_mqtt_graphdb.uns_client.disconnect()

        if ((uns_mqtt_graphdb is not None)
                and (uns_mqtt_graphdb.graph_db_handler is not None)):
            uns_mqtt_graphdb.graph_db_handler.close()


# end of main()------------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
