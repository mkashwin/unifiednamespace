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

Test historian queries
"""

import json
from datetime import UTC, datetime
from typing import Literal

import pytest
import pytest_asyncio

from uns_graphql.backend.historian import HistorianDBPool
from uns_graphql.graphql_config import HistorianConfig

# model for db entry
DatabaseRow = tuple[datetime, str, str, dict]

test_data_set: list[DatabaseRow] = [
    (datetime.fromtimestamp(1701232000, UTC), "a/b/c",
     "client4", json.dumps({"key1": "value1"})),
    (datetime.fromtimestamp(1701233000, UTC), "a/b/c",
     "client5", json.dumps({"key2": "value2"})),
    (datetime.fromtimestamp(1701233500, UTC), "a/b/c",
     "client6", json.dumps({"key3": "value3"})),
    (datetime.fromtimestamp(1701234000, UTC), "topic1",
     "client1", json.dumps({"key4": "value4"})),
    (datetime.fromtimestamp(1701245000, UTC), "topic1/subtopic1",
     "client1", json.dumps({"key5": "value5.1"})),
    (datetime.fromtimestamp(1701245000, UTC), "topic1/subtopic2",
     "client2", json.dumps({"key5": "value5.2"})),
    (datetime.fromtimestamp(1701257000, UTC), "topic3",
     "client1", json.dumps({"key6": "value6"})),
    (
        datetime.fromtimestamp(170129000, UTC),
        "test/nested/json",
        "nested",
        json.dumps({"a": "value1", "b": [10, 23, 23, 34], "c": {
                   "k1": "v1", "k2": 100}, "k3": "outer_v1"}),
    ),
]


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def historian_pool():
    """
    Initialize a shared connection pool based on the pytest marker integrationtest
    """
    pool = await HistorianDBPool.get_shared_pool()
    yield pool
    # Close the connection pool after all tests are completed
    await HistorianDBPool.close_pool()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def prepare_database(historian_pool):  # noqa: ARG001
    """
    Prepare the database with test data based on the pytest marker integrationtest
    """
    # time: datetime, topic: str, client_id: str, mqtt_msg: dict
    insert_sql_cmd = f"""INSERT INTO {HistorianConfig.table} ( time, topic, client_id, mqtt_msg )
                        VALUES ($1,$2,$3,$4)
                        RETURNING *;"""  # noqa: S608
    delete_sql_cmd = f""" DELETE FROM {HistorianConfig.table} WHERE
                               time =  $1  AND
                               topic = $2 AND
                               client_id = $3;"""  # noqa: S608

    # clean up database before inserting to avoid UniqueViolationError if previous run crashed
    for row in test_data_set:
        # row is (time, topic, client_id, mqtt_msg)
        # we only need the first 3 for delete
        delete_params = list(row)[:3]
        async with HistorianDBPool() as historian:
            await historian.execute_prepared(delete_sql_cmd, *delete_params)

    # insert testdata into database
    for row in test_data_set:
        async with HistorianDBPool() as historian:
            await historian.execute_prepared(insert_sql_cmd, *list(row))
    yield
    # clean up database
    for row in test_data_set:
        delete_params = list(row)[:3]
        async with HistorianDBPool() as historian:
            await historian.execute_prepared(delete_sql_cmd, *delete_params)


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.integrationtest
@pytest.mark.xdist_group(name="graphql_historian")
# Fix for xdist not working with VsCode https://github.com/microsoft/vscode-python/issues/19374
# VSCode executes the test but does not mark the result correctly when xdist_group is used.
@pytest.mark.parametrize(
    "topic_list,publisher_list,from_date, to_date, count_of_return",
    [
        (["topic1/#"], None, datetime.fromtimestamp(1701233000, UTC),
         datetime.fromtimestamp(1701259000, UTC), 3),
        (["topic1/+"], None, datetime.fromtimestamp(1701233000, UTC),
         datetime.fromtimestamp(1701259000, UTC), 2),
        (["topic3"], None, datetime.fromtimestamp(1701257000, UTC),
         datetime.fromtimestamp(1701257000, UTC), 1),
        (["#"], None, None, datetime.fromtimestamp(1701257000, UTC), 8),
        (["#"], None, datetime.fromtimestamp(1701257000, UTC), None, 1),
        (["a/#"], None, None, None, 3),
        (["topic1/#"], None, None, None, 3),
        (["topic1/+"], None, None, None, 2),
        (["topic3"], None, None, None, 1),
        (["topic3"], ["client1"], None, None, 1),
        (["#"], ["client1", "client2"], None, None, 4),
        (["topic3"], ["do_not_exist"], None, None, 0),
        (["topic1/#", "topic3"], None, None, None, 4),
        (["topic1/#", "topic3"], None, datetime.fromtimestamp(1701233000,
         UTC), datetime.fromtimestamp(1701259000, UTC), 4),
    ],
)
async def test_get_historic_events(
    prepare_database,  # noqa: ARG001
    topic_list: list[str],
    publisher_list: list[str],
    from_date: datetime,
    to_date: datetime,
    count_of_return: int,
):
    async with HistorianDBPool() as historian:
        result = await historian.get_historic_events(
            topics=topic_list, publishers=publisher_list, from_datetime=from_date, to_datetime=to_date
        )
        assert len(result) == count_of_return


@pytest.mark.integrationtest
@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.xdist_group(name="graphql_historian")
# Fix for xdist not working with VsCode https://github.com/microsoft/vscode-python/issues/19374
# VSCode executes the test but does not mark the result correctly when xdist_group is used.
@pytest.mark.parametrize(
    "property_keys,binary_operator, topics, from_timestamp, to_timestamp, count_of_return",
    [
        (["key5"], None, None, None, None, 2),
        (
            ["key1", "key2"],
            "OR",
            ["a/b/c"],
            datetime.fromtimestamp(1701231000, UTC),
            datetime.fromtimestamp(1701236000, UTC),
            2,
        ),  # binary operator is None. default to OR
        (["key1"], None, None, None, None, 1),  #
        (["key5", "key4"], "OR", ["topic1/#"], None, None, 3),
        (["key1", "key2"], "OR", None, None, None, 2),
        (["key1", "key2"], "OR", ["a/b/c"], None, None, 2),
        (["k1", "k2"], "OR", None, None, None, 1),  # nested
        (["i_dont_exist"], "OR", None, None, None, 0),  # non existent path
        (["key1", "key2"], "AND", ["topic1/#", "topic3"], None, None, 0),
        (["k1", "key1"], "AND", None, None, None, 0),
        (["key1", "key2"], "NOT", None, None, None, 6),  # NOT
        (["key1"], None, [
         f"; SELECT * FROM {HistorianConfig.table}"], None, None, 0),  # noqa: S608 for SQL Injection on topics
        ([f"; SELECT * FROM {HistorianConfig.table}"],  # noqa: S608 for SQL Injection on topics
         None, None, None, None, 0),
    ],
)
async def test_get_historic_events_for_property_keys(
    prepare_database,  # noqa: ARG001
    property_keys: list[str],
    binary_operator: Literal["AND", "OR", "NOT"],
    topics: list[str],
    from_timestamp,
    to_timestamp,
    count_of_return: int,
):
    async with HistorianDBPool() as historian:
        result = await historian.get_historic_events_for_property_keys(
            property_keys=property_keys,
            binary_operator=binary_operator,
            topics=topics,
            from_datetime=from_timestamp,
            to_datetime=to_timestamp,
        )
        assert len(result) == count_of_return
