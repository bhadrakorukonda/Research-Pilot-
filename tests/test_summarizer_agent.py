import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from agents.summarizer_agent import summarizer_agent

@pytest.fixture
def state_with_sources():
    return {
        "query": "test query",
        "output_path": "output/report.md",
        "sources": [
            {"title": "Source 1", "content": "Content 1"},
            {"title": "Source 2", "snippet": "Snippet 2"}
        ],
        "summaries": [],
        "critique": "",
        "report": "",
        "messages": []
    }

def test_summarizer_agent_success(state_with_sources):
    mock_llm = MagicMock()
    # Mock invoke to return different summaries for each call
    mock_llm.invoke.side_effect = [
        AIMessage(content="Summary 1"),
        AIMessage(content="Summary 2")
    ]
    
    with patch("agents.summarizer_agent.get_llm", return_value=mock_llm):
        new_state = summarizer_agent(state_with_sources)
        
        assert len(new_state["summaries"]) == 2
        assert "**Source 1**\nSummary 1" in new_state["summaries"]
        assert "**Source 2**\nSummary 2" in new_state["summaries"]
        assert mock_llm.invoke.call_count == 2
        assert len(new_state["messages"]) == 1
        assert "Produced 2 summaries" in new_state["messages"][0].content

def test_summarizer_agent_no_sources():
    state = {
        "query": "test",
        "sources": [],
        "summaries": [],
        "messages": []
    }
    mock_llm = MagicMock()
    
    with patch("agents.summarizer_agent.get_llm", return_value=mock_llm):
        new_state = summarizer_agent(state)
        
        assert new_state["summaries"] == []
        assert mock_llm.invoke.call_count == 0
        assert "Produced 0 summaries" in new_state["messages"][0].content

def test_summarizer_agent_malformed_source(state_with_sources):
    # Source with no content or snippet
    state_with_sources["sources"].append({"title": "Bad Source"})
    
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="Default Summary")
    
    with patch("agents.summarizer_agent.get_llm", return_value=mock_llm):
        new_state = summarizer_agent(state_with_sources)
        
        assert len(new_state["summaries"]) == 3
        # Check that the 3rd call used "No content available."
        last_call_args = mock_llm.invoke.call_args_list[2][0][0]
        assert "No content available." in last_call_args

def test_summarizer_agent_llm_error(state_with_sources):
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = Exception("LLM Timeout")
    
    with patch("agents.summarizer_agent.get_llm", return_value=mock_llm):
        with pytest.raises(Exception) as excinfo:
            summarizer_agent(state_with_sources)
        assert "LLM Timeout" in str(excinfo.value)
