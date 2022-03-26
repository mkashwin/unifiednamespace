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
     (None, "a/b/c", False), ("+", "a/b/c", False)]
)
def test_isTopicMatching(topicWithWildcard: str, topic: str,
                         expectedResult: bool):
    result = Uns_Mqtt_Historian.isTopicMatching(topicWithWildcard, topic)
    assert result == expectedResult , f"""
            Topic WildCard:{topicWithWildcard}, 
            Topic:{topic}, 
            Expected Result:{expectedResult},
            Actual Result: {result}"""


@pytest.mark.parametrize("message, ignored_attr , filtered_msg" , [
                        ({} , ["key1"] , {}) ,
                        ({"key1": "value1"} , ["key1"] , {}) ,
                        ({"key1": ["value1" , "value2" , "value3"]} , ["key1"] , {}) , 
                        ({"key1": "value1" , "key2": "value2"} , ["key1"] , {"key2": "value2"}) , 
                        ({"key1": "value1" , "key2": "value2"} , ["key1" , "key2"] , {"key1": "value1" , "key2": "value2"} ) ,         
                        ({"key1":  {"key1":"val" , "key2":100} , "key2": "value2" ,  "key3":"value3"} , ["key1" , "key2"] , 
                                    {"key1":  {"key1":"val"} , "key2": "value2" ,  "key3":"value3"} ) , 
                        ({"key1": "value1"} , ["key1", "childKey1"] , {"key1": "value1"}) , 
                        ({"key1": {"child1":"val" , "child2":100}} , ["key1","child1"] , {"key1": {"child2":100}}) ,         
                        ]
)
def test_del_key_from_dict(message:dict , ignored_attr:list, filtered_msg:dict):
    result = Uns_Mqtt_Historian.del_key_from_dict(message, ignored_attr)
    assert result == filtered_msg , f""" message:{message}, 
            Attributes to filter:{ignored_attr}, 
            Expected Result:{filtered_msg},
            Actual Result: {result}"""


def test_filter_ignored_attributes(topic:str, mqtt_message:dict, mqtt_ignored_attribute):
    pytest.fail()