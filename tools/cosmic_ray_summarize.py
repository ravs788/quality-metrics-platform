#!/usr/bin/env python3
"""Summarize Cosmic Ray dump output.

Cosmic Ray's `dump` output may be JSONL (one JSON document per line). This script:
- counts outcomes (killed/survived/incompetent/timeout/etc.)
- writes a human-readable summary
- extracts a small list of surviving mutants (if present in dump)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DUMP_PATH = Path("cosmic-ray-report.json")
SUMMARY_PATH = Path("cosmic-ray-summary.txt")
SURVIVORS_PATH = Path("cosmic-ray-survivors.json")


def _iter_jsonl(path: Path) -> list[Any]:
    raw = path.read_text()
    docs: list[Any] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        docs.append(json.loads(line))
    return docs


def _collect_items(docs: list[Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for obj in docs:
        if isinstance(obj, list):
            for x in obj:
                if isinstance(x, dict):
                    items.append(x)
        elif isinstance(obj, dict):
            # Some versions nest under known keys
            for k in ("mutants", "work_items", "results", "outcomes"):
                v = obj.get(k)
                if isinstance(v, list):
                    for x in v:
                        if isinstance(x, dict):
                            items.append(x)
                    break
            else:
                items.append(obj)
    return items


def _status(item: dict[str, Any]) -> str:
    return (
        item.get("test_outcome")
        or item.get("outcome")
        or item.get("status")
        or item.get("result")
        or "unknown"
    )


def main() -> None:
    if not DUMP_PATH.exists():
        raise SystemExit(f"Missing {DUMP_PATH} (run cosmic-ray dump first)")

    docs = _iter_jsonl(DUMP_PATH)
    items = _collect_items(docs)

    counts: dict[str, int] = {}
    survivors: list[dict[str, Any]] = []

    for it in items:
        st = _status(it)
        counts[st] = counts.get(st, 0) + 1

        if st == "survived":
            # Keep only useful keys to avoid huge output
            muts = it.get("mutations")
            if isinstance(muts, list) and muts and isinstance(muts[0], dict):
                module_path = muts[0].get("module_path")
                operator = muts[0].get("operator_name")
            else:
                module_path = it.get("module_path")
                operator = it.get("operator_name") or it.get("operator")

            survivors.append(
                {
                    "job_id": it.get("job_id"),
                    "module_path": module_path,
                    "operator": operator,
                    "diff": it.get("diff"),
                }
            )

    total = sum(counts.values())
    lines = [f"Total items parsed: {total}", "", "By outcome:"]
    for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append(f"Survivors captured: {len(survivors)} (see {SURVIVORS_PATH})")
    out = "\n".join(lines) + "\n"

    SUMMARY_PATH.write_text(out)
    SURVIVORS_PATH.write_text(json.dumps(survivors, indent=2))

    print(out)


if __name__ == "__main__":
    main()
