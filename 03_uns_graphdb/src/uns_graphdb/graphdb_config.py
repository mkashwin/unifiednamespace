"""
Configuration reader for mqtt server and Neo4J DB server details
"""
from pathlib import Path
from typing import Optional

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
    mqtt_transport: Optional[str] = settings.get("mqtt.transport", "tcp")
    mqtt_mqtt_version_code: int = settings.get("mqtt.version",
                                               UnsMQTTClient.MQTTv5)
    mqtt_qos: int = settings.get("mqtt.qos", 1)
    reconnect_on_failure: bool = settings.get("mqtt.reconnect_on_failure",
                                              True)
    clean_session: bool = settings.get("mqtt.clean_session", None)

    mqtt_host: Optional[str] = settings.mqtt["host"]
    mqtt_port: int = settings.get("mqtt.port", 1883)
    mqtt_username: Optional[str] = settings.get("mqtt.username")
    mqtt_password: Optional[str] = settings.get("mqtt.password")
    mqtt_tls: dict = settings.get("mqtt.tls", None)
    topics: Optional[str] = settings.get("mqtt.topics", ["#"])
    mqtt_keepalive: int = settings.get("mqtt.keep_alive", 60)
    mqtt_ignored_attributes: dict = settings.get("mqtt.ignored_attributes",
                                                 None)
    mqtt_timestamp_key = settings.get("mqtt.timestamp_attribute", "timestamp")
    if mqtt_host is None:
        raise SystemError(
            "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
        )


class GraphDBConfig:
    """
    Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'"
    """
    graphdb_url: Optional[str] = settings.graphdb["url"]
    graphdb_user: Optional[str] = settings.graphdb["username"]

    graphdb_password: Optional[str] = settings.graphdb["password"]
    # if we want to use a database different from the default
    graphdb_database: Optional[str] = settings.get("graphdb.database", None)

    graphdb_node_types: tuple = tuple(
        settings.get("graphdb.uns_node_types",
                     ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE")))

    graphdb_spb_node_types: tuple = tuple(
        settings.get(
            "graphdb.spB_node_types",
            ("spBv1_0", "GROUP", "MESSAGE_TYPE", "EDGE_NODE", "DEVICE")))
    graphdb_nested_attribute_node_type: Optional[str] = settings.get(
        "graphdb.nested_attribute_node_type", "NESTED_ATTRIBUTE")
    if graphdb_url is None:
        raise SystemError(
            "GraphDB Url not provided. Update key 'graphdb.url' in '../../conf/settings.yaml'",
        )

    if (graphdb_user is None) or (graphdb_password is None):
        raise SystemError(
            "GraphDB Username & Password not provided."
            "Update keys 'graphdb.username' and 'graphdb.password' "
            "in '../../conf/.secrets.yaml'")
