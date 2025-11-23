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

Configuration reader for the simulator
"""

import logging
from pathlib import Path
from typing import Literal

from aiomqtt import ProtocolVersion, TLSParameters
from dynaconf import Dynaconf
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

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
    Read the MQTT configurations required to connect to the MQTT broker
    """

    transport: Literal["tcp", "websockets"] = settings.get(
        "mqtt.transport", "tcp")
    version: ProtocolVersion = ProtocolVersion(
        settings.get("mqtt.version", ProtocolVersion.V5))
    properties: Properties = Properties(
        PacketTypes.CONNECT) if version == ProtocolVersion.V5 else None
    qos: Literal[0, 1, 2] = settings.get("mqtt.qos", 1)
    clean_session: bool | None = settings.get("mqtt.clean_session", None)

    host: str = settings.get("mqtt.host")
    port: int = settings.get("mqtt.port", 1883)
    username: str | None = settings.get("mqtt.username")
    password: str | None = settings.get("mqtt.password")
    tls: dict | None = settings.get("mqtt.tls", None)

    tls_params: TLSParameters | None = (
        TLSParameters(
            ca_certs=tls.get("ca_certs"),
            certfile=tls.get("certfile"),
            keyfile=tls.get("keyfile"),
            cert_reqs=tls.get("cert_reqs"),
            ciphers=tls.get("ciphers"),
            keyfile_password=tls.get("keyfile_password"),
        )
        if tls is not None
        else None
    )

    tls_insecure: bool | None = tls.get(
        "insecure_cert") if tls is not None else None

    keep_alive: int = settings.get("mqtt.keep_alive", 60)
    retry_interval: int = settings.get("mqtt.retry_interval", 10)

    @classmethod
    def is_config_valid(cls) -> bool:
        """
        Checks if mandatory configurations were provided
        Does not check if the values provided are correct or not
        """
        return cls.host is not None
