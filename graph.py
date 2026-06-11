"""
ResearchPilot — Core LangGraph Orchestration Graph
----------------------------------------------------
State machine:  START → search → summarize → critique → write → END
Each node is an agent that reads/writes shared ResearchState.
"""

import argparse
import os
from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from agents.search_agent    import search_agent
from agents.summarizer_agent import summarizer_agent
from agents.critic_agent    import critic_agent
from agents.writer_agent    import writer_agent


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
def build_graph() -> StateGraph:
    g = StateGraph(ResearchState)

    g.add_node("search",    search_agent)
    g.add_node("summarize", summarizer_agent)
    g.add_node("critique",  critic_agent)
    g.add_node("write",     writer_agent)

    # Linear pipeline for now; swap add_edge → add_conditional_edges later
    g.set_entry_point("search")
    g.add_edge("search",    "summarize")
    g.add_edge("summarize", "critique")
    g.add_edge("critique",  "write")
    g.add_edge("write",     END)

    return g.compile()


# ── Run helper ────────────────────────────────────────────────────────────────
def run_pipeline(query: str, output_path: str = "output/report.md") -> ResearchState:
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

    result = run_pipeline(args.query, args.output)

    print(f"\n[✔] Research complete!")
    print(f"[*] Report saved to: {args.output}")