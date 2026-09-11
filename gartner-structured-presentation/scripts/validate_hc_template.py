#!/usr/bin/env python3
"""Check edited SVG against its template, input facts and declared display policy.

This is the chart gate; document structure validation is a separate gate.
Label positions may change. Annual point and migration geometry may not.
"""
from pathlib import Path
import argparse, hashlib, json, tempfile, re
from lxml import etree as E
from build_hc_template import build
from build_hc_editor import prepare

def visual(n):
    attrs={k:v for k,v in n.attrib.items() if not k.startswith('data-') and k!='class' and not k.endswith('}space')}
    return E.QName(n).localname, attrs, (n.text or '').strip(), [visual(c) for c in n if isinstance(c.tag,str)]

def check(svg_path, mapping_path):
    m=json.loads(Path(mapping_path).read_text())
    for key in ('template_svg','template_html','source_data'):
        if hashlib.sha256(Path(m[key]).read_bytes()).hexdigest()!=m[key+'_sha256']:
            raise ValueError('Input changed after generation: '+key)
    with tempfile.TemporaryDirectory() as d:
        build(m['source_data'],d,m['subject'],m['years'],m['source_edges'],m['template_svg'],m['template_html'],'stage-relative-v1')
        expected=E.parse(str(Path(d)/'hc-comparison.svg')).getroot()
    text=Path(svg_path).read_text();prepare(text)
    actual=E.fromstring(text.encode())
    def nodes(r,q):return r.xpath(q)
    def one(r,i):
        result=r.xpath('.//*[@id=$i]',i=i)
        if len(result)!=1:raise ValueError('Missing or duplicate group: '+i)
        return result[0]
    for group in ['figure_1','axes_1']:
        if one(actual,group).get('transform')!=one(expected,group).get('transform'):raise ValueError('Template ancestor transform changed: '+group)
    if actual.get('viewBox')!=expected.get('viewBox'):raise ValueError('Template viewBox changed')
    for i in [f'line2d_{v}' for v in range(1,9)]+['legend_1','legend_2']:
        if visual(one(actual,i))!=visual(one(expected,i)):raise ValueError('Template geometry, colour or legend changed: '+i)
    selectors=['.//*[@data-year and @data-technology]', './/*[@class="annual-connector"]']
    for q in selectors:
        aa=nodes(actual,q);ee=nodes(expected,q)
        if {n.get('id') for n in aa}!={n.get('id') for n in ee}:raise ValueError('Point or migration coverage differs')
        for n in ee:
            a=one(actual,n.get('id'))
            if visual(a)!=visual(n):raise ValueError('Annual symbol, position or migration changed: '+n.get('id'))
            for k in ['data-year','data-technology','data-adoption','data-source-normalized-x','data-source-normalized-y','data-x','data-y']:
                if a.get(k)!=n.get(k):raise ValueError('Annual source metadata changed: '+str(n.get('id')))
    def labels(r):return {n.get('data-name'):n for n in r.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," tech-label ")]')}
    aa,ee=labels(actual),labels(expected)
    if aa.keys()!=ee.keys():raise ValueError('Technology label coverage differs')
    for key,n in ee.items():
        a=aa[key]
        if re.sub(r'\s+',' ',''.join(a.itertext())).strip()!=re.sub(r'\s+',' ',''.join(n.itertext())).strip():raise ValueError('Source technology name changed: '+key)
        for k in ['style','data-source-name','data-point-x','data-point-y']:
            if a.get(k)!=n.get(k):raise ValueError('Label colour or source anchor changed: '+key)
    if actual.xpath('.//*[@id="selectionRect" or contains(@class,"editor-hit-path") or contains(concat(" ",normalize-space(@class)," ")," selected ")]'):raise ValueError('Editor helpers remain in export')
    result={'status':'pass','tracks':2,'technologies':len(aa),'annual_markers':len(nodes(actual,selectors[0])),'migration_relations':len(nodes(actual,selectors[1])),'svg_sha256':hashlib.sha256(Path(svg_path).read_bytes()).hexdigest(),'browser_visual_check':'required separately'}
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--svg',required=True,type=Path);p.add_argument('--mapping',required=True,type=Path)
    a=p.parse_args();print(json.dumps(check(a.svg,a.mapping),ensure_ascii=False,indent=2))
