import inspect
import os
import sys
import pytest

# From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
cmd_subfolder = os.path.realpath(
    os.path.abspath(
        os.path.join(
            os.path.split(inspect.getfile(inspect.currentframe()))[0], '..',
            'src')))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)
    sys.path.insert(1, os.path.join(cmd_subfolder,"uns_historian"))

from uns_historian.uns_mqtt_historian import Uns_Mqtt_Historian


@pytest.mark.parametrize(
    "topicWithWildcard,topic,expectedResult",[
     ("#", "a", True), ("#", "a/b/c", True), ("a/#", "a", False),
     ("a/#", "a/b/c", True), ("+", "a", True), ("+", "a/b/c", False),
     (None, "a/b/c", False), ("+", "a/b/c", False), ("topic1","topic1",True)]
)
def test_isTopicMatching(topicWithWildcard: str, topic: str,
                         expectedResult: bool):
    result = Uns_Mqtt_Historian.isTopicMatching(topicWithWildcard, topic)
    assert result == expectedResult , f"""
            Topic WildCard:{topicWithWildcard}, 
            Topic:{topic}, 
            Expected Result:{expectedResult},
            Actual Result: {result}"""


@pytest.mark.parametrize("message, ignored_attr , expected_result" , [
                        ({} , ["key1"] , {}) ,
                        ({"key1": "value1"} , ["key1"] , {}) ,
                        ({"key1": ["value1" , "value2" , "value3"]} , ["key1"] , {}) , 
                        ({"key1": "value1" , "key2": "value2"} , ["key1"] , {"key2": "value2"}) , 
                        ({"key1": "value1" , "key2": "value2"} , ["key1" , "key2"] , {"key1": "value1" , "key2": "value2"} ) ,         
                        ({"key1":  {"key1":"val" , "key2":100} , "key2": "value2" ,  "key3":"value3"} , ["key1" , "key2"] , 
                                    {"key1":  {"key1":"val"} , "key2": "value2" ,  "key3":"value3"} ) , 
                        ({"key1": "value1"} , ["key1", "childKey1"] , {"key1": "value1"}) , 
                        ({"key1": {"child1":"val" , "child2":100}} , ["key1","child1"] , {"key1": {"child2":100}}) ,         
                        ({"key1": {"child1":"val" , "child2":100}, "child1": "value2"} , ["key1","child1"] , {"key1": {"child2":100},"child1": "value2"}) ,         
                        ]
)
def test_del_key_from_dict(message:dict , ignored_attr:list, expected_result:dict):
    """
    Should remove just the key should it be present.
    Test support for nested keys. e.g. the key "parent.child" goes in as ["parent", "ch{}ild"]
    The index of the array always indicates the depth of the key tree
    """
    result = Uns_Mqtt_Historian.del_key_from_dict(message, ignored_attr)
    assert result == expected_result , f""" message:{message}, 
            Attributes to filter:{ignored_attr}, 
            Expected Result:{expected_result},
            Actual Result: {result}"""

@pytest.mark.parametrize("topic,json_dict, mqtt_ignored_attributes, expected_result" , [
    ("topic1", {"timestamp":123456, "val1": 1234 }, {"+":"timestamp"}, {"val1": 1234 }),
    ("topic1", {"timestamp":123456, "val1": 1234 }, {"#":"timestamp"}, {"val1": 1234 }),
    ("topic1", {"timestamp":123456, "val1": 1234 }, {"topic1":"timestamp"}, {"val1": 1234 }),
    ("topic1", {"timestamp":123456, "val1": 1234 }, {"topic2":"timestamp"}, {"timestamp":123456, "val1": 1234 }),
])
def test_filter_ignored_attributes(topic:str, json_dict:dict, mqtt_ignored_attributes, expected_result):
    result = Uns_Mqtt_Historian.filter_ignored_attributes(topic, json_dict, mqtt_ignored_attributes)
    assert result == expected_result , f""" message:{json_dict}, 
            Attributes to filter:{mqtt_ignored_attributes}, 
            Expected Result:{expected_result},
            Actual Result: {result}"""
