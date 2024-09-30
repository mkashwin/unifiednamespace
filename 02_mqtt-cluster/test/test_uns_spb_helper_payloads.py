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

All tests for uns_spb_helper with different payloads
"""

import pytest

from uns_sparkplugb import uns_spb_helper
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload
from uns_sparkplugb.uns_spb_enums import SPBMetricDataTypes
from uns_sparkplugb.uns_spb_helper import SpBMessageGenerator


@pytest.fixture(autouse=True)
def setup_alias_map():
    # clear the alias map for each test
    spb_mgs_gen = SpBMessageGenerator()
    spb_mgs_gen.alias_name_map.clear()


@pytest.mark.parametrize(
    "spb_dict,renamed_dict",
    [
        ({"test": "value"}, {"test": "value"}),
        (
            {
                "timestamp": "1671554024644",
                "metrics": [
                    {
                        "name": "Inputs/A",
                        "timestamp": "1486144502122",
                        "alias": "0",
                        "datatype": 11,
                        "boolean_value": False,
                    },
                    {
                        "name": "Inputs/B",
                        "timestamp": "1486144502122",
                        "alias": "1",
                        "datatype": 11,
                        "boolean_value": False,
                    },
                    {
                        "name": "Outputs/E",
                        "timestamp": "1486144502122",
                        "alias": "2",
                        "datatype": 11,
                        "boolean_value": False,
                    },
                    {
                        "name": "Outputs/F",
                        "timestamp": "1486144502122",
                        "alias": "3",
                        "datatype": 11,
                        "boolean_value": False,
                    },
                    {
                        "name": "Properties/Hardware Make",
                        "timestamp": "1486144502122",
                        "alias": "4",
                        "datatype": 12,
                        "string_value": "Sony",
                    },
                    {
                        "name": "Properties/Weight",
                        "timestamp": "1486144502122",
                        "alias": "5",
                        "datatype": 3,
                        "int_value": 200,
                    },
                ],
                "seq": "0",
            },
            {
                "timestamp": 1671554024644,
                "metrics": [
                    {
                        "name": "Inputs/A",
                        "timestamp": 1486144502122,
                        "alias": 0,
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Inputs/B",
                        "timestamp": 1486144502122,
                        "alias": 1,
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Outputs/E",
                        "timestamp": 1486144502122,
                        "alias": 2,
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Outputs/F",
                        "timestamp": 1486144502122,
                        "alias": 3,
                        "datatype": 11,
                        "value": False,
                    },
                    {
                        "name": "Properties/Hardware Make",
                        "timestamp": 1486144502122,
                        "alias": 4,
                        "datatype": 12,
                        "value": "Sony",
                    },
                    {
                        "name": "Properties/Weight",
                        "timestamp": 1486144502122,
                        "alias": 5,
                        "datatype": 3,
                        "value": 200,
                    },
                ],
                "seq": 0,
            },
        ),
        ("not a dict", "not a dict"),
    ],
)
def test__correct_keys_and_value_types(spb_dict: dict, renamed_dict: dict):
    assert uns_spb_helper._fix_keys_and_value_types(spb_dict) == renamed_dict


# #########  Test Data Payload 1 #########
bytes_payload_1: bytes = (
    b"\x08\xc4\x89\x89\x83\xd30\x12\x17\n\x08Inputs/A\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ "
    b"\x0bp\x00\x12\x17\n\x08Inputs/B\x10\x01\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\t"
    b"Outputs/E\x10\x02\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\tOutputs/F\x10\x03\x18\xea\xf2\xf5\xa8\xa0+ "
    b"\x0bp\x00\x12+\n\x18Properties/Hardware Make\x10\x04\x18\xea\xf2\xf5\xa8\xa0+ \x0cz\x04Sony\x12!\n\x11"
    b"Properties/Weight\x10\x05\x18\xea\xf2\xf5\xa8\xa0+ \x03P\xc8\x01\x18\x00"
)
# convert binary string to Payload Object
spb_payload_1 = Payload()
spb_payload_1.ParseFromString(bytes_payload_1)

dict_payload_1 = {
    "timestamp": 1671554024644,
    "metrics": [
        {"name": "Inputs/A", "alias": 0, "timestamp": 1486144502122, "datatype": 11, "value": False},
        {"name": "Inputs/B", "alias": 1, "timestamp": 1486144502122, "datatype": 11, "value": False},
        {"name": "Outputs/E", "alias": 2, "timestamp": 1486144502122, "datatype": 11, "value": False},
        {"name": "Outputs/F", "alias": 3, "timestamp": 1486144502122, "datatype": 11, "value": False},
        {
            "name": "Properties/Hardware Make",
            "alias": 4,
            "timestamp": 1486144502122,
            "datatype": 12,
            "value": "Sony",
        },
        {"name": "Properties/Weight", "alias": 5, "timestamp": 1486144502122, "datatype": 3, "value": 200},
    ],
    "seq": 0,
}

# #########  Test Data Payload 2 #########
bytes_payload_2: bytes = (
    b"\x08\x93\xde\xa0\xcb\x05\x12-\n\x0bInputs/UUID\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ "
    b'\x0fz\x13unique_id_123456789\x12"\n\x0cInputs/bytes\x10\x01\x18\xea\xf2\xf5\xa8\xa0+ '
    b"\x11\x82\x01\x06\x0c\x00\x00\x004\xd0\x12+\n\x0bInputs/file\x10\x02\x18\xea\xf2\xf5\xa8\xa0+ "
    b"\x12\x82\x01\x10\xc7\xd0\x90u$\x01\x00\x00\xb8\xba\xb8\x97\x81\x01\x00\x00\x12\xe3\x01\n\x0e"
    b"Inputs/dataset\x10\x03\x18\xea\xf2\xf5\xa8\xa0+ \x10\x8a\x01\xc4\x01\x08\x05\x12\x06uint32\x12"
    b'\x06double\x12\x05int64\x12\x06string\x12\x07boolean\x18\x07\x18\n\x18\x08\x18\x0c\x18\x0b".\n'
    b"\x02\x08\n\n\t!\x00\x00\x00\x00\x00\x00Y@\n\x04\x10\xa0\x8d\x06\n\x132\x11I am dataset row1\n\x02("
    b'\x00".\n\x02\x08\x14\n\t!\x00\x00\x00\x00\x00\x00i@\n\x04\x10\xc0\x9a\x0c\n\x132\x11I am dataset row2\n\x02(\x01".\n\x02'
    b"\x08\x1e\n\t!\x00\x00\x00\x00\x00\xc0r@\n\x04\x10\xe0\xa7\x12\n\x132\x11I am dataset row3\n\x02(\x00\x18\x00"
)
spb_payload_2 = Payload()
spb_payload_2.ParseFromString(bytes_payload_2)
dict_payload_2: dict = {
    "timestamp": 1500000019,
    "metrics": [
        {"name": "Inputs/UUID", "alias": 0, "timestamp": 1486144502122, "datatype": 15, "value": "unique_id_123456789"},
        {"name": "Inputs/bytes", "alias": 1, "timestamp": 1486144502122, "datatype": 17, "value": b"\x0c\x00\x00\x004\xd0"},
        {
            "name": "Inputs/file",
            "alias": 2,
            "timestamp": 1486144502122,
            "datatype": 18,
            "value": b"\xc7\xd0\x90u$\x01\x00\x00\xb8\xba\xb8\x97\x81\x01\x00\x00",
        },
        {
            "name": "Inputs/dataset",
            "alias": 3,
            "timestamp": 1486144502122,
            "datatype": 16,
            "value": {
                "num_of_columns": 5,
                "columns": ["uint32", "double", "int64", "string", "boolean"],
                "types": [7, 10, 8, 12, 11],
                "rows": [
                    {
                        "elements": [
                            {"value": 10},
                            {"value": 100.0},
                            {"value": 100000},
                            {"value": "I am dataset row1"},
                            {"value": False},
                        ]
                    },
                    {
                        "elements": [
                            {"value": 20},
                            {"value": 200.0},
                            {"value": 200000},
                            {"value": "I am dataset row2"},
                            {"value": True},
                        ]
                    },
                    {
                        "elements": [
                            {"value": 30},
                            {"value": 300.0},
                            {"value": 300000},
                            {"value": "I am dataset row3"},
                            {"value": False},
                        ]
                    },
                ],
            },
        },
    ],
    "seq": 0,
}

# #########  Test Data Payload 3 #########
bytes_payload_3: bytes = (
    b"\x08\x8e\xc8\xaf\xa0%\x12\x1a\n\x0bInputs/int8\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ \x01P\n\x12\x1f\n\x0fInputs/int8.Neg"
    b"\x10\x01\x18\xeb\xf2\xf5\xa8\xa0+ \x01P\xf6\x01\x12\x1b\n\x0cInputs/uint8\x10\x02\x18\xeb\xf2\xf5\xa8\xa0+ \x05P\n"
    b"\x12!\n\x10Inputs/int16.neg\x10\x03\x18\xeb\xf2\xf5\xa8\xa0+ \x02P\x9c\xff\x03\x12\x1c\n\rInputs/uint16\x10\x04\x18"
    b"\xeb\xf2\xf5\xa8\xa0+ \x06Pd\x12 \n\x10Properties/int32\x10\x05\x18\xea\xf2\xf5\xa8\xa0+ \x03P\xc8\x01\x12'\n\x14"
    b"Properties/int32.neg\x10\x06\x18\xea\xf2\xf5\xa8\xa0+ \x03P\xb8\xfe\xff\xff\x0f\x12!\n\x11Properties/Uint32\x10\x07\x18"
    b"\xea\xf2\xf5\xa8\xa0+ \x07P\xc8\x01\x12$\n\x10Outputs/DateTime\x10\x08\x18\xea\xf2\xf5\xa8\xa0+ \rX\xea\xf2\xf5\xa8"
    b"\xa0+\x12\x1f\n\x0eOutputs/Uint64\x10\t\x18\xea\xf2\xf5\xa8\xa0+ \x08X\xc0\xc4\x07\x12)\n\x11Outputs/int64.Neg"
    b"\x10\n\x18\xea\xf2\xf5\xa8\xa0+ \x04X\xc0\xbb\xf8\xff\xff\xff\xff\xff\xff\x01\x12\x1b\n\x0cOutputs/Bool\x10\x0b\x18\xea"
    b"\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x1f\n\rOutputs/Float\x10\x0c\x18\xea\xf2\xf5\xa8\xa0+ \te\x92\xcb\x8f?\x12$\n\x0e"
    b"Outputs/Double\x10\r\x18\xea\xf2\xf5\xa8\xa0+ \niEGr\xf9Q\xde\xfd@\x12$\n\x11Properties/String\x10\x0e\x18\xea\xf2\xf5"
    b"\xa8\xa0+ \x0cz\x04Sony\x12;\n\x0fProperties/Text\x10\x0f\x18\xea\xf2\xf5\xa8\xa0+ \x0ez\x1dSony made this device in "
    b"1986\x18\x00"
)

spb_payload_3 = Payload()
spb_payload_3.ParseFromString(bytes_payload_3)
dict_payload_3: dict = {
    "timestamp": 10000000014,
    "metrics": [
        {"name": "Inputs/int8", "alias": 0, "timestamp": 1486144502122, "datatype": 1, "value": 10},
        {"name": "Inputs/int8.Neg", "alias": 1, "timestamp": 1486144502123, "datatype": 1, "value": 246},
        {"name": "Inputs/uint8", "alias": 2, "timestamp": 1486144502123, "datatype": 5, "value": 10},
        {"name": "Inputs/int16.neg", "alias": 3, "timestamp": 1486144502123, "datatype": 2, "value": 65436},
        {"name": "Inputs/uint16", "alias": 4, "timestamp": 1486144502123, "datatype": 6, "value": 100},
        {"name": "Properties/int32", "alias": 5, "timestamp": 1486144502122, "datatype": 3, "value": 200},
        {"name": "Properties/int32.neg", "alias": 6, "timestamp": 1486144502122, "datatype": 3, "value": 4294967096},
        {"name": "Properties/Uint32", "alias": 7, "timestamp": 1486144502122, "datatype": 7, "value": 200},
        {"name": "Outputs/DateTime", "alias": 8, "timestamp": 1486144502122, "datatype": 13, "value": 1486144502122},
        {"name": "Outputs/Uint64", "alias": 9, "timestamp": 1486144502122, "datatype": 8, "value": 123456},
        {
            "name": "Outputs/int64.Neg",
            "alias": 10,
            "timestamp": 1486144502122,
            "datatype": 4,
            "value": 18446744073709428160,
        },
        {"name": "Outputs/Bool", "alias": 11, "timestamp": 1486144502122, "datatype": 11, "value": False},
        {"name": "Outputs/Float", "alias": 12, "timestamp": 1486144502122, "datatype": 9, "value": 1.1234},
        {"name": "Outputs/Double", "alias": 13, "timestamp": 1486144502122, "datatype": 10, "value": 122341.1234},
        {"name": "Properties/String", "alias": 14, "timestamp": 1486144502122, "datatype": 12, "value": "Sony"},
        {
            "name": "Properties/Text",
            "alias": 15,
            "timestamp": 1486144502122,
            "datatype": 14,
            "value": "Sony made this device in 1986",
        },
    ],
    "seq": 0,
}

# #########  Test Data Payload 4 #########
# spell-checker:disable
bytes_payload_4: bytes = (
    b"a8a42d159d5c815a80629c7ce443d404B\x0bdescription\x82\x01\x10I am a text file"
    b"a8a42d159d5c815a80629c7ce443d404B\x0bdescription\x82\x01\x10I am a text file"
)
# spell-checker:enable
spb_payload_4 = Payload()
spb_payload_4.ParseFromString(bytes_payload_4)
dict_payload_4: dict = {
    "metrics": [
        {
            "name": "test metadata",
            "timestamp": 1705260080276,
            "datatype": 18,
            "metadata": {
                "is_multi_part": False,
                "content_type": "utf-8",
                "size": 57,
                "seq": 1,
                "file_name": "test.txt",
                "file_type": "txt",
                "md5": "a8a42d159d5c815a80629c7ce443d404",
                "description": "description",
            },
            "value": bytes("I am a text file", "utf-8"),
        }
    ]
}

# #########  Test Data Payload 5 #########
# spell-checker:disable
bytes_payload_5: bytes = (
    b"\x08\xa2\xac\x85\x99\x08\x12\x1e\n\x0bInputs/int8\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ \x16\x82"
    b"\x01\x03\n\x0b\xe9\x12 \n\x0cInputs/int16\x10\x01\x18\xea\xf2\xf5\xa8\xa0+ \x17\x82\x01\x04\xd0\x8a0u\x12$\n\x0c"
    b"Inputs/int32\x10\x02\x18\xea\xf2\xf5\xa8\xa0+ \x18\x82\x01\x08\xff\xff\xff\xff\xfa\xaf\xcb\x12\x12,\n\x0cInputs/int64"
    b"\x10\x03\x18\xea\xf2\xf5\xa8\xa0+ \x19\x82\x01\x10\xce\x06r\xac\x18\x9c\xba\xc4\xc4\xba\x9c\x18\xacr\x06\xce\x12\x1e\n"
    b"\x0cInputs/uint8\x10\x04\x18\xea\xf2\xf5\xa8\xa0+ \x1a\x82\x01\x02\x17\xfa\x12!\n\rInputs/uint16\x10\x05\x18\xea\xf2\xf5"
    b"\xa8\xa0+ \x1b\x82\x01\x04\x1e\x00\x88\xcc\x12%\n\rInputs/uint32\x10\x06\x18\xea\xf2\xf5\xa8\xa0+ \x1c\x82\x01\x084\x00"
    b"\x00\x00I\xfbU\xc4\x12-\n\rInputs/uint64\x10\x07\x18\xea\xf2\xf5\xa8\xa0+ \x1d\x82\x01\x10}\x14\x00\x00\x00\x00\x00\x00"
    b"\xd9\x9e\x02\xd1\xb2v7\xe4\x12/\n\x0fInputs/datetime\x10\x08\x18\xea\xf2\xf5\xa8\xa0+ \x1d\x82\x01\x10jy\x1d\x05Z\x01"
    b'\x00\x00"\x85\x1d\x05Z\x01\x00\x00\x12#\n\x0eInputs/boolean\x10\t\x18\xea\xf2\xf5\xa8\xa0+  \x82\x01\x05\x03\x00\x00'
    b"\x00\xa0\x12[\n\rInputs/string\x10\n\x18\xea\xf2\xf5\xa8\xa0+ !\x82\x01>4920616d206120737472696e67"
    b"\x004920746f6f20616d206120737472696e67\x00\x18\x00"
)
spb_payload_5 = Payload()
spb_payload_5.ParseFromString(bytes_payload_5)
dict_payload_5: dict = {
    "timestamp": 2200000034,
    "metrics": [
        {"name": "Inputs/int8", "alias": 0, "timestamp": 1486144502122, "datatype": 22, "value": [10, 11, -23]},
        {"name": "Inputs/int16", "alias": 1, "timestamp": 1486144502122, "datatype": 23, "value": [-30000, 30000]},
        {"name": "Inputs/int32", "alias": 2, "timestamp": 1486144502122, "datatype": 24, "value": [-1, 315338746]},
        {
            "name": "Inputs/int64",
            "alias": 3,
            "timestamp": 1486144502122,
            "datatype": 25,
            "value": [-4270929666821191986, -3601064768563266876],
        },
        {"name": "Inputs/uint8", "alias": 4, "timestamp": 1486144502122, "datatype": 26, "value": [23, 250]},
        {"name": "Inputs/uint16", "alias": 5, "timestamp": 1486144502122, "datatype": 27, "value": [30, 52360]},
        {"name": "Inputs/uint32", "alias": 6, "timestamp": 1486144502122, "datatype": 28, "value": [52, 3293969225]},
        {
            "name": "Inputs/uint64",
            "alias": 7,
            "timestamp": 1486144502122,
            "datatype": 29,
            "value": [5245, 16444743074749521625],
        },
        {
            "name": "Inputs/datetime",
            "alias": 8,
            "timestamp": 1486144502122,
            "datatype": 29,
            "value": [1486144502122, 1486144505122],
        },
        {"name": "Inputs/boolean", "alias": 9, "timestamp": 1486144502122, "datatype": 32, "value": [True, False, True]},
        {
            "name": "Inputs/string",
            "alias": 10,
            "timestamp": 1486144502122,
            "datatype": 33,
            "value": ["I am a string", "I too am a string"],
        },
    ],
    "seq": 0,
}

# #########  Test Data Payload 6 #########
bytes_payload_6: bytes = (
    b"\x12\xd7\x01\n\x0ftest properties\x18\x82\xf6\xc6\xcb\xd01 \x0cJ\x9a\x01\n\x0cproperty set\n\x11property set list\x12'"
    b"\x08\x14J#\n\x06key1_1\n\x06key1_2\x12\n\x08\x0cB\x06nested\x12\x05\x08\x07\x18\xb9`\x12N\x08\x15RJ\n#\n\x06key1_1\n"
    b"\x06key1_2\x12\n\x08\x0cB\x06nested\x12\x05\x08\x07\x18\xb9`\n#\n\x06key1_1\n\x06key1_2\x12\n\x08\x0cB\x06nested\x12\x05"
    b"\x08\x07\x18\xb9`z\x1eTest various property settings"
)
spb_payload_6 = Payload()
spb_payload_6.ParseFromString(bytes_payload_6)
dict_payload_6: dict = {
    "metrics": [
        {
            "name": "test properties",
            "timestamp": 1705260464898,
            "datatype": 12,
            "properties": {
                "keys": ["property set", "property set list"],
                "values": [
                    {
                        "type": 20,
                        "value": {
                            "keys": ["key1_1", "key1_2"],
                            "values": [{"type": 12, "value": "nested"}, {"type": 7, "value": 12345}],
                        },
                    },
                    {
                        "type": 21,
                        "value": {
                            "propertyset": [
                                {
                                    "keys": ["key1_1", "key1_2"],
                                    "values": [{"type": 12, "value": "nested"}, {"type": 7, "value": 12345}],
                                },
                                {
                                    "keys": ["key1_1", "key1_2"],
                                    "values": [{"type": 12, "value": "nested"}, {"type": 7, "value": 12345}],
                                },
                            ]
                        },
                    },
                ],
            },
            "value": "Test various property settings",
        }
    ]
}
# #########  Test Data Ends #########
# spell-checker:enable


@pytest.mark.parametrize(
    "payload_bytes,expected_dict",
    [
        (bytes_payload_1, dict_payload_1),
        (bytes_payload_2, dict_payload_2),
        (bytes_payload_3, dict_payload_3),
        (bytes_payload_4, dict_payload_4),
        (bytes_payload_5, dict_payload_5),
        (bytes_payload_6, dict_payload_6),
    ],
)
def test_convert_spb_bytes_payload_to_dict(payload_bytes: bytes, expected_dict):
    assert uns_spb_helper.convert_spb_bytes_payload_to_dict(payload_bytes) == expected_dict


@pytest.mark.parametrize(
    "dict_payload, spb_payload",
    [
        (dict_payload_1, spb_payload_1),
        (dict_payload_2, spb_payload_2),
        (dict_payload_3, spb_payload_3),
        (dict_payload_4, spb_payload_4),
        (dict_payload_5, spb_payload_5),
        (dict_payload_6, spb_payload_6),
    ],
)
def test_convert_dict_payload_bytes(dict_payload: dict, spb_payload: Payload):
    assert uns_spb_helper.convert_dict_to_payload(dict_payload) == spb_payload


def test_get_seq_num():
    """
    Test case for Spb_Message_Generator#get_seq_num()
    """
    sparkplug_message = SpBMessageGenerator()
    # Test sequence
    old_sequence = sparkplug_message.get_seq_num()
    assert old_sequence == 0, f"Sequence number should start with 0 but stated with {old_sequence}"

    for count in range(270):  # choose a number greater than 256 to test the counter reset
        new_sequence = sparkplug_message.get_seq_num()
        if old_sequence < 255:
            assert old_sequence == new_sequence - 1, f"Loop {count}: Sequence not incrementing-> {old_sequence}:{new_sequence}"
        else:
            assert new_sequence == 0, f"Loop {count}: Sequence number should reset to 0 after 256 but got  {new_sequence}"
        old_sequence = new_sequence


def test_get_birth_seq_num():
    """
    Test case for Spb_Message_Generator#get_birth_seq_num()
    """
    # Test sequence
    sparkplug_message = SpBMessageGenerator()
    old_sequence = sparkplug_message.get_birth_seq_num()
    assert old_sequence == 0, f"Sequence number should start with 0 but stated with {old_sequence}"

    for count in range(260):  # choose a number greater than 256 to test the counter reset
        new_sequence = sparkplug_message.get_birth_seq_num()
        if old_sequence < 255:
            assert old_sequence == new_sequence - 1, f"Loop {count}: Sequence not incrementing-> {old_sequence}:{new_sequence}"
        else:
            assert new_sequence == 0, f"Loop {count}: Sequence number should reset to 0 after 256 but got  {new_sequence}"
        old_sequence = new_sequence


@pytest.mark.parametrize(
    "alias, timestamp, expected_exception",
    [
        (None, None, ValueError),  # Missing required parameters
        (2000, None, ValueError),  # Alias without name set
        (1, 173476070, ValueError),  # Alias without a mapped name
    ],
)
def test__get_metric_wrapper_exception(alias, timestamp, expected_exception):
    spb_mgs_generator = SpBMessageGenerator()
    with pytest.raises(expected_exception):
        spb_mgs_generator._get_metric_wrapper(Payload(), name=None, alias=alias, timestamp=timestamp)
    # test negative if alias was provided
    if alias is not None:
        spb_mgs_generator._get_metric_wrapper(Payload(), name="Name 1", alias=alias, timestamp=timestamp)
        with pytest.raises(expected_exception):
            spb_mgs_generator._get_metric_wrapper(Payload(), name="Name 2", alias=alias, timestamp=timestamp)


@pytest.mark.parametrize(
    "name, alias, timestamp",
    [
        ("SomeName", 123, None),
        ("SomeName", 123, 123345),
        ("SomeName", None, 123345),
    ],
)
def test__get_metric_wrapper(name, alias, timestamp):
    spb_mgs_generator = SpBMessageGenerator()
    payload = Payload()
    metric_1 = spb_mgs_generator._get_metric_wrapper(payload, name=name, alias=alias, timestamp=timestamp)
    assert metric_1.name == name
    assert metric_1.timestamp is not None

    if alias is not None:
        assert metric_1.alias == alias
        # check for ability to create a metric with alias and name
        metric_2 = spb_mgs_generator._get_metric_wrapper(payload, name=name, alias=alias, timestamp=timestamp)
        assert metric_2.name == name
        assert metric_2.alias == alias
        assert metric_2.timestamp is not None

        # check for ability to create a metric with alias and without name
        metric_3 = spb_mgs_generator._get_metric_wrapper(payload, name=None, alias=alias, timestamp=timestamp)
        assert metric_3.alias == alias
        assert spb_mgs_generator.alias_name_map[alias] == name


def test_get_node_death_payload():
    """
    Test case for Spb_Message_Generator#get_node_death_payload()
    """
    sparkplug_message = SpBMessageGenerator()
    payload = sparkplug_message.get_node_death_payload()

    assert isinstance(payload, Payload)
    metrics = payload.metrics
    assert len(metrics) == 1

    assert metrics[0].name == "bdSeq"
    assert metrics[0].timestamp is not None
    assert metrics[0].datatype == SPBMetricDataTypes.Int64
    assert metrics[0].long_value == 0


def test_get_node_birth_payload():
    """
    Test case for Spb_Message_Generator#get_node_birth_payload()
    """
    spb_mgs_generator = SpBMessageGenerator()
    spb_mgs_generator.get_node_death_payload()
    payload_node1 = spb_mgs_generator.get_node_birth_payload()
    assert isinstance(payload_node1, Payload)
    assert payload_node1.seq == 0

    metrics = payload_node1.metrics
    assert len(metrics) == 1

    assert metrics[0].name == "bdSeq"
    assert metrics[0].timestamp is not None
    assert metrics[0].datatype == SPBMetricDataTypes.Int64
    assert metrics[0].long_value == 1


def test_get_node_data_payload():
    """
    Test case for Spb_Message_Generator#get_node_data_payload()
    """
    sparkplug_message = SpBMessageGenerator()
    sparkplug_message.get_node_death_payload()
    payload = sparkplug_message.get_node_data_payload()
    assert isinstance(payload, Payload)
    assert payload.seq == 0

    metrics = payload.metrics
    assert len(metrics) == 1

    assert metrics[0].name == "bdSeq"
    assert metrics[0].timestamp is not None
    assert metrics[0].datatype == SPBMetricDataTypes.Int64
    assert metrics[0].long_value == 1


def test_get_device_birth_payload():
    """
    Test case for Spb_Message_Generator#get_device_birth_payload()
    """
    sparkplug_message = SpBMessageGenerator()
    payload_device_1 = sparkplug_message.get_device_birth_payload()

    assert payload_device_1.timestamp is not None
    assert payload_device_1.seq == 0
    # create second message to check sequence is correct
    payload_device_2 = sparkplug_message.get_device_birth_payload()
    assert payload_device_2.timestamp is not None
    assert payload_device_2.seq == 1
