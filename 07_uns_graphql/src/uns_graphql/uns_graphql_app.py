"""
Entry point for all GraphQL queries to the UNS
"""
import logging
import random
import time
from typing import Optional

from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_graphql.graphql_config import settings

LOGGER = logging.getLogger(__name__)


class UNSGraphql:
    """
    Class providing the entry point for all GraphQL queries to the UNS & SPB Namespaces
    """

    def __init__(self):
        self.load_mqtt_configs()
        self.load_graphdb_config()
        self.load_historian_config()
        self.load_kafka_configs()

    def load_mqtt_configs(self):
        """
        Read the MQTT configurations required to connect to the MQTT broker
        """
        # generate client ID with pub prefix randomly
        self.client_id = f"graphql-{time.time()}-{random.randint(0, 1000)}"  # noqa: S311

        self.mqtt_transport: Optional[str] = settings.get(
            "mqtt.transport", "tcp")
        self.mqtt_mqtt_version_code: int = settings.get(
            "mqtt.version", UnsMQTTClient.MQTTv5)
        self.mqtt_qos: int = settings.get("mqtt.qos", 1)
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
        self.mqtt_timestamp_key = settings.get("mqtt.timestamp_attribute",
                                               "timestamp")
        if self.mqtt_host is None:
            raise SystemError(
                "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
            )

    def load_graphdb_config(self):
        """
        Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'"
        """
        self.graphdb_url: Optional[str] = settings.graphdb["url"]
        self.graphdb_user: Optional[str] = settings.graphdb["username"]

        self.graphdb_password: Optional[str] = settings.graphdb["password"]
        # if we want to use a database different from the default
        self.graphdb_database: Optional[str] = settings.get(
            "graphdb.database", None)

        self.graphdb_node_types: tuple = tuple(
            settings.get("graphdb.uns_node_types",
                         ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE")))

        self.graphdb_spb_node_types: tuple = tuple(
            settings.get(
                "graphdb.spB_node_types",
                ("spBv1_0", "GROUP", "MESSAGE_TYPE", "EDGE_NODE", "DEVICE")))
        self.graphdb_nested_attribute_node_type: Optional[str] = settings.get(
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

    def load_kafka_configs(self):
        """
        Read the Kafka configurations required to connect to the Kafka broker
        """
        self.kafka_config_map: dict = settings.kafka["config"]

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


def main():
    """
    Main function invoked from command line
    """
    print("TO DO")


if __name__ == "__main__":
    main()
