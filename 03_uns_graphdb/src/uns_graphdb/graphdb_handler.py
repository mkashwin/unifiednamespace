"""
Class responsible for persisting the MQTT message into the Graph Database
"""
import logging
import time

import neo4j
from neo4j import exceptions

# Logger
LOGGER = logging.getLogger(__name__)

# Constants used for creating the CQL query
NODE_NAME_KEY = "node_name"
CREATED_TIMESTAMP_KEY = "_created_timestamp"
MODIFIED_TIMESTAMP_KEY = "_modified_timestamp"
NODE_RELATION_NAME = "PARENT_OF"


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
        Initialize the GraphDBHandler class.

        Parameters
        ----------
        uri: str
            Full URI to the Neo4j database including protocol, server name and port
        user : str
            db user name. Must have write access on the Neo4j database also specified here
        password:
            password for the db user
        database : str = neo4j.DEFAULT_DATABASE
            The Neo4j database in which this data should be persisted
        max_retry: int
                Must be a positive integer. Default value is 5.
                Number of attempts after a failed database connection to retry connecting
        sleep_btw_attempts: float
                Must be a positive float. Default value is 10 seconds.
                Seconds to sleep between retries
        """
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
        Validates if the current driver is still connected and if not will create a new connection

        Parameters
        ----------
        retry: int
            Optional parameters to retry making a connection in case of errors.
            The max number of retry is `GraphDBHandler.MAX_RETRIES`
            The time between attempts is  `GraphDBHandler.SLEEP_BTW_ATTEMPT`
        Returns:
            neo4j.Driver: The Neo4j driver object.

        Raises:
            neo4j.exceptions.DatabaseError: When there is a general error from the database.
            neo4j.exceptions.TransientError: When there is a problem connecting to the database.
            neo4j.exceptions.DatabaseUnavailable: When the database is unavailable.
            neo4j.exceptions.ServiceUnavailable: When the service is unavailable.
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
                         attr_node_type: str = "NESTED_ATTRIBUTE",
                         retry: int = 0):
        """
        Persists all nodes and the message as attributes to the leaf node
        ----------
        topic: str
            The topic on which the message was sent
        message: dict
            The JSON MQTT message payload in dict format
        timestamp : float, optional
            Timestamp for receiving the message, by default `time.time()`
        node_types : tuple, optional
            Tuple of names given to nodes based on the hierarchy of the topic.
            By default `("ENTERPRISE", "FACILITY", "AREA","LINE", "DEVICE")`
        attr_node_type:
            Node type used to depict nested attributes which will be child nodes
            by default `"NESTED_ATTRIBUTE"`
        """
        # attributes = None

        # Neo4j supports only flat messages.
        # Also need to ensure that the message doesn't contain
        # any attribute with the name "node_name"
        # if message is not None:
        #     attributes = GraphDBHandler.flatten_json_for_neo4j(message)
        try:
            with self.connect(retry) as driver:
                with driver.session(database=self.database) as session:
                    session.execute_write(self.save_all_nodes, topic, message,
                                          timestamp, node_types,
                                          attr_node_type)
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
                                      attr_node_type=attr_node_type,
                                      retry=retry)

    # method  starts
    def save_all_nodes(self, session: neo4j.Session, topic: str, message: dict,
                       timestamp: float, node_types: tuple,
                       attr_node_type: str):
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
        node_types : tuple
            Tuple of strings representing the node types for each level in the topic hierarchy
        attr_node_type : str
            The node type for attribute nodes
        """
        response = None
        count = 0
        lastnode_id = None
        nodes = topic.split('/')
        dict_less_message, child_dict_vals = GraphDBHandler.separate_plain_composite_attributes(
            message)
        for node in nodes:
            LOGGER.debug("Processing sub topic: %s of topic:%s", str(node),
                         str(topic))

            node_attr = None
            if count == len(nodes) - 1:
                # Save the attributes without nested dicts only for the leaf node of topics
                node_attr = dict_less_message
            node_type: str = GraphDBHandler.get_topic_node_type(
                count, node_types)
            response = GraphDBHandler.save_node(session, node, node_type,
                                                node_attr, lastnode_id,
                                                timestamp)
            lastnode_id = getattr(response.peek()[0], "_element_id")
            if count == len(nodes) - 1:
                # If this is the last node we iterate through the nested dicts
                GraphDBHandler.save_attribute_nodes(session, lastnode_id,
                                                    child_dict_vals,
                                                    attr_node_type, timestamp)
            count += 1

    # method Ends

    # static method starts
    @staticmethod
    def save_attribute_nodes(session, lastnode_id: str, attr_nodes: dict,
                             attr_node_type: str, timestamp: float):
        """
        This function saves attribute nodes in the graph database.

        Parameters:
        -----------
        session: The session object to interact with the database.
        lastnode_id (str): The _element_id of the parent node in the graph. None for top most nodes
        attr_nodes (dict): A dictionary containing nested dicts, lists and/or tuples
        attr_node_type (str): The type of attribute node.
        timestamp (float): The timestamp of when the attribute nodes were saved.

        """
        for key in attr_nodes:
            plain_attributes, composite_attributes = GraphDBHandler.separate_plain_composite_attributes(
                attr_nodes[key])
            response = GraphDBHandler.save_node(session, key, attr_node_type,
                                                plain_attributes, lastnode_id,
                                                timestamp)
            last_attr_node_id = getattr(response.peek()[0], "_element_id")
            # After all the topics have been created the nested dicts , list of dicts in the message
            # need to be created as nodes so that they are properly persisted and traversable
            # The Label for all nodes created for attributes will be the same `attr_node_type`
            if (composite_attributes is not None
                    and len(composite_attributes) > 0):
                for child_key in composite_attributes:

                    response = GraphDBHandler.save_attribute_nodes(
                        session, last_attr_node_id,
                        {child_key, composite_attributes[child_key]},
                        attr_node_type, timestamp)

    # method Ends

    # static method starts
    @staticmethod
    def get_topic_node_type(current_depth: int, node_types: tuple) -> str:
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

        # Need to create unique tree structures so jut a merge for the node name will not do
        # FIXME facing some issues with apoc.do.when to handle this in the DB hence will temp
        # handle this in the python code
        node_exist = None
        if parent_id is not None:
            check_query: str = "MATCH (parent)-[relation:PARENT_OF]->"
            check_query = check_query + f" (node:{nodetype} {{ {NODE_NAME_KEY}: $nodename }})\n"
            check_query = check_query + "WHERE elementId(parent)= $parent_id \n RETURN node"
            node_exist_result: neo4j.Result = session.run(check_query,
                                                          nodename=nodename,
                                                          parent_id=parent_id)
            node_exist = list(node_exist_result)
        if parent_id is None:
            # Merge the top most node always
            query = f"MERGE (node:{nodetype} {{ {NODE_NAME_KEY}: $nodename }}) \n"
            query = query + "ON CREATE \n"
            query = query + f"   SET node.{CREATED_TIMESTAMP_KEY} = $timestamp \n"
            query = query + "ON MATCH \n"
            query = query + f"    SET node.{MODIFIED_TIMESTAMP_KEY} = $timestamp \n"
        elif node_exist is None or len(node_exist) == 0:
            # other nodes should be created if they dont exist in the tree path
            query = f"CREATE (node:{nodetype} {{ {NODE_NAME_KEY}: $nodename }}) \n"
            query = query + f"SET node.{CREATED_TIMESTAMP_KEY} = $timestamp \n"
        else:
            # get the element if of the existing node
            # nodes should be updated if they  exist in the tree path
            node_element_id = getattr(node_exist[0].values()[0], "_element_id")
            query = f"MATCH (node) WHERE elementId(node)= '{node_element_id}'\n"
            query = query + f"SET node.{MODIFIED_TIMESTAMP_KEY} = $timestamp \n"
        # CQL doesn't allow  the node label as a parameter.
        # using a statement with parameters is a safer option against CQL injection

        if attributes is not None:
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
            """
            Recursive function to flatten nested dict/json objects
            """
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
                if name[:-1] == NODE_NAME_KEY:
                    name = name.upper()
                output[name[:-1]] = json_object

        flatten(mqtt_msg)
        return output

    # static Method Ends

    # static Method Starts
    @staticmethod
    def separate_plain_composite_attributes(attributes: dict):
        """
        Splits provided dict into simple values and composite values
        Removes a composite values from the attribute object
        Composite values are of instance list, tuple and dict
        Does not recursively go into the value object
        Parameters
        ----------
        attributes  : dict
            Message properties which may or may not contain combination of plain and composite values

        Returns
        ----------
        1. dict with only simple attribute
        2. dict of remaining composite attributes ( list, dict, tuple)
        """
        # dictionary of simple attributes
        simple_attr: dict = {}
        # dictionary of complex attributes
        complex_attr: dict = {}
        if attributes is None:
            # if this is not a dict then this must be a nested simple list
            attributes = {}
        for key in attributes:
            attr_val = attributes.get(key)
            # Handle restricted name node_name
            if isinstance(attr_val, dict):
                # if the value is type dict then add it to the complex_attributes
                complex_attr[key] = attr_val

            elif isinstance(attr_val, list) or isinstance(attr_val, tuple):
                counter: int = 0
                temp_dict: dict = {}
                is_only_simple_arr: bool = True
                for item in attr_val:
                    name_key = key + "_" + str(counter)
                    if isinstance(item, dict) or isinstance(
                            item, list) or isinstance(item, tuple):
                        # special handling. if there is a sub attribute "name", use it for the node name
                        if isinstance(item,
                                      dict) and "name" in item is not None:
                            name_key = item["name"]
                        is_only_simple_arr = False
                    temp_dict[name_key] = item
                    counter = counter + 1
                if is_only_simple_arr:
                    # if the item is a list or tuple of only primitive types
                    # then it can be merged to the simple_attributes
                    simple_attr[key] = attr_val
                else:
                    complex_attr.update(temp_dict)
            else:
                # if the value is neither dict, list or tuple  add it to the simple_attributes
                simple_attr[key] = attr_val

        return simple_attr, complex_attr

    # static Method Ends
