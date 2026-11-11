import pytest

from chat_manuscript_bridge.models import (
    BridgeError, git_blob_sha, manuscript_bytes, sha256, validate_article_id,
    validate_image_sources,
)


def test_hashes_match_github_blob_semantics():
    raw = "你好，robot!\n".encode("utf-8")
    assert git_blob_sha(raw) == __import__("hashlib").sha1(
        b"blob " + str(len(raw)).encode() + b"\0" + raw
    ).hexdigest()
    assert len(sha256(raw)) == 64


def test_zero_transform_and_invalid_source():
    text = "\n# 标题\nA  B  \n"
    assert manuscript_bytes(text).decode("utf-8") == text
    for bad in ("", "  ", "\0bad"):
        with pytest.raises(BridgeError):
            manuscript_bytes(bad)


@pytest.mark.parametrize("bad", ["../bad", "X/Y", "", "空白", "b" * 81])
def test_bad_article_identifiers(bad):
    with pytest.raises(BridgeError):
        validate_article_id(bad)


def test_image_map_validates_https_and_blocks_private_ips():
    value = {"async:official figure 1": "https://example.org/paper/figure1.png"}
    assert validate_image_sources(value) == value
    for url in ["http://example.org/a.png", "https://localhost/a",
                "https://127.0.0.1/a", "https://192.168.0.8/a",
                "https://user:pass@example.org/a.png"]:
        with pytest.raises(BridgeError):
            validate_image_sources({"async:figure": url})
