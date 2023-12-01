"""
Test cases for sparkplugb_enc_config
"""
import re
import socket
from pathlib import Path

import pytest
from uns_mqtt.mqtt_listener import UnsMQTTClient
from uns_spb_mapper.sparkplugb_enc_config import MQTTConfig, settings

is_configs_provided: bool = settings.get("mqtt.host") is not None

# Constant regex expression to match valid MQTT topics
REGEX_TO_MATCH_TOPIC = r"^(\+|\#|.+/\+|[^#]+#|.*/\+/.*)$"


@pytest.mark.xfail(not is_configs_provided,
                   reason="Configurations have not been provided")
def test_mqtt_config():
    """
    Test if the mqtt configurations are valid
    """
    # run these tests only if both configuration files exists or mandatory environment vars are set

    assert MQTTConfig.transport in (
        "tcp",
        "ws"), f"Invalid value for key 'mqtt.transport':{MQTTConfig.transport}"

    assert MQTTConfig.version_code in (
        UnsMQTTClient.MQTTv31, UnsMQTTClient.MQTTv311, UnsMQTTClient.MQTTv5
    ), f"Invalid value for key 'mqtt.version':{MQTTConfig.version_code}"

    assert MQTTConfig.qos in (
        0, 1, 2), f"Invalid value for key 'mqtt.qos':{MQTTConfig.qos}"

    assert MQTTConfig.reconnect_on_failure in (
        True,
        False,
    ), f"Invalid value for key 'mqtt.reconnect_on_failure'{MQTTConfig.reconnect_on_failure}"

    assert MQTTConfig.clean_session in (
        None, True, False
    ), f"Invalid value for key 'mqtt.clean_session'{MQTTConfig.clean_session}"

    assert MQTTConfig.host is not None, f"Invalid value for key 'mqtt.host'{MQTTConfig.host}"

    assert MQTTConfig.port is not None and isinstance(
        MQTTConfig.port,
        int), f"Invalid value for key 'mqtt.port':{MQTTConfig.port}"
    assert 1024 <= MQTTConfig.port <= 49151, f"'mqtt.port':{MQTTConfig.port} must be between 1024 to 49151"

    assert (MQTTConfig.username is None and MQTTConfig.password is None) or (
        isinstance(MQTTConfig.username, str) and len(MQTTConfig.username) > 0
        and isinstance(MQTTConfig.password, str) and len(MQTTConfig.password)
        > 0), "Either both username & password need to be specified or neither"

    assert (MQTTConfig.tls is None) or (
        isinstance(MQTTConfig.tls, dict) and not bool(MQTTConfig.tls)
        and MQTTConfig.tls.get("ca_certs") is not None
    ), ("Check the configuration provided for tls connection to the broker."
        "The property ca_certs is missing")

    assert (MQTTConfig.tls is None) or (Path(
        MQTTConfig.tls.get("ca_certs")).is_file(
        )), f"Unable to find certificate at: {MQTTConfig.tls.get('ca_certs')}"

    for topic in MQTTConfig.topics:
        assert bool(
            re.fullmatch(REGEX_TO_MATCH_TOPIC, topic),
        ), f"configuration 'mqtt.topics':{MQTTConfig.topics} has an invalid MQTT topic topic:{topic}"
        assert topic.startswith(
            UnsMQTTClient.SPARKPLUG_NS
        ), f"topic:{topic} is not a SparkplugB namespace"

    assert (MQTTConfig.keepalive is not None) and (
        MQTTConfig.keepalive > 0
    ), f"'mqtt.keep_alive'{MQTTConfig.keepalive} must be a positive number"

    assert (MQTTConfig.ignored_attributes is None) or (
        isinstance(MQTTConfig.ignored_attributes, dict)
    ), f"Configuration 'mqtt.ignored_attributes':{MQTTConfig.ignored_attributes} is not a valid dict"

    # Should be a valid JSON key name
    assert (isinstance(MQTTConfig.timestamp_key, str)) and (
        len(MQTTConfig.timestamp_key) > 0
    ), f"Configuration 'mqtt.timestamp_attribute':{MQTTConfig.timestamp_key } is not a valid JSON key"


@pytest.mark.integrationtest()
def test_connectivity_to_mqtt():
    """
    Test if the provided configurations for the MQTT server are valid and
    there is connectivity to the MQTT broker
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert sock.connect_ex(
        (MQTTConfig.host, MQTTConfig.port)
    ) == 0, f"Host: {MQTTConfig.host} is not reachable at port:{MQTTConfig.port}"
