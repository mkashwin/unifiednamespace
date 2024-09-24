"""*******************************************************************************
* Copyright (c) 2021 Ashwin Krishnan
*
* All rights reserved. This program and the accompanying materials
* are made available under the terms of MIT and  is provided "as is",
* without warranty of any kind, express or implied, including but
* not limited to the warranties of merchantability, fitness for a
* particular purpose and noninfringement. In no event shall the
* authors, contributors or copyright holders be liable for any claim,
* damages or other liability, whether in an action of contract,
* tort or otherwise, arising from, out of or in connection with the software
* or the use or other dealings in the software.
*
* Contributors:
*    -
*******************************************************************************

Class responsible for persisting the MQTT message into the Graph Database
"""

import logging
import re
import sys
import time
from typing import Optional

import neo4j
from neo4j import exceptions

# Logger
LOGGER = logging.getLogger(__name__)

# Constants used for creating the CQL query
NODE_NAME_KEY = "node_name"
CREATED_TIMESTAMP_KEY = "_created_timestamp"
MODIFIED_TIMESTAMP_KEY = "_modified_timestamp"

NODE_RELATION_NAME = "PARENT_OF"
REL_ATTR_KEY = "attribute_name"
REL_ATTR_TYPE = "type"
REL_INDEX = "index"

SANITIZE_PATTERN = r"[^A-Za-z0-9_]"  # used to sanitize fields sent to Neo4j which cant be sent as params


