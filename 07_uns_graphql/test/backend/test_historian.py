import asyncio
import json
from datetime import datetime

import pytest
import pytest_asyncio
from uns_graphql.backend.historian import HistorianDBPool
from uns_graphql.graphql_config import HistorianConfig

# model for db entry
DatabaseRow = tuple[datetime, str, str, dict]
Query = tuple[list[list[str]], list[str], datetime, datetime]  # topic list, publisher list, from_time, to_time

query_topic1_hashtag_wildcard: Query = (
    ["topic1/#"],
    None,
    datetime.fromtimestamp(1701233000),
    datetime.fromtimestamp(1701259000),
)
query_single_wildcard: Query = (["topic1/+"], None, datetime.fromtimestamp(1701233000), datetime.fromtimestamp(1701259000))
query_from_to_same: Query = (["topic3"], None, datetime.fromtimestamp(1701257000), datetime.fromtimestamp(1701257000))
query_from_is_none: Query = (["#"], None, None, datetime.fromtimestamp(1701257000))
query_to_is_none: Query = (["#"], None, datetime.fromtimestamp(1701257000), None)
query_only_topic_a: Query = (["a/#"], None, None, None)
query_only_topic1_wc: Query = (["topic1/#"], None, None, None)
query_only_topic1_sub_wc: Query = (["topic1/+"], None, None, None)
query_only_topic3: Query = (["topic3"], None, None, None)
query_multiple_topics_no_times: Query = (["topic1/#", "topic3"], None, None, None)
query_multiple_topics: Query = (
    ["topic1/#", "topic3"],
    None,
    datetime.fromtimestamp(1701233000),
    datetime.fromtimestamp(1701259000),
)

test_data_set: list[DatabaseRow] = [
    (datetime.fromtimestamp(1701232000), "a/b/c", "client4", json.dumps({"key4": "value4"})),
    (datetime.fromtimestamp(1701233000), "a/b/c", "client5", json.dumps({"key5": "value5"})),
    (datetime.fromtimestamp(1701233500), "a/b/c", "client6", json.dumps({"key6": "value6"})),
    (datetime.fromtimestamp(1701234000), "topic1", "client1", json.dumps({"key1": "value1"})),
    (datetime.fromtimestamp(1701245000), "topic1/subtopic1", "client1", json.dumps({"key2": "value2"})),
    (datetime.fromtimestamp(1701245000), "topic1/subtopic2", "client2", json.dumps({"key3": "value5"})),
    (datetime.fromtimestamp(1701257000), "topic3", "client1", json.dumps({"key3": "value3"})),
]
"""
Test Data
Session fixture is equivalent to running SQL commands
    INSERT INTO unifiednamespace (time, topic, client_id, mqtt_msg)
    VALUES 
        (TO_TIMESTAMP(1701232000), 'a/b/c', 'client4', '{"key4": "value4"}'),
        (TO_TIMESTAMP(1701233000), 'a/b/c', 'client5', '{"key5": "value5"}'),
        (TO_TIMESTAMP(1701233500), 'a/b/c', 'client6', '{"key6": "value6"}'),
        (TO_TIMESTAMP(1701234000), 'topic1', 'client1', '{"key1": "value1"}'),
        (TO_TIMESTAMP(1701245000), 'topic1/subtopic1', 'client1', '{"key2": "value2"}'),
        (TO_TIMESTAMP(1701245000), 'topic1/subtopic2', 'client2', '{"key3": "value5"}'),
        (TO_TIMESTAMP(1701257000), 'topic3', 'client1', '{"key3": "value3"}')
    RETURNING *;
and
    DELETE FROM unifiednamespace;

"""


@pytest.yield_fixture(scope="session")
def event_loop(request):  # noqa: ARG001
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
@pytest.mark.integrationtest
async def historian_pool(event_loop):
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
@pytest.mark.xdist_group(
    name="graphql_historian"
)  # FIXME not working with VsCode https://github.com/microsoft/vscode-python/issues/19374
@pytest.mark.parametrize(
    "query, count_of_return",
    [
        (query_topic1_hashtag_wildcard, 3),
        (query_single_wildcard, 2),
        (query_from_to_same, 1),
        (query_from_is_none, 7),
        (query_to_is_none, 1),
        (query_only_topic_a, 3),
        (query_only_topic1_wc, 3),
        (query_only_topic1_sub_wc, 2),
        (query_only_topic3, 1),
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
