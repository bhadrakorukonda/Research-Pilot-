"""
Search Agent
------------
Calls the MCP tool server to fetch web/paper results for the query.
Returns populated state["sources"].
"""

from langchain_core.messages import AIMessage
from tools.mcp_client import call_mcp_tool


def search_agent(state: dict) -> dict:
    query = state["query"]
    print(f"[SearchAgent] Searching for: {query}")

    # Call our MCP server's `web_search` tool
    raw_results = call_mcp_tool(
        tool_name="web_search",
        arguments={"query": query, "max_results": 5},
    )

    sources = raw_results.get("results", [])

    return {
        **state,
        "sources": sources,
        "messages": state["messages"] + [
            AIMessage(content=f"[SearchAgent] Found {len(sources)} sources for '{query}'")
        ],
    }