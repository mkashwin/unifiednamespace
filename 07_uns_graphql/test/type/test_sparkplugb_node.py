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

import math
from ast import literal_eval
from datetime import UTC, datetime

import pytest
import strawberry
from uns_sparkplugb import uns_spb_helper
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload
from uns_sparkplugb.uns_spb_enums import SPBDataSetDataTypes, SPBMetricDataTypes, SPBParameterTypes, SPBPropertyValueTypes
from uns_sparkplugb.uns_spb_helper import SpBMessageGenerator

from uns_graphql.type.basetype import BytesPayload
from uns_graphql.type.sparkplugb_node import (
    SPBDataSet,
    SPBDataSetRow,
    SPBDataSetValue,
    SPBMetadata,
    SPBMetric,
    SPBNode,
    SPBPrimitive,
    SPBPropertySet,
    SPBPropertyValue,
    SPBTemplate,
    SPBTemplateParameter,
)

FLOAT_PRECISION = 4  # Decimal precision for float comparisons


@pytest.mark.parametrize(
    "value, expected_value",
    [
        (100, "100"),  # int
        (100.123, "100.123"),  # float
        ("str", "str"),  # str
        (True, "True"),  # bool
        ([100, 200, 300], "[100, 200, 300]"),  # int array
        ([1.123, 2.345, 3.456], "[1.123, 2.345, 3.456]"),  # float array
        ([True, False, True], "[True, False, True]"),  # bool array
        (["str1", "str2", "str3"], "['str1', 'str2', 'str3']"),  # str array
    ],
)
def test_spb_primitive(value, expected_value):
    assert SPBPrimitive(value).data == expected_value == str(value)


sample_binary_spb_payload: bytes = (
    b"\x08\xc4\x89\x89\x83\xd30\x12\x17\n\x08Inputs/A\x10\x00\x18\xea\xf2\xf5\xa8\xa0+ "
    b"\x0bp\x00\x12\x17\n\x08Inputs/B\x10\x01\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\t"
    b"Outputs/E\x10\x02\x18\xea\xf2\xf5\xa8\xa0+ \x0bp\x00\x12\x18\n\tOutputs/F\x10\x03\x18\xea\xf2\xf5\xa8\xa0+ "
    b"\x0bp\x00\x12+\n\x18Properties/Hardware Make\x10\x04\x18\xea\xf2\xf5\xa8\xa0+ \x0cz\x04Sony\x12!\n\x11"
    b"Properties/Weight\x10\x05\x18\xea\xf2\xf5\xa8\xa0+ \x03P\xc8\x01\x18\x00"
)


def create_dummy_dataset() -> Payload.DataSet:
    """
    utility method to create a dataset
    """

    row1 = Payload.DataSet.Row(
        elements=[
            Payload.DataSet.DataSetValue(int_value=10),
            Payload.DataSet.DataSetValue(double_value=100.0),
            Payload.DataSet.DataSetValue(long_value=100000),
            Payload.DataSet.DataSetValue(string_value="I am dataset row1"),
            Payload.DataSet.DataSetValue(boolean_value=False),
        ]
    )
    row2 = Payload.DataSet.Row(
        elements=[
            Payload.DataSet.DataSetValue(int_value=20),
            Payload.DataSet.DataSetValue(double_value=200.0),
            Payload.DataSet.DataSetValue(long_value=200000),
            Payload.DataSet.DataSetValue(string_value="I am dataset row2"),
            Payload.DataSet.DataSetValue(boolean_value=True),
        ]
    )
    row3 = Payload.DataSet.Row(
        elements=[
            Payload.DataSet.DataSetValue(int_value=30),
            Payload.DataSet.DataSetValue(double_value=300.0),
            Payload.DataSet.DataSetValue(long_value=300000),
            Payload.DataSet.DataSetValue(string_value="I am dataset row3"),
            Payload.DataSet.DataSetValue(boolean_value=False),
        ]
    )

    data_set: Payload.DataSet = Payload.DataSet(
        num_of_columns=5,
        columns=["uint32", "double", "int64", "string", "boolean"],
        rows=[row1, row2, row3],
        types=[
            SPBDataSetDataTypes.UInt32,
            SPBDataSetDataTypes.Double,
            SPBDataSetDataTypes.UInt64,
            SPBDataSetDataTypes.String,
            SPBDataSetDataTypes.Boolean,
        ],
    )
    return data_set


