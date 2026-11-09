"""
Citation Agent
--------------
Appends a References section to the final report: every source (title + URL)
plus any DOI / arXiv / Author-Year citations found in the full source text.
"""

from langchain_core.messages import AIMessage
from tools.mcp_client import call_mcp_tool


def _source_text(source: dict) -> str:
    """Return the richest text available for a source (PDF content, else snippet)."""
    return source.get("content") or source.get("snippet") or ""


def _format_source(source: dict) -> str:
    """Render one source as a Markdown list item."""
    title = source.get("title") or "Untitled"
    url = source.get("url", "")
    return f"- {title} — {url}" if url else f"- {title}"


def citation_agent(state: dict) -> dict:
    """Append a References section to state["report"] and re-save the report.

    Citations are extracted from the full text of state["sources"] (plus the
    summaries), not just the summaries, so identifiers in PDFs are not lost.
    State is returned unchanged if there is no report or nothing to cite.
    """
    sources = state.get("sources", [])
    summaries = state.get("summaries", [])
    report = state.get("report", "")
    output_path = state.get("output_path", "output/report.md")

    if not report or not (sources or summaries):
        return state

    print(f"[CitationAgent] Extracting citations from {len(sources)} sources...")
    combined = "\n\n".join([_source_text(s) for s in sources] + summaries)

    try:
        result = call_mcp_tool(tool_name="extract_citations", arguments={"text": combined})
        citations = result.get("citations", [])
    except Exception as e:
        print(f"[CitationAgent] Error extracting citations: {e}")
        return state

    source_lines = [_format_source(s) for s in sources]
    if not source_lines and not citations:
        print("[CitationAgent] No citations found.")
        return state

    ref_section = "\n\n## References\n"
    if source_lines:
        ref_section += "\n### Sources\n" + "\n".join(source_lines) + "\n"
    if citations:
        ref_section += "\n### Cited works\n" + "\n".join(f"- {c}" for c in sorted(citations)) + "\n"

    updated_report = report + ref_section
    print(f"[CitationAgent] Appending {len(source_lines)} sources and {len(citations)} citations...")

    try:
        call_mcp_tool(
            tool_name="write_file",
            arguments={"path": output_path, "content": updated_report},
        )
    except Exception as e:
        print(f"[CitationAgent] Error updating report file: {e}")
        # State is still updated even if the file write fails

    return {
        **state,
        "report": updated_report,
        "messages": state["messages"] + [
            AIMessage(
                content=f"[CitationAgent] Appended {len(source_lines)} sources "
                        f"and {len(citations)} citations to report."
            )
        ],
    }
