from unittest.mock import MagicMock, patch

import psutil
import psutil._common
import pytest

from uns_spb_mapper import health_check
from uns_spb_mapper.sparkplugb_enc_config import MQTTConfig

# Get MQTT configuration
mqtt_host = MQTTConfig.host
mqtt_port = MQTTConfig.port


def test_check_process():
    with patch("psutil.process_iter") as mock_process_iter:
        uns_spb_mapper_process = MagicMock(spec=psutil.Process, autospec=True)
        uns_spb_mapper_process.info = {"cmdline": ["python", "uns_spb_mapper"]}
        mock_process_iter.return_value = [
            MagicMock(),
            uns_spb_mapper_process,
            MagicMock(),
        ]
        assert health_check.check_process("uns_spb_mapper")
        assert not health_check.check_process("not_running")


@pytest.mark.parametrize(
    "host_ip, host, port,match_conn",
    [
        ("127.0.0.1", mqtt_host, mqtt_port, True),
        ("127.0.0.1", mqtt_host, mqtt_port, False),
        ("172.0.0.2", "uns_mqtt", mqtt_port, True),
        ("172.0.0.2", "uns_mqtt", mqtt_port, False),
    ],
)
def test_check_existing_connection(host_ip: str, host: str | None, port: int, match_conn: bool):
    with patch("socket.gethostbyname") as mock_socket, patch("psutil.net_connections") as mock_net_connections:
        mock_socket.return_value = host_ip
        # cSpell:ignore raddr sconn
        mock_conn = MagicMock(psutil._common.sconn, autospec=True)
        mock_conn.status = "ESTABLISHED"
        # Match connection based based on match_conn value
        if match_conn:
            mock_conn.raddr.port = port
            mock_conn.raddr.ip = host_ip

        mock_net_connections.return_value = [
            MagicMock(psutil._common.sconn, autospec=True),
            mock_conn,
            MagicMock(psutil._common.sconn, autospec=True),
        ]
        assert health_check.check_existing_connection(host, port) == match_conn


@pytest.mark.parametrize(
    "process_info, remote_host_port_list,sys_err_ext_count",
    [
        ({"cmdline": ["python", "uns_spb_mapper"]},
         [(mqtt_host, mqtt_port)], 0),
        ({"cmdline": ["python", "something else"]},
         [(mqtt_host, mqtt_port)], 1),
        ({"cmdline": ["python", "uns_spb_mapper"]}, [], 1),
        ({"cmdline": ["python", "anything"]}, [], 2),
    ],
)
def test_main_multiple_scenarios(process_info: dict, remote_host_port_list: list[set], sys_err_ext_count: int):
    """
    process_info: should be a dict[str,list[str]] if the list contains the string uns_spb_mapper to mimic process names
    remote_host_port_list: list of host,port tuple to mimic service with successful connections
    sys_err_ext_count: count of expected calls to sys.exit(1)
                       if 0 then no erroneous exits and only sys.exit(0) was called
    """
    with patch("sys.exit") as mock_exit, patch("psutil.process_iter") as mock_process_iter, patch(
            "psutil.net_connections") as mock_net_connections, patch("socket.gethostbyname") as mock_socket:
        # mock the historian listener  process
        mock_spb_mapper_process = MagicMock(spec=psutil.Process, autospec=True)
        mock_spb_mapper_process.info = process_info
        mock_process_iter.return_value = [
            mock_spb_mapper_process,
        ]
        mock_socket.return_value = "::1"          # mocking ip to localhost
        # mock the services connected to process based in test params
        mock_conn_list = []
        for (host, port) in remote_host_port_list:
            mock_socket.gethostbyname.return_value = host
            mock_conn = MagicMock(psutil._common.sconn, autospec=True)
            mock_conn.status = "ESTABLISHED"
            mock_conn.raddr.port = port
            mock_conn.raddr.ip = host
            mock_conn_list.append(mock_conn)
        mock_net_connections.return_value = mock_conn_list
        health_check.main()
        assert mock_exit.call_count == sys_err_ext_count + 1
        for i, call in enumerate(mock_exit.call_args_list):
            if i == sys_err_ext_count:  # the last call would have returned 0
                assert call.args[0] == 0
            else:
                assert call.args[0] == 1