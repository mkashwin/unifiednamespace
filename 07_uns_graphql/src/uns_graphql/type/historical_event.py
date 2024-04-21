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

Type of data to be retrieved from the UNS
Events map to a single message in the queue or historization of those messages
"""

import logging
from datetime import datetime

import strawberry

from uns_graphql.type.basetype import JSONPayload

LOGGER = logging.getLogger(__name__)


@strawberry.type
class HistoricalUNSEvent:
    """
    Model of a UNS Events
    """

    # Client id of the what/who published this messages
    publisher: str

    # Timestamp of when this event was published/historied
    timestamp: datetime

    # Topic
    topic: str

    # Payload
    payload: JSONPayload
