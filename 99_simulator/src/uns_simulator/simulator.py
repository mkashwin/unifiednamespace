import asyncio
import logging

from uns_simulator.config import settings
from uns_simulator.devices import HMI, PLC, SCADA
from uns_simulator.models import ISA95Hierarchy

LOGGER = logging.getLogger(__name__)


class UnifiedNamespaceSimulator:
    """Main simulator class following unifiednamespace patterns"""

    def __init__(self):
        self.mqtt_config = settings.mqtt
        self.simulation_config = settings.simulation
        self.hierarchy = ISA95Hierarchy(**settings.hierarchy)
        self.devices: list = []
        self.tasks: list[asyncio.Task] = []

    def create_plc(self) -> list[PLC]:
        """Create PLC instances from configuration"""
        plc_list = []
        plc_count = self.simulation_config.get('plc_count', 2)

        for i in range(plc_count):
            plc_id = f"{i + 1:03d}"
            equipment_config = settings.get("equipment.mixer_tank")

            if equipment_config:
                plc = PLC(
                    plc_id=plc_id,
                    hierarchy=self.hierarchy,
                    mqtt_config=self.mqtt_config,
                    equipment_config=equipment_config
                )
                plc_list.append(plc)

        return plc_list

    def create_scada(self) -> SCADA:
        """Create SCADA instance"""
        return SCADA(hierarchy=self.hierarchy, mqtt_config=self.mqtt_config)

    def create_hmi(self, count: int = 1) -> list[HMI]:
        """Create HMI instances"""
        return [
            HMI(hmi_id=f"{i:02d}", hierarchy=self.hierarchy,
                mqtt_config=self.mqtt_config)
            for i in range(count)
        ]

    async def run_simulation(self, duration_minutes: int | None = None):
        """Run the complete simulation"""
        duration = duration_minutes or self.simulation_config.duration_minutes

        LOGGER.info("Starting Unified Namespace Simulator")
        LOGGER.info(f"Duration: {duration} minutes")

        # Create devices
        self.devices = (
            [*self.create_plc(), self.create_scada(), *self.create_hmi(2)]
        )

        # Start all devices
        interval = self.simulation_config.interval
        for device in self.devices:
            task = asyncio.create_task(device.start(interval))
            self.tasks.append(task)

        try:
            await asyncio.sleep(duration * 60)
        except KeyboardInterrupt:
            LOGGER.warning("Simulation interrupted by user")
        finally:
            await self._stop_simulation()

    async def _stop_simulation(self):
        """Cleanly stop all devices"""
        for device in self.devices:
            await device.stop()

        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
