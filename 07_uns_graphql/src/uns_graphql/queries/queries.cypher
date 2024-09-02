// Step 1: Find all nodes containing the specified property
// Use a subquery to handle both MATCH conditions
CALL {
  WITH $propertyNames AS propertyNames
  UNWIND propertyNames AS propertyName
  // Match nodes that directly contain the specified property
  MATCH (simple_node)
  WHERE simple_node[propertyName] IS NOT NULL
  RETURN DISTINCT simple_node AS resultNode
UNION
  WITH $propertyNames AS propertyNames
  UNWIND propertyNames AS propertyName
  // Match nodes that are related via a specific relationship property
  MATCH (nested_node)-[r:PARENT_OF {attribute_name: propertyName}]->(:NESTED_ATTRIBUTE)
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
// Step 4: Find nested children with label "NESTED_ATTRIBUTE" and their relationships
OPTIONAL MATCH (resultNode)-[r:PARENT_OF]->(nestedChild:NESTED_ATTRIBUTE)
OPTIONAL MATCH (nestedChild)-[nestedRel:PARENT_OF*]->(child:NESTED_ATTRIBUTE)

// Step 5: Return the full path, resultNode, nested children, and relationships
RETURN DISTINCT 
  fullName,
  resultNode,
  COLLECT(DISTINCT nestedChild) AS nestedChildren,
  COLLECT(DISTINCT r) + COLLECT(DISTINCT nestedRel) AS relationships

-----------------

-----------------
// Get node based on topics. Does not work for # and + entries. need atleast one 
WITH $topics AS inputPaths
UNWIND inputPaths AS inputPath
WITH split(inputPath, '/') AS nodeNames, inputPath

// Step 1: Match the root node based on the first part of the path
MATCH (root {node_name: nodeNames[0]})

// Step 2: Expand paths from the root node
CALL apoc.path.expand(
  root, 
  'PARENT_OF>', 
  '',          // No label filter
  0,           // Min depth 0 to include the root node
  -1           // Max depth is unlimited to cover all possible depths
) YIELD path AS fullPath

// Step 3: Filter paths according to the inputPath with wildcards
WITH fullPath, nodeNames, nodes(fullPath) AS nodesPath
WITH fullPath, nodeNames, nodesPath, last(nodes(fullPath)) AS lastNode
WHERE
  size(nodesPath) >= size(nodeNames) AND
  all(i IN range(0, size(nodeNames) - 1) WHERE
    (nodeNames[i] = '+' AND size(nodesPath) > i) OR
    (nodeNames[i] = '#' AND size(nodesPath) > i) OR
    (nodeNames[i] = nodesPath[i].node_name)
  ) AND
  (size(nodeNames) = size(nodesPath) OR nodeNames[-1] = '#' OR nodeNames[-1] = lastNode.node_name)

// Step 4: Construct the MQTT topic path from the matched path
WITH fullPath, lastNode, reduce(fullPathStr = '', n IN nodesPath | 
            CASE 
                WHEN fullPathStr = '' THEN n.node_name 
                ELSE fullPathStr + '/' + n.node_name 
            END) AS mqttTopic

// Step 5: Exclude paths containing 'NESTED_ATTRIBUTE' nodes in the path
WHERE NOT any(n IN nodesPath WHERE 'NESTED_ATTRIBUTE' IN labels(n))

// Step 6: Match directly connected nested children of the last node that have the label 'NESTED_ATTRIBUTE'
OPTIONAL MATCH (lastNode)-[r:PARENT_OF]->(nestedChild:NESTED_ATTRIBUTE)

// Step 7: Match any children of the nestedChild if they have the label "NESTED_ATTRIBUTE"
OPTIONAL MATCH (nestedChild)-[nestedRel:PARENT_OF*]->(child:NESTED_ATTRIBUTE)

// Step 8: Collect results
WITH DISTINCT mqttTopic, lastNode, 
     COLLECT(DISTINCT nestedChild) AS nestedChildren, 
     COLLECT(DISTINCT r) + COLLECT(DISTINCT nestedRel) AS relationships

// Step 9: Return the MQTT topic path, the last node, nested children, and relationships
RETURN 
  mqttTopic,
  lastNode as node,
  nestedChildren,
  relationships
