import inspect
import os
import sys
import time
import pytest

# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            'src')))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)
    sys.path.insert(1, os.path.join(cmd_subfolder,"uns_mqtt"))
from uns_mqtt.mqtt_listener import Uns_MQTT_ClientWrapper

EMQX_HOST = "broker.emqx.io"  # test the client against the hosted emqx broker
EMQX_CERT_FILE = os.path.join(
    os.path.split(inspect.getfile(inspect.currentframe()))[0], 'cert',
    'broker.emqx.io-ca.crt')

MOSQUITTO_HOST = "test.mosquitto.org"  # test the client against the hosted mosquitto broker
# See https://test.mosquitto.org/
MOSQUITTO_CERT_FILE = os.path.join(
    os.path.split(inspect.getfile(inspect.currentframe()))[0], 'cert',
    'mosquitto.org.crt')

DEFAULT_TOPIC = "test/uns/#"  # used to reduce load on the hosted broker
KEEP_ALIVE = 60


@pytest.mark.parametrize("protocol", [(Uns_MQTT_ClientWrapper.MQTTv5),
                                      (Uns_MQTT_ClientWrapper.MQTTv311)])
#                                     (UNS_MQTT_Listener.MQTTv31)])
## There appears to be a bug for MQTTv31. The call backs are not occuring
@pytest.mark.parametrize("transport,port,tls", [("tcp", 1883, None),
                                                ("websockets", 8083, None),
                                                ("tcp", 8883, {
                                                    "ca_certs": EMQX_CERT_FILE
                                                }),
                                                ("websockets", 8084, {
                                                    "ca_certs": EMQX_CERT_FILE
                                                })])
@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("reconnect_on_failure", [(True), (False)])
@pytest.mark.parametrize("qos", [(0), (1), (2)])
def test_01_unauthenticated_connections(clean_session, protocol, transport,
                                        port, reconnect_on_failure, tls, qos):
    """
    Test all the parameters ( except username password against EMQX's hosted broker instance)
    """
    uns_client = Uns_MQTT_ClientWrapper(f"test_01_{protocol}",
                                   clean_session=clean_session,
                                   protocol=protocol,
                                   transport=transport,
                                   reconnect_on_failure=reconnect_on_failure)
    # container to mark callbacks happened correctly
    callback = []

    def on_connect_fail():
        callback.append(True)
        assert pytest.fail(), "Client should have connected "

    def on_connect(client, userdata, flags, rc, properties=None):
        callback.append(True)
        old_on_connect(client=client,
                       userdata=userdata,
                       flags=flags,
                       rc=rc,
                       properties=properties)
        if (rc != 0):
            assert pytest.fail(
            ), f"Client should have connected. Connection error:{rc}"

    uns_client.on_connect_fail = on_connect_fail
    old_on_connect = uns_client.on_connect
    uns_client.on_connect = on_connect
    try:
        uns_client.run(EMQX_HOST,
                       port,
                       tls=tls,
                       keepalive=KEEP_ALIVE,
                       topic=DEFAULT_TOPIC,
                       qos=qos)
        uns_client.loop()
        while (len(callback) == 0):
            time.sleep(5)
        assert uns_client.protocol == protocol, "Protocol not matching"
        assert len(callback) > 0, f"Connection Callback were not invoked for protocol : {protocol}"
        assert uns_client.connected_flag == True, "Client should have connected "
    finally:
        uns_client.loop_stop()
        uns_client.disconnect()


###############################################################################
@pytest.mark.parametrize("protocol", [(Uns_MQTT_ClientWrapper.MQTTv5),
                                      (Uns_MQTT_ClientWrapper.MQTTv311),
                                      (Uns_MQTT_ClientWrapper.MQTTv31)])
## There appears to be a bug for MQTTv31. The call backs are not occuring
@pytest.mark.parametrize("transport,port,tls",
                         [("tcp", 1884, None), ("websockets", 8090, None),
                          ("tcp", 8885, {
                              "ca_certs": MOSQUITTO_CERT_FILE
                          }),
                          ("websockets", 8091, {
                              "ca_certs": MOSQUITTO_CERT_FILE
                          })])
@pytest.mark.parametrize("username,password", [("ro", "readonly")])
@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("reconnect_on_failure", [(True), (False)])
@pytest.mark.parametrize("qos", [(0), (1), (2)])
def test_02_authenticated_connections(clean_session, protocol, transport, port,
                                      reconnect_on_failure, username, password,
                                      tls, qos):
    """
    Test all the parameters ( including username password against Mosquitto's hosted broker)
    """
    uns_client = Uns_MQTT_ClientWrapper(f"test_01_{protocol}_",
                                   clean_session=clean_session,
                                   protocol=protocol,
                                   transport=transport,
                                   reconnect_on_failure=reconnect_on_failure)
    # container to mark callbacks happened correctly
    callback = []

    def on_connect_fail():
        callback.append(True)
        assert pytest.fail(), "Client should have connected "

    def on_connect(client, userdata, flags, rc, properties=None):
        callback.append(True)
        old_on_connect(client=client,
                       userdata=userdata,
                       flags=flags,
                       rc=rc,
                       properties=properties)
        if (rc != 0):
            assert pytest.fail(
            ), f"Client should have connected. Connection error:{rc}"

    uns_client.on_connect_fail = on_connect_fail
    old_on_connect = uns_client.on_connect
    uns_client.on_connect = on_connect
    try:
        uns_client.run(MOSQUITTO_HOST,
                       port,
                       username=username,
                       password=password,
                       tls=tls,
                       keepalive=KEEP_ALIVE,
                       topic=DEFAULT_TOPIC,
                       qos=qos)
        uns_client.loop()
        while (len(callback) == 0):
            time.sleep(5)
        assert uns_client.protocol == protocol, "Protocol not matching"
        assert len(callback) > 0, f"Connection Callback were not invoked for protocol : {protocol}"
        assert uns_client.connected_flag == True, "Client should have connected "
    finally:
        uns_client.loop_stop()
        uns_client.disconnect()