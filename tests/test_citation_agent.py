import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from agents.citation_agent import citation_agent

@pytest.fixture
def state_with_report():
    return {
        "query": "test query",
        "output_path": "output/report.md",
        "summaries": ["Summary 1 with (Smith, 2023)", "Summary 2 with DOI: 10.1038/s41586-021-03491-6"],
        "report": "# Research Report\nThis is the content.",
        "messages": []
    }

def test_citation_agent_success(state_with_report):
    mock_citations = ["(Smith, 2023)", "10.1038/s41586-021-03491-6"]
    
    with patch("agents.citation_agent.call_mcp_tool") as mock_call:
        # First call: extract_citations, Second call: write_file
        mock_call.side_effect = [
            {"citations": mock_citations},
            {"status": "ok"}
        ]
        
        new_state = citation_agent(state_with_report)
        
        # Check extraction call
        mock_call.assert_any_call(
            tool_name="extract_citations",
            arguments={"text": "Summary 1 with (Smith, 2023)\n\nSummary 2 with DOI: 10.1038/s41586-021-03491-6"}
        )
        
        # Check report update
        assert "## References" in new_state["report"]
        assert "- (Smith, 2023)" in new_state["report"]
        assert "- 10.1038/s41586-021-03491-6" in new_state["report"]
        
        # Check file write call
        mock_call.assert_any_call(
            tool_name="write_file",
            arguments={
                "path": "output/report.md",
                "content": new_state["report"]
            }
        )
        
        assert len(new_state["messages"]) == 1
        assert "Appended 2 references" in new_state["messages"][0].content

def test_citation_agent_empty_citations(state_with_report):
    with patch("agents.citation_agent.call_mcp_tool") as mock_call:
        mock_call.return_value = {"citations": []}
        
        new_state = citation_agent(state_with_report)
        
        # Report should be unchanged
        assert new_state["report"] == state_with_report["report"]
        assert "## References" not in new_state["report"]
        assert mock_call.call_count == 1 # Only extraction called

def test_citation_agent_error_handling(state_with_report):
    with patch("agents.citation_agent.call_mcp_tool") as mock_call:
        mock_call.side_effect = Exception("MCP Error")
        
        new_state = citation_agent(state_with_report)
        
        # Should exit gracefully without modifying report
        assert new_state["report"] == state_with_report["report"]
        assert len(new_state["messages"]) == 0

def test_citation_agent_write_failure(state_with_report):
    with patch("agents.citation_agent.call_mcp_tool") as mock_call:
        mock_call.side_effect = [
            {"citations": ["Cite 1"]},
            Exception("Write Failed")
        ]
        
        new_state = citation_agent(state_with_report)
        
        # Report in state should still be updated even if file write failed
        assert "## References" in new_state["report"]
        assert "- Cite 1" in new_state["report"]
        assert len(new_state["messages"]) == 1
