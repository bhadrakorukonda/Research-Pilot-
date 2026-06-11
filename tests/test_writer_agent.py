import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from agents.writer_agent import writer_agent

@pytest.fixture
def state_for_writer():
    return {
        "query": "test query",
        "output_path": "custom/path.md",
        "sources": [],
        "summaries": ["Summary 1", "Summary 2"],
        "critique": "Some critique",
        "report": "",
        "messages": []
    }

def test_writer_agent_success(state_for_writer):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="# Final Report Content")
    
    with patch("agents.writer_agent.get_llm", return_value=mock_llm), \
         patch("agents.writer_agent.call_mcp_tool") as mock_mcp:
        
        new_state = writer_agent(state_for_writer)
        
        assert new_state["report"] == "# Final Report Content"
        assert mock_llm.invoke.called
        
        # Check if MCP write_file was called with the custom path from state
        mock_mcp.assert_called_once_with(
            tool_name="write_file",
            arguments={
                "path": "custom/path.md",
                "content": "# Final Report Content"
            }
        )
        
        assert len(new_state["messages"]) == 1
        assert "Report written to custom/path.md" in new_state["messages"][0].content

def test_writer_agent_mcp_failure(state_for_writer):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="# Final Report Content")
    
    with patch("agents.writer_agent.get_llm", return_value=mock_llm), \
         patch("agents.writer_agent.call_mcp_tool") as mock_mcp:
        
        mock_mcp.side_effect = Exception("FS Write Error")
        
        with pytest.raises(Exception) as excinfo:
            writer_agent(state_for_writer)
        assert "FS Write Error" in str(excinfo.value)

def test_writer_agent_missing_input():
    state = {
        "query": "test",
        "summaries": [],
        "critique": "",
        "messages": []
    }
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="Empty Report")
    
    with patch("agents.writer_agent.get_llm", return_value=mock_llm), \
         patch("agents.writer_agent.call_mcp_tool"):
        
        new_state = writer_agent(state)
        assert new_state["report"] == "Empty Report"
