"""
ResearchPilot — Core LangGraph Orchestration Graph
----------------------------------------------------
State machine:
    START → search → pdf_fetch → summarize → critique → write → citations → END
Each node is an agent that reads/writes shared ResearchState.
"""

import argparse
import os
from typing import Annotated, TypedDict, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from langgraph.graph.state import CompiledStateGraph

from agents.search_agent    import search_agent
from agents.pdf_agent       import pdf_agent
from agents.summarizer_agent import summarizer_agent
from agents.critic_agent    import critic_agent
from agents.writer_agent    import writer_agent
from agents.citation_agent  import citation_agent

load_dotenv()  # read .env before any LLM_PROVIDER / API-key lookups


# ── Shared state passed between every node ───────────────────────────────────
class ResearchState(TypedDict):
    query:      str                                   # original user query
    output_path: str                                  # where to save the final report
    sources:    List[dict]                            # raw results from search
    summaries:  List[str]                             # per-source summaries
    critique:   str                                   # critic's gap analysis
    report:     str                                   # final written report
    messages:   Annotated[List[BaseMessage], add_messages]  # full message log


# ── Build the graph ───────────────────────────────────────────────────────────
def build_graph() -> CompiledStateGraph:
    """Build and compile the six-node research pipeline."""
    g = StateGraph(ResearchState)

    g.add_node("search",    search_agent)
    g.add_node("pdf_fetch", pdf_agent)
    g.add_node("summarize", summarizer_agent)
    g.add_node("critique",  critic_agent)
    g.add_node("write",     writer_agent)
    g.add_node("citations", citation_agent)

    # Linear pipeline for now; swap add_edge → add_conditional_edges later
    g.set_entry_point("search")
    g.add_edge("search",    "pdf_fetch")
    g.add_edge("pdf_fetch", "summarize")
    g.add_edge("summarize", "critique")
    g.add_edge("critique",  "write")
    g.add_edge("write",     "citations")
    g.add_edge("citations", END)

    return g.compile()


# ── Run helper ────────────────────────────────────────────────────────────────
def run_pipeline(query: str, output_path: str = "output/report.md") -> ResearchState:
    """Run the full pipeline for ``query`` and return the final state."""
    graph = build_graph()
    initial_state: ResearchState = {
        "query":       query,
        "output_path": output_path,
        "sources":     [],
        "summaries":   [],
        "critique":    "",
        "report":      "",
        "messages":    [],
    }
    return graph.invoke(initial_state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ResearchPilot — LangGraph Research Pipeline")
    parser.add_argument("--query", required=True, help="The research question to investigate")
    parser.add_argument("--provider", 
                        default=os.getenv("LLM_PROVIDER", "ollama"),
                        choices=["ollama", "anthropic", "openai"],
                        help="LLM provider (default: ollama or LLM_PROVIDER env var)")
    parser.add_argument("--output", default="output/report.md", help="Path to write the final report")

    args = parser.parse_args()

    # Set LLM_PROVIDER for tools/llm.py
    os.environ["LLM_PROVIDER"] = args.provider

    print(f"[*] Starting research for: {args.query}")
    print(f"[*] Using provider: {args.provider}")

    run_pipeline(args.query, args.output)

    print("\n[✔] Research complete!")
    print(f"[*] Report saved to: {args.output}")