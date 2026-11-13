"""
Search Agent
------------
Calls the MCP tool server to fetch web/paper results for the query.
Returns populated state["sources"].
"""

from langchain_core.messages import AIMessage
from tools.mcp_client import call_mcp_tool


def search_agent(state: dict) -> dict:
    """Populate state["sources"] from the MCP web_search tool."""
    query = state["query"]
    print(f"[SearchAgent] Searching for: {query}")

    # Call our MCP server's `web_search` tool
    raw_results = call_mcp_tool(
        tool_name="web_search",
        arguments={"query": query, "max_results": 5},
    )

    sources = raw_results.get("results", [])
    if raw_results.get("mock"):
        print("[SearchAgent] WARNING: using MOCK search results - set BRAVE_API_KEY for real sources.")

    return {
        **state,
        "sources": sources,
        "messages": state["messages"] + [
            AIMessage(content=f"[SearchAgent] Found {len(sources)} sources for '{query}'")
        ],
    }