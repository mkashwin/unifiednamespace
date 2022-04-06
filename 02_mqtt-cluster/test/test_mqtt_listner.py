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

@pytest.mark.parametrize(
    "topicWithWildcard,topic,expectedResult",[
     ("#", "a", True), ("#", "a/b/c", True), ("a/#", "a", False),
     ("a/#", "a/b/c", True), ("+", "a", True), ("+", "a/b/c", False),
     (None, "a/b/c", False), ("+", "a/b/c", False), ("topic1","topic1",True)]
)
def test_isTopicMatching(topicWithWildcard: str, topic: str,
                         expectedResult: bool):
    result = Uns_MQTT_ClientWrapper.isTopicMatching(topicWithWildcard, topic)
    assert result == expectedResult , f"""
            Topic WildCard:{topicWithWildcard}, 
            Topic:{topic}, 
            Expected Result:{expectedResult},
            Actual Result: {result}"""


@pytest.mark.parametrize("message, ignored_attr , expected_result" , [
                        ({} , ["key1"] , {}) ,
                        ({"key1": "value1"} , ["key1"] , {}) ,
                        ({"key1": ["value1" , "value2" , "value3"]} , ["key1"] , {}) , 
                        ({"key1": "value1" , "key2": "value2"} , ["key1"] , {"key2": "value2"}) , 
                        ({"key1": "value1" , "key2": "value2"} , ["key1" , "key2"] , {"key1": "value1" , "key2": "value2"} ) ,         
                        ({"key1":  {"key1":"val" , "key2":100} , "key2": "value2" ,  "key3":"value3"} , ["key1" , "key2"] , 
                                    {"key1":  {"key1":"val"} , "key2": "value2" ,  "key3":"value3"} ) , 
                        ({"key1": "value1"} , ["key1", "childKey1"] , {"key1": "value1"}) , 
                        ({"key1": {"child1":"val" , "child2":100}} , ["key1","child1"] , {"key1": {"child2":100}}) ,         
                        ({"key1": {"child1":"val" , "child2":100}, "child1": "value2"} , ["key1","child1"] , {"key1": {"child2":100},"child1": "value2"}) ,         
                        ]
)
def test_del_key_from_dict(message:dict , ignored_attr:list, expected_result:dict):
    """
    Should remove just the key should it be present.
    Test support for nested keys. e.g. the key "parent.child" goes in as ["parent", "ch{}ild"]
    The index of the array always indicates the depth of the key tree
    """
    result = Uns_MQTT_ClientWrapper.del_key_from_dict(message, ignored_attr)
    assert result == expected_result , f""" message:{message}, 
            Attributes to filter:{ignored_attr}, 
            Expected Result:{expected_result},
            Actual Result: {result}"""

@pytest.mark.parametrize("topic,json_dict, mqtt_ignored_attributes, expected_result" , [
    ("topic1", {"timestamp":123456, "val1": 1234 }, None, {"timestamp":123456, "val1": 1234 }),
    ("topic1", {"timestamp":123456, "val1": 1234 }, {"+":"timestamp"}, {"val1": 1234 }),
    ("topic1", {"timestamp":123456, "val1": 1234 }, {"#":"timestamp"}, {"val1": 1234 }),
    ("topic1", {"timestamp":123456, "val1": 1234 }, {"topic1":"timestamp"}, {"val1": 1234 }),
    ("topic1", {"timestamp":123456, "val1": 1234 }, {"topic2":"timestamp"}, {"timestamp":123456, "val1": 1234 }),
])
def test_filter_ignored_attributes(topic:str, json_dict:dict, mqtt_ignored_attributes, expected_result):
    result = Uns_MQTT_ClientWrapper.filter_ignored_attributes(topic, json_dict, mqtt_ignored_attributes)
    assert result == expected_result , f""" message:{json_dict}, 
            Attributes to filter:{mqtt_ignored_attributes}, 
            Expected Result:{expected_result},
            Actual Result: {result}"""
