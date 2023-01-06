import inspect
import os
import sys
import time
from types import SimpleNamespace

import pytest

cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            'src')))
uns_mqtt_folder = os.path.realpath(
    os.path.abspath(
        os.path.join(cmd_subfolder, '..', '..', '02_mqtt-cluster', 'src')))

if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

if uns_mqtt_folder not in sys.path:
    sys.path.insert(2, uns_mqtt_folder)

from uns_mqtt.mqtt_listener import Uns_MQTT_ClientWrapper
from uns_sparkplugb import uns_spb_helper
from uns_sparkplugb.generated import sparkplug_b_pb2
from uns_spb_mapper.spb2unspublisher import Spb2UNSPublisher


@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("reconnect_on_failure", [(True)])
@pytest.mark.parametrize("protocol", [(Uns_MQTT_ClientWrapper.MQTTv5),
                                      (Uns_MQTT_ClientWrapper.MQTTv311)])
@pytest.mark.parametrize("qos", [(1), (2)])
@pytest.mark.parametrize("transport,host, port, tls",
                         [("tcp", "broker.emqx.io", 1883, None)])
def test_Spb2UNSPublisher_init(clean_session, protocol, transport, host, port,
                               tls, qos, reconnect_on_failure):
    """
    See Spb2UNSPublisher#init()
    """
    uns_client: Uns_MQTT_ClientWrapper = Uns_MQTT_ClientWrapper(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=clean_session,
        userdata=None,
        protocol=protocol,
        transport=transport,
        reconnect_on_failure=reconnect_on_failure)
    # Connection not made to broker
    spg2unPub = Spb2UNSPublisher(uns_client)
    if protocol == Uns_MQTT_ClientWrapper.MQTTv5:
        assert (
            spg2unPub.isMQTTv5 is True
        ), f"Spb2UNSPublisher#isMQTTv5 should have been True but was {spg2unPub.isMQTTv5}"
    else:
        assert (
            spg2unPub.isMQTTv5 is False
        ), f"Spb2UNSPublisher#isMQTTv5 should have been False but was {spg2unPub.isMQTTv5}"

    assert spg2unPub.mqtt_client == uns_client, "Spb2UNSPublisher#mqtt_client should have been correctly initialized"
    assert len(spg2unPub.metric_name_alias_map
               ) == 0, "Spb2UNSPublisher#message_alias_map should be empty"
    assert len(spg2unPub.topic_alias
               ) == 0, "Spb2UNSPublisher#topic_alias should be empty"


@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("reconnect_on_failure", [(True)])
@pytest.mark.parametrize("protocol", [(Uns_MQTT_ClientWrapper.MQTTv5),
                                      (Uns_MQTT_ClientWrapper.MQTTv311)])
@pytest.mark.parametrize("qos", [(1), (2)])
@pytest.mark.parametrize("transport,host, port, tls",
                         [("tcp", "broker.emqx.io", 1883, None)])
def test_Spb2UNSPublisher_clearMetricAlias(clean_session, protocol, transport,
                                           host, port, tls, qos,
                                           reconnect_on_failure):
    """
    See Spb2UNSPublisher#clearMetricAlias()
    """
    uns_client: Uns_MQTT_ClientWrapper = Uns_MQTT_ClientWrapper(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=clean_session,
        userdata=None,
        protocol=protocol,
        transport=transport,
        reconnect_on_failure=reconnect_on_failure)
    # Connection not made to broker
    spg2unPub = Spb2UNSPublisher(uns_client)
    spg2unPub.metric_name_alias_map[1] = "value1"
    spg2unPub.metric_name_alias_map[2] = "value2"
    spg2unPub.metric_name_alias_map[3] = "value3"
    assert len(spg2unPub.metric_name_alias_map
               ) == 3, "Spb2UNSPublisher#message_alias_map should not be empty"
    spg2unPub.clearMetricAlias()
    assert len(spg2unPub.metric_name_alias_map
               ) == 0, "Spb2UNSPublisher#message_alias_map should be empty"


