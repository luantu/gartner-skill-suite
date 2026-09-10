#!/usr/bin/env python3
"""Translate a Gartner Hype Cycle PDF into a searchable Chinese PDF.

The source PDF is kept as the visual/vector base. Text blocks are translated,
redacted and written back into the original bounding boxes. Raster figures are
left intact because their technical labels are industry-standard and unsafe to
edit automatically.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import fitz


# PyMuPDF's text writer handles the extracted TrueType face reliably. Direct
# TTC input can render CJK glyphs as tofu on some macOS builds.
HIRA = os.environ.get("GARTNER_CJK_FONT", "/tmp/gartner_probe/hira0.ttf")

# Terms that should remain in their source form. Longer terms come first.
PROTECTED_TERMS = [
    "Peak of Inflated Expectations",
    "Trough of Disillusionment",
    "Slope of Enlightenment",
    "Plateau of Productivity",
    "Innovation Trigger",
    "Years to Mainstream Adoption",
    "Benefit Rating",
    "Analysis By",
    "Zero-Trust Technology",
    "Zero-Trust",
    "zero-trust",
    "Zero trust",
    "zero trust",
    "Hype Cycle",
    "Automated Moving Target Defense",
    "Automated Security Control Assessment",
    "Unmanaged Device Access",
    "CPS Network Cloaking and Segmentation",
    "CPS Secure Remote Access",
    "CPS Protection Platforms",
    "Network Security Microsegmentation",
    "Decentralized Identity",
    "Coffee Shop Networking",
    "Shared Signals Framework",
    "AI-Augmented Backup",
    "AI for Access Administration",
    "Universal ZTNA",
    "Security Service Edge",
    "Machine IAM",
    "Postquantum Cryptography",
    "Crypto-Agility",
    "Endpoint Management",
    "Network Detection and Response",
    "Secure Access Service Edge",
    "Cyber-physical systems",
    "Cyber-physical",
    "Gartner Recommended Reading",
    "Document Revision History",
    "Gartner",
    "ZTNA",
    "NDR",
    "SASE",
    "IAM",
    "PQC",
    "AI-CT",
    "AI",
    "CPS",
    "I&O",
    "IoT",
    "MASQUE",
    "QUIC",
    "CAEP",
    "NIS2",
    "NIS",
    "UDP",
    "XDR",
    "EAI",
    "VDI",
    "DaaS",
    "MFA",
    "CISO",
    "API",
    "GB/T",
    "Enterprise Networking",
    "AI-Native Network Infrastructure",
    "Agentic NetOps",
    "AI Network Fabric",
    "Network AI Assistants",
    "Network Digital Twin",
    "Network Microsegmentation",
    "Supplemental Coverage From Space (SCS)",
    "Supplemental Coverage From Space",
    "OpenRoaming",
    "Postquantum Crypto",
    "Quantum Key Distribution",
    "Quantum Networking",
    "5G Private Mobile Networks",
    "Function Accelerator Cards",
    "Network as a Service",
    "Alternative WAN Backbone Services",
    "Software-Defined Cloud Interconnect",
    "Extended Berkeley Packet Filter",
    "Software for Open Networking in the Cloud",
    "Multicloud Networking",
    "Wi-Fi 7",
    "Wi-Fi 8",
    "802.11be",
    "802.11bn",
    "6G",
    "SCS",
    "LEO",
    "D2D",
    "3GPP",
    "5G NR",
    "AGNTCY",
    "NetOps",
    "NaaS",
    "SONiC",
    "eBPF",
    "IPv6",
    "SD-WAN",
    "MNO",
    "QKD",
    "NAT",
    "MNS",
    # Leadership-specific Gartner profile names and recurring technical terms.
    "Cyber Performance Management",
    "Cyber Performance Management Platforms",
    "AI Cybersecurity Governance",
    "Cybersecurity Third-Party Intelligence",
    "Secure Behavior Management",
    "Security Behavior and Culture Program",
    "Cyber Incident Response Retainer",
    "Cyber Incident Response Retainer Services",
    "Cybersecurity Sovereignty",
    "Geopatriation",
    "Agentic AI Security",
    "AI Literacy",
    "Cyber Risk Quantification",
    "Identity-First Security",
    "Threat Exposure Management",
    "Cybersecurity Platformization",
    "Multipolar Cyber Compliance",
    "Cybersecurity AI Assistants",
    "SaaS Security",
    "Machine IAM",
    "Public Cloud Security",
    "Zero-Trust Strategy",
    # AI and cybersecurity report terminology.
    "Cyberbiosecurity",
    "AI Cybersecurity Governance",
    "Deepfake Detection in Meeting Solutions",
    "Disinformation Security",
    "AI Governance Platforms",
    "Model Context Protocol",
    "AI in Cyber-Risk Management",
    "AI Security Testing",
    "AI SPM",
    "AI Usage Control",
    "AI Gateways",
    "AI Code Security Assistants",
    "Artificial General Intelligence",
    "Composite AI",
    "AI SOC Agents",
    "AI Runtime Defense",
    "AI Literacy",
    "AI TRiSM",
    "Differential Privacy",
    "Software Bill of Materials",
    "Synthetic Data",
    "Data Security Governance",
    "Predictive Modeling for Cybersecurity",
    "Threat Modeling Automation",
    "ML-Based Anomaly Detection",
    "AI network fabric",
    "AI network fabrics",
    "agentic NetOps",
    "Network AI assistants",
    "Network as a Service",
    "Network Sustainability",
    "CPO",
    "LPO",
    "OBO",
    "NPO",
    "OCS",
    "OpenTelemetry",
    "Sovereign Networking",
    "Cross-Cloud Networking",
    "Network Slicing",
    "Multi-Core Fiber",
    "Photonic Interconnect",
]

TERMINOLOGY_PATH = Path(__file__).resolve().parents[2] / "gartner-analysis" / "references" / "analysis-terminology.json"
if not TERMINOLOGY_PATH.is_file():
    raise FileNotFoundError(f"Shared Gartner terminology is missing: {TERMINOLOGY_PATH}")
TERMINOLOGY_DATA = json.loads(TERMINOLOGY_PATH.read_text(encoding="utf-8"))
PROTECTED_TERMS.extend(TERMINOLOGY_DATA.get("protected_technology_terms", []))
PROTECTED_TERMS = sorted(set(PROTECTED_TERMS), key=len, reverse=True)
PHASE_BILINGUAL = {
    english: f"{chinese}（{english}）"
    for english, chinese in TERMINOLOGY_DATA["hype_cycle_stages"].items()
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return text.replace("\xa0", " ").replace("\u00ad", "").replace("\ufb01", "fi").replace("\ufb02", "fl")


def block_text(block: dict) -> str:
    lines = []
    for line in block.get("lines", []):
        lines.append("".join(span.get("text", "") for span in line.get("spans", [])))
    return normalize("\n".join(lines)).strip()


def sorted_text_blocks(page: fitz.Page) -> list[dict]:
    raw = [b for b in page.get_text("dict")["blocks"] if b.get("type") == 0]
    raw.sort(key=lambda b: (round(b["bbox"][1], 2), round(b["bbox"][0], 2)))
    out = []
    for idx, b in enumerate(raw):
        t = block_text(b)
        if t:
            out.append({"id": idx, "text": t, "bbox": b["bbox"], "raw": b})
    return out


def _line_text(line: dict) -> str:
    return normalize("".join(span.get("text", "") for span in line.get("spans", []))).strip()


def _union_bbox(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _unit_from_lines(unit_id: int, source_ids: list[int], lines: list[dict], *, bullet: bool = False) -> dict:
    """Create a layout unit from one or more source PDF text lines.

    Gartner's PDF frequently stores a visual line as a separate text block and
    stores the bullet glyph in that same block.  Keeping the line objects here
    lets us split the bullet from its body and later merge adjacent body lines
    into a single translation unit.
    """
    boxes = [tuple(line["bbox"]) for line in lines]
    text = "\n".join(_line_text(line) for line in lines if _line_text(line))
    raw = {"lines": lines}
    color, size, bold = color_tuple({"raw": raw}) if lines else ((0, 0, 0), 10.0, False)
    return {
        "id": unit_id,
        "source_ids": source_ids,
        "text": text,
        "bbox": _union_bbox(boxes),
        "raw": raw,
        "bullet": bullet,
        "style": (tuple(round(c, 3) for c in color), round(size, 1), bool(bold)),
    }


def layout_units(page: fitz.Page) -> list[dict]:
    """Return paragraph and bullet units in visual reading order.

    Text extracted from the report is often split at every visual line.  Body
    lines with the same left edge and a small vertical gap are merged before
    translation, so the translator sees a complete sentence/paragraph.  A
    bullet-only line is kept as its own non-editable unit.  This prevents the
    translation model from moving or duplicating bullets while retaining their
    exact source geometry.
    """
    blocks = sorted_text_blocks(page)
    body_units: list[dict] = []
    bullet_units: list[dict] = []
    next_id = 0
    for block in blocks:
        lines = block["raw"].get("lines", [])
        body_lines = []
        bullet_lines = []
        for line in lines:
            txt = _line_text(line)
            if txt and re.fullmatch(r"[■•●▪◼]+", txt):
                bullet_lines.append(line)
            else:
                body_lines.append(line)
        if body_lines:
            body_units.append(_unit_from_lines(next_id, [block["id"]], body_lines))
            next_id += 1
        if bullet_lines:
            bullet_units.append(_unit_from_lines(next_id, [block["id"]], bullet_lines, bullet=True))
            next_id += 1

    # Merge only body units.  Use the effective text left edge (rather than the
    # block bbox, which may include a bullet at x=68) and ignore columns whose
    # line spacing indicates a new paragraph or heading.
    columns: dict[float, list[dict]] = {}
    for unit in body_units:
        x0 = min((line["bbox"][0] for line in unit["raw"]["lines"]), default=unit["bbox"][0])
        key = round(x0, 1)
        columns.setdefault(key, []).append(unit)
    merged: list[dict] = []
    for key, units in columns.items():
        units.sort(key=lambda u: (u["bbox"][1], u["bbox"][0]))
        current = None
        for unit in units:
            if current is None:
                current = unit
                continue
            gap = unit["bbox"][1] - current["bbox"][3]
            # A normal visual line gap in these reports is about 1.7pt.  A
            # paragraph/heading gap is usually >= 12pt.  Keep a little margin
            # for PDFs with fractional coordinates.
            if gap <= 4.0 and unit.get("style") == current.get("style"):
                current["source_ids"].extend(unit["source_ids"])
                current["text"] = (current["text"] + " " + unit["text"]).strip()
                current["bbox"] = _union_bbox([current["bbox"], unit["bbox"]])
                current["raw"]["lines"].extend(unit["raw"]["lines"])
            else:
                merged.append(current)
                current = unit
        if current is not None:
            merged.append(current)
    merged.extend(bullet_units)
    merged.sort(key=lambda u: (round(u["bbox"][1], 2), round(u["bbox"][0], 2)))
    # IDs are reassigned after merging to make the cache stable and compact.
    for idx, unit in enumerate(merged):
        unit["id"] = idx
    return merged


def protect(text: str):
    mapping = {}
    counter = 0
    # Protect explicit terms first. Match visual line-break whitespace inside
    # multiword names (PDF extraction often splits a phrase across lines).
    for term in PROTECTED_TERMS:
        words = term.split()
        pattern = r"(?<![A-Za-z0-9])" + r"\s+".join(re.escape(w) for w in words) + r"(?![A-Za-z0-9])"
        if not re.search(pattern, text, flags=re.IGNORECASE):
            continue
        token = f"ZZTERM{counter:04d}ZZ"
        counter += 1
        text = re.sub(pattern, token, text, flags=re.IGNORECASE)
        mapping[token] = term
    # Preserve email addresses and web-like identifiers.
    for match in sorted(set(re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)), key=len, reverse=True):
        token = f"ZZTERM{counter:04d}ZZ"
        counter += 1
        text = text.replace(match, token)
        mapping[token] = match
    return text, mapping


def restore(text: str, mapping: dict[str, str]) -> str:
    for token, term in mapping.items():
        replacement = PHASE_BILINGUAL.get(term, term)
        text = re.sub(re.escape(token), replacement, text, flags=re.IGNORECASE)
    # Guard against common machine-translation errors if a model ignored a token.
    text = text.replace("炒作周期", "Hype Cycle（技术成熟度曲线）")
    text = text.replace("生产力 plateau", "生产成熟期（Plateau of Productivity）")
    text = text.replace("生产力平台期", "生产成熟期（Plateau of Productivity）")
    # Use one report-wide spelling in prose. Keep the named Gartner report
    # phrase "Zero-Trust Technology" in title case.
    title_token = "ZZZEROTRUSTTECHZZ"
    text = text.replace("Zero-Trust Technology", title_token)
    text = re.sub(r"(?<![A-Za-z])zero[ -]trust(?![A-Za-z])", "zero-trust", text, flags=re.IGNORECASE)
    text = text.replace(title_token, "Zero-Trust Technology")
    # Keep Gartner field labels stable when a model redundantly translates a
    # protected label (for example, "Benefit Rating 普及度").
    text = re.sub(r"Benefit Rating\s+(?:普及度|影响|评级|评分)", "Benefit Rating", text)
    text = re.sub(r"Market Penetration\s+(?:市场渗透率|渗透率)", "Market Penetration", text)
    return text


def canonicalize_cached_translation(text: str) -> str:
    """Normalize spelling in a cached translation without touching other terms."""
    title_token = "ZZZEROTRUSTTECHZZ"
    text = text.replace("Zero-Trust Technology", title_token)
    text = re.sub(r"(?<![A-Za-z])zero[ -]trust(?![A-Za-z])", "zero-trust", text, flags=re.IGNORECASE)
    return text.replace(title_token, "Zero-Trust Technology")


def enforce_fixed_gartner_fields(page_data: list[dict], cache: dict[str, dict[str, str]]) -> None:
    """Keep profile metadata and technology item names deterministic.

    Gartner HC profiles put the technology item immediately before the
    ``Analysis By`` metadata line.  Those item names are proper technical
    terms, so they must remain exactly as printed in the source PDF.  The
    metadata label is also fixed to ``Analysis By`` to prevent the model from
    producing variants such as ``分析师`` or ``分析者``.
    """
    for page in page_data:
        page_cache = cache.setdefault(str(page["page"]), {})
        blocks = page["blocks"]
        for idx, block in enumerate(blocks):
            source_text = re.sub(r"\s+", " ", str(block.get("text", ""))).strip()
            if not re.search(r"^Analysis By\s*:", source_text, flags=re.IGNORECASE):
                continue
            page_cache[str(block["id"])] = re.sub(
                r"^Analysis By\s*:", "Analysis By:", source_text, flags=re.IGNORECASE
            )
            if idx == 0:
                continue
            title = blocks[idx - 1]
            title_text = re.sub(r"\s+", " ", str(title.get("text", ""))).strip()
            # The preceding unit is the profile's technology item in Gartner's
            # fixed HC layout. Exclude obvious section/field lines defensively.
            if title_text and title_text not in {"On the Rise", "At the Peak", "Sliding into the Trough", "Climbing the Slope", "Entering the Plateau"}:
                page_cache[str(title["id"])] = title_text


def api_call(payload: dict, model: str, timeout: int = 240) -> str:
    # Google Translate's public GTX endpoint is used only when explicitly
    # selected with --model google-gtx. It keeps the same marker/token
    # contract as the OpenRouter path and requires no credential.
    if model == "google-gtx":
        user_text = ""
        for message in payload.get("messages", []):
            if message.get("role") == "user":
                user_text += str(message.get("content", ""))
        query = urllib.parse.quote(user_text)
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q=" + query
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=min(timeout, 60)) as response:
            data = json.loads(response.read().decode("utf-8"))
        return "".join(part[0] for part in data[0] if part and part[0])
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://codex.local",
            "X-Title": "Gartner PDF Translation",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def parse_json_array(content: str):
    start = content.find("[")
    end = content.rfind("]")
    if start < 0 or end <= start:
        raise ValueError("model did not return a JSON array")
    return json.loads(content[start : end + 1])


def estimate_max_tokens(text: str) -> int:
    """Reserve enough output budget without triggering free-tier precharge.

    OpenRouter may reject a request when its implicit 4096-token reservation is
    larger than the remaining credit, even for a short translation.  A bounded
    estimate keeps ordinary page batches affordable while leaving room for
    Chinese expansion and marker overhead.
    """
    return max(256, min(4096, len(text) // 2 + 160))


def translate_single_block(page_no: int, block: dict, model: str) -> str:
    """Small fallback used when a model drops a marker in a larger batch."""
    protected, mapping = protect(block["text"])
    marker = f"ZZP{page_no:03d}B{block['id']:03d}ZZ"
    end_marker = f"ZZEND{page_no:03d}B{block['id']:03d}ZZ"
    system = (
        "Translate the marked Gartner report block to Simplified Chinese. Return the "
        "start and end markers exactly unchanged, with the translation between them. "
        "Keep every ZZTERM####ZZ token exactly unchanged. Preserve numbers, names, "
        "acronyms, punctuation and meaning. Do not add abbreviations, explanations, parenthetical "
        "text or facts that are not present in the source block. Output only the marked block."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"{marker}\n{protected}\n{end_marker}"},
        ],
        "temperature": 0.05,
        "max_tokens": estimate_max_tokens(protected),
        "reasoning": {"exclude": True},
    }
    last = None
    for attempt in range(4):
        try:
            content = api_call(payload, model)
            match = re.search(re.escape(marker) + r"\s*(.*?)\s*" + re.escape(end_marker), content, flags=re.IGNORECASE | re.DOTALL)
            if not match:
                raise ValueError(f"missing marker pair {marker}")
            translated = match.group(1).strip()
            missing_tokens = [tok for tok in mapping if tok.lower() not in translated.lower()]
            if missing_tokens:
                raise ValueError(f"protected token(s) missing or changed: {missing_tokens[:5]}")
            return restore(translated, mapping)
        except Exception as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"single-block translation failed: {last}")


def translate_batch(batch: list[dict], model: str) -> list[dict]:
    # Each block carries its own protected-term map so restoration is deterministic.
    prepared = []
    maps = {}
    for page in batch:
        pblocks = []
        for b in page["blocks"]:
            protected, mapping = protect(b["text"])
            marker = f"ZZP{page['page']:03d}B{b['id']:03d}ZZ"
            end_marker = f"ZZEND{page['page']:03d}B{b['id']:03d}ZZ"
            pblocks.append((marker, end_marker, protected))
            maps[(page["page"], b["id"])] = mapping
        prepared.append(pblocks)
    marked_text = []
    expected_markers = []
    for page_blocks in prepared:
        for marker, end_marker, protected in page_blocks:
            marked_text.append(f"{marker}\n{protected}\n{end_marker}")
            expected_markers.append((marker, end_marker))
    system = (
        "You are a senior Gartner technical-report translator. Translate the marked "
        "blocks from English to Simplified Chinese. Keep every start marker ZZP###B###ZZ "
        "and matching end marker ZZEND###B###ZZ exactly unchanged and in the same order, "
        "with exactly one translated block between each pair. Do not merge or omit blocks. "
        "Keep every ZZTERM####ZZ token exactly unchanged; it represents an industry-standard "
        "technical term, product, vendor, organization, protocol, standard, acronym, Gartner "
        "term or email address. Preserve all numbers, IDs, footnote markers, names, punctuation, "
        "bullets and paragraph breaks. Do not add abbreviations, explanations, parenthetical text "
        "or facts that are not present in the source block. Translate ordinary prose accurately "
        "and naturally."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": "\n\n".join(marked_text)},
        ],
        "temperature": 0.05,
        "max_tokens": estimate_max_tokens("\n\n".join(marked_text)),
        "reasoning": {"exclude": True},
    }
    last = None
    for attempt in range(4):
        try:
            content = api_call(payload, model)
            result_map = {}
            missing = []
            for marker, end_marker in expected_markers:
                pattern = re.escape(marker) + r"\s*(.*?)\s*" + re.escape(end_marker)
                match = re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL)
                if not match:
                    missing.append(marker)
                    continue
                m = re.fullmatch(r"ZZP(\d{3})B(\d{3})ZZ", marker, flags=re.IGNORECASE)
                if not m:
                    raise ValueError(f"bad marker {marker}")
                key = (int(m.group(1)), int(m.group(2)))
                translated = match.group(1).strip()
                missing_tokens = [tok for tok in maps[key] if tok.lower() not in translated.lower()]
                if missing_tokens:
                    missing.append(marker)
                    continue
                result_map[key] = restore(translated, maps[key])
            if missing:
                # A model occasionally merges adjacent short blocks. Re-translate
                # the complete affected batch one block at a time to avoid loss or
                # accidental duplication.
                result = []
                for p in batch:
                    result.append({
                        "page": p["page"],
                        "blocks": [
                            {"id": b["id"], "translation": translate_single_block(p["page"], b, model)}
                            for b in p["blocks"]
                        ],
                    })
                return result
            result = []
            for p in batch:
                result.append({"page": p["page"], "blocks": [{"id": b["id"], "translation": result_map[(p["page"], b["id"])]} for b in p["blocks"]]})
            return result
        except Exception as exc:
            last = exc
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"translation batch failed: {last}")


def color_tuple(block: dict):
    colors = []
    sizes = []
    bold = False
    for line in block["raw"].get("lines", []):
        for span in line.get("spans", []):
            colors.append(span.get("color", 0))
            sizes.append(float(span.get("size", 10)))
            bold = bold or "bold" in span.get("font", "").lower()
    color = max(set(colors), key=colors.count) if colors else 0
    rgb = (((color >> 16) & 255) / 255, ((color >> 8) & 255) / 255, (color & 255) / 255)
    size = max(sizes) if sizes else 10.0
    return rgb, size, bold


def has_mixed_span_colors(block: dict) -> bool:
    colors = []
    for line in block["raw"].get("lines", []):
        for span in line.get("spans", []):
            colors.append(span.get("color", 0))
    return len(set(colors)) > 1


def build_pdf(source: Path, output: Path, translations: dict[int, dict[int, str]]):
    doc = fitz.open(source)
    for page_index, page in enumerate(doc):
        links = [{k: v for k, v in link.items() if k != "xref"} for link in page.get_links()]
        blocks = layout_units(page)
        # Landscape appendix matrix cells use white and black text on different
        # colored bands. A single replacement color would make some cells vanish;
        # retain those original cell labels to preserve the exact table geometry.
        page_text = page.get_text("text")
        priority_matrix_page = page.rect.width > 700 and (
            "Priority Matrix" in page_text or "Benefit\nYears to Mainstream Adoption" in page_text
        )
        editable_blocks = [
            b for b in blocks
            if not b.get("bullet")
            and not (priority_matrix_page and (
                b["bbox"][1] >= 100 or "Priority Matrix" not in page_text
            ) and b["bbox"][1] <= 500)
            and not (page.rect.width > 700 and has_mixed_span_colors(b))
        ]
        # Remove only text; preserve raster figures, fills, rules and vector graphics.
        for b in editable_blocks:
            page.add_redact_annot(fitz.Rect(b["bbox"]), fill=None)
        if editable_blocks:
            page.apply_redactions(
                images=fitz.PDF_REDACT_IMAGE_NONE,
                graphics=0,
                text=fitz.PDF_REDACT_TEXT_REMOVE,
            )
        for block_pos, b in enumerate(editable_blocks):
            raw_translated = translations.get(page_index + 1, {}).get(b["id"], b["text"])
            text = raw_translated
            # Never carry soft hyphens into the searchable Chinese layer.
            text = text.replace("\u00ad", "")
            # Source line breaks are usually visual wraps rather than paragraph
            # boundaries. Let the Chinese text reflow naturally inside the same box.
            text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
            # Keep Latin technical terms together when adjacent to CJK text.
            for term in ("Hype Cycle", "Zero-Trust", "zero-trust", "Zero trust", "zero trust"):
                glued = term.replace(" ", "\u00a0")
                text = text.replace(term, f" {glued} ")
            for term in PROTECTED_TERMS:
                if " " in term:
                    text = text.replace(term, term.replace(" ", "\u00a0"))
            text = re.sub(r" {2,}", " ", text).strip()
            rect = fitz.Rect(b["bbox"])
            color, fontsize, bold = color_tuple(b)
            # The source line width is optimized for English glyphs.  Give a
            # translated unit the full main-column width before reducing its
            # font, which keeps headings and metadata legible in Chinese.
            if page.rect.width < 700 and rect.x0 >= 60 and rect.x0 < 110:
                rect.x1 = max(rect.x1, page.rect.width - 68)
            elif page.rect.width < 700 and rect.x0 >= 90:
                rect.x1 = max(rect.x1, page.rect.width - 68)
            # Chinese can be a little wider; adapt within the original block.
            # A grouped paragraph may need one extra line, so grow its box into
            # the whitespace before the next visible unit in the same column.
            next_y = None
            for candidate in blocks:
                if candidate is b or candidate.get("bullet"):
                    continue
                if candidate["bbox"][1] <= rect.y1 + 0.1:
                    continue
                x_overlap = min(rect.x1, candidate["bbox"][2]) - max(rect.x0, candidate["bbox"][0])
                if x_overlap > 5:
                    gap = candidate["bbox"][1] - rect.y1
                    if gap >= 0 and (next_y is None or candidate["bbox"][1] < next_y):
                        next_y = candidate["bbox"][1]
            if next_y is not None and next_y - rect.y1 > 2:
                rect.y1 = min(next_y - 1.5, rect.y1 + 18.0)
            # The personal-use notice sits close to the bottom edge.  Chinese
            # glyphs need a little more vertical room at the source 9pt size;
            # use the remaining bottom margin before considering any further
            # fitting adjustments.
            if rect.y1 > page.rect.height - 60:
                rect.y1 = min(page.rect.height - 5, rect.y1 + 18.0)
            inserted = False
            # The footer combines a left-aligned identifier and a right-aligned
            # page label in one text block. Recreate those two original line boxes
            # independently so the right footer remains right aligned.
            if "Gartner" in b["text"] and ("Page " in b["text"] or "of " in b["text"]):
                source_lines = b["raw"].get("lines", [])
                page_match = re.search(r"Page\s+([0-9A-Za-z]+)\s+of\s+([0-9A-Za-z]+)", b["text"])
                if page_match and len(source_lines) >= 2:
                    source_page, source_total = page_match.groups()
                    translated_lines = [f"Gartner, Inc. | {re.search(r'G\d{7,}', b['text']).group(0) if re.search(r'G\d{7,}', b['text']) else ''}", f"第 {source_page} 页，共 {source_total} 页"]
                    for line, line_text in zip(source_lines, translated_lines):
                        line_rect = fitz.Rect(line["bbox"])
                        if "Gartner" in line_text:
                            line_text = line_text.replace("Gartner公司", "Gartner, Inc.")
                            line_rect.x1 += 18
                        else:
                            line_rect.x0 -= 24
                        line_color, line_size, _ = color_tuple({"raw": {"lines": [line]}})
                        align = 2 if line["bbox"][0] > rect.x0 + rect.width * 0.6 else 0
                        for scale in (1.0, 0.92, 0.84, 0.76, 0.68):
                            rc = page.insert_textbox(line_rect, line_text, fontname="CN", fontfile=HIRA,
                                                     fontsize=max(6, line_size * scale), color=line_color, align=align,
                                                     lineheight=1.1, overlay=True)
                            if rc >= -0.05:
                                break
                    inserted = True
            if inserted:
                continue
            # Keep body text at or above 9pt.  If a translated paragraph still
            # does not fit, the expanded rectangle above provides the extra
            # line rather than shrinking it to an unreadable size.
            lineheight = 1.10 if fontsize >= 15.0 else 1.45
            for scale in [1.0, 0.96, 0.92, 0.88, 0.84, 0.80, 0.78]:
                result = page.insert_textbox(
                    rect,
                    text,
                    fontname="CN",
                    fontfile=HIRA,
                    fontsize=max(9.0, fontsize * scale),
                    color=color,
                    lineheight=lineheight,
                    overlay=True,
                )
                if result >= -0.05:
                    inserted = True
                    break
                # Remove the failed text insertion before retrying by redacting its rect.
                page.add_redact_annot(rect, fill=None)
                page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=0, text=fitz.PDF_REDACT_TEXT_REMOVE)
            if not inserted:
                # Last-resort insertion at a reduced size; keep the content searchable.
                page.insert_textbox(rect, text, fontname="CN", fontfile=HIRA, fontsize=9.0, color=color, lineheight=lineheight, overlay=True)
        for link in links:
            try:
                page.insert_link(link)
            except Exception:
                pass
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output, garbage=4, deflate=True)
    doc.close()
    normalize_pdf_tounicode(output)


def normalize_pdf_tounicode(pdf_path: Path) -> None:
    """Map the ASCII hyphen correctly in the generated ToUnicode CMap."""
    doc = fitz.open(pdf_path)
    changed = False
    for xref in range(doc.xref_length()):
        try:
            stream = doc.xref_stream(xref)
        except Exception:
            continue
        if stream and b"<000e> <00ad>" in stream.lower():
            doc.update_stream(xref, stream.replace(b"<000e> <00ad>", b"<000e> <002d>"))
            changed = True
    if changed:
        temp = pdf_path.with_suffix(".tounicode-fix.pdf")
        doc.save(temp, garbage=4, deflate=True)
        doc.close()
        os.replace(temp, pdf_path)
    else:
        doc.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--batch-pages", type=int, default=2)
    parser.add_argument("--batch-blocks", type=int, default=4,
                        help="Maximum non-bullet layout units per model request")
    parser.add_argument("--model", default="tencent/hy-mt2-30b-a3b")
    parser.add_argument("--font", type=Path, default=None, help="Embedded CJK TrueType font")
    parser.add_argument("--cache-dir", type=Path, default=None, help="Directory for translation cache")
    args = parser.parse_args()

    source = args.source.resolve()
    outdir = args.output_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    global HIRA
    if args.font:
        HIRA = str(args.font.resolve())
    elif not os.environ.get("GARTNER_CJK_FONT"):
        local_font = outdir / "assets" / "HiraginoSansGB-W3.ttf"
        if local_font.exists():
            HIRA = str(local_font.resolve())
    # v2 cache stores paragraph-level units.  The older translations.json was
    # generated one visual block at a time and can contain duplicated sentence
    # fragments, so it must not be mixed with grouped units.
    cache_dir = (args.cache_dir.resolve() if args.cache_dir else outdir / "assets" / "translation-cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "translations-grouped.json"
    audit_path = outdir / (source.stem + "-translation.md")
    pdf_path = outdir / (source.stem + "-pdf-zh.pdf")

    doc = fitz.open(source)
    page_data = []
    for page_no, page in enumerate(doc, start=1):
        page_data.append({"page": page_no, "blocks": layout_units(page), "has_images": bool(page.get_images(full=True))})
    doc.close()

    cache = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    for page_key, page_values in cache.items():
        if isinstance(page_values, dict):
            for block_key, value in list(page_values.items()):
                if isinstance(value, str):
                    page_values[block_key] = canonicalize_cached_translation(value)
    # Reapply source-authoritative technical item names after generic spelling
    # normalization. This prevents a normalization rule such as ``zero-trust``
    # from changing the title case of ``Zero-Trust Strategy`` or another
    # technology item.
    enforce_fixed_gartner_fields(page_data, cache)
    expected_cache = {str(p["page"]): {str(b["id"]) for b in p["blocks"]} for p in page_data}
    # Bullets are layout glyphs, not language. Seed them into the cache and
    # exclude them from model calls so their source symbols remain untouched.
    for p in page_data:
        page_cache = cache.setdefault(str(p["page"]), {})
        for b in p["blocks"]:
            if b.get("bullet"):
                page_cache[str(b["id"])] = b["text"]
    for start in range(0, len(page_data), args.batch_pages):
        batch = page_data[start : start + args.batch_pages]
        missing = [
            p for p in batch
            if str(p["page"]) not in cache
            or set(cache.get(str(p["page"]), {}).keys()) != expected_cache[str(p["page"])]
        ]
        if missing:
            print(f"Translating physical pages {missing[0]['page']}-{missing[-1]['page']}...", flush=True)
            translate_pages = [
                {**p, "blocks": [b for b in p["blocks"] if not b.get("bullet")]} for p in missing
            ]
            # Split dense pages into small marker batches. This prevents a
            # single long page from hanging a free model while preserving
            # exact block IDs and allowing resume after interruption.
            translated = []
            for page in translate_pages:
                blocks = page["blocks"]
                step = max(1, args.batch_blocks)
                for offset in range(0, len(blocks), step):
                    chunk = {**page, "blocks": blocks[offset:offset + step]}
                    translated.extend(translate_batch([chunk], args.model))
            for p in translated:
                page_cache = cache.setdefault(str(p["page"]), {})
                for b in p["blocks"]:
                    page_cache[str(b["id"])] = b["translation"]
            cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    translations = {int(p): {int(b): t for b, t in blocks.items()} for p, blocks in cache.items()}
    residual = []
    for page_no, blocks in translations.items():
        for block_id, value in blocks.items():
            if re.search(r"ZZTERM\d{4}ZZ", value, flags=re.IGNORECASE):
                residual.append((page_no, block_id))
    if residual:
        raise RuntimeError(f"unrestored protected-term tokens in translation cache: {residual[:10]}")
    build_pdf(source, pdf_path, translations)

    # Auditable page-by-page translation text.
    lines = [
        f"# 中文保真翻译：{source.stem}",
        "",
        f"> 原报告：{source.name}",
        f"> 原文物理页数：{len(page_data)}",
        "> 翻译原则：正文、表格、标题和页脚翻译为简体中文；业界通用技术名、产品名、厂商名、标准、协议、缩写和 Gartner 方法术语保留英文或中英并列；栅格图表保留原图以避免失真。",
        "> 核验状态：已生成 PDF；需对图表栅格内英文标签进行人工确认。",
        "",
    ]
    for p in page_data:
        lines.append(f"## 原文第 {p['page']} 页")
        lines.append("")
        page_trans = translations.get(p["page"], {})
        image_note = "此页含栅格图表：原图保留，图内技术标签按原样保留。"
        if any(page_no == p["page"] for page_no in [q["page"] for q in page_data if q.get("has_images")]):
            lines.append(image_note)
            lines.append("")
        for b in p["blocks"]:
            lines.append(page_trans.get(b["id"], b["text"]))
            lines.append("")
    audit_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"PDF: {pdf_path}")
    print(f"Audit Markdown: {audit_path}")


if __name__ == "__main__":
    main()
