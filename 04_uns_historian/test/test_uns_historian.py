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

Test cases for uns_historian
"""

import asyncio
import json
import random
import time
from unittest.mock import patch

import pytest
import pytest_asyncio
from paho.mqtt.enums import MQTTErrorCode
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties
from uns_mqtt.mqtt_listener import MQTTVersion, UnsMQTTClient
from uns_sparkplugb.uns_spb_helper import convert_spb_bytes_payload_to_dict

from uns_historian.historian_config import HistorianConfig, MQTTConfig
from uns_historian.historian_handler import HistorianHandler
from uns_historian.uns_mqtt_historian import UnsMqttHistorian, main


@pytest.fixture(scope="session")
def mock_uns_client():
    with patch("uns_historian.uns_mqtt_historian.UnsMQTTClient", autospec=True) as mock_client:
        yield mock_client


@pytest.fixture(scope="session")
def mock_historian_handler():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with patch("uns_historian.uns_mqtt_historian.HistorianHandler", autospec=True) as mock_handler:
        yield mock_handler
    loop.close()


def test_uns_mqtt_disconnect_historian_close_pool(mock_uns_client, mock_historian_handler):  # noqa: ARG001
    uns_mqtt_historian = UnsMqttHistorian()
    # simulate the disconnection by calling the callback directly
    uns_mqtt_historian.uns_client.on_disconnect(
        client=uns_mqtt_historian.uns_client,
        userdata=None,
        flags=None,
        reason_codes=MQTTErrorCode.MQTT_ERR_SUCCESS,
        properties=None,
    )
    # verify the pool was closed
    mock_historian_handler.close_pool.assert_not_called()


def test_uns_mqtt_historian_main_positive_pool_closure(mock_uns_client, mock_historian_handler):  # noqa: ARG001
    # verify that the main method closed the pool in normal execution
    main()
    mock_historian_handler.close_pool.assert_called_once()


def test_uns_mqtt_historian_main_negative_pool_closure(mock_uns_client, mock_historian_handler):
    # verify that the main method closed the pool even if exceptions were raised
    mock_uns_client.loop_forever.side_effect = Exception("Mocked MQTT Error")
    try:
        main()
    except Exception:
        mock_historian_handler.close_pool.assert_called_once()


# test data_list :  [{topic,[messages]}]
# ensure that the topics mentioned here align with settings.yaml
test_data_list: list[dict[str, list[dict | bytes | str]]] = [
    {
        "test/uns/ar1/ln2":  # test_data[0]: test for normal messages
        [
            {
                "timestamp": 1486144502122,
                "TestMetric1": "TestUNS",
            },
            {
                "timestamp": 1586144502222,
                "TestMetric2": "TestUNS",
            },
        ],
    },
    {
        "spBv1.0/uns_group/NBIRTH/eon1":  # test_data[1]: test for SparkplugB messages
        [
            (
                b"\x08\xc4\x89\x89\x83\xd30\x12\x17\n\x08Inputs/A\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ "
                b"\x0bp\x00\x12\x17\n\x08Inputs/B\x10\x01\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\t"
                b"Outputs/E\x10\x02\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\tOutputs/F\x10\x03\x18\xea\xf2\xf5\xa8\xa0+ "
                b"\x0bp\x00\x12+\n\x18Properties/Hardware Make\x10\x04\x18\xea\xf2\xf5\xa8\xa0+ \x0cz\x04Sony\x12!\n\x11"
                b"Properties/Weight\x10\x05\x18\xea\xf2\xf5\xa8\xa0+ \x03P\xc8\x01\x18\x00"
            ),
        ],
    },
]


def create_publisher() -> UnsMQTTClient:
    """
    utility method to create publisher
    """
    uns_publisher = UnsMQTTClient(
        client_id=f"publisher-{time.time()}-{random.randint(0, 1000)}",  # noqa: S311
        clean_session=MQTTConfig.clean_session,
        userdata=None,
        protocol=MQTTConfig.version,
        transport=MQTTConfig.transport,
        reconnect_on_failure=MQTTConfig.reconnect_on_failure,
    )
    if MQTTConfig.username is not None:
        uns_publisher.username_pw_set(MQTTConfig.username, MQTTConfig.password)
    uns_publisher.setup_tls(MQTTConfig.tls)
    uns_publisher.topics = MQTTConfig.topics
    connect_properties = None
    if MQTTConfig.version == MQTTVersion.MQTTv5:
        connect_properties = Properties(PacketTypes.CONNECT)
    uns_publisher.connect(
        host=MQTTConfig.host, port=MQTTConfig.port, keepalive=MQTTConfig.keepalive, properties=connect_properties
    )
    return uns_publisher


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def clean_up_database():
    """
    Clean database from test data from the historian after execution of the tests
    """
    yield
    delete_sql_cmd = f""" DELETE FROM {HistorianConfig.table} WHERE
                               topic = $1 AND
                               mqtt_msg = $2;"""  # noqa: S608
    for test_data in test_data_list:
        for topic, messages in test_data.items():
            for message in messages:
                if type(message) is bytes:
                    message = convert_spb_bytes_payload_to_dict(message)
                async with HistorianHandler() as historian:
                    await historian.execute_prepared(delete_sql_cmd, *[topic, json.dumps(message)])


@pytest.mark.integrationtest
# FIXME not working with VsCode https://github.com/microsoft/vscode-python/issues/19374
# Comment this marker and run test individually in VSCode. Uncomment for running from command line / CI
@pytest.mark.xdist_group(name="uns_mqtt_historian")
@pytest.mark.parametrize(  # convert test data dict into tuples for pytest parameterize
    "topic, messages", [(topic, messages) for dictionary in test_data_list for topic, messages in dictionary.items()]
)
def test_uns_mqtt_historian(clean_up_database, topic: str, messages: list):  # noqa: ARG001
    uns_mqtt_historian = None
    uns_publisher = None
    try:
        # 1. Start the historian listener in a new thread
        uns_mqtt_historian = UnsMqttHistorian()
        mgs_received: list = []
        old_on_message = uns_mqtt_historian.uns_client.on_message
        # Loop inside on_message_decorator is null for some reason. hence trying to set outer loop in callback
        loop = asyncio.get_event_loop()

        def on_message_decorator(client, userdata, msg):
            """
            Override / wrap the existing on_message callback so that
            we can track the messages were processed
            """
            asyncio.set_event_loop(loop)
            old_on_message(client, userdata, msg)
            mgs_received.append(msg)

        uns_mqtt_historian.uns_client.on_message = on_message_decorator

        uns_mqtt_historian.uns_client.loop_start()

        # 2. Create an MQTT publisher
        uns_publisher: UnsMQTTClient = create_publisher()
        uns_publisher.loop_start()

        if MQTTConfig.version == MQTTVersion.MQTTv5:
            publish_properties = Properties(PacketTypes.PUBLISH)
        for message in messages:
            if type(message) is dict or type(message) is str:
                message = json.dumps(message)
            # publish multiple message as non-persistent
            # to allow the tests to be idempotent across multiple runs
            uns_publisher.publish(topic=topic, payload=message, qos=2, retain=True, properties=publish_properties)
            # allow for the message to be received
            time.sleep(0.1)

        # wait for uns_mqtt_historian to have persisted to the database
        while len(mgs_received) < len(messages):
            time.sleep(0.1)
        # disconnect the historian listener to free the asyncio loop
        uns_mqtt_historian.uns_client.disconnect()
        uns_mqtt_historian.uns_client.loop_stop()
        # connect to the database and validate
        select_query = f""" SELECT * FROM {HistorianConfig.table} WHERE
                               topic = $1 AND
                               mqtt_msg = $2 AND
                               client_id = $3;"""  # noqa: S608

        # Inline the async function
        async def execute_prepared_async(select_query, topic, message, client_id):
            async with HistorianHandler() as historian:
                return await historian.execute_prepared(select_query, *[topic, json.dumps(message), client_id])

        for message in messages:
            if type(message) is bytes:
                message = convert_spb_bytes_payload_to_dict(message)

            result = loop.run_until_complete(
                execute_prepared_async(select_query, topic, message, uns_mqtt_historian.client_id)
            )

            assert result is not None, "Should have gotten a result"
            assert len(result) == 1, "Should have gotten only one record because we inserted only one record"

    finally:
        # clean up the topic and disconnect the publisher
        uns_publisher.publish(topic=topic, payload=b"", qos=2, retain=True, properties=publish_properties)
        uns_publisher.disconnect()
        uns_mqtt_historian.uns_client.disconnect()
