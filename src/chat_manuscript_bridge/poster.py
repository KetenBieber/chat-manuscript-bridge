"""Markdown -> PDF -> GitHub poster images.

A separate, deterministic output workflow. This module never authors or
summarizes source Markdown, and never publishes it to Feishu.
"""
from __future__ import annotations

from tempfile import TemporaryDirectory
from io import BytesIO
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import posixpath
import re
import shutil
import socket
import subprocess
from urllib.parse import unquote, urlsplit
from urllib.request import (
    HTTPRedirectHandler, ProxyHandler, Request, build_opener,
)

from .models import BridgeError, canonical_json, sha256
from .storage import Storage, validate_prefix

IMAGE_MARKER = re.compile(r'!\[([^\]\n]*)\]\((<?[^)\s>]+>?)(?:\s+["\'][^"\']*["\'])?\)')
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_REMOTE_IMAGE = 8 * 1024 * 1024
MAX_IMAGES = 40
MAX_PAGES = 48
MAX_COMBINED_PIXELS = 65_000_000
MAX_LONG_HEIGHT = 45_000


def _safe_path(path: str, suffix: str | None = None) -> str:
    if not isinstance(path, str) or not path or path.startswith("/"):
        raise BridgeError("Provide a nonempty, repository-relative Markdown path")
    if "\x00" in path or "\\" in path or "//" in path:
        raise BridgeError("Invalid repository-relative path")
    normalized = posixpath.normpath(path)
    if normalized != path or any(x in ("", ".", "..") for x in path.split("/")):
        raise BridgeError("Repository-relative path may not traverse directories")
    if not re.fullmatch(r"[A-Za-z0-9._/-]{1,250}", path):
        raise BridgeError("Repository source paths allow ASCII filename characters only")
    if suffix and not path.lower().endswith(suffix):
        raise BridgeError("Source must be a .md file already stored in GitHub")
    return path


def _trusted_remote_image(url: str, hosts: set[str]) -> bytes:
    """Explicit allowlist + public DNS + no redirects.

    Operators must only allow trusted HTTPS hosts. This is not a general
    untrusted web crawler; DNS rebinding needs egress firewall protections
    if arbitrary domains can be allowlisted.
    """
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not hostname or hostname not in hosts:
        raise BridgeError("Remote Figure host is not in BRIDGE_POSTER_IMAGE_HOSTS")
    if parsed.username or parsed.password or parsed.fragment or parsed.port not in (None, 443):
        raise BridgeError("Remote Figure URL has unsupported credentials, port or fragment")
    try:
        ips = [ipaddress.ip_address(item[4][0])
               for item in socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)]
    except (socket.gaierror, ValueError, OSError) as exc:
        raise BridgeError("Cannot verify remote Figure hostname") from exc
    if not ips or not all(ip.is_global for ip in ips):
        raise BridgeError("Remote Figure resolves to a non-public IP")

    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise BridgeError("Remote Figure redirects are not allowed")

    opener = build_opener(ProxyHandler({}), NoRedirect())
    request = Request(url, headers={"User-Agent": "chat-manuscript-bridge-poster/0.2",
                                    "Accept": "image/png,image/jpeg,image/webp"})
    try:
        with opener.open(request, timeout=20) as res:
            if res.status != 200:
                raise BridgeError("Remote Figure was not available")
            data = res.read(MAX_REMOTE_IMAGE + 1)
    except BridgeError:
        raise
    except Exception as exc:
        raise BridgeError("Remote Figure download failed") from exc
    if not data or len(data) > MAX_REMOTE_IMAGE:
        raise BridgeError("Remote Figure exceeds allowed image size")
    return data


def _normalize_image(data: bytes) -> bytes:
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
        with Image.open(BytesIO(data)) as img:
            if img.format not in {"PNG", "JPEG", "WEBP"}:
                raise BridgeError("Only PNG, JPEG and WebP Figures are supported")
            if img.width * img.height > 24_000_000:
                raise BridgeError("Figure is too large to render safely")
            img.load()
            converted = ImageOps.exif_transpose(img).convert("RGB")
            output = BytesIO()
            converted.save(output, "PNG", optimize=True)
            return output.getvalue()
    except BridgeError:
        raise
    except Exception as exc:
        raise BridgeError("Figure is not a valid or safely renderable image") from exc


