import time
import neo4j
import logging
from neo4j import exceptions

# Logger
LOGGER = logging.getLogger(__name__)


class GraphDBHandler:

    def __init__(self,
                 uri: str,
                 user: str,
                 password: str,
                 database: str = neo4j.DEFAULT_DATABASE,
                 node_types: tuple = ("ENTERPRISE", "FACILITY", "AREA", "LINE",
                                      "DEVICE"),
                 MAX_RETRIES: int = 5,
                 SLEEP_BTW_ATTEMPT: float = 10):
        """
        uri: str
            Full URI to the Neo4j database including protocol, server name and port
        user : str
            db user name. Must have write access on the Neo4j database also specified here
        password:
            password for the db user
        database : str = neo4j.DEFAULT_DATABASE
            The Neo4j database in which this data should be persisted
        node_types : tuple [str]
            Configuration for Node Labels to be used for the topics based on topic hierarchy
            Default value is ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE")

        MAX_RETRIES: int
                Must be a positive integer. Default value is 5.
                Number of attempts after a failed database connection to retry connecting
        SLEEP_BTW_ATTEMPT: float
                Must be a positive float. Default value is 10 seconds. Seconds to sleep between retries
        """
        # TODO support additional secure authentication  methods
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        if [self.database is None]:
            self.database = ""
        self.NODE_TYPES = node_types
        self.MAX_RETRIES = MAX_RETRIES
        self.SLEEP_BTW_ATTEMPT = SLEEP_BTW_ATTEMPT
        self.driver = None
        try:
            self.connect()
        except Exception as ex:
            LOGGER.error("Failed to create the driver: %s",
                         str(ex),
                         stack_info=True,
                         exc_info=True)
            raise ex

    def connect(self, retry: int = 0):
        try:
            if (self.driver is None):
                self.driver = neo4j.GraphDatabase.driver(self.uri,
                                                         auth=(self.user,
                                                               self.password))
            self.driver.verify_connectivity()
        except (exceptions.DatabaseError, exceptions.TransientError,
                exceptions.DatabaseUnavailable,
                exceptions.ServiceUnavailable) as ex:
            if (retry >= self.MAX_RETRIES):
                LOGGER.error("No. of retries exceeded %s",
                             str(self.MAX_RETRIES),
                             stack_info=True,
                             exc_info=True)
                raise ex
            else:
                retry += 1
                LOGGER.error("Error Connecting to %s.\n Error: %s",
                             self.database,
                             str(ex),
                             stack_info=True,
                             exc_info=True)
                time.sleep(self.SLEEP_BTW_ATTEMPT)
                self.connect(retry=retry)

        except Exception as ex:
            LOGGER.error("Error Connecting to %s. Unable to retry. Error: %s",
                         self.database,
                         str(ex),
                         stack_info=True,
                         exc_info=True)
            raise ex
        return self.driver

    def close(self):
        if self.driver is not None:
            try:
                self.driver.close()
                self.driver = None
            except Exception as ex:
                LOGGER.error("Failed to close the driver:%s",
                             str(ex),
                             stack_info=True,
                             exc_info=True)

    def persistMQTTmsg(self,
                       topic: str,
                       message: dict,
                       timestamp: float = time.time(),
                       retry: int = 0):
        """
        Persists all nodes and the message as attributes to the leaf node
        ----------
        topic: str
            The topic on which the message was sent
        message: dict
            The JSON MQTT message payload in in dict format
        timestamp:
            timestamp for receiving the message
        """
        response = None
        attributes = None

        # Neo4j supports only flat messages.
        # Also need to ensure that the message doesn't contain any attribute with the name "node_name"
        if (message is not None):
            attributes = GraphDBHandler._flatten_json_for_Neo4J(message)
        try:
            with self.connect().session(
                    database=f"{self.database}") as session:
                response = session.write_transaction(self.save_all_nodes,
                                                     topic, attributes,
                                                     timestamp)
        except (exceptions.TransientError, exceptions.TransactionError) as ex:
            if (retry >= self.MAX_RETRIES):
                LOGGER.error("No. of retries exceeded %s",
                             str(self.MAX_RETRIES),
                             stack_info=True,
                             exc_info=True)
                raise ex
            else:
                retry += 1
                LOGGER.error(
                    "Error persisting \ntopic:%s \nmessage %s. on Error: %s",
                    topic,
                    str(message),
                    str(ex),
                    stack_info=True,
                    exc_info=True)
                time.sleep(self.SLEEP_BTW_ATTEMPT)
                self.persistMQTTmsg(topic=topic,
                                    message=message,
                                    timestamp=timestamp,
                                    retry=retry)
        return response

    # method  starts
    def save_all_nodes(self, session, topic: str, message: dict,
                       timestamp: float):
        """
        Iterate the topics by '/'. create node for each level and merge the messages to the final node
        For the other topics in the hierarchy a node will be created / merged and linked to the parent topic node
        Parameters
        ----------
        session :
            The Neo4j database session used for the write transaction
        topic: str
            The topic on which the message was sent
        message: dict
            The MQTT message in JSON format converted to a dict
        timestamp:
            timestamp for receiving the message
        """
        response = None
        count = 0
        lastnode = None
        nodes = topic.split('/')
        for node in nodes:
            LOGGER.debug(f"Processing sub topic:\"{node}\" of topic:{topic}")

            nodeAttributes = None
            if (count == len(nodes) - 1):
                # Save the attributes only for the leaf node
                nodeAttributes = message
            node_name: str = GraphDBHandler.getNodeName(count, self.NODE_TYPES)
            response = GraphDBHandler.saveNode(session, node, node_name,
                                               nodeAttributes, lastnode,
                                               timestamp)
            count += 1
            lastnode = node
        return response

    # method Ends

    # static method starts
    @staticmethod
    def getNodeName(current_depth: int, node_types: tuple) -> str:
        if (current_depth < len(node_types)):
            return node_types[current_depth]
        else:
            return f"{node_types[-1]}_depth_{current_depth - len(node_types)+ 1}"

    # static method ends

    # static Method Starts
    @staticmethod
    def saveNode(session: neo4j.Session,
                 nodename: str,
                 nodetype: str,
                 attributes: dict = None,
                 parent: str = None,
                 timestamp: float = time.time()):
        """
        Creates or Merges the MQTT message as a Graph node. Each level of the topic is also persisted
        as a graph node with appropriate parent relationship
        Parameters
        ----------
        session  : neo4j.Session
            Neo4j session object
        nodename : str
            Trimmed name of the topic
        nodetype : str
            Based on ISA-95 part 2 the nested depth of the topic determines the node type.
        message : dict
            The JSON delivered as message in the MQTT payload converted to a dict.
            Defaults to None (for all intermettent topics)
        parent  : str
            The name of the parent node to which a relationship will be established. Defaults to None(for root nodes)
        """
        LOGGER.debug(
            f"Saving node:{nodename} of type:{nodetype} and attributes:{attributes} with parent:{parent}"
        )

        # CQL doesn't allow  the node label as a parameter.
        # using a statement with parameters is a safer option against CQL injection
        query = f"MERGE (node:{nodetype} {{ node_name: $nodename }}) \n"
        query = query + "ON CREATE \n"
        query = query + "   SET node._created_timestamp = $timestamp \n"
        if (attributes is not None):
            query = query + "ON MATCH \n"
            query = query + "    SET node._modified_timestamp = $timestamp \n"
            query = query + "SET node += $attributes \n"

        if (parent is not None):
            query = "MATCH (parent {node_name: $parent})" + '\n' + query + '\n'
            query = query + "MERGE (parent) -[r:PARENT_OF]-> (node) \n"
            query = query + "RETURN node, parent"
        else:
            query = query + "RETURN node" ""
        LOGGER.debug(f"CQL statement to be executed: {query}")
        # non-referred would be ignored in the execution.
        node = session.run(query,
                           nodename=nodename,
                           timestamp=timestamp,
                           parent=parent,
                           attributes=attributes)
        return node

    # static Method Ends

    # static Method Starts
    @staticmethod
    def _flatten_json_for_Neo4J(mqtt_msg: dict) -> dict:
        """
        Utility methods to convert a nested JSON into a flat structure
        Keys for lists will be of the form <key>_<count>
        Keys for dicts will be of the form <parent key>_<child key>
        if any attribute is named "node_name" it will be replaced by "NODE_NAME"
        Parameters
        ----------
        message  : dict
        created by coverting MQTT message string in JSON format to python object
        """
        LOGGER.debug(mqtt_msg)
        output = {}

        def flatten(json_object, name=''):
            if (type(json_object) is dict):
                # iterate through the dict. recursively call the flattening function for each item
                for items in json_object:
                    flatten(json_object[items], name + items + '_')
            elif (type(json_object) is list or type(json_object) is tuple):
                i = 0
                # iterate through the list. recursively call the flattening function for each item
                for items in json_object:
                    flatten(items, name + str(i) + '_')
                    i += 1
            elif (json_object is not None):
                if (name[:-1] == "node_name"):
                    name = name.upper()
                output[name[:-1]] = json_object

        flatten(mqtt_msg)
        return output

    # static Method Ends