@pytest.mark.parametrize(
    "metric,name",
    [(SimpleNamespace(**{Spb2UNSPublisher.SPB_NAME: "metric_name"}),
      "metric_name"),
     (SimpleNamespace(
         **{
             Spb2UNSPublisher.SPB_NAME: "metric_name1",
             Spb2UNSPublisher.SPB_ALIAS: 1,
             Spb2UNSPublisher.SPB_DATATYPE: "Int8"
         }), "metric_name1")])
def testGetMetricName(metric, name: str):
    """
    See Spb2UNSPublisher#getMetricName()
    """
    uns_client: Uns_MQTT_ClientWrapper = Uns_MQTT_ClientWrapper(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=True,
        userdata=None,
        protocol=Uns_MQTT_ClientWrapper.MQTTv5,
        transport="tcp",
        reconnect_on_failure=True)
    # Connection not made to broker
    spg2unPub = Spb2UNSPublisher(uns_client)
    assert spg2unPub.getMetricName(
        metric
    ) == name, f"Incorrect Name: {name} retrieved from metric: {metric}."


@pytest.mark.parametrize("metric",
                         [(SimpleNamespace(**{"no_name": "bad key"})),
                          (SimpleNamespace(**{})), (None)])
def testNegativeGetMetricName(metric):
    """
    See Spb2UNSPublisher#getMetricName()
    """
    uns_client: Uns_MQTT_ClientWrapper = Uns_MQTT_ClientWrapper(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=True,
        userdata=None,
        protocol=Uns_MQTT_ClientWrapper.MQTTv5,
        transport="tcp",
        reconnect_on_failure=True)
    # Connection not made to broker
    spg2unPub = Spb2UNSPublisher(uns_client)
    assert spg2unPub.getMetricName(
        metric) is None, f"Metric name should be none for metric:{metric}"


@pytest.mark.parametrize("metric,name, alias", [(SimpleNamespace(
    **{
        Spb2UNSPublisher.SPB_NAME: "metric_name1",
        Spb2UNSPublisher.SPB_ALIAS: 1,
        Spb2UNSPublisher.SPB_DATATYPE: "Int8"
    }), "metric_name1", 1)])
def testGetMetricName_from_Alias(metric, name: str, alias: int):
    """
    See Spb2UNSPublisher#getMetricName()
    """
    uns_client: Uns_MQTT_ClientWrapper = Uns_MQTT_ClientWrapper(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=True,
        userdata=None,
        protocol=Uns_MQTT_ClientWrapper.MQTTv5,
        transport="tcp",
        reconnect_on_failure=True)
    # Connection not made to broker
    spg2unPub = Spb2UNSPublisher(uns_client)

    assert spg2unPub.getMetricName(
        metric
    ) == name, f"Incorrect Name: {name} retrieved from metric: {metric}."

    assert spg2unPub.metric_name_alias_map[alias] == name, (
        f"Metric AliasMap was not filled {spg2unPub.metric_name_alias_map}"
        f"with alias: {alias} and name: {name}.")
    # remove the name from the metric and check again. The alias map should ensure that the name is returned
    delattr(metric, Spb2UNSPublisher.SPB_NAME)

    assert spg2unPub.getMetricName(
        metric
    ) == name, f"Incorrect Name: {name} retrieved from metric: {metric}."
    assert spg2unPub.metric_name_alias_map[alias] == name, (
        f"Metric AliasMap was not filled {spg2unPub.metric_name_alias_map}"
        f"with alias: {alias} and name: {name}.")


@pytest.mark.parametrize(
    "group_id,message_type, edge_node_id, device_id, expected_ctx",
    [("grp1", "DDATA", "node1", "dev1", {
        "spBv1.0_group_id": "grp1",
        "spBv1.0_message_type": "DDATA",
        "spBv1.0_edge_node_id": "node1",
        "spBv1.0_device_id": "dev1"
    }),
     ("grp1", "DDATA", "node1", None, {
         "spBv1.0_group_id": "grp1",
         "spBv1.0_message_type": "DDATA",
         "spBv1.0_edge_node_id": "node1"
     })])