def _prepare_images(markdown: str, source_path: str, store: Storage,
                    folder: Path, hosts: set[str]) -> tuple[str, int]:
    """Replace Markdown image references with verified local PNG assets."""
    if re.search(r"<\s*(?:AsyncImage|img|iframe|script)\b", markdown, re.I):
        raise BridgeError("Unresolved HTML/AsyncImage element: provide normal Markdown Figure links")
    matches = list(IMAGE_MARKER.finditer(markdown))
    if len(matches) > MAX_IMAGES:
        raise BridgeError("Too many Figures in one poster")
    image_dir = folder / "images"
    image_dir.mkdir()
    replacement = markdown
    # Reverse replacement preserves original offsets in Markdown text.
    for i in reversed(range(len(matches))):
        match = matches[i]
        value = match.group(2).strip("<>")
        url = unquote(value)
        if url.startswith("https://"):
            raw = _trusted_remote_image(url, hosts)
        elif "://" in url or url.startswith(("data:", "/", "#")):
            raise BridgeError("Unsupported Figure URL protocol")
        else:
            base = posixpath.dirname(source_path)
            resolved = posixpath.normpath(posixpath.join(base, url))
            raw = store.read(_safe_path(resolved))
            if raw is None:
                raise BridgeError("Source Figure is missing from the GitHub repository")
        png = _normalize_image(raw)
        name = f"images/image-{i+1:03d}.png"
        (folder / name).write_bytes(png)
        replacement = replacement[:match.start()] + f"![{match.group(1)}]({name})" + replacement[match.end():]
    return replacement, len(matches)


def _render(markdown_bytes: bytes, source_path: str, store: Storage,
            *, dpi: int, font: str, allowed_hosts: set[str]) -> tuple[dict[str, bytes], dict]:
    if not 90 <= dpi <= 180:
        raise BridgeError("Poster DPI must be from 90 to 180")
    if not re.fullmatch(r"[\w -]{2,80}", font, re.UNICODE):
        raise BridgeError("Poster font must be a simple installed font family")
    if len(markdown_bytes) > MAX_INPUT_BYTES:
        raise BridgeError("Markdown source exceeds 2 MiB poster limit")
    try:
        text = markdown_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise BridgeError("Source Markdown must be valid UTF-8") from exc
    if not text.strip():
        raise BridgeError("Empty Markdown cannot produce a poster")
    if not shutil.which("pandoc") or not shutil.which("xelatex"):
        raise BridgeError("Poster rendering requires pandoc and XeLaTeX installed on the worker")
    try:
        import fitz
        from PIL import Image
    except ImportError as exc:
        raise BridgeError('Install poster dependencies: pip install "chat-manuscript-bridge[poster]"') from exc

    with TemporaryDirectory(prefix="cmb-poster-") as temp:
        tempdir = Path(temp)
        source, image_count = _prepare_images(text, source_path, store, tempdir, allowed_hosts)
        (tempdir / "source.md").write_text(source, encoding="utf-8")
        pdf_path = tempdir / "document.pdf"
        args = [
            "pandoc", "--sandbox", "--standalone",
            "--from=markdown+tex_math_dollars+tex_math_single_backslash-raw_tex-raw_html",
            "--pdf-engine=xelatex",
            "--variable", f"mainfont:{font}",
            "--variable", f"CJKmainfont:{font}",
            "--variable", "geometry:margin=22mm",
            "--variable", "colorlinks:true",
            "--variable", "linkcolor:blue",
            "--variable", "fontsize:11pt",
            "--variable", "linestretch:1.22",
            "--variable", "papersize:a4",
            "--resource-path", str(tempdir),
            "source.md", "--output", str(pdf_path),
        ]
        try:
            cp = subprocess.run(args, cwd=tempdir, capture_output=True,
                                text=True, timeout=180, check=False)
        except subprocess.TimeoutExpired as exc:
            raise BridgeError("Poster PDF compiler exceeded time limit") from exc
        if cp.returncode != 0 or not pdf_path.exists():
            # Report only a safely classified TeX error; never log private
            # source lines, file paths or the complete compiler transcript.
            output = cp.stderr or ""
            diagnosis = "unclassified"
            if re.search(r"(?i)fontspec error|font .* cannot be found|font .* not found", output):
                diagnosis = "missing_font"
            elif re.search(r"(?i)LaTeX Error: File [^\\n]+ not found", output):
                diagnosis = "missing_latex_package"
            elif re.search(r"(?i)unable to load picture|cannot find image|no such file or directory", output):
                diagnosis = "missing_figure"
            elif re.search(r"(?i)Undefined control sequence", output):
                diagnosis = "unsupported_latex_command"
            elif re.search(r"(?i)Missing \$ inserted|Double subscript|Extra \\}", output):
                diagnosis = "malformed_math"
            elif re.search(r"(?i)not allowed in sandbox", output):
                diagnosis = "pandoc_sandbox_denied"
            elif "Error producing PDF." in output:
                diagnosis = "pdf_engine_error"
            # A bounded LaTeX-error header is safer and far more actionable
            # than complete Pandoc stderr (which can echo manuscript prose).
            header = re.search(r"(?m)^! ([^\\n]{1,140})", output)
            if header:
                candidate = re.sub(r"[^A-Za-z0-9 .,:()!_+\\-]", "", header.group(1))
                diagnosis += " (" + candidate[:95] + ")"
            raise BridgeError("Poster PDF compilation failed: " + diagnosis)
        pdf_bytes = pdf_path.read_bytes()
        if not pdf_bytes.startswith(b"%PDF") or len(pdf_bytes) > 20 * 1024 * 1024:
            raise BridgeError("Generated PDF is invalid or too large")
        results = {"document.pdf": pdf_bytes}
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            pages = document.page_count
            if not 1 <= pages <= MAX_PAGES:
                raise BridgeError("Poster has too many PDF pages")
            assembled = []
            total_pixels = 0
            height = 0
            max_width = 0
            for i, page in enumerate(document):
                pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72),
                                      alpha=False)
                png = pix.tobytes("png")
                results[f"page-{i+1:03d}.png"] = png
                width, page_height = pix.width, pix.height
                total_pixels += width * page_height
                max_width = max(max_width, width)
                height += page_height
                if total_pixels <= MAX_COMBINED_PIXELS and height <= MAX_LONG_HEIGHT:
                    assembled.append(Image.open(BytesIO(png)).convert("RGB"))
        long_poster = bool(assembled and len(assembled) == pages)
        if long_poster:
            output = Image.new("RGB", (max_width, height), "#ffffff")
            offset = 0
            for page in assembled:
                output.paste(page, (0, offset))
                offset += page.height
            buffer = BytesIO()
            output.save(buffer, format="PNG", optimize=True)
            results["poster-long.png"] = buffer.getvalue()
        manifest = {
            "schema_version": 1,
            "status": "rendered",
            "source_path": source_path,
            "source_sha256": sha256(markdown_bytes),
            "pages": pages,
            "figures": image_count,
            "dpi": dpi,
            "long_poster": long_poster,
            "files": sorted(results),
        }
        return results, manifest


