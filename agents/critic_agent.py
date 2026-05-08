"""
Critic Agent
------------
Reviews all summaries, identifies contradictions, gaps, and unanswered questions.
Writes a structured critique into state["critique"].
"""

from langchain_core.messages import AIMessage
from tools.llm import get_llm


def critic_agent(state: dict) -> dict:
    llm       = get_llm()
    query     = state["query"]
    summaries = state["summaries"]

    print("[CriticAgent] Analysing summaries for gaps and contradictions...")

    combined = "\n\n---\n\n".join(summaries)

    prompt = (
        f"You are a critical research reviewer.\n"
        f"Original query: {query}\n\n"
        f"Here are summaries of {len(summaries)} sources:\n\n"
        f"{combined}\n\n"
        f"Identify:\n"
        f"1. Key contradictions or conflicting claims across sources\n"
        f"2. Important gaps — what is NOT covered that the query needs?\n"
        f"3. Any low-quality or irrelevant sources to discount\n\n"
        f"Be concise and structured. Use numbered lists."
    )

    response = llm.invoke(prompt)
    critique = response.content if hasattr(response, "content") else str(response)

    return {
        **state,
        "critique": critique,
        "messages": state["messages"] + [
            AIMessage(content="[CriticAgent] Critique complete.")
        ],
    }