def create_dummy_template() -> Payload.Template:
    spb_mgs_gen = SpBMessageGenerator()
    payload = Payload()

    template: Payload.Template = spb_mgs_gen.init_template_metric(
        payload=payload,
        name="Dummy Template",
        metrics=[Payload.Metric(
            name="met1", datatype=SPBMetricDataTypes.Boolean, boolean_value=True)],
        version="v_0.1.1",
        template_ref=None,
        parameters=[("prop1", SPBParameterTypes.UInt32, 100),
                    ("prop2", SPBParameterTypes.String, "property string")],
    )

    return template


list_of_metrics_dict: list[dict] = [
    {
        "name": "Inputs/int8",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Int8,
        "value": 10,
    },
    {
        "name": "Inputs/int8.Neg",
        "timestamp": 1486144502123,
        "datatype": SPBMetricDataTypes.Int8,
        "value": -10,
    },
    {
        "name": "Inputs/uint8",
        "timestamp": 1486144502123,
        "datatype": SPBMetricDataTypes.UInt8,
        "value": 10,
    },
    {
        "name": "Inputs/int16.neg",
        "timestamp": 1486144502123,
        "datatype": SPBMetricDataTypes.Int16,
        "value": -100,
    },
    {
        "name": "Inputs/uint16",
        "timestamp": 1486144502123,
        "datatype": SPBMetricDataTypes.UInt16,
        "value": 100,
    },
    {
        "name": "Properties/int32",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Int32,
        "value": 200,
    },
    {
        "name": "Properties/int32.neg",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Int32,
        "value": -200,
    },
    {
        "name": "Properties/Uint32",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.UInt32,
        "value": 200,
    },
    {
        "name": "Outputs/DateTime",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.DateTime,
        "value": 1486144502122,
    },
    {
        "name": "Outputs/Uint64",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.UInt64,
        "value": 123456,
    },
    {
        "name": "Outputs/int64.Neg",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Int64,
        "value": -123456,
    },
    {
        "name": "Outputs/Bool",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Boolean,
        "value": False,
    },
    {
        "name": "Outputs/Float",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Float,
        "value": 1.1234,
    },
    {
        "name": "Outputs/Double",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Double,
        "value": 122341.1234,
    },
    {
        "name": "Properties/String",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.String,
        "value": "Sony",
    },
    {
        "name": "Properties/Text",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Text,
        "value": "Sony made this device in 1986",
    },
    {
        "name": "Inputs/int8.Array",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Int8Array,
        "value": [10, 11, -23],
    },
    {
        "name": "Inputs/int16.Array",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Int16Array,
        "value": [-30000, 30000],
    },
    {
        "name": "Inputs/int32.Array",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Int32Array,
        "value": [-1, 315338746],
    },
    {
        "name": "Inputs/int64.Array",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Int64Array,
        "value": [-4270929666821191986, -3601064768563266876],
    },
    {
        "name": "Inputs/uint8.Array",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.UInt8Array,
        "value": [23, 250],
    },
    {
        "name": "Inputs/uint16.Array",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.UInt16Array,
        "value": [30, 52360],
    },
    {
        "name": "Inputs/uint32.Array",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.UInt32Array,
        "value": [52, 3293969225],
    },
    {
        "name": "Inputs/uint64.Array",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.UInt64Array,
        "value": [5245, 16444743074749521625],
    },
    {
        "name": "Inputs/datetime.Array",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.UInt64Array,
        "value": [1486144502122, 1486144505122],
    },
    {
        "name": "Inputs/boolean.Array",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.BooleanArray,
        "value": [True, False, True],
    },
    {
        "name": "Inputs/string.Array",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.StringArray,
        "value": ["I am a string", "I too am a string"],
    },
    {
        "name": "Inputs/UUID",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.UUID,
        "value": "unique_id_123456789",
    },
    {
        "name": "Inputs/bytes",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Bytes,
        "value": bytes([0x0C, 0x00, 0x00, 0x00, 0x34, 0xD0]),
    },
    {
        "name": "Inputs/file",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.File,
        "value": bytes([0xC7, 0xD0, 0x90, 0x75, 0x24, 0x01, 0x00, 0x00, 0xB8, 0xBA, 0xB8, 0x97, 0x81, 0x01, 0x00, 0x00]),
    },
    {
        "name": "Inputs/dataset",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.DataSet,
        "value": create_dummy_dataset(),
    },
    {
        "name": "Inputs/template",
        "timestamp": 1486144502122,
        "datatype": SPBMetricDataTypes.Template,
        "value": create_dummy_template(),
    },
]

