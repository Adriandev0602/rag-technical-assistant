"""Evaluation harness CLI: runs golden.jsonl and reports the four metrics."""

from __future__ import annotations

import json
from pathlib import Path

GOLDEN_PATH = Path(__file__).parent / "golden.jsonl"


def load_golden_set(path: Path = GOLDEN_PATH) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    golden_set = load_golden_set()
    print(f"Golden set: {len(golden_set)} questions")
    raise NotImplementedError("evaluation harness not implemented yet")


if __name__ == "__main__":
    main()
