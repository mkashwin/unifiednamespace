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

Test cases for uns_graphql_config.
"""

import re
import socket
from pathlib import Path
from urllib.parse import urlparse

import pytest
from aiomqtt import ProtocolVersion
from uns_graphql.graphql_config import GraphDBConfig, HistorianConfig, MQTTConfig, settings

# run these tests only if both configuration files exists or mandatory environment vars are set
is_configs_provided: bool = (
    settings.get("mqtt.host") is not None
    and settings.get("graphdb.url") is not None
    and settings.get("graphdb.username") is not None
    and settings.get("historian.hostname") is not None
    and settings.get("historian.username") is not None
    and settings.get("kafka.config") is not None
    and "bootstrap.servers" in settings.get("kafka.config")
)

# Constant regex expression to match valid MQTT topics
REGEX_TO_MATCH_TOPIC = r"^(\+|\#|.+/\+|[^#]+#|.*/\+/.*)$"

# Constant regex expression to match valid neo4j database url
REGEX_FOR_NEO4J = r"^(bolt|neo4j|bolt\+s|neo4j\+s)[\:][/][/][a-zA-Z0-9.]*[\:]*[0-9]*$"

# Constant regex expression to match valid node types
REGEX_FOR_NODE_TYPES = "^[a-zA-Z0-9_]*$"


@pytest.mark.xfail(not is_configs_provided, reason="Configurations have not been provided")
def test_mqtt_config():
    """
    Test if the mqtt configurations are valid
    """
    assert MQTTConfig.transport in (
        None, "tcp", "websockets"), f"Invalid value for key 'mqtt.transport':{MQTTConfig.transport}"

    assert MQTTConfig.version in {
        item.value for item in ProtocolVersion
    }, f"Invalid value for key 'mqtt.version':{MQTTConfig.version}"

    assert MQTTConfig.qos in (
        None, 0, 1, 2), f"Invalid value for key 'mqtt.qos':{MQTTConfig.qos}"

    # assert MQTTConfig.reconnect_on_failure in (
    #     None,
    #     True,
    #     False,
    # ), f"Invalid value for key 'mqtt.reconnect_on_failure'{MQTTConfig.reconnect_on_failure}"

    assert MQTTConfig.clean_session in (
        True,
        False,
        None,
    ), f"Invalid value for key 'mqtt.clean_session'{MQTTConfig.clean_session}"

    assert MQTTConfig.host is not None, f"Invalid value for key 'mqtt.host'{MQTTConfig.mqtt_host}"

    assert isinstance(
        MQTTConfig.port, int) or MQTTConfig.port is None, f"Invalid value for key 'mqtt.port':{MQTTConfig.port}"
    assert (
        isinstance(
            MQTTConfig.port,
            int,
        )
        and 1024 <= MQTTConfig.port <= 49151
    ), f"'mqtt.port':{MQTTConfig.port} must be between 1024 to 49151"

    assert (MQTTConfig.username is None and MQTTConfig.password is None) or (
        isinstance(MQTTConfig.username, str)
        and len(MQTTConfig.username) > 0
        and isinstance(MQTTConfig.password, str)
        and len(MQTTConfig.password) > 0
    ), "Either both username & password need to be specified or neither"

    assert (MQTTConfig.tls is None) or (
        isinstance(MQTTConfig.tls, dict) and not bool(
            MQTTConfig.tls) and MQTTConfig.tls.get("ca_certs") is not None
    ), "Check the configuration provided for tls connection to the broker. " "the property ca_certs is missing"

    assert (MQTTConfig.tls is None) or (
        Path(MQTTConfig.tls.get("ca_certs")).is_file()
    ), f"Unable to find certificate at: {MQTTConfig.tls.get('ca_certs')}"

    assert (MQTTConfig.keep_alive is None) or (
        MQTTConfig.keep_alive > 0
    ), f"'mqtt.keep_alive'{MQTTConfig.keep_alive} must be a positive number"

    assert MQTTConfig.retry_interval > 0, f"'mqtt.retry_interval'{MQTTConfig.retry_interval} must be a positive number"


@pytest.mark.xfail(not is_configs_provided, reason="Configurations have not been provided")
def test_graph_db_configs():
    """
    Test if the provided configurations for GraphDBHandler are valid and
    """
    # run these tests only if both configuration files exists or mandatory environment vars are set

    assert bool(
        re.fullmatch(REGEX_FOR_NEO4J, GraphDBConfig.conn_url),
    ), f"configuration 'graphdb.url':{GraphDBConfig.conn_url} is not a valid Neo4j URL"

    assert (
        GraphDBConfig.user is not None and isinstance(
            GraphDBConfig.user, str) and len(GraphDBConfig.user) > 0
    ), "Invalid username configured at key: 'graphdb.username'. Cannot be None or empty string"

    assert (
        GraphDBConfig.password is not None and isinstance(
            GraphDBConfig.password, str) and len(GraphDBConfig.password) > 0
    ), "Invalid password configured at key: 'graphdb.password'. Cannot be None or empty string"

    assert GraphDBConfig.uns_node_types is not None and len(GraphDBConfig.uns_node_types) > 0, (
        "Invalid node_types configured at key:'graphdb.uns_node_types'. " "Must be list of length > 1"
    )

    for node_type in GraphDBConfig.uns_node_types:
        assert bool(
            re.fullmatch(REGEX_FOR_NODE_TYPES, node_type),
        ), f"configuration {node_type} in {GraphDBConfig.uns_node_types} is not a valid node name"

    assert GraphDBConfig.spb_node_types is not None and len(GraphDBConfig.spb_node_types) == 5, (
        "Invalid node_types configured at key:'graphdb.spB_node_types'. " "Must be list of length of 5"
    )

    for node_type in GraphDBConfig.spb_node_types:
        assert bool(
            re.fullmatch(REGEX_FOR_NODE_TYPES, node_type),
        ), f"configuration {node_type} in {GraphDBConfig.spb_node_types} is not a valid node name"

    assert re.fullmatch(
        REGEX_FOR_NODE_TYPES,
        GraphDBConfig.nested_attribute_node_type,
    ), f"{GraphDBConfig.nested_attribute_node_type} at key: 'graphdb.nested_attribute_node_type' isn't a valid node name"


@pytest.mark.xfail(not is_configs_provided, reason="Configurations have not been provided")
def test_timescale_db_configs():
    """
    Test if the historian database configurations are valid
    """
    # run these tests only if both configuration files exists or mandatory environment vars are set
    assert HistorianConfig.hostname is not None, f"Invalid value for key 'historian.hostname'{HistorianConfig.hostname}"

    assert HistorianConfig.port is None or not isinstance(
        HistorianConfig.port, int
    ), f"Invalid value for key 'historian.port':{HistorianConfig.port}"

    if HistorianConfig.port is not None:
        assert isinstance(HistorianConfig.port, int) and HistorianConfig.port >= 1024 and HistorianConfig.port <= 49151, (
            f"'historian.port':{HistorianConfig.port} " "must be between 1024 to 49151"
        )

    assert (
        HistorianConfig.db_user is not None and isinstance(
            HistorianConfig.db_user, str) and len(HistorianConfig.db_user) > 0
    ), "Invalid username configured at key: 'historian.username'. Cannot be None or empty string"

    assert (
        HistorianConfig.db_password is not None
        and isinstance(HistorianConfig.db_password, str)
        and len(HistorianConfig.db_password) > 0
    ), "Invalid password configured at key: 'historian.password'. Cannot be None or empty string"

    assert HistorianConfig.db_sslmode in (
        None,
        "disable",
        "allow",
        "prefer",
        "require",
        "verify-ca",
        "verify-full",
    ), f"Invalid value for key 'historian.sslmode'{HistorianConfig.db_sslmode}"

    assert (
        HistorianConfig.db_sslcert is None or Path(
            HistorianConfig.db_sslcert).is_file()
    ), f"Unable to find ssl certificate at: {HistorianConfig.db_sslcert}"
    assert (
        HistorianConfig.db_sslkey is None or Path(
            HistorianConfig.db_sslkey).is_file()
    ), f"Unable to find ssl secret key at: {HistorianConfig.db_sslkey}"

    assert (
        HistorianConfig.db_sslrootcert is None or Path(
            HistorianConfig.db_sslrootcert).is_file()
    ), f"Unable to find ssl certificate authority at: {HistorianConfig.db_sslrootcert}"
    assert (
        HistorianConfig.db_sslcrl is None or Path(
            HistorianConfig.db_sslcrl).is_file()
    ), f"Unable to find ssl certificate revocation list at: {HistorianConfig.db_sslcrl}"

    assert (
        HistorianConfig.database is not None
        and isinstance(HistorianConfig.database, str)
        and len(HistorianConfig.database) > 0
    ), f"""Invalid database name configured at key: 'historian.database' value:{HistorianConfig.database}.
         Cannot be None or empty string"""

    assert (
        HistorianConfig.table is not None and isinstance(
            HistorianConfig.table, str) and len(HistorianConfig.table) > 0
    ), f"""Invalid database name configured at key: 'historian.table' value:{HistorianConfig.table}.
         Cannot be None or empty string"""


@pytest.mark.integrationtest()
def test_connectivity_to_mqtt():
    """
    Test if the provided configurations for the MQTT server are valid and
    there is connectivity to the MQTT broker
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert (
        sock.connect_ex((MQTTConfig.host, MQTTConfig.port)) == 0
    ), f"Host: {MQTTConfig.host} is not reachable at port:{MQTTConfig.port}"


@pytest.mark.integrationtest()
def test_connectivity_to_graphdb():
    """
    Test if the provided configurations to connect to  GraphDB Server are valid and
    there is connectivity to the GraphDB.
    """

    parsed = urlparse(GraphDBConfig.conn_url).netloc.split(":")

    host: str | None = parsed[0]
    port: int = None
    if len(parsed) == 2:
        port: int = int(parsed[1])
    if port is None or port == "":
        port = 7687
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert sock.connect_ex(
        (host, port)) == 0, f"Host: {host} is not reachable at port:{port}"


@pytest.mark.integrationtest()
def test_connectivity_to_historian():
    """
    Test if the provided configurations for the Historian DB Server are valid and
    there is connectivity to the Historian
    """
    hostname: str = HistorianConfig.hostname
    port: int = HistorianConfig.port
    if port is None:
        port = 5432
    # if port not provided use default postgres port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert sock.connect_ex(
        (hostname, port)) == 0, f"Host: {hostname} is not reachable at port:{port}"