DUMMY_PROPERTY_SET = Payload.PropertySet(
    keys=["key1_1", "key1_2"],
    values=[
        Payload.PropertyValue(
            type=SPBPropertyValueTypes.String, string_value="nested"),
        Payload.PropertyValue(
            type=SPBPropertyValueTypes.UInt32, int_value=12345),
    ],
)

DUMMY_PROPERTY_SET_LIST = Payload.PropertySetList(
    propertyset=[DUMMY_PROPERTY_SET, DUMMY_PROPERTY_SET])


def _create_sample_spb_payload() -> Payload:
    spb_mgs_gen = SpBMessageGenerator()
    payload = spb_mgs_gen.get_device_data_payload()

    for metric_dict in list_of_metrics_dict:
        name: str = metric_dict["name"]
        datatype: int = metric_dict["datatype"]
        value = metric_dict.get("value", None)
        metric_timestamp = metric_dict.get("timestamp", None)
        metric = spb_mgs_gen.add_metric(
            payload_or_template=payload, name=name, datatype=datatype, value=value, timestamp=metric_timestamp
        )
        spb_mgs_gen.add_properties_to_metric(
            metric,
            keys=["key1", "key2", "key3", "key4", "key5", "key6", "key7"],
            datatypes=[
                SPBPropertyValueTypes.UInt32,
                SPBPropertyValueTypes.UInt64,
                SPBPropertyValueTypes.Float,
                SPBPropertyValueTypes.Double,
                SPBPropertyValueTypes.String,
                SPBPropertyValueTypes.PropertySet,
                SPBPropertyValueTypes.PropertySetList,
            ],
            values=[10, 10000, 10.1234, 100000.12345678, "String 1",
                    DUMMY_PROPERTY_SET, DUMMY_PROPERTY_SET_LIST],
        )
    return payload


@pytest.fixture(autouse=True)
def setup_alias_map():
    # clear the alias map for each test
    spb_mgs_gen = SpBMessageGenerator()
    spb_mgs_gen.alias_name_map.clear()


@pytest.mark.parametrize(
    "query",
    [
        """
    {
        value {
            topic,
            timestamp,
            seq,
            uuid,
            body,
        }
    }""",
    ],
)
@pytest.mark.parametrize(
    "topic, payload",
    [
        ("spBv1.0/uns_group/DDATA/eon1", _create_sample_spb_payload()),
        ("spBv1.0/uns_group/DDATA/eon2", sample_binary_spb_payload),
        ("spBv1.0/uns_group/DDATA/eon2",
         uns_spb_helper.convert_spb_bytes_payload_to_dict(sample_binary_spb_payload)),
    ],
)
def test_strawberry_types(query, topic, payload):
    spb_node = SPBNode(topic=topic, payload=payload)

    @strawberry.type
    class Query:
        value: SPBNode

    schema = strawberry.Schema(
        query=Query,
        types=[
            SPBPrimitive,
            SPBNode,
            SPBMetric,
            SPBTemplate,
            SPBTemplateParameter,
            SPBDataSet,
            SPBDataSetRow,
            SPBDataSetValue,
            SPBMetadata,
            SPBPropertySet,
            SPBPropertyValue,
            BytesPayload,
        ],
    )
    result = schema.execute_sync(query, root_value=Query(value=spb_node))
    assert not result.errors


@pytest.mark.parametrize(
    "topic, payload",
    [
        ("spBv1.0/uns_group/DDATA/eon1", _create_sample_spb_payload()),
        ("spBv1.0/uns_group/DDATA/eon2", sample_binary_spb_payload),
    ],
)
def test_spb_node(topic: str, payload: Payload | bytes):
    """
    Test creating SPBNode with binary serialized Payload as well as instantiated Payload
    Based on the payload, recursively checks all sub types of the Payload like:
    - Metric
    - Template
    - PropertySet
    - DataSet
    """
    # test with bytes, Payload and dict
    spb_node = SPBNode(topic=topic, payload=payload)

    if isinstance(payload, bytes):
        parsed_payload = Payload()
        parsed_payload.ParseFromString(payload)
        payload = parsed_payload
    assert spb_node is not None
    assert spb_node.topic == topic
    assert spb_node.timestamp == datetime.fromtimestamp(
        payload.timestamp / 1000, UTC)
    assert spb_node.seq == payload.seq
    if payload.HasField("uuid"):
        assert spb_node.uuid == strawberry.ID(payload.uuid)
    if payload.HasField("body"):
        assert spb_node.body == strawberry.scalars.Base64(payload.body)
    # this doesn't work because of float values
    # assert spb_node.metrics == [SPBMetric(metric) for metric in payload.metrics]
    for spb_node_metric, payload_metric in zip(spb_node.metrics, payload.metrics, strict=True):
        compare_metrics(spb_node_metric, payload_metric)


