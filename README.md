# ResearchPilot 🚀

ResearchPilot is an autonomous, multi-agent research pipeline built on **LangGraph** and the **Model Context Protocol (MCP)**. It transforms a single research query into a structured, deep-dive Markdown report by orchestrating specialized agents that handle everything from web search and PDF ingestion to gap analysis and automated citation extraction.

## 🏗 Architecture & Pipeline Flow

The system operates as a 6-node state machine where agents communicate through a shared, typed `ResearchState`.

```mermaid
graph LR
    search[Search Agent] --> pdf[PDF Agent]
    pdf --> sum[Summarizer]
    sum --> critic[Critic Agent]
    critic --> write[Writer Agent]
    write --> cite[Citation Agent]
    cite --> END((Report))
```

**Pipeline Sequence:**
1.  **search**: Fetches web/paper results via Brave Search.
2.  **pdf_fetch**: Detects PDF/arXiv links and extracts full-text content.
3.  **summarize**: Produces concise, multi-point summaries for every ingested source.
4.  **critique**: Performs literature gap analysis and identifies contradictions.
5.  **write**: Compiles findings into a professional Markdown report.
6.  **citations**: Automatically extracts DOIs and arXiv IDs to build a Bibliography.

---

## 🤖 Agent Breakdown

| Agent | Responsibility | Tooling Used |
| :--- | :--- | :--- |
| **Search Agent** | Discovers sources and populates the initial state. | MCP `web_search` |
| **PDF Agent** | Ingests full text from PDFs (arXiv, etc.) to replace snippets. | MCP `fetch_pdf` |
| **Summarizer** | Converts raw content into structured bullet points. | Configured LLM |
| **Critic Agent** | Identifies gaps, conflicts, and low-quality sources. | Configured LLM |
| **Writer Agent** | Generates the final structured Markdown report. | MCP `write_file` |
| **Citation Agent** | Appends a `## References` section using regex patterns. | MCP `extract_citations` |

---

## 🛠 MCP Tool Server

The project includes a custom MCP stdio server (`mcp_server/server.py`) exposing the following capabilities:

- `web_search(query)`: High-quality web search (Brave Search API or Dev Mock).
- `fetch_pdf(url)`: Robust text extraction from remote PDF URLs using `pypdf`.
- `extract_citations(text)`: Pattern matching for DOIs, arXiv IDs, and Author-Year citations.
- `write_file(path, content)`: Secure local filesystem persistence for generated reports.

---

## 🚀 Quickstart

### 1. Prerequisites
- Python 3.10+
- (Optional) `BRAVE_API_KEY` for real search results (defaults to Mock mode if missing).

### 2. Setup
```bash
git clone https://github.com/your-repo/ResearchPilot.git
cd ResearchPilot
pip install -r requirements.txt
```

### 3. Usage
```bash
# Basic run using local Ollama (default)
python graph.py --query "Latest advances in GNN-based traffic forecasting"

# Use OpenAI with a custom output path
python graph.py --query "Self-supervised learning in robotics" --provider openai --output reports/robotics.md
```

---

## ⚙️ Configuration

| Flag | Env Var | Options | Description |
| :--- | :--- | :--- | :--- |
| `--query` | - | *String* | **Required.** The research question. |
| `--provider`| `LLM_PROVIDER` | `ollama`, `openai`, `anthropic` | LLM backend (Default: `ollama`). |
| `--output` | - | *Path* | Output file path (Default: `output/report.md`). |

---

## 📂 Project Layout

```text
H:\Random projects\ResearchPilot\
├── agents/             # Agent node implementations
├── mcp_server/         # MCP Tool Server (Python SDK)
├── tools/              # LLM Factory & MCP Client Wrapper
├── tests/              # 21 unit/integration test cases
├── output/             # Generated research reports
├── graph.py            # LangGraph definition & CLI entrypoint
└── requirements.txt    # Project dependencies
```

---

## 🧪 Testing

The project maintains high reliability through a comprehensive test suite of **21 pytest cases**. These tests mock all external MCP and LLM calls to validate agent logic, state transitions, and error recovery.

```bash
# Ensure PYTHONPATH includes root
$env:PYTHONPATH="."
pytest tests/
```

---

## 📄 License
MIT
