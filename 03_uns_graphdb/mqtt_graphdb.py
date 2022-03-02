import random
import time
from neo4j import GraphDatabase
import json
import paho.mqtt.client as mqtt_client


#read these values from the configuration file 
broker = ''
port = ''
topic = "#"
qos = 1
keep_alive = 60
# generate client ID with pub prefix randomly 
client_id = f'historian-{random.randint(0, 1000)}'
username = ''
password = ''



def on_connect(client, userdata, flags, rc):

	# TODO replace these print statement with logger
	print(
			"{"
			f"Client: {client},"
			f"Userdata: {userdata},"
			f"Flags: {flags},"
			f"rc: {rc}"
			"}" 
		)
	#subscribe to the topic only if connection was successful
	historian_client.subscribe(topic, qos)
	# TODO Error handling
	print( f"Successfully connect {historian_client} to MQTT Broker at {broker}:{port}")

def on_subscribe(client: mqtt_client):
	print( f"Successfully connect {historian_client} to Topic {topic} with QOS {qos} ")


def on_message(client, userdata, msg):
	print("")


# create historian mqtt client
historian_client = mqtt_client.Client()

# Assign event callbacks
historian_client.on_connect = on_connect
historian_client.on_subscribe = on_subscribe
historian_client.on_message = on_message

# Connect
historian_client.connect(broker, int(port), int(keep_alive))

# Continue the network loop
historian_client.loop_forever()


class UNSCurrentView:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()
    
    #TODO:  Itereage teh topics by '/'. create node for each level and merge the messages to the final node   
    def persistMQTTmsg(topic,message):
        # TODO Error handling
        node_type = ["ENTERPRISE", "FACILITY","AREA", "LINE","DEVICE" ]
        nodes = topic.split('/')
        count = 0
        lastnode = null
        for node in nodes:
            # TODO Logger
            print(node)
            
            # refer https://stackoverflow.com/questions/35255540/neo4j-add-update-properties-if-node-exists
            # TODO create create or merge node in database. 
            # save the last node name to ensure that we are able to insert / merge attributes of the message into that node
            ## MERGE (node)
            if(count == int(nodes.length)):
                attributes = json.loads(message)
                ## MERGE (node,)
                print (attributes)
                for attribute in attributes:
                    # TODO create create or merge attributes in the last note
                    print(attribute) 
            lastnode = node