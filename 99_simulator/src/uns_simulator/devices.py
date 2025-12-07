"""
Industrial device implementations: PLC, SCADA, and HMI.
All devices communicate via MQTT using ISA-95 topic structure.
"""
import asyncio
import json
import logging
import random
import time
from datetime import datetime
from typing import Any

import aiomqtt

from uns_simulator.config import MQTTConfig
from uns_simulator.models import Equipment, ISA95Hierarchy, ParameterType

LOGGER = logging.getLogger(__name__)


class AsyncMQTTDevice:
    """
    Base class for async MQTT devices.

    Provides common functionality for connection management, message publishing,
    and error handling for industrial devices.
    """

    def __init__(self, device_id: str, hierarchy: ISA95Hierarchy, mqtt_config: dict[str, Any]):
        self.device_id = device_id
        self.hierarchy = hierarchy
        self.mqtt_config = mqtt_config

        client_id = f"graphql-{time.time()}-{random.randint(0, 1000)}"  # noqa: S311

        self.client = aiomqtt.Client(
            identifier=client_id,
            clean_session=MQTTConfig.clean_session,
            protocol=MQTTConfig.version,
            transport=MQTTConfig.transport,
            hostname=MQTTConfig.host,
            port=MQTTConfig.port,
            username=MQTTConfig.username,
            password=MQTTConfig.password,
            keepalive=MQTTConfig.keep_alive,
            tls_params=MQTTConfig.tls_params,
            tls_insecure=MQTTConfig.tls_insecure,
        )

        LOGGER.info("Initialized device: %s", device_id)

    async def publish_parameter(self, equipment: str, param_type: ParameterType,
                                param_name: str, data: dict[str, Any]) -> bool:
        """
        Publish parameter data to MQTT using ISA-95 topic structure.

        Args:
            equipment: Equipment identifier
            param_type: Parameter type
            param_name: Parameter name
            data: Parameter data dictionary

        Returns:
            True if publish successful, False otherwise
        """

        try:
            # Enrich data with metadata
            enriched_data = {
                **data,
                'timestamp': datetime.timestamp(datetime.now()),
                'source': self.device_id,
                'equipment': equipment
            }

            # Validate data structure
            if not self._validate_publish_data(enriched_data):
                return False

            topic = self.hierarchy.get_parameter_topic(
                equipment, param_type, param_name)

            # Publish to MQTT
            async with self.client:
                await self.client.publish(topic, json.dumps(enriched_data))
                LOGGER.debug("Device %s published to %s: %s",
                             self.device_id, topic, enriched_data.get('value', 'N/A'))
            return True

        except json.JSONDecodeError as e:
            LOGGER.error("JSON encoding error in device %s: %s",
                         self.device_id, e)
            return False
        except Exception as e:
            LOGGER.error("Publish error in device %s: %s", self.device_id, e)
            return False

    def _validate_publish_data(self, data: dict[str, Any]) -> bool:
        """
        Validate data before publishing.

        Args:
            data: Data dictionary to validate

        Returns:
            True if data is valid
        """
        required_fields = ['timestamp', 'source', 'equipment']
        for field in required_fields:
            if field not in data:
                LOGGER.error("Missing required field %s in publish data from %s",
                             field, self.device_id)
                return False
        return True

    async def handle_message(self, topic: str, payload: dict[str, Any]) -> None:
        """
        Handle incoming MQTT messages.

        Args:
            topic: MQTT topic
            payload: Message payload
        """
        LOGGER.debug("Device %s received message on %s: %s",
                     self.device_id, topic, payload)

    async def start(self, interval: float = 5.0) -> None:
        """Start device operation - to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement start method")

    async def stop(self) -> None:
        """Stop device operation."""
        self._running = False
        LOGGER.info("Device %s stopped", self.device_id)


class PLC(AsyncMQTTDevice):
    """
    Programmable Logic Controller device.

    Simulates industrial PLCs that generate sensor data, equipment status,
    and alarm conditions.
    """

    def __init__(self, plc_id: str, hierarchy: ISA95Hierarchy,
                 mqtt_config: dict[str, Any], equipment_config: dict[str, Any]):
        super().__init__(f"PLC_{plc_id}", hierarchy, mqtt_config)
        self.plc_id = plc_id

        # Create equipment definition
        self.equipment = Equipment(
            name=equipment_config['name'],
            sensors=equipment_config['sensors']
        )

        # Equipment state
        self.operational = True
        self.performance = 1.0
        self.operating_hours = random.randint(0, 5000)  # noqa: S311
        self.last_maintenance = datetime.timestamp(datetime.now())

        LOGGER.info("Initialized PLC %s for equipment %s",
                    plc_id, self.equipment.name)

    async def generate_sensor_data(self) -> list[dict[str, Any]]:
        """
        Generate realistic sensor data with random variation.

        Returns:
            List of sensor data messages
        """
        messages = []

        for sensor_name, sensor_config in self.equipment.sensors.items():
            try:
                base_value = sensor_config['base_value']
                variation = sensor_config['variation']

                # Generate value with realistic variation

                current_value = base_value + \
                    random.uniform(-variation,  # noqa: S311
                                   variation)
                # Determine status based on deviation
                deviation = abs(current_value - base_value)
                if deviation > variation * 3:
                    status = "Alarm"
                elif deviation > variation * 2:
                    status = "Warning"
                else:
                    status = "Normal"

                sensor_data = {
                    'value': round(current_value, 2),
                    'unit': sensor_config['unit'],
                    'status': status,
                    'quality': 'Good'
                }

                messages.append({
                    'equipment': self.equipment.name,
                    'param_type': ParameterType.PROCESS_VALUE,
                    'param_name': sensor_name,
                    'data': sensor_data
                })

            except KeyError as e:
                LOGGER.error("Missing sensor configuration key %s in PLC %s",
                             e, self.plc_id)

        LOGGER.debug("PLC %s generated %d sensor data points",
                     self.plc_id, len(messages))
        return messages

    async def generate_status_data(self) -> dict[str, Any]:
        """
        Generate equipment status information.

        Returns:
            Status data dictionary
        """
        # Simulate occasional equipment state changes
        if random.random() < 0.02:   # noqa: S311 # 2% chance of fault
            self.operational = False
            self.performance = round(random.uniform(0.5, 0.8), 2)  # noqa: S311
            LOGGER.warning("PLC %s equipment fault simulated", self.plc_id)
        elif random.random() < 0.05 and not self.operational:   # noqa: S311 # 5% chance of recovery
            self.operational = True
            self.performance = round(random.uniform(0.9, 1.0), 2)  # noqa: S311
            LOGGER.info("PLC %s equipment recovery simulated", self.plc_id)

        status_data = {
            'operational': self.operational,
            'performance': self.performance,
            'mode': 'Auto' if self.operational else 'Maintenance',
            'operating_hours': self.operating_hours,
            'last_maintenance': self.last_maintenance
        }

        return {
            'equipment': self.equipment.name,
            'param_type': ParameterType.STATUS,
            'param_name': 'EquipmentStatus',
            'data': status_data
        }

    async def generate_alarm_data(self) -> dict[str, Any] | None:
        """
        Generate alarm data with random occurrence.

        Returns:
            Alarm data dictionary or None if no alarms
        """

        if random.random() < 0.05:   # noqa: S311 # 5% chance of alarm
            alarm_types = [
                ("HIGH_TEMPERATURE", "High temperature detected", "HIGH"),
                ("LOW_PRESSURE", "Low pressure warning", "MEDIUM"),
                ("EQUIPMENT_FAULT", "Equipment fault detected", "HIGH"),
                ("COMMUNICATION_LOSS", "Communication loss with sensor", "MEDIUM")
            ]

            alarm_type, message, severity = random.choice(alarm_types)  # noqa: S311

            alarm_data = {
                'alarms': [{
                    'id': f"ALM_{random.randint(1000, 9999)}",  # noqa: S311
                    'type': alarm_type,
                    'message': message,
                    'severity': severity,
                    'timestamp': datetime.timestamp(datetime.now()),
                    'acknowledged': False
                }]
            }

            LOGGER.warning("PLC %s generated alarm: %s",
                           self.plc_id, alarm_type)

            return {
                'equipment': self.equipment.name,
                'param_type': ParameterType.ALARM,
                'param_name': 'ActiveAlarms',
                'data': alarm_data
            }

        return None

    async def start(self, interval: float = 5.0) -> None:
        """
        Start PLC data generation.

        Args:
            interval: Data generation interval in seconds
        """
        self._running = True
        LOGGER.info("PLC %s started for equipment %s (interval: %ss)",
                    self.plc_id, self.equipment.name, interval)

        try:
            while self._running:

                # Generate and publish sensor data
                sensor_messages = await self.generate_sensor_data()
                for msg in sensor_messages:
                    success = await self.publish_parameter(
                        msg['equipment'], msg['param_type'], msg['param_name'], msg['data'])
                    if not success:
                        LOGGER.warning(
                            "PLC %s failed to publish sensor data", self.plc_id)

                # Generate and publish status data
                status_msg = await self.generate_status_data()
                await self.publish_parameter(
                    status_msg['equipment'], status_msg['param_type'],
                    status_msg['param_name'], status_msg['data']
                )

                # Generate and publish alarms if any
                alarm_msg = await self.generate_alarm_data()
                if alarm_msg:
                    await self.publish_parameter(
                        alarm_msg['equipment'], alarm_msg['param_type'],
                        alarm_msg['param_name'], alarm_msg['data']
                    )

                    # Increment operating hours
                self.operating_hours += 1

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            LOGGER.info("PLC %s operation cancelled", self.plc_id)
        except Exception as e:
            LOGGER.error("PLC %s encountered error: %s",
                         self.plc_id, e, exc_info=True)
        finally:
            await self.stop()


class SCADA(AsyncMQTTDevice):
    """
    Supervisory Control and Data Acquisition system.

    Monitors multiple field devices and provides system-wide overview
    and performance metrics.
    """

    def __init__(self, hierarchy: ISA95Hierarchy, mqtt_config: dict[str, Any],
                 system_name: str = "SCADA_Main"):
        super().__init__("SCADA_System", hierarchy, mqtt_config)
        self.system_name = system_name
        self.connected_devices = 0
        self.data_points_received = 0
        self.start_time = datetime.now()

        LOGGER.info("Initialized SCADA system: %s", system_name)

    async def generate_system_status(self) -> dict[str, Any]:
        """
        Generate SCADA system health and performance data.

        Returns:
            System status dictionary
        """
        uptime = (datetime.now() - self.start_time).total_seconds()

        status_data = {
            'system_name': self.system_name,
            'system_status': 'Operational',
            # Simulated device count
            'connected_devices': random.randint(5, 10),  # noqa: S311
            'data_points_per_second': random.randint(500, 1500),  # noqa: S311
            'system_uptime_hours': round(uptime / 3600, 2),
            'cpu_usage_percent': round(random.uniform(10, 60), 1),  # noqa: S311
            'memory_usage_percent': round(random.uniform(20, 80), 1),  # noqa: S311
            'alarms_active': random.randint(0, 3),  # noqa: S311
            'version': '2.1.4'
        }

        return status_data

    async def start(self, interval: float = 10.0) -> None:
        """
        Start SCADA system monitoring.

        Args:
            interval: Status update interval in seconds
        """
        self._running = True
        LOGGER.info("SCADA system %s started (update interval: %ss)",
                    self.system_name, interval)

        try:
            while self._running:

                status_data = await self.generate_system_status()
                success = await self.publish_parameter(
                    "SCADA", ParameterType.STATUS, "SystemStatus", status_data
                )

                if success:
                    LOGGER.debug("SCADA system published status update")
                else:
                    LOGGER.warning(
                        "SCADA system failed to publish status update")

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            LOGGER.info("SCADA system operation cancelled")
        except Exception as e:
            LOGGER.error("SCADA system encountered error: %s",
                         e, exc_info=True)
        finally:
            await self.stop()


class HMI(AsyncMQTTDevice):
    """
    Human Machine Interface device.

    Simulates operator workstations and user interactions with the
    industrial control system.
    """

    def __init__(self, hmi_id: str, hierarchy: ISA95Hierarchy, mqtt_config: dict[str, Any]):
        super().__init__(f"HMI_{hmi_id}", hierarchy, mqtt_config)
        self.hmi_id = hmi_id
        self.current_screen = "MainDashboard"
        self.operator = f"operator{random.randint(1, 5)}"  # noqa: S311
        self.interaction_count = 0
        self.session_start = datetime.now()

        LOGGER.info("Initialized HMI %s for operator %s",
                    hmi_id, self.operator)

    async def generate_operator_actions(self) -> dict[str, Any]:
        """
        Generate simulated operator interactions.

        Returns:
            Operator actions data dictionary
        """
        actions = []

        # 30% chance of operator action each cycle
        if random.random() < 0.3:  # noqa: S311
            action_types = [
                ("SETPOINT_CHANGE", "Changed temperature setpoint"),
                ("ALARM_ACKNOWLEDGE", "Acknowledged alarm"),
                ("MODE_CHANGE", "Changed operating mode"),
                ("RECIPE_LOAD", "Loaded production recipe"),
                ("MANUAL_OVERRIDE", "Manual override activated"),
                ("TREND_VIEW", "Viewed trend data")
            ]

            action_type, description = random.choice(action_types)  # noqa: S311

            # Simulate screen navigation with action
            screens = ["MainDashboard", "AlarmSummary", "TrendDisplay",
                       "ControlPanel", "RecipeManagement"]
            self.current_screen = random.choice(screens)  # noqa: S311

            action_data = {
                'type': action_type,
                'description': description,
                'operator': self.operator,
                'screen': self.current_screen,
                'timestamp': datetime.timestamp(datetime.now()),
                'session_duration_minutes': round(
                    (datetime.now() - self.session_start).total_seconds() / 60, 1
                )
            }

            # Add context-specific data
            if action_type == "SETPOINT_CHANGE":
                action_data['parameter'] = f"Temp_Setpoint_{random.randint(1, 5)}"  # noqa: S311
                action_data['new_value'] = round(random.uniform(60, 90), 2)  # noqa: S311
                action_data['old_value'] = round(
                    action_data['new_value'] - random.uniform(1, 5), 2)  # noqa: S311

            actions.append(action_data)
            self.interaction_count += 1

            LOGGER.debug("HMI %s generated operator action: %s",
                         self.hmi_id, action_type)

        return {
            'actions': actions,
            'current_screen': self.current_screen,
            'operator': self.operator,
            'total_interactions': self.interaction_count,
            'workstation_id': self.device_id
        }

    async def start(self, interval: float = 3.0) -> None:
        """
        Start HMI operation simulation.

        Args:
            interval: Action generation interval in seconds
        """
        self._running = True
        LOGGER.info("HMI %s started for operator %s (interval: %ss)",
                    self.hmi_id, self.operator, interval)

        try:
            while self._running:
                action_data = await self.generate_operator_actions()

                # Only publish if there are actions
                if action_data['actions']:
                    success = await self.publish_parameter(
                        "HMI", ParameterType.EVENT, "OperatorActions", action_data
                    )

                    if success:
                        LOGGER.debug(
                            "HMI %s published operator actions", self.hmi_id)
                    else:
                        LOGGER.warning(
                            "HMI %s failed to publish operator actions", self.hmi_id)

                await asyncio.sleep(interval)

        except asyncio.CancelledError:
            LOGGER.info("HMI %s operation cancelled", self.hmi_id)
        except Exception as e:
            LOGGER.error("HMI %s encountered error: %s",
                         self.hmi_id, e, exc_info=True)
        finally:
            await self.stop()
