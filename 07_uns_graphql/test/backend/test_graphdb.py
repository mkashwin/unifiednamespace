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
    Test with mock object to validate singulatiry of the neo4j driver
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

        assert driver1 == driver2, "The driver instace should be same befor releasing"
    finally:
        await GraphDB.release_graphdb_driver()


@patch("uns_graphql.backend.graphdb.GraphDB._graphdb_driver", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_release_graphdb_driver(mock_graphdb_driver):
    """
    Validatres that the driver was closed
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
        ("CREATE (n:NEW_NODE) RETURN n", None, None, False),  # Valid insert valid results
    ],
)
async def test_execute_read_query(
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
        result = await graph_db.execute_query(query=query, args=args, kwargs=kwargs)
        assert result is not None
    except Exception as ex:
        if is_error:
            assert True  # Error was expected
        else:
            pytest.fail(f"Exception {ex} occurred while executing quwery: {query} ")
