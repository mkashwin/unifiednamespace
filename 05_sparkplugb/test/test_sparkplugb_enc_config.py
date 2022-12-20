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
    sys.path.insert(1, os.path.join(cmd_subfolder, "uns_sparkplugb"))
from sparkplugb_enc_config import settings

is_configs_provided: bool = (
    os.path.exists(os.path.join(cmd_subfolder, "../conf/.secrets.yaml"))
    and os.path.exists(os.path.join(cmd_subfolder, "../conf/settings.yaml"))
    or (bool(os.getenv("UNS_mqtt.host"))))


@pytest.mark.xfail(not is_configs_provided,
                   reason="Configurations have not been provided")
def test_mqtt_config():
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
        None, True, False
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
        int) or port is None, f"Invalid value for key 'mqtt.port':{str(port)}"
    assert isinstance(
        port, int
    ) and port >= 1024 and port <= 49151, f"'mqtt.port':{str(port)} must be between 1024 to 49151"

    username = settings.mqtt["username"]
    password = settings.mqtt["password"]
    assert (username is None and password is None) or (
        isinstance(username, str) and len(username) > 0
        and isinstance(password, str) and len(password) > 0
    ), "Either both username & password need to be specified or neither"

    tls: dict = settings.get("mqtt.tls", None)
    assert (tls is None) or (
        isinstance(tls, dict) and not bool(tls)
        and tls.get("ca_certs") is not None
    ), "Check the configuration provided for tls connection to the broker. the property ca_certs is missing"

    assert (tls is None) or (os.path.isfile(tls.get(
        "ca_certs"))), f"Unable to find certificate at: {tls.get('ca_certs')}"

    topics: str = settings.get("mqtt.topics", ["#"])
    REGEX_TO_MATCH_TOPIC = r"^(\+|\#|.+/\+|[^#]+#|.*/\+/.*)$"
    for topic in topics:
        assert bool(
            re.fullmatch(REGEX_TO_MATCH_TOPIC, topic)
        ), f"configuration 'mqtt.topic':{topic} is not a valid MQTT topic"

    keep_alive: float = settings.get("mqtt.keep_alive", 60)
    assert (keep_alive is None) or (
        keep_alive >
        0), f"'mqtt.keep_alive'{keep_alive} must be a positive number"

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


@pytest.mark.integrationtest
@pytest.mark.xfail(
    not is_configs_provided,
    reason="Configurations absent, or these are not integration tests")
def test_connectivity_to_mqtt():
    host: str = settings.mqtt["host"]
    port: int = settings.get("mqtt.port", 1883)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert sock.connect_ex(
        (host,
         port)) == 0, f"Host: {host} is not reachable at port:{str(port)}"
