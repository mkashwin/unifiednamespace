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

Test cases for graphdb_config
"""

import re
import socket
from pathlib import Path
from urllib.parse import urlparse

import pytest

from uns_graphdb.graphdb_config import GraphDBConfig, MQTTConfig, settings

is_configs_provided: bool = (
    settings.get("graphdb.url") is not None
    and settings.get("graphdb.username") is not None
    and settings.get("mqtt.host") is not None
)

# Constant regex expression to match valid MQTT topics
REGEX_TO_MATCH_TOPIC = (
    r"^(?:(?:(?:(?:(?:(?:[.0-9a-zA-Z_-]+)|(?:\+))(?:\/))*)" r"(?:(?:(?:[.0-9a-zA-Z_-]+)|(?:\+)|(?:\#))))|(?:(?:\#)))$"
)

# Constant regex expression to match valid neo4j database url
REGEX_FOR_NEO4J = r"^(bolt|neo4j|bolt\+s|neo4j\+s)[\:][/][/][a-zA-Z0-9.]*[\:]*[0-9]*$"

# Constant regex expression to match valid node types
REGEX_FOR_NODE_TYPES = "^[a-zA-Z0-9_]*$"


@pytest.mark.xfail(not is_configs_provided, reason="Configurations have not been provided")
def test_mqtt_config():
    """
    Test if the mqtt configurations are valid
    """
    # run these tests only if both configuration files exists or mandatory environment vars are set

    assert MQTTConfig.transport in (None, "tcp", "ws"), f"Invalid value for key 'mqtt.transport':{MQTTConfig.transport}"

    assert MQTTConfig.version in (None, 3, 4, 5), f"Invalid value for key 'mqtt.version':{MQTTConfig.version}"

    assert MQTTConfig.qos in (0, 1, 2), f"Invalid value for key 'mqtt.qos':{MQTTConfig.qos}"

    assert MQTTConfig.reconnect_on_failure in (
        True,
        False,
    ), f"Invalid value for key 'mqtt.reconnect_on_failure'{MQTTConfig.reconnect_on_failure}"

    assert MQTTConfig.clean_session in (
        True,
        False,
        None,
    ), f"Invalid value for key 'mqtt.clean_session'{MQTTConfig.clean_session}"

    assert MQTTConfig.host is not None, f"Invalid value for key 'mqtt.host'{MQTTConfig.host}"

    assert isinstance(MQTTConfig.port, int) or MQTTConfig.port is None, f"Invalid value for key 'mqtt.port':{MQTTConfig.port}"
    assert 1024 <= MQTTConfig.port <= 49151, f"'mqtt.port':{MQTTConfig.port} must be between 1024 to 49151"

    assert (MQTTConfig.username is None and MQTTConfig.password is None) or (
        isinstance(MQTTConfig.username, str)
        and len(MQTTConfig.username) > 0
        and isinstance(MQTTConfig.password, str)
        and len(MQTTConfig.password) > 0
    ), "Either both username & password need to be specified or neither"

    assert (MQTTConfig.tls is None) or (
        isinstance(MQTTConfig.tls, dict) and not bool(MQTTConfig.tls) and MQTTConfig.tls.get("ca_certs") is not None
    ), "Check the configuration provided for tls connection to the broker. " "The property ca_certs is missing"

    assert (MQTTConfig.tls is None) or (
        Path(MQTTConfig.tls.get("ca_certs")).is_file()
    ), f"Unable to find certificate at: {MQTTConfig.tls.get('ca_certs')}"

    assert len(MQTTConfig.topics) > 1, f"configuration 'mqtt.topics':{MQTTConfig.topics} must have at least 1 topic"

    for topic in MQTTConfig.topics:
        assert bool(
            re.fullmatch(REGEX_TO_MATCH_TOPIC, topic),
        ), f"configuration 'mqtt.topics':{MQTTConfig.topics} has an invalid MQTT topic:{topic}"

    assert (isinstance(MQTTConfig.keepalive, int)) and (
        MQTTConfig.keepalive > 0
    ), f"'mqtt.keep_alive'{MQTTConfig.keepalive} must be a positive number"

    assert (MQTTConfig.ignored_attributes is None) or (
        isinstance(MQTTConfig.ignored_attributes, dict)
    ), f"Configuration 'mqtt.ignored_attributes':{MQTTConfig.ignored_attributes} is not a valid dict"

    # Should be a valid JSON attribute
    assert (isinstance(MQTTConfig.timestamp_key, str)) and (
        len(MQTTConfig.timestamp_key) > 0
    ), f"Configuration 'mqtt.timestamp_attribute':{MQTTConfig.timestamp_key} is not a valid JSON key"


@pytest.mark.xfail(not is_configs_provided, reason="Configurations have not been provided")
def test_graph_db_configs():
    """
    Test if the provided configurations for GraphDBHandler are valid and
    """
    # run these tests only if both configuration files exists or mandatory environment vars are set

    assert bool(
        re.fullmatch(REGEX_FOR_NEO4J, GraphDBConfig.db_url),
    ), f"configuration 'graphdb.url':{GraphDBConfig.db_url} is not a valid Neo4j URL"

    assert (
        GraphDBConfig.user is not None and isinstance(GraphDBConfig.user, str) and len(GraphDBConfig.user) > 0
    ), "Invalid username configured at key: 'graphdb.username'. Cannot be None or empty string"

    assert (
        GraphDBConfig.password is not None and isinstance(GraphDBConfig.password, str) and len(GraphDBConfig.password) > 0
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
        GraphDBConfig.nested_attributes_node_type,
    ), f"{GraphDBConfig.nested_attributes_node_type} at key: 'graphdb.nested_attribute_node_type' isn't a valid node name"


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
    there is connectivity to the GraphDB
    """
    graphdb_url: str = GraphDBConfig.db_url
    parsed = urlparse(graphdb_url).netloc.split(":")

    host: str = parsed[0]
    port: int = None
    if len(parsed) == 2:
        port: int = int(parsed[1])
    if port is None or port == "":
        port = 7687
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert sock.connect_ex((host, port)) == 0, f"Host: {host} is not reachable at port:{port}"
