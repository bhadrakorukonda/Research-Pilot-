"""
Writer Agent
------------
Compiles summaries + critique into a clean, structured Markdown research report.
Optionally saves it via the MCP filesystem tool.
"""

from langchain_core.messages import AIMessage
from tools.llm import get_llm
from tools.mcp_client import call_mcp_tool


def writer_agent(state: dict) -> dict:
    llm       = get_llm()
    query     = state["query"]
    summaries = state["summaries"]
    critique  = state["critique"]

    print("[WriterAgent] Compiling final report...")

    combined = "\n\n---\n\n".join(summaries)

    prompt = (
        f"You are a research writer. Produce a professional, well-structured Markdown report.\n\n"
        f"## Topic\n{query}\n\n"
        f"## Source Summaries\n{combined}\n\n"
        f"## Critic's Notes\n{critique}\n\n"
        f"Write the report with these sections:\n"
        f"1. Executive Summary (2-3 sentences)\n"
        f"2. Key Findings (bullet points)\n"
        f"3. Detailed Analysis (prose, ~3 paragraphs)\n"
        f"4. Open Questions / Future Work\n"
        f"5. Sources\n\n"
        f"Use clean Markdown. Be factual and precise."
    )

    response = llm.invoke(prompt)
    report   = response.content if hasattr(response, "content") else str(response)

    # Persist via MCP filesystem tool
    call_mcp_tool(
        tool_name="write_file",
        arguments={
            "path":    "output/report.md",
            "content": report,
        },
    )

    return {
        **state,
        "report":   report,
        "messages": state["messages"] + [
            AIMessage(content="[WriterAgent] Report written to output/report.md")
        ],
    }