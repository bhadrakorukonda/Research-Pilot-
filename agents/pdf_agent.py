"""
PDF Agent
---------
Checks sources for PDF links and extracts text using the MCP `fetch_pdf` tool.
"""

from langchain_core.messages import AIMessage
from tools.mcp_client import call_mcp_tool

def pdf_agent(state: dict) -> dict:
    sources = state.get("sources", [])
    updated_sources = []
    pdf_count = 0

    print(f"[PDFAgent] Checking {len(sources)} sources for PDFs...")

    for source in sources:
        url = source.get("url", "")
        is_pdf = url.lower().endswith(".pdf") or "arxiv.org/pdf" in url.lower()

        if is_pdf:
            print(f"[PDFAgent] Extracting text from PDF: {url}")
            try:
                result = call_mcp_tool(
                    tool_name="fetch_pdf",
                    arguments={"url": url}
                )
                if result and "content" in result:
                    source["content"] = result["content"]
                    pdf_count += 1
            except Exception as e:
                print(f"[PDFAgent] Error fetching PDF {url}: {e}")
                # Keep original source as is (maybe it has a snippet already)
        
        updated_sources.append(source)

    return {
        **state,
        "sources": updated_sources,
        "messages": state["messages"] + [
            AIMessage(content=f"[PDFAgent] Processed {pdf_count} PDFs.")
        ],
    }
