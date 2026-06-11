import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from agents.critic_agent import critic_agent

@pytest.fixture
def state_with_summaries():
    return {
        "query": "test query",
        "output_path": "output/report.md",
        "sources": [],
        "summaries": [
            "**Source 1**\nSummary 1",
            "**Source 2**\nSummary 2"
        ],
        "critique": "",
        "report": "",
        "messages": []
    }

def test_critic_agent_success(state_with_summaries):
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="Mock Critique")
    
    with patch("agents.critic_agent.get_llm", return_value=mock_llm):
        new_state = critic_agent(state_with_summaries)
        
        assert new_state["critique"] == "Mock Critique"
        assert mock_llm.invoke.called
        # Check if summaries were passed to prompt
        prompt = mock_llm.invoke.call_args[0][0]
        assert "Summary 1" in prompt
        assert "Summary 2" in prompt
        assert "test query" in prompt
        
        assert len(new_state["messages"]) == 1
        assert "Critique complete" in new_state["messages"][0].content

def test_critic_agent_empty_summaries():
    state = {
        "query": "test",
        "summaries": [],
        "messages": []
    }
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = AIMessage(content="No summaries to critique.")
    
    with patch("agents.critic_agent.get_llm", return_value=mock_llm):
        new_state = critic_agent(state)
        
        assert new_state["critique"] == "No summaries to critique."
        assert len(new_state["messages"]) == 1

def test_critic_agent_llm_error(state_with_summaries):
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = Exception("LLM Error")
    
    with patch("agents.critic_agent.get_llm", return_value=mock_llm):
        with pytest.raises(Exception):
            critic_agent(state_with_summaries)
