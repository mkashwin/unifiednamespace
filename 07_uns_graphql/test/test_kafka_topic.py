import pytest
from pydantic import ValidationError
from uns_graphql.input.kafka_subscription import KAFKATopic, KAFKATopicInput

# Test data for parameterized tests
test_data_valid = [
    "topic1",
    "level1level2.level3"
    "valid_topic_1",
    "another_valid_topic",
    "topic_123_with_underscores",
]

test_data_invalid = [
    "",  # Empty string (fails min_length constraint)
    "topic_with_invalid@character",  # Invalid character (fails pattern constraint)
    "a" * 101,  # Exceeds max_length constraint
    None,  # None value (not a string)
    123,  # Integer (not a string)
    "a/b/c",  # string with slashes (not a string)
]


@pytest.mark.parametrize("topic", test_data_valid)
def test_valid_topics(topic):
    """
    Test valid topics.

    Tests the validation of valid topics using the `KAFKATopic` constructor.

    Args:
    - topic: A string representing a valid topic.

    Raises:
    - pytest.fail: If a validation error occurs for a valid topic.
    """
    try:
        kafka_topic = KAFKATopic(topic=topic)
        assert kafka_topic.topic == topic
    except ValidationError:
        pytest.fail(f"Validation error for valid topic: {topic}")


@pytest.mark.parametrize("topic", test_data_valid)
def test_valid_topics_input(topic):
    """
    Test valid topics for the Strawberry wrapper over the pydantic base

    Tests the validation of valid topics using `KAFKATopicInput.from_pydantic`
    to convert from `KAFKATopic`.

    Args:
    - topic: A string representing a valid topic.

    Raises:
    - pytest.fail: If a validation error occurs for a valid topic.
    """
    try:
        kafka_topic_input = KAFKATopicInput.from_pydantic(
            KAFKATopic(topic=topic))
        assert kafka_topic_input.topic == topic
    except ValidationError:
        pytest.fail(f"Validation error for valid topic: {topic}")


@pytest.mark.parametrize("topic", test_data_invalid)
def test_invalid_topics(topic):
    """
    Test invalid topic for the Strawberry wrapper over the pydantic base

    Tests the validation of invalid topics using the `KAFKATopic` constructor.

    Args:
    - topic: A value representing an invalid topic.

    Raises:
    - pytest.raises: Expects a validation error for invalid topics.
    """
    with pytest.raises(ValidationError):
        KAFKATopic(topic=topic)


@pytest.mark.parametrize("topic", test_data_invalid)
def test_invalid_topics_input(topic):
    """
    Test invalid topics for input.

    Tests the validation of invalid topics using `KAFKATopicInput.from_pydantic`
    to convert from `KAFKATopic`.

    Args:
    - topic: A value representing an invalid topic.

    Raises:
    - pytest.raises: Expects a validation error for invalid topics.
    """
    with pytest.raises(ValidationError):
        KAFKATopicInput.from_pydantic(KAFKATopic(topic=topic))
