"""Unmocked tests: real MCP client talking to the real server subprocess."""

import pytest

from tools.mcp_client import call_mcp_tool


@pytest.fixture(autouse=True)
def _mock_search_mode(monkeypatch):
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)


def test_web_search_roundtrip_returns_mock_results():
    result = call_mcp_tool("web_search", {"query": "graph networks", "max_results": 2})
    assert len(result["results"]) == 2
    assert result["results"][0]["title"].startswith("[MOCK]")


def test_extract_citations_roundtrip():
    result = call_mcp_tool(
        "extract_citations", {"text": "See arXiv:2101.12345 and 10.1038/s41586-021-03491-6."}
    )
    assert "arXiv:2101.12345" in result["citations"]
