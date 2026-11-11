"""Small, private GitHub Contents API backend with byte-for-byte readback."""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Protocol

from .models import BridgeError, Conflict, git_blob_sha

PATH_SEGMENT = re.compile(r"^[A-Za-z0-9._-]+$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
BRANCH = re.compile(r"^[A-Za-z0-9._/-]{1,120}$")


def validate_prefix(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 180:
        raise BridgeError("Storage prefix must be nonempty and at most 180 characters")
    if any(not PATH_SEGMENT.fullmatch(p) or p in (".", "..") for p in value.split("/")):
        raise BridgeError("Storage prefix must consist of safe repository path components")
    return value


class Storage(Protocol):
    def read(self, path: str) -> bytes | None: ...
    def create(self, path: str, data: bytes) -> str: ...
    def list_names(self, directory: str) -> list[str]: ...


class GitHubStorage:
    """No public repository is required: supports a separate private data repository.

    The access token is used only for requests to the pinned GitHub REST host.
    Writes are create-only; conflicts are checked by reading the existing SHA.
    """

    def __init__(self, repository: str, token: str, branch: str = "main"):
        if not REPOSITORY.fullmatch(repository):
            raise BridgeError("Invalid GitHub owner/repository")
        if not token:
            raise BridgeError("BRIDGE_GITHUB_TOKEN is not configured")
        if not BRANCH.fullmatch(branch) or ".." in branch.split("/"):
            raise BridgeError("Invalid GitHub branch")
        self.repository, self.token, self.branch = repository, token, branch

    def _route(self, path: str) -> str:
        if not isinstance(path, str) or path.startswith("/") or any(
            not PATH_SEGMENT.fullmatch(p) or p in (".", "..") for p in path.split("/")
        ):
            raise BridgeError("Invalid private repository path")
        return "https://api.github.com/repos/" + self.repository + "/contents/" + urllib.parse.quote(path, safe="/")

    def _request(self, method: str, url: str, body: dict | None = None) -> object:
        raw = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(url, data=raw, method=method, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "chat-manuscript-bridge/0.1",
        })
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read(3 * 1024 * 1024)
            return json.loads(payload.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code in (409, 422):
                raise Conflict("GitHub create conflict") from exc
            raise BridgeError("GitHub HTTP " + str(exc.code)) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise BridgeError("GitHub API transport failure (write outcome may be uncertain)") from exc
        except (ValueError, UnicodeError) as exc:
            raise BridgeError("GitHub returned invalid JSON") from exc

    def read(self, path: str) -> bytes | None:
        url = self._route(path) + "?ref=" + urllib.parse.quote(self.branch, safe="")
        obj = self._request("GET", url)
        if obj is None:
            return None
        if not isinstance(obj, dict) or obj.get("type") != "file" or obj.get("encoding") != "base64":
            raise BridgeError("GitHub file is not a small base64-encoded blob")
        try:
            raw = base64.b64decode(obj["content"], validate=False)
        except (KeyError, ValueError, TypeError) as exc:
            raise BridgeError("Invalid GitHub file content") from exc
        if len(raw) > 2 * 1024 * 1024 or git_blob_sha(raw) != obj.get("sha"):
            raise BridgeError("GitHub file SHA verification failed")
        return raw

    def create(self, path: str, data: bytes) -> str:
        if not isinstance(data, bytes) or not data or len(data) > 2 * 1024 * 1024:
            raise BridgeError("Immutable record must be between 1 byte and 2 MiB")
        expected = git_blob_sha(data)
        existing = self.read(path)
        if existing is not None:
            if existing != data:
                raise Conflict("Immutable GitHub file already exists with different bytes")
            return expected
        request = {
            "message": "bridge: add immutable " + path.split("/")[-1],
            "content": base64.b64encode(data).decode("ascii"),
            "branch": self.branch,
        }
        try:
            self._request("PUT", self._route(path), request)
        except BridgeError:
            # Reconcile a timeout or race with a read. Never blindly re-PUT.
            existing = self.read(path)
            if existing != data:
                raise
        actual = self.read(path)
        if actual != data:
            raise BridgeError("GitHub create not verified; do not repeat the write blindly")
        return expected

    def list_names(self, directory: str) -> list[str]:
        url = self._route(directory) + "?ref=" + urllib.parse.quote(self.branch, safe="")
        obj = self._request("GET", url)
        if obj is None:
            return []
        if not isinstance(obj, list) or len(obj) >= 1000:
            raise BridgeError("GitHub directory listing too large; use a paginated index")
        return sorted(entry["name"] for entry in obj if isinstance(entry, dict) and entry.get("type") == "file")
