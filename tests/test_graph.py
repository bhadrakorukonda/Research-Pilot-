"""Smoke tests for the LangGraph wiring (no LLM or MCP calls)."""

from graph import build_graph


def test_graph_compiles_with_all_nodes():
    graph = build_graph()
    nodes = set(graph.get_graph().nodes)
    assert {"search", "pdf_fetch", "summarize", "critique", "write", "citations"} <= nodes
