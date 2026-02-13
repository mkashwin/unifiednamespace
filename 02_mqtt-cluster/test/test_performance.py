
import pytest
from uns_mqtt.mqtt_listener import UnsMQTTClient

def test_get_regex_caching():
    """Verify that get_regex_for_topic_with_wildcard is cached."""
    wildcard = "a/+/b/#"

    # Clear cache to start fresh
    UnsMQTTClient.get_regex_for_topic_with_wildcard.cache_clear()

    # First call - Miss
    UnsMQTTClient.get_regex_for_topic_with_wildcard(wildcard)
    info_after_first = UnsMQTTClient.get_regex_for_topic_with_wildcard.cache_info()
    assert info_after_first.misses >= 1
    assert info_after_first.hits == 0

    # Second call - Hit
    UnsMQTTClient.get_regex_for_topic_with_wildcard(wildcard)
    info_after_second = UnsMQTTClient.get_regex_for_topic_with_wildcard.cache_info()
    assert info_after_second.hits >= 1

def test_cached_pattern_caching():
    """Verify that _get_cached_pattern is cached."""
    wildcard = "x/y/+"

    # Clear cache
    UnsMQTTClient._get_cached_pattern.cache_clear()

    # First call via is_topic_matched - Miss
    UnsMQTTClient.is_topic_matched(wildcard, "x/y/z")
    info_after_first = UnsMQTTClient._get_cached_pattern.cache_info()
    assert info_after_first.misses >= 1
    assert info_after_first.hits == 0

    # Second call via is_topic_matched - Hit
    UnsMQTTClient.is_topic_matched(wildcard, "x/y/a")
    info_after_second = UnsMQTTClient._get_cached_pattern.cache_info()
    assert info_after_second.hits >= 1
