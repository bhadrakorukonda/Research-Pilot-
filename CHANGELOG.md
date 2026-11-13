# Changelog

## [Unreleased]

### Fixed
- `graph.py` no longer fails to load (stray duplicated text caused a SyntaxError).
- MCP server starts correctly over stdio; tool calls no longer fail with "Connection closed".
- `BRAVE_API_KEY` and other env vars are forwarded to the MCP server, so real search works.
- MCP server is launched with the current Python interpreter (`sys.executable`).
- Reports are written to the path given by `--output` (previously nested as `output/output/...`).
- `fetch_pdf` follows redirects (arXiv) and refuses downloads over 20 MB.
- Author-Year citation pattern is case-sensitive and no longer matches ordinary words.

- CLI no longer crashes at the end on Windows consoles (non-ASCII character in final message).
- Search warns clearly when it falls back to MOCK results (no `BRAVE_API_KEY`).

### Security
- `write_file` rejects paths that resolve outside the project directory.

### Changed
- References section now lists every source (title + URL) and citations found in the full
  source text, not just the summaries.
- Default Anthropic model is `claude-sonnet-5-5`.
- `.env` is loaded automatically; `.env.example` documents all settings.
- `pdf_agent` no longer mutates the sources it receives.
- Line endings normalised to LF; compiled `.pyc` files removed from version control.
