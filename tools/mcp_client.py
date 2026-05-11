"""
MCP Client
----------
Thin synchronous wrapper that agents use to call the MCP server.
Spawns the server as a subprocess (stdio transport) and caches the session.

Usage:
    from tools.mcp_client import call_mcp_tool

    results = call_mcp_tool("web_search", {"query": "GNN traffic forecasting"})
"""

import asyncio
import json
from functools import lru_cache
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVER_SCRIPT = str(Path(__file__).parent.parent / "mcp_server" / "server.py")


async def _call_tool_async(tool_name: str, arguments: dict) -> dict:
    """Open a fresh stdio session, call one tool, close."""
    server_params = StdioServerParameters(
        command="python",
        args=[SERVER_SCRIPT],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            # result.content is a list of TextContent / ImageContent blocks
            text_blocks = [b.text for b in result.content if hasattr(b, "text")]
            raw = text_blocks[0] if text_blocks else "{}"
            return json.loads(raw)


def call_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Synchronous entry point for agent nodes."""
    return asyncio.run(_call_tool_async(tool_name, arguments))