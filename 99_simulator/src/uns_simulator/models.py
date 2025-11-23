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

Data models for ISA-95 hierarchy and equipment definitions.
Defines the structure for MQTT topics and industrial equipment.
"""
from enum import Enum
from typing import Any


class ParameterType(Enum):
    """Types of industrial parameters following ISA-95 standards"""
    PROCESS_VALUE = "ProcessValue"    # Measured values from sensors
    SETPOINT = "Setpoint"             # Target values for control
    STATUS = "Status"                 # Equipment status information
    ALARM = "Alarm"                   # Alarm and warning conditions
    EVENT = "EVENT"                   # EVENT STATUS


class ISA95Hierarchy:
    """
    Implements ISA-95 hierarchical model for industrial systems.
    Creates structured MQTT topics like: Enterprise/Site/Area/Line/WorkCell/Equipment/ParameterType/ParameterName
    """

    def __init__(self, enterprise: str, site: str, area: str, line: str, cell: str):
        self.enterprise = enterprise
        self.site = site
        self.area = area
        self.line = line
        self.cell = cell

    def get_parameter_topic(self, equipment: str, param_type: ParameterType, param_name: str) -> str:
        """
        Generate ISA-95 compliant MQTT topic
        Example: ManufacturingCo/PlantA/Production/Line1/Cell1/MixerTank/ProcessValue/Temperature
        """
        return f"{self.enterprise}/{self.site}/{self.area}/{self.line}/{self.cell}/{equipment}/{param_type.value}/{param_name}"


class Equipment:
    """Represents industrial equipment with sensors and parameters"""

    def __init__(self, name: str, sensors: dict[str, Any]):
        self.name = name
        self.sensors = sensors  # sensor_name -> {base_value, variation, unit}
        self.operational = True
        self.performance = 1.0
