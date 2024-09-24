// spBv1_0|GROUP|MESSAGE_TYPE|EDGE_NODE|DEVICE <= add as label filter to simple_node and nested_node
// ENTERPRISE|FACILITY|AREA|LINE|DEVICE<= add as label filter to simple_node and nested_node

WITH $propertyNames AS propertyNames
UNWIND propertyNames AS propertyName
// Step 1: Find all nodes containing the specified property
// Use a sub query to handle both MATCH conditions
CALL (propertyName)  { 
  // Match nodes that directly contain the specified property
  MATCH (simple_node) // dynamically add the label filter here
  WHERE simple_node[propertyName] IS NOT NULL
  RETURN DISTINCT simple_node AS resultNode
UNION
  // Match nodes that are related via a specific relationship property
  MATCH (nested_node)-[r:PARENT_OF {attribute_name: propertyName}]->(:NESTED_ATTRIBUTE) // dynamically add the label filter here
  WHERE r.type IN ["list", "dict"]
  RETURN DISTINCT nested_node AS resultNode
}

// Step 2: Use APOC to find the path from each node to the root, excluding 'NESTED_ATTRIBUTE' nodes
CALL apoc.path.subgraphNodes(resultNode, {
  relationshipFilter: 'PARENT_OF<',
  labelFilter: '-NESTED_ATTRIBUTE',
  maxLevel: -1
}) YIELD node AS pathNode

// Step 3: Collect the nodes along the path and construct the full name
WITH resultNode, 
     COLLECT(pathNode) AS pathNodes
WITH resultNode,
     REDUCE(fullPath = '', n IN pathNodes | 
            CASE 
                WHEN fullPath = '' THEN n.node_name 
                ELSE  n.node_name + '/' + fullPath 
            END) AS fullName
// Step 4: Apply the topic filter (array of regex expressions)
WITH resultNode, fullName, $topicFilter AS topicFilter
WHERE ANY(regex IN topicFilter WHERE fullName =~ regex) // If Topics are to be matched
//WHERE NONE(regex IN topicFilter WHERE fullName =~ regex) // <= If Topics are to be excluded
// Step 5: Find nested children with label "NESTED_ATTRIBUTE" and their relationships

OPTIONAL MATCH (resultNode)-[r:PARENT_OF]->(nestedChild:NESTED_ATTRIBUTE)
OPTIONAL MATCH (nestedChild)-[nestedRel:PARENT_OF*]->(child:NESTED_ATTRIBUTE)

// Step 6: Return the full path, resultNode, nested children, and relationships
RETURN DISTINCT 
  fullName,
  resultNode,
  COLLECT(DISTINCT nestedChild) AS nestedChildren,
  COLLECT(DISTINCT r) + COLLECT(DISTINCT nestedRel) AS relationships


-----------------

// query for getting the node based on the topics. supports wildcards
WITH $topics AS inputPaths
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
             ELSE 'MATCH (N' + toString(idx-1)+')-[:PARENT_OF*]->(N' + toString(idx) + ':' + labels + ')'
           END
         // Handle the "+" wildcard
         WHEN nodeNames[idx] = "+" THEN
          CASE
            WHEN idx = 0 THEN 'MATCH (N' + toString(idx) + ':' + labels + ') WHERE NOT ()-[:PARENT_OF]->(N' + toString(idx) + ')'
            ELSE 'MATCH (N' + toString(idx-1)+')-[:PARENT_OF]->(N' + toString(idx) + ':' + labels + ')'
           END
         // Handle exact node names
         ELSE
           CASE
             WHEN idx = 0 THEN 'MATCH (N' + toString(idx) + ':' + labels + ' {node_name: "' + nodeNames[idx] + '"})'
             ELSE 'MATCH (N' + toString(idx-1)+')-[:PARENT_OF]->(N' + toString(idx) + ':' + labels + ' {node_name: "' + nodeNames[idx] + '"})'
           END
       END
     ] AS queryParts



// Step 2: Join the query parts into a full Cypher query
WITH apoc.text.join(queryParts, '') + ' RETURN N' + toString(size(nodeNames) - 1) + ' AS resultNode' AS finalQuery

// Step 3: Execute the dynamically constructed query
CALL apoc.cypher.run(finalQuery, {}) YIELD  value

WITH DISTINCT value.resultNode as resultNode
// Step 4: Use APOC to find the path from each node to the root, excluding 'NESTED_ATTRIBUTE' nodes
CALL apoc.path.subgraphNodes(resultNode, {
  relationshipFilter: 'PARENT_OF<',
  labelFilter: '-NESTED_ATTRIBUTE',
  maxLevel: -1
}) YIELD node AS pathNode

// Step 5: Collect the nodes along the path and construct the full name
WITH resultNode, 
     COLLECT(pathNode) AS pathNodes
WITH resultNode,
     REDUCE(fullPath = '', n IN pathNodes | 
            CASE 
                WHEN fullPath = '' THEN n.node_name 
                ELSE  n.node_name + '/' + fullPath 
            END) AS fullName
// Step 6: Find nested children with label "NESTED_ATTRIBUTE" and their relationships
OPTIONAL MATCH (resultNode)-[r:PARENT_OF]->(nestedChild:NESTED_ATTRIBUTE)
OPTIONAL MATCH (nestedChild)-[nestedRel:PARENT_OF*]->(child:NESTED_ATTRIBUTE)

// Step 7: Return the full path, resultNode, nested children, and relationships
RETURN DISTINCT 
  fullName,
  resultNode,
  COLLECT(DISTINCT nestedChild) AS nestedChildren,
  COLLECT(DISTINCT r) + COLLECT(DISTINCT nestedRel) AS relationships


  ============
  //Query to search SPB Node by Metrics
WITH $metric_names as metric_names
UNWIND metric_names as metric_name
MATCH (resultNode)-[rel:PARENT_OF*{attribute_name:"metrics"}]->(:NESTED_ATTRIBUTE{node_name:metric_name})

// Step 2: Use APOC to find the path from each node to the root, excluding 'NESTED_ATTRIBUTE' nodes
CALL apoc.path.subgraphNodes(resultNode, {
  relationshipFilter: 'PARENT_OF<',
  labelFilter: '-NESTED_ATTRIBUTE',
  maxLevel: -1
}) YIELD node AS pathNode

// Step 3: Collect the nodes along the path and construct the full name
WITH resultNode, 
     COLLECT(pathNode) AS pathNodes
WITH resultNode,
     REDUCE(fullPath = '', n IN pathNodes | 
            CASE 
                WHEN fullPath = '' THEN n.node_name 
                ELSE  n.node_name + '/' + fullPath 
            END) AS fullName

// Step 4: Find nested children with label "NESTED_ATTRIBUTE" and their relationships

OPTIONAL MATCH (resultNode)-[r:PARENT_OF]->(nestedChild:NESTED_ATTRIBUTE)
OPTIONAL MATCH (nestedChild)-[nestedRel:PARENT_OF*]->(child:NESTED_ATTRIBUTE)

// Step 5: Return the full path, resultNode, nested children, and relationships
RETURN DISTINCT 
  fullName,
  resultNode,
  COLLECT(DISTINCT nestedChild) AS nestedChildren,
  COLLECT(DISTINCT r) + COLLECT(DISTINCT nestedRel) AS relationships