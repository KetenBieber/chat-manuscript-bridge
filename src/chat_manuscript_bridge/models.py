"""Source hashing, schema validation and safe immutable record encoding."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import re
from urllib.parse import urlsplit

MAX_MANUSCRIPT_BYTES = 1024 * 1024
ARTICLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$")
CATEGORY = re.compile(r"^[^\x00-\x1f\x7f]{1,80}$")
DESTINATION = re.compile(r"^[A-Za-z0-9._/-]{1,160}$")
MAP_KEY = re.compile(r"^(async:|async-ref:|async-src:).{1,512}$")


class BridgeError(RuntimeError):
    """User-visible safe error, never includes credentials or article bodies."""


class Conflict(BridgeError):
    """A supposedly immutable identifier already points to different bytes."""


def validate_article_id(value: str) -> str:
    if not isinstance(value, str) or not ARTICLE_ID.fullmatch(value):
        raise BridgeError("article_id must be 1-80 ASCII letters, digits, - or _")
    return value


def validate_category(value: str) -> str:
    if not isinstance(value, str) or not CATEGORY.fullmatch(value) or not value.strip():
        raise BridgeError("category must be a nonempty printable string of at most 80 characters")
    return value


def validate_destination(value: str) -> str:
    if not isinstance(value, str) or not DESTINATION.fullmatch(value) or ".." in value.split("/"):
        raise BridgeError("destination must be a nonempty logical identifier, not a secret or URL")
    return value


def manuscript_bytes(markdown: str) -> bytes:
    if not isinstance(markdown, str) or "\x00" in markdown:
        raise BridgeError("markdown must be UTF-8 text without NUL characters")
    data = markdown.encode("utf-8")
    if not data.strip() or len(data) > MAX_MANUSCRIPT_BYTES:
        raise BridgeError("markdown must contain 1 to 1048576 UTF-8 bytes")
    return data  # No normalization, trimming or reconstruction.


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_json(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def decode_record(raw: bytes, kind: str) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise BridgeError("Corrupted " + kind + " record") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise BridgeError("Unsupported " + kind + " record schema")
    return value


def validate_image_sources(value: dict[str, str] | None) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict) or len(value) > 100:
        raise BridgeError("image_sources must be a mapping with at most 100 entries")
    out = {}
    for key, url in value.items():
        if not isinstance(key, str) or not MAP_KEY.fullmatch(key):
            raise BridgeError("Figure map keys must use async:, async-ref: or async-src:")
        if not isinstance(url, str) or len(url) > 2048:
            raise BridgeError("Invalid Figure source URL")
        parsed = urlsplit(url)
        hostname = parsed.hostname or ""
        if (parsed.scheme != "https" or not hostname or parsed.username is not None
                or parsed.password is not None or parsed.fragment):
            raise BridgeError("Figure source URLs must be absolute HTTPS URLs without credentials/fragments")
        if hostname.lower() in ("localhost", "localhost.localdomain") or hostname.lower().endswith(".local"):
            raise BridgeError("Local Figure source URL denied")
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise BridgeError("Non-public Figure IP denied")
        out[key] = url
    return dict(sorted(out.items()))
