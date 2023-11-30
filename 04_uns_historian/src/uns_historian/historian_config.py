"""
Configuration reader for mqtt server and Timescale DB server details
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
)
# `envvar_prefix` = export envvars with `export UNS_FOO=bar`.
# `settings_files` = Load these files in the order.


class MQTTConfig:
    """
    Read the MQTT configurations required to connect to the MQTT broker
    """
    # generate client ID with pub prefix randomly

    mqtt_transport: Optional[str] = settings.get("mqtt.transport", "tcp")
    mqtt_mqtt_version_code: int = settings.get("mqtt.version",
                                               UnsMQTTClient.MQTTv5)
    mqtt_qos: int = settings.get("mqtt.qos", 2)
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


class HistorianConfig:
    """
    Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'
    """
    historian_hostname: str = settings.historian["hostname"]
    historian_port: int = settings.get("historian.port", None)
    historian_user: str = settings.historian["username"]
    historian_password: str = settings.historian["password"]
    historian_sslmode: Optional[str] = settings.get("historian.sslmode", None)

    historian_database: str = settings.historian["database"]

    historian_table: str = settings.historian["table"]

    if historian_hostname is None:
        raise SystemError(
            "Historian Url not provided. "
            "Update key 'historian.hostname' in '../../conf/settings.yaml'", )
    if historian_database is None:
        raise SystemError(
            "Historian Database name  not provided. "
            "Update key 'historian.database' in '../../conf/settings.yaml'", )
    if historian_table is None:
        raise SystemError(
            f"""Table in Historian Database {historian_database} not provided.
            Update key 'historian.table' in '../../conf/settings.yaml'""")
    if ((historian_user is None) or (historian_password is None)):
        raise SystemError(
            "Historian DB  Username & Password not provided."
            "Update keys 'historian.username' and 'historian.password' "
            "in '../../conf/.secrets.yaml'")
