import inspect
import os
import sys
import time
import paho.mqtt.client as mqtt_client
import pytest

# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            'src')))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)
from uns_mqtt.mqtt_listener import UNS_MQTT_Listener

DEFAULT_HOST = "broker.emqx.io"  # test the client against the hosted broker
DEFAULT_TOPIC = "test/uns/#"  # as the hosted broker doesn't allow subscription to #
KEEP_ALIVE = 60
CA_CERT_FILE=os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], 'cert',
            'broker.emqx.io-ca.crt')
EMQX_TLS:dict = {"ca_certs":CA_CERT_FILE}


@pytest.mark.parametrize("protocol", [(mqtt_client.MQTTv5),
                                      (mqtt_client.MQTTv311)])
#                                     (mqtt_client.MQTTv31)])
## There appears to be a bug for MQTTv31. The call backs are not occuring 
@pytest.mark.parametrize("transport,port,tls", [("tcp", 1883, None),
                                            ("websockets", 8083, None),
                                            ("tcp", 8883, EMQX_TLS),
                                            ("websockets", 8084, EMQX_TLS)])
@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("reconnect_on_failure", [(True), (False)])
@pytest.mark.parametrize("qos", [(0),(1), (2)])
def test_01_positive_options(clean_session, protocol, transport,
                                         port, reconnect_on_failure,tls,qos):
    """
    Test all the parameters ( except username password against EMQX's default broker)
    """
    uns_client = UNS_MQTT_Listener(f"test_01_{protocol}",
                                   clean_session=clean_session,
                                   protocol=protocol,
                                   transport=transport,
                                   reconnect_on_failure=reconnect_on_failure,
                                   tls=tls)
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
        uns_client.run(DEFAULT_HOST, port, KEEP_ALIVE, DEFAULT_TOPIC,
                       qos)
        uns_client.loop()
        while (len(callback) == 0):
            time.sleep(5)
        assert uns_client.protocol == protocol, "Protocol not matching"
        assert len(
            callback
        ) > 0, f"Connection Callback were not invoked for protocol : {protocol}"
        assert uns_client.connected_flag == True, "Client should have connected "
    finally:
        uns_client.loop_stop()
        uns_client.disconnect()