def testGetSpbContext(group_id: str, message_type: str, edge_node_id: str,
                      device_id: str, expected_ctx: dict[str, str]):
    """
    See Spb2UNSPublisher#getSpbContext
    """
    received_ctx = Spb2UNSPublisher.getSpbContext(group_id=group_id,
                                                  message_type=message_type,
                                                  edge_node_id=edge_node_id,
                                                  device_id=device_id)
    assert received_ctx == expected_ctx, f"The context received: {received_ctx} was not as expected: {expected_ctx}"


@pytest.mark.parametrize(
    "metrics_list",
    [
        ([
            (
                "Temperature",  # name
                1,  # alias
                sparkplug_b_pb2.Int32,  # datatype
                32  # value
            ),
            (
                "Scale",  # name
                2,  # alias
                sparkplug_b_pb2.String,  # datatype
                "Celsius"  # value
            )
        ]),
        ([
            (
                "Pressure",  # name
                3,  # alias
                sparkplug_b_pb2.Float,  # datatype
                23.20  # value
            ),
            (
                "Scale",  # name
                4,  # alias
                sparkplug_b_pb2.String,  # datatype
                "Bar"  # value
            )
        ]),
    ])
def testGetPayloadAndMetrics_Ddata(metrics_list: list[dict]):
    """
    See Spb2UNSPublisher#getPayload
    Spb2UNSPublisher#getMetricsListFromPayload
    """
    sparkplug_message = uns_spb_helper.Spb_Message_Generator()
    sPBpayload = sparkplug_message.getDeviceDataPayload()

    for metric_data in metrics_list:
        sparkplug_message.addMetric(payload=sPBpayload,
                                    name=metric_data[0],
                                    alias=metric_data[1],
                                    data_type=metric_data[2],
                                    value=metric_data[3])
    parsedPayload = Spb2UNSPublisher.getPayload(sPBpayload.SerializeToString())
    assert parsedPayload is not None, "parsed payload should not be none"

    assert parsedPayload == sPBpayload, f"parsed payload: {parsedPayload} is not matching original payload: {sPBpayload}"

    parsedMetrics_list: list = Spb2UNSPublisher.getMetricsListFromPayload(
        sPBpayload.SerializeToString())
    assert len(parsedMetrics_list) == len(metrics_list)
    for (parsed_metric, org_metric) in zip(parsedMetrics_list, metrics_list):
        name = parsed_metric.name
        alias = parsed_metric.alias
        datatype = parsed_metric.datatype
        value = getattr(parsed_metric,
                        Spb2UNSPublisher.SPB_DATATYPE_KEYS.get(datatype))

        assert name == org_metric[0] and alias == org_metric[
            1] and datatype == org_metric[2]
        if (datatype == sparkplug_b_pb2.Float
                or datatype == sparkplug_b_pb2.Double):
            # Need to handle floating point issue in Python
            assert round(value, 5) == round(org_metric[3], 5)
        else:
            assert value == org_metric[3]

        assert parsed_metric.timestamp is not None and parsed_metric.timestamp > 0


@pytest.mark.parametrize("spbContext", [({
    "spBv1.0_group_id": "grp1",
    "spBv1.0_message_type": "DDATA",
    "spBv1.0_edge_node_id": "node1"
})])
@pytest.mark.parametrize(
    "parsed_message, tag_name, metric_value, metric_timestamp, isHistorical, expected_uns_message ",
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
                "spBv1.0_edge_node_id": "node1"
            }),
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
                "spBv1.0_edge_node_id": "node1"
            }),
        (
            {
                "Grade": ("A", 1671008100,
                          True),  # Test Set 3 -String, with historical data
                "timestamp": 1671008100,
                "spBv1.0_group_id": "grp1",
                "spBv1.0_message_type": "DDATA",
                "spBv1.0_edge_node_id": "node1"
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
                "spBv1.0_edge_node_id": "node1"
            }),
    ])
