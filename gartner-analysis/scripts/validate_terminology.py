#!/usr/bin/env python3
"""Validate that active Gartner Skill resources use shared terminology."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ACTIVE_FILES = (
    "gartner-analysis/references/analysis-translation-content-protocol.md",
    "gartner-analysis/references/analysis-hc-mq-protocol.md",
    "gartner-pdf-zh-translation/references/term-policy.md",
    "gartner-structured-presentation/references/presentation-contract.md",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills-root",
        type=Path,
        default=Path("/Users/luantu/.agents/skills"),
    )
    args = parser.parse_args()
    root = args.skills_root.expanduser().resolve()
    data_path = root / "gartner-analysis" / "references" / "analysis-terminology.json"
    if not data_path.is_file():
        print(f"FAIL: missing shared terminology file: {data_path}")
        return 1
    data = json.loads(data_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for relative_path in ACTIVE_FILES:
        path = root / relative_path
        if not path.is_file():
            errors.append(f"missing active file: {relative_path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for variant in data["forbidden_variants"]:
            if variant in text:
                errors.append(f"{relative_path} contains forbidden variant: {variant}")

    translator_path = (
        root / "gartner-pdf-zh-translation" / "scripts" / "translate_gartner_pdf.py"
    )
    translator = translator_path.read_text(encoding="utf-8") if translator_path.is_file() else ""
    if "analysis-terminology.json" not in translator or "PHASE_BILINGUAL" not in translator:
        errors.append("PDF translator does not load the shared terminology data")

    stages = data.get("hype_cycle_stages", {})
    maturity = data.get("maturity", {})
    if stages.get("Innovation Trigger") == maturity.get("Embryonic"):
        errors.append("Innovation Trigger and Maturity=Embryonic must remain distinct")

    if errors:
        for item in errors:
            print(f"ERROR: {item}")
        print(f"FAIL: {len(errors)} terminology error(s)")
        return 1
    print("PASS: shared terminology is loaded and active resources contain no forbidden variants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
