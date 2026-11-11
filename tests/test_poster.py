"""Poster outputs are a separate workflow, never a disguised Feishu upload."""
from io import BytesIO
from pathlib import Path

import pytest

from chat_manuscript_bridge.models import BridgeError
from chat_manuscript_bridge.poster import (
    _safe_path, _prepare_images, _normalize_image, generate_document_poster
)


class Storage:
    def __init__(self):
        self.files = {"manuscripts/v1/originals/example.md": b"# Synthetic\n\nHello world.\n"}
        self.commits = []

    def read(self, path):
        return self.files.get(path)

    def commit_files(self, files, message):
        for path, data in files.items():
            if path in self.files and self.files[path] != data:
                raise BridgeError("already exists")
        identical = all(self.files.get(p) == v for p, v in files.items())
        self.files.update(files)
        self.commits.append(message)
        return {"commit": "example-commit", "idempotent": identical}


@pytest.mark.parametrize("bad", ["../escaped.md", "/absolute.md", "a//b.md",
                                  "x\\y.md", "a/../../c.md", "story.txt"])
def test_source_path_rejects_unsafe_or_non_markdown_names(bad):
    with pytest.raises(BridgeError):
        _safe_path(bad, ".md")


def test_rendered_files_returned_in_github_folder(monkeypatch):
    source = Storage()

    def fake_render(data, path, store, *, dpi, font, allowed_hosts):
        assert data == source.files[path]
        assert font == "Noto Serif CJK SC"
        return ({
            "document.pdf": b"%PDF-synthetic",
            "page-001.png": b"\x89PNG\r\nsynthetic",
            "poster-long.png": b"\x89PNG\r\nsynthetic",
        }, {
            "schema_version": 1,
            "status": "rendered",
            "source_path": path,
            "source_sha256": "synthetic-sha",
            "pages": 1, "figures": 0, "dpi": dpi, "long_poster": True,
            "files": ["document.pdf", "page-001.png", "poster-long.png"],
        })

    monkeypatch.setattr("chat_manuscript_bridge.poster._render", fake_render)
    first = generate_document_poster(
        source, "manuscripts/v1/originals/example.md", "posters/example")
    assert first["status"] == "generated"
    assert first["pages"] == 1
    assert first["long_poster"] is True
    assert set(first["files"]) == {
        "posters/example/document.pdf",
        "posters/example/page-001.png",
        "posters/example/poster-long.png",
        "posters/example/manifest.json",
    }
    assert source.files["posters/example/document.pdf"].startswith(b"%PDF")
    again = generate_document_poster(
        source, "manuscripts/v1/originals/example.md", "posters/example")
    assert again["idempotent"]


def test_missing_source_fails_without_github_write():
    source = Storage()
    with pytest.raises(BridgeError, match="does not exist"):
        generate_document_poster(source, "other.md")
    assert source.commits == []


def test_remote_image_requires_allowlist(tmp_path):
    source = Storage()
    with pytest.raises(BridgeError, match="allowlist|not in"):
        _prepare_images("![a](https://example.org/a.png)", "a.md",
                        source, tmp_path, set())


def test_unresolved_async_image_must_not_silently_disappear(tmp_path):
    source = Storage()
    with pytest.raises(BridgeError, match="Unresolved"):
        _prepare_images('<AsyncImage query="a figure"/>', "a.md", source, tmp_path, set())


def test_relative_image_is_embedded_and_normalized(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    source = Storage()
    buf = BytesIO()
    Image.new("RGB", (30, 20), (240, 60, 60)).save(buf, format="PNG")
    source.files["manuscripts/v1/originals/figure.png"] = buf.getvalue()
    processed, count = _prepare_images(
        "![Figure 1](figure.png)", "manuscripts/v1/originals/example.md",
        source, tmp_path, set())
    assert count == 1
    assert "images/image-001.png" in processed
    assert (tmp_path / "images" / "image-001.png").read_bytes().startswith(b"\x89PNG")


def test_invalid_poster_font_or_dpi_fails_closed(monkeypatch):
    source = Storage()
    with pytest.raises(BridgeError):
        generate_document_poster(source, "manuscripts/v1/originals/example.md",
                                 font=r"\input{/etc/passwd}")
    with pytest.raises(BridgeError):
        generate_document_poster(source, "manuscripts/v1/originals/example.md", dpi=300)
