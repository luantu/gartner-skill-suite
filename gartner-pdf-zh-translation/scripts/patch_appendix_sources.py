#!/usr/bin/env python3
"""Reflow translated Source: Gartner lines on landscape appendix pages."""
from __future__ import annotations
import importlib.util, json, re
from pathlib import Path
import fitz
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tp',HERE/'translate_gartner_pdf.py');tp=importlib.util.module_from_spec(spec);spec.loader.exec_module(tp)

def prep(text):
    text=re.sub(r'(?<!\n)\n(?!\n)',' ',text)
    for term in ('Hype Cycle','Zero-Trust','zero-trust','Zero trust','zero trust'):
        text=text.replace(term,f' {term.replace(" ",chr(160))} ')
    for term in tp.PROTECTED_TERMS:
        if ' ' in term: text=text.replace(term,term.replace(' ',chr(160)))
    return re.sub(r' {2,}',' ',text).strip()

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('translated',type=Path);ap.add_argument('cache',type=Path);ap.add_argument('--font',type=Path,required=True);args=ap.parse_args()
    src=fitz.open(args.source);cache=json.loads(args.cache.read_text(encoding='utf-8')); tr={int(p):{int(b):v for b,v in bs.items()} for p,bs in cache.items()}
    tp.HIRA=str(args.font.resolve()); base=args.translated.with_suffix('.base.pdf');tp.build_pdf(args.source,base,tr);doc=fitz.open(base)
    count=0
    for i,p in enumerate(src,1):
        if p.rect.width <= 700: continue
        for uid,u in enumerate(tp.layout_units(p)):
            if not u['text'].startswith('Source: Gartner'): continue
            text=prep(cache[str(i)][str(uid)]); rect=fitz.Rect(u['bbox']); rect.x1=min(p.rect.width-68, rect.x1+120); rect.y1=min(p.rect.height-5,rect.y1+12)
            page=doc[i-1]; page.add_redact_annot(rect,fill=None);page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,graphics=0,text=fitz.PDF_REDACT_TEXT_REMOVE)
            color,size,_=tp.color_tuple(u)
            for scale in (0.82,0.76,0.70,0.64):
                res=page.insert_textbox(rect,text,fontname='CN',fontfile=str(args.font),fontsize=max(8.5,size*scale),color=color,lineheight=1.1,overlay=True)
                if res>=-0.05: break
            count+=1
    out=args.translated.with_suffix('.patched.pdf');doc.save(out,garbage=4,deflate=True);doc.close();src.close();base.unlink(missing_ok=True);out.replace(args.translated)
    print('patched source lines',count)
if __name__=='__main__':main()
