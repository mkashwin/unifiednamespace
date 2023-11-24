"""
Test cases for graphdb_config
"""
import inspect
import os
import re
import socket
from urllib.parse import urlparse

import pytest
from uns_graphdb.graphdb_config import settings

cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], "..",
            "src")))

is_configs_provided: bool = (os.path.exists(
    os.path.join(cmd_subfolder, "../conf/.secrets.yaml")) and os.path.exists(
        os.path.join(cmd_subfolder, "../conf/settings.yaml"))) or (bool(
            os.getenv("UNS_graphdb__username")))

# Constant regex expression to match valid MQTT topics
REGEX_TO_MATCH_TOPIC = r"^(\+|\#|.+/\+|[^#]+#|.*/\+/.*)$"

# Constant regex expression to match valid neo4j database url
REGEX_FOR_NEO4J = r"^(bolt|neo4j|bolt\+s|neo4j\+s)[\:][/][/][a-zA-Z0-9.]*[\:]*[0-9]*$"

# Constant regex expression to match valid node types
REGEX_FOR_NODE_TYPES = "^[a-zA-Z0-9_]*$"


@pytest.mark.xfail(not is_configs_provided,
                   reason="Configurations have not been provided")
def test_mqtt_config():
    """
    Test if the mqtt configurations are valid
    """
    # run these tests only if both configuration files exists or mandatory environment vars are set
    mqtt_transport: str = settings.get("mqtt.transport")
    assert mqtt_transport in (
        None, "tcp",
        "ws"), f"Invalid value for key 'mqtt.transport':{mqtt_transport}"

    mqtt_version: int = settings.get("mqtt.version")
    assert mqtt_version in (
        None, 3, 4, 5), f"Invalid value for key 'mqtt.version':{mqtt_version}"

    mqtt_qos: int = settings.get("mqtt.qos")
    assert mqtt_qos in (None, 0, 1,
                        2), f"Invalid value for key 'mqtt.qos':{mqtt_qos}"

    reconnect_on_failure: bool = settings.get("mqtt.reconnect_on_failure")
    assert reconnect_on_failure in (
        None,
        True,
        False,
    ), f"Invalid value for key 'mqtt.reconnect_on_failure'{reconnect_on_failure}"

    clean_session: bool = settings.get("mqtt.clean_session")
    assert clean_session in (
        True, False,
        None), f"Invalid value for key 'mqtt.clean_session'{clean_session}"

    host: str = settings.mqtt["host"]
    assert host is not None, f"Invalid value for key 'mqtt.host'{host}"

    port: int = settings.get("mqtt.port", 1883)
    assert isinstance(
        port,
        int) or port is None, f"Invalid value for key 'mqtt.port':{port!s}"
    assert isinstance(
        port,
        int,
    ) and 1024 <= port <= 49151, f"'mqtt.port':{port!s} must be between 1024 to 49151"

    username = settings.get("mqtt.username")
    password = settings.get("mqtt.password")
    assert (username is None and password is None) or (
        isinstance(username, str) and len(username) > 0
        and isinstance(password, str) and len(password)
        > 0), "Either both username & password need to be specified or neither"

    tls: dict = settings.get("mqtt.tls", None)
    assert (tls is None) or (
        isinstance(tls, dict) and not bool(tls)
        and tls.get("ca_certs") is not None
    ), ("Check the configuration provided for tls connection to the broker. "
        "The property ca_certs is missing")

    assert (tls is None) or (os.path.isfile(tls.get(
        "ca_certs"))), f"Unable to find certificate at: {tls.get('ca_certs')}"

    topics: str = settings.get("mqtt.topics", ["#"])
    for topic in topics:
        assert bool(
            re.fullmatch(REGEX_TO_MATCH_TOPIC, topic),
        ), f"configuration 'mqtt.topics':{topics} has an valid MQTT topic topic:{topic}"

    keep_alive: float = settings.get("mqtt.keep_alive", 60)
    assert (keep_alive is None) or (
        keep_alive
        > 0), f"'mqtt.keep_alive'{keep_alive} must be a positive number"

    ignored_attributes: dict = settings.get("mqtt.ignored_attributes")
    assert (ignored_attributes is None) or (
        isinstance(ignored_attributes, dict)
    ), f"Configuration 'mqtt.ignored_attributes':{ignored_attributes} is not a valid dict"

    timestamp_attribute: str = settings.get("mqtt.timestamp_attribute",
                                            "timestamp")
    # Should be a valid JSON attribute
    assert (timestamp_attribute is None) or (
        len(timestamp_attribute) > 0
    ), f"Configuration 'mqtt.timestamp_attribute':{timestamp_attribute} is not a valid JSON key"


