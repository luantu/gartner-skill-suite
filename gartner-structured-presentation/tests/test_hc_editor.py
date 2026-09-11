import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hc_builder', ROOT / 'scripts/build_hc_editor.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
SVG = ROOT / 'tests/fixtures/hc-pair.svg'

class EditorPackagingTests(unittest.TestCase):
    def test_packages_and_preserves_labels_without_overwriting(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'editor.html'
            builder.build(SVG, out)
            text = out.read_text()
            self.assertIn('Example A (2024)', text)
            self.assertIn('Example B — added', text)
            self.assertNotIn('<!-- HC_SVG -->',text)
            with self.assertRaises(FileExistsError):
                builder.build(SVG,out)
    def test_multiple_facets_with_only_two_distinct_years_are_rejected(self):
        extra = '<g id="extra-track" data-hc-year="2024"><path d="M 0 0 L 5 5"/></g>'
        with self.assertRaises(ValueError):
            builder.prepare(SVG.read_text().replace('</svg>', extra + '</svg>'))
    def test_safe_local_style_export_can_be_reopened(self):
        builder.prepare(SVG.read_text().replace('</svg>', '<style>.dynamic-leader{stroke:#98a2b3}</style></svg>'))
    def test_unsafe_css_is_rejected(self):
        for css in ['@import "https://example.com/a.css";', '*{fill:url(https://example.com/a)}', r'*{fill:u\72l(https://example.com/a)}']:
            with self.assertRaises(ValueError):
                builder.prepare(SVG.read_text().replace('</svg>', '<style>'+css+'</style></svg>'))
    def test_missing_second_year_is_rejected(self):
        with self.assertRaises(ValueError):
            builder.prepare(SVG.read_text().replace('data-hc-year="2025"','data-hc-year="2024"'))
    def test_missing_anchor_or_duplicate_key_is_rejected(self):
        for text in [SVG.read_text().replace('data-point-x="360"','data-point-x="NaN"'),
                     SVG.read_text().replace('data-name="a:2025"','data-name="a:2024"')]:
            with self.assertRaises(ValueError): builder.prepare(text)
    def test_script_and_external_resources_are_rejected(self):
        for content in ['<script>alert(1)</script>', '<image href="https://example.com/image.png"/>',
                        '<text onclick="alert(1)">X</text>']:
            with self.assertRaises(ValueError): builder.prepare(SVG.read_text().replace('</svg>',content+'</svg>'))

if __name__ == '__main__': unittest.main()