def testExtractUNSMessageForTopic(parsed_message, tag_name, metric_value,
                                  metric_timestamp, isHistorical, spbContext,
                                  expected_uns_message):
    uns_msg = Spb2UNSPublisher.extractUNSMessageForTopic(
        parsed_message=parsed_message,
        tag_name=tag_name,
        metric_value=metric_value,
        metric_timestamp=metric_timestamp,
        isHistorical=isHistorical,
        spbContext=spbContext)
    assert uns_msg == expected_uns_message


@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("protocol", [(Uns_MQTT_ClientWrapper.MQTTv5),
                                      (Uns_MQTT_ClientWrapper.MQTTv311)])
@pytest.mark.parametrize("transport,host, port, tls",
                         [("tcp", "broker.emqx.io", 1883, None)])
@pytest.mark.parametrize("qos", [(1), (2)])
@pytest.mark.parametrize("reconnect_on_failure", [(True)])
def test_publishToUNS_not_connected(clean_session, protocol, transport, host,
                                    port, tls, qos, reconnect_on_failure):
    """
    See Spb2UNSPublisher#init()
    """
    uns_client: Uns_MQTT_ClientWrapper = Uns_MQTT_ClientWrapper(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=clean_session,
        userdata=None,
        protocol=protocol,
        transport=transport,
        reconnect_on_failure=reconnect_on_failure)
    # Connection not made to broker
    spg2unPub = Spb2UNSPublisher(uns_client)
    all_uns_messages: dict = {
        "a/b/c": {
            "temperature": 28.0,
            123: "testing value",
            "pressure": 10.12
        },
        "x/y/z": {
            "temperature": 28.0,
            123: "testing value",
            "pressure": 10.12
        }
    }
    with pytest.raises(ConnectionError):
        spg2unPub.publishToUNS(all_uns_messages)


@pytest.mark.parametrize("clean_session", [(True), (False)])
@pytest.mark.parametrize("protocol", [(Uns_MQTT_ClientWrapper.MQTTv5),
                                      (Uns_MQTT_ClientWrapper.MQTTv311)])
@pytest.mark.parametrize("transport,host, port, tls",
                         [("tcp", "broker.emqx.io", 1883, None)])
@pytest.mark.parametrize("qos", [(1), (2)])
@pytest.mark.parametrize("reconnect_on_failure", [(True)])
@pytest.mark.parametrize("all_uns_messages", [({
    "a/b/c": {
        "temperature": 28.0,
        123: "testing value",
        "pressure": 10.12
    },
    "x/y/z": {
        "temperature": 28.0,
        78945.12: "Can I have different keys?",
        "my metric": 200
    }
})])
def test_publishToUNS_connected(clean_session, protocol, transport, host, port,
                                tls, qos, reconnect_on_failure,
                                all_uns_messages):
    """
    See Spb2UNSPublisher#publishToUNS()
    """
    msg_published = []
    uns_client: Uns_MQTT_ClientWrapper = Uns_MQTT_ClientWrapper(
        client_id=f"spBv1.0_mapper_tester_{time.time()}",
        clean_session=clean_session,
        userdata=None,
        protocol=protocol,
        transport=transport,
        reconnect_on_failure=reconnect_on_failure)

    spg2unPub = Spb2UNSPublisher(uns_client)

    def on_publish(client, userdata, result):
        msg_published.append(True)
        print(f"{client} successfully published to {host} ")
        if (len(msg_published) == len(all_uns_messages)):
            client.disconnect()

    def on_connect(client, userdata, flags, rc, properties=None):
        print(f"{client} successfully connected to {host} ")
        spg2unPub.publishToUNS(all_uns_messages)

    uns_client.on_connect = on_connect
    uns_client.on_publish = on_publish
    try:
        uns_client.run(host=host,
                       port=port,
                       tls=tls,
                       topics="spBv1.0",
                       qos=qos)
        uns_client.loop_forever()
    except Exception as ex:
        pytest.fail, f"Exception occurred: {ex}"
    finally:
        uns_client.loop_stop()
        uns_client.disconnect()

    assert len(msg_published) == len(
        all_uns_messages), "Not all messages were published"
