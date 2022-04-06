import inspect
import os
import re
import socket
import sys
import pytest

# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            'src')))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)
    sys.path.insert(1, os.path.join(cmd_subfolder, "uns_historian"))
from historian_config import settings


def test_mqtt_config():
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
        None, True, False
    ), f"Invalid value for key 'mqtt.reconnect_on_failure'{reconnect_on_failure}"

    clean_session: bool = settings.get("mqtt.clean_session")
    assert clean_session in (
        True, False,
        None), f"Invalid value for key 'mqtt.clean_session'{clean_session}"

    host: str = settings.mqtt["host"]
    assert host is not None, f"Invalid value for key 'mqtt.host'{host}"

    port: int = settings.get("mqtt.port", 1883)
    assert type(
        port
    ) is int or port is None, f"Invalid value for key 'mqtt.port':{port}"
    assert type(
        port
    ) is int and port >= 1024 and port <= 49151, f"'mqtt.port':{port} must be between 1024 to 49151"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert sock.connect_ex(
        (host, port)) == 0, f"Host: {host} is not reachable at port:{port}"

    username = settings.mqtt["username"]
    password = settings.mqtt["password"]
    assert (username is None and password is None) or (
        type(username) is str and type(password) is str
    ), "Either both username & password need to be specified or neither"

    tls: dict = settings.get("mqtt.tls", None)
    assert (tls is None) or (
        type(tls) is dict and not bool(tls) and tls.get("ca_certs") is not None
    ), "Check the configuration provided for tls connection to the broker. the property ca_certs is missing"

    assert (tls is None) or (os.path.isfile(tls.get(
        "ca_certs"))), f"Unable to find certificate at: {tls.get('ca_certs')}"

    topic: str = settings.get("mqtt.topic", "#")
    REGEX_TO_MATCH_TOPIC = "^(\+|\#|.+/\+|[^#]+#|.*/\+/.*)$"
    assert bool(
        re.fullmatch(REGEX_TO_MATCH_TOPIC, topic)
    ), f"configuration 'mqtt.topic':{topic} is not a valid MQTT topic"

    keep_alive: float = settings.get("mqtt.keep_alive", 60)
    assert (keep_alive is None) or (
        keep_alive >
        0), f"'mqtt.keep_alive'{keep_alive} must be a positive number"

    ignored_attributes: dict = settings.get("mqtt.ignored_attributes")
    assert (ignored_attributes is None) or (
        len(ignored_attributes) > 0
    ), f"Configuration 'mqtt.ignored_attributes':{ignored_attributes} is not a valid dict"

    timestamp_attribute: str = settings.get("mqtt.timestamp_attribute",
                                            "timestamp")
    # Should be a valid JSON attribute
    assert (timestamp_attribute is None) or (
        len(timestamp_attribute) > 0
    ), f"Configuration 'mqtt.timestamp_attribute':{timestamp_attribute} is not a valid JSON key"


def test_timescale_db_configs():
    hostname: str = settings.historian["hostname"]
    port: int = settings.get(
        "historian.port",
        5432)  # if port not provided use default postgres port
    assert hostname is not None, f"Invalid value for key 'historian.hostname'{hostname}"

    assert type(
        port
    ) is int or port is None, f"Invalid value for key 'historian.port':{port}"
    assert type(
        port
    ) is int and port >= 1024 and port <= 49151, f"'historian.port':{port} must be between 1024 to 49151"


    historian_user: str = settings.historian["username"]
    assert (
        historian_user is not None and type(historian_user) is str
        and len(historian_user) > 0
    ), "Invalid username configured at key: 'historian.username'. Cannot be None or empty string"

    historian_password: str = settings.historian["password"]
    assert (
        historian_password is not None and type(historian_password) is str
        and len(historian_password) > 0
    ), "Invalid password configured at key: 'historian.password'. Cannot be None or empty string"

    historian_sslmode: str = settings.get("historian.sslmode")
    assert historian_sslmode in (
        None, "disable", "allow", "prefer", "require", "verify-ca",
        "verify-full"
    ), f"Invalid value for key 'historian.sslmode'{historian_sslmode}"

    historian_database: str = settings.historian["database"]
    assert (
        historian_database is not None and type(historian_database) is str
        and len(historian_database) > 0
    ), f"""Invalid database name configured at key: 'historian.database' value:{historian_database}.
         Cannot be None or empty string"""

    historian_table: str = settings.historian["table"]
    assert (
        historian_table is not None and type(historian_table) is str
        and len(historian_table) > 0
    ), f"""Invalid database name configured at key: 'historian.table' value:{historian_table}.
         Cannot be None or empty string"""
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert sock.connect_ex(
        (hostname,
         port)) == 0, f"Host: {hostname} is not reachable at port:{port}"