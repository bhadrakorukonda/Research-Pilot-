"""Direct tests for the MCP server tool handlers (no subprocess)."""

import asyncio
import json
from io import BytesIO

import httpx
import pytest
from pypdf import PdfWriter

from mcp_server import server


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def project_root(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    monkeypatch.setattr(server, "PROJECT_ROOT", root)
    return root


def test_write_file_writes_exact_relative_path(project_root):
    out = _run(server._write_file({"path": "output/report.md", "content": "hi"}))
    assert json.loads(out[0].text)["status"] == "ok"
    assert (project_root / "output" / "report.md").read_text(encoding="utf-8") == "hi"
    assert not (project_root / "output" / "output").exists()


@pytest.mark.parametrize("bad", ["../escape.md", "a/../../escape.md"])
def test_write_file_rejects_parent_traversal(project_root, bad):
    with pytest.raises(ValueError, match="escapes"):
        _run(server._write_file({"path": bad, "content": "x"}))


def test_write_file_rejects_absolute_path_outside_root(project_root, tmp_path_factory):
    outside = tmp_path_factory.mktemp("elsewhere") / "x.md"
    with pytest.raises(ValueError, match="escapes"):
        _run(server._write_file({"path": str(outside), "content": "x"}))
    assert not outside.exists()


def _pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _patch_http(monkeypatch, handler):
    real = httpx.AsyncClient
    monkeypatch.setattr(
        server.httpx,
        "AsyncClient",
        lambda **kw: real(transport=httpx.MockTransport(handler), **kw),
    )


def test_fetch_pdf_follows_redirects(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/pdf/1":
            return httpx.Response(302, headers={"location": "https://x.test/final.pdf"})
        return httpx.Response(200, content=_pdf_bytes())

    _patch_http(monkeypatch, handler)
    out = _run(server._fetch_pdf({"url": "https://x.test/pdf/1"}))
    assert json.loads(out[0].text)["url"] == "https://x.test/pdf/1"


def test_fetch_pdf_rejects_oversized_download(monkeypatch):
    monkeypatch.setattr(server, "MAX_PDF_BYTES", 100)
    _patch_http(monkeypatch, lambda request: httpx.Response(200, content=b"0" * 500))
    with pytest.raises(ValueError, match="exceeds"):
        _run(server._fetch_pdf({"url": "https://x.test/big.pdf"}))
