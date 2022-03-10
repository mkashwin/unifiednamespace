from config import settings
import neo4j
import json
import logging

LOGGER = logging.getLogger(__name__)
_NODE_TYPES = settings.graphdb["node_types"]


class GraphDBHandler:

    def __init__(self, uri : str, user  : str, password : str):
        ## TODO support other authentications like cert based authentication
        try:
            self.driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:
            LOGGER.error("Failed to create the driver:", e)

    def close(self):
        if self.driver is not None:
            self.driver.close()

    def persistMQTTmsg(self, topic: str, message: str):
        """
        Iterate the topics by '/'. create node for each level and merge the messages to the final node
        For the other topics in the hierarchy a node will be created / merged and linked to the parent topic node
        Parameters
        ----------
        topic: str
            The topic on which the message was sent
        message: str 
            The MQTT message. String is expected to be a JSON
        """
        nodes = topic.split('/')
        count = 0
        lastnode = None
        with self.driver.session() as session:
            try:
                for node in nodes:
                    # TODO improve logger message
                    LOGGER.debug(node)
                    response = None
                    jsonStr = None
                    if (count == int(nodes.length)):
                        ## Save the message only for the leaf node
                        jsonStr = message

                    if (count < _NODE_TYPES.length):
                        response = GraphDBHandler._saveNode(session, node,
                                                  _NODE_TYPES[count], jsonStr)
                    else:
                        response = GraphDBHandler._saveNode(
                            session, node,
                            f"{_NODE_TYPES[_NODE_TYPES.length]}_count", jsonStr)
                    count += 1
                    lastnode = node
            except Exception as ex:
                LOGGER.error(ex)
            finally:
                if session is not None:
                    session.close()
            return response

    @staticmethod
    def _saveNode(session : neo4j.Session, nodename: str, nodetype: str, message=None):
        """
        Creates or Merges the MQTT message as a Graph node. Each level of the topic is also persisted 
        as a graph node with appropriate parent relationship
        Parameters
        ----------
        session 
            Neo4j session object
        nodename : str
            Trimmed name of the topic
        nodetype : str
            Based on ISA-95 part 2 the nested depth of the topic determines the node type. 
            Also see settings.yaml graphdb.node_types
        @message  The JSON string delivered as message in the MQTT payload. Defaults to null
        """
        attributes = r'{ }'
        LOGGER.debug(
            f"Saving node:{nodename} of type:{nodetype} and message:{message}")
        if (message is not None):
            ## FIXME: Neo4j supports only flat messages. also the json.load does not remove quotes around the keys of the dict
            ## Also need to ensure that the message doesn't contain any attribute with the name "node_name"
            attributes = GraphDBHandler._flatten_json_for_Neo4J(message)
        return session.run("MERGE (node:$nodetype { node_name: $nodename }) "
                           "SET node += $attributes"
                           "RETURN node",nodetype=nodetype)

    @staticmethod
    def _flatten_json_for_Neo4J(message) -> str:
        LOGGER.debug(message)
        output={}
        
        def flatten(json_object, name=''):
            if type(json_object) is dict:
                for items in json_object:
                    flatten(json_object[items], name + items + '_')
            elif type(json_object) is list:
                i = 0
                for items in json_object:
                    flatten(items, name + str(i) + '_')
                    i += 1
            else:
                output[name[:-1]] = json_object

        flatten(message)
        string_output = "{"
        for key, value in output.items():
            LOGGER.debug(key,value)
            string_output += f" {key} : \"{value}\" ,"
        string_output =string_output[:-1] + " }"
        return string_output
