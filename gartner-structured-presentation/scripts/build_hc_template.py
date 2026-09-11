"""Populate the user's actual SVG and HTML templates with verified annual data.

Track paths, axes, legends, marker paths, palette and editor shell are copied.
Source positions are projected monotonically by stage onto template tracks;
layout coordinates and shift display classes are not Gartner measurements.
"""
from pathlib import Path
from copy import deepcopy
import bisect
import hashlib
import json
import math
import re
from lxml import etree as E

ASSET = Path(__file__).resolve().parents[1]/'assets/hc-two-track-template'
NS = 'http://www.w3.org/2000/svg'
ns = {'s': NS}
def tag(t): return '{'+NS+'}'+t
def add(parent,t,attrs=None,text=None):
    n=E.SubElement(parent,tag(t),{k:str(v) for k,v in (attrs or {}).items()})
    if text is not None:n.text=text
    return n
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def node(root,id):return root.xpath('.//*[@id=$id]',id=id)[0]
def points(path):
    a=[float(x) for x in re.findall(r'-?\d+(?:\.\d+)?',path)]
    return list(zip(a[::2],a[1::2]))
def interp(x,xy):
    i=max(0,min(len(xy)-2,bisect.bisect_right([p[0] for p in xy],x)-1))
    a,b=xy[i:i+2];return a[1]+(x-a[0])*(b[1]-a[1])/(b[0]-a[0]) if b[0]!=a[0] else a[1]

