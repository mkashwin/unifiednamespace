"""GraphDB Client with health checking and resource management."""

import logging
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase, Record
from neo4j.exceptions import Neo4jError
from uns_mqtt.mqtt_listener import UnsMQTTClient

from uns_mcp.config import GraphDBConfig

LOGGER = logging.getLogger(__name__)


class GraphDBClient:
    """Async client for Neo4j with automatic resource management."""

    def __init__(self):
        self.driver: AsyncDriver | None = None
        self.database = GraphDBConfig.database

    async def connect(self) -> None:
        """Establish connection to Neo4j."""
        try:
            self.driver = AsyncGraphDatabase.driver(
                uri=GraphDBConfig.conn_url,
                auth=(GraphDBConfig.user, GraphDBConfig.password),
                database=self.database,
                max_connection_pool_size=10,
                connection_acquisition_timeout=30
            )
            await self.driver.verify_connectivity()
            LOGGER.info(f"Connected to Neo4j at {GraphDBConfig.conn_url}")
        except Neo4jError as e:
            LOGGER.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def disconnect(self) -> None:
        """Close the Neo4j driver."""
        if self.driver:
            try:
                await self.driver.close()
                LOGGER.info("Neo4j connection closed")
            except Exception as e:
                LOGGER.error(f"Error closing Neo4j: {e}")
            finally:
                self.driver = None

    async def health_check(self) -> bool:
        """Check if connection is healthy."""
        if not self.driver:
            return False
        try:
            await self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    async def execute_query(self, query: str, **params) -> list[Record]:
        """Execute a Cypher query."""
        if not self.driver:
            raise ValueError("GraphDB client not connected")

        async def run_query(tx, query: str, **params):
            result = await tx.run(query, **params)
            return [record async for record in result]

        async with self.driver.session() as session:
            records = await session.execute_read(run_query, query=query, **params)
            return records

    async def get_uns_nodes(self, topics: list[str]) -> list[dict[str, Any]]:
        """Query UNS nodes by topic patterns."""
        query = """
        WITH $topics AS inputPaths
        UNWIND inputPaths AS inputPath
        WITH split(inputPath, '/') AS nodeNames
        WITH $labels AS labels, nodeNames, range(0, size(nodeNames) - 1) AS idxRange

        WITH nodeNames, labels, idxRange,
            [idx IN idxRange |
            CASE
                WHEN nodeNames[idx] = "#" THEN
                CASE
                    WHEN idx = 0 THEN 'MATCH (N' + toString(idx) + ':' + labels + ')'
                    ELSE 'MATCH (N' + toString(idx-1)+')-[:PARENT_OF*]->(N' + toString(idx) + ':' + labels + ')'
                END
                WHEN nodeNames[idx] = "+" THEN
                CASE
                    WHEN idx = 0 THEN 'MATCH (N' + toString(idx) + ':' + labels + ')'
                    ELSE 'MATCH (N' + toString(idx-1)+')-[:PARENT_OF]->(N' + toString(idx) + ':' + labels + ')'
                END
                ELSE
                CASE
                    WHEN idx = 0 THEN 'MATCH (N' + toString(idx) + ':' + labels + ' {node_name: "' + nodeNames[idx] + '"})'
                    ELSE 'MATCH (N' + toString(idx-1)+')-[:PARENT_OF]->
                        (N' + toString(idx) + ':' + labels + ' {node_name: "' + nodeNames[idx] + '"})'
                END
            END
            ] AS queryParts

        WITH apoc.text.join(queryParts, '') + ' RETURN N' + toString(size(nodeNames) - 1) + ' AS resultNode' AS finalQuery
        CALL apoc.cypher.run(finalQuery, {}) YIELD value

        WITH DISTINCT value.resultNode as resultNode
        CALL apoc.path.subgraphNodes(resultNode, {
            relationshipFilter: 'PARENT_OF<',
            labelFilter: '-NESTED_ATTRIBUTE',
            maxLevel: -1
        }) YIELD node AS pathNode

        WITH resultNode, COLLECT(DISTINCT pathNode) AS pathNodes
        WITH resultNode,
            REDUCE(fullPath = '', n IN pathNodes |
                CASE WHEN fullPath = '' THEN n.node_name ELSE n.node_name + '/' + fullPath END) AS fullName

        OPTIONAL MATCH (resultNode)-[r:PARENT_OF]->(nestedChild:NESTED_ATTRIBUTE)
        OPTIONAL MATCH (nestedChild)-[nestedRel:PARENT_OF*]->(child:NESTED_ATTRIBUTE)

        RETURN DISTINCT fullName, resultNode,
            COLLECT(DISTINCT nestedChild) AS nestedChildren,
            COLLECT(DISTINCT r) + COLLECT(DISTINCT nestedRel) AS relationships
        """

        label_filter = "|".join(GraphDBConfig.uns_node_types)
        records = await self.execute_query(query, topics=topics, labels=label_filter)
        return self._process_node_records(records)

    async def get_uns_nodes_by_property(
        self, property_keys: list[str], topics: list[str] | None = None, exclude_topics: bool = False
    ) -> list[dict[str, Any]]:
        """Query nodes containing specific properties."""
        topic_regex_list = []
        if topics:
            topic_regex_list = [UnsMQTTClient.get_regex_for_topic_with_wildcard(
                topic) for topic in topics]

        topic_subquery = ""
        if topic_regex_list:
            if exclude_topics:
                topic_subquery = "WITH resultNode, fullName, $topicFilter AS topicFilter " \
                    "WHERE NONE(regex IN topicFilter WHERE fullName =~ regex)"
            else:
                topic_subquery = "WITH resultNode, fullName, $topicFilter AS topicFilter WHERE ANY(regex IN topicFilter " \
                    "WHERE fullName =~ regex)"

        label_filter = "|".join(GraphDBConfig.uns_node_types)
        nested_type = GraphDBConfig.nested_attribute_node_type

        query = f"""
        WITH $propertyNames AS propertyNames
        UNWIND propertyNames AS propertyName
        CALL (propertyName) {{
            MATCH (simple_node:{label_filter}) WHERE simple_node[propertyName] IS NOT NULL
            RETURN DISTINCT simple_node AS resultNode
        UNION
            MATCH (nested_node:{label_filter})-[r:PARENT_OF {{attribute_name: propertyName}}]->(:{nested_type})
            WHERE r.type IN ["list", "dict"]
            RETURN DISTINCT nested_node AS resultNode
        }}

        CALL apoc.path.subgraphNodes(resultNode, {{
            relationshipFilter: 'PARENT_OF<', labelFilter: '-{nested_type}', maxLevel: -1
        }}) YIELD node AS pathNode

        WITH resultNode, COLLECT(DISTINCT pathNode) AS pathNodes
        WITH resultNode, REDUCE(fullPath = '', n IN pathNodes |
            CASE WHEN fullPath = '' THEN n.node_name ELSE n.node_name + '/' + fullPath END) AS fullName

        {topic_subquery}

        OPTIONAL MATCH (resultNode)-[r:PARENT_OF]->(nestedChild:{nested_type})
        OPTIONAL MATCH (nestedChild)-[nestedRel:PARENT_OF*]->(child:{nested_type})

        RETURN DISTINCT fullName, resultNode,
            COLLECT(DISTINCT nestedChild) AS nestedChildren,
            COLLECT(DISTINCT r) + COLLECT(DISTINCT nestedRel) AS relationships
        """

        records = await self.execute_query(query, propertyNames=property_keys, topicFilter=topic_regex_list)
        return self._process_node_records(records)

    async def get_namespace_hierarchy(self) -> dict[str, Any]:
        """Get complete namespace hierarchy."""
        query = """
        MATCH (root) WHERE NOT ()-[:PARENT_OF]->(root) AND any(label IN labels(root) WHERE label IN $nodeTypes)
        CALL apoc.path.subgraphAll(root, {relationshipFilter: 'PARENT_OF>', labelFilter: '-NESTED_ATTRIBUTE', maxLevel: -1})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """

        records = await self.execute_query(query, nodeTypes=list(GraphDBConfig.uns_node_types))

        hierarchy = {}
        for record in records:
            nodes = record.get("nodes", [])
            for node in nodes:
                name = node.get("node_name", "unknown")
                hierarchy[name] = {
                    "type": next((label for label in node.labels if label in GraphDBConfig.uns_node_types), "unknown"),
                    "properties": dict(node)
                }
        return hierarchy

    def _process_node_records(self, records: list[Record]) -> list[dict[str, Any]]:
        """Process Neo4j records into node dictionaries."""
        nodes = []
        for record in records:
            topic = record["fullName"]
            node = record["resultNode"]
            nested_children = record["nestedChildren"]
            relationships = record["relationships"]

            node_dict = {
                "node_name": node.get("node_name"),
                "node_type": self._get_node_type(node.labels),
                "namespace": topic,
                "payload": self._reconstruct_payload(node, nested_children, relationships),
                "created": node.get("_created_timestamp"),
                "last_updated": node.get("_modified_timestamp") or node.get("_created_timestamp")
            }
            nodes.append(node_dict)
        return nodes

    def _get_node_type(self, labels: list[str]) -> str:
        """Extract UNS node type from labels."""
        for label in labels:
            if label in GraphDBConfig.uns_node_types:
                return label
        return "UNKNOWN"

    def _reconstruct_payload(self, parent_node, nested_children: list, relationships: list) -> dict:
        """Reconstruct complete payload from graph structure."""
        payload = {k: v for k, v in dict(parent_node).items()
                   if k not in ["node_name", "_created_timestamp", "_modified_timestamp"]}

        node_map = {}
        for child in nested_children:
            node_map[child.element_id] = {
                k: v for k, v in dict(child).items()
                if k not in ["node_name", "_created_timestamp", "_modified_timestamp"]
            }
        node_map[parent_node.element_id] = payload

        for rel in relationships:
            if rel.type != "PARENT_OF":
                continue
            parent_id = rel.nodes[0].element_id
            child_id = rel.nodes[1].element_id
            attr_name = rel.get("attribute_name")
            attr_type = rel.get("type")

            if not attr_name or parent_id not in node_map or child_id not in node_map:
                continue

            parent_dict = node_map[parent_id]
            child_dict = node_map[child_id]

            if attr_type == "dict":
                parent_dict[attr_name] = child_dict
            elif attr_type == "list":
                index = rel.get("index", 0)
                if attr_name not in parent_dict:
                    parent_dict[attr_name] = []
                while len(parent_dict[attr_name]) <= index:
                    parent_dict[attr_name].append(None)
                parent_dict[attr_name][index] = child_dict

        return payload
