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

Test the graph_db backend integration
"""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from uns_graphql.backend.graphdb import GraphDB
from uns_graphql.graphql_config import GraphDBConfig

QUERY = """
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
    // Step 4: Apply the topic filter (array of regex expressions)
    WITH resultNode, fullName, $topicFilter AS topicFilter
    WHERE ANY(regex IN topicFilter WHERE fullName =~ regex)

    // Step 5: Find nested children with label "NESTED_ATTRIBUTE" and their relationships
    OPTIONAL MATCH (resultNode)-[r:PARENT_OF]->(nestedChild:NESTED_ATTRIBUTE)
    OPTIONAL MATCH (nestedChild)-[nestedRel:PARENT_OF*]->(child:NESTED_ATTRIBUTE)

    // Step 6: Return the full path, resultNode, nested children, and relationships
    RETURN DISTINCT
    fullName,
    resultNode,
    COLLECT(DISTINCT nestedChild) AS nestedChildren,
    COLLECT(DISTINCT r) + COLLECT(DISTINCT nestedRel) AS relationships
    """
QUERY_PARAMS = {"propertyNames": ["seq", "dict_list"], "topicFilter": ["(.)*"]}


@pytest_asyncio.fixture
async def mock_graphdb_driver():
    """Fixture to mock the Neo4j async driver."""
    mock_driver = AsyncMock()
    yield mock_driver
    await mock_driver.close()  # Ensure the mock driver is properly closed


@patch("uns_graphql.backend.graphdb.AsyncGraphDatabase.driver")
@patch("uns_graphql.backend.graphdb.GraphDBConfig")
@pytest.mark.asyncio
async def test_get_graphdb_driver(mock_config, mock_driver_class, mock_graphdb_driver):
    """
    Test with mock object to validate singularity of the neo4j driver
    """
    mock_driver_class.return_value = mock_graphdb_driver
    mock_config.conn_url = GraphDBConfig.conn_url
    mock_config.user = GraphDBConfig.user
    mock_config.password = GraphDBConfig.password
    mock_config.database = GraphDBConfig.database

    # Test first call to get_graphdb_driver
    try:
        driver1 = await GraphDB.get_graphdb_driver()
        mock_driver_class.assert_called_once_with(
            uri=GraphDBConfig.conn_url, auth=(GraphDBConfig.user, GraphDBConfig.password), database=GraphDBConfig.database
        )
        driver1.verify_connectivity.assert_called_once()

        # Test second call reuses the same driver
        driver2 = await GraphDB.get_graphdb_driver()
        mock_driver_class.assert_called_once()  # Should still be called only once

        assert driver1 is driver2, "The driver instance should be same before releasing"
    finally:
        await GraphDB.release_graphdb_driver()


@patch("uns_graphql.backend.graphdb.GraphDB._graphdb_driver", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_release_graphdb_driver(mock_graphdb_driver):
    """
    Validates that the driver was closed
    """
    await GraphDB.release_graphdb_driver()
    mock_graphdb_driver.close.assert_called_once()


@pytest.mark.asyncio(scope="session")
@pytest.mark.integrationtest
@pytest.mark.parametrize(
    "query, args, kwargs, is_error",
    [
        ("MATCH (n:NOMAD {name: 'IamNotFound'}) RETURN n", None, None, False),  # Valid query but empty result, no params
        ("MATCH (n) RETURN n", None, None, False),  # Valid query valid results
        ("CREATE (n:NEW_NODE) RETURN n", None, None, True),  # Valid insert valid results
        (QUERY, None, QUERY_PARAMS, False),
    ],
)
async def test_execute_query(
    query: str,
    args: tuple,
    kwargs: dict,
    is_error: bool,
):
    """
    Test Read Queries from Graphdb
    """
    # Initialize the GraphDB
    graph_db = GraphDB()
    try:
        # Pass args and kwargs only if they are not None
        if args is None and kwargs is None:
            result = await graph_db.execute_read_query(query)
        elif args is None:
            result = await graph_db.execute_read_query(query, **kwargs)
        elif kwargs is None:
            result = await graph_db.execute_read_query(query, *args)
        else:
            result = await graph_db.execute_read_query(query, *args, **kwargs)
        assert result is not None
    except Exception as ex:
        if is_error:
            assert True  # Error was expected
        else:
            pytest.fail(f"Exception {ex} occurred while executing query: {query} ")
