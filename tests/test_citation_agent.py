import pytest
from unittest.mock import patch

from agents.citation_agent import citation_agent


@pytest.fixture
def state_with_report():
    return {
        "query": "test query",
        "output_path": "output/report.md",
        "sources": [
            {"title": "PDF Paper", "url": "https://arxiv.org/pdf/2101.12345",
             "content": "Full text citing arXiv:2101.11111 and doi 10.1038/s41586-021-03491-6."},
            {"title": "Web Page", "url": "https://example.com/a", "snippet": "A snippet."},
        ],
        "summaries": ["Summary mentioning (Smith, 2023)"],
        "report": "# Research Report\nThis is the content.",
        "messages": [],
    }


def test_citation_agent_uses_full_source_text(state_with_report):
    with patch("agents.citation_agent.call_mcp_tool") as mock_call:
        mock_call.side_effect = [{"citations": ["10.1038/s41586-021-03491-6"]}, {"status": "ok"}]

        citation_agent(state_with_report)

        sent = mock_call.call_args_list[0].kwargs["arguments"]["text"]
        assert "arXiv:2101.11111" in sent  # from PDF content, not a summary
        assert "A snippet." in sent        # snippet fallback
        assert "(Smith, 2023)" in sent     # summaries still included


def test_citation_agent_appends_sources_and_citations(state_with_report):
    with patch("agents.citation_agent.call_mcp_tool") as mock_call:
        mock_call.side_effect = [{"citations": ["(Smith, 2023)", "arXiv:2101.11111"]}, {"status": "ok"}]

        new_state = citation_agent(state_with_report)

        report = new_state["report"]
        assert "## References" in report
        assert "- PDF Paper — https://arxiv.org/pdf/2101.12345" in report
        assert "- Web Page — https://example.com/a" in report
        assert "- (Smith, 2023)" in report
        assert "- arXiv:2101.11111" in report
        mock_call.assert_any_call(
            tool_name="write_file",
            arguments={"path": "output/report.md", "content": report},
        )
        assert "2 sources and 2 citations" in new_state["messages"][0].content


def test_citation_agent_lists_sources_even_without_citations(state_with_report):
    with patch("agents.citation_agent.call_mcp_tool") as mock_call:
        mock_call.side_effect = [{"citations": []}, {"status": "ok"}]

        new_state = citation_agent(state_with_report)

        assert "### Sources" in new_state["report"]
        assert "### Cited works" not in new_state["report"]


def test_citation_agent_nothing_to_cite_leaves_report_unchanged(state_with_report):
    state_with_report["sources"] = []
    with patch("agents.citation_agent.call_mcp_tool") as mock_call:
        mock_call.return_value = {"citations": []}

        new_state = citation_agent(state_with_report)

        assert new_state["report"] == state_with_report["report"]
        assert mock_call.call_count == 1  # extraction only, no write


def test_citation_agent_no_report_is_noop(state_with_report):
    state_with_report["report"] = ""
    with patch("agents.citation_agent.call_mcp_tool") as mock_call:
        citation_agent(state_with_report)
        mock_call.assert_not_called()


def test_citation_agent_extraction_error_leaves_report_unchanged(state_with_report):
    with patch("agents.citation_agent.call_mcp_tool", side_effect=Exception("MCP Error")):
        new_state = citation_agent(state_with_report)
        assert new_state["report"] == state_with_report["report"]
        assert new_state["messages"] == []


def test_citation_agent_write_failure_still_updates_state(state_with_report):
    with patch("agents.citation_agent.call_mcp_tool") as mock_call:
        mock_call.side_effect = [{"citations": ["Cite 1"]}, Exception("Write Failed")]
        new_state = citation_agent(state_with_report)
        assert "- Cite 1" in new_state["report"]
        assert len(new_state["messages"]) == 1