class GraphDBHandler:
    """
    Class responsible for persisting the MQTT message into the Graph Database
    """

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: Optional[str] = neo4j.DEFAULT_DATABASE,
        max_retry: int = 5,
        sleep_btw_attempts: float = 10,
    ):
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
        database : Optional[str] = neo4j.DEFAULT_DATABASE
            The Neo4j database in which this data should be persisted
        max_retry: int
                Must be a positive integer. Default value is 5.
                Number of attempts after a failed database connection to retry connecting
        sleep_btw_attempts: float
                Must be a positive float. Default value is 10 seconds.
                Seconds to sleep between retries
        """
        self.uri: Optional[str] = uri
        self.auth: tuple = (user, password)
        self.database: Optional[str] = database
        if self.database is None or self.database == "":
            self.database = neo4j.DEFAULT_DATABASE
        self.max_retry: int = max_retry
        self.sleep_btw_attempts: int = sleep_btw_attempts
        self.driver: neo4j.Driver = None
        try:
            self.connect()

        except SystemError as ex:
            raise ex
        except Exception as ex:
            LOGGER.error("Failed to create the driver: %s", str(ex), stack_info=True, exc_info=True)
            raise SystemError(ex) from ex

    def connect(self, retry: int = 0) -> neo4j.Driver:
        """
        Returns Neo4j Driver which is the connection to the database
        Validates if the current driver is still connected and if not will create a new connection

        Parameters
        ----------
        retry: int
            Optional parameters to retry making a connection in case of errors.
            The max number of retry is `GraphDBHandler.max_retry`
            The time between attempts is  `GraphDBHandler.sleep_btw_attempts`
        Returns:
            neo4j.Driver: The Neo4j driver object.

        Raises
        ------
            neo4j.exceptions.DatabaseError: When there is a general error from the database.
            neo4j.exceptions.TransientError: When there is a problem connecting to the database.
            neo4j.exceptions.DatabaseUnavailable: When the database is unavailable.
            neo4j.exceptions.ServiceUnavailable: When the service is unavailable.
        """
        try:
            if self.driver is None:
                self.driver = neo4j.GraphDatabase.driver(self.uri, auth=self.auth, database=self.database)
            self.driver.verify_connectivity()
        except (
            exceptions.DatabaseError,
            exceptions.TransientError,
            exceptions.DatabaseUnavailable,
            exceptions.ServiceUnavailable,
        ) as ex:
            if retry >= self.max_retry:
                LOGGER.error("No. of retries exceeded %s", str(self.max_retry), stack_info=True, exc_info=True)
                raise SystemError(ex) from ex

            retry += 1
            LOGGER.error("Error Connecting to %s.\n Error: %s", self.database, str(ex), stack_info=True, exc_info=True)
            time.sleep(self.sleep_btw_attempts)
            self.connect(retry=retry)

        except Exception as ex:
            LOGGER.error(
                "Error Connecting to %s. Unable to retry. Error: %s", self.database, str(ex), stack_info=True, exc_info=True
            )
            raise SystemError(ex) from ex
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
                # pylint: disable=broad-exception-caught
                LOGGER.error("Failed to close the driver:%s", str(ex), stack_info=True, exc_info=True)
                self.driver = None

    def persist_mqtt_msg(
        self,
        topic: str,
        message: dict,
        timestamp: float = time.time(),
        node_types: tuple = ("ENTERPRISE", "FACILITY", "AREA", "LINE", "DEVICE"),
        attr_node_type: Optional[str] = "NESTED_ATTRIBUTE",
        retry: int = 0,
    ):
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
            tuple of names given to nodes based on the hierarchy of the topic.
            By default `("ENTERPRISE", "FACILITY", "AREA","LINE", "DEVICE")`
        attr_node_type:
            Node type used to depict nested attributes which will be child nodes
            by default `"NESTED_ATTRIBUTE"`
        """
        try:
            driver = self.connect(retry)
            with driver.session(database=self.database) as session:
                session.execute_write(self.save_all_nodes, topic, message, timestamp, node_types, attr_node_type)
        except (exceptions.TransientError, exceptions.TransactionError, exceptions.SessionExpired) as ex:
            if retry >= self.max_retry:
                LOGGER.error("No. of retries exceeded %s", str(self.max_retry), stack_info=True, exc_info=True)
                raise ex

            retry += 1
            LOGGER.error(
                "Error persisting \ntopic:%s \nmessage %s. on Error: %s",
                topic,
                str(message),
                str(ex),
                stack_info=True,
                exc_info=True,
            )
            # reset the driver
            self.close()
            time.sleep(self.sleep_btw_attempts)
            self.persist_mqtt_msg(
                topic=topic, message=message, timestamp=timestamp, attr_node_type=attr_node_type, retry=retry
            )

    # method  starts
    def save_all_nodes(
        self, session: neo4j.Session, topic: str, message: dict, timestamp: float, node_types: tuple, attr_node_type: str
    ):
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
            tuple of strings representing the node types for each level in the topic hierarchy
        attr_node_type : str
            The node type for attribute nodes
        """
        response = None
        count: int = 0
        lastnode_id = None
        nodes = topic.split("/")

        for node in nodes:
            LOGGER.debug("Processing sub topic: %s of topic:%s", str(node), str(topic))
            node_type: str = GraphDBHandler.get_topic_node_type(count, node_types)
            if node != nodes[-1]:  # check if this is the leaf node of the topic
                response = GraphDBHandler.save_node(
                    session=session,
                    nodename=node,
                    nodetype=node_type,
                    node_props=None,
                    parent_id=lastnode_id,
                    timestamp=timestamp,
                )
                records = list(response)
                lastnode_id = records[0][0].element_id

            else:  # if this is the leaf node of the topic then save the attributes to this nodes
                GraphDBHandler.save_attribute_nodes(
                    session=session,
                    nodename=node,
                    lastnode_id=lastnode_id,
                    attr_nodes=message,
                    node_type=node_type,
                    attr_node_type=attr_node_type,
                    timestamp=timestamp,
                )
            count += 1

    # method Ends

    # static method starts
    @staticmethod
    def save_attribute_nodes(
        session,
        nodename: str,
        lastnode_id: str,
        attr_nodes: dict,
        node_type: str,
        attr_node_type: str,
        timestamp: float,
        nodetype_props: Optional[dict] = None,
    ):
        """
        This function saves attribute nodes in the graph database.

        Parameters
        ----------
        session: The session object to interact with the database.
        nodename (str): name of the node
        node_type(str): type of the node
        lastnode_id (str): The element_id of the parent node in the graph. None for top most nodes
        attr_nodes (dict): A dictionary containing nested dicts, lists and/or tuples.
        nodetype_props (dict): dict of primitive values to be added to relations
        attr_node_type (str): The type of attribute node. i.e the child nodes of attribute node
        timestamp (float): The timestamp of when the attribute nodes were saved.
        """
        primitive_properties, compound_properties = GraphDBHandler.separate_plain_composite_attributes(attr_nodes)
        if len(primitive_properties) > 0 or len(compound_properties) > 0:  # Dont create empty node
            response = GraphDBHandler.save_node(
                session=session,
                nodename=nodename,
                nodetype=node_type,
                node_props=primitive_properties,
                nodetype_props=nodetype_props,
                parent_id=lastnode_id,
                timestamp=timestamp,
            )
            attr_node_id = response.peek()[0].element_id
        else:
            attr_node_id = lastnode_id

        for key, value in compound_properties.items():
            if isinstance(value, dict):
                # split the attributes of the nested dict into primitive and compound.
                dict_name: str = str(value.get("name", key))
                GraphDBHandler.save_attribute_nodes(
                    session=session,
                    nodename=dict_name,
                    node_type=attr_node_type,
                    attr_node_type=attr_node_type,
                    attr_nodes=value,
                    nodetype_props={"attribute_name": key, "type": "dict"},
                    lastnode_id=attr_node_id,
                    timestamp=timestamp,
                )

            elif isinstance(value, list | tuple):
                # recursively create/update child nodes for list of dicts to the parent node
                # currently ignoring the index in the array as subsequent updates may not have same position
                # value should be uniquely identified by it's name
                index: int = 0
                for sub_dict in value:
                    # save each element as a different node.
                    # to avoid clashes get the name of the child node sub_dict["name"] and append to the key
                    # Not using index because the length of the array could change across invocations
                    # if name is not present use the current index number
                    sub_dict_name = sub_dict.get("name", key + "_" + str(index))

                    GraphDBHandler.save_attribute_nodes(
                        session=session,
                        nodename=sub_dict_name,
                        node_type=attr_node_type,
                        lastnode_id=attr_node_id,
                        attr_nodes=sub_dict,
                        nodetype_props={REL_ATTR_KEY: key, REL_ATTR_TYPE: "list", REL_INDEX: index},
                        attr_node_type=attr_node_type,
                        timestamp=timestamp,
                    )
                    index = index + 1
            else:
                LOGGER.error(
                    f"Compound Properties: {value} should either be dict or a list of dict. Ignored and not persisted"
                )
                pass

    # method Ends

    # static method starts
    @staticmethod
    def get_topic_node_type(current_depth: int, node_types: tuple) -> str:
        """
        Get the name of the node depending on the depth in the tree
        """
        if current_depth < len(node_types):
            return node_types[current_depth]

        return f"{node_types[-1]}_depth_{current_depth - len(node_types) + 1}"

    # static method ends

    # static Method Starts
    @staticmethod
    def save_node(
        session: neo4j.Session,
        nodename: str,
        nodetype: str,
        node_props: Optional[dict] = None,
        nodetype_props: Optional[dict] = None,
        parent_id: Optional[str] = None,
        timestamp: float = time.time(),
    ):
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
        node_props : dict
            The JSON delivered as message in the MQTT payload converted to a dict.
            Defaults to None (for all intermittent topics)
            Should not contain composite values i.e. dict or list[dict]
        nodetype_props: dict
            Optional properties added to the relation between parent and newly created  node
            Used for nested attributes
        parent_id  : str
            elementId of the parent node to ensure unique relationships

        Returns the result of the query which will either be
            - one node (in case of top most node)
            - two node in the order of currently created/updated node, parent node
        """
        LOGGER.debug(
            "Saving node: %s of type: %s and attributes: %s with parent: %s",
            str(nodename),
            str(nodetype),
            str(node_props),
            str(nodetype_props),
            str(parent_id),
        )
        # attributes should not be null for the query to work
        node_props = GraphDBHandler.transform_node_params_for_neo4j(node_props)
        # convert dict to a literal map for CQL as parameter maps are not allowed by Neo4j in queries
        literal_map = GraphDBHandler.get_literal_map(nodetype_props)

        query = f"""//Find Parent node
    OPTIONAL MATCH (parent) WHERE elementId(parent) = $parent_id
    // Optional match the child node
    OPTIONAL MATCH (parent) -[r:{NODE_RELATION_NAME} {literal_map} ]-> (child:{nodetype}{{ node_name: $nodename}})

    // Use apoc.do.when to handle the case where parent is null
    CALL apoc.do.when(
        // Check if the child is null
        parent is null,
        "
        MERGE (new_node:{nodetype} {{ node_name: $nodename }})
        SET new_node.{CREATED_TIMESTAMP_KEY} = $timestamp
        SET new_node += $attributes
        RETURN new_node as child
        ",
        "
        CALL apoc.do.when(
            // Check if the child is nulls
            child is null,
            // Create a new node when the child is null
            'CREATE (new_node:{nodetype} {{ node_name: $nodename }})
            SET new_node.{CREATED_TIMESTAMP_KEY} = $timestamp
            SET new_node += $attributes
            MERGE (parent)-[r:{NODE_RELATION_NAME} {literal_map.replace('"', r'\"')} ]-> (new_node)
            // Return the new child node, parent node
            RETURN new_node as child, parent as parent
            ',
            // Modify the existing child node when it is not null
            'SET child.{MODIFIED_TIMESTAMP_KEY} = $timestamp
            SET child += $attributes
            RETURN child as child, parent as parent
            ',
            // Pass in the variables
            {{parent:parent, child:child, nodename:$nodename,
             timestamp:$timestamp, attributes:$attributes}}
            ) YIELD value as result

        // Return the child node and the parent node
        RETURN result.child as child, result.parent as parent
        ",
        // Pass in the variables
        {{parent:parent, child:child, nodename:$nodename,
          timestamp:$timestamp, attributes:$attributes}}
        ) YIELD value
    // return the child node
    RETURN value.child
    """

        LOGGER.debug("CQL statement to be executed: %s", str(query))

        result: neo4j.Result = session.run(
            query,
            nodename=nodename,
            timestamp=timestamp,
            parent_id=parent_id,
            attributes=node_props,
        )
        return result

    # static Method Ends

    @staticmethod
    def transform_node_params_for_neo4j(attributes: dict):
        """
        Function to transform parameters being sent
        - null parameters
        - BigInt
        """
        if attributes is None:
            attributes = {}
        else:
            for key, value in attributes.items():
                if isinstance(value, int) and not (-sys.maxsize - 1) < value < sys.maxsize:
                    # for values greater than 9223372036854775807 i.e. sys.maxsize we get an error Integer Out of Range
                    # Hence converting this into a string object
                    attributes[key] = str(value)

                elif (
                    isinstance(value, list)
                    and all(isinstance(x, int) for x in value)
                    and any(not (-sys.maxsize - 1) < x < sys.maxsize for x in value)
                ):  # for int arrays for any element is beyond max size convert all elements to string
                    attributes[key] = [str(x) for x in value]
        return attributes

    # static Method Starts
    @staticmethod
    def get_literal_map(attributes: dict) -> str:
        """
        Convert the attributes to be added to a relationship to a string,
        because parameters are not allowed for relationship attributes.
        Also sanitizes all keys and values to prevent CQL injection attacks
        """
        literal_map: str = ""
        if attributes is not None:
            literal_map = literal_map + "{ "
            for key, val in attributes.items():
                literal_map = (
                    # sanitizing the properties to reduce risk of CQL Injection  attacks
                    literal_map
                    + " "
                    + re.sub(SANITIZE_PATTERN, "", key)
                    + ': "'
                    + re.sub(SANITIZE_PATTERN, "", str(val))
                    + '" ,'
                )
            literal_map = literal_map[:-1] + "}"

        return literal_map

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
        -------
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
        for key, attr_val in attributes.items():
            # Handle restricted name node_name
            if key == NODE_NAME_KEY:
                key = key.upper()

            if isinstance(attr_val, dict):
                # if the value is type dict then add it to the complex_attributes
                complex_attr[key] = attr_val

            elif isinstance(attr_val, list | tuple) and all(isinstance(item, dict) for item in attr_val):
                # List/Tuple of complex attributes only. list of primitive values allowed under node
                complex_attr[key] = attr_val
            else:
                # if the value is neither dict, list or tuple  add it to the simple_attributes
                simple_attr[key] = attr_val

        return simple_attr, complex_attr

    # static Method Ends
