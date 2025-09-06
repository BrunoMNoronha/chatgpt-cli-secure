from __future__ import annotations

import argparse
from pathlib import Path

from update_strategies import FileStrategy, GitHubStrategy, UrlStrategy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update installer")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--from-github", action="store_true", help="Install from GitHub")
    group.add_argument("--from-url", type=str, help="Install from direct URL")
    group.add_argument("--from-file", type=str, help="Install from local file")
    parser.add_argument("hash", nargs="?", default=None, help="SHA256 hash for --from-file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.from_github:
        strategy = GitHubStrategy()
    elif args.from_url:
        strategy = UrlStrategy(args.from_url)
    else:
        strategy = FileStrategy(Path(args.from_file), args.hash)
    strategy.install()


if __name__ == "__main__":
    main()