def generate_document_poster(store: Storage, source_path: str,
                             output_dir: str | None = None, *, dpi: int = 140,
                             font: str = "Noto Serif CJK SC",
                             image_hosts: str = "") -> dict:
    """Create real PDF+PNG images and atomically save them in GitHub.

    source_path is an existing .md path in the configured GitHub data repo.
    The output is an independent folder in that SAME repo; the public source
    code repository never receives the user's paper or generated images.
    """
    source_path = _safe_path(source_path, ".md")
    stem = Path(source_path).stem
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", stem):
        raise BridgeError("Source basename must be a safe article ID")
    target = validate_prefix(output_dir or f"posters/{stem}")
    if target == source_path or target.startswith("src/") or target.startswith(".github/"):
        raise BridgeError("Choose a dedicated GitHub output folder")
    original = store.read(source_path)
    if original is None:
        raise BridgeError("Markdown source does not exist in the configured GitHub repository")
    hosts = {h.strip().lower() for h in image_hosts.split(",") if h.strip()}
    if any(not re.fullmatch(r"[a-z0-9.-]{3,253}", h) or h.startswith(".")
           or h.endswith(".") for h in hosts):
        raise BridgeError("Invalid remote Figure host allowlist")
    files, metadata = _render(original, source_path, store, dpi=dpi, font=font,
                              allowed_hosts=hosts)
    metadata["output_dir"] = target
    files["manifest.json"] = canonical_json(metadata)
    payload = {f"{target}/{name}": value for name, value in files.items()}
    if not hasattr(store, "commit_files"):
        raise BridgeError("Storage backend does not support atomic GitHub binary artifacts")
    result = store.commit_files(payload, "poster: render " + stem)
    return {
        "status": "generated",
        "source_path": source_path,
        "output_dir": target,
        "pages": metadata["pages"],
        "figures": metadata["figures"],
        "long_poster": metadata["long_poster"],
        "files": sorted(payload),
        "commit": result["commit"],
        "idempotent": result["idempotent"],
    }
