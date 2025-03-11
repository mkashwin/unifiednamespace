from unittest.mock import MagicMock, patch

import psutil
import psutil._common
import pytest

import uns_graphql.health_check as health_check
from uns_graphql.graphql_config import GraphDBConfig, HistorianConfig, KAFKAConfig, MQTTConfig


def test_check_process():
    with patch("psutil.process_iter") as mock_process_iter:
        mock_uvicorn_process = MagicMock(spec=psutil.Process, autospec=True)
        mock_uvicorn_process.info = {"cmdline": ["python", "uvicorn", "uns_graphql.uns_graphql_app:UNSGraphql.app"]}
        mock_process_iter.return_value = [
            MagicMock(),
            mock_uvicorn_process,
            MagicMock(),
        ]
        assert health_check.check_process("uvicorn")
        assert not health_check.check_process("not_running")


def test_check_listening_port():
    port_positive_test = 9000
    port_negative_test = 9900
    with patch("psutil.net_connections") as mock_net_connections:
        # cSpell:ignore laddr sconn
        mock_conn = MagicMock(psutil._common.sconn, autospec=True)
        mock_conn.status = "LISTEN"
        mock_conn.laddr.port = port_positive_test
        mock_net_connections.return_value = [
            MagicMock(psutil._common.sconn, autospec=True),
            mock_conn,
            MagicMock(psutil._common.sconn, autospec=True),
        ]
        assert health_check.check_listening_port(port=port_positive_test)
        assert not health_check.check_listening_port(port=port_negative_test)


def test_check_connection_possible():
    with patch("socket.socket") as mock_socket:
        mock_socket.return_value.connect_ex.return_value = 0
        assert health_check.check_connection_possible("host", 8000)


def test_check_connection_possible_neg():
    with patch("socket.socket") as mock_socket:
        mock_socket.return_value.connect_ex.return_value = -1
        assert not health_check.check_connection_possible("host", 8000)


# ports defined in the configuration
mqtt_conn_port = MQTTConfig.port
neo4j_conn_port = int(GraphDBConfig.conn_url.split("://")[1].split(":")[1])
postgres_conn_port = HistorianConfig.port if HistorianConfig.port else 5432

# Get KAFKA configuration
kafka_host_port_list: list = [(url.split(":")[0], int(url.split(":")[1]))
                              for url in KAFKAConfig.config_map.get("bootstrap.servers").split(",")]


@pytest.mark.parametrize(
    "args, port",
    [
        (["health_check.py", "--port", "9000"], 9000),
        (["health_check.py", "--port", "8000"], 8000),
        (["health_check.py"], 8000),
    ],
)
def test_main_positive(args: list[str], port: int):
    with patch("sys.argv", args), patch("sys.exit") as mock_exit, patch("psutil.process_iter") as mock_process_iter, patch(
        "socket.socket"
    ) as mock_socket, patch("psutil.net_connections") as mock_net_connections:
        # mock the uvicorn process
        mock_uvicorn_process = MagicMock(spec=psutil.Process, autospec=True)
        mock_uvicorn_process.info = {"cmdline": ["python", "uvicorn", "uns_graphql.uns_graphql_app:UNSGraphql.app"]}
        mock_process_iter.return_value = [
            mock_uvicorn_process,
        ]
        # mock the uvicorn process listening on specified port
        # cSpell:ignore laddr sconn
        mock_uvicorn_conn = MagicMock(psutil._common.sconn, autospec=True)
        mock_uvicorn_conn.status = "LISTEN"
        mock_uvicorn_conn.laddr.port = port
        mock_net_connections.return_value = [
            MagicMock(psutil._common.sconn, autospec=True),
            mock_uvicorn_conn,
            MagicMock(psutil._common.sconn, autospec=True),
        ]
        mock_net_connections.return_value = [
            mock_uvicorn_conn,
        ]

        # mock socket reachability
        def mock_connect_ex(addr):
            host, port = addr
            if port in (mqtt_conn_port, neo4j_conn_port, postgres_conn_port, *tuple(
                kafka_port for kafka_host, kafka_port in kafka_host_port_list)):
                return 0  # Simulate successful connection for matching ports
            return 1  # Simulate failure for other ports

        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.connect_ex.side_effect = mock_connect_ex

        health_check.main()
        mock_exit.assert_called_once_with(0)


