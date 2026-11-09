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
6.  **citations**: Appends a `## References` section: every source (title + URL) plus DOIs, arXiv IDs and Author-Year citations found in the full source text.

---

## 🤖 Agent Breakdown

| Agent | Responsibility | Tooling Used |
| :--- | :--- | :--- |
| **Search Agent** | Discovers sources and populates the initial state. | MCP `web_search` |
| **PDF Agent** | Ingests full text from PDFs (arXiv, etc.) to replace snippets. | MCP `fetch_pdf` |
| **Summarizer** | Converts raw content into structured bullet points. | Configured LLM |
| **Critic Agent** | Identifies gaps, conflicts, and low-quality sources. | Configured LLM |
| **Writer Agent** | Generates the final structured Markdown report. | MCP `write_file` |
| **Citation Agent** | Appends a `## References` section (sources + extracted citations). | MCP `extract_citations`, `write_file` |

---

## 🛠 MCP Tool Server

The project includes a custom MCP stdio server (`mcp_server/server.py`) exposing the following capabilities:

- `web_search(query)`: High-quality web search (Brave Search API or Dev Mock).
- `fetch_pdf(url)`: Text extraction from remote PDF URLs using `pypdf` (follows redirects, refuses files over 20 MB).
- `extract_citations(text)`: Pattern matching for DOIs, arXiv IDs, and Author-Year citations.
- `write_file(path, content)`: Writes to `path` (relative to the project root). Paths resolving outside the project are rejected.

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
cp .env.example .env   # optional: provider, model and API keys
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
| `--output` | - | *Path* | Report path relative to the project root (Default: `output/report.md`). |

Other settings (`OLLAMA_MODEL`, `ANTHROPIC_MODEL`, `OPENAI_MODEL`, API keys, `BRAVE_API_KEY`) are read from the environment or a `.env` file; see `.env.example`. The default Anthropic model is `claude-sonnet-5-5`.

---

## 📂 Project Layout

```text
ResearchPilot/
├── agents/             # Agent node implementations
├── mcp_server/         # MCP Tool Server (Python SDK)
├── tools/              # LLM Factory & MCP Client Wrapper
├── tests/              # 35 unit/integration test cases
├── output/             # Generated research reports (git-ignored)
├── graph.py            # LangGraph definition & CLI entrypoint
└── requirements.txt    # Project dependencies
```

---

## 🧪 Testing

The project maintains high reliability through a suite of **35 pytest cases**. Agent tests mock the LLM and MCP calls; `test_mcp_server.py` and `test_mcp_integration.py` exercise the real MCP server and client.

```bash
python -m pytest tests/
```

---

## 📄 License
MIT
