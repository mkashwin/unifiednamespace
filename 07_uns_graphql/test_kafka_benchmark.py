import asyncio
import time
from unittest.mock import MagicMock, patch

from uns_graphql.subscriptions.kafka import KAFKASubscription
from uns_graphql.input.kafka import KAFKATopicInput
from uns_graphql.graphql_config import KAFKAConfig

async def main():
    topics = [KAFKATopicInput(topic="test_topic")]

    # We want to benchmark how fast we can process X messages
    NUM_MESSAGES = 100000

    mock_consumer = MagicMock()
    # Return valid message then StopIteration
    mock_msg = MagicMock()
    mock_msg.error.return_value = False
    mock_msg.topic.return_value = "test_topic"
    mock_msg.value.return_value = b'{"data": 1}'

    class MockPoll:
        def __init__(self):
            self.count = 0
        def __call__(self, timeout=None):
            if self.count < NUM_MESSAGES:
                self.count += 1
                return mock_msg
            return None # Simulate timeout when done

    mock_consumer.poll.side_effect = MockPoll()

    with patch("uns_graphql.subscriptions.kafka.Consumer", return_value=mock_consumer):
        # We need a small timeout for the mock when it returns None to exit the test
        original_timeout = KAFKAConfig.consumer_poll_timeout
        KAFKAConfig.consumer_poll_timeout = 0.001

        subscription = KAFKASubscription()

        start = time.perf_counter()

        received = 0
        async_gen = subscription.get_kafka_messages(topics)

        try:
            async for msg in async_gen:
                received += 1
                if received >= NUM_MESSAGES:
                    break
        finally:
            await async_gen.aclose()

        end = time.perf_counter()

        KAFKAConfig.consumer_poll_timeout = original_timeout

        print(f"Time taken to process {NUM_MESSAGES} messages: {end - start:.4f} seconds")
        print(f"Messages per second: {NUM_MESSAGES / (end - start):.2f}")

if __name__ == "__main__":
    asyncio.run(main())
