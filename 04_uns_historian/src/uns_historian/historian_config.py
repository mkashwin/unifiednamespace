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

Configuration reader for mqtt server and Timescale DB server details
"""

import logging
import ssl
from pathlib import Path
from typing import Literal

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
    clean_session: bool | None = settings.get("mqtt.clean_session", None)

    host: str | None = settings.get("mqtt.host")
    port: int = settings.get("mqtt.port", 1883)
    username: str | None = settings.get("mqtt.username")
    password: str | None = settings.get("mqtt.password")
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

    @classmethod
    def is_config_valid(cls) -> bool:
        """
        Checks if mandatory configurations were provided
        Does not check if the values provided are correct or not
        """
        return cls.host is not None


class HistorianConfig:
    """
    Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'
    """

    hostname: str = settings.get("historian.hostname")
    port: int = settings.get("historian.port", None)
    user: str = settings.get("historian.username")
    password: str = settings.get("historian.password")
    sslmode: str | None = settings.get("historian.sslmode", None)
    sslcert: str | None = settings.get("historian.sslcert", None)
    sslkey: str | None = settings.get("historian.sslkey", None)
    sslrootcert: str | None = settings.get("historian.sslrootcert", None)
    sslcrl: str | None = settings.get("historian.sslcrl", None)

    database: str = settings.get("historian.database")

    table: str = settings.get("historian.table")

    if hostname is None:
        LOGGER.error(
            "Historian Url not provided. Update key 'historian.hostname' in '../../conf/settings.yaml'",
        )
    if database is None:
        LOGGER.error(
            "Historian Database name  not provided. Update key 'historian.database' in '../../conf/settings.yaml'",
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

    @classmethod
    def is_config_valid(cls) -> bool:
        """
        Checks if mandatory configurations were provided
        Does not check if the values provided are correct or not
        """
        return not (
            cls.hostname is None or cls.database is None or cls.table is None or cls.user is None or cls.password is None
        )

    @classmethod
    def get_ssl_context(cls) -> ssl.SSLContext | None:
        """
        Creates the SSL Context needed for DB connect based on the SSL Params
        See https://github.com/MagicStack/asyncpg/issues/737
        """
        if cls.sslmode:
            ssl_context: ssl.SSLContext = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.options |= {
                "disable": ssl.OP_NO_SSLv2,
                "allow": ssl.OP_NO_SSLv3,
                "prefer": ssl.OP_NO_TLSv1,
                "require": ssl.OP_NO_TLSv1_1,
                "verify-ca": ssl.OP_NO_TLSv1_2,
                "verify-full": ssl.OP_NO_TLSv1_3,
            }.get(cls.db_sslmode.lower(), 0)

            if cls.sslcert:
                ssl_context.load_cert_chain(certfile=cls.sslcert, keyfile=cls.sslkey)

            if cls.sslrootcert:
                ssl_context.load_verify_locations(cafile=cls.sslrootcert)

            if cls.sslcrl:
                ssl_context.load_verify_locations(cafile=cls.sslcrl)

            return ssl_context
        return None
