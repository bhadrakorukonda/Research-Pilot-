"""
ResearchPilot MCP Tool Server
------------------------------
Exposes two tools over the Model Context Protocol (stdio transport):
  • web_search  — uses Brave Search API (or mocked for dev)
  • write_file  — writes content to local filesystem

Run with:
    python mcp_server/server.py

Agents connect via MCPClient (tools/mcp_client.py).
"""

import json
import os
import sys
from pathlib import Path

# pip install mcp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx


app = Server("researchpilot-tools")

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")
OUTPUT_DIR    = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ── Tool definitions ──────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="web_search",
            description="Search the web for research content using Brave Search.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query":       {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="write_file",
            description="Write text content to a file in the output directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path":    {"type": "string", "description": "Relative path under output/"},
                    "content": {"type": "string", "description": "File content"},
                },
                "required": ["path", "content"],
            },
        ),
    ]


# ── Tool handlers ─────────────────────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:

    if name == "web_search":
        return await _web_search(arguments)

    if name == "write_file":
        return await _write_file(arguments)

    raise ValueError(f"Unknown tool: {name}")


async def _web_search(args: dict) -> list[TextContent]:
    query       = args["query"]
    max_results = args.get("max_results", 5)

    if not BRAVE_API_KEY:
        # ── Dev mock — swap for real Brave call in production ──
        mock = {
            "results": [
                {
                    "title":   f"[MOCK] Paper on {query} #{i}",
                    "url":     f"https://example.com/paper{i}",
                    "snippet": f"This mock result discusses key aspects of {query}, "
                               f"including methodology, datasets, and evaluation metrics. "
                               f"Result #{i}.",
                }
                for i in range(1, max_results + 1)
            ]
        }
        return [TextContent(type="text", text=json.dumps(mock))]

    # ── Real Brave Search ──
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY},
            params={"q": query, "count": max_results},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

    results = [
        {
            "title":   r.get("title", ""),
            "url":     r.get("url", ""),
            "snippet": r.get("description", ""),
        }
        for r in data.get("web", {}).get("results", [])
    ]
    return [TextContent(type="text", text=json.dumps({"results": results}))]


async def _write_file(args: dict) -> list[TextContent]:
    target = OUTPUT_DIR / args["path"].lstrip("/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(args["content"], encoding="utf-8")
    msg = f"File written: {target}"
    print(msg, file=sys.stderr)
    return [TextContent(type="text", text=json.dumps({"status": "ok", "path": str(target)}))]


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio
    asyncio.run(stdio_server(app))