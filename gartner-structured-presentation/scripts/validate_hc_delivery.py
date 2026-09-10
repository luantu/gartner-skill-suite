#!/usr/bin/env python3
"""Validate the structural contract for a two-year HC Feishu delivery.

This checks only the manifest and exported document structure. It does not
replace human review of PDF extraction fidelity, Gartner evidence semantics,
analyst conclusions, citations' truthfulness, or whiteboard visual rendering.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


DETAIL_TOPICS = {
    "技术", "技术成熟度", "优先级矩阵", "市场渗透率", "定义", "为什么重要",
    "业务影响", "驱动力", "障碍", "用户建议", "供应商",
}
SUMMARY_COLUMNS = ["分类", "技术布局结论", "未来规模应用窗口期", "未来重点技术趋势"]
GARTNER_LINK = re.compile(r"^\[G\d{3}\]$")
MANUAL_NUMBER = re.compile(
    r"^\s*(?:\d+(?:[.．]\d+)*(?:[、．]|\.(?!\d))(?=\s|[\u4e00-\u9fff]|$)"
    r"|\d+(?:[.．]\d+)+(?=\s|$)|[一二三四五六七八九十]+[、.．])"
)


def element_text(node: ET.Element) -> str:
    return " ".join("".join(node.itertext()).split())


def error(errors: list[str], message: str) -> None:
    errors.append(f"ERROR: {message}")


def parse_xml(content: str) -> ET.Element:
    try:
        return ET.fromstring(content)
    except ET.ParseError:
        return ET.fromstring(f"<root>{content}</root>")


def content_from_fetch(fetched: Any) -> tuple[bool, str | None, str | None]:
    if not isinstance(fetched, dict) or fetched.get("ok") is not True:
        return False, None, None
    data = fetched.get("data")
    document = data.get("document", {}) if isinstance(data, dict) else {}
    if not isinstance(document, dict):
        return True, None, None
    return True, document.get("document_id"), document.get("content")


def table_by_id(ids: dict[str, ET.Element], block_id: str, errors: list[str], label: str) -> ET.Element | None:
    node = ids.get(block_id)
    if node is None or node.tag != "table":
        error(errors, f"{label} block id {block_id!r} does not identify a table")
        return None
    return node


def table_headers(table: ET.Element) -> list[str]:
    row = table.find("./thead/tr")
    if row is None:
        return []
    return [element_text(cell) for cell in list(row) if cell.tag in {"th", "td"}]


def data_rows(table: ET.Element) -> list[ET.Element]:
    body = table.find("./tbody")
    return [] if body is None else [row for row in list(body) if row.tag == "tr"]


def check_vertical_alignment(table: ET.Element, errors: list[str], label: str) -> None:
    for cell in table.iter():
        if cell.tag in {"td", "th"} and cell.get("vertical-align") not in {None, "middle"}:
            error(errors, f"{label} has a cell not vertically centered")
            return


def click_gartner_reference(node: ET.Element, ids: dict[str, ET.Element], errors: list[str], label: str) -> None:
    links = [link for link in node.iter("a") if GARTNER_LINK.fullmatch(element_text(link))]
    if not links:
        error(errors, f"{label} is missing a clickable Gartner citation")
        return
    for link in links:
        href = link.get("href", "")
        if not href:
            error(errors, f"{label} Gartner citation has no href")
            continue
        if "#" in href:
            target = href.rsplit("#", 1)[1]
            if not target or target not in ids:
                error(errors, f"{label} Gartner citation has a broken local anchor")
        elif not href.startswith(("http://", "https://")):
            error(errors, f"{label} Gartner citation href is neither a local anchor nor an HTTP URL")


def validate_manifest(manifest: Any, errors: list[str], *, local_only: bool) -> dict[str, Any] | None:
    if not isinstance(manifest, dict):
        error(errors, "manifest must be a JSON object")
        return None
    years = manifest.get("years")
    if not isinstance(years, list) or len(years) != 2 or not all(isinstance(year, int) for year in years) or years != sorted(years) or years[0] == years[1]:
        error(errors, "manifest years must contain two distinct ascending integer years")
        return None
    reports = manifest.get("source_reports")
    if not isinstance(reports, list) or len(reports) != 2:
        error(errors, "manifest source_reports must contain two reports")
        return None
    report_technologies: dict[int, set[str]] = {}
    for report in reports:
        if not isinstance(report, dict) or report.get("year") not in years:
            error(errors, "every source report must name a manifest year")
            continue
        names = report.get("technologies")
        if not isinstance(names, list) or not names or any(not isinstance(name, str) or not name.strip() for name in names):
            error(errors, f"source report {report.get('year')} technologies must be a nonempty string list")
            continue
        if len(set(names)) != len(names):
            error(errors, f"source report {report.get('year')} technologies contains duplicates")
        report_technologies[report["year"]] = set(names)
    if set(report_technologies) != set(years):
        error(errors, "source_reports must cover each manifest year exactly once")

    technologies = manifest.get("technologies")
    if not isinstance(technologies, list) or not technologies:
        error(errors, "manifest technologies must be a nonempty list")
        return None
    ids_seen: set[str] = set()
    display_seen: set[str] = set()
    mapped: dict[int, list[str]] = {year: [] for year in years}
    for technology in technologies:
        if not isinstance(technology, dict):
            error(errors, "every technology entry must be an object")
            continue
        tech_id, display = technology.get("id"), technology.get("display_name")
        if not isinstance(tech_id, str) or not tech_id or tech_id in ids_seen:
            error(errors, "technology id values must be nonempty and unique")
        ids_seen.add(tech_id) if isinstance(tech_id, str) else None
        if not isinstance(display, str) or not display or display in display_seen:
            error(errors, "technology display_name values must be nonempty and unique")
        display_seen.add(display) if isinstance(display, str) else None
        names = technology.get("names")
        allowed_years = {str(year) for year in years}
        if not isinstance(names, dict) or not names or not set(names).issubset(allowed_years):
            error(errors, f"technology {display!r} names must use one or both manifest years")
        else:
            for year_text, raw_names in names.items():
                values = [raw_names] if isinstance(raw_names, str) else raw_names
                if (
                    not isinstance(values, list)
                    or not values
                    or any(not isinstance(name, str) or not name for name in values)
                ):
                    error(errors, f"technology {display!r} has invalid {year_text} names")
                else:
                    mapped[int(year_text)].extend(values)
        detail = technology.get("detail")
        if not isinstance(detail, bool):
            error(errors, f"technology {display!r} detail must be boolean")
        if detail is False and (not isinstance(technology.get("exclusion_reason"), str) or not technology["exclusion_reason"].strip()):
            error(errors, f"non-detail technology {display!r} needs exclusion_reason")
    for year in years:
        if len(mapped[year]) != len(set(mapped[year])) or set(mapped[year]) != report_technologies.get(year, set()):
            error(errors, f"technology names for {year} do not exactly cover source_reports technologies")

    blocks = manifest.get("blocks")
    block_names = ("summary_table", "overview_table", "summary_board", "comparison_board")
    if not isinstance(blocks, dict) or any(not isinstance(blocks.get(name), str) or not blocks[name] for name in block_names):
        error(errors, "manifest blocks must provide four nonempty block ids")
    elif len({blocks[name] for name in block_names}) != len(block_names):
        error(errors, "manifest block ids must be unique")

    figures = manifest.get("source_figures")
    expected_figures = {(year, kind) for year in years for kind in ("hype-cycle", "priority-matrix")}
    found_figures: set[tuple[int, str]] = set()
    figure_ids: set[str] = set()
    if not isinstance(figures, list) or len(figures) != 4:
        error(errors, "manifest source_figures must contain four entries")
    else:
        for figure in figures:
            if not isinstance(figure, dict):
                error(errors, "each source figure must be an object")
                continue
            block_id, year, kind, page = (figure.get("block_id"), figure.get("year"), figure.get("kind"), figure.get("page"))
            if not isinstance(block_id, str) or not block_id or block_id in figure_ids:
                error(errors, "source figure block_id values must be nonempty and unique")
            figure_ids.add(block_id) if isinstance(block_id, str) else None
            if year not in years or kind not in {"hype-cycle", "priority-matrix"} or not isinstance(page, int) or page <= 0:
                error(errors, "source figure must use a manifest year, known kind, and positive page")
            else:
                found_figures.add((year, kind))
        if found_figures != expected_figures:
            error(errors, "source_figures must cover each year × figure kind exactly once")
    if not local_only and (not isinstance(manifest.get("document_id"), str) or not manifest["document_id"]):
        error(errors, "manifest document_id must be nonempty")
    return manifest


def normalized_overview_headers(headers: list[str], years: list[int]) -> bool:
    if len(headers) != 4:
        return False
    compact = [re.sub(r"[\s（）()]", "", header).replace("相比于", "相比") for header in headers]
    return compact == ["技术", f"{years[1]}年变化相比{years[0]}年", "关键变化", "变化解读"] or compact == ["技术", f"{years[1]}年变化相比{years[0]}", "关键变化", "变化解读"]


def validate(manifest: Any, fetched: Any) -> list[str]:
    """Return structural contract failures for a manifest and a fetched document."""
    errors: list[str] = []
    local_only = isinstance(fetched, dict) and fetched.get("_local_only") is True
    manifest = validate_manifest(manifest, errors, local_only=local_only)
    if manifest is None or errors:
        return errors
    ok, document_id, content = content_from_fetch(fetched)
    if not ok:
        error(errors, "fetch response ok must be true")
        return errors
    if not local_only and document_id != manifest["document_id"]:
        error(errors, "manifest document_id does not match fetched document_id")
    if not isinstance(content, str) or not content.strip():
        error(errors, "fetch response has no real document content")
        return errors
    try:
        root = parse_xml(content)
    except ET.ParseError as exc:
        error(errors, f"document content is not parseable XML: {exc}")
        return errors
    ids = {node.get("id"): node for node in root.iter() if node.get("id")}
    direct = list(root)
    headings = [node for node in root.iter() if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}]
    if headings and headings[0].tag != "h1":
        error(errors, "first heading must be h1")
    previous = 0
    for heading in headings:
        level = int(heading.tag[1])
        if MANUAL_NUMBER.match(element_text(heading)):
            error(errors, f"heading {element_text(heading)!r} has a manual number")
        if previous and level > previous + 1:
            error(errors, f"heading {element_text(heading)!r} skips a heading level")
        previous = level
        marker = heading.get("seq-marker", "")
        if not local_only and not re.fullmatch(r"\d+(?:\.\d+)*\.?", marker.strip()):
            error(errors, f"heading {element_text(heading)!r} is missing seq-marker")
    required_h1 = ["洞察总结", "技术线索分析", "方法与限制", "参考文献"]
    h1_text = [element_text(node) for node in headings if node.tag == "h1"]
    positions = []
    for title in required_h1:
        if title not in h1_text:
            error(errors, f"missing required h1 {title}")
        else:
            positions.append(h1_text.index(title))
    if positions and positions != sorted(positions):
        error(errors, "required h1 sections are out of order")
    summary_heading = next((node for node in direct if node.tag == "h1" and element_text(node) == "洞察总结"), None)
    if summary_heading is None:
        error(errors, "洞察总结 must be a direct h1 block")
    else:
        position = direct.index(summary_heading)
        if position + 1 >= len(direct) or direct[position + 1].tag != "callout":
            error(errors, "洞察总结 must be immediately followed by a callout")

    blocks = manifest["blocks"]
    # Check section placement, including media nested in a grid or column.
    top_positions = {node: index for index, top in enumerate(direct) for node in top.iter()}
    section_positions = {
        title: next((i for i, node in enumerate(direct) if node.tag == "h1" and element_text(node) == title), -1)
        for title in required_h1
    }
    def in_section(node: ET.Element | None, start: int, end: int) -> bool:
        return node is not None and start >= 0 and start < top_positions.get(node, -1) < end

    summary_start, analysis_start = section_positions["洞察总结"], section_positions["技术线索分析"]
    limits_start = section_positions["方法与限制"]
    for name in ("summary_board", "summary_table"):
        if not in_section(ids.get(blocks[name]), summary_start, analysis_start):
            error(errors, f"{name} must be in the 洞察总结 section")
    for label in ("线索总结", "年度对比总览"):
        if not any(element_text(h) == label and in_section(h, analysis_start, limits_start) for h in headings):
            error(errors, f"missing analysis subsection {label}")
    overview_heading = next((h for h in headings if element_text(h) == "年度对比总览"), None)
    overview_start = top_positions.get(overview_heading, -1)
    detail_names = {t["display_name"] for t in manifest["technologies"] if t["detail"]}
    detail_positions = [top_positions[h] for h in headings if element_text(h) in detail_names]
    overview_end = min(detail_positions) if detail_positions else limits_start
    for name in ("comparison_board", "overview_table"):
        if not in_section(ids.get(blocks[name]), overview_start, overview_end):
            error(errors, f"{name} must precede technology details in 年度对比总览")
    for figure in manifest["source_figures"]:
        if not in_section(ids.get(figure["block_id"]), overview_start, overview_end):
            error(errors, f"source figure {figure['block_id']} must be in 年度对比总览")
    summary = table_by_id(ids, blocks["summary_table"], errors, "summary_table")
    if summary is not None:
        if table_headers(summary) != SUMMARY_COLUMNS:
            error(errors, "summary_table has invalid columns")
        check_vertical_alignment(summary, errors, "summary_table")
    overview = table_by_id(ids, blocks["overview_table"], errors, "overview_table")
    if overview is not None:
        if not normalized_overview_headers(table_headers(overview), manifest["years"]):
            error(errors, "overview_table has invalid columns")
        names: list[str] = []
        for row in data_rows(overview):
            cells = [cell for cell in list(row) if cell.tag == "td"]
            if len(cells) != 4 or any(not element_text(cell) for cell in cells):
                error(errors, "overview_table has an empty or malformed data row")
                continue
            names.append(element_text(cells[0]))
        declared = {tech["display_name"] for tech in manifest["technologies"]}
        missing = declared - set(names)
        if missing:
            error(errors, f"overview_table is missing technologies: {', '.join(sorted(missing))}")
        duplicates = {name for name in names if names.count(name) > 1}
        if duplicates:
            error(errors, f"overview_table has duplicate technologies: {', '.join(sorted(duplicates))}")
        undeclared = set(names) - declared
        if undeclared:
            error(errors, f"overview_table has undeclared technologies: {', '.join(sorted(undeclared))}")
        check_vertical_alignment(overview, errors, "overview_table")

    for name in ("summary_board", "comparison_board"):
        board = ids.get(blocks[name])
        if board is None or board.tag != "whiteboard":
            error(errors, f"{name} block id {blocks[name]!r} does not identify a whiteboard")
        elif not local_only and not board.get("token"):
            error(errors, f"{name} whiteboard is missing token")

    for figure in manifest["source_figures"]:
        node = ids.get(figure["block_id"])
        if node is None or node.tag != "img":
            error(errors, f"source figure {figure['block_id']!r} is not an img block")
        elif not local_only and not any(node.get(key) for key in ("src", "token", "href", "url")):
            error(errors, f"source figure {figure['block_id']!r} has no loaded image resource")

    for technology in manifest["technologies"]:
        if not technology["detail"]:
            continue
        title = next((node for node in direct if node.tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and element_text(node) == technology["display_name"]), None)
        if title is None:
            error(errors, f"detail technology {technology['display_name']!r} is missing a title")
            continue
        if not in_section(title, analysis_start, limits_start):
            error(errors, f"detail technology {technology['display_name']!r} must be in 技术线索分析")
        index = direct.index(title)
        if index + 2 >= len(direct) or direct[index + 1].tag != "callout" or direct[index + 2].tag != "table":
            error(errors, f"detail technology {technology['display_name']!r} must be title, callout, then table")
            continue
        callout, table = direct[index + 1], direct[index + 2]
        if not local_only:
            click_gartner_reference(callout, ids, errors, f"detail callout {technology['display_name']}")
            click_gartner_reference(table, ids, errors, f"detail table {technology['display_name']}")
        if table_headers(table) != ["技术", "主题", "内容"]:
            error(errors, f"detail table {technology['display_name']} has invalid columns")
        rows = data_rows(table)
        if not rows:
            error(errors, f"detail table {technology['display_name']} has no data rows")
            continue
        first_cells = [cell for cell in list(rows[0]) if cell.tag == "td"]
        if len(first_cells) != 3 or first_cells[0].get("rowspan") != str(len(rows)):
            error(errors, f"detail table {technology['display_name']} has invalid rowspan")
        elif element_text(first_cells[0]) != technology["display_name"]:
            error(errors, f"detail table {technology['display_name']} has the wrong technology cell")
        for row in rows[1:]:
            if len([cell for cell in list(row) if cell.tag == "td"]) != 2:
                error(errors, f"detail table {technology['display_name']} has a topic row in the technology column")
                break
        topics = [element_text(list(row)[1 if index == 0 else 0]) for index, row in enumerate(rows) if len(list(row)) >= (2 if index == 0 else 1)]
        if not DETAIL_TOPICS.issubset(set(topics)) or any(topic not in DETAIL_TOPICS | {"成熟度（Maturity）", "成熟度"} for topic in topics):
            error(errors, f"detail table {technology['display_name']} has invalid required topics")
        for cell in table.iter():
            if cell.tag in {"td", "th"} and not element_text(cell):
                error(errors, f"detail table {technology['display_name']} has an empty cell")
                break
        check_vertical_alignment(table, errors, f"detail table {technology['display_name']}")
        cols = table.findall("./colgroup/col")
        widths = []
        for col in cols:
            raw_width = col.get("width", "").strip()
            match = re.fullmatch(r"(\d+(?:\.\d+)?)(?:px)?", raw_width)
            widths.append(float(match.group(1)) if match else 0.0)
        if len(widths) != 3 or not all(math.isfinite(width) and width > 0 for width in widths) or widths[2] != max(widths):
            error(errors, f"detail table {technology['display_name']} needs three positive widths with the content column largest")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fetch", type=Path, help="Full JSON emitted by lark-cli docs +fetch")
    source.add_argument("--xml", type=Path, help="Local XML fragment for offline structural checking")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if args.fetch:
            fetched = json.loads(args.fetch.read_text(encoding="utf-8"))
            if isinstance(fetched, dict):
                fetched.pop("_local_only", None)
        else:
            document_id = manifest.get("document_id") if isinstance(manifest, dict) else None
            fetched = {"ok": True, "data": {"document": {"document_id": document_id, "content": args.xml.read_text(encoding="utf-8")}}, "_local_only": True}
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"ERROR: cannot read input: {exc}\n")
    errors = validate(manifest, fetched)
    if errors:
        print("\n".join(errors))
        return 1
    if args.xml:
        print("LOCAL ONLY: validated local HC delivery XML; online numbering, document identity, and whiteboard-token checks were skipped")
    else:
        print("STRUCTURE PASS: fetched HC Feishu structure; PDF semantics and media rendering still require review")
    return 0


if __name__ == "__main__":
    sys.exit(main())
