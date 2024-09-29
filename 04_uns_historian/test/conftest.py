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
"""

import pytest_asyncio

from uns_historian.historian_handler import HistorianHandler


@pytest_asyncio.fixture(loop_scope="session", scope="session")
async def historian_pool():
    """
    Initialize a shared connection pool based on the pytest marker integrationtest
    """
    pool = await HistorianHandler.get_shared_pool()
    yield pool
    # Close the connection pool after all tests are completed
    await HistorianHandler.close_pool()
