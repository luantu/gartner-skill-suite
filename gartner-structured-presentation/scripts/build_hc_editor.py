#!/usr/bin/env python3
"""Package a reviewed two-year HC SVG into the portable interactive editor.

This packages presentation data; it does not extract or infer PDF facts.
"""
import argparse
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')


def prepare(svg_text):
    if re.search(r'<!DOCTYPE|<!ENTITY', svg_text, re.I):
        raise ValueError('DTD/entities are not supported')
    root = ET.fromstring(svg_text)
    if root.tag != f'{{{NS}}}svg':
        raise ValueError('Expected an SVG namespace root')
    box = [float(x) for x in root.get('viewBox', '').replace(',', ' ').split()]
    if len(box) != 4 or not all(map(math.isfinite, box)) or min(box[2:]) <= 0:
        raise ValueError('A finite positive viewBox is required')
    ids = set()
    labels, leaders, years = [], {}, set()
    for n in root.iter():
        tag = n.tag.split('}')[-1]
        if tag in {'script', 'foreignObject', 'image', 'style', 'animate', 'set'}:
            raise ValueError(f'Unsupported element: {tag}; use self-contained SVG primitives and inline styles')
        for key, value in n.attrib.items():
            k = key.split('}')[-1].lower()
            if k.startswith('on') or (k in {'href','src'} and not value.startswith('#')):
                raise ValueError('Executable or external resources are not allowed')
            if k == 'style' and re.search(r'@import|javascript:|expression\s*\(', value, re.I):
                raise ValueError('Unsafe SVG style')
            for url in re.findall(r'url\((.*?)\)', value, re.I):
                if not url.strip(' \"\'').startswith('#'):
                    raise ValueError('Only local SVG resource references are allowed')
        ident = n.get('id')
        if ident:
            if ident in ids:
                raise ValueError(f'Duplicate SVG id: {ident}')
            ids.add(ident)
        classes = n.get('class', '').split()
        if 'tech-label' in classes or 'aux-label' in classes:
            if tag != 'text':
                raise ValueError('Editable labels must be SVG text')
            for coordinate in ['x','y']:
                value = float(n.get(coordinate, 'nan'))
                if not math.isfinite(value):
                    raise ValueError('Label coordinates must be finite')
                n.set('data-original-'+coordinate, str(value))
            labels.append(n)
        if 'tech-label' in classes:
            if not n.get('data-name'):
                raise ValueError('Technology labels require a unique data-name')
            for k in ['data-point-x','data-point-y']:
                if not math.isfinite(float(n.get(k, 'nan'))):
                    raise ValueError('Technology leader anchors must be finite')
        if 'dynamic-leader' in classes:
            key = n.get('data-for')
            if not key or key in leaders:
                raise ValueError('Leader data-for must be unique')
            leaders[key] = n
        if n.get('data-hc-year'):
            years.add(n.get('data-hc-year'))
        if n.get('data-geometry-editable') == 'true':
            if not ident:
                raise ValueError('Editable geometry requires a stable id')
            n.set('data-original-transform', n.get('transform',''))
    axes = root.find(f'.//*[@id="axes_1"]')
    if axes is None:
        raise ValueError('Missing axes_1 group')
    if len(years) != 2 or any(not re.fullmatch(r'\d{4}', y) for y in years):
        raise ValueError('Exactly two distinct data-hc-year curve groups are required')
    tech = [n for n in labels if 'tech-label' in n.get('class','').split()]
    keys = [n.get('data-name') for n in labels]
    if not tech or any(not k for k in keys) or len(keys) != len(set(keys)):
        raise ValueError('All labels require distinct data-name values')
    if set(leaders) != {n.get('data-name') for n in tech}:
        raise ValueError('Each technology label requires exactly one matching leader')
    root.set('id','chart')
    root.set('width','100%'); root.set('height','100%')
    root.set('preserveAspectRatio','xMidYMid meet')
    axes.set('class','data-geometry locked')
    return ET.tostring(root, encoding='unicode')


def build(source, output):
    svg = prepare(source.read_text(encoding='utf-8'))
    shell = Path(__file__).resolve().parents[1] / 'assets/hc-editor-shell.html'
    template = shell.read_text(encoding='utf-8')
    if template.count('<!-- HC_SVG -->') != 1:
        raise ValueError('Editor template must have exactly one SVG slot')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as f:
        f.write(template.replace('<!-- HC_SVG -->',svg))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--svg', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        build(args.svg, args.output)
    except (ValueError, ET.ParseError, OSError) as exc:
        parser.exit(1, f'ERROR: {exc}\n')
    print(f'Created editable HTML: {args.output}')
