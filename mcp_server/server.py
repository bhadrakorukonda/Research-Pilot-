"""
ResearchPilot MCP Tool Server
------------------------------
Exposes tools over the Model Context Protocol (stdio transport):
  • web_search        — uses Brave Search API (or mocked for dev)
  • write_file        — writes content to local filesystem
  • fetch_pdf         — downloads and extracts text from a PDF
  • extract_citations — extracts DOIs, arXiv IDs, and Author-Year citations

Run with:
    python mcp_server/server.py

Agents connect via MCPClient (tools/mcp_client.py).
"""

import json
import os
import re
import sys
from io import BytesIO
from pathlib import Path

# pip install mcp pypdf
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx
from pypdf import PdfReader


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
        Tool(
            name="fetch_pdf",
            description="Download a PDF from a URL and extract its text content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL of the PDF file"},
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="extract_citations",
            description="Extract citation patterns (DOI, arXiv, Author-Year) from raw text.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Raw text to scan for citations"},
                },
                "required": ["text"],
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

    if name == "fetch_pdf":
        return await _fetch_pdf(arguments)

    if name == "extract_citations":
        return await _extract_citations(arguments)

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


async def _fetch_pdf(args: dict) -> list[TextContent]:
    url = args["url"]
    print(f"Fetching PDF: {url}", file=sys.stderr)

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        pdf_bytes = BytesIO(resp.content)

    reader = PdfReader(pdf_bytes)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    return [TextContent(type="text", text=json.dumps({"url": url, "content": text}))]


async def _extract_citations(args: dict) -> list[TextContent]:
    text = args["text"]

    # Patterns:
    # 1. DOI: 10.\d{4,9}/[-._;()/:A-Z0-9]+
    # 2. arXiv: arXiv:\d{4}\.\d{4,5}
    # 3. Author-Year: (Author et al., 2023) or (Author, 2023)
    patterns = [
        r"10\.\d{4,9}/[-._;()/:A-Z0-9]+",
        r"arXiv:\d{4}\.\d{4,5}",
        r"\([A-Z][a-z]+(?: et al\.)?, \d{4}\)",
    ]

    found = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        found.extend(matches)

    # De-duplicate
    found = list(set(found))

    return [TextContent(type="text", text=json.dumps({"citations": found}))]


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio
    asyncio.run(stdio_server(app))
