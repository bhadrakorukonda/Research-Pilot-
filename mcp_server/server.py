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

import asyncio
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
PROJECT_ROOT  = Path(__file__).resolve().parent.parent
MAX_PDF_BYTES = 20 * 1024 * 1024  # refuse PDFs larger than 20 MB


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
            description="Write text content to a file inside the project directory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path":    {"type": "string", "description": "File path relative to the project root"},
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


def _resolve_inside_root(relative_path: str) -> Path:
    """Resolve ``relative_path`` against the project root, rejecting escapes."""
    target = (PROJECT_ROOT / relative_path).resolve()
    if not target.is_relative_to(PROJECT_ROOT):
        raise ValueError(f"Path escapes the project directory: {relative_path}")
    return target


async def _write_file(args: dict) -> list[TextContent]:
    target = _resolve_inside_root(args["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(args["content"], encoding="utf-8")
    print(f"File written: {target}", file=sys.stderr)
    return [TextContent(type="text", text=json.dumps({"status": "ok", "path": str(target)}))]


async def _fetch_pdf(args: dict) -> list[TextContent]:
    url = args["url"]
    print(f"Fetching PDF: {url}", file=sys.stderr)

    chunks: list[bytes] = []
    size = 0
    async with httpx.AsyncClient(follow_redirects=True) as client:
        async with client.stream("GET", url, timeout=30) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes():
                size += len(chunk)
                if size > MAX_PDF_BYTES:
                    raise ValueError(f"PDF exceeds {MAX_PDF_BYTES} bytes: {url}")
                chunks.append(chunk)

    reader = PdfReader(BytesIO(b"".join(chunks)))
    text = "".join(page.extract_text() or "" for page in reader.pages)

    return [TextContent(type="text", text=json.dumps({"url": url, "content": text}))]


async def _extract_citations(args: dict) -> list[TextContent]:
    text = args["text"]

    # (pattern, flags): DOI/arXiv are case-insensitive; Author-Year must be
    # case-sensitive or it matches lowercase words such as "(see, 2023)".
    #   1. DOI:         10.\d{4,9}/...
    #   2. arXiv:       arXiv:\d{4}.\d{4,5}
    #   3. Author-Year: (Author et al., 2023) or (Author, 2023)
    patterns = [
        (r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE),
        (r"arXiv:\d{4}\.\d{4,5}", re.IGNORECASE),
        (r"\([A-Z][a-z]+(?: et al\.)?, \d{4}\)", 0),
    ]

    found: set[str] = set()
    for pattern, flags in patterns:
        for match in re.findall(pattern, text, flags):
            found.add(match.rstrip(".,;:"))  # drop sentence punctuation

    return [TextContent(type="text", text=json.dumps({"citations": sorted(found)}))]


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    """Serve the MCP tools over stdio until the client disconnects."""
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
