#!/usr/bin/env python3
"""Validate the Markdown package produced by the Gartner analysis skill."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


COMPARATIVE_HEADINGS = [
    "总结概述",
    "Gartner 年度核心结论",
    "年度变化总览",
    "完整变化底表",
    "关键变化详细分析",
    "方法限制",
    "参考文献",
]

SINGLE_HEADINGS = [
    "总结概述",
    "Gartner 单年核心结论",
    "完整结构化底表",
    "重点内容详细提炼",
    "方法限制",
    "参考文献",
]

CROSS_REQUIRED_HEADINGS = {
    1: "总结概述",
    2: "HC×MQ 信号映射矩阵",
    3: "双报告支持的核心趋势",
    4: "外部证据的支持、修正与反证",
    5: "行业竞争结构、产品架构与交付模式影响",
    6: "对行业、用户与厂商的启示",
    7: "触发条件、领先指标与反向信号",
    9: "参考文献与分析研判说明",
}

# 历史交付物曾使用通信设备专属标题。保留读取兼容性，新的交付物和
# 生成协议统一使用通用标题；这样重跑 QA 不会因标题迁移掩盖内容问题。
CROSS_HEADING_ALIASES = {
    6: {"对通信设备方案厂商的启示"},
}

PAGE_ANCHOR_RE = re.compile(r"^##\s+原文第\s*(\d+)\s*页\s*$", re.MULTILINE)
H2_RE = re.compile(r"^##\s+(\d+)\s+(.+?)\s*$", re.MULTILINE)
ANY_HEADING_RE = re.compile(r"^#{2,6}\s+(.+?)\s*$", re.MULTILINE)
VALID_CITATION_RE = re.compile(
    r"「\[([GSPRVM]\d{3})(?:,\s*[^\]]+)?\]\(#ref-([GSPRVM]\d{3})\)」",
    re.IGNORECASE,
)
REFERENCE_RE = re.compile(
    r'^<a\s+id=["\']ref-([GSPRVM]\d{3})["\']\s*></a>(.*)$',
    re.IGNORECASE | re.MULTILINE,
)
SOURCE_META_RE = re.compile(
    r"<!--\s*source-meta:\s*([SPRVM]\d{3})\s*"
    r"\|\s*publisher=([^|]+?)\s*"
    r"\|\s*relationship=([^|]+?)\s*"
    r"\|\s*canonical=([^|>]+?)\s*-->",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://[^)\s]+", re.IGNORECASE)
PUBLISHER_RE = re.compile(r"发布者\s*[：:]\s*([^。；;]+)")
VALID_RELATIONSHIPS = {"independent", "vendor", "commissioned"}
QUANTITATIVE_CLAIM_RE = re.compile(
    r"(?:\d+(?:\.\d+)?\s*[%％]"
    r"|(?:增长|下降|提升|减少|达到|超过|低于|高于)\s*\d"
    r"|(?:[$¥€]|人民币|美元|亿元|million|billion)\s*\d"
    r"|\b\d+(?:\.\d+)?\s*(?:million|billion|万|亿)\b)",
    re.IGNORECASE,
)


def error(errors: list[str], message: str) -> None:
    errors.append(f"ERROR: {message}")


def planned_files(mode: str, years: list[str]) -> set[str]:
    if mode in {"full", "hc", "mq"} and len(years) != 2:
        raise ValueError(f"mode {mode} requires exactly two years")
    if mode in {"single-hc", "single-mq"} and len(years) != 1:
        raise ValueError(f"mode {mode} requires exactly one year")
    if len(set(years)) != len(years):
        raise ValueError("--years must not contain duplicates")
    if any(not re.fullmatch(r"\d{4}", year) for year in years):
        raise ValueError("every year must contain four digits")
    if len(years) == 2 and int(years[0]) >= int(years[1]):
        raise ValueError("--years must be in ascending order")

    if mode == "full":
        y1, y2 = years
        return {
            f"01-HC-{y1}-中文保真翻译.md",
            f"02-HC-{y2}-中文保真翻译.md",
            f"03-MQ-{y1}-中文保真翻译.md",
            f"04-MQ-{y2}-中文保真翻译.md",
            f"05-HC-{y1}-{y2}-结构化分析.md",
            f"06-MQ-{y1}-{y2}-结构化分析.md",
            f"07-HC-MQ-{y1}-{y2}-交叉洞察与趋势解读.md",
        }
    if mode == "hc":
        y1, y2 = years
        return {
            f"01-HC-{y1}-中文保真翻译.md",
            f"02-HC-{y2}-中文保真翻译.md",
            f"05-HC-{y1}-{y2}-结构化分析.md",
        }
    if mode == "mq":
        y1, y2 = years
        return {
            f"03-MQ-{y1}-中文保真翻译.md",
            f"04-MQ-{y2}-中文保真翻译.md",
            f"06-MQ-{y1}-{y2}-结构化分析.md",
        }
    year = years[0]
    if mode == "single-hc":
        return {
            f"01-HC-{year}-中文保真翻译.md",
            f"05-HC-{year}-单年结构化提炼.md",
        }
    return {
        f"03-MQ-{year}-中文保真翻译.md",
        f"06-MQ-{year}-单年结构化提炼.md",
    }


def validate_translation(path: Path, text: str, errors: list[str]) -> None:
    pages = [int(value) for value in PAGE_ANCHOR_RE.findall(text)]
    if not pages:
        error(errors, f"{path.name}: translation is missing page anchors")
    elif pages != list(range(1, max(pages) + 1)):
        error(errors, f"{path.name}: translation page anchors must be unique and consecutive from 1")

    forbidden_tokens = ("<推理>", "<估算>", "外部证据", "支持程度")
    forbidden_heading = re.search(
        r"^#{1,6}\s+.*(?:趋势解读|交叉洞察|战略启示|厂商启示|分析研判|年度变化|厂商对标)",
        text,
        re.MULTILINE,
    )
    found = [token for token in forbidden_tokens if token in text]
    if forbidden_heading:
        found.append(forbidden_heading.group(0).strip())
    if found:
        error(
            errors,
            f"{path.name}: translation contains analysis content or markers: {', '.join(found)}",
        )


def citation_data(text: str) -> tuple[set[str], dict[str, str], list[str]]:
    citations: set[str] = set()
    problems: list[str] = []
    for match in VALID_CITATION_RE.finditer(text):
        visible = match.group(1).upper()
        target = match.group(2).upper()
        if visible != target:
            problems.append(f"citation {visible} points to ref-{target.lower()}")
        else:
            citations.add(visible)

    references = {
        match.group(1).upper(): match.group(2).strip()
        for match in REFERENCE_RE.finditer(text)
    }

    malformed_patterns = (
        re.compile(r"\[\[[GSPRVM]\d{3}\]\]", re.IGNORECASE),
        re.compile(
            r"(?<!「)\[[GSPRVM]\d{3}(?:,\s*[^\]]+)?\]\(#ref-[^)]+\)(?!」)",
            re.IGNORECASE,
        ),
    )
    if any(pattern.search(text) for pattern in malformed_patterns):
        problems.append("citation syntax must be 「[G001](#ref-g001)」")
    return citations, references, problems


def source_metadata(text: str) -> dict[str, dict[str, str]]:
    return {
        match.group(1).upper(): {
            "publisher": match.group(2).strip(),
            "relationship": match.group(3).strip().casefold(),
            "canonical": match.group(4).strip(),
        }
        for match in SOURCE_META_RE.finditer(text)
    }


def reference_identity(detail: str) -> tuple[str | None, str | None]:
    publisher_match = PUBLISHER_RE.search(detail)
    publisher = publisher_match.group(1).strip() if publisher_match else None
    urls = URL_RE.findall(detail)
    canonical = urls[0].rstrip(".,;；。") if urls else None
    return publisher, canonical


def validate_citations_and_references(
    path: Path,
    text: str,
    errors: list[str],
    *,
    require_gartner_citation: bool,
) -> tuple[set[str], dict[str, str]]:
    citations, references, problems = citation_data(text)
    metadata = source_metadata(text)
    for problem in problems:
        error(errors, f"{path.name}: {problem}")
    if require_gartner_citation and not any(item.startswith("G") for item in citations):
        error(errors, f"{path.name}: missing Gartner citation")
    for item in sorted(citations - references.keys()):
        error(errors, f"{path.name}: citation {item} has no matching reference anchor")
    for item in sorted(citations):
        detail = references.get(item, "")
        if item.startswith("G") and not re.search(r"(?:第\s*\d+\s*页|\bp(?:age)?\.?\s*\d+)", detail, re.I):
            error(errors, f"{path.name}: Gartner reference {item} is missing a page number")
        if item[0] in "SPRVM" and not re.search(r"https?://", detail):
            error(errors, f"{path.name}: external reference {item} is missing a URL")
        if item[0] in "SPRVM" and item not in metadata:
            error(errors, f"{path.name}: external reference {item} is missing source-meta")
        if item[0] in "SPRVM" and item in metadata:
            item_meta = metadata[item]
            if item_meta["relationship"] not in VALID_RELATIONSHIPS:
                error(
                    errors,
                    f"{path.name}: external reference {item} has invalid relationship: "
                    f"{item_meta['relationship']}",
                )
            publisher, canonical = reference_identity(detail)
            if not publisher:
                error(errors, f"{path.name}: external reference {item} is missing publisher field")
            elif publisher.casefold() != item_meta["publisher"].casefold():
                error(errors, f"{path.name}: external reference {item} publisher does not match source-meta")
            if not canonical or canonical.casefold() != item_meta["canonical"].casefold():
                error(errors, f"{path.name}: external reference {item} canonical URL does not match source-meta")
        if detail and "核心证据片段" not in detail:
            error(errors, f"{path.name}: reference {item} is missing core evidence excerpt")
    return citations, references


def validate_quantitative_claims(path: Path, text: str, errors: list[str]) -> None:
    in_code_fence = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if (
            in_code_fence
            or not stripped
            or stripped.startswith(("#", "|", "<a ", "<!--"))
        ):
            continue
        if not QUANTITATIVE_CLAIM_RE.search(stripped):
            continue
        has_citation = bool(VALID_CITATION_RE.search(stripped))
        is_labeled = "<推理>" in stripped or "<估算>" in stripped
        if not has_citation and not is_labeled:
            error(
                errors,
                f"{path.name}:{line_number}: unsourced quantitative claim: {stripped}",
            )


def require_headings(
    path: Path, text: str, required: Iterable[str], errors: list[str]
) -> None:
    actual = [heading.strip() for _, heading in H2_RE.findall(text)]
    expected = list(required)
    if actual != expected:
        error(
            errors,
            f"{path.name}: required headings are {expected}; found {actual}",
        )


def validate_evidence_blocks(path: Path, text: str, errors: list[str]) -> None:
    starts = list(re.finditer(r"<!--\s*change-priority:\s*(P[01])\s*-->", text, re.I))
    blocks = re.findall(
        r"<!--\s*change-priority:\s*(P[01])\s*-->(.*?)<!--\s*/change\s*-->",
        text,
        re.I | re.S,
    )
    if not starts:
        if re.search(r"<!--\s*no-p0-p1:\s*\S.+?-->", text, re.I):
            return
        error(errors, f"{path.name}: missing P0/P1 evidence block")
        return
    if len(blocks) != len(starts):
        error(errors, f"{path.name}: an evidence block is not closed with <!-- /change -->")

    required_fields = [
        "变化事实",
        "Gartner 证据",
        "Gartner 结论",
        "外部证据",
        "支持程度",
        "限制",
    ]
    metadata = source_metadata(text)
    _, references, _ = citation_data(text)
    for index, (priority, block) in enumerate(blocks, start=1):
        missing = [
            field
            for field in required_fields
            if not re.search(rf"^-\s*{re.escape(field)}\s*[：:]", block, re.MULTILINE)
        ]
        if missing:
            error(
                errors,
                f"{path.name}: {priority.upper()} evidence block {index} missing fields: {', '.join(missing)}",
            )
        block_citations, _, _ = citation_data(block)
        if not any(item.startswith("G") for item in block_citations):
            error(errors, f"{path.name}: {priority.upper()} evidence block {index} missing Gartner evidence")
        external = {item for item in block_citations if item[0] in "SPRVM"}
        if len(external) < 2:
            error(errors, f"{path.name}: {priority.upper()} evidence block {index} needs two external sources")
        if not any(item[0] in "SPR" for item in external):
            error(errors, f"{path.name}: {priority.upper()} evidence block {index} needs an S/P/R source")
        external_meta = [metadata.get(item) for item in external]
        if all(item is not None for item in external_meta):
            metadata_identities = [
                (item["publisher"].casefold(), item["canonical"].casefold())
                for item in external_meta
            ]
            if len(set(metadata_identities)) < len(metadata_identities):
                error(
                    errors,
                    f"{path.name}: {priority.upper()} evidence block {index} external sources are not independent",
                )
            identities = [reference_identity(references.get(item, "")) for item in external]
            publishers = {
                publisher.casefold()
                for publisher, _ in identities
                if publisher
            }
            canonicals = {
                canonical.casefold()
                for _, canonical in identities
                if canonical
            }
            if len(publishers) < len(external) or len(canonicals) < len(external):
                error(
                    errors,
                    f"{path.name}: {priority.upper()} evidence block {index} external sources are not independent",
                )
            if not any(
                item[0] in "SPR"
                and metadata.get(item, {}).get("relationship") == "independent"
                for item in external
            ):
                error(
                    errors,
                    f"{path.name}: {priority.upper()} evidence block {index} needs an independent S/P/R source",
                )


def validate_analysis(
    path: Path,
    text: str,
    errors: list[str],
    *,
    single: bool,
    kind: str,
) -> None:
    require_headings(
        path,
        text,
        SINGLE_HEADINGS if single else COMPARATIVE_HEADINGS,
        errors,
    )
    strategy_heading = re.search(
        r"^#{2,6}\s+.*(?:对行业、用户与厂商的启示|对通信设备方案厂商的启示|厂商战略|战略建议|行动建议|厂商对标)",
        text,
        re.MULTILINE,
    )
    if strategy_heading:
        error(errors, f"{path.name}: analysis contains vendor strategy section")
    body = re.split(r"^##\s+(?:6|7)\s+参考文献", text, maxsplit=1, flags=re.MULTILINE)[0]
    strategy_statement = re.search(
        r"(?:通信设备方案厂商|网络设备厂商|厂商|供应商).{0,40}"
        r"(?:应该|应当|需要|必须|建议).{0,60}"
        r"(?:投入|布局|研发|收购|合作|产品|路线图|战略|行动)",
        body,
    )
    reverse_strategy_statement = re.search(
        r"(?:应该|应当|需要|必须|建议).{0,40}"
        r"(?:通信设备方案厂商|网络设备厂商|厂商|供应商).{0,60}"
        r"(?:投入|布局|研发|收购|合作|产品|路线图|战略|行动)",
        body,
    )
    if strategy_statement or reverse_strategy_statement:
        error(errors, f"{path.name}: analysis contains vendor strategy statement")
    forbidden_by_kind = {
        "HC": re.compile(
            r"Magic Quadrant|象限|\bLeaders?\b|\bChallengers?\b|\bVisionaries\b|"
            r"Niche Players|Ability to Execute|Completeness of Vision|\bStrengths\b|\bCautions\b",
            re.IGNORECASE,
        ),
        "MQ": re.compile(
            r"Hype Cycle|\bHC\b|Innovation Trigger|Peak of Inflated Expectations|"
            r"Trough of Disillusionment|Slope of Enlightenment|Plateau of Productivity|"
            r"Benefit Rating|Years to Mainstream Adoption|技术萌芽期|期望膨胀期|"
            r"泡沫破裂谷底期|稳步爬升复苏期|生产成熟期|收益：|主流采用年限",
            re.IGNORECASE,
        ),
    }
    if forbidden_by_kind[kind].search(body):
        other = "MQ" if kind == "HC" else "HC"
        error(errors, f"{path.name}: {kind} analysis contains {other} content")
    validate_citations_and_references(
        path, text, errors, require_gartner_citation=True
    )
    validate_quantitative_claims(path, text, errors)
    if not single:
        validate_evidence_blocks(path, text, errors)


def validate_core_insights(path: Path, text: str, errors: list[str]) -> None:
    starts = list(re.finditer(r"<!--\s*insight:\s*core\s*-->", text, re.I))
    blocks = re.findall(
        r"<!--\s*insight:\s*core\s*-->(.*?)<!--\s*/insight\s*-->",
        text,
        re.I | re.S,
    )
    if not starts:
        error(errors, f"{path.name}: missing core insight evidence block")
        return
    if len(blocks) != len(starts):
        error(errors, f"{path.name}: a core insight block is not closed with <!-- /insight -->")
    for index, block in enumerate(blocks, start=1):
        fields = {
            "HC 信号": re.search(r"^-?\s*HC\s*信号\s*[：:](.*)$", block, re.MULTILINE),
            "MQ 信号": re.search(r"^-?\s*MQ\s*信号\s*[：:](.*)$", block, re.MULTILINE),
            "外部证据": re.search(r"^-?\s*外部证据\s*[：:](.*)$", block, re.MULTILINE),
            "变化机制": re.search(r"^-?\s*变化机制\s*[：:](.*)$", block, re.MULTILINE),
            "行业影响": re.search(r"^-?\s*行业影响\s*[：:](.*)$", block, re.MULTILINE),
            "行业、用户与厂商启示": re.search(
                r"^-?\s*(?:行业、用户与厂商启示|行业、用户与厂商的启示)\s*[：:](.*)$",
                block,
                re.MULTILINE,
            ),
        }
        if not fields["行业、用户与厂商启示"]:
            # 兼容旧版 networking 交叉洞察块；新内容应使用通用字段。
            fields["行业、用户与厂商启示"] = re.search(
                r"^-?\s*通信设备方案厂商启示\s*[：:](.*)$", block, re.MULTILINE
            )
        for label, match in fields.items():
            if not match:
                error(errors, f"{path.name}: core insight {index} missing field: {label}")
            elif not match.group(1).strip():
                error(errors, f"{path.name}: core insight {index} empty field: {label}")
        for label in ("HC 信号", "MQ 信号"):
            value = fields[label].group(1) if fields[label] else ""
            cited, _, _ = citation_data(value)
            if not any(item.startswith("G") for item in cited):
                short_label = "HC" if label.startswith("HC") else "MQ"
                error(errors, f"{path.name}: core insight {index} missing Gartner {short_label} citation")
        external_value = fields["外部证据"].group(1) if fields["外部证据"] else ""
        external_citations, _, _ = citation_data(external_value)
        if not any(item[0] in "SPRVM" for item in external_citations):
            error(errors, f"{path.name}: core insight {index} missing external citation")


def validate_cross(
    path: Path,
    text: str,
    errors: list[str],
    target_vendor: str | None,
) -> None:
    numbered = {int(number): heading.strip() for number, heading in H2_RE.findall(text)}
    for number, heading in CROSS_REQUIRED_HEADINGS.items():
        actual_heading = numbered.get(number)
        if actual_heading != heading and actual_heading not in CROSS_HEADING_ALIASES.get(number, set()):
            error(errors, f"{path.name}: section {number} must be '{heading}'")

    section_eight = numbered.get(8)
    if target_vendor:
        expected = f"{target_vendor} 对标"
        if section_eight != expected:
            error(errors, f"{path.name}: target vendor section 8 must be '{expected}'")
    elif section_eight is not None:
        error(errors, f"{path.name}: target vendor section requires --target-vendor")

    validate_citations_and_references(
        path, text, errors, require_gartner_citation=False
    )
    validate_quantitative_claims(path, text, errors)
    validate_core_insights(path, text, errors)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path, help="Directory containing the formal Markdown outputs")
    parser.add_argument(
        "--mode",
        required=True,
        choices=("full", "hc", "mq", "single-hc", "single-mq"),
    )
    parser.add_argument("--years", nargs="+", required=True, metavar="YEAR")
    parser.add_argument("--target-vendor", help="Vendor name allowed in cross-insight section 8")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    try:
        expected = planned_files(args.mode, args.years)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 2

    root = args.output_dir
    if not root.is_dir():
        print(f"ERROR: output directory does not exist or is not a directory: {root}")
        return 2

    actual = {
        path.name
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in {".md", ".markdown"}
    }
    for name in sorted(expected - actual):
        error(errors, f"missing Markdown: {name}")
    for name in sorted(actual - expected):
        error(errors, f"unexpected Markdown: {name}")

    for name in sorted(expected & actual):
        path = root / name
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            error(errors, f"{name}: cannot read UTF-8 Markdown: {exc}")
            continue
        if not text.strip():
            error(errors, f"{name}: document is empty")
            continue
        if "中文保真翻译" in name:
            validate_translation(path, text, errors)
        elif "交叉洞察与趋势解读" in name:
            validate_cross(path, text, errors, args.target_vendor)
        else:
            kind = "HC" if "-HC-" in name else "MQ"
            validate_analysis(
                path,
                text,
                errors,
                single="单年结构化提炼" in name,
                kind=kind,
            )

    if errors:
        print("\n".join(errors))
        return 1
    print(f"PASS: validated {len(expected)} Markdown document(s) in {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
