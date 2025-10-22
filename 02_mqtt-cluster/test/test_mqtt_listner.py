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

Test for uns_mqtt.mqtt_listener
"""

import random
import time
from pathlib import Path

import pytest

from uns_mqtt.mqtt_listener import MQTTVersion, UnsMQTTClient

EMQX_HOST = "broker.emqx.io"  # test the client against the hosted emqx broker
EMQX_CERT_FILE = Path(__file__).resolve().parent / \
    "cert" / "broker.emqx.io-ca.crt"

# MOSQUITTO_HOST = "test.mosquitto.org"  # test the client against the hosted mosquitto broker
# MOSQUITTO_CERT_FILE = Path(__file__).resolve().parent / "cert" / "mosquitto.org.crt"
MOSQUITTO_HOST = "localhost"  # test the client against the hosted mosquitto broker
MOSQUITTO_CERT_FILE = Path(__file__).resolve(
).parent / "local_mqtt" / "certs" / "server" / "server.crt"

ONE_TOPIC = ["test/uns/#"]

# used to reduce load on the hosted broker
TWO_TOPICS = ["test/uns/#", "spBv1.0/#"]
KEEP_ALIVE = 60


@pytest.mark.integrationtest()
@pytest.mark.parametrize("broker", [MOSQUITTO_HOST])  # EMQX_HOST
@pytest.mark.parametrize("protocol", [(MQTTVersion.MQTTv5), (MQTTVersion.MQTTv311)])
#                                     (UNS_MQTT_Listener.MQTTv31)])
# There appears to be a bug for MQTTv31. The call backs are not occurring
@pytest.mark.parametrize(
    "transport,port,tls",
    [
        ("tcp", 1883, None),
        ("websockets", 8080, None),  # 8083
        (
            "tcp",
            8883,
            {
                "ca_certs": MOSQUITTO_CERT_FILE  # EMQX_CERT_FILE,
            },
        ),
        (
            "websockets",
            8081,  # 8084
            {
                "ca_certs": MOSQUITTO_CERT_FILE  # EMQX_CERT_FILE,,
            },
        ),
    ],
)
@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("reconnect_on_failure", [(True), (False)])
@pytest.mark.parametrize("qos", [(0), (1), (2)])
@pytest.mark.parametrize("topics", [TWO_TOPICS, ONE_TOPIC])
def test_01_unauthenticated_connections(clean_session, protocol, broker, transport, port, reconnect_on_failure, topics, tls, qos):
    """
    Test all the parameters ( except username password against EMQX's hosted broker instance)
    """
    uns_client = UnsMQTTClient(
        client_id=f"test_01_{protocol}-{time.time()}-{random.randint(0, 1000)}",  # noqa: S311
        clean_session=clean_session,
        protocol=protocol,
        transport=transport,
        reconnect_on_failure=reconnect_on_failure,
    )
    # container to mark callbacks happened correctly
    callback = []

    def on_connect_fail():
        callback.append(True)
        assert pytest.fail(), "Client should have connected "

    def on_connect(client, userdata, flags, result_code, properties=None):
        callback.append(True)
        old_on_connect(client=client, userdata=userdata, flags=flags,
                       return_code=result_code, properties=properties)
        if result_code != 0:
            assert pytest.fail(
            ), f"Client should have connected. Connection error:{result_code}"

    uns_client.on_connect_fail = on_connect_fail
    old_on_connect = uns_client.on_connect
    uns_client.on_connect = on_connect

    try:
        uns_client.run(broker, port, tls=tls,
                       keepalive=KEEP_ALIVE, topics=topics, qos=qos)

        while not uns_client.is_connected():
            time.sleep(1)
            uns_client.loop()

        assert uns_client.protocol == protocol, "Protocol not matching"
        assert (
            len(
                callback,
            )
            > 0
        ), f"Connection Callback were not invoked for protocol : {protocol}"
        assert uns_client.is_connected() is True, "Client should have connected "
    finally:
        uns_client.loop_stop()
        uns_client.disconnect()


###############################################################################
@pytest.mark.integrationtest()
@pytest.mark.parametrize("broker", [MOSQUITTO_HOST])
@pytest.mark.parametrize("protocol", [(MQTTVersion.MQTTv5), (MQTTVersion.MQTTv311), (MQTTVersion.MQTTv31)])
@pytest.mark.parametrize(
    "transport,port,tls",
    [
        ("tcp", 1884, None),
        ("websockets", 8090, None),
        (
            "tcp",
            8885,
            {
                "ca_certs": MOSQUITTO_CERT_FILE,
            },
        ),
        (
            "websockets",
            8091,
            {
                "ca_certs": MOSQUITTO_CERT_FILE,
            },
        ),
    ],
)
@pytest.mark.parametrize("username,password", [("ro", "readonly")])
@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("reconnect_on_failure", [(True), (False)])
@pytest.mark.parametrize("qos", [(0), (1), (2)])
@pytest.mark.parametrize("topics", [TWO_TOPICS, ONE_TOPIC])
def test_02_authenticated_connections(
    clean_session, protocol, broker, transport, port, reconnect_on_failure, username, password, topics, tls, qos
):
    """
    Test all the parameters ( including username password against Mosquitto's hosted broker)
    """
    uns_client = UnsMQTTClient(
        client_id=f"test_01_{protocol}-{time.time()}-{random.randint(0, 1000)}",  # noqa: S311
        clean_session=clean_session,
        protocol=protocol,
        transport=transport,
        reconnect_on_failure=reconnect_on_failure,
    )
    # container to mark callbacks happened correctly
    callback = []

    def on_connect_fail():
        callback.append(True)
        assert pytest.fail(), "Client should have connected "

    def on_connect(client, userdata, flags, result_code, properties=None):
        callback.append(True)
        old_on_connect(client=client, userdata=userdata, flags=flags,
                       return_code=result_code, properties=properties)
        if result_code != 0:
            assert pytest.fail(
            ), f"Client should have connected. Connection error:{result_code}"

    uns_client.on_connect_fail = on_connect_fail
    old_on_connect = uns_client.on_connect
    uns_client.on_connect = on_connect
    try:
        uns_client.run(
            broker, port, username=username, password=password, tls=tls, keepalive=KEEP_ALIVE, topics=topics, qos=qos
        )
        while not uns_client.is_connected():
            time.sleep(1)
            uns_client.loop()

        assert uns_client.protocol == protocol, "Protocol not matching"
        assert (
            len(
                callback,
            )
            > 0
        ), f"Connection Callback were not invoked for protocol : {protocol}"
        assert uns_client.is_connected() is True, "Client should have connected "
    finally:
        uns_client.loop_stop()
        uns_client.disconnect()


@pytest.mark.parametrize(
    "topic_with_wildcard,topic,expected_result",
    [
        ("#", "a", True),
        ("#", "a/b/c", True),
        ("a/#", "a", True),
        ("a/#", "a/b/c", True),
        ("a/#", "a/bbb", True),
        ("a/#", "ab/a", False),
        ("a/#/c", "ab/a", False),
        ("a/#/c", "a/b/c", True),
        ("aa/#/cc", "aa/abc/cc", True),
        ("a/+", "a/b", True),
        ("a/+", "a/bbb", True),
        ("a/+/c", "a/b/c", True),
        ("a/+/c", "a/bbb/c", True),
        ("+", "a", True),
        ("+", "abc", True),
        ("+", "a/b/c", False),
        (None, "a/b/c", False),
        ("+", "a/b/c", False),
        ("topic1", "topic1", True),
        ("a/b/c", "a/b/c", True),
        ("a/b", "a/b/c", False),
    ],
)
def test_is_topic_matched(topic_with_wildcard: str, topic: str, expected_result: bool):
    """
    Test case for function Uns_MQTT_ClientWrapper.isTopicMatching
    """
    result = UnsMQTTClient.is_topic_matched(topic_with_wildcard, topic)
    assert result == expected_result, f"""
            Topic WildCard:{topic_with_wildcard},
            Topic:{topic},
            Expected Result:{expected_result},
            Actual Result: {result}"""


@pytest.mark.parametrize(
    "message, ignored_attr , expected_result",
    [
        ({}, ["key1"], {}),
        (
            {
                "key1": "value1",
            },
            ["key1"],
            {},
        ),
        (
            {
                "key1": ["value1", "value2", "value3"],
            },
            ["key1"],
            {},
        ),
        (
            {
                "key1": "value1",
                "key2": "value2",
            },
            ["key1"],
            {
                "key2": "value2",
            },
        ),
        (
            {
                "key1": "value1",
                "key2": "value2",
            },
            ["key1", "key2"],
            {
                "key1": "value1",
                "key2": "value2",
            },
        ),
        (
            {
                "key1": {
                    "key1": "val",
                    "key2": 100,
                },
                "key2": "value2",
                "key3": "value3",
            },
            ["key1", "key2"],
            {
                "key1": {
                    "key1": "val",
                },
                "key2": "value2",
                "key3": "value3",
            },
        ),
        (
            {
                "key1": "value1",
            },
            ["key1", "childKey1"],
            {
                "key1": "value1",
            },
        ),
        (
            {
                "key1": {
                    "child1": "val",
                    "child2": 100,
                },
            },
            ["key1", "child1"],
            {
                "key1": {
                    "child2": 100,
                },
            },
        ),
        (
            {
                "key1": {
                    "child1": "val",
                    "child2": 100,
                },
                "child1": "value2",
            },
            ["key1", "child1"],
            {
                "key1": {
                    "child2": 100,
                },
                "child1": "value2",
            },
        ),
    ],
)
def test_del_key_from_dict(message: dict, ignored_attr: list, expected_result: dict):
    """
    Should remove just the key should it be present.
    Test support for nested keys. e.g. the key "parent.child" goes in as ["parent", "ch{}ild"]
    The index of the array always indicates the depth of the key tree
    """
    result = UnsMQTTClient.del_key_from_dict(message, ignored_attr)
    assert result == expected_result, f""" message:{message},
            Attributes to filter:{ignored_attr},
            Expected Result:{expected_result},
            Actual Result: {result}"""


@pytest.mark.parametrize(
    "topic,json_dict, mqtt_ignored_attributes, expected_result",
    [
        (
            "topic1",
            {
                "timestamp": 123456,
                "val1": 1234,
            },
            None,
            {
                "timestamp": 123456,
                "val1": 1234,
            },
        ),
        (
            "topic1",
            {
                "timestamp": 123456,
                "val1": 1234,
            },
            {},
            {
                "timestamp": 123456,
                "val1": 1234,
            },
        ),
        (
            "topic1",
            {
                "timestamp": 123456,
                "val1": 1234,
            },
            {
                "+": "timestamp",
            },
            {
                "val1": 1234,
            },
        ),
        (
            "topic1",
            {
                "timestamp": 123456,
                "val1": 1234,
            },
            {
                "#": "timestamp",
            },
            {
                "val1": 1234,
            },
        ),
        (
            "topic1",
            {
                "timestamp": 123456,
                "val1": 1234,
            },
            {
                "topic1": "timestamp",
            },
            {
                "val1": 1234,
            },
        ),
        (
            "topic1",
            {
                "timestamp": 123456,
                "val1": 1234,
            },
            {
                "topic2": "timestamp",
            },
            {
                "timestamp": 123456,
                "val1": 1234,
            },
        ),
    ],
)
def test_filter_ignored_attributes(topic: str, json_dict: dict, mqtt_ignored_attributes, expected_result):
    """
    Test case for Uns_MQTT_ClientWrapper.filter_ignored_attributes
    """
    result = UnsMQTTClient.filter_ignored_attributes(
        topic, json_dict, mqtt_ignored_attributes)
    assert result == expected_result, f""" message:{json_dict},
            Attributes to filter:{mqtt_ignored_attributes},
            Expected Result:{expected_result},
            Actual Result: {result}"""


@pytest.mark.parametrize(
    "topic, payload_msg, expected_result",
    [
        (
            "a/b/c",
            b'{"timestamp": 123456, "val1": 1234}',
            {
                "timestamp": 123456,
                "val1": 1234,
            },
        ),
        (
            "spBv1.0/STATE/scada_1",
            b'{"online": true, "timestamp": 1668114759262}',
            {"online": True, "timestamp": 1668114759262},
        ),
        (
            "spBv1.0/uns_group/NBIRTH/eon1",
            b"\x08\xc4\x89\x89\x83\xd30\x12\x17\n\x08Inputs/A\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ "
            b"\x0bp\x00\x12\x17\n\x08Inputs/B\x10\x01\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\t"
            b"Outputs/E\x10\x02\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\tOutputs/F\x10\x03\x18\xea\xf2\xf5\xa8\xa0+ "
            b"\x0bp\x00\x12+\n\x18Properties/Hardware Make\x10\x04\x18\xea\xf2\xf5\xa8\xa0+ \x0cz\x04Sony\x12!\n\x11"
            b"Properties/Weight\x10\x05\x18\xea\xf2\xf5\xa8\xa0+ \x03P\xc8\x01\x18\x00",
            {
                "timestamp": 1671554024644,
                "metrics": [
                    {
                        "name": "Inputs/A",
                        "timestamp": 1486144502122,
                        "alias": 0,
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Inputs/B",
                        "timestamp": 1486144502122,
                        "alias": 1,
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Outputs/E",
                        "timestamp": 1486144502122,
                        "alias": 2,
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Outputs/F",
                        "timestamp": 1486144502122,
                        "alias": 3,
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Properties/Hardware Make",
                        "timestamp": 1486144502122,
                        "alias": 4,
                        "datatype": 12,
                        "value": "Sony",
                    },
                    {
                        "name": "Properties/Weight",
                        "timestamp": 1486144502122,
                        "alias": 5,
                        "datatype": 3,
                        "value": 200,
                    },
                ],
                "seq": 0,
            },
        ),
    ],
)
def test_get_payload_as_dict(topic: str, payload_msg, expected_result):
    """
    Test case for Uns_MQTT_ClientWrapper.get_payload_as_dict
    """
    # create a UnsMQTTClient but dont connect to the broker
    # object is needed to test the functions
    uns_client = UnsMQTTClient(
        client_id=f"test_01_{time.time()}-{random.randint(0, 1000)}",  # noqa: S311
        clean_session=True,
        protocol=MQTTVersion.MQTTv5,
        transport="tcp",
        reconnect_on_failure=True,
    )
    result = uns_client.get_payload_as_dict(topic, payload_msg, None)
    assert result == expected_result, f""" message:{payload_msg},
            Expected Result:{expected_result},
            Actual Result: {result}"""
