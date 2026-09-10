#!/usr/bin/env python3
"""Check auditable page, number, term, figure, and table coverage in a translation."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path


PAGE_ANCHOR_RE = re.compile(r"^##\s+原文第\s*(\d+)\s*页\s*$", re.MULTILINE)
GARTNER_ID_RE = re.compile(r"\bG\d{8}\b", re.IGNORECASE)
NUMBER_RE = re.compile(
    r"(?<![A-Za-z])(?:[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|[+-]?\d+(?:\.\d+)?)"
    r"(?:\s*[-–—~～]\s*(?:[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|[+-]?\d+(?:\.\d+)?))?"
    r"\s*[%％]?(?![A-Za-z])"
)

PROTECTED_TERMS = (
    "Hype Cycle",
    "Magic Quadrant",
    "Innovation Trigger",
    "Peak of Inflated Expectations",
    "Trough of Disillusionment",
    "Slope of Enlightenment",
    "Plateau of Productivity",
    "Completeness of Vision",
    "Ability to Execute",
)


def read_source(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        executable = shutil.which("pdftotext")
        if not executable:
            raise RuntimeError("pdftotext is required to validate a PDF source")
        result = subprocess.run(
            [executable, str(path), "-"],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or f"exit code {result.returncode}"
            raise RuntimeError(f"pdftotext failed: {detail}")
        return result.stdout
    raise ValueError("--source must be a .txt or .pdf file")


def canonical_number(value: str) -> str:
    value = value.strip().replace("％", "%")
    value = re.sub(r"\s*[–—~～]\s*", "-", value)
    value = re.sub(r"\s+", "", value)
    return value


def numeric_tokens(text: str) -> Counter[str]:
    return Counter(
        canonical_number(match.group(0))
        for match in NUMBER_RE.finditer(text)
        if canonical_number(match.group(0))
    )


def numbered_labels(text: str, kind: str) -> set[str]:
    if kind == "figure":
        pattern = r"(?:\bFigure|\bFig\.?|图)\s*([A-Za-z]?\d+(?:[.-]\d+)*)"
    else:
        pattern = r"(?:\bTable|表)\s*([A-Za-z]?\d+(?:[.-]\d+)*)"
    return {value.casefold() for value in re.findall(pattern, text, re.IGNORECASE)}


def split_source_pages(text: str, expected_pages: int) -> list[str] | None:
    if "\f" in text:
        pages = text.split("\f")
        while pages and not pages[-1].strip():
            pages.pop()
        if len(pages) == expected_pages:
            return pages

    markers = list(re.finditer(r"^Page\s+(\d+)\b", text, re.MULTILINE | re.IGNORECASE))
    if [int(match.group(1)) for match in markers] == list(range(1, expected_pages + 1)):
        return [
            text[match.start() : markers[index + 1].start() if index + 1 < len(markers) else len(text)]
            for index, match in enumerate(markers)
        ]
    if expected_pages == 1:
        return [text]
    return None


def split_translation_pages(text: str) -> list[str]:
    anchors = list(PAGE_ANCHOR_RE.finditer(text))
    return [
        text[match.start() : anchors[index + 1].start() if index + 1 < len(anchors) else len(text)]
        for index, match in enumerate(anchors)
    ]


def format_missing_counts(missing: Counter[str]) -> list[str]:
    return [
        f"{token}×{count}" if count > 1 else token
        for token, count in sorted(missing.items())
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Original .txt or .pdf")
    parser.add_argument("--translation", required=True, type=Path, help="Translated Markdown")
    parser.add_argument("--expected-pages", required=True, type=int)
    parser.add_argument(
        "--term",
        action="append",
        default=[],
        help="Protected term that must remain verbatim; may be repeated",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    if args.expected_pages < 1:
        print("ERROR: --expected-pages must be at least 1")
        return 2
    if not args.source.is_file():
        print(f"ERROR: source file does not exist: {args.source}")
        return 2
    if not args.translation.is_file():
        print(f"ERROR: translation file does not exist: {args.translation}")
        return 2

    try:
        source = read_source(args.source)
        translation = args.translation.read_text(encoding="utf-8")
    except (OSError, UnicodeError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 2

    anchors = [int(value) for value in PAGE_ANCHOR_RE.findall(translation)]
    expected_anchors = list(range(1, args.expected_pages + 1))
    if anchors != expected_anchors:
        missing = [str(page) for page in expected_anchors if page not in anchors]
        duplicates = sorted({page for page in anchors if anchors.count(page) > 1})
        extras = [str(page) for page in anchors if page not in expected_anchors]
        detail: list[str] = []
        if missing:
            detail.append("missing " + ", ".join(missing))
        if duplicates:
            detail.append("duplicate " + ", ".join(map(str, duplicates)))
        if extras:
            detail.append("unexpected " + ", ".join(extras))
        if not detail and anchors != expected_anchors:
            detail.append("anchors are out of order")
        errors.append("ERROR: missing page anchors or invalid page-anchor sequence: " + "; ".join(detail))

    requested_terms: list[str] = []
    for term in (*PROTECTED_TERMS, *args.term):
        if term and term.casefold() in source.casefold() and term.casefold() not in {
            item.casefold() for item in requested_terms
        }:
            requested_terms.append(term)
    source_pages = split_source_pages(source, args.expected_pages)
    translated_pages = split_translation_pages(translation)
    if source_pages is None:
        errors.append(
            "ERROR: source cannot be split into the expected page count; "
            "use PDF form-feed output or Page N markers"
        )
    else:
        translated_pages = (
            translated_pages + [""] * args.expected_pages
        )[: args.expected_pages]
        for page_number, (source_page, translated_page) in enumerate(
            zip(source_pages, translated_pages), start=1
        ):
            missing_numbers = format_missing_counts(
                numeric_tokens(source_page) - numeric_tokens(translated_page)
            )
            if missing_numbers:
                errors.append(
                    f"ERROR: page {page_number} missing numeric tokens: "
                    + ", ".join(missing_numbers)
                )

            source_ids = {value.upper() for value in GARTNER_ID_RE.findall(source_page)}
            translated_ids = {
                value.upper() for value in GARTNER_ID_RE.findall(translated_page)
            }
            missing_ids = sorted(source_ids - translated_ids)
            if missing_ids:
                errors.append(
                    f"ERROR: page {page_number} missing Gartner IDs: "
                    + ", ".join(missing_ids)
                )

            missing_terms = [
                term
                for term in requested_terms
                if term.casefold() in source_page.casefold()
                and term.casefold() not in translated_page.casefold()
            ]
            if missing_terms:
                errors.append(
                    f"ERROR: page {page_number} missing protected terms: "
                    + ", ".join(missing_terms)
                )

            for kind in ("figure", "table"):
                missing_labels = sorted(
                    numbered_labels(source_page, kind)
                    - numbered_labels(translated_page, kind)
                )
                if missing_labels:
                    errors.append(
                        f"ERROR: page {page_number} missing {kind} labels: "
                        + ", ".join(missing_labels)
                    )

    if errors:
        print("\n".join(errors))
        return 1
    print(
        "PASS: translation coverage validated "
        f"({args.expected_pages} pages, {sum(numeric_tokens(source).values())} numeric tokens, "
        f"{len({value.upper() for value in GARTNER_ID_RE.findall(source)})} Gartner IDs)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
