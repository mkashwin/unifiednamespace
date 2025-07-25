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

Test cases for uns_spb_mapper.spb2unspublisher#Spb2UNSPublisher
"""

import math
import time
from types import SimpleNamespace

import pytest
from uns_mqtt.mqtt_listener import MQTTVersion, UnsMQTTClient
from uns_sparkplugb import uns_spb_helper
from uns_sparkplugb.generated import sparkplug_b_pb2
from uns_sparkplugb.uns_spb_enums import SPBMetricDataTypes

from uns_spb_mapper.sparkplugb_enc_config import MQTTConfig
from uns_spb_mapper.spb2unspublisher import Spb2UNSPublisher

MQTT_HOST: str = MQTTConfig.host
MQTT_PORT: int = MQTTConfig.port
FLOAT_PRECISION = 4  # Decimal precision for float comparisons


@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("reconnect_on_failure", [(True)])
@pytest.mark.parametrize("protocol", [(MQTTVersion.MQTTv5), (MQTTVersion.MQTTv311)])
def test_spb_2_uns_publisher_init(clean_session, protocol, reconnect_on_failure):
    """
    See Spb2UNSPublisher#init()
    """
    uns_client: UnsMQTTClient = UnsMQTTClient(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=clean_session,
        userdata=None,
        protocol=protocol,
        transport="tcp",
        reconnect_on_failure=reconnect_on_failure,
    )
    # Connection not made to broker
    spb_to_uns_publisher = Spb2UNSPublisher(uns_client)
    if protocol == MQTTVersion.MQTTv5:
        assert spb_to_uns_publisher.is_mqtt_v5 is True, (
            "Spb2UNSPublisher#isMQTTv5 should have been True" f"but was {
                spb_to_uns_publisher.is_mqtt_v5}"
        )
    else:
        assert spb_to_uns_publisher.is_mqtt_v5 is False, (
            "Spb2UNSPublisher#isMQTTv5 should have been False " f" but was {
                spb_to_uns_publisher.is_mqtt_v5}"
        )

    assert spb_to_uns_publisher.mqtt_client == uns_client, "Spb2UNSPublisher#mqtt_client should " "have correctly initialized"
    assert (
        len(
            spb_to_uns_publisher.node_device_metric_alias_map,
        )
        == 0
    ), "Spb2UNSPublisher#message_alias_map should be empty"
    assert (
        len(
            spb_to_uns_publisher.topic_alias,
        )
        == 0
    ), "Spb2UNSPublisher#topic_alias should be empty"


@pytest.mark.parametrize("cache_key", ["group1_/edge_node_1/None", "group1_/edge_node_1/MyDevice"])
@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("protocol", [(MQTTVersion.MQTTv5), (MQTTVersion.MQTTv311)])
@pytest.mark.parametrize("reconnect_on_failure", [(True)])
def test_clear_metric_alias(cache_key, clean_session, protocol, reconnect_on_failure):
    """
    See Spb2UNSPublisher#clear_metric_alias()
    """
    uns_client: UnsMQTTClient = UnsMQTTClient(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=clean_session,
        userdata=None,
        protocol=protocol,
        transport="tcp",
        reconnect_on_failure=reconnect_on_failure,
    )
    # Connection not made to broker
    spb_to_uns_pub = Spb2UNSPublisher(uns_client)
    spb_to_uns_pub.save_name_for_alias(cache_key, "value1", 1)
    spb_to_uns_pub.save_name_for_alias(cache_key, "value2", 2)
    spb_to_uns_pub.save_name_for_alias(cache_key, "value3", 3)

    assert (
        len(spb_to_uns_pub.node_device_metric_alias_map[cache_key]) == 3
    ), "Spb2UNSPublisher#node_device_metric_alias_map for cache_key should not be empty"
    spb_to_uns_pub.clear_metric_alias(cache_key)
    assert (
        cache_key not in spb_to_uns_pub.node_device_metric_alias_map
    ), "Spb2UNSPublisher#node_device_metric_alias_map for cache_key should be empty"


@pytest.mark.parametrize("cache_key", ["group1_/edge_node_1/None", "group1_/edge_node_1/MyDevice"])
@pytest.mark.parametrize(
    "metric,name",
    [
        (SimpleNamespace(
            **{Spb2UNSPublisher.SPB_NAME: "metric_name"}), "metric_name"),
        (
            SimpleNamespace(
                **{
                    Spb2UNSPublisher.SPB_NAME: "metric_name1",
                    Spb2UNSPublisher.SPB_ALIAS: 1,
                    Spb2UNSPublisher.SPB_DATATYPE: "Int8",
                }
            ),
            "metric_name1",
        ),
    ],
)
def test_get_metric_name(cache_key, metric, name: str):
    """
    See Spb2UNSPublisher#get_metric_name()
    """
    uns_client: UnsMQTTClient = UnsMQTTClient(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=True,
        userdata=None,
        protocol=MQTTVersion.MQTTv5,
        transport="tcp",
        reconnect_on_failure=True,
    )
    # Connection not made to broker
    spb_to_uns_pub = Spb2UNSPublisher(uns_client)
    assert (
        spb_to_uns_pub.get_metric_name(
            cache_key,
            metric,
        )
        == name
    ), f"Incorrect Name: {name} retrieved from metric: {metric}."


@pytest.mark.parametrize("cache_key", ["group1_/edge_node_1/None", "group1_/edge_node_1/MyDevice"])
@pytest.mark.parametrize("metric", [(SimpleNamespace(no_name="bad key")), (SimpleNamespace()), (None)])
def test_negative_get_metric_name(cache_key, metric):
    """
    Negative tests for Spb2UNSPublisher#get_metric_name()
    """
    uns_client: UnsMQTTClient = UnsMQTTClient(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=True,
        userdata=None,
        protocol=MQTTVersion.MQTTv5,
        transport="tcp",
        reconnect_on_failure=True,
    )
    # Connection not made to broker
    spb_to_uns_pub = Spb2UNSPublisher(uns_client)
    assert spb_to_uns_pub.get_metric_name(
        cache_key, metric) is None, f"Metric name should be none for metric:{metric}"


@pytest.mark.parametrize(
    "cache_key, metric,name, alias",
    [
        (
            "group1_/edge_node_1/None",
            SimpleNamespace(
                **{
                    Spb2UNSPublisher.SPB_NAME: "metric_name2",
                    Spb2UNSPublisher.SPB_ALIAS: 1,
                    Spb2UNSPublisher.SPB_DATATYPE: "Int8",
                }
            ),
            "metric_name2",
            1,
        ),
        (
            "group1_/edge_node_1/MyDevice",
            SimpleNamespace(
                **{
                    Spb2UNSPublisher.SPB_NAME: "metric_name2",
                    Spb2UNSPublisher.SPB_ALIAS: 1,
                    Spb2UNSPublisher.SPB_DATATYPE: "Int8",
                }
            ),
            "metric_name2",
            1,
        ),
    ],
)
def test_get_metric_name_from_alias(cache_key, metric, name: str, alias: int):
    """
    See Spb2UNSPublisher#get_metric_name()
    """
    uns_client: UnsMQTTClient = UnsMQTTClient(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=True,
        userdata=None,
        protocol=MQTTVersion.MQTTv5,
        transport="tcp",
        reconnect_on_failure=True,
    )
    # Connection not made to broker
    spb_2_uns_pub = Spb2UNSPublisher(uns_client)

    assert (
        spb_2_uns_pub.get_metric_name(
            cache_key,
            metric,
        )
        == name
    ), f"Incorrect Name: {name} retrieved from metric: {metric}."

    assert spb_2_uns_pub.node_device_metric_alias_map[cache_key][alias] == name, (
        f"Metric AliasMap was not filled {
            spb_2_uns_pub.node_device_metric_alias_map[cache_key]}"
        f"with alias: {alias} and name: {name}."
    )
    # remove the name from the metric and check again.
    # The alias map should ensure that the name is returned
    delattr(metric, Spb2UNSPublisher.SPB_NAME)

    assert (
        spb_2_uns_pub.get_metric_name(
            cache_key,
            metric,
        )
        == name
    ), f"Incorrect Name: {name} retrieved from metric: {metric}."
    assert spb_2_uns_pub.node_device_metric_alias_map[cache_key][alias] == name, (
        f"Metric AliasMap was not filled {
            spb_2_uns_pub.node_device_metric_alias_map[cache_key]}"
        f"with alias: {alias} and name: {name}."
    )


@pytest.mark.parametrize(
    "group_id,message_type, edge_node_id, device_id, expected_ctx",
    [
        (
            "grp1",
            "DDATA",
            "node1",
            "dev1",
            {
                "spBv1.0_group_id": "grp1",
                "spBv1.0_message_type": "DDATA",
                "spBv1.0_edge_node_id": "node1",
                "spBv1.0_device_id": "dev1",
            },
        ),
        (
            "grp1",
            "DDATA",
            "node1",
            None,
            {
                "spBv1.0_group_id": "grp1",
                "spBv1.0_message_type": "DDATA",
                "spBv1.0_edge_node_id": "node1",
            },
        ),
    ],
)
def test_get_spb_context(group_id: str, message_type: str, edge_node_id: str, device_id: str, expected_ctx: dict[str, str]):
    """
    See Spb2UNSPublisher#get_spb_context
    """
    received_ctx = Spb2UNSPublisher.get_spb_context(
        group_id=group_id, message_type=message_type, edge_node_id=edge_node_id, device_id=device_id
    )
    assert received_ctx == expected_ctx, f"The context received: {
        received_ctx}" f"was not as expected: {expected_ctx}"


@pytest.mark.parametrize(
    "metrics_list",
    [
        (
            [
                (
                    "Temperature",  # name
                    1,  # alias
                    sparkplug_b_pb2.Int32,  # datatype
                    32,  # value
                ),
                (
                    "Scale",  # name
                    2,  # alias
                    sparkplug_b_pb2.String,  # datatype
                    "Celsius",  # value
                ),
            ]
        ),
        (
            [
                (
                    "Pressure",  # name
                    3,  # alias
                    sparkplug_b_pb2.Float,  # datatype
                    23.20,  # value
                ),
                (
                    "Scale",  # name
                    2,  # alias
                    sparkplug_b_pb2.String,  # datatype
                    "Bar",  # value
                ),
            ]
        ),
    ],
)
def test_get_payload_metrics_ddata(metrics_list: list[dict]):
    """
    See Spb2UNSPublisher#getPayload
    Spb2UNSPublisher#getMetricsListFromPayload
    """
    sparkplug_generator = uns_spb_helper.SpBMessageGenerator()
    spb_data_payload = sparkplug_generator.get_device_data_payload()

    for metric_data in metrics_list:
        sparkplug_generator.add_metric(
            payload_or_template=spb_data_payload,
            name=metric_data[0],
            alias=metric_data[1],
            datatype=metric_data[2],
            value=metric_data[3],
        )
    parsed_payload: dict = Spb2UNSPublisher.get_payload(
        spb_data_payload.SerializeToString())
    assert parsed_payload is not None, "parsed payload should not be none"

    assert parsed_payload == spb_data_payload, (
        f"parsed payload: {parsed_payload} is not matching" f" original payload: {
            spb_data_payload}"
    )

    parsed_metrics_list: list = Spb2UNSPublisher.get_metrics_from_payload(
        spb_data_payload.SerializeToString())
    assert len(parsed_metrics_list) == len(metrics_list)
    for parsed_metric, org_metric in zip(parsed_metrics_list, metrics_list, strict=True):
        name = parsed_metric.name
        alias = parsed_metric.alias
        datatype = parsed_metric.datatype

        value = getattr(parsed_metric, SPBMetricDataTypes(
            datatype).get_field_name())

        if alias is not None:
            assert alias == org_metric[1]
        else:
            assert name == org_metric[0]

        assert datatype == org_metric[2]
        if datatype == sparkplug_b_pb2.Float or datatype == sparkplug_b_pb2.Double:
            assert math.isclose(
                value, org_metric[3], rel_tol=1 / 10**FLOAT_PRECISION, )
        else:
            assert value == org_metric[3]

        assert parsed_metric.timestamp is not None and parsed_metric.timestamp > 0


@pytest.mark.parametrize(
    "spb_ctx",
    [
        (
            {
                "spBv1.0_group_id": "grp1",
                "spBv1.0_message_type": "DDATA",
                "spBv1.0_edge_node_id": "node1",
            }
        )
    ],
)
@pytest.mark.parametrize(
    "parsed_msg, tag_name, metric_value, metric_timestamp, is_historical, expected_uns_message",
    [
        (
            None,
            "Temp",
            23,
            1671028163,
            False,
            {  # Test Set 1 -int, no historical data
                "Temp": (23, 1671028163, False),
                "timestamp": 1671028163,
                "spBv1.0_group_id": "grp1",
                "spBv1.0_message_type": "DDATA",
                "spBv1.0_edge_node_id": "node1",
            },
        ),
        (
            None,
            "Grade",
            "A",
            1671008100,
            False,
            {  # Test Set 2 -String, no historical data
                "Grade": ("A", 1671008100, False),
                "timestamp": 1671008100,
                "spBv1.0_group_id": "grp1",
                "spBv1.0_message_type": "DDATA",
                "spBv1.0_edge_node_id": "node1",
            },
        ),
        (
            {
                # Test Set 3 -String, with historical data
                "Grade": ("A", 1671008100, True),
                "timestamp": 1671008100,
                "spBv1.0_group_id": "grp1",
                "spBv1.0_message_type": "DDATA",
                "spBv1.0_edge_node_id": "node1",
            },
            "Grade",
            "B",
            1671008200,
            False,
            {
                "Grade": [("B", 1671008200, False), ("A", 1671008100, True)],
                "timestamp": 1671008200,
                "spBv1.0_group_id": "grp1",
                "spBv1.0_message_type": "DDATA",
                "spBv1.0_edge_node_id": "node1",
            },
        ),
    ],
)
def test_extract_uns_message_for_topic(
    parsed_msg, tag_name, metric_value, metric_timestamp, is_historical, spb_ctx, expected_uns_message
):
    """
    See Spb2UNSPublisher#extract_uns_message_for_topic
    """
    uns_msg = Spb2UNSPublisher.extract_uns_message_for_topic(
        parsed_message=parsed_msg,
        tag_name=tag_name,
        metric_value=metric_value,
        metric_timestamp=metric_timestamp,
        is_historical=is_historical,
        spb_context=spb_ctx,
    )
    assert uns_msg == expected_uns_message


@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("protocol", [(MQTTVersion.MQTTv5), (MQTTVersion.MQTTv311)])
@pytest.mark.parametrize("reconnect_on_failure", [(True)])
def test_publish_to_uns_not_connected(clean_session, protocol, reconnect_on_failure):
    """
    Negative test for Spb2UNSPublisher#publish_to_uns()
    """
    uns_client: UnsMQTTClient = UnsMQTTClient(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=clean_session,
        userdata=None,
        protocol=protocol,
        transport="tcp",
        reconnect_on_failure=reconnect_on_failure,
    )
    # Connection not made to broker
    spb_2_uns_pub = Spb2UNSPublisher(uns_client)
    all_uns_messages: dict = {
        "a/b/c": {
            "temperature": 28.0,
            123: "testing value",
            "pressure": 10.12,
        },
        "x/y/z": {
            "temperature": 28.0,
            123: "testing value",
            "pressure": 10.12,
        },
    }
    with pytest.raises(ConnectionError):
        spb_2_uns_pub.publish_to_uns(all_uns_messages)


@pytest.mark.integrationtest()
@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("protocol", [(MQTTVersion.MQTTv5), (MQTTVersion.MQTTv311)])
@pytest.mark.parametrize("transport,host, port, tls", [("tcp", MQTT_HOST, MQTT_PORT, None)])
@pytest.mark.parametrize("qos", [(1), (2)])
@pytest.mark.parametrize("reconnect_on_failure", [(True)])
@pytest.mark.parametrize(
    "all_uns_messages",
    [
        (
            {
                "a/b/c": {
                    "temperature": 28.0,
                    123: "testing value",
                    "pressure": 10.12,
                },
                "x/y/z": {
                    "temperature": 28.0,
                    78945.12: "Can I have different keys?",
                    "my metric": 200,
                },
            }
        )
    ],
)
def test_publish_to_uns_connected(
    clean_session, protocol, transport, host, port, tls, qos, reconnect_on_failure, all_uns_messages
):
    """
    See Spb2UNSPublisher#publish_to_uns()
    """
    msg_published = []
    uns_client: UnsMQTTClient = UnsMQTTClient(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=clean_session,
        userdata=None,
        protocol=protocol,
        transport=transport,
        reconnect_on_failure=reconnect_on_failure,
    )

    spb_to_uns_pub = Spb2UNSPublisher(uns_client)

    def on_publish(client, userdata, mid, reason_codes, properties):  # noqa: ARG001
        """
        Call back for publish to MQTT
        """
        msg_published.append(True)
        if len(msg_published) == len(all_uns_messages):
            client.disconnect()

    def on_connect(
        client,  # noqa: ARG001
        userdata,  # noqa: ARG001
        flags,  # noqa: ARG001
        reason_code,  # noqa: ARG001
        properties=None,  # noqa: ARG001
    ):
        """
        Call back for connection to MQTT
        """
        spb_to_uns_pub.publish_to_uns(all_uns_messages)

    uns_client.on_connect = on_connect
    uns_client.on_publish = on_publish
    try:
        uns_client.run(host=host, port=port, tls=tls,
                       topics="spBv1.0", qos=qos)
        uns_client.loop_forever(retry_first_connection=True)
        assert True, "Successfully executed the test with no exceptions"
    finally:
        uns_client.loop_stop()
        uns_client.disconnect()

    assert len(msg_published) == len(
        all_uns_messages), "Not all messages were published"
