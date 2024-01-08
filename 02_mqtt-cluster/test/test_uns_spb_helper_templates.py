"""
All tests for uns_spb_helper  related to Templates within Metrics
"""

import pytest
from uns_sparkplugb.generated.sparkplug_b_pb2 import Payload
from uns_sparkplugb.uns_spb_enums import SPBMetricDataTypes, SPBParameterTypes
from uns_sparkplugb.uns_spb_helper import SpBMessageGenerator


@pytest.mark.parametrize(
    "template_metrics_dict",
    [
        [],  # No Metrics
        [  # Test for SPBBasicDataTypes
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
        ],
        [  # Test for SPBArrayDataTypes
            {
                "name": "Inputs/int8",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Int8Array,
                "value": [10, 11, -23],
            },
            {
                "name": "Inputs/int16",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Int16Array,
                "value": [-30000, 30000],
            },
            {
                "name": "Inputs/int32",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Int32Array,
                "value": [-1, 315338746],
            },
            {
                "name": "Inputs/int64",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.Int64Array,
                "value": [-4270929666821191986, -3601064768563266876],
            },
            {
                "name": "Inputs/uint8",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UInt8Array,
                "value": [23, 250],
            },
            {
                "name": "Inputs/uint16",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UInt16Array,
                "value": [30, 52360],
            },
            {
                "name": "Inputs/uint32",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UInt32Array,
                "value": [52, 3293969225],
            },
            {
                "name": "Inputs/uint64",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UInt64Array,
                "value": [5245, 16444743074749521625],
            },
            {
                "name": "Inputs/datetime",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.UInt64Array,
                "value": [1486144502122, 1486144505122],
            },
            {
                "name": "Inputs/boolean",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.BooleanArray,
                "value": [True, False, True],
            },
            {
                "name": "Inputs/string",
                "timestamp": 1486144502122,
                "datatype": SPBMetricDataTypes.StringArray,
                "value": ["I am a string", "I too am a string"],
            },
        ],
        [  # Test for SPBAdditionalDataTypes
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
                "value": bytes(
                    [0xC7, 0xD0, 0x90, 0x75, 0x24, 0x01, 0x00, 0x00, 0xB8, 0xBA, 0xB8, 0x97, 0x81, 0x01, 0x00, 0x00]
                ),
            },
        ],
    ],
)
@pytest.mark.parametrize(
    "name, metrics, version, template_ref, parameters",
    [
        ("Template", None, "v_0.1.0", None, None),  # No metrics, no parameters
        (
            "Template",
            [Payload.Metric(name="met1", datatype=SPBMetricDataTypes.Boolean, boolean_value=True)],
            "v_0.1.0",
            None,
            None,
        ),  # No parameters
        (
            "Template",
            [Payload.Metric(name="met1", datatype=SPBMetricDataTypes.Boolean, boolean_value=True)],
            "v_0.1.0",
            None,
            [("prop1", SPBParameterTypes.UInt32, 100), ("prop2", SPBParameterTypes.String, "property string")],
        ),  # with Params
        ("Template_Reference", None, "v_0.1.1", "Template Reference", None),  # No parameters
        (
            "Template_Reference",
            [Payload.Metric(name="met1", datatype=SPBMetricDataTypes.Boolean, boolean_value=True)],
            "v_0.1.1",
            "Template Reference",
            None,
        ),  # No parameters
        (
            "Template_Reference",
            [Payload.Metric(name="met1", datatype=SPBMetricDataTypes.Boolean, boolean_value=True)],
            "v_0.1.1",
            "Template Reference",
            [("prop4", SPBParameterTypes.Boolean, True), ("prop2", SPBParameterTypes.Double, 142.12343)],
        ),  # No parameters
    ],
)
def test_init_template_metric(name: str, metrics, template_metrics_dict, version, template_ref, parameters):
    """
    Test case for  SpBMessageGenerator#init_template_metric
    """
    spb_mgs_generator = SpBMessageGenerator()

    payload = Payload()
    template: Payload.Template = spb_mgs_generator.init_template_metric(
        payload=payload,
        name=name,
        metrics=metrics,
        version=version,
        template_ref=template_ref,
        parameters=parameters,
    )
    assert template is not None

    assert payload.metrics[0].datatype == SPBMetricDataTypes.Template
    assert payload.metrics[0].template_value == template
    assert payload.metrics[0].name == name
    if template_ref is None:
        assert template.is_definition
    else:
        assert template.template_ref == template_ref
    assert template.version == version

    if metrics is not None:
        for set_met, param_met in zip(template.metrics, metrics):
            assert set_met == param_met
    else:
        metrics = []

    if parameters is not None:
        for param, template_params in zip(parameters, template.parameters):
            assert template_params.name == param[0]
            assert template_params.type == param[1]
            assert SPBParameterTypes(param[1]).get_value_from_sparkplug(template_params) == param[2]

    # add the metrics to the template
    for metric in template_metrics_dict:
        name: str = metric["name"]
        datatype: int = metric["datatype"]
        value = metric.get("value", None)
        metric_timestamp = metric.get("timestamp", None)
        child_metric = spb_mgs_generator.add_metric(
            payload_or_template=template, name=name, datatype=datatype, value=value, timestamp=metric_timestamp
        )
        assert child_metric.name == name
        assert child_metric.datatype == datatype
        assert value == SPBMetricDataTypes(datatype).get_value_from_sparkplug(child_metric)
        assert child_metric.timestamp is not None

    assert len(template.metrics) == len(template_metrics_dict) + len(metrics)


@pytest.mark.parametrize(
    "child_templates",
    [
        [
            Payload.Template(
                is_definition=False,
                version="v1.0",
                template_ref="my_temp",
                metrics=[Payload.Metric(name="met1", datatype=SPBMetricDataTypes.Boolean, boolean_value=True)],
            ),
            Payload.Template(
                is_definition=True,
                version="v1.0",
                metrics=[Payload.Metric(name="ref", datatype=SPBMetricDataTypes.String, string_value="Template Definition")],
            ),
        ]
    ],
)
@pytest.mark.parametrize(
    "name, version, template_ref, parameters",
    [
        ("Template", "v_0.1.0", None, None),  # no parameters
        ("Template_Reference", "v_0.1.1", "Template Reference", None),  # No parameters
    ],
)
def test_init_template_with_template(name: str, version, template_ref, parameters, child_templates):
    """
    Tests to add Template to Template
    """
    spb_mgs_generator = SpBMessageGenerator()

    payload = Payload()
    template: Payload.Template = spb_mgs_generator.init_template_metric(
        payload=payload,
        name=name,
        metrics=None,
        version=version,
        template_ref=template_ref,
        parameters=parameters,
    )
    count: int = 0
    for child in child_templates:
        set_child_tem = spb_mgs_generator.add_metric(
            payload_or_template=template, name=f"child_{count}", datatype=SPBMetricDataTypes.Template, value=child
        )
        assert child == set_child_tem.template_value