def compare_metrics(graphql_metric: SPBMetric, payload_metric: Payload.Metric):
    """
    Utility method to compare metrics and handle float in value, template , dataset
    """
    spb_metric = SPBMetric(payload_metric)
    fields = [
        "alias",
        "is_null",
        "is_historical",
        "is_transient",
        "timestamp",
    ]
    for field in fields:
        assert getattr(graphql_metric, field) == getattr(spb_metric, field)

    assert graphql_metric.metadata == spb_metric.metadata
    if payload_metric.HasField("metadata"):
        compare_metric_metadata(payload_metric.metadata, spb_metric.metadata)

    assert graphql_metric.properties == spb_metric.properties
    if payload_metric.HasField("properties"):
        compare_propertyset(graphql_metric.properties,
                            payload_metric.properties)

    assert graphql_metric.datatype == spb_metric.datatype == SPBMetricDataTypes(
        payload_metric.datatype).name

    # compare values and handle floating point precision issue
    match payload_metric.datatype:
        case SPBMetricDataTypes.Float:
            assert graphql_metric.value == spb_metric.value
            assert math.isclose(
                literal_eval(
                    graphql_metric.value.data), payload_metric.float_value, rel_tol=1 / 10**FLOAT_PRECISION,
            )

        case SPBMetricDataTypes.FloatArray:
            assert graphql_metric.value == spb_metric.value

            for val1, val2 in zip(
                literal_eval(graphql_metric.value.data), SPBMetricDataTypes.FloatArray.get_value_from_sparkplug(
                    payload_metric), strict=True
            ):
                assert math.isclose(
                    val1, val2, rel_tol=1 / 10**FLOAT_PRECISION,)

        case SPBMetricDataTypes.Template:
            compare_templates(graphql_metric.value,
                              payload_metric.template_value)

        case SPBMetricDataTypes.DataSet:
            compare_datasets(graphql_metric.value,
                             payload_metric.dataset_value)

        case SPBMetricDataTypes.String | SPBMetricDataTypes.Text | SPBMetricDataTypes.UUID:
            assert graphql_metric.value == spb_metric.value
            assert graphql_metric.value.data == payload_metric.string_value

        case SPBMetricDataTypes.Bytes | SPBMetricDataTypes.File:
            assert graphql_metric.value == spb_metric.value
            assert graphql_metric.value.data == payload_metric.bytes_value

        case _:
            assert graphql_metric.value == spb_metric.value
            assert literal_eval(graphql_metric.value.data) == SPBMetricDataTypes(
                payload_metric.datatype
            ).get_value_from_sparkplug(payload_metric)


def compare_metric_metadata(graphql_metadata: SPBMetadata, metadata: Payload.MetaData):
    if metadata.HasField("is_multi_part"):
        assert graphql_metadata.is_multi_part == metadata.is_multi_part

    if metadata.HasField("content_type"):
        assert graphql_metadata.content_type == metadata.content_type

    if metadata.HasField("size"):
        assert graphql_metadata.size == metadata.size

    if metadata.HasField("seq"):
        assert graphql_metadata.seq == metadata.seq

    if metadata.HasField("file_name"):
        assert graphql_metadata.file_name == metadata.file_name

    if metadata.HasField("file_type"):
        assert graphql_metadata.file_type == metadata.file_type

    if metadata.HasField("md5"):
        assert graphql_metadata.md5 == metadata.md5

    if metadata.HasField("description"):
        assert graphql_metadata.description == metadata.description