@pytest.mark.parametrize(
    "args, port",
    [
        (["health_check.py", "--port", "9000"], 9000),
        (["health_check.py", "--port", "8000"], 8000),
        (["health_check.py"], 8000),
    ],
)
@pytest.mark.parametrize(
    "process_info, uvicorn_running, reachable_ports, sys_err_ext_count",
    [
        (
            {"cmdline": ["python", "uvicorn", "uns_graphql.uns_graphql_app:UNSGraphql.app"]},
            True,
            (mqtt_conn_port, neo4j_conn_port, postgres_conn_port,
             *tuple(kafka_port for kafka_host, kafka_port in kafka_host_port_list)),
            0,
        ),  # health green everything is working
        (
            {"cmdline": ["python", "something", "uns_graphql.uns_graphql_app:UNSGraphql.app"]},
            True,
            (mqtt_conn_port, neo4j_conn_port, postgres_conn_port,
             *tuple(kafka_port for kafka_host, kafka_port in kafka_host_port_list)),
            1,
        ),  # No service called uvicorn is running
        (
            {"cmdline": ["python", "something", "uns_graphql.uns_graphql_app:UNSGraphql.app"]},
            False,
            (mqtt_conn_port, neo4j_conn_port, postgres_conn_port,
             *tuple(kafka_port for kafka_host, kafka_port in kafka_host_port_list)),
            2,
        ),  # No service called uvicorn is running, No service running on the port
        (
            {"cmdline": ["python", "uvicorn", "uns_graphql.uns_graphql_app:UNSGraphql.app"]},
            False,
            (mqtt_conn_port, neo4j_conn_port, postgres_conn_port,
             *tuple(kafka_port for kafka_host, kafka_port in kafka_host_port_list)),
            1,
        ),  # Uvicorn service isn't running on the port
        (
            {"cmdline": ["python", "uvicorn", "uns_graphql.uns_graphql_app:UNSGraphql.app"]},
            True,
            (neo4j_conn_port, postgres_conn_port, *tuple(kafka_port for kafka_host, kafka_port in kafka_host_port_list)),
            1,
        ),  # No connectivity to MQTT server
        (
            {"cmdline": ["python", "uvicorn", "uns_graphql.uns_graphql_app:UNSGraphql.app"]},
            True,
            (neo4j_conn_port, postgres_conn_port),
            2,
        ),  # No connectivity to MQTT server & Kafka server
        (
            {"cmdline": ["python", "uvicorn", "uns_graphql.uns_graphql_app:UNSGraphql.app"]},
            True,
            (mqtt_conn_port, postgres_conn_port, *tuple(kafka_port for kafka_host, kafka_port in kafka_host_port_list)),
            1,
        ),  # No connectivity to Neo4j server
        (
            {"cmdline": ["python", "uvicorn", "uns_graphql.uns_graphql_app:UNSGraphql.app"]},
            True,
            (mqtt_conn_port, *tuple(kafka_port for kafka_host, kafka_port in kafka_host_port_list)),
            2,
        ),  # No connectivity to Neo4j servers and  timescaledb
        (
            {"cmdline": ["python", "uvicorn", "uns_graphql.uns_graphql_app:UNSGraphql.app"]},
            True,
            (),
            4,
        ),  # No connectivity to any servers
    ],
)
def test_main_multiple_scenarios(
    args: str, port: int, process_info: dict, uvicorn_running: bool, reachable_ports: set[int], sys_err_ext_count
):
    """
    args: command line params sent to health_check. should either be null of of the for --port <port>
    port: the port on which uvicorn server is expected to be running
    process_info: should be a dict[str,list[str]] if the list contains the string uvicorn to mimic process names
    uvicorn_running: boolean flag to indicate to the uvicorn process is listening th the mention port,
    reachable_ports: set of ports which mocked process should listen to
    sys_err_ext_count: count of expected calls to sys.exit(1)
                       if 0 then no erroneous exits and only sys.exit(0) was called
    """
    with patch("sys.argv", args), patch("sys.exit") as mock_exit, patch("psutil.process_iter") as mock_process_iter, patch(
        "socket.socket"
    ) as mock_socket, patch("psutil.net_connections") as mock_net_connections:
        # mock the uvicorn process
        mock_uvicorn_process = MagicMock(spec=psutil.Process, autospec=True)
        mock_uvicorn_process.info = process_info
        mock_process_iter.return_value = [
            mock_uvicorn_process,
        ]
        # mock the uvicorn process listening on specified port
        # cSpell:ignore laddr sconn
        mock_uvicorn_conn = MagicMock(psutil._common.sconn, autospec=True)
        mock_uvicorn_conn.status = "LISTEN"
        if uvicorn_running:  # dont provide the port in the mock if the test scenario needs to check uvicorn not running
            mock_uvicorn_conn.laddr.port = port
        mock_net_connections.return_value = [
            MagicMock(psutil._common.sconn, autospec=True),
            mock_uvicorn_conn,
            MagicMock(psutil._common.sconn, autospec=True),
        ]
        mock_net_connections.return_value = [
            mock_uvicorn_conn,
        ]
        # mock socket reachability

        def mock_connect_ex(addr):
            host, port = addr
            if port in reachable_ports:
                return 0  # Simulate successful connection for matching ports
            return 1  # Simulate failure for other ports

        mock_socket_instance = mock_socket.return_value
        mock_socket_instance.connect_ex.side_effect = mock_connect_ex
        # Since we are mocking the sys.exit call, the flow does not break
        # therefore we check if the number of incorrect states matches the expected sys.exit(1) calls
        health_check.main()
        assert mock_exit.call_count == sys_err_ext_count + 1
        for i, call in enumerate(mock_exit.call_args_list):
            if i == sys_err_ext_count:  # the last call would have returned 0
                assert call.args[0] == 0
            else:
                assert call.args[0] == 1
