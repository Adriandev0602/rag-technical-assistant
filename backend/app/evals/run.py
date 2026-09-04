"""CLI del arnés de evaluación: corre golden.jsonl y reporta las cuatro métricas."""

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
    print(f"Golden set: {len(golden_set)} preguntas")
    raise NotImplementedError("arnés de evaluación pendiente de implementar")


if __name__ == "__main__":
    main()
