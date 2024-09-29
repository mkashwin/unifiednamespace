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
import strawberry
from pydantic import ValidationError

from uns_graphql.input.mqtt import MQTTTopic, MQTTTopicInput

test_data_valid = [
    "valid_topic_1",
    "another_valid_topic",
    "topic/with/slashes",
    "topic/level/+/wildcard",
    "level1/level2/level3/level4",
    "+/wildcard/usage",
    "+/wild.card/usa.ge/dots",
    "a/+/b/+/c",  # Multiple single-level wildcards in a topic level
    "#",  # multi level wildcard
    "test/uns/#",
    "spBv1.0/uns_group/#",
    "+",  # single-level wildcard
]

test_data_invalid = [
    "",  # Empty string
    "topic_with_invalid@character",  # Invalid character
    "a" * 101,  # Exceeds max_length constraint
    None,  # None value
    123,  # Integer value
    "a/b/c#",  # wildcard  mixed with topic
    "a/#/b",  # '#' not at the end
    "+/+#",  # Multiple multi-level wildcards
]


@pytest.mark.parametrize("topic", test_data_valid)
def test_valid_topics(topic):
    # Test valid topics via constructor
    try:
        mqtt_topic = MQTTTopic(topic=topic)
        assert mqtt_topic.topic == topic
    except ValidationError:
        pytest.fail(f"Validation error for valid topic: {topic}")


@pytest.mark.parametrize("topic", test_data_valid)
def test_valid_topics_input(topic):
    # Test valid topics via constructor
    try:
        mqtt_topic_input = MQTTTopicInput.from_pydantic(MQTTTopic(topic=topic))
        assert mqtt_topic_input.topic == topic
    except ValidationError:
        pytest.fail(f"Validation error for valid topic: {topic}")


@pytest.mark.parametrize("topic", test_data_invalid)
def test_invalid_topics(topic):
    # Test invalid topics via constructor
    with pytest.raises(ValidationError):
        MQTTTopic(topic=topic)


@pytest.mark.parametrize("topic", test_data_invalid)
def test_invalid_topics_input(topic):
    # Convert the Pydantic object to the Strawberry input type
    with pytest.raises(ValidationError):
        MQTTTopicInput.from_pydantic(MQTTTopic(topic=topic))


@pytest.mark.parametrize(
    "topic",
    [
        "ent1/fac1/area5",
        "spBv1.0/STATE/scada_1",
        "spBv1.0/uns_group/NBIRTH/eon1",
    ],
)
def test_strawberry_type(topic: str):
    @strawberry.type
    class Query:
        @strawberry.field
        def get_topic(self, inputs: MQTTTopicInput) -> str:
            return inputs.topic

    schema = strawberry.Schema(query=Query, types=[MQTTTopicInput])

    input_data = {"topic": f"{topic}"}

    result = schema.execute_sync(
        query="query ($inputs: MQTTTopicInput!) { getTopic(inputs: $inputs) }",  # Update the query here
        root_value=Query(),
        variable_values={"inputs": input_data},
    )

    assert not result.errors
