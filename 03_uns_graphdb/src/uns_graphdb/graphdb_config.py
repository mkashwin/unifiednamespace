"""
Configuration reader for mqtt server and Neo4J DB server details
"""
from pathlib import Path
from typing import List, Optional

from dynaconf import Dynaconf
from uns_mqtt.mqtt_listener import UnsMQTTClient

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
    transport: str = settings.get("mqtt.transport", "tcp")
    version: int = settings.get("mqtt.version", UnsMQTTClient.MQTTv5)
    qos: int = settings.get("mqtt.qos", 1)
    reconnect_on_failure: bool = settings.get("mqtt.reconnect_on_failure",
                                              True)
    clean_session: Optional[bool] = settings.get("mqtt.clean_session", None)

    host: str = settings.mqtt["host"]
    port: int = settings.get("mqtt.port", 1883)
    username: Optional[str] = settings.get("mqtt.username")
    password: Optional[str] = settings.get("mqtt.password")
    tls: Optional[dict] = settings.get("mqtt.tls", None)
    topics: List[str] = settings.get("mqtt.topics", ["#"])
    if isinstance(topics, str):
        topics = [topics]
    keepalive: int = settings.get("mqtt.keep_alive", 60)
    ignored_attributes: Optional[dict] = settings.get(
        "mqtt.ignored_attributes", None)
    timestamp_key = settings.get("mqtt.timestamp_attribute", "timestamp")
    if host is None:
        raise SystemError(
            "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
        )


class GraphDBConfig:
    """
    Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'"
    """
    db_url: str = settings.graphdb["url"]
    user: str = settings.graphdb["username"]

    password: str = settings.graphdb["password"]
    # if we want to use a database different from the default
    database: Optional[str] = settings.get("graphdb.database", None)

    uns_node_types: tuple = tuple(
        settings.get("graphdb.uns_node_types",
                     ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE")))

    spb_node_types: tuple = tuple(
        settings.get(
            "graphdb.spB_node_types",
            ("spBv1_0", "GROUP", "MESSAGE_TYPE", "EDGE_NODE", "DEVICE")))
    nested_attributes_node_type: str = settings.get(
        "graphdb.nested_attribute_node_type", "NESTED_ATTRIBUTE")
    if db_url is None:
        raise SystemError(
            "GraphDB Url not provided. Update key 'graphdb.url' in '../../conf/settings.yaml'",
        )

    if (user is None) or (password is None):
        raise SystemError(
            "GraphDB Username & Password not provided."
            "Update keys 'graphdb.username' and 'graphdb.password' "
            "in '../../conf/.secrets.yaml'")
