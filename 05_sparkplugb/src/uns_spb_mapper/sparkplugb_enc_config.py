"""
Configuration reader for mqtt server where UNS and SparkplugB are published
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
)

# `envvar_prefix` = export envvars with `export UNS_FOO=bar`.
# `settings_files` = Load these files in the order.


class MQTTConfig:
    """
    Read the MQTT configurations required to connect to the MQTT broker
    """
    transport: str = settings.get("mqtt.transport", "tcp")
    version_code: int = settings.get("mqtt.version", UnsMQTTClient.MQTTv5)
    qos: int = settings.get("mqtt.qos", 2)
    reconnect_on_failure: bool = settings.get("mqtt.reconnect_on_failure",
                                              True)
    clean_session: Optional[bool] = settings.get("mqtt.clean_session", None)

    host: str = settings.mqtt["host"]
    port: int = settings.get("mqtt.port", 1883)
    username: Optional[str] = settings.get("mqtt.username")
    password: Optional[str] = settings.get("mqtt.password")
    tls: dict = settings.get("mqtt.tls", None)
    topics: List[str] = settings.get("mqtt.topics", ["spBv1.0/#"])
    if isinstance(topics, str):
        topics = [topics]
    keepalive: int = settings.get("mqtt.keep_alive", 60)
    ignored_attributes: dict = settings.get("mqtt.ignored_attributes", None)
    timestamp_key = settings.get("mqtt.timestamp_attribute", "timestamp")
    if host is None:
        raise SystemError(
            "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
        )
