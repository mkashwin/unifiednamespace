"""*******************************************************************************
* Copyright (c) 2024 Ashwin Krishnan
*
* All rights reserved. This program and the accompanying materials
* are made available under the terms of MIT and is provided "as is",
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

MCP Server for Unified Namespace (UNS)


This module provides a production-ready Model Context Protocol (MCP) server
implementation following best practices for resource management, error handling,
and graceful cleanup.

Key Features:
- Automatic resource cleanup with context managers
- Graceful degradation when backends unavailable
- Comprehensive error handling and logging
- Efficient connection pooling
- Progress reporting for long-running operations
- Structured, user-friendly responses
"""

import asyncio
import json
import logging
import signal
import sys
from collections.abc import Sequence
from datetime import UTC, datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    EmbeddedResource,
    GetPromptResult,
    ImageContent,
    Prompt,
    PromptMessage,
    Resource,
    TextContent,
    Tool,
)

from uns_mcp.backend.graphdb_client import GraphDBClient
from uns_mcp.backend.historian_client import HistorianClient
from uns_mcp.backend.mqtt_client import MQTTPublisher
from uns_mcp.config import GraphDBConfig, HistorianConfig, MQTTConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler('uns_mcp_server.log')
    ]
)
LOGGER = logging.getLogger(__name__)


