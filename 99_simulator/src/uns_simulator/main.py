#!/usr/bin/env python3
"""Main entry point for the simulator"""

import asyncio

from uns_simulator.config import settings
from uns_simulator.simulator import UnifiedNamespaceSimulator


async def main():
    """Run the simulator"""
    simulator = UnifiedNamespaceSimulator()
    await simulator.run_simulation(settings.get("simulation.duration", 60))


def run_simulator():
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
