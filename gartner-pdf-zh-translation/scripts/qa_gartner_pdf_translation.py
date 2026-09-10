#!/usr/bin/env python3
"""Check structural invariants of a translated Gartner PDF."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import fitz


def page_signature(page):
    return {
        "rect": [round(v, 2) for v in (page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1)],
        "rotation": page.rotation,
        "images": len(page.get_images(full=True)),
        "links": len(page.get_links()),
    }


def normalized_text(text: str) -> str:
    """Collapse PDF whitespace so NBSP and line-wraps compare consistently."""
    return re.sub(r"\s+", " ", text).strip()


def source_profile_titles(page) -> list[str]:
    """Return profile item names immediately preceding each source Analysis By line."""
    lines = [normalized_text(line) for line in page.get_text("text").splitlines()]
    lines = [line for line in lines if line]
    titles = []
    for idx, line in enumerate(lines):
        if re.match(r"^Analysis\s+By\s*:", line, re.IGNORECASE) and idx:
            title = lines[idx - 1]
            if title not in {
                "On the Rise", "At the Peak", "Sliding into the Trough",
                "Climbing the Slope", "Entering the Plateau",
            }:
                titles.append(title)
    return titles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("translated", type=Path)
    ap.add_argument("--audit", type=Path, default=None)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()
    src = fitz.open(args.source)
    dst = fitz.open(args.translated)
    report = {
        "source": str(args.source.resolve()),
        "translated": str(args.translated.resolve()),
        "source_pages": len(src), "translated_pages": len(dst),
        "page_count_equal": len(src) == len(dst),
        "pages": [], "font_issues": [], "marker_issues": [], "empty_pages": [],
        "number_issues": [], "analysis_by_issues": [], "technical_item_issues": [],
        "status": "pass",
    }
    if len(src) != len(dst):
        report["status"] = "fail"
    for i, (sp, dp) in enumerate(zip(src, dst), 1):
        ss, ds = page_signature(sp), page_signature(dp)
        item = {"page": i, "source": ss, "translated": ds,
                "geometry_equal": ss["rect"] == ds["rect"] and ss["rotation"] == ds["rotation"],
                "images_equal": ss["images"] == ds["images"],
                "links_equal": ss["links"] == ds["links"]}
        report["pages"].append(item)
        if not item["geometry_equal"] or not item["images_equal"] or not item["links_equal"]:
            report["status"] = "fail"
        text = dp.get_text("text")
        normalized_dst = normalized_text(text)
        if not text.strip():
            report["empty_pages"].append(i)
            report["status"] = "fail"
        if re.search(r"ZZ(?:P|END|TERM)\d+", text, re.I):
            report["marker_issues"].append(i)
            report["status"] = "fail"
        # Analysis By is a fixed Gartner metadata label. Any Chinese variant
        # or a count mismatch indicates that a model changed a protected field.
        source_analysis_count = len(re.findall(r"Analysis\s+By\s*:", sp.get_text("text"), re.I))
        translated_analysis_count = len(re.findall(r"Analysis\s+By\s*:", text, re.I))
        chinese_variants = re.findall(r"(?:分析师|分析者|分析人员|分析人|分析作者)\s*[：:]", text)
        if source_analysis_count != translated_analysis_count or chinese_variants:
            report["analysis_by_issues"].append({
                "page": i,
                "source_count": source_analysis_count,
                "translated_count": translated_analysis_count,
                "chinese_variants": chinese_variants,
            })
            report["status"] = "fail"
        # Profile technology item names are source-authoritative English. Check
        # every source title appears verbatim on the corresponding translated page.
        missing_titles = [title for title in source_profile_titles(sp) if title not in normalized_dst]
        if missing_titles:
            report["technical_item_issues"].append({"page": i, "missing": missing_titles})
            report["status"] = "fail"
        # Preserve year, percentages, decimals and Gartner IDs at page level.
        src_nums = set(re.findall(r"(?<![A-Za-z])(?:G\d{7,}|\d{4}|\d+(?:\.\d+)?%)(?![A-Za-z])", sp.get_text("text")))
        dst_text = text
        missing = sorted(n for n in src_nums if n not in dst_text)
        if missing:
            report["number_issues"].append({"page": i, "missing": missing[:30]})
        fonts = dp.get_fonts(full=True)
        if any("Hira" in (f[3] or "") or "Noto" in (f[3] or "") or "CN" in (f[3] or "") for f in fonts):
            pass
        elif re.search(r"[\u3400-\u9fff]", text):
            report["font_issues"].append(i)
            report["status"] = "fail"
    if args.audit:
        audit = args.audit.read_text(encoding="utf-8", errors="replace")
        anchors = [int(x) for x in re.findall(r"^## 原文第 (\d+) 页$", audit, re.M)]
        expected = list(range(1, len(src) + 1))
        report["audit_anchor_count"] = len(anchors)
        report["audit_anchors_contiguous"] = anchors == expected
        if anchors != expected:
            report["status"] = "fail"
    if report["number_issues"]:
        # Some figures are image-only, so report rather than fail automatically.
        report["number_issues_note"] = "数字覆盖需结合图表页人工复核。"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "pages"}, ensure_ascii=False, indent=2))
    print(f"pages_checked={len(report['pages'])}")
    if report["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
