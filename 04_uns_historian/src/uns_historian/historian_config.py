"""
Configuration reader for mqtt server and Timescale DB server details
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
)
# `envvar_prefix` = export envvars with `export UNS_FOO=bar`.
# `settings_files` = Load these files in the order.


class MQTTConfig:
    """
    Read the MQTT configurations required to connect to the MQTT broker
    """

    # generate client ID with pub prefix randomly

    transport: Literal["tcp", "websockets"] = settings.get("mqtt.transport", "tcp")
    version: Literal[MQTTVersion.MQTTv5, MQTTVersion.MQTTv311, MQTTVersion.MQTTv31] = settings.get(
        "mqtt.version", MQTTVersion.MQTTv5
    )
    qos: Literal[0, 1, 2] = settings.get("mqtt.qos", 2)
    reconnect_on_failure: bool = settings.get("mqtt.reconnect_on_failure", True)
    clean_session: Optional[bool] = settings.get("mqtt.clean_session", None)

    host: Optional[str] = settings.get("mqtt.host")
    port: int = settings.get("mqtt.port", 1883)
    username: Optional[str] = settings.get("mqtt.username")
    password: Optional[str] = settings.get("mqtt.password")
    tls: dict = settings.get("mqtt.tls", None)
    topics: list[str] = settings.get("mqtt.topics", ["#"])
    if isinstance(topics, str):
        topics = [topics]
    keepalive: int = settings.get("mqtt.keep_alive", 60)
    ignored_attributes: dict = settings.get("mqtt.ignored_attributes", None)
    timestamp_key = settings.get("mqtt.timestamp_attribute", "timestamp")
    if host is None:
        LOGGER.error(
            "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
        )

    def is_config_valid(self) -> bool:
        return self.host is not None


class HistorianConfig:
    """
    Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'
    """

    hostname: str = settings.get("historian.hostname")
    port: int = settings.get("historian.port", None)
    user: str = settings.get("historian.username")
    password: str = settings.get("historian.password")
    sslmode: Optional[str] = settings.get("historian.sslmode", None)

    database: str = settings.get("historian.database")

    table: str = settings.get("historian.table")

    if hostname is None:
        LOGGER.error(
            "Historian Url not provided. " "Update key 'historian.hostname' in '../../conf/settings.yaml'",
        )
    if database is None:
        LOGGER.error(
            "Historian Database name  not provided. " "Update key 'historian.database' in '../../conf/settings.yaml'",
        )
    if table is None:
        LOGGER.error(
            f"""Table in Historian Database {database} not provided.
            Update key 'historian.table' in '../../conf/settings.yaml'"""
        )
    if (user is None) or (password is None):
        LOGGER.error(
            "Historian DB  Username & Password not provided."
            "Update keys 'historian.username' and 'historian.password' "
            "in '../../conf/.secrets.yaml'"
        )

    def is_config_valid(self) -> bool:
        return not (
            self.hostname is None or self.database is None or self.table is None or self.user is None or self.password is None
        )
