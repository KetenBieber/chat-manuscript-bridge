"""Atomic Git Data API regression tests for PDF/PNG publication."""
import base64
import hashlib

import pytest

from chat_manuscript_bridge.models import Conflict, git_blob_sha
from chat_manuscript_bridge.storage import GitHubStorage


class GitDataStub(GitHubStorage):
    def __init__(self):
        super().__init__("example/private-docs", "synthetic-test-token")
        self.head = "h0"
        self.trees = {"t0": {}}
        self.commits = {"h0": {"tree": {"sha": "t0"}}}
        self.blobs = {}
        self.calls = []
        self.seq = 0

    def _request(self, method, url, body=None, max_response_bytes=3145728):
        self.calls.append((method, url, body))
        if method == "GET" and "/git/ref/heads/" in url:
            return {"object": {"sha": self.head}}
        if method == "GET" and "/git/commits/" in url:
            return self.commits[url.rsplit("/", 1)[-1]]
        if method == "GET" and "/git/trees/" in url:
            sha = url.split("/git/trees/")[1].split("?")[0]
            return {
                "truncated": False,
                "tree": [{"path": path, "type": "blob", "sha": blob}
                         for path, blob in self.trees[sha].items()],
            }
        if method == "POST" and url.endswith("/git/blobs"):
            content = base64.b64decode(body["content"])
            sha = git_blob_sha(content)
            self.blobs[sha] = content
            return {"sha": sha}
        if method == "POST" and url.endswith("/git/trees"):
            self.seq += 1
            sha = "t" + str(self.seq)
            files = dict(self.trees[body["base_tree"]])
            for entry in body["tree"]:
                files[entry["path"]] = entry["sha"]
            self.trees[sha] = files
            return {"sha": sha}
        if method == "POST" and url.endswith("/git/commits"):
            sha = "h" + str(self.seq)
            self.commits[sha] = {"tree": {"sha": body["tree"]}}
            return {"sha": sha}
        if method == "PATCH" and "/git/refs/heads/" in url:
            assert body["force"] is False
            self.head = body["sha"]
            return {"ref": "refs/heads/main"}
        raise AssertionError("Unexpected GitHub API call " + method + " " + url)


def test_atomic_two_binary_outputs_and_idempotency():
    store = GitDataStub()
    files = {
        "posters/example/document.pdf": b"%PDF-demo",
        "posters/example/page-001.png": b"\x89PNG-demo",
    }
    one = store.commit_files(files, "poster: example")
    assert one == {"commit": "h1", "idempotent": False}
    assert store.trees["t1"] == {k: git_blob_sha(v) for k, v in files.items()}
    two = store.commit_files(files, "poster: example")
    assert two == {"commit": "h1", "idempotent": True}
    assert len([x for x in store.calls if x[0] == "POST" and x[1].endswith("/git/commits")]) == 1


def test_existing_different_poster_is_never_overwritten():
    store = GitDataStub()
    store.commit_files({"posters/x/document.pdf": b"first"}, "first poster")
    with pytest.raises(Conflict, match="different content"):
        store.commit_files({"posters/x/document.pdf": b"changed"}, "unsafe rewrite")
    assert store.blobs[store.trees["t1"]["posters/x/document.pdf"]] == b"first"


def test_path_traversal_denied_before_any_github_write():
    store = GitDataStub()
    with pytest.raises(Exception):
        store.commit_files({"posters/../escape.pdf": b"nope"}, "unsafe path")
    assert not store.calls