@pytest.mark.xfail(not is_configs_provided,
                   reason="Configurations have not been provided")
def test_graph_db_configs():
    """
    Test if the provided configurations for GraphDBHandler are valid and
    """
    # run these tests only if both configuration files exists or mandatory environment vars are set
    graphdb_url: str = settings.graphdb["url"]

    assert bool(
        re.fullmatch(REGEX_FOR_NEO4J, graphdb_url),
    ), f"configuration 'graphdb.url':{graphdb_url} is not a valid Neo4j URL"

    graphdb_user: str = settings.graphdb["username"]
    assert (
        graphdb_user is not None and isinstance(graphdb_user, str)
        and len(graphdb_user) > 0
    ), "Invalid username configured at key: 'graphdb.username'. Cannot be None or empty string"

    graphdb_password: str = settings.graphdb["password"]
    assert (
        graphdb_password is not None and isinstance(graphdb_password, str)
        and len(graphdb_password) > 0
    ), "Invalid password configured at key: 'graphdb.password'. Cannot be None or empty string"

    node_types: tuple = settings.get(
        "graphdb.uns_node_types",
        ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE"))
    assert node_types is not None and len(node_types) > 0, (
        "Invalid node_types configured at key:'graphdb.uns_node_types'. "
        "Must be list of length > 1")

    spb_node_types: tuple = settings.get(
        "graphdb.spB_node_types",
        ("spBv1_0", "GROUP", "MESSAGE_TYPE", "EDGE_NODE", "DEVICE"))
    assert spb_node_types is not None and len(spb_node_types) == 5, (
        "Invalid node_types configured at key:'graphdb.spB_node_types'. "
        "Must be list of length of 5")

    for node_type in node_types:
        assert bool(
            re.fullmatch(REGEX_FOR_NODE_TYPES, node_type),
        ), f"configuration {node_type} in {node_types} is not a valid node name"

    nested_attribute_node_type = settings.get(
        "graphdb.nested_attribute_node_type", "NESTED_ATTRIBUTE")
    assert re.fullmatch(
        REGEX_FOR_NODE_TYPES,
        nested_attribute_node_type,
    ), f"{nested_attribute_node_type} at key: 'graphdb.nested_attribute_node_type' isn't a valid node name"


@pytest.mark.integrationtest()
def test_connectivity_to_mqtt():
    """
    Test if the provided configurations for the MQTT server are valid and
    there is connectivity to the MQTT broker
    """
    host: str = settings.mqtt["host"]
    port: int = settings.get("mqtt.port", 1883)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert sock.connect_ex(
        (host, port)) == 0, f"Host: {host} is not reachable at port:{port!s}"


@pytest.mark.integrationtest()
def test_connectivity_to_graphdb():
    """
    Test if the provided configurations to connect to  GraphDB Server are valid and
    there is connectivity to the GraphDB
    """
    graphdb_url: str = settings.graphdb["url"]
    parsed = urlparse(graphdb_url).netloc.split(":")

    host: str = parsed[0]
    port: int = None
    if len(parsed) == 2:
        port: int = int(parsed[1])
    if port is None or port == "":
        port = 7687
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert sock.connect_ex(
        (host, port)) == 0, f"Host: {host} is not reachable at port:{port!s}"
