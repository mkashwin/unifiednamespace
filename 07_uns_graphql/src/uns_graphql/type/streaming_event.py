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

Type of data to be retrieved from the KAFKA Queues
"""

import strawberry

from uns_graphql.type.basetype import JSONPayload


@strawberry.type
class StreamingMessage:
    """
    Model of a UNS Events
    """

    # Fully qualified path of the namespace including current name
    # Usually maps to the topic where multiple messages were published e.g. ent1/fac1/area5
    topic: str

    # In the UNS KAFKA setup, all bytes payloads are converted to a dict/JSON by the MQTT client prior to publishing to KAFKA
    # Hence the payload only needs to be JSON
    # see 06_uns_kafka uns_kafka.uns_kafka_listener:UNSKafkaMapper.on_message(..)
    payload: JSONPayload

    def __init__(self, topic: str, payload: bytes):
        self.topic = topic
        self.payload = JSONPayload(data=payload.decode("utf-8"))
