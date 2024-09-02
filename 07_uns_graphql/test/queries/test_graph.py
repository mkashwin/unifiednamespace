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
Test cases for uns_graphql.queries.graph.Query
"""

from pathlib import Path

import pytest_asyncio
from uns_graphql.backend.graphdb import GraphDB


@pytest_asyncio.fixture(scope="module")
async def setup_graphdb_data():
    """Fixture to set up data in the GraphDB from the test_data.cypher file."""
    # Read the Cypher script as read only
    with open(file=Path(__file__).resolve().parent / "test_data.cypher") as file:
        cypher_script = file.read()
    # Filter out lines that are not valid Cypher queries
    valid_queries = cypher_script.replace(":begin\n", "").replace(":commit\n", "").split(";")
    # Initialize the GraphDB
    graph_db = GraphDB()

    # Execute each query separately
    for query in valid_queries:
        if query.strip():  # Make sure the query is not empty
            await graph_db.execute_query(query=query)

    # Yield control to the test
    yield

    # Teardown code i.e. clearing the database)
    await graph_db.execute_query("MATCH (n) DETACH DELETE n;")
    # Release the driver
    await graph_db.release_graphdb_driver()
