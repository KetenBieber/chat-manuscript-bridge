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

    def _request(self, method: str, url: str, body: dict | None = None,
                 max_response_bytes: int = 3 * 1024 * 1024) -> object:
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
                payload = response.read(max_response_bytes + 1)
            if len(payload) > max_response_bytes:
                raise BridgeError("GitHub response exceeds safe size limit")
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
        if not isinstance(obj, dict) or obj.get("type") != "file":
            raise BridgeError("GitHub path is not an ordinary file")
        blob_sha = obj.get("sha")
        if not isinstance(blob_sha, str) or len(blob_sha) != 40:
            raise BridgeError("GitHub file has no verified Git Blob SHA")
        if obj.get("encoding") == "base64":
            encoded = obj.get("content")
        elif obj.get("encoding") == "none":
            # GitHub Contents API returns metadata only for larger images.
            # Read that exact blob instead of silently losing Figure assets.
            url = "https://api.github.com/repos/" + self.repository + "/git/blobs/" + blob_sha
            blob = self._request("GET", url, max_response_bytes=15 * 1024 * 1024)
            if (not isinstance(blob, dict) or blob.get("sha") != blob_sha
                    or blob.get("encoding") != "base64"):
                raise BridgeError("GitHub large binary blob unavailable")
            encoded = blob.get("content")
        else:
            raise BridgeError("GitHub file uses unsupported encoding")
        if not isinstance(encoded, str):
            raise BridgeError("GitHub file has no decodable content")
        try:
            raw = base64.b64decode(encoded, validate=False)
        except (ValueError, TypeError) as exc:
            raise BridgeError("Invalid GitHub base64 content") from exc
        if len(raw) > 8 * 1024 * 1024 or git_blob_sha(raw) != blob_sha:
            raise BridgeError("GitHub file SHA verification or image size failed")
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


    def commit_files(self, files: dict[str, bytes], message: str) -> dict:
        """Atomically add a set of PDF/PNG artifacts using the Git Data API.

        Every file is create-only. Existing files with identical Git Blob SHAs
        are idempotent; differing bytes abort the whole operation. A branch
        fast-forward race is retried from the latest tree, never force-pushed.
        """
        if not isinstance(files, dict) or not 1 <= len(files) <= 60:
            raise BridgeError("Poster must contain between 1 and 60 output files")
        if not isinstance(message, str) or len(message) > 180:
            raise BridgeError("Invalid GitHub commit message")
        total_size = 0
        expected = {}
        for path, data in files.items():
            self._route(path)  # Validate each destination against traversal.
            if not isinstance(data, bytes) or not 1 <= len(data) <= 25 * 1024 * 1024:
                raise BridgeError("Poster output artifact size must be 1 byte to 25 MiB")
            expected[path] = git_blob_sha(data)
            total_size += len(data)
        if total_size > 55 * 1024 * 1024:
            raise BridgeError("Poster output directory exceeds 55 MiB")
        base = "https://api.github.com/repos/" + self.repository + "/git/"
        refurl = base + "refs/heads/" + urllib.parse.quote(self.branch, safe="/")
        for _ in range(3):
            ref = self._request("GET", base + "ref/heads/" +
                                urllib.parse.quote(self.branch, safe="/"))
            if not isinstance(ref, dict) or not isinstance(ref.get("object"), dict):
                raise BridgeError("GitHub branch reference unavailable")
            head_sha = ref["object"]["sha"]
            old_commit = self._request("GET", base + "commits/" + head_sha)
            tree_sha = old_commit["tree"]["sha"]
            tree = self._request("GET", base + "trees/" + tree_sha + "?recursive=1")
            if not isinstance(tree, dict) or tree.get("truncated"):
                raise BridgeError("GitHub repository tree listing is incomplete")
            existing = {node["path"]: node["sha"] for node in tree.get("tree", [])
                        if node.get("type") == "blob"}
            for path, wanted in expected.items():
                if path in existing and existing[path] != wanted:
                    raise Conflict("Existing poster file has different content: " + path)
            missing = [path for path in expected if path not in existing]
            if not missing:
                return {"commit": head_sha, "idempotent": True}
            entries = []
            for path in missing:
                obj = self._request("POST", base + "blobs", {
                    "content": base64.b64encode(files[path]).decode("ascii"),
                    "encoding": "base64",
                })
                if not isinstance(obj, dict) or obj.get("sha") != expected[path]:
                    raise BridgeError("GitHub binary blob readback SHA mismatch")
                entries.append({"path": path, "mode": "100644", "type": "blob",
                                "sha": expected[path]})
            created_tree = self._request("POST", base + "trees",
                                        {"base_tree": tree_sha, "tree": entries})
            commit = self._request("POST", base + "commits", {
                "message": message, "tree": created_tree["sha"],
                "parents": [head_sha],
            })
            try:
                self._request("PATCH", refurl, {"sha": commit["sha"], "force": False})
            except (Conflict, BridgeError):
                # A concurrent branch update or transport timeout may have
                # succeeded. Re-read everything and never force push.
                continue
            check = self._request("GET", base + "trees/" + created_tree["sha"] + "?recursive=1")
            if (not isinstance(check, dict) or check.get("truncated") or
                    any(next((node.get("sha") for node in check.get("tree", [])
                              if node.get("path") == path and node.get("type") == "blob"),
                             None) != wanted for path, wanted in expected.items())):
                raise BridgeError("Poster was committed but artifact verification failed")
            return {"commit": commit["sha"], "idempotent": False}
        raise BridgeError("Concurrent GitHub updates prevented a verified poster commit")
