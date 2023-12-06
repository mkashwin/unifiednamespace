from typing import List
from unittest.mock import MagicMock, patch

import pytest
from uns_graphql.input.mqtt_subscription import MQTTTopic, MQTTTopicInput
from uns_graphql.subscriptions import Subscription
from uns_graphql.type.streaming_event import StreamingMessage
