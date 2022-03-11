import random
import logging
import time
import paho.mqtt.client as mqtt_client

from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes

from config import settings
from graphdb_handler import GraphDBHandler

# read these values from the configuration file
mqtt_host: str = settings.mqtt["host"]
mqtt_port: int = settings.get("mqtt.port", 1883)
keepalive: int = settings.get("mqtt.keep_alive", 60)

transport: str = settings.get("mqtt.transport", "tcp")
mqtt_version_code: int = settings.get("mqtt.version", mqtt_client.MQTTv5)
qos: int = settings.get("mqtt.qos", 1)
reconnect_on_failure: bool = settings.get("mqtt.reconnect_on_failure", True)
clean_session: bool = settings.get("mqtt.clean_session", None)

topic: str = settings.get("mqtt.topic", "#")
# generate client ID with pub prefix randomly
client_id = f'graphdb- { time.time()}-{random.randint(0, 1000)}'
mqtt_username: str = settings.mqtt["username"]
mqtt_password: str = settings.mqtt["password"]
mqtt_isSSL: bool = settings.get("mqtt.isSSL", False)

graphdb_url: str = settings.graphdb["url"]
graphdb_user: str = settings.graphdb["username"]

graphdb_password: str = settings.graphdb["password"]
# if we want to use a database different from the default
graphdb_database: str = settings.get("graphdb.database", None)

LOGGER = logging.getLogger(__name__)


def on_connect(client, userdata, flags, rc, properties=None):

    LOGGER.debug(
        f"{{Client: {client}, Userdata: {userdata},Flags: {flags}, rc: {rc}  }}"
    )
    if (rc == 0):
        LOGGER.debug("Connection established. Returned code=", rc)
        # subscribe to the topic only if connection was successful
        client.connected_flag = True
        mqtt_graphdb_client.subscribe(topic,
                                      qos,
                                      options=None,
                                      properties=properties)

        LOGGER.info(
            f"Successfully connect {mqtt_graphdb_client} to MQTT Broker at {transport}:{mqtt_host}:{mqtt_port}"
        )
    else:
        LOGGER.error("Bad connection. Returned code=", rc)
        client.bad_connection_flag = True


def on_subscribe(client: mqtt_client,
                 userdata,
                 mid,
                 granted_qos,
                 properties=None):
    LOGGER.info(
        f"Successfully connect {mqtt_graphdb_client} to Topic {topic} with QOS {granted_qos} "
    )
    ##TODO


def on_message(client, userdata, msg):
    LOGGER.debug("{"
                 f"Client: {client},"
                 f"Userdata: {userdata},"
                 f"Message: {msg},"
                 "}")
    ## Connect to the database
    try:
        graph_db_handler = GraphDBHandler(graphdb_url, graphdb_user,
                                          graphdb_password)
        ## parse message and topic
        ## save message
        graph_db_handler.persistMQTTmsg(msg.topic, msg.payload.decode("utf-8"),
                                        graphdb_database)
        ## disconnect from db
        graph_db_handler.close()
    except Exception as ex:
        LOGGER.error(ex)


# create graphdb mqtt client
mqtt_graphdb_client = mqtt_client.Client(
    client_id=client_id,
    clean_session=clean_session,
    userdata=None,
    protocol=mqtt_version_code,
    transport=transport,
    reconnect_on_failure=reconnect_on_failure)
if (mqtt_isSSL):
    ##TODO Configure certificates for SSL communication
    LOGGER.debug("Connection with MQTT Broker is over SSL")
mqtt_graphdb_client.username_pw_set(mqtt_username, mqtt_password)
# Assign event callbacks
mqtt_graphdb_client.on_connect = on_connect
mqtt_graphdb_client.on_subscribe = on_subscribe
mqtt_graphdb_client.on_message = on_message

# Connect
try:
    properties = None
    if (mqtt_version_code == mqtt_client.MQTTv5):
        properties = Properties(PacketTypes.CONNECT)
    mqtt_graphdb_client.connect(host=mqtt_host,
                                port=mqtt_port,
                                keepalive=keepalive,
                                properties=properties)
except Exception as ex:
    LOGGER.error("Unable to connect to MQTT broker", ex)
    exit(1)

# Continue the network loop
mqtt_graphdb_client.loop_forever()
