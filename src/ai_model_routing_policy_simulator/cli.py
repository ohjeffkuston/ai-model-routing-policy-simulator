"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import evaluate_route


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate a governed AI model-routing decision")
    parser.add_argument("--input", required=True, type=Path, help="JSON file with policy and request")
    parser.add_argument("--output", type=Path, help="Optional JSON output file")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    result = evaluate_route(payload["policy"], payload["request"])
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0
