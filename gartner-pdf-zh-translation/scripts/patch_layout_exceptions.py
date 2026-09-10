#!/usr/bin/env python3
"""Repair a few known narrow boxes after PDF text overlay."""
from __future__ import annotations
import importlib.util, json, re
from pathlib import Path
import fitz

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('translate_gartner_pdf', HERE/'translate_gartner_pdf.py')
tp = importlib.util.module_from_spec(spec); spec.loader.exec_module(tp)


def prep(text: str) -> str:
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    for term in ("Hype Cycle", "Zero-Trust", "zero-trust", "Zero trust", "zero trust"):
        text = text.replace(term, f" {term.replace(' ', chr(160))} ")
    for term in tp.PROTECTED_TERMS:
        if " " in term:
            text = text.replace(term, term.replace(" ", chr(160)))
    return re.sub(r" {2,}", " ", text).strip()


def replace_block(page, bbox, text, font_size, color, font, redact_bbox=None):
    links = [{k:v for k,v in l.items() if k != 'xref'} for l in page.get_links()]
    rect = fitz.Rect(bbox)
    redact_rect = fitz.Rect(redact_bbox or bbox)
    page.add_redact_annot(redact_rect, fill=None)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=0, text=fitz.PDF_REDACT_TEXT_REMOVE)
    rect.x1 = max(rect.x1, page.rect.width - 68 if page.rect.width < 700 else rect.x1 + 100)
    rect.y1 = min(page.rect.height - 5, rect.y1 + 18)
    txt = prep(text)
    for scale in (1.0, .94, .88, .82, .76):
        result = page.insert_textbox(rect, txt, fontname='CN', fontfile=str(font),
                                     fontsize=max(8.5, font_size*scale), color=color,
                                     lineheight=1.35 if font_size < 15 else 1.1,
                                     overlay=True)
        if result >= -0.05:
            break
        page.add_redact_annot(rect, fill=None)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=0, text=fitz.PDF_REDACT_TEXT_REMOVE)
    for link in links:
        try: page.insert_link(link)
        except Exception: pass


def insert_only(page, bbox, text, font_size, color, font):
    rect = fitz.Rect(bbox)
    rect.x1 = max(rect.x1, page.rect.width - 68 if page.rect.width < 700 else rect.x1 + 100)
    rect.y1 = min(page.rect.height - 5, rect.y1 + 18)
    txt = prep(text)
    for scale in (1.0, .94, .88, .82, .76):
        result = page.insert_textbox(rect, txt, fontname='CN', fontfile=str(font),
                                     fontsize=max(8.5, font_size*scale), color=color,
                                     lineheight=1.35 if font_size < 15 else 1.1,
                                     overlay=True)
        if result >= -0.05:
            return


def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('source',type=Path); ap.add_argument('translated',type=Path); ap.add_argument('cache',type=Path); ap.add_argument('--font',type=Path,required=True); args=ap.parse_args()
    src=fitz.open(args.source); cache=json.loads(args.cache.read_text(encoding='utf-8'))
    translations={int(p):{int(b):v for b,v in bs.items()} for p,bs in cache.items()}
    # Always rebuild from the immutable source before applying exceptions, so
    # a retry never layers new text on top of a previously patched PDF.
    base=args.translated.with_suffix('.base.pdf')
    tp.HIRA=str(args.font.resolve())
    tp.build_pdf(args.source, base, translations)
    doc=fitz.open(base)
    targets = {(1,8):10.5, (15,13):10.0, (63,11):9.5}
    overrides = {
        (63, 11): "SDCI 是连接多个云服务提供商并持续管理此类连接的最灵活私有方式。\n到2028年底，30%的大型企业将使用SDCI服务连接公共云服务提供商，\n而2024年这一比例不足15%。"
    }
    for page_no in (110,112,113):
        for idx,u in enumerate(tp.layout_units(src[page_no-1])):
            if u['text'].startswith('Source: Gartner'):
                targets[(page_no,idx)] = 9.0
    for (page_no, unit_id), size in targets.items():
        units=tp.layout_units(src[page_no-1]); u=units[unit_id]
        text=overrides.get((page_no, unit_id), cache[str(page_no)][str(unit_id)])
        color, source_size, _ = tp.color_tuple(u)
        redact_bbox = {
            (15, 13): (60, 530, 540, 650),
            (63, 11): (88, 515, 540, 610),
            (103, 17): (60, 610, 540, 650),
        }.get((page_no, unit_id))
        replace_block(doc[page_no-1], u['bbox'], text, min(size, source_size), color, args.font, redact_bbox)
    u = tp.layout_units(src[102])[17]
    color, source_size, _ = tp.color_tuple(u)
    insert_only(doc[102], u['bbox'], cache['103']['17'], 9.5, color, args.font)
    patched=args.translated.with_suffix('.patched.pdf')
    doc.save(patched, garbage=4, deflate=True)
    doc.close(); src.close(); base.unlink(missing_ok=True)
    patched.replace(args.translated)
    print(f'patched {len(targets)} boxes')

if __name__=='__main__': main()
