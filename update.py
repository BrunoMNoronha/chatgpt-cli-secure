from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable, Dict

from update_strategies import (
    FileStrategy,
    GitHubStrategy,
    UpdateStrategy,
    URLStrategy,
)


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
    factories: Dict[str, Callable[[argparse.Namespace], UpdateStrategy]] = {
        # Mapping flags to their concrete strategies avoids long if/elif chains
        # and performs dispatch in O(1) time.
        "from_github": lambda a: GitHubStrategy(),
        "from_url": lambda a: URLStrategy(a.from_url),
        "from_file": lambda a: FileStrategy(Path(a.from_file), a.hash),
    }
    key = next(k for k in factories if getattr(args, k))
    strategy = factories[key](args)
    strategy.run()


if __name__ == "__main__":
    main()