def build(data_path, output, subject, years, source_edges, svg_template=None, html_template=None, shift_policy=None):
    if shift_policy != 'stage-relative-v1':
        raise ValueError('Explicit display policy required: stage-relative-v1; not a Gartner score')
    before, after = years
    if not isinstance(before,int) or not isinstance(after,int) or not 1900 <= before < after <= 2200:
        raise ValueError('Two increasing report years required')
    if len(source_edges)!=6 or any(not math.isfinite(v) for v in source_edges) or any(a>=b for a,b in zip(source_edges,source_edges[1:])):
        raise ValueError('Six finite increasing source track endpoints/stage boundaries required')
    OUT=Path(output); SVG_PATH=Path(svg_template or ASSET/'standard.svg').resolve(); HTML_PATH=Path(html_template or ASSET/'editor.html').resolve(); DATA_PATH=Path(data_path).resolve()
    for name in ['hc-comparison.svg','hc-comparison-editor.html','hc-template-mapping.json']:
        if (OUT/name).exists(): raise FileExistsError(OUT/name)
    data=json.loads(DATA_PATH.read_text())
    seen=set()
    for p in data['chart']['points']:
        key=(p['technology_id'],p['year'])
        if key in seen or p['year'] not in years: raise ValueError('Duplicate point or unexpected year')
        seen.add(key)
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*',p['technology_id']):raise ValueError('Stable slug technology_id required')
        if p['years'] not in ('Less than 2 years','2 to 5 years','5 to 10 years','More than 10 years','Obsolete before plateau'):
            raise ValueError('Unsupported adoption status; provide an explicit reviewed template extension')
        if not all(math.isfinite(p['normalized_plot'][k]) for k in ('x','y')):raise ValueError('Finite source coordinates required')
        if not source_edges[0] <= p['source_pixel']['x'] <= source_edges[-1]:raise ValueError('Point outside source track bounds')
    if not seen or {y for _,y in seen} != set(years):raise ValueError('Both annual point sets required')
    OUT.mkdir(parents=True,exist_ok=True)
    raw_template=SVG_PATH.read_bytes()
    if re.search(br'<!DOCTYPE|<!ENTITY',raw_template,re.I):raise ValueError('DTD/entities are not supported')
    source=E.fromstring(raw_template,parser=E.XMLParser(resolve_entities=False,no_network=True));root=deepcopy(source)
    axes=node(root,'axes_1')
    keep={f'line2d_{i}' for i in range(1,9)}|{f'text_{i}' for i in range(1,7)}
    for child in list(axes):
        if child.get('id') not in keep:axes.remove(child)
    for n in list(root.xpath('.//*[@id="selectionRect" or contains(@class,"editor-hit-path")]')):
        n.getparent().remove(n)
    for n in root.xpath('.//*[@class]'):
        n.set('class',' '.join(c for c in n.get('class').split() if c!='selected'))
    axes.set('class','data-geometry locked')
    # Preserve exact template tracks, including their different geometry.
    tracks={y:node(root,f'line2d_{i}') for y,i in [(before,7),(after,8)]}
    curves={y:points(g[0].get('d')) for y,g in tracks.items()}
    for y,g in tracks.items():g.set('data-hc-year',str(y));g.set('data-template-role','annual-track')
    for t in node(root,'text_42').iter(tag('text')):
        for child in list(t):t.remove(child)
        t.text=f'{subject} Hype Cycle: {before}–{after} Technology Shifts'
        for k in ['data-original-text','data-label-text']:t.attrib.pop(k,None)
    for n in root.xpath('.//*[@id="legend_1" or @id="legend_2"]//*'):
        if n.text: n.text=re.sub(r'2025|2026',lambda m:str({'2025':before,'2026':after}[m[0]]),n.text)
    # Reset uses the user's edited template positions, not the older V7 positions.
    for n in root.xpath('.//*[@data-geometry-editable="true"]'):
        n.set('data-original-transform',n.get('transform',''))
    for n in root.xpath('.//s:text',namespaces=ns):
        n.set('class','aux-label');n.set('data-name',n.getparent().get('id','axis')+':text')
        n.set('data-original-x',n.get('x','0'));n.set('data-original-y',n.get('y','0'))

    data=json.loads(DATA_PATH.read_text());by={}
    for p in data['chart']['points']:by.setdefault(p['technology_id'],{})[p['year']]=p
    shapes={'Less than 2 years':'me008422fc4','2 to 5 years':'m1266f2a81f','5 to 10 years':'mc39a7314f2','More than 10 years':'mb69cddacf1'}
    shape_paths={k:node(source,v).get('d') for k,v in shapes.items()}
    cross=node(source,'ma17723f2b7').get('d')
    font="'DejaVu Sans', 'Bitstream Vera Sans', 'Computer Modern Sans Serif', 'Lucida Grande', 'Verdana', 'Geneva', 'Lucid', 'Arial', 'Helvetica', 'Avant Garde', sans-serif"
    dest_edges=[None,341.13024,468.44928,650.20032,871.6608,None]
    def project(p):
        y=p['year'];raw=p['source_pixel']['x'];xy=curves[y]
        edges=[xy[0][0]]+dest_edges[1:-1]+[xy[-1][0]]
        i=max(0,min(4,bisect.bisect_right(source_edges,raw)-1))
        f=(raw-source_edges[i])/(source_edges[i+1]-source_edges[i])
        x=edges[i]+f*(edges[i+1]-edges[i]);return x,interp(x,xy)
    records=[];labels=[]
    # Arrow classes use source x progression and stage, never display separation.
    for ident,ps in by.items():
        status='continued' if len(ps)==2 else 'new' if after in ps else 'removed'
        dx=abs(ps[after]['normalized_plot']['x']-ps[before]['normalized_plot']['x']) if len(ps)==2 else 0
        zero=len(ps)==2 and ps[before]['normalized_plot']==ps[after]['normalized_plot']
        stage_change=len(ps)==2 and ps[before]['stage']!=ps[after]['stage']
        level=('stable' if zero else 'large' if stage_change or dx>=.12 else 'medium' if dx>=.035 else 'minor') if len(ps)==2 else status
        color={'stable':'#475467','new':'#475467','removed':'#667085','large':'#e43d30','medium':'#f2a900','minor':'#2176c7'}[level]
        coords={y:project(p) for y,p in ps.items()}
        record={'technology_id':ident,'name':next(iter(ps.values()))['name'],'status':status,'shift_class':level,'source_delta_x':dx,'source_stage_changed':stage_change,'same_source_position':zero,'points':[],'migration_drawn':len(ps)==2 and not zero}
        if record['migration_drawn']:
            a,b=coords[before],coords[after]
            opacity,width={'large':(.52,1.092),'medium':(.38,.832),'minor':(.24,.598)}[level]
            # A curved arrow, matching the template. Large shifts are emphasized.
            vx,vy=b[0]-a[0],b[1]-a[1];bend=.18 if level!='large' else -.22
            cx,cy=(a[0]+b[0])/2-vy*bend,(a[1]+b[1])/2+vx*bend
            g=add(axes,'g',{'id':'migration-'+ident,'class':'annual-connector','data-technology':ident,'data-shift-class':level,'data-source-delta-x':dx,'data-geometry-editable':'true','data-original-transform':''})
            add(g,'path',{'d':f'M {a[0]} {a[1]} Q {cx} {cy} {b[0]} {b[1]}','style':f'fill:none;opacity:{opacity};stroke:{color};stroke-width:{width};stroke-linecap:round'})
            if level=='large':
                theta=math.atan2(b[1]-cy,b[0]-cx);tip=(b[0]-4*math.cos(theta),b[1]-4*math.sin(theta))
                left=(tip[0]-3.2*math.cos(theta)+1.6*math.sin(theta),tip[1]-3.2*math.sin(theta)-1.6*math.cos(theta))
                right=(tip[0]-3.2*math.cos(theta)-1.6*math.sin(theta),tip[1]-3.2*math.sin(theta)+1.6*math.cos(theta))
                add(g,'path',{'d':f'M {left[0]} {left[1]} L {tip[0]} {tip[1]} L {right[0]} {right[1]} Z','style':f'fill:{color};opacity:{opacity};stroke:{color};stroke-width:{width}'})
        for year,p in sorted(ps.items()):
            x,y=coords[year]
            g=add(axes,'g',{'id':f'point-{ident}-{year}','data-year':year,'data-technology':ident,'data-adoption':p['years'],'data-x':x,'data-y':y,'data-source-normalized-x':p['normalized_plot']['x'],'data-source-normalized-y':p['normalized_plot']['y'],'data-geometry-editable':'true','data-original-transform':''})
            if p['years']=='Obsolete before plateau':
                add(g,'text',{'x':x,'y':y+3,'text-anchor':'middle','style':f'font-family:{font};font-size:11px;font-weight:700;fill:{color}'},'†')
            else:
                style=f'fill:#ffffff;stroke:{color};stroke-width:{1.5 if status=="removed" else 1.6}' if year==before else f'fill:{color}'
                add(g,'path',{'d':shape_paths[p['years']],'transform':f'translate({x} {y})','style':style})
            if status=='removed':add(g,'path',{'d':cross,'transform':f'translate({x} {y})','style':'fill:#667085;stroke:#667085;stroke-width:1.2'})
            record['points'].append({'year':year,'source_pixel':p['source_pixel'],'normalized_plot':p['normalized_plot'],'display':{'x':x,'y':y},'years':p['years']})
        lp=ps.get(after,ps.get(before));x,y=coords[lp['year']]
        size={'large':10.6,'medium':9.5,'minor':8.7,'new':8,'stable':8,'removed':8.2}[level]
        weight={'large':700,'medium':700,'minor':600,'new':400,'stable':400,'removed':400}[level]
        labelcolor='#344054' if level in ('new','stable') else color
        key=ident+':label'
        leader=add(axes,'path',{'class':'dynamic-leader','data-for':key,'d':f'M {x} {y} L {x+25} {y-25}','style':'fill:none;stroke:#98a2b3;stroke-width:.42;stroke-opacity:.68'})
        style=f'font-weight:{weight};font-size:{size}px;font-family:{font};text-anchor:middle;fill:{labelcolor}'
        if status=='removed':style+=';text-decoration:line-through'
        text=lp['name']+(' †' if any(p['years']=='Obsolete before plateau' for p in ps.values()) else '')
        label=add(axes,'text',{'class':'tech-label','data-name':key,'data-point-x':x,'data-point-y':y,'data-source-name':lp['name'],'x':x+25,'y':y-25,'style':style},text)
        labels.append({'id':ident,'name':text,'x':x,'y':y,'size':size,'weight':weight,'label_key':key})
        records.append(record)
    # Footnotes use the template's existing auxiliary-text typography and palette.
    foot=add(node(root,'figure_1'),'g',{'id':'chart-notes'})
    notes=[
        f'{subject}: {before}–{after}. {len(records)} technologies / {len(seen)} annual markers; source details in accompanying data.',
        'Template tracks show stage-relative placement; track separation is visual only. Shift colours are display classes, not Gartner scores.'
    ]
    if any(p['years']=='Obsolete before plateau' for p in data['chart']['points']):
        notes.append('† Obsolete before plateau: not a year-range shape or annual removal. See annual data for affected technologies.')
    for i,text in enumerate(notes):add(foot,'text',{'class':'aux-label','data-name':f'chart-note-{i}','x':46.9,'y':549+i*10,'style':f'font-size:7px;font-family:{font};fill:#667085'},text)
    # A descriptive record is embedded for audit without altering the template legend.
    desc=add(root,'desc',{'id':'chart-data-description'},'Template projection, source coordinates and display classifications are documented in the accompanying chart data. Same-source-position relationships have no migration arrow.')
    for n in root.xpath('.//s:text[contains(@class,"label")]',namespaces=ns):
        n.set('data-original-x',n.get('x'));n.set('data-original-y',n.get('y'))
    svg=E.tostring(root,encoding='unicode')
    from build_hc_editor import prepare
    prepare(svg)  # Validate security/DOM without changing the template's visual bytes.
    html=HTML_PATH.read_text()
    html=re.sub(r'<title>.*?</title>','<title>HC 双年度曲线编辑器</title>',html,count=1)
    html=html.replace('id="geometryLocked" type="checkbox">','id="geometryLocked" type="checkbox" checked>')
    html=html.replace("editLabel.addEventListener('blur', () => { if (selected && document.activeElement !== applyLabel)","editLabel.addEventListener('blur', e => { if (selected && e.relatedTarget !== applyLabel)")
    html=html.replace("const geometry = !label && !lock.checked ? geometryFromTarget(e.target) : null;", "const geometryCandidate = !label ? geometryFromTarget(e.target) : null; const geometry = geometryCandidate && (!lock.checked || geometryCandidate.dataset.editorRole === 'legend-symbol') ? geometryCandidate : null;")
    html=html.replace("clone.querySelectorAll('.editor-hit-path')", "clone.querySelectorAll('.editor-hit-path,#selectionRect')")
    if "e.target.matches?.('textarea,input" not in html and "e.target.closest?.('textarea,input" not in html:
        html=html.replace("if(!selected || !['ArrowLeft'", "if(e.target.closest?.('textarea,input,[contenteditable]')) return; if(!selected || !['ArrowLeft'")
    html=html.replace('恢复 V7','恢复初始布局').replace('已恢复 V7 初始排版','已恢复初始排版')
    if '<!-- HC_SVG -->' in html:
        if html.count('<!-- HC_SVG -->')!=1:raise ValueError('Exactly one SVG slot required')
        html=html.replace('<!-- HC_SVG -->',svg)
    else:
        start=html.index('<svg ');end=html.index('</svg>',start)+6
        html=html[:start]+svg+html[end:]
    (OUT/'hc-comparison.svg').write_text(svg)
    (OUT/'hc-comparison-editor.html').write_text(html)
    manifest={'template_svg':str(SVG_PATH),'template_svg_sha256':sha(SVG_PATH),'template_html':str(HTML_PATH),'template_html_sha256':sha(HTML_PATH),'source_data':str(DATA_PATH),'source_data_sha256':sha(DATA_PATH),'years':list(years),'subject':subject,'source_edges':source_edges,'projection':'Piecewise monotone source-pixel x mapping at declared source_edges onto unchanged template stage edges and annual curve endpoints. Y interpolated on each original template track. No point collision displacement.','shift_classification':'Presentation-only: unchanged source normalized x/y => stable, no arrow; different source Stage or abs(delta normalized x)>=0.12 => large; >=0.035 => medium; otherwise minor. Not Gartner quantitative scores.','legend_exception':'Template legends preserved; actual years substituted. Obsolete uses dagger and explicit footnote, never removal cross or time-range shape.','technologies':records,'label_inputs':labels}
    (OUT/'hc-template-mapping.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',required=True,type=Path);p.add_argument('--output-dir',required=True,type=Path)
    p.add_argument('--subject',required=True);p.add_argument('--years',nargs=2,required=True,type=int)
    p.add_argument('--source-edges',nargs=6,required=True,type=float)
    p.add_argument('--shift-policy',required=True,choices=['stage-relative-v1'])
    p.add_argument('--svg-template',type=Path);p.add_argument('--html-template',type=Path)
    a=p.parse_args()
    result=build(a.data,a.output_dir,a.subject,a.years,a.source_edges,a.svg_template,a.html_template,a.shift_policy)
    print(json.dumps({'output_dir':str(a.output_dir),'technologies':len(result['technologies']),'status':'generated; browser layout and validation required'}))
