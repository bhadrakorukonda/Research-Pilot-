"""
LLM Factory
-----------
Returns a LangChain-compatible chat model.
Controlled by the LLM_PROVIDER env var:

    LLM_PROVIDER=ollama        → local Ollama (default, free)
    LLM_PROVIDER=anthropic     → Claude via Anthropic API
    LLM_PROVIDER=openai        → GPT-4o

Set the matching API key env var when using cloud providers.
"""

import os
from langchain_core.language_models.chat_models import BaseChatModel


def get_llm() -> BaseChatModel:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Choose ollama | anthropic | openai")