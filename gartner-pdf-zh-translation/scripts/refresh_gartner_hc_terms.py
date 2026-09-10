#!/usr/bin/env python3
"""Refresh cached Gartner HC translations with deterministic term rules.

This pass is intentionally local and does not call a translation model. It
sets each profile's technical item name and ``Analysis By`` line to the exact
source wording, then the normal translator rebuilds the PDF and audit file.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path


def load_translator():
    path = Path(__file__).with_name("translate_gartner_pdf.py")
    spec = importlib.util.spec_from_file_location("gartner_translate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def refresh(source: Path, outdir: Path) -> int:
    t = load_translator()
    cache_path = outdir / "assets" / "translation-cache" / "translations-grouped.json"
    if not cache_path.exists():
        raise FileNotFoundError(cache_path)
    doc = t.fitz.open(source)
    page_data = []
    for page_no, page in enumerate(doc, start=1):
        page_data.append({"page": page_no, "blocks": t.layout_units(page), "has_images": bool(page.get_images(full=True))})
    doc.close()
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    changed = 0
    before = json.dumps(cache, ensure_ascii=False, sort_keys=True)
    # Normalize the common free-model spellings in every cached value.
    for page_values in cache.values():
        for key, value in list(page_values.items()):
            if isinstance(value, str):
                value = t.canonicalize_cached_translation(value)
                value = re.sub(r"^(?:分析师|分析者|分析人员|分析人|分析作者)\s*[：:]", "Analysis By:", value)
                page_values[key] = value
    # Apply source-authoritative names last so generic zero-trust spelling
    # normalization cannot alter title case in technology item headings.
    t.enforce_fixed_gartner_fields(page_data, cache)
    after = json.dumps(cache, ensure_ascii=False, sort_keys=True)
    if after != before:
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
        changed = 1
    return changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("outdir", type=Path)
    args = ap.parse_args()
    print(refresh(args.source.resolve(), args.outdir.resolve()))


if __name__ == "__main__":
    main()
