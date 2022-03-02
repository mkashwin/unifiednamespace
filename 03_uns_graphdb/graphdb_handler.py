from neo4j import GraphDatabase
from config import settings
import json

class UNSCurrentView:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # TODO:  Itereage teh topics by '/'. create node for each level and merge the messages to the final node
    def persistMQTTmsg(topic, message):
        # TODO Error handling
        node_type = ["ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE"]
        nodes = topic.split('/')
        count = 0
        lastnode 
        for node in nodes:
            # TODO Logger
            print(node)

            # refer https://stackoverflow.com/questions/35255540/neo4j-add-update-properties-if-node-exists
            # TODO create create or merge node in database.
            # save the last node name to ensure that we are able to insert / merge attributes of the message into that node
            ## MERGE (node)
            if(count == int(nodes.length)):
                attributes = json.loads(message)
                # FIXME node_type length must be >= nodes.length. if not decide how to handle
                ## MERGE (node:node_type[count],attributes)
                print(attributes)
                for attribute in attributes:
                    # TODO create create or merge attributes in the last note
                    print(attribute)
            lastnode = node
