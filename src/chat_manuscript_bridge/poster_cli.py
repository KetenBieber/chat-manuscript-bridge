"""Standalone CLI entrypoint to export a GitHub Markdown document as PDF/PNG."""
from __future__ import annotations

import argparse
import json
import os

from .models import BridgeError
from .poster import generate_document_poster
from .storage import GitHubStorage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="chat-manuscript-poster",
        description="Convert an existing GitHub Markdown file to PDF and PNG posters.",
    )
    parser.add_argument("--source", required=True,
                        help="Repository-relative path to an existing .md file")
    parser.add_argument("--output", default=None,
                        help="Repository-relative output folder (default posters/<name>)")
    parser.add_argument("--dpi", type=int, default=140)
    parser.add_argument("--font", default="Noto Serif CJK SC")
    args = parser.parse_args(argv)
    try:
        store = GitHubStorage(
            repository=os.environ.get("BRIDGE_GITHUB_REPO", ""),
            token=os.environ.get("BRIDGE_GITHUB_TOKEN", ""),
            branch=os.environ.get("BRIDGE_GITHUB_BRANCH", "main"),
        )
        result = generate_document_poster(
            store, args.source, args.output, dpi=args.dpi, font=args.font,
            image_hosts=os.environ.get("BRIDGE_POSTER_IMAGE_HOSTS", ""),
        )
    except (BridgeError, OSError) as exc:
        parser.exit(2, "Poster export failed: " + str(exc) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
