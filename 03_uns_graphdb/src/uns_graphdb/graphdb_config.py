"""
Configuration reader for mqtt server and Neo4J DB server details
"""
import logging
from pathlib import Path
from typing import Literal, Optional

from dynaconf import Dynaconf
from uns_mqtt.mqtt_listener import MQTTVersion

# Logger
LOGGER = logging.getLogger(__name__)

current_folder = Path(__file__).resolve()

settings = Dynaconf(
    envvar_prefix="UNS",
    root_path=current_folder,
    settings_files=["../../conf/settings.yaml", "../../conf/.secrets.yaml"],
    # `envvar_prefix` = export envvars with `export UNS_FOO=bar`.
    # `settings_files` = Load these files in the order.
)


class MQTTConfig:
    """
    Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'"
    for all MQTT Broker specific configurations
    """

    transport: Literal["tcp", "websockets"] = settings.get("mqtt.transport", "tcp")
    version: Literal[MQTTVersion.MQTTv5, MQTTVersion.MQTTv311, MQTTVersion.MQTTv31] = settings.get(
        "mqtt.version", MQTTVersion.MQTTv5
    )
    qos: Literal[0, 1, 2] = settings.get("mqtt.qos", 1)
    reconnect_on_failure: bool = settings.get("mqtt.reconnect_on_failure", True)
    clean_session: Optional[bool] = settings.get("mqtt.clean_session", None)

    host: str = settings.get("mqtt.host")
    port: int = settings.get("mqtt.port", 1883)
    username: Optional[str] = settings.get("mqtt.username")
    password: Optional[str] = settings.get("mqtt.password")
    tls: Optional[dict] = settings.get("mqtt.tls", None)
    topics: list[str] = settings.get("mqtt.topics", ["#"])
    if isinstance(topics, str):
        topics = [topics]
    keepalive: int = settings.get("mqtt.keep_alive", 60)
    ignored_attributes: Optional[dict] = settings.get("mqtt.ignored_attributes", None)
    timestamp_key = settings.get("mqtt.timestamp_attribute", "timestamp")
    if host is None:
        LOGGER.error(
            "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
        )

    def is_config_valid(self) -> bool:
        return self.host is not None


class GraphDBConfig:
    """
    Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'"
    """

    db_url: str = settings.get("graphdb.url")
    user: str = settings.get("graphdb.username")

    password: str = settings.get("graphdb.password")
    # if we want to use a database different from the default
    database: Optional[str] = settings.get("graphdb.database", None)

    uns_node_types: tuple = tuple(settings.get("graphdb.uns_node_types", ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE")))

    spb_node_types: tuple = tuple(
        settings.get("graphdb.spB_node_types", ("spBv1_0", "GROUP", "MESSAGE_TYPE", "EDGE_NODE", "DEVICE"))
    )
    nested_attributes_node_type: str = settings.get("graphdb.nested_attribute_node_type", "NESTED_ATTRIBUTE")

    if db_url is None:
        LOGGER.error(
            "GraphDB Url not provided. Update key 'graphdb.url' in '../../conf/settings.yaml'",
        )

    if (user is None) or (password is None):
        LOGGER.error(
            "GraphDB Username & Password not provided."
            "Update keys 'graphdb.username' and 'graphdb.password' "
            "in '../../conf/.secrets.yaml'"
        )

    def is_config_valid(self) -> bool:
        return not ((self.user is None) or (self.password is None) or self.db_url is None)
