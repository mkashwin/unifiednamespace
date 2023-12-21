import asyncio
import json
from datetime import UTC, datetime
from typing import Literal

import pytest
import pytest_asyncio
from uns_graphql.backend.historian import HistorianDBPool
from uns_graphql.graphql_config import HistorianConfig

# model for db entry
DatabaseRow = tuple[datetime, str, str, dict]
Query = tuple[list[list[str]], list[str], datetime, datetime]  # topic list, publisher list, from_time, to_time


test_data_set: list[DatabaseRow] = [
    (datetime.fromtimestamp(1701232000, UTC), "a/b/c", "client4", json.dumps({"key1": "value1"})),
    (datetime.fromtimestamp(1701233000, UTC), "a/b/c", "client5", json.dumps({"key2": "value2"})),
    (datetime.fromtimestamp(1701233500, UTC), "a/b/c", "client6", json.dumps({"key3": "value3"})),
    (datetime.fromtimestamp(1701234000, UTC), "topic1", "client1", json.dumps({"key4": "value4"})),
    (datetime.fromtimestamp(1701245000, UTC), "topic1/subtopic1", "client1", json.dumps({"key5": "value5.1"})),
    (datetime.fromtimestamp(1701245000, UTC), "topic1/subtopic2", "client2", json.dumps({"key5": "value5.2"})),
    (datetime.fromtimestamp(1701257000, UTC), "topic3", "client1", json.dumps({"key6": "value6"})),
    (
        datetime.fromtimestamp(170129000, UTC),
        "test/nested/json",
        "nested",
        json.dumps({"a": "value1", "b": [10, 23, 23, 34], "c": {"k1": "v1", "k2": 100}, "k3": "outer_v1"}),
    ),
]

query_topic1_hashtag_wildcard: Query = (
    ["topic1/#"],
    None,
    datetime.fromtimestamp(1701233000, UTC),
    datetime.fromtimestamp(1701259000, UTC),
)
query_single_wildcard: Query = (
    ["topic1/+"],
    None,
    datetime.fromtimestamp(1701233000, UTC),
    datetime.fromtimestamp(1701259000, UTC),
)
query_from_to_same: Query = (
    ["topic3"],
    None,
    datetime.fromtimestamp(1701257000, UTC),
    datetime.fromtimestamp(1701257000, UTC),
)
query_from_is_none: Query = (["#"], None, None, datetime.fromtimestamp(1701257000, UTC))
query_to_is_none: Query = (["#"], None, datetime.fromtimestamp(1701257000, UTC), None)
query_only_topic_a: Query = (["a/#"], None, None, None)
query_only_topic1_wc: Query = (["topic1/#"], None, None, None)
query_only_topic1_sub_wc: Query = (["topic1/+"], None, None, None)
query_only_topic3: Query = (["topic3"], None, None, None)
query_only_topic3_publisher: Query = (["topic3"], ["client1"], None, None)
query_multiple_topics_no_times: Query = (["topic1/#", "topic3"], None, None, None)
query_multiple_topics: Query = (
    ["topic1/#", "topic3"],
    None,
    datetime.fromtimestamp(1701233000, UTC),
    datetime.fromtimestamp(1701259000, UTC),
)


@pytest.fixture(scope="session")
def event_loop(request):  # noqa: ARG001
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
@pytest.mark.integrationtest
async def historian_pool(event_loop):  # noqa: ARG001
    """
    Initialize a shared connection pool based on the pytest marker integrationtest
    """
    pool = await HistorianDBPool.get_shared_pool()
    yield pool
    # Close the connection pool after all tests are completed
    await HistorianDBPool.close_pool()


@pytest_asyncio.fixture(scope="session")
@pytest.mark.integrationtest
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
                               client_id = $3 AND
                               mqtt_msg = $4;"""  # noqa: S608

    # insert testdata into database
    for row in test_data_set:
        async with HistorianDBPool() as historian:
            await historian.execute_prepared(insert_sql_cmd, *list(row))
    yield
    # clean up database
    for row in test_data_set:
        async with HistorianDBPool() as historian:
            await historian.execute_prepared(delete_sql_cmd, *list(row))


@pytest.mark.asyncio(scope="session")
@pytest.mark.integrationtest
# FIXME not working with VsCode https://github.com/microsoft/vscode-python/issues/19374
# Comment this marker and run test individually
@pytest.mark.xdist_group(name="graphql_historian")
@pytest.mark.parametrize(
    "query, count_of_return",
    [
        (query_topic1_hashtag_wildcard, 3),
        (query_single_wildcard, 2),
        (query_from_to_same, 1),
        (query_from_is_none, 8),
        (query_to_is_none, 1),
        (query_only_topic_a, 3),
        (query_only_topic1_wc, 3),
        (query_only_topic1_sub_wc, 2),
        (query_only_topic3, 1),
        (query_only_topic3_publisher, 1),
        (query_multiple_topics_no_times, 4),
        (query_multiple_topics, 4),
    ],
)
async def test_get_historic_events(prepare_database, query: Query, count_of_return: int):  # noqa: ARG001
    async with HistorianDBPool() as historian:
        result = await historian.get_historic_events(
            topics=query[0], publishers=query[1], from_datetime=query[2], to_datetime=query[3]
        )
        assert len(result) == count_of_return


@pytest.mark.asyncio(scope="session")
@pytest.mark.integrationtest
# FIXME not working with VsCode https://github.com/microsoft/vscode-python/issues/19374
# Comment this marker and run test individually
@pytest.mark.xdist_group(name="graphql_historian")
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
        ),
        (["key5", "key4"], "OR", ["topic1/#"], None, None, 3),
        (["key1", "key2"], "AND", ["topic1/#"], None, None, 0),
        (["key1", "key2"], "OR", None, None, None, 2),
        (["key1", "key2"], "OR", ["a/b/c"], None, None, 2),
        (["k1", "k2"], "OR", None, None, None, 1),  # nested
        (["k1", "key1"], "AND", None, None, None, 0),
        (["key1", "key2"], "NOT", None, None, None, 6),  # NOT
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
