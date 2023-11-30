"""
Configuration reader for mqtt server where UNS are read from and the Kafka broker to publish to
"""
from pathlib import Path

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

    mqtt_transport: str = settings.get("mqtt.transport", "tcp")
    mqtt_version_code: int = settings.get("mqtt.version", UnsMQTTClient.MQTTv5)
    mqtt_qos: int = settings.get("mqtt.qos", 2)
    reconnect_on_failure: bool = settings.get("mqtt.reconnect_on_failure",
                                              True)
    clean_session: bool = settings.get("mqtt.clean_session", None)

    mqtt_host: str = settings.mqtt["host"]
    mqtt_port: int = settings.get("mqtt.port", 1883)
    mqtt_username: str = settings.get("mqtt.username")
    mqtt_password: str = settings.get("mqtt.password")
    mqtt_tls: dict = settings.get("mqtt.tls", None)
    topics: list = settings.get("mqtt.topics", ["#"])
    mqtt_keepalive: int = settings.get("mqtt.keep_alive", 60)
    mqtt_ignored_attributes: dict = settings.get("mqtt.ignored_attributes",
                                                 None)
    mqtt_timestamp_key: str = settings.get("mqtt.timestamp_attribute",
                                           "timestamp")
    if mqtt_host is None:
        raise SystemError(
            "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
        )


class KAFKAConfig:
    """
        Read the Kafka configurations required to connect to the Kafka broker
        """
    kafka_config_map: dict = settings.kafka["config"]
