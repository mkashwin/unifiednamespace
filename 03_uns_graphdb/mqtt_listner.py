import random
import logging

import paho.mqtt.client as mqtt_client
from config import settings
from graphdb_handler import GraphDBHandler


# read these values from the configuration file
mqtt_broker = settings.mqtt["broker_url"]
topic = settings.mqtt["topic"]
qos = settings.mqtt["qos"]
keep_alive = settings.mqtt["keep_alive"]
# generate client ID with pub prefix randomly
client_id = f'graphdb-{random.randint(0, 1000)}'
mqtt_username = settings.mqtt["username"]
mqtt_password = settings.mqtt["password"]


graphdb_url = settings.graphdb["url"]
graphdb_user = settings.graphdb["username"]

graphdb_password = settings.graphdb["password"]

LOGGER = logging.getLogger(__name__)

def on_connect(client, userdata, flags, rc):
    # TODO replace these print statement with logger
    LOGGER.debug(
        "{"
        f"Client: {client},"
        f"Userdata: {userdata},"
        f"Flags: {flags},"
        f"rc: {rc}"
        "}"
    )
    # subscribe to the topic only if connection was successful
    graphdb_client.subscribe(topic, qos)
    # TODO Error handling
    LOGGER.info( f"Successfully connect {graphdb_client} to MQTT Broker at {mqtt_broker}")


def on_subscribe(client: mqtt_client):
    LOGGER.info(f"Successfully connect {graphdb_client} to Topic {topic} with QOS {qos} ")


def on_message(client, userdata, msg):
    LOGGER.debug(
        "{"
        f"Client: {client},"
        f"Userdata: {userdata},"
        f"Message: {msg},"
        "}"
    )
    ## Connect to the database
    try :
        graph_db_handler = GraphDBHandler(graphdb_url,graphdb_user,graphdb_password)
        ## parse message and topic 
        ## save message
        graph_db_handler.persistMQTTmsg(msg.topic,msg)
        ## disconnect from db
        graph_db_handler.close()
    except Exception as ex:
        LOGGER.error(ex)



# create graphdb mqtt client
graphdb_client = mqtt_client.Client()

# Assign event callbacks
graphdb_client.on_connect = on_connect
graphdb_client.on_subscribe = on_subscribe
graphdb_client.on_message = on_message

# Connect
graphdb_client.connect(mqtt_broker, int(keep_alive))

# Continue the network loop
graphdb_client.loop_forever()


