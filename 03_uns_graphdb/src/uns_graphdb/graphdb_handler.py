"""
Class responsible for persisting the MQTT message into the Graph Database
"""
import logging
import time

import neo4j
from neo4j import exceptions

# Logger
LOGGER = logging.getLogger(__name__)


class GraphDBHandler:
    """
    Class responsible for persisting the MQTT message into the Graph Database
    """

    def __init__(self,
                 uri: str,
                 user: str,
                 password: str,
                 database: str = neo4j.DEFAULT_DATABASE,
                 max_retry: int = 5,
                 sleep_btw_attempts: float = 10):
        """
        uri: str
            Full URI to the Neo4j database including protocol, server name and port
        user : str
            db user name. Must have write access on the Neo4j database also specified here
        password:
            password for the db user
        database : str = neo4j.DEFAULT_DATABASE
            The Neo4j database in which this data should be persisted
        MAX_RETRIES: int
                Must be a positive integer. Default value is 5.
                Number of attempts after a failed database connection to retry connecting
        SLEEP_BTW_ATTEMPT: float
                Must be a positive float. Default value is 10 seconds.
                Seconds to sleep between retries
        """
        # TODO support additional secure authentication  methods
        self.uri: str = uri
        self.auth: tuple = (user, password)
        self.database: str = database
        if self.database is None or self.database == "":
            self.database = neo4j.DEFAULT_DATABASE
        self.max_retry: int = max_retry
        self.sleep_btw_attempts: int = sleep_btw_attempts
        self.driver: neo4j.Driver = None
        try:
            self.connect()
        except Exception as ex:
            LOGGER.error("Failed to create the driver: %s",
                         str(ex),
                         stack_info=True,
                         exc_info=True)
            raise ex

    def connect(self, retry: int = 0) -> neo4j.Driver:
        """
        Returns Neo4j Driver which is the connection to the database
        Validates if the current driver is still connected and of not will create a new connection
        retry: int
            Optional parameters to retry making a connection in case of errors.
            The max number of retry is `GraphDBHandler.MAX_RETRIES`
            The time between attempts is  `GraphDBHandler.SLEEP_BTW_ATTEMPT`
        """
        try:
            if self.driver is None:
                self.driver = neo4j.GraphDatabase.driver(self.uri,
                                                         auth=self.auth)
            self.driver.verify_connectivity()
        except (exceptions.DatabaseError, exceptions.TransientError,
                exceptions.DatabaseUnavailable,
                exceptions.ServiceUnavailable) as ex:
            if retry >= self.max_retry:
                LOGGER.error("No. of retries exceeded %s",
                             str(self.max_retry),
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
                time.sleep(self.sleep_btw_attempts)
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
        """
        Closes the connection to the graph database
        """
        if self.driver is not None:
            try:
                self.driver.close()
                self.driver = None
            except Exception as ex:
                LOGGER.error("Failed to close the driver:%s",
                             str(ex),
                             stack_info=True,
                             exc_info=True)
                self.driver = None

    def persist_mqtt_msg(self,
                         topic: str,
                         message: dict,
                         timestamp: float = time.time(),
                         node_types: tuple = ("ENTERPRISE", "FACILITY", "AREA",
                                              "LINE", "DEVICE"),
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
        node_types:
            tuple of names given to nodes based on the hierarchy of the topic
            Default value-> `("ENTERPRISE", "FACILITY", "AREA","LINE", "DEVICE")`
        """
        response = None
        attributes = None

        # Neo4j supports only flat messages.
        # Also need to ensure that the message doesn't contain
        # any attribute with the name "node_name"
        if message is not None:
            attributes = GraphDBHandler.flatten_json_for_neo4j(message)
        try:
            with self.connect(retry) as driver:
                with driver.session(database=self.database) as session:
                    response = session.execute_write(self.save_all_nodes,
                                                     topic, attributes,
                                                     timestamp, node_types)
        except (exceptions.TransientError, exceptions.TransactionError,
                exceptions.SessionExpired) as ex:
            if retry >= self.max_retry:
                LOGGER.error("No. of retries exceeded %s",
                             str(self.max_retry),
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
                # reset the driver
                self.close()
                time.sleep(self.sleep_btw_attempts)
                self.persist_mqtt_msg(topic=topic,
                                      message=message,
                                      timestamp=timestamp,
                                      retry=retry)
        return response

    # method  starts
    def save_all_nodes(self, session, topic: str, message: dict,
                       timestamp: float, node_types: tuple):
        """
        Iterate the topics by '/'. create node for each level & merge the messages to the final node
        For the other topics in the hierarchy a node will be created / merged and linked to the
        parent topic node
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
        lastnode_id = None
        nodes = topic.split('/')
        for node in nodes:
            LOGGER.debug("Processing sub topic: %s of topic:%s", str(node),
                         str(topic))

            node_attr = None
            if count == len(nodes) - 1:
                # Save the attributes only for the leaf node
                node_attr = message
            node_name: str = GraphDBHandler.get_node_name(count, node_types)
            response = GraphDBHandler.save_node(session, node, node_name,
                                                node_attr, lastnode_id,
                                                timestamp)
            lastnode_id = getattr(response.peek()[0], "_element_id")
            count += 1
        return response

    # method Ends

    # static method starts
    @staticmethod
    def get_node_name(current_depth: int, node_types: tuple) -> str:
        """
        Get the name of the node depending on the depth in the tree
        """
        if current_depth < len(node_types):
            return node_types[current_depth]
        else:
            return f"{node_types[-1]}_depth_{current_depth - len(node_types)+ 1}"

    # static method ends

    # static Method Starts
    @staticmethod
    def save_node(session: neo4j.Session,
                  nodename: str,
                  nodetype: str,
                  attributes: dict = None,
                  parent_id: str = None,
                  timestamp: float = time.time()):
        """
        Creates or Merges the MQTT message as a Graph node. Each level of the topic is also
        persisted as a graph node with appropriate parent relationship
        Parameters
        ----------
        session  : neo4j.Session
            Neo4j session object
        nodename : str
            Trimmed name of the topic
        nodetype : str
            Based on ISA-95 part 2 or Sparkplug spec
            The nested depth of the topic determines the node type.
        message : dict
            The JSON delivered as message in the MQTT payload converted to a dict.
            Defaults to None (for all intermittent topics)
        parent_id  : str
            elementId of the parent node to ensure unique relationships

        Returns the result of the query which will either be
            - one node (in case of top most node)
            - two node in the order of currently created/updated node, parent node
        """
        LOGGER.debug(
            "Saving node: %s of type: %s and attributes: %s with parent: %s",
            str(nodename), str(nodetype), str(attributes), str(parent_id))

        # CQL doesn't allow  the node label as a parameter.
        # using a statement with parameters is a safer option against CQL injection
        query = f"MERGE (node:{nodetype} {{ node_name: $nodename }}) \n"
        query = query + "ON CREATE \n"
        query = query + "   SET node._created_timestamp = $timestamp \n"
        if attributes is not None:
            query = query + "ON MATCH \n"
            query = query + "    SET node._modified_timestamp = $timestamp \n"
            query = query + "SET node += $attributes \n"

        if parent_id is not None:
            query = "MATCH (parent) \n WHERE  elementId(parent)= $parent_id" + '\n' + query + '\n'
            query = query + "MERGE (parent) -[r:PARENT_OF]-> (node) \n"
            query = query + "RETURN node, parent"
        else:
            query = query + "RETURN node"
        LOGGER.debug("CQL statement to be executed: %s", str(query))
        # non-referred would be ignored in the execution.
        result: neo4j.Result = session.run(query,
                                           nodename=nodename,
                                           timestamp=timestamp,
                                           parent_id=parent_id,
                                           attributes=attributes)
        return result

    # static Method Ends

    # static Method Starts
    @staticmethod
    def flatten_json_for_neo4j(mqtt_msg: dict) -> dict:
        """
        Utility methods to convert a nested JSON into a flat structure
        Keys for lists will be of the form <key>_<count>
        Keys for dicts will be of the form <parent key>_<child key>
        if any attribute is named "node_name" it will be replaced by "NODE_NAME"
        Parameters
        ----------
        message  : dict
        created by converting MQTT message string in JSON format to python object
        """
        LOGGER.debug(mqtt_msg)
        output = {}

        def flatten(json_object, name=''):
            if isinstance(json_object, dict):
                # iterate through the dict. recursively call the flattening function for each item
                for items in json_object:
                    flatten(json_object[items], name + items + '_')
            elif (isinstance(json_object, list)
                  or isinstance(json_object, tuple)):
                i = 0
                # iterate through the list. recursively call the flattening function for each item
                for items in json_object:
                    flatten(items, name + str(i) + '_')
                    i += 1
            elif json_object is not None:
                if name[:-1] == "node_name":
                    name = name.upper()
                output[name[:-1]] = json_object

        flatten(mqtt_msg)
        return output

    # static Method Ends
