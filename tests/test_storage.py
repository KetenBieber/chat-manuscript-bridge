import pytest

from chat_manuscript_bridge.models import BridgeError
from chat_manuscript_bridge.storage import GitHubStorage, validate_prefix


@pytest.mark.parametrize("prefix", ["", "../escape", "a//b", "a/../b",
                                    "/root", "a/back\\slash"])
def test_invalid_prefix_rejected(prefix):
    with pytest.raises(BridgeError):
        validate_prefix(prefix)


def test_private_github_token_required():
    with pytest.raises(BridgeError):
        GitHubStorage("someone/private", "")


def test_transport_never_puts_token_in_url():
    backend = GitHubStorage("person/repo", "unrelated-secret", "main")
    assert backend._route("manuscripts/v1/jobs/test.json") == (
        "https://api.github.com/repos/person/repo/contents/manuscripts/v1/jobs/test.json"
    )
