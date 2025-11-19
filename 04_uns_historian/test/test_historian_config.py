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

Test cases for historian_config
"""

import re
import socket
from pathlib import Path

import pytest

from uns_historian.historian_config import HistorianConfig, MQTTConfig, settings

is_configs_provided: bool = (
    settings.get("mqtt.host") is not None
    and settings.get("historian.hostname") is not None
    and settings.get("historian.username") is not None
)

# Constant regex expression to match valid MQTT topics
REGEX_TO_MATCH_TOPIC = (
    r"^(?:(?:(?:(?:(?:(?:[.0-9a-zA-Z_-]+)|(?:\+))(?:\/))*)" r"(?:(?:(?:[.0-9a-zA-Z_-]+)|(?:\+)|(?:\#))))|(?:(?:\#)))$"
)


@pytest.mark.xfail(not is_configs_provided, reason="Configurations have not been provided")
def test_mqtt_config():
    """
    Test if the mqtt configurations are valid
    """
    # run these tests only if both configuration files exists or mandatory environment vars are set

    assert MQTTConfig.transport in (
        "tcp", "websockets"), f"Invalid value for key 'mqtt.transport':{MQTTConfig.transport}"

    assert MQTTConfig.version in (
        3, 4, 5), f"Invalid value for key 'mqtt.version':{MQTTConfig.version}"

    assert MQTTConfig.qos in (
        0, 1, 2), f"Invalid value for key 'mqtt.qos':{MQTTConfig.qos}"

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

    assert MQTTConfig.port is not None and isinstance(
        MQTTConfig.port, int
    ), f"Invalid value for key 'mqtt.port':{MQTTConfig.port}"

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

    for topic in MQTTConfig.topics:
        assert bool(
            re.fullmatch(REGEX_TO_MATCH_TOPIC, topic),
        ), f"configuration 'mqtt.topics':{MQTTConfig.topics} has an valid MQTT topic topic:{topic}"

    assert MQTTConfig.keepalive > 0, f"'mqtt.keep_alive'{MQTTConfig.keepalive} must be a positive number"

    assert (MQTTConfig.ignored_attributes is None) or (
        isinstance(MQTTConfig.ignored_attributes, dict)
    ), f"Configuration 'mqtt.ignored_attributes':{MQTTConfig.ignored_attributes} is not a valid dict"

    # Should be a valid JSON attribute
    assert (MQTTConfig.timestamp_key is None) or (
        len(MQTTConfig.timestamp_key) > 0
    ), f"Configuration 'mqtt.timestamp_attribute':{MQTTConfig.timestamp_key} is not a valid JSON key"


@pytest.mark.xfail(not is_configs_provided, reason="Configurations have not been provided")
def test_timescale_db_configs():
    """
    Test if the historian database configurations are valid
    """
    # run these tests only if both configuration files exists or mandatory environment vars are set

    assert HistorianConfig.hostname is not None, f"Invalid value for key 'historian.hostname'{HistorianConfig.hostname}"

    assert (
        isinstance(HistorianConfig.port, int) or HistorianConfig.port is None
    ), f"Invalid value for key 'historian.port':{HistorianConfig.port}"

    if isinstance(HistorianConfig.port, int):
        assert (
            isinstance(HistorianConfig.port,
                       int) and 1024 >= HistorianConfig.port <= 49151
        ), f"'historian.port':{HistorianConfig.port} must be between 1024 to 49151"

    assert (
        HistorianConfig.user is not None and isinstance(
            HistorianConfig.user, str) and len(HistorianConfig.user) > 0
    ), "Invalid username configured at key: 'historian.username'. Cannot be None or empty string"

    assert (
        HistorianConfig.password is not None
        and isinstance(HistorianConfig.password, str)
        and len(HistorianConfig.password) > 0
    ), "Invalid password configured at key: 'historian.password'. Cannot be None or empty string"

    assert HistorianConfig.sslmode in (
        None,
        "disable",
        "allow",
        "prefer",
        "require",
        "verify-ca",
        "verify-full",
    ), f"Invalid value for key 'historian.sslmode'{HistorianConfig.sslmode}"

    assert (
        HistorianConfig.sslcert is None or Path(
            HistorianConfig.sslcert).is_file()
    ), f"Unable to find ssl certificate at: {HistorianConfig.sslcert}"
    assert (
        HistorianConfig.sslkey is None or Path(
            HistorianConfig.sslkey).is_file()
    ), f"Unable to find ssl secret key at: {HistorianConfig.sslkey}"

    assert (
        HistorianConfig.sslrootcert is None or Path(
            HistorianConfig.sslrootcert).is_file()
    ), f"Unable to find ssl certificate authority at: {HistorianConfig.sslrootcert}"
    assert (
        HistorianConfig.sslcrl is None or Path(
            HistorianConfig.sslcrl).is_file()
    ), f"Unable to find ssl certificate revocation list at: {HistorianConfig.sslcrl}"

    assert (
        HistorianConfig.database is not None
        and isinstance(HistorianConfig.database, str)
        and len(HistorianConfig.database) > 0
    ), f"""Invalid database name configured at key: 'historian.database' value:{HistorianConfig.database}.
         Cannot be None or empty string"""

    assert (
        HistorianConfig.table is not None and isinstance(
            HistorianConfig.table, str) and len(HistorianConfig.table) > 0
    ), f"""Invalid database name configured at key: 'historian.table' value:{HistorianConfig.able}.
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
def test_connectivity_to_historian():
    """
    Test if the provided configurations for the Historian DB Server are valid and
    there is connectivity to the Historian
    """
    # if port not provided use default postgres port 5432)
    port = HistorianConfig.port
    if port is None:
        port = 5432
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert (
        sock.connect_ex((HistorianConfig.hostname, port)) == 0
    ), f"Host: {HistorianConfig.hostname} is not reachable at port:{port}"