class BackendConnectionManager:
    """
    Manages backend connections with automatic cleanup and health checking.

    This class ensures that all backend connections are properly initialized,
    monitored, and cleaned up even in case of errors or signals.

    Attributes:
        graphdb: Neo4j GraphDB client
        historian: TimescaleDB historian client
        mqtt: MQTT publisher client
        _cleanup_tasks: List of cleanup coroutines
        _health_check_task: Background task for health monitoring
    """

    def __init__(self):
        """Initialize the backend connection manager."""
        self.graphdb: GraphDBClient | None = None
        self.historian: HistorianClient | None = None
        self.mqtt: MQTTPublisher | None = None
        self._cleanup_tasks: list = []
        self._health_check_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()

    async def initialize(self) -> dict[str, bool]:
        """
        Initialize all configured backends.

        Returns:
            Dictionary mapping backend names to their availability status

        Notes:
            - Backends are initialized independently
            - Failures in one backend don't prevent others from initializing
            - All initialization attempts are logged
        """
        LOGGER.info("Initializing UNS MCP Server backends...")
        status = {}

        # Initialize GraphDB
        if GraphDBConfig.is_config_valid():
            try:
                self.graphdb = GraphDBClient()
                await self.graphdb.connect()
                self._cleanup_tasks.append(self.graphdb.disconnect)
                status['graphdb'] = True
                LOGGER.info("✓ GraphDB connection established")
            except Exception as e:
                LOGGER.error(
                    f"✗ Failed to connect to GraphDB: {e}", exc_info=True)
                self.graphdb = None
                status['graphdb'] = False
        else:
            LOGGER.warning("GraphDB not configured, skipping")
            status['graphdb'] = False

        # Initialize Historian
        if HistorianConfig.is_config_valid():
            try:
                self.historian = HistorianClient()
                await self.historian.connect()
                self._cleanup_tasks.append(self.historian.disconnect)
                status['historian'] = True
                LOGGER.info("✓ Historian connection established")
            except Exception as e:
                LOGGER.error(
                    f"✗ Failed to connect to Historian: {e}", exc_info=True)
                self.historian = None
                status['historian'] = False
        else:
            LOGGER.warning("Historian not configured, skipping")
            status['historian'] = False

        # Initialize MQTT
        if MQTTConfig.is_config_valid():
            try:
                self.mqtt = MQTTPublisher()
                await self.mqtt.connect()
                self._cleanup_tasks.append(self.mqtt.disconnect)
                status['mqtt'] = True
                LOGGER.info("✓ MQTT connection established")
            except Exception as e:
                LOGGER.error(
                    f"✗ Failed to connect to MQTT: {e}", exc_info=True)
                self.mqtt = None
                status['mqtt'] = False
        else:
            LOGGER.warning("MQTT not configured, skipping")
            status['mqtt'] = False

        # Start health monitoring
        self._health_check_task = asyncio.create_task(self._monitor_health())

        return status

    async def cleanup(self):
        """
        Gracefully cleanup all backend connections.

        This method ensures that:
        - All connections are closed in reverse order of initialization
        - Cleanup continues even if individual cleanups fail
        - All errors are logged but don't prevent further cleanup
        - Health monitoring is stopped
        """
        LOGGER.info("Cleaning up UNS MCP Server backends...")

        # Stop health monitoring
        if self._health_check_task and not self._health_check_task.done():
            self._shutdown_event.set()
            try:
                await asyncio.wait_for(self._health_check_task, timeout=5.0)
            except TimeoutError:
                LOGGER.warning(
                    "Health check task didn't stop gracefully, cancelling")
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

        # Run cleanup tasks in reverse order
        for cleanup_task in reversed(self._cleanup_tasks):
            try:
                await asyncio.wait_for(cleanup_task(), timeout=10.0)
                LOGGER.info(
                    f"✓ Cleaned up {cleanup_task.__self__.__class__.__name__}")
            except TimeoutError:
                LOGGER.error(
                    f"✗ Timeout cleaning up {cleanup_task.__self__.__class__.__name__}")
            except Exception as e:
                LOGGER.error(
                    f"✗ Error cleaning up {cleanup_task.__self__.__class__.__name__}: {e}")

        self._cleanup_tasks.clear()
        LOGGER.info("Cleanup completed")

    async def _monitor_health(self):
        """
        Background task to monitor backend health.

        Periodically checks connection status and logs warnings if
        connections are lost.
        """
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(60)  # Check every minute

                if self.graphdb:
                    try:
                        await self.graphdb.health_check()
                    except Exception as e:
                        LOGGER.warning(f"GraphDB health check failed: {e}")

                if self.historian:
                    try:
                        await self.historian.health_check()
                    except Exception as e:
                        LOGGER.warning(f"Historian health check failed: {e}")

                if self.mqtt:
                    try:
                        await self.mqtt.health_check()
                    except Exception as e:
                        LOGGER.warning(f"MQTT health check failed: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                LOGGER.error(f"Error in health monitoring: {e}")


class UNSMCPServer:  # cSpell:ignore UNSMCP
    """
    Production-ready MCP Server for Unified Namespace interactions.

    This server provides tools and resources for AI assistants to interact
    with industrial data through the Unified Namespace, following MCP best
    practices for error handling, resource management, and user experience.

    Best Practices Implemented:
    - Clear, structured tool responses
    - Detailed error messages with context
    - Progress reporting for long operations
    - Automatic resource cleanup
    - Graceful degradation
    - Health monitoring
    """

    def __init__(self):
        """Initialize the UNS MCP Server."""
        self.server = Server("uns-mcp-server")
        self.backend_manager = BackendConnectionManager()
        self._shutdown_task = None  # Store cleanup task reference
        self._register_handlers()

        # Setup signal handlers for graceful shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._signal_handler)

    # trunk-ignore(ruff/ARG002)
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        LOGGER.info(
            f"Received signal {signum}, initiating graceful shutdown...")
        # Store task reference to avoid RUF006 warning
        self._shutdown_task = asyncio.create_task(
            self.backend_manager.cleanup())
        sys.exit(0)

    def _register_handlers(self):  # noqa: C901
        """Register all MCP protocol handlers with comprehensive error handling."""

        @self.server.list_resources()
        # Sync function, no await needed
        def list_resources() -> list[Resource]:
            """List available UNS resources."""
            try:
                return [
                    Resource(
                        uri="uns://namespace/hierarchy",
                        name="UNS Namespace Hierarchy",
                        mimeType="application/json",
                        description="Complete ISA-95 hierarchy of all UNS nodes with their current states"
                    ),
                    Resource(
                        uri="uns://config/backends",
                        name="Backend Configuration Status",
                        mimeType="application/json",
                        description="Real-time status of GraphDB, Historian, and MQTT backends"
                    ),
                    Resource(
                        uri="uns://config/node-types",
                        name="Node Type Configuration",
                        mimeType="application/json",
                        description="ISA-95 and SparkplugB node type mappings"
                    ),
                ]
            except Exception as e:
                LOGGER.error(f"Error listing resources: {e}", exc_info=True)
                return []

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a specific UNS resource."""
            try:
                if uri == "uns://namespace/hierarchy":
                    if not self.backend_manager.graphdb:
                        return json.dumps({
                            "error": "GraphDB not available",
                            "message": "GraphDB backend is not connected. Check configuration and logs.",
                            "timestamp": datetime.now(UTC).isoformat()
                        }, indent=2)

                    hierarchy = await self.backend_manager.graphdb.get_namespace_hierarchy()
                    return json.dumps({
                        "hierarchy": hierarchy,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "node_count": len(hierarchy)
                    }, indent=2)

                elif uri == "uns://config/backends":
                    status = {
                        "timestamp": datetime.now(UTC).isoformat(),
                        "backends": {
                            "graphdb": {
                                "available": self.backend_manager.graphdb is not None,
                                "url": GraphDBConfig.conn_url if GraphDBConfig.is_config_valid() else None,
                                "configured": GraphDBConfig.is_config_valid()
                            },
                            "historian": {
                                "available": self.backend_manager.historian is not None,
                                "host": HistorianConfig.hostname if HistorianConfig.is_config_valid() else None,
                                "configured": HistorianConfig.is_config_valid()
                            },
                            "mqtt": {
                                "available": self.backend_manager.mqtt is not None,
                                "host": MQTTConfig.host if MQTTConfig.is_config_valid() else None,
                                "configured": MQTTConfig.is_config_valid()
                            }
                        }
                    }
                    return json.dumps(status, indent=2)

                elif uri == "uns://config/node-types":
                    config = {
                        "timestamp": datetime.now(UTC).isoformat(),
                        "uns_node_types": list(GraphDBConfig.uns_node_types),
                        "spb_node_types": list(GraphDBConfig.spb_node_types),
                        "nested_attribute_type": GraphDBConfig.nested_attribute_node_type
                    }
                    return json.dumps(config, indent=2)

                else:
                    return json.dumps({
                        "error": "Unknown resource URI",
                        "uri": uri,
                        "timestamp": datetime.now(UTC).isoformat()
                    }, indent=2)

            except Exception as e:
                LOGGER.error(
                    f"Error reading resource {uri}: {e}", exc_info=True)
                return json.dumps({
                    "error": "Internal error reading resource",
                    "details": str(e),
                    "uri": uri,
                    "timestamp": datetime.now(UTC).isoformat()
                }, indent=2)

        @self.server.list_tools()
        def list_tools() -> list[Tool]:  # Sync function, no await needed
            """List available UNS tools dynamically based on backend availability."""
            tools = []

            # GraphDB tools
            if self.backend_manager.graphdb:
                tools.extend([
                    Tool(
                        name="get_uns_nodes",
                        description="""Query current state of UNS nodes by topic pattern.

Supports MQTT wildcards:
- '+' for single-level wildcard (e.g., 'factory/+/sensor')
- '#' for multi-level wildcard (e.g., 'factory/#')

Returns consolidated node states with full namespace path, node type, complete payload, and timestamps.

Best for: Getting current state of devices, checking operational status""",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "topics": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "MQTT topic patterns (e.g., ['enterprise/facility/+', 'factory/#'])",
                                    "minItems": 1,
                                    "maxItems": 20
                                }
                            },
                            "required": ["topics"]
                        }
                    ),
                    Tool(
                        name="get_uns_nodes_by_property",
                        description="""Search for nodes containing specific properties/tags.

Finds all nodes that have the specified property keys in their payload, regardless of values.

Best for: Discovery, finding all temperature sensors, locating devices with specific capabilities""",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "property_keys": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Property/tag names to search for",
                                    "minItems": 1,
                                    "maxItems": 10
                                },
                                "topics": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional topic patterns to limit search scope"
                                },
                                "exclude_topics": {
                                    "type": "boolean",
                                    "description": "If true, exclude matching topics",
                                    "default": False
                                }
                            },
                            "required": ["property_keys"]
                        }
                    ),
                ])

            # Historian tools
            if self.backend_manager.historian:
                tools.extend([
                    Tool(
                        name="get_historic_events",
                        description="""Query historical time-series data from the UNS historian.

Retrieves all events published to specified topics within a time range. Limited to 1000 records.

Best for: Trend analysis, historical reporting, debugging message flow""",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "topics": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "MQTT topics (supports wildcards)",
                                    "minItems": 1
                                },
                                "from_datetime": {
                                    "type": "string",
                                    "description": "Start timestamp (ISO 8601: '2024-01-20T10:00:00Z')",
                                    "format": "date-time"
                                },
                                "to_datetime": {
                                    "type": "string",
                                    "description": "End timestamp (ISO 8601)",
                                    "format": "date-time"
                                }
                            },
                            "required": ["topics"]
                        }
                    ),
                    Tool(
                        name="get_historic_events_by_property",
                        description="""Search historical data for events containing specific properties.

Supports AND/OR/NOT operators. Returns up to 1000 matching events.

Best for: Finding when specific metrics were reported, analyzing property correlations""",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "property_keys": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Property names to search for",
                                    "minItems": 1
                                },
                                "binary_operator": {
                                    "type": "string",
                                    "enum": ["AND", "OR", "NOT"],
                                    "description": "Logical operator",
                                    "default": "OR"
                                },
                                "topics": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Optional topic filters"
                                },
                                "from_datetime": {
                                    "type": "string",
                                    "description": "Start timestamp (ISO 8601)",
                                    "format": "date-time"
                                },
                                "to_datetime": {
                                    "type": "string",
                                    "description": "End timestamp (ISO 8601)",
                                    "format": "date-time"
                                }
                            },
                            "required": ["property_keys"]
                        }
                    ),
                ])

            # MQTT tools
            if self.backend_manager.mqtt:
                tools.append(
                    Tool(
                        name="publish_to_uns",
                        description="""Publish data to the Unified Namespace via MQTT.

ONLY way to update UNS data. All changes must go through MQTT.
Payload auto-timestamped if missing. Use QoS 1 or 2 for important data.

Follow ISA-95 structure: <enterprise>/<facility>/<area>/<line>/<device>

Best for: Updating device states, publishing sensor readings, sending commands""",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "topic": {
                                    "type": "string",
                                    "description": "MQTT topic (ISA-95 structure, no wildcards)",
                                    "minLength": 1,
                                    "maxLength": 256,
                                    "pattern": "^[^#+]*$"
                                },
                                "payload": {
                                    "type": "object",
                                    "description": "JSON payload (timestamp added if missing)"
                                },
                                "qos": {
                                    "type": "integer",
                                    "enum": [0, 1, 2],
                                    "description": "QoS: 0=at most once, 1=at least once, 2=exactly once",
                                    "default": 1
                                }
                            },
                            "required": ["topic", "payload"]
                        }
                    )
                )

            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
            """Execute a UNS tool with comprehensive error handling."""
            start_time = datetime.now(UTC)

            try:
                # GraphDB tools
                if name == "get_uns_nodes":
                    if not self.backend_manager.graphdb:
                        return [TextContent(
                            type="text",
                            text=json.dumps({
                                "error": "GraphDB not available",
                                "message": "Cannot query nodes without GraphDB connection.",
                                "tool": name,
                                "timestamp": start_time.isoformat()
                            }, indent=2)
                        )]

                    topics = arguments["topics"]
                    LOGGER.info(f"Querying UNS nodes for topics: {topics}")

                    result = await self.backend_manager.graphdb.get_uns_nodes(topics)

                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "nodes": result,
                            "metadata": {
                                "node_count": len(result),
                                "topics_queried": topics,
                                "timestamp": start_time.isoformat(),
                                "duration_ms": int((datetime.now(UTC) - start_time).total_seconds() * 1000)
                            }
                        }, indent=2, default=str)
                    )]

                elif name == "get_uns_nodes_by_property":
                    if not self.backend_manager.graphdb:
                        return [TextContent(type="text", text=json.dumps({"error": "GraphDB not available"}, indent=2))]

                    property_keys = arguments["property_keys"]
                    topics = arguments.get("topics")
                    exclude_topics = arguments.get("exclude_topics", False)

                    result = await self.backend_manager.graphdb.get_uns_nodes_by_property(
                        property_keys, topics, exclude_topics
                    )

                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "nodes": result,
                            "metadata": {
                                "node_count": len(result),
                                "properties_searched": property_keys,
                                "duration_ms": int((datetime.now(UTC) - start_time).total_seconds() * 1000)
                            }
                        }, indent=2, default=str)
                    )]

                # Historian tools
                elif name == "get_historic_events":
                    if not self.backend_manager.historian:
                        return [TextContent(type="text", text=json.dumps({"error": "Historian not available"}, indent=2))]

                    topics = arguments["topics"]
                    from_dt = arguments.get("from_datetime")
                    to_dt = arguments.get("to_datetime")

                    from_datetime = datetime.fromisoformat(
                        from_dt.replace('Z', '+00:00')) if from_dt else None
                    to_datetime = datetime.fromisoformat(
                        to_dt.replace('Z', '+00:00')) if to_dt else None

                    result = await self.backend_manager.historian.get_historic_events(
                        topics, from_datetime, to_datetime
                    )

                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "events": result,
                            "metadata": {
                                "event_count": len(result),
                                "duration_ms": int((datetime.now(UTC) - start_time).total_seconds() * 1000)
                            }
                        }, indent=2, default=str)
                    )]

                elif name == "get_historic_events_by_property":
                    if not self.backend_manager.historian:
                        return [TextContent(type="text", text=json.dumps({"error": "Historian not available"}, indent=2))]

                    property_keys = arguments["property_keys"]
                    binary_op = arguments.get("binary_operator", "OR")
                    topics = arguments.get("topics")
                    from_dt = arguments.get("from_datetime")
                    to_dt = arguments.get("to_datetime")

                    from_datetime = datetime.fromisoformat(
                        from_dt.replace('Z', '+00:00')) if from_dt else None
                    to_datetime = datetime.fromisoformat(
                        to_dt.replace('Z', '+00:00')) if to_dt else None

                    result = await self.backend_manager.historian.get_historic_events_by_property(
                        property_keys, binary_op, topics, from_datetime, to_datetime
                    )

                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "events": result,
                            "metadata": {"event_count": len(result)}
                        }, indent=2, default=str)
                    )]

                # MQTT tools
                elif name == "publish_to_uns":
                    if not self.backend_manager.mqtt:
                        return [TextContent(type="text", text=json.dumps({"error": "MQTT not available"}, indent=2))]

                    topic = arguments["topic"]
                    payload = arguments["payload"]
                    qos = arguments.get("qos", 1)

                    if '#' in topic or '+' in topic:
                        return [TextContent(type="text", text=json.dumps({
                            "error": "Invalid topic",
                            "message": "Wildcards not allowed in publish topics"
                        }, indent=2))]

                    await self.backend_manager.mqtt.publish(topic, payload, qos)

                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "message": "Data published successfully",
                            "details": {"topic": topic, "qos": qos}
                        }, indent=2)
                    )]

                else:
                    return [TextContent(type="text", text=json.dumps({"error": "Unknown tool", "tool": name}, indent=2))]

            except Exception as e:
                LOGGER.error(
                    f"Error executing tool {name}: {e}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Tool execution failed",
                        "message": str(e),
                        "tool": name
                    }, indent=2)
                )]

        @self.server.list_prompts()
        def list_prompts() -> list[Prompt]:  # Sync function, no await needed
            """List available interaction prompts."""
            return [
                Prompt(
                    name="query_current_state",
                    description="Get current state of devices in a facility",
                    arguments=[
                        {"name": "location", "description": "Facility path", "required": True}]
                ),
                Prompt(
                    name="analyze_trends",
                    description="Analyze historical trends for metrics",
                    arguments=[
                        {"name": "metrics", "description": "Metric names",
                            "required": True},
                        {"name": "hours", "description": "Hours to analyze",
                            "required": False}
                    ]
                ),
            ]

        @self.server.get_prompt()
        def get_prompt(name: str, arguments: dict | None) -> GetPromptResult:  # Sync function
            """Get formatted prompt templates."""
            if name == "query_current_state":
                location = arguments.get(
                    "location", "enterprise") if arguments else "enterprise"
                return GetPromptResult(
                    description=f"Query {location} state",
                    messages=[PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"Show current state of all devices in {location} using get_uns_nodes with '{location}/#'"
                        )
                    )]
                )

            elif name == "analyze_trends":
                metrics = arguments.get(
                    "metrics", "temperature") if arguments else "temperature"
                hours = arguments.get("hours", "24") if arguments else "24"
                return GetPromptResult(
                    description=f"Analyze {metrics} trends",
                    messages=[PromptMessage(
                        role="user",
                        content=TextContent(
                            type="text",
                            text=f"Analyze {metrics} trends over last {hours}h using get_historic_events_by_property"
                        )
                    )]
                )

            raise ValueError(f"Unknown prompt: {name}")


async def main():
    """Main entry point for the UNS MCP Server."""
    server = UNSMCPServer()  # cSpell:ignore UNSMCP

    try:
        # Initialize backends
        status = await server.backend_manager.initialize()
        LOGGER.info(f"Backend status: {status}")

        # Run the server
        LOGGER.info("Starting UNS MCP Server...")
        async with stdio_server() as (read_stream, write_stream):
            await server.server.run(
                read_stream,
                write_stream,
                server.server.create_initialization_options()
            )
    except KeyboardInterrupt:
        LOGGER.info("Server interrupted by user")
    except Exception as e:
        LOGGER.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        # Cleanup
        await server.backend_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
