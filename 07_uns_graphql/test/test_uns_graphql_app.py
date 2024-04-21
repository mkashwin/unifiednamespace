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

import pytest
import pytest_asyncio
from uns_graphql.uns_graphql_app import UNSGraphql


def test_uns_graphql_app_attributes():
    """
    Test validity of key attributes of  UNSGraphql needed to start run the GraphQL server
    """
    assert UNSGraphql.schema is not None
    assert UNSGraphql.app is not None
