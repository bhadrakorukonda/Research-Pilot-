import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from agents.pdf_agent import pdf_agent

@pytest.fixture
def state_with_mixed_sources():
    return {
        "query": "test query",
        "sources": [
            {"url": "https://example.com/paper.pdf", "title": "PDF Paper"},
            {"url": "https://arxiv.org/pdf/2101.12345", "title": "Arxiv Paper"},
            {"url": "https://example.com/article", "title": "Normal Webpage", "content": "Original content"}
        ],
        "messages": []
    }

def test_pdf_agent_success(state_with_mixed_sources):
    mock_pdf_content = "Extracted PDF text content."
    
    with patch("agents.pdf_agent.call_mcp_tool") as mock_call:
        mock_call.return_value = {"content": mock_pdf_content}
        
        new_state = pdf_agent(state_with_mixed_sources)
        
        # Should call fetch_pdf twice
        assert mock_call.call_count == 2
        
        # PDF sources should have updated content
        assert new_state["sources"][0]["content"] == mock_pdf_content
        assert new_state["sources"][1]["content"] == mock_pdf_content
        
        # Non-PDF source should remain unchanged
        assert new_state["sources"][2]["content"] == "Original content"
        
        # Check messages
        assert len(new_state["messages"]) == 1
        assert "Processed 2 PDFs" in new_state["messages"][0].content

def test_pdf_agent_fetch_error(state_with_mixed_sources):
    with patch("agents.pdf_agent.call_mcp_tool") as mock_call:
        # First call fails, second succeeds
        mock_call.side_effect = [
            Exception("Connection Error"),
            {"content": "Arxiv content"}
        ]
        
        new_state = pdf_agent(state_with_mixed_sources)
        
        # Should not crash
        assert mock_call.call_count == 2
        
        # First PDF should not have 'content' field if it didn't exist, or remain unchanged
        assert "content" not in new_state["sources"][0]
        assert new_state["sources"][1]["content"] == "Arxiv content"
        
        # Processed count should be 1
        assert "Processed 1 PDFs" in new_state["messages"][0].content

def test_pdf_agent_no_pdfs():
    state = {
        "sources": [{"url": "https://example.com/page"}],
        "messages": []
    }
    with patch("agents.pdf_agent.call_mcp_tool") as mock_call:
        new_state = pdf_agent(state)
        assert mock_call.call_count == 0
        assert "Processed 0 PDFs" in new_state["messages"][0].content
