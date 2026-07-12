from __future__ import annotations

import argparse

from poem_agent.app import run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a poem with agent-core.")
    parser.add_argument("prompt", help="User request for the poem.")
    parser.add_argument("--json", action="store_true", help="Return {'poem': '...'} validated by Pydantic.")
    parser.add_argument("--show-usage", action="store_true", help="Print exact provider token usage after the poem.")
    args = parser.parse_args()
    return run_cli(args.prompt, json_mode=args.json, show_usage=args.show_usage)


if __name__ == "__main__":
    raise SystemExit(main())
