"""
Configuration reader for mqtt server where UNS are read from and the Kafka broker to publish to
"""
import logging
from pathlib import Path
from typing import List, Literal, Optional

from dynaconf import Dynaconf
from uns_mqtt.mqtt_listener import MQTTVersion

# Logger
LOGGER = logging.getLogger(__name__)

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

    transport: Literal["tcp", "websockets"] = settings.get("mqtt.transport", "tcp")
    version: Literal[MQTTVersion.MQTTv5, MQTTVersion.MQTTv311, MQTTVersion.MQTTv31] = settings.get(
        "mqtt.version", MQTTVersion.MQTTv5
    )
    qos: Literal[0, 1, 2] = settings.get("mqtt.qos", 2)
    reconnect_on_failure: bool = settings.get("mqtt.reconnect_on_failure", True)
    clean_session: Optional[bool] = settings.get("mqtt.clean_session", None)

    host: str = settings.get("mqtt.host")
    port: int = settings.get("mqtt.port", 1883)
    username: str = settings.get("mqtt.username")
    password: str = settings.get("mqtt.password")
    tls: Optional[dict] = settings.get("mqtt.tls", None)
    topics: List[str] = settings.get("mqtt.topics", ["#"])
    if isinstance(topics, str):
        topics = [topics]
    keep_alive: int = settings.get("mqtt.keep_alive", 60)
    ignored_attributes: Optional[dict] = settings.get("mqtt.ignored_attributes", None)
    timestamp_key: str = settings.get("mqtt.timestamp_attribute", "timestamp")
    if host is None:
        LOGGER.error(
            "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
        )

    def is_config_valid(self) -> bool:
        return self.host is not None


class KAFKAConfig:
    """
    Read the Kafka configurations required to connect to the Kafka broker
    """

    kafka_config_map: dict = settings.get("kafka.config")
