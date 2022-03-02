import random
import logging

import paho.mqtt.client as mqtt_client
from config import settings


# read these values from the configuration file
mqtt_broker = settings.mqtt["broker_url"]
mqtt_port = settings.mqtt["port"]
topic = settings.mqtt["topic"]
qos = settings.mqtt["qos"]
keep_alive = settings.mqtt["keep_alive"]
# generate client ID with pub prefix randomly
client_id = f'graphdb-{random.randint(0, 1000)}'
username = settings.mqtt["username"]
password = settings.mqtt["password"]

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
    LOGGER.info( f"Successfully connect {graphdb_client} to MQTT Broker at {mqtt_broker}:{mqtt_port}")


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
    ##Conntect to the database
    ## parse message and topic 
    ## save message
    ## disconnect from db


# create historian mqtt client
graphdb_client = mqtt_client.Client()

# Assign event callbacks
graphdb_client.on_connect = on_connect
graphdb_client.on_subscribe = on_subscribe
graphdb_client.on_message = on_message

# Connect
graphdb_client.connect(mqtt_broker, int(mqtt_port), int(keep_alive))

# Continue the network loop
graphdb_client.loop_forever()


