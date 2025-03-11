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

Test cases for uns_kafka_config
"""

import re
import socket
from pathlib import Path

import pytest
from confluent_kafka import Producer

from uns_kafka.uns_kafka_config import settings

is_configs_provided: bool = settings.get("kafka.config") is not None and "bootstrap.servers" in settings.get("kafka.config")

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
    mqtt_transport: str | None = settings.get("mqtt.transport")
    assert mqtt_transport in (None, "tcp", "ws"), f"Invalid value for key 'mqtt.transport':{mqtt_transport}"

    mqtt_version: int = settings.get("mqtt.version")
    assert mqtt_version in (None, 3, 4, 5), f"Invalid value for key 'mqtt.version':{mqtt_version}"

    mqtt_qos: int = settings.get("mqtt.qos")
    assert mqtt_qos in (None, 0, 1, 2), f"Invalid value for key 'mqtt.qos':{mqtt_qos}"

    reconnect_on_failure: bool = settings.get("mqtt.reconnect_on_failure")
    assert reconnect_on_failure in (
        None,
        True,
        False,
    ), f"Invalid value for key 'mqtt.reconnect_on_failure'{reconnect_on_failure}"

    clean_session: bool = settings.get("mqtt.clean_session")
    assert clean_session in (True, False, None), f"Invalid value for key 'mqtt.clean_session'{clean_session}"

    host: str | None = settings.get("mqtt.host")
    assert host is not None, f"Invalid value for key 'mqtt.host'{host}"

    port: int = settings.get("mqtt.port", 1883)
    assert isinstance(port, int) or port is None, f"Invalid value for key 'mqtt.port':{port}"
    assert (
        isinstance(
            port,
            int,
        )
        and 1024 <= port <= 49151
    ), f"'mqtt.port':{port} must be between 1024 to 49151"

    username = settings.get("mqtt.username")
    password = settings.get("mqtt.password")
    assert (username is None and password is None) or (
        isinstance(username, str) and len(username) > 0 and isinstance(password, str) and len(password) > 0
    ), "Either both username & password need to be specified or neither"

    assert (username is None and password is None) or (
        isinstance(username, str) and len(username) > 0 and isinstance(password, str) and len(password) > 0
    ), "Either both username & password need to be specified or neither"

    tls: dict = settings.get("mqtt.tls", None)
    assert (tls is None) or (isinstance(tls, dict) and not bool(tls) and tls.get("ca_certs") is not None), (
        "Check the configuration provided for tls connection to the broker. " "the property ca_certs is missing"
    )

    assert (tls is None) or (Path(tls.get("ca_certs")).is_file()), f"Unable to find certificate at: {tls.get('ca_certs')}"

    topics: list[str] = settings.get("mqtt.topics", ["#"])
    for topic in topics:
        assert bool(
            re.fullmatch(REGEX_TO_MATCH_TOPIC, topic),
        ), f"configuration 'mqtt.topics':{topics} has an valid MQTT topic topic:{topic}"

    keep_alive: float = settings.get("mqtt.keep_alive", 60)
    assert (keep_alive is None) or (keep_alive > 0), f"'mqtt.keep_alive'{keep_alive} must be a positive number"

    ignored_attributes: dict = settings.get("mqtt.ignored_attributes")
    assert (ignored_attributes is None) or (
        isinstance(ignored_attributes, dict)
    ), f"Configuration 'mqtt.ignored_attributes':{ignored_attributes} is not a valid dict"

    timestamp_attribute: str | None = settings.get("mqtt.timestamp_attribute", "timestamp")
    # Should be a valid JSON attribute
    assert (timestamp_attribute is None) or (
        len(timestamp_attribute) > 0
    ), f"Configuration 'mqtt.timestamp_attribute':{timestamp_attribute} is not a valid JSON key"


@pytest.mark.xfail(not is_configs_provided, reason="Configurations have not been provided")
def test_kafka_config():
    """
    Test if the Kafka configurations are valid
    """
    config: dict = settings.get("kafka.config")

    assert "client.id" in config, f"Kafka configurations missing mandatory client.id: {config}"

    assert ("bootstrap.servers" in config) or (
        "metadata.broker.list" in config
    ), f"Kafka configurations missing mandatory server config: {config}"

    # assert "group.id" in config, f"Kafka configurations missing mandatory server config: {config}"


@pytest.mark.integrationtest()
def test_connectivity_to_mqtt():
    """
    Test if the provided configurations for the MQTT server are valid and
    there is connectivity to the MQTT broker
    """
    host: str | None = settings.get("mqtt.host")
    port: int = settings.get("mqtt.port", 1883)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert sock.connect_ex((host, port)) == 0, f"Host: {host} is not reachable at port:{port}"


@pytest.mark.integrationtest()
def test_connectivity_to_kafka():
    """
    Test if the provided configurations for the Kafka Server are valid and
    there is connectivity to the Kafka cluster
    """
    config: dict = settings.get("kafka.config")

    producer = Producer(config)
    assert producer is not None, f"Kafka configurations did not create a valid kafka producer: {config}"
    assert (
        producer.list_topics(
            timeout=10,
        )
        is not None
    ), f"Kafka configurations did allow connectivity to broker: {config}"