def compare_templates(graphql_template: SPBTemplate, template: Payload.Template):
    spb_template = SPBTemplate(template)

    assert graphql_template.is_definition == spb_template.is_definition
    if template.HasField("is_definition"):
        assert graphql_template.is_definition == template.is_definition

    assert graphql_template.template_ref == spb_template.template_ref
    if template.HasField("template_ref"):
        assert graphql_template.template_ref == template.template_ref

    assert graphql_template.version == spb_template.version
    if template.HasField("version"):
        assert graphql_template.version == template.version

    for graphql_metric, template_metric in zip(graphql_template.metrics, template.metrics, strict=True):
        compare_metrics(graphql_metric, template_metric)

    if len(template.parameters) > 0:
        for graphql_template_param, template_param in zip(graphql_template.parameters, template.parameters, strict=True):
            assert graphql_template_param.name == template_param.name
            assert graphql_template_param.datatype == SPBParameterTypes(
                template_param.type).name
            match template_param.type:
                case SPBParameterTypes.Float:
                    assert math.isclose(
                        literal_eval(graphql_template_param.value.data),
                        template_param.float_value,
                        rel_tol=1 / 10**FLOAT_PRECISION,
                    )
                case SPBParameterTypes.String:
                    assert graphql_template_param.value.data == template_param.string_value

                case _:
                    assert literal_eval(graphql_template_param.value.data) == SPBParameterTypes(
                        template_param.type
                    ).get_value_from_sparkplug(template_param)
    else:
        assert len(graphql_template.parameters) == len(
            spb_template.parameters) == 0


def compare_datasets(graphql_dataset: SPBDataSet, dataset: Payload.DataSet):
    spb_dataset = SPBDataSet(dataset)
    assert graphql_dataset.columns == spb_dataset.columns == dataset.columns
    assert graphql_dataset.num_of_columns == spb_dataset.num_of_columns == dataset.num_of_columns
    assert graphql_dataset.types == spb_dataset.types == [
        SPBDataSetDataTypes(datatype).name for datatype in dataset.types]
    for graphql_row, dataset_row in zip(graphql_dataset.rows, dataset.rows, strict=True):
        for graphql_dt_val, dt_val, datatype in zip(graphql_row.elements, dataset_row.elements, dataset.types, strict=True):
            match datatype:
                case SPBDataSetDataTypes.Float:
                    assert math.isclose(
                        literal_eval(
                            graphql_dt_val.value.data), dt_val.float_value, rel_tol=1 / 10**FLOAT_PRECISION
                    )

                case SPBDataSetDataTypes.String:  # literal_eval doesn't support string
                    assert graphql_dt_val.value.data == dt_val.string_value

                case _:
                    assert literal_eval(graphql_dt_val.value.data) == SPBDataSetDataTypes(datatype).get_value_from_sparkplug(
                        dt_val
                    )


def compare_propertyset(graphql_propertyset: SPBPropertySet, propertyset: Payload.PropertySet):
    spb_propertyset = SPBPropertySet(propertyset)

    assert graphql_propertyset.keys == spb_propertyset.keys == propertyset.keys
    for gql_prop_val, spb_prop_val, prop_val in zip(graphql_propertyset.values, spb_propertyset.values,
                                                    propertyset.values, strict=True):
        match prop_val.type:
            case SPBPropertyValueTypes.Float:
                assert gql_prop_val.value == spb_prop_val.value
                assert math.isclose(
                    literal_eval(gql_prop_val.value.data), prop_val.float_value, rel_tol=1 / 10**FLOAT_PRECISION,
                )

            case SPBPropertyValueTypes.String:
                assert gql_prop_val.value == spb_prop_val.value
                assert gql_prop_val.value.data == SPBPropertyValueTypes(
                    prop_val.type).get_value_from_sparkplug(prop_val)

            case SPBPropertyValueTypes.PropertySet:
                compare_propertyset(gql_prop_val.value,
                                    prop_val.propertyset_value)

            case SPBPropertyValueTypes.PropertySetList:
                for gql_sub_prop_set, sub_prop_set in zip(
                    gql_prop_val.value.propertysets, prop_val.propertysets_value.propertyset,
                    strict=True
                ):
                    compare_propertyset(gql_sub_prop_set, sub_prop_set)
            case _:
                assert gql_prop_val.value == spb_prop_val.value
                assert literal_eval(gql_prop_val.value.data) == SPBPropertyValueTypes(prop_val.type).get_value_from_sparkplug(
                    prop_val
                )
