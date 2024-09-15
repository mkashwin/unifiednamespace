"""*******************************************************************************
* Copyright (c) 2024 Ashwin Krishnan
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

GraphQL queries to the graph database
"""

import logging
from datetime import UTC, datetime
from typing import Any, Optional

import strawberry
from neo4j import Record
from neo4j.graph import Node, Relationship
from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_graphql.backend.graphdb import GraphDB
from uns_graphql.graphql_config import GraphDBConfig
from uns_graphql.input.mqtt import MQTTTopicInput
from uns_graphql.type.isa95_node import UNSNode
from uns_graphql.type.sparkplugb_node import SPBNode

LOGGER = logging.getLogger(__name__)

# Constants used for node and relationship key properties
NODE_NAME_KEY = "node_name"
CREATED_TIMESTAMP_KEY = "_created_timestamp"
MODIFIED_TIMESTAMP_KEY = "_modified_timestamp"

NODE_RELATION_NAME = "PARENT_OF"
REL_ATTR_KEY = "attribute_name"
REL_ATTR_TYPE = "type"
REL_INDEX = "index"


@strawberry.type(description="Query GraphDB for current consolidated UNS Nodes created by merging multiple UNS Events ")
class Query:
    """
    All Queries for latest consolidated node from the Unified Namespace
    """

    # Label filters to be used in the queries
    UNS_LABEL_FILTER = "|".join(GraphDBConfig.uns_node_types)
    SPB_LABEL_FILTER = "|".join(GraphDBConfig.spb_node_types)

    #
    """
        Template for the query to search by property. following variables used in the query
        {0} - label filter to determine if the query is for UNS or SPB i.e. UNS_LABEL_FILTER or SPB_LABEL_FILTER
        {1} - label filter for NESTED_ATTRIBUTE i.e GraphDBConfig.nested_attribute_node_type
        {2} - optional subquery for including or excluding nodes based on topics. Pass empty string if no topics are present

        While running the query the propertyNames array and the topicFilter array values are passed in as parameters.
        Ensure that topicFilter is an array of regex expressions. Convert the topic wildcards to regex.

        The result of the query is a list of
            - fullName: topic or path till the node,
            - resultNode: the node matching the query,
            - nestedChildren: all the nested children of the node of type  GraphDBConfig.nested_attribute_node_type
            - relationships: between resultNode and nestedChildren  & between nestedChildren if more than 1 level of nesting
    """
    _SEARCH_BY_PROPERTY_QUERY = """WITH $propertyNames AS propertyNames
        UNWIND propertyNames AS propertyName
        // Step 1: Find all nodes containing the specified property
        // Use a sub query to handle both MATCH conditions
        CALL (propertyName)  {{
            // Match nodes that directly contain the specified property
            MATCH (simple_node:{0}) // dynamically add the label filter here
            WHERE simple_node[propertyName] IS NOT NULL
            RETURN DISTINCT simple_node AS resultNode
        UNION
            // Match nodes that are related via a specific relationship property
            MATCH (nested_node:{0})-[r:PARENT_OF {{attribute_name: propertyName}}]->(:{1})
            WHERE r.type IN ["list", "dict"]
            RETURN DISTINCT nested_node AS resultNode
        }}

        // Step 2: Use APOC to find the path from each node to the root, excluding '{1}' nodes
        CALL apoc.path.subgraphNodes(resultNode, {{
            relationshipFilter: 'PARENT_OF<',
            labelFilter: '-{1}',
            maxLevel: -1
            }}) YIELD node AS pathNode

        // Step 3: Collect the nodes along the path and construct the full name
        WITH resultNode,
            COLLECT(pathNode) AS pathNodes
        WITH resultNode,
            REDUCE(fullPath = '', n IN pathNodes |
                    CASE
                        WHEN fullPath = '' THEN n.node_name
                        ELSE  n.node_name + '/' + fullPath
                    END) AS fullName

        {2}

        // Step 5: Find nested children with label "{1}" and their relationships

        OPTIONAL MATCH (resultNode)-[r:PARENT_OF]->(nestedChild:{1})
        OPTIONAL MATCH (nestedChild)-[nestedRel:PARENT_OF*]->(child:{1})

        // Step 6: Return the full path, resultNode, nested children, and relationships
        RETURN DISTINCT
        fullName,
        resultNode,
        COLLECT(DISTINCT nestedChild) AS nestedChildren,
        COLLECT(DISTINCT r) + COLLECT(DISTINCT nestedRel) AS relationships
        """

    # sub query for _SEARCH_BY_PROPERTY_QUERY template
    _FILTER_BY_TOPIC_INCLUSION_QUERY = """// Step 4: Apply the topic filter (array of regex expressions) to include
        WITH resultNode, fullName, $topicFilter AS topicFilter
        WHERE ANY(regex IN topicFilter WHERE fullName =~ regex) // If Topics are to be matched
    """
    # sub query for _SEARCH_BY_PROPERTY_QUERY template
    _FILTER_BY_TOPIC_EXCLUSION_QUERY = """// Step 4: Apply the topic filter (array of regex expressions) to exclude
        WITH resultNode, fullName, $topicFilter AS topicFilter
        WHERE NONE(regex IN topicFilter WHERE fullName =~ regex) // If Topics are to be matched
    """
    #
    """
        Search by topic query. Parameters used in the query are
          - topics - array of topics from client ( no need to convert wildcards to regex, the query will handle it )
          - labels - array of labels to match for the nodes i.e. UNS_LABEL_FILTER or SPB_LABEL_FILTER
        The result of the query is a list of
            - fullName: topic or path till the node,
            - resultNode: the node matching the query,
            - nestedChildren: all the nested children of the node of type  GraphDBConfig.nested_attribute_node_type
            - relationships: between resultNode and nestedChildren  & between nestedChildren if more than 1 level of nesting
    """
    _SEARCH_BY_TOPIC_QUERY = f"""WITH $topics AS inputPaths
        UNWIND inputPaths AS inputPath
        WITH split(inputPath, '/') AS nodeNames, inputPath
        WITH $labels AS labels, nodeNames, range(0, size(nodeNames) - 1) AS idxRange

        // Step 1: Construct each part of the query dynamically
        WITH nodeNames, labels, idxRange,
            [idx IN idxRange |
            CASE
                // Handle the "#" wildcard
                WHEN nodeNames[idx] = "#" THEN
                CASE
                    WHEN idx = 0 THEN 'MATCH (N' + toString(idx) + ':' + labels + ')'
                    ELSE 'MATCH (N' + toString(idx-1)+')-[:{NODE_RELATION_NAME}*]->(N' + toString(idx) + ':' + labels + ')'
                END
                // Handle the "+" wildcard
                WHEN nodeNames[idx] = "+" THEN
                CASE
                    WHEN idx = 0 THEN 'MATCH (N' + toString(idx) + ':' + labels + ') WHERE NOT ()-[:{NODE_RELATION_NAME}]->(N' + toString(idx) + ')'
                    ELSE 'MATCH (N' + toString(idx-1)+')-[:{NODE_RELATION_NAME}]->(N' + toString(idx) + ':' + labels + ')'
                END
                // Handle exact node names
                ELSE
                CASE
                    WHEN idx = 0 THEN 'MATCH (N' + toString(idx) + ':' + labels + ' {{node_name: "' + nodeNames[idx] + '"}})'
                    ELSE 'MATCH (N' + toString(idx-1)+')-[:{NODE_RELATION_NAME}]->(N' + toString(idx) + ':' + labels + ' {{node_name: "' + nodeNames[idx] + '"}})'
                END
            END
            ] AS queryParts

        // Step 2: Join the query parts into a full Cypher query
        WITH apoc.text.join(queryParts, '') + ' RETURN N' + toString(size(nodeNames) - 1) + ' AS resultNode' AS finalQuery

        // Step 3: Execute the dynamically constructed query
        CALL apoc.cypher.run(finalQuery, {{}}) YIELD  value

        WITH DISTINCT value.resultNode as resultNode
        // Step 4: Use APOC to find the path from each node to the root, excluding '{ GraphDBConfig.nested_attribute_node_type }' nodes
        CALL apoc.path.subgraphNodes(resultNode, {{
        relationshipFilter: '{ NODE_RELATION_NAME }<',
        labelFilter: '-{ GraphDBConfig.nested_attribute_node_type }',
        maxLevel: -1
        }}) YIELD node AS pathNode

        // Step 5: Collect the nodes along the path and construct the full name
        WITH resultNode,
            COLLECT(pathNode) AS pathNodes
        WITH resultNode,
            REDUCE(fullPath = '', n IN pathNodes |
                    CASE
                        WHEN fullPath = '' THEN n.node_name
                        ELSE  n.node_name + '/' + fullPath
                    END) AS fullName
        // Step 6: Find nested children with label "{  GraphDBConfig.nested_attribute_node_type }" and their relationships
        OPTIONAL MATCH (resultNode)-[r:{NODE_RELATION_NAME}]->(nestedChild:{  GraphDBConfig.nested_attribute_node_type })
        OPTIONAL MATCH (nestedChild)-[nestedRel:{NODE_RELATION_NAME}*]->(child:{  GraphDBConfig.nested_attribute_node_type })

        // Step 7: Return the full path, resultNode, nested children, and relationships
        RETURN DISTINCT
        fullName,
        resultNode,
        COLLECT(DISTINCT nestedChild) AS nestedChildren,
        COLLECT(DISTINCT r) + COLLECT(DISTINCT nestedRel) AS relationships
    """  # noqa: E501
    #
    """
        Search SparkplugB namespace to get all payloads containing the provided metric name
        Parameters used in the query are
            - metic_names : array of metric names. case sensitive and exact match

        The result of the query is a list of
            - fullName: topic or path till the node,
            - resultNode: the node matching the query,
            - nestedChildren: all the nested children of the node of type  GraphDBConfig.nested_attribute_node_type
            - relationships: between resultNode and nestedChildren  & between nestedChildren if more than 1 level of nesting
    """
    _SEARCH_SPB_BY_METRIC_QUERY = f"""WITH $metric_names as metric_names
        UNWIND metric_names as metric_name
        MATCH (resultNode:{{{SPB_LABEL_FILTER}}})-[rel:{NODE_RELATION_NAME}*{{attribute_name:"metrics"}}]->
            (:{ GraphDBConfig.nested_attribute_node_type }{{node_name:metric_name}})

        // Step 2: Use APOC to find the path from each node to the root,
        // excluding '{GraphDBConfig.nested_attribute_node_type}' nodes
        CALL apoc.path.subgraphNodes(resultNode, {{
        relationshipFilter: '{NODE_RELATION_NAME}<',
        labelFilter: '-{ GraphDBConfig.nested_attribute_node_type }',
        maxLevel: -1
        }}) YIELD node AS pathNode

        // Step 3: Collect the nodes along the path and construct the full name
        WITH resultNode,
            COLLECT(pathNode) AS pathNodes
        WITH resultNode,
            REDUCE(fullPath = '', n IN pathNodes |
                    CASE
                        WHEN fullPath = '' THEN n.node_name
                        ELSE  n.node_name + '/' + fullPath
                    END) AS fullName

        // Step 4: Find nested children with label "{ GraphDBConfig.nested_attribute_node_type }" and their relationships

        OPTIONAL MATCH (resultNode)-[r:{NODE_RELATION_NAME}]->(nestedChild:{ GraphDBConfig.nested_attribute_node_type })
        OPTIONAL MATCH (nestedChild)-[nestedRel:{NODE_RELATION_NAME}*]->(child:{ GraphDBConfig.nested_attribute_node_type })

        // Step 5: Return the full path, resultNode, nested children, and relationships
        RETURN DISTINCT
        fullName,
        resultNode,
        COLLECT(DISTINCT nestedChild) AS nestedChildren,
        COLLECT(DISTINCT r) + COLLECT(DISTINCT nestedRel) AS relationships
    """

    @strawberry.field(description="Get consolidation of nodes for given array of topics. MQTT wildcards are supported")
    async def get_uns_nodes(
        self,
        mqtt_topics: list[MQTTTopicInput],
    ) -> list[UNSNode]:
        LOGGER.debug("Query for Nodes in UNS with Params :\n" f"topics={mqtt_topics}")
        if type(mqtt_topics) is not list:
            # convert single topic to array for consistent handling. Done need to convert to regex
            mqtt_topics = [mqtt_topics]
        # Initialize the GraphDB
        graph_db = GraphDB()
        results: list[Record] = await graph_db.execute_query(
            query=self._SEARCH_BY_TOPIC_QUERY,
            topics=[mqtt_topic.topic for mqtt_topic in mqtt_topics],
            labels=self.UNS_LABEL_FILTER,
        )
        uns_node_list: list[UNSNode] = []
        for record in results:
            topic: str = record["fullName"]
            node: Node = record["resultNode"]
            child_nodes: list[Node] = record["nestedChildren"]
            relationships: list[Relationship] = record["relationships"]

            if node[MODIFIED_TIMESTAMP_KEY]:
                modified_timestamp = datetime.fromtimestamp(node[MODIFIED_TIMESTAMP_KEY] / 1000, UTC)
            else:
                # if the DB doesn't have any value, then created and modified timestamps are the same
                modified_timestamp = datetime.fromtimestamp(node[CREATED_TIMESTAMP_KEY] / 1000, UTC)

            uns_node: UNSNode = UNSNode(
                node_name=node[NODE_NAME_KEY],
                # As the node can have multiple labels extract only those which are of UNS Node types
                node_type=self.get_node_type(list(node.labels), GraphDBConfig.uns_node_types),
                namespace=topic,
                payload=self.get_nested_properties(node, child_nodes, relationships),
                created=datetime.fromtimestamp(node[CREATED_TIMESTAMP_KEY] / 1000, UTC),
                last_updated=modified_timestamp,
            )
            uns_node_list.append(uns_node)
        return uns_node_list

    @strawberry.field(
        description="Get all UNSNodes published which have specific attribute name as 'property_keys'. \n "
        "Optionally Filter results with list of  topics. \n"
        "If topics are provided then optional boolean value exclude_topics attribute can be set to true .\n"
        "to exclude the nodes which match the topics.\n"
    )
    async def get_uns_nodes_by_property(
        self,
        property_keys: list[str],
        topics: Optional[list[MQTTTopicInput]] = strawberry.UNSET,
        exclude_topics: Optional[bool] = False,
    ) -> list[UNSNode]:
        LOGGER.debug(
            "Query for historic events by properties, with params :\n"
            f"property_keys={property_keys}, topics={topics}, exclude_topics={exclude_topics}"
        )
        if topics is None or topics == strawberry.UNSET:
            topics = []
        elif type(topics) is not list:
            # convert single topic to array for consistent handling
            topics = [topics]

        if type(property_keys) is not list:
            property_keys = [property_keys]

        topic_regex_list: list[str] = [UnsMQTTClient.get_regex_for_topic_with_wildcard(topic.topic) for topic in topics]

        topic_sub_query = None
        if len(topic_regex_list) == 0:
            topic_sub_query = ""
        elif exclude_topics:
            topic_sub_query = Query._FILTER_BY_TOPIC_EXCLUSION_QUERY
        else:
            topic_sub_query = Query._FILTER_BY_TOPIC_INCLUSION_QUERY

        final_query = Query._SEARCH_BY_PROPERTY_QUERY.format(
            Query.UNS_LABEL_FILTER, GraphDBConfig.nested_attribute_node_type, topic_sub_query
        )
        # Initialize the GraphDB
        graph_db = GraphDB()
        results: list[Record] = await graph_db.execute_query(
            query=final_query, propertyNames=property_keys, topicFilter=topic_regex_list
        )
        uns_node_list: list[UNSNode] = []
        for record in results:
            topic: str = record["fullName"]
            node: Node = record["resultNode"]
            child_nodes: list[Node] = record["nestedChildren"]
            relationships: list[Relationship] = record["relationships"]

            if node[MODIFIED_TIMESTAMP_KEY]:
                modified_timestamp = datetime.fromtimestamp(node[MODIFIED_TIMESTAMP_KEY] / 1000, UTC)
            else:
                # if the DB doesn't have any value, then created and modified timestamps are the same
                modified_timestamp = datetime.fromtimestamp(node[CREATED_TIMESTAMP_KEY] / 1000, UTC)

            uns_node: UNSNode = UNSNode(
                node_name=node[NODE_NAME_KEY],
                # As the node can have multiple labels extract only those which are of UNS Node types
                node_type=self.get_node_type(list(node.labels), GraphDBConfig.uns_node_types),
                namespace=topic,
                payload=self.get_nested_properties(node, child_nodes, relationships),
                created=datetime.fromtimestamp(node[CREATED_TIMESTAMP_KEY] / 1000, UTC),
                last_updated=modified_timestamp,
            )
            uns_node_list.append(uns_node)
        return uns_node_list

    @strawberry.field(description="Get all the SPBNode by the provided metric name")
    async def get_spb_nodes_by_metric(self, metric_names: list[str]) -> list[SPBNode]:
        """ """
        LOGGER.debug("Query for Nodes in SpB with Params :\n" f"topics={metric_names}")
        if type(metric_names) is not list:
            # convert single topic to array for consistent handling. Done need to convert to regex
            metric_names = [metric_names]
        # Initialize the GraphDB
        graph_db = GraphDB()
        results: list[Record] = await graph_db.execute_query(query=self._SEARCH_SPB_BY_METRIC_QUERY, metric_names=metric_names)
        spb_metric_nodes: list[SPBNode] = []
        for record in results:
            topic: str = record["fullName"]
            node: Node = record["resultNode"]
            child_nodes: list[Node] = record["nestedChildren"]
            relationships: list[Relationship] = record["relationships"]

            spb_metric = SPBNode(
                topic=topic,
                payload=self.get_nested_properties(node, child_nodes, relationships),
            )
            spb_metric_nodes.append(spb_metric)

        return spb_metric_nodes

    @classmethod
    async def on_shutdown(cls):
        """
        Clean up Db connection pool
        """
        await GraphDB.release_graphdb_driver()

    @classmethod
    def get_node_type(cls, labels: list[str], valid_labels: tuple[str]) -> str:
        """
        Compares teh labels on a node with the valid set of label types and returns the one which matches
        this allows the nodes to have multiple labels in the future
        """
        for label in labels:
            if label in valid_labels:
                return label

    @classmethod
    def get_nested_properties(cls, parent: Node, nested_children: list[Node], relationships: list[Relationship]) -> dict:  # noqa: C901
        """
        Retrieves nested properties for a given parent node by merging the nested chid

        Args:
            parent: The parent node.
            nested_children (list): A list of child node types
            relationships (list): A list of relationships to traverse.

        Returns:
            dict : All child nodes converted into child dicts.
            The returned dict can be merged into the properties of parent node
        """
        if parent is None:
            raise ValueError("parent cannot be null")
        if nested_children is None:
            nested_children = []
        if relationships is None:
            relationships = []
        # map element id uniquely identifying a node to the corresponding properties map
        node_to_prop: dict[str, dict] = {}

        for node in [parent, *nested_children]:
            # loop through all the nodes to create the corresponding dict objects
            nested_properties: dict[str, Any] = {
                # filter out special properties added to the neo4j node which were not present in the original payload
                key: value
                for key, value in node.items()
                if key not in [NODE_NAME_KEY, CREATED_TIMESTAMP_KEY, MODIFIED_TIMESTAMP_KEY]
            }

            #  logic for handling changing key NODE_NAME to lower case which was done while persisting
            if nested_properties.get(NODE_NAME_KEY.upper()):
                nested_properties[NODE_NAME_KEY] = nested_properties.pop(NODE_NAME_KEY.upper())

            # save those objects against the element id for later retrieval
            node_to_prop[node.element_id] = nested_properties

        # find max index for nested lists ( key (parent_id, attribute_name))
        map_list_size: dict[tuple, int] = {}
        for relation in relationships:
            if relation.type != NODE_RELATION_NAME or relation[REL_ATTR_TYPE] != "list":
                continue  # ensure that only relevant relations are processed

            attr_name = relation[REL_ATTR_KEY]
            size: int = map_list_size.get((relation.nodes[0].element_id, attr_name), 0)
            index = int(relation[REL_INDEX])
            if size - 1 < index:
                map_list_size[relation.nodes[0].element_id, attr_name] = index + 1

        for relation in relationships:
            # in a relationship relation.nodes[0] is the parent and relation.nodes[1] is the child
            # get the the node_properties based on the element id
            if relation.type != NODE_RELATION_NAME:
                continue  # ensure that only relevant relations are processed
            parent_property_map: dict = node_to_prop[relation.nodes[0].element_id]
            child_property_map: dict = node_to_prop[relation.nodes[1].element_id]
            attr_name: str = relation[REL_ATTR_KEY]
            attr_type: str = relation[REL_ATTR_TYPE]  # will be either dict or list

            match attr_type:
                case "dict":
                    # get the properties of the child and merge it into parent_property_map
                    parent_property_map[attr_name] = child_property_map

                case "list":
                    index = int(relation[REL_INDEX])  # will be null for dict, list index for list
                    dict_size = map_list_size.get((relation.nodes[0].element_id, attr_name))
                    child_list: list = parent_property_map.get(attr_name, [None] * dict_size)

                    # update the list map at correct index
                    child_list[index] = child_property_map
                    parent_property_map[attr_name] = child_list

        return node_to_prop[parent.element_id]
