"""
Citation Agent
--------------
Extracts citations from summaries and appends a References section to the final report.
"""

import json
from langchain_core.messages import AIMessage
from tools.mcp_client import call_mcp_tool

def citation_agent(state: dict) -> dict:
    summaries = state.get("summaries", [])
    report = state.get("report", "")
    output_path = state.get("output_path", "output/report.md")
    
    if not summaries or not report:
        return state

    print(f"[CitationAgent] Extracting citations from {len(summaries)} summaries...")
    combined_summaries = "\n\n".join(summaries)
    
    try:
        result = call_mcp_tool(
            tool_name="extract_citations",
            arguments={"text": combined_summaries}
        )
        citations = result.get("citations", [])
    except Exception as e:
        print(f"[CitationAgent] Error extracting citations: {e}")
        return state

    if not citations:
        print("[CitationAgent] No citations found.")
        return state

    print(f"[CitationAgent] Found {len(citations)} citations. Appending to report...")
    
    # Build References section
    ref_section = "\n\n## References\n"
    for cite in sorted(citations):
        ref_section += f"- {cite}\n"
    
    updated_report = report + ref_section
    
    # Overwrite the file with the updated report
    try:
        call_mcp_tool(
            tool_name="write_file",
            arguments={
                "path": output_path,
                "content": updated_report
            }
        )
    except Exception as e:
        print(f"[CitationAgent] Error updating report file: {e}")
        # We still update the state even if file write fails

    return {
        **state,
        "report": updated_report,
        "messages": state["messages"] + [
            AIMessage(content=f"[CitationAgent] Appended {len(citations)} references to report.")
        ],
    }
