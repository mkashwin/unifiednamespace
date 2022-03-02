# import the neo4j driver for Python
from asyncio.windows_events import NULL
from neo4j import GraphDatabase
import json
import requests

# Database Credentials
# FIXME Need to read these secrets from Kubernetes
uri             = "" #TBD
userName        = "" #TBD
password        = "" #TBD
#
#    with open("/var/openfaas/secrets/graphdb-key") as f:
#        password = f.read().strip()
#Extract the topic 
topic=""
#Extract the msg in JSON format
msg=""

def handle(request):
    """handle a request to the function
    Args:
        req (str): request body
    """




    print(request)
    return request

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
        lastnode = NULL
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
        
        

