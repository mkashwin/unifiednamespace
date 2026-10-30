import asyncio
import time
import threading
from unittest.mock import MagicMock, patch

from uns_graphql.subscriptions.kafka import KAFKASubscription
from uns_graphql.input.kafka import KAFKATopicInput
from uns_graphql.graphql_config import KAFKAConfig

async def other_async_task():
    """Simulate another async task on the event loop, e.g. handling another GraphQL request."""
    iterations = 0
    start = time.perf_counter()
    while time.perf_counter() - start < 1.0:
        await asyncio.sleep(0.01)
        iterations += 1
    return iterations

async def main():
    topics = [KAFKATopicInput(topic="test_topic")]

    mock_consumer = MagicMock()

    class SlowMockPoll:
        def __call__(self, timeout=None):
            # Simulate a blocking network call (I/O)
            time.sleep(0.1)
            return None

    mock_consumer.poll.side_effect = SlowMockPoll()

    with patch("uns_graphql.subscriptions.kafka.Consumer", return_value=mock_consumer):
        # We need a small timeout for the mock when it returns None to exit the test
        original_timeout = KAFKAConfig.consumer_poll_timeout
        KAFKAConfig.consumer_poll_timeout = 0.1

        subscription = KAFKASubscription()

        # Run kafka listener and another task concurrently
        async def run_listener():
            async_gen = subscription.get_kafka_messages(topics)
            try:
                # We'll just run it for 1 second then cancel
                async with asyncio.timeout(1.0):
                    async for msg in async_gen:
                        pass
            except TimeoutError:
                pass
            finally:
                await async_gen.aclose()

        t1 = asyncio.create_task(run_listener())
        t2 = asyncio.create_task(other_async_task())

        await asyncio.gather(t1, t2)

        iterations = t2.result()
        print(f"Iterations of other async task (should be ~100 in 1 second if non-blocking): {iterations}")

if __name__ == "__main__":
    asyncio.run(main())
