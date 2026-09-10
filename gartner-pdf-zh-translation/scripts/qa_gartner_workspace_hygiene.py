#!/usr/bin/env python3
"""Check Gartner workspace directory hygiene without changing files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path, help="Gartner workstream directory")
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()
    root = args.root.resolve()
    violations: list[dict[str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if "_archive" in rel.parts:
            continue
        if path.name == ".DS_Store":
            violations.append({"path": str(rel), "reason": "macOS metadata in active tree"})
        if "work" in rel.parts and "pdf-zh" not in rel.parts:
            violations.append({"path": str(rel), "reason": "work directory outside pdf-zh"})
        if len(rel.parts) >= 2 and rel.parts[-2] == "pdf-zh" and path.suffix.lower() not in {".pdf", ".md"}:
            violations.append({"path": str(rel), "reason": "intermediate file in pdf-zh root"})
    report = {"root": str(root), "status": "pass" if not violations else "fail", "violations": violations}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if violations:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
