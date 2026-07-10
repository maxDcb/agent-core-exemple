from __future__ import annotations

import argparse

from poem_agent.app import run_cli


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a poem with agent-core.")
    parser.add_argument("prompt", help="User request for the poem.")
    parser.add_argument("--json", action="store_true", help="Return {'poem': '...'} validated by Pydantic.")
    args = parser.parse_args()
    return run_cli(args.prompt, json_mode=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
