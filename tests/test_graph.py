"""Smoke tests for the LangGraph wiring (no LLM or MCP calls)."""

from graph import build_graph


def test_graph_compiles_with_all_nodes():
    graph = build_graph()
    nodes = set(graph.get_graph().nodes)
    assert {"search", "pdf_fetch", "summarize", "critique", "write", "citations"} <= nodes


def test_cli_prints_are_ascii_safe():
    """Non-ASCII in print() crashes on Windows consoles (cp1252)."""
    import ast
    from pathlib import Path

    tree = ast.parse(Path("graph.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "print":
            for const in ast.walk(node):
                if isinstance(const, ast.Constant) and isinstance(const.value, str):
                    assert const.value.isascii(), const.value
