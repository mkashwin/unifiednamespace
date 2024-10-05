import logging
import socket
import sys

import psutil

from uns_graphql.graphql_config import GraphDBConfig, HistorianConfig, KAFKAConfig, MQTTConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_process(name: str) -> bool:
    """Check if the process is running."""
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        cmdline = proc.info.get("cmdline", [])
        if any(name in " ".join(cmdline) for part in cmdline):
            return True
    return False


def check_listening_port(port: int) -> bool:
    """Check if the current server is listening on the specified port"""
    try:
        # Get all active network connections
        connections = psutil.net_connections("inet")

        # Check if any connection matches the resolved IP and port
        for conn in connections:
            # cSpell:ignore laddr
            if conn.status == "LISTEN" and conn.laddr and conn.laddr.port == port:
                return True
        # Return False if no matching connection is found
        return False
    except Exception as ex:
        logger.error(ex)
        return False


def check_connection_possible(host: str, port: int) -> bool:
    """
    Check if a connection to the specified host and port can be established
    GraphQL server performs laze loading
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return sock.connect_ex((host, port)) == 0
    except Exception as ex:
        logger.error(ex)
        return False


def main():
    """
    Healthcheck script.
    Call with cmd parameters  --port <port> to specify the port to check
    Default port is 8000
    """
    # get port from command line arg --port 8000
    graphql_port = 8000  # Default values
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--port":
        graphql_port = int(args[1])

    if not check_process("uvicorn"):
        sys.exit(1)

    #  check if the uvicorn server is running?
    if not check_listening_port(port=graphql_port):
        sys.exit(1)

    # Get MQTT configuration
    mqtt_host = MQTTConfig.host
    mqtt_port = MQTTConfig.port

    if not check_connection_possible(mqtt_host, mqtt_port):
        sys.exit(1)

    # Get Kafka configuration
    kafka_url: str = KAFKAConfig.config_map.get("bootstrap.servers")
    if "://" in kafka_url:
        kafka_url = kafka_url.split("://")[1]  # Remove the protocol
    host_port = kafka_url.split(":")
    kafka_host: str = host_port[0]
    kafka_port: str | None = host_port[1] if len(host_port) > 1 else ""  # Get port
    if not check_connection_possible(kafka_host, int(kafka_port)):
        sys.exit(1)

    # Get GraphDB configuration
    graphdb_url = GraphDBConfig.conn_url

    # Split the GraphDB URL to extract the host and port
    if "://" in graphdb_url:
        graphdb_url = graphdb_url.split("://")[1]  # Remove the protocol
    host_port = graphdb_url.split(":")
    graphdb_host: str = host_port[0]
    graphdb_port: str | None = host_port[1] if len(host_port) > 1 else ""  # Get port
    if not check_connection_possible(graphdb_host, int(graphdb_port)):
        sys.exit(1)

    # Get Historian configuration
    historian_host: str = HistorianConfig.hostname
    historian_port: int = HistorianConfig.port if HistorianConfig.port else 5432

    if not check_connection_possible(historian_host, int(historian_port)):
        sys.exit(1)

    logger.info("Health check passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
