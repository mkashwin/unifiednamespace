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

Configuration reader for mqtt server, kafka, historian and Neo4J DB server details
"""

import logging
import ssl
from pathlib import Path
from typing import Literal

import neo4j
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
)

# `envvar_prefix` = export envvars with `export UNS_FOO=bar`.
# `settings_files` = Load these files in the order.


class MQTTConfig:
    """
    Read the MQTT configurations required to connect to the MQTT broker
    """

    # generate client ID with pub prefix randomly

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
    mqtt_timestamp_key = settings.get("mqtt.timestamp_attribute", "timestamp")
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


class GraphDBConfig:
    """
    Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'"
    """

    conn_url: str = settings.get("graphdb.url")
    user: str = settings.get("graphdb.username")

    password: str = settings.get("graphdb.password")
    # if we want to use a database different from the default
    database: str = settings.get("graphdb.database", neo4j.DEFAULT_DATABASE)

    uns_node_types: tuple = tuple(settings.get(
        "graphdb.uns_node_types", ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE")))

    spb_node_types: tuple = tuple(
        settings.get("graphdb.spB_node_types", ("spBv1_0",
                     "GROUP", "MESSAGE_TYPE", "EDGE_NODE", "DEVICE"))
    )
    nested_attribute_node_type: str = settings.get(
        "graphdb.nested_attribute_node_type", "NESTED_ATTRIBUTE")

    if conn_url is None:
        LOGGER.error(
            "GraphDB Url not provided. Update key 'graphdb.url' in '../../conf/settings.yaml'",
        )

    if (user is None) or (password is None):
        LOGGER.error(
            "GraphDB Username & Password not provided."
            "Update keys 'graphdb.username' and 'graphdb.password' "
            "in '../../conf/.secrets.yaml'"
        )

    @classmethod
    def is_config_valid(cls) -> bool:
        """
        Checks if mandatory configurations were provided
        Does not check if the values provided are correct or not
        """
        return not ((cls.user is None) or (cls.password is None) or cls.conn_url is None)


class HistorianConfig:
    """
    Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'
    """

    hostname: str = settings.get("historian.hostname")
    port: int = settings.get("historian.port", None)
    db_user: str = settings.get("historian.username")
    db_password: str = settings.get("historian.password")

    db_sslmode: str = settings.get("historian.sslmode", None)
    db_sslcert: str = settings.get("historian.sslcert", None)
    db_sslkey: str = settings.get("historian.sslkey", None)
    db_sslrootcert: str = settings.get("historian.sslrootcert", None)
    db_sslcrl: str = settings.get("historian.sslcrl", None)

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
    if (db_user is None) or (db_password is None):
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
            cls.hostname is None or cls.database is None or cls.table is None or cls.db_user is None or cls.db_password is None
        )

    @classmethod
    def get_ssl_context(cls) -> ssl.SSLContext | None:
        """
        Creates the SSL Context needed for DB connect based on the SSL Params
        See https://github.com/MagicStack/asyncpg/issues/737
        """
        if cls.db_sslmode:
            ssl_context: ssl.SSLContext = ssl.create_default_context(
                ssl.Purpose.SERVER_AUTH)
            ssl_context.options |= {
                "disable": ssl.OP_NO_SSLv2,
                "allow": ssl.OP_NO_SSLv3,
                "prefer": ssl.OP_NO_TLSv1,
                "require": ssl.OP_NO_TLSv1_1,
                "verify-ca": ssl.OP_NO_TLSv1_2,
                "verify-full": ssl.OP_NO_TLSv1_3,
            }.get(cls.db_sslmode.lower(), 0)

            if cls.db_sslcert:
                ssl_context.load_cert_chain(
                    certfile=cls.db_sslcert, keyfile=cls.db_sslkey)

            if cls.db_sslrootcert:
                ssl_context.load_verify_locations(cafile=cls.db_sslrootcert)

            if cls.db_sslcrl:
                ssl_context.load_verify_locations(cafile=cls.db_sslcrl)

            return ssl_context
        return None
