"""
Configuration reader for mqtt server and Neo4J DB server details
"""
import logging
from pathlib import Path
from typing import Literal, Optional

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

    transport: Literal["tcp", "websockets"] = settings.get("mqtt.transport", "tcp")
    version: ProtocolVersion = ProtocolVersion(settings.get("mqtt.version", ProtocolVersion.V5))
    properties: Properties = Properties(PacketTypes.CONNECT) if version == ProtocolVersion.V5 else None
    qos: Literal[0, 1, 2] = settings.get("mqtt.qos", 1)
    clean_session: Optional[bool] = settings.get("mqtt.clean_session", None)

    host: str = settings.get("mqtt.host")
    port: int = settings.get("mqtt.port", 1883)
    username: Optional[str] = settings.get("mqtt.username")
    password: Optional[str] = settings.get("mqtt.password")
    tls: Optional[dict] = settings.get("mqtt.tls", None)

    tls_params: Optional[TLSParameters] = (
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

    tls_insecure: Optional[bool] = tls.get("insecure_cert") if tls is not None else None

    keep_alive: int = settings.get("mqtt.keep_alive", 60)
    retry_interval: int = settings.get("mqtt.retry_interval", 10)
    mqtt_timestamp_key = settings.get("mqtt.timestamp_attribute", "timestamp")
    if host is None:
        LOGGER.error(
            "MQTT Host not provided. Update key 'mqtt.host' in '../../conf/settings.yaml'",
        )

    def is_config_valid(self) -> bool:
        """
        Checks if mandatory configurations were provided
        Does not check if the values provided are correct or not
        """
        return self.host is not None


class GraphDBConfig:
    """
    Loads the configurations from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'"
    """

    conn_url: str = settings.get("graphdb.url")
    user: str = settings.get("graphdb.username")

    password: str = settings.get("graphdb.password")
    # if we want to use a database different from the default
    database: str = settings.get("graphdb.database", None)

    uns_node_types: tuple = tuple(settings.get("graphdb.uns_node_types", ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE")))

    spb_node_types: tuple = tuple(
        settings.get("graphdb.spB_node_types", ("spBv1_0", "GROUP", "MESSAGE_TYPE", "EDGE_NODE", "DEVICE"))
    )
    nested_attribute_node_type: str = settings.get("graphdb.nested_attribute_node_type", "NESTED_ATTRIBUTE")

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

    def is_config_valid(self) -> bool:
        """
        Checks if mandatory configurations were provided
        Does not check if the values provided are correct or not
        """
        return not ((self.user is None) or (self.password is None) or self.conn_url is None)


class KAFKAConfig:
    """
    Read the Kafka configurations required to connect to the Kafka broker
    from '../../conf/settings.yaml' and '../../conf/.secrets.yaml'
    """

    config_map: dict = settings.get("kafka.config")
    consumer_poll_timeout: float = float(settings.get("kafka.consumer_timeout", 1.0))


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

    def is_config_valid(self) -> bool:
        """
        Checks if mandatory configurations were provided
        Does not check if the values provided are correct or not
        """
        return not (
            self.hostname is None
            or self.database is None
            or self.table is None
            or self.db_user is None
            or self.db_password is None
        )


# The regex matches any of the following patterns:
#   - A single-level wildcard (+)
#   - A multi-level wildcard (#)
#   - A literal string followed by a single-level wildcard (literal/+)
#   - A literal string followed by a multi-level wildcard (literal/#)
#   - A literal string followed by a single-level wildcard, followed by another literal string and
#     another single-level wildcard (literal/+literal/+)
# REGEX_FOR_MQTT_TOPIC = r"^(\+|\#|.+/\+|[^#]+#|.*/\+/.*)$"
REGEX_FOR_MQTT_TOPIC = (
    r"^(?:(?:(?:(?:(?:(?:[.0-9a-zA-Z_-]+)|(?:\+))(?:\/))*)" r"(?:(?:(?:[.0-9a-zA-Z_-]+)|(?:\+)|(?:\#))))|(?:(?:\#)))$"
)

# This regex matches the following:
#   - Topic names: A string consisting of alphanumeric characters, hyphens, and periods.
# TODO add support for wildcards or RegEx
REGEX_FOR_KAFKA_TOPIC = r"^[a-zA-Z0-9._-]+$"
