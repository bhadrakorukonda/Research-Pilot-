"""
Summarizer Agent
----------------
Takes each source from state["sources"] and produces a concise summary.
Uses the LLM directly (no tool call needed here).
"""

from langchain_core.messages import AIMessage
from tools.llm import get_llm


def summarizer_agent(state: dict) -> dict:
    llm = get_llm()
    sources = state["sources"]
    summaries = []

    print(f"[SummarizerAgent] Summarizing {len(sources)} sources...")

    for i, source in enumerate(sources):
        title   = source.get("title", f"Source {i+1}")
        content = source.get("content", source.get("snippet", "No content available."))

        prompt = (
            f"Summarize the following research content in 3-5 bullet points.\n"
            f"Title: {title}\n\n"
            f"Content:\n{content[:3000]}\n\n"   # guard against huge pages
            f"Return only the bullet points, no preamble."
        )

        response = llm.invoke(prompt)
        summary  = response.content if hasattr(response, "content") else str(response)
        summaries.append(f"**{title}**\n{summary}")

    return {
        **state,
        "summaries": summaries,
        "messages":  state["messages"] + [
            AIMessage(content=f"[SummarizerAgent] Produced {len(summaries)} summaries.")
        ],
    }