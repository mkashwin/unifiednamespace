"""*******************************************************************************
* Copyright (c) 2021 Ashwin Krishnan
*
* All rights reserved. This program and the accompanying materials
* are made available under the terms of MIT and  is provided "as is",
* without warranty of any kind, express or implied, including but
* not limited to the warranties of merchantability, fitness for a
* particular purpose and noninfringement. In no event shall the
* authors, contributors or copyright holders be liable for any claim,
* damages or other liability, whether in an action of contract,
* tort or otherwise, arising from, out of or in connection with the software
* or the use or other dealings in the software.
*
* Contributors:
*    -
*******************************************************************************

Configuration reader for mqtt server where UNS and SparkplugB are published
"""

import logging
from pathlib import Path
from typing import Literal

from dynaconf import Dynaconf
from uns_mqtt.mqtt_listener import MQTTVersion

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
    version_code: Literal[MQTTVersion.MQTTv5, MQTTVersion.MQTTv311, MQTTVersion.MQTTv31] = settings.get(
        "mqtt.version", MQTTVersion.MQTTv5
    )
    qos: Literal[0, 1, 2] = settings.get("mqtt.qos", 2)
    reconnect_on_failure: bool = settings.get("mqtt.reconnect_on_failure", True)
    clean_session: bool | None = settings.get("mqtt.clean_session", None)

    host: str = settings.get("mqtt.host")
    port: int = settings.get("mqtt.port", 1883)
    username: str | None = settings.get("mqtt.username")
    password: str | None = settings.get("mqtt.password")
    tls: dict = settings.get("mqtt.tls", None)
    topics: list[str] = settings.get("mqtt.topics", ["spBv1.0/#"])
    if isinstance(topics, str):
        topics = [topics]
    keepalive: int = settings.get("mqtt.keep_alive", 60)
    ignored_attributes: dict = settings.get("mqtt.ignored_attributes", None)
    timestamp_key = settings.get("mqtt.timestamp_attribute", "timestamp")
    if host is None:
        LOGGER.error(
            "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
        )

    @classmethod
    def is_config_valid(cls) -> bool:
        """
        Checks if mandatory configurations were provided
        Does not check if the values provided are correct or not
        """
        return cls.host is not None
