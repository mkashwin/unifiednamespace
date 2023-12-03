import pytest
from pydantic import ValidationError
from uns_graphql.input.mqtt_subscription import MQTTTopic, MQTTTopicInput

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
