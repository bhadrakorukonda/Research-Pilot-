import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from agents.search_agent import search_agent

@pytest.fixture
def initial_state():
    return {
        "query": "test query",
        "output_path": "output/report.md",
        "sources": [],
        "summaries": [],
        "critique": "",
        "report": "",
        "messages": []
    }

def test_search_agent_success(initial_state):
    mock_results = {
        "results": [
            {"title": "Source 1", "snippet": "Snippet 1"},
            {"title": "Source 2", "snippet": "Snippet 2"}
        ]
    }
    
    with patch("agents.search_agent.call_mcp_tool") as mock_call:
        mock_call.return_value = mock_results
        
        new_state = search_agent(initial_state)
        
        # Check if call_mcp_tool was called correctly
        mock_call.assert_called_once_with(
            tool_name="web_search",
            arguments={"query": "test query", "max_results": 5}
        )
        
        # Check state updates
        assert len(new_state["sources"]) == 2
        assert new_state["sources"][0]["title"] == "Source 1"
        assert len(new_state["messages"]) == 1
        assert isinstance(new_state["messages"][0], AIMessage)
        assert "Found 2 sources" in new_state["messages"][0].content

def test_search_agent_empty_results(initial_state):
    with patch("agents.search_agent.call_mcp_tool") as mock_call:
        mock_call.return_value = {"results": []}
        
        new_state = search_agent(initial_state)
        
        assert new_state["sources"] == []
        assert "Found 0 sources" in new_state["messages"][0].content

def test_search_agent_malformed_state():
    # Test with missing keys
    state = {"query": "missing sources"}
    with patch("agents.search_agent.call_mcp_tool") as mock_call:
        mock_call.return_value = {"results": []}
        
        # This might raise KeyError if not handled, let's see how search_agent is written
        # search_agent.py: query = state["query"]
        # It doesn't handle missing 'messages' gracefully in the return: state["messages"] + [...]
        with pytest.raises(KeyError):
            search_agent(state)

def test_search_agent_mcp_error(initial_state):
    with patch("agents.search_agent.call_mcp_tool") as mock_call:
        mock_call.side_effect = Exception("MCP Connection failed")
        
        with pytest.raises(Exception) as excinfo:
            search_agent(initial_state)
        assert "MCP Connection failed" in str(excinfo.value)
