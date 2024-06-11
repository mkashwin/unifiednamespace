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

Encapsulates integration with the Graph database database
"""

import logging
from datetime import datetime
from typing import Literal, Optional

import neo4j

from uns_graphql.graphql_config import GraphDBConfig

LOGGER = logging.getLogger(__name__)


class GraphDB:
    """
    Encapsulates the connection and queries to the graph database database
    """

    # Class variable to hold the shared pool/driver for the graph DB
    _neo4jdriver: neo4j.GraphDatabase.driver

    @classmethod
    def get_graphdb_driver(cls) -> neo4j.GraphDatabase.driver:
        """
        Returns Neo4j Driver which is the connection to the database
        Validates if the current driver is still connected and if not will create a new connection
        Driver is cached and
        """
