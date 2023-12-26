# Fixture to handle event loop
import asyncio

import pytest
import pytest_asyncio
from uns_historian.historian_handler import HistorianHandler


@pytest.fixture(scope="session")
def my_event_loop(request):  # noqa: ARG001
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
@pytest.mark.integrationtest
async def historian_pool(my_event_loop):  # noqa: ARG001
    """
    Initialize a shared connection pool based on the pytest marker integrationtest
    """
    pool = await HistorianHandler.get_shared_pool()
    yield pool
    # Close the connection pool after all tests are completed
    await HistorianHandler.close_pool()
