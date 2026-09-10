import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "hc_delivery_validator", ROOT / "scripts" / "validate_hc_delivery.py"
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def manifest():
    return {
        "years": [2024, 2025],
        "source_reports": [
            {"year": 2024, "technologies": ["Alpha", "Beta"]},
            {"year": 2025, "technologies": ["Alpha", "Beta"]},
        ],
        "technologies": [
            {
                "id": "alpha",
                "display_name": "Alpha",
                "names": {"2024": "Alpha", "2025": "Alpha"},
                "detail": True,
            },
            {
                "id": "beta",
                "display_name": "Beta",
                "names": {"2024": "Beta", "2025": "Beta"},
                "detail": False,
                "exclusion_reason": "证据不足，保留在年度总览。",
            },
        ],
        "blocks": {
            "summary_table": "summary-table",
            "overview_table": "overview-table",
            "summary_board": "summary-board",
            "comparison_board": "comparison-board",
        },
        "source_figures": [
            {"block_id": "hc-2024", "year": 2024, "kind": "hype-cycle", "page": 1},
            {"block_id": "pm-2024", "year": 2024, "kind": "priority-matrix", "page": 2},
            {"block_id": "hc-2025", "year": 2025, "kind": "hype-cycle", "page": 1},
            {"block_id": "pm-2025", "year": 2025, "kind": "priority-matrix", "page": 2},
        ],
        "document_id": "doc-1",
    }


TOPICS = [
    "技术", "技术成熟度", "优先级矩阵", "市场渗透率", "定义", "为什么重要",
    "业务影响", "驱动力", "障碍", "用户建议", "供应商",
]


def detail_rows():
    first = (
        f'<tr><td rowspan="{len(TOPICS)}" vertical-align="middle">Alpha</td>'
        f'<td vertical-align="middle">{TOPICS[0]}</td>'
        '<td vertical-align="middle">内容<a href="#ref-g001">[G001]</a></td></tr>'
    )
    rest = "".join(
        f'<tr><td vertical-align="middle">{topic}</td>'
        '<td vertical-align="middle">内容<a href="#ref-g001">[G001]</a></td></tr>'
        for topic in TOPICS[1:]
    )
    return first + rest


def xml():
    return f'''<document id="doc-1">
<title>合成 HC 报告</title>
<h1 id="summary" seq-marker="1.">洞察总结</h1>
<callout id="summary-callout"><p>总结<a href="#ref-g001">[G001]</a></p></callout>
<table id="summary-table"><thead><tr><th>分类</th><th>技术布局结论</th><th>未来规模应用窗口期</th><th>未来重点技术趋势</th></tr></thead><tbody><tr><td>重点</td><td>关注</td><td>2–5 年</td><td>趋势</td></tr></tbody></table>
<whiteboard id="summary-board" token="board-summary"/>
<h1 id="insights" seq-marker="2">技术线索分析</h1>
<h2 id="clues" seq-marker="2.1">线索总结</h2><p>年度线索。</p>
<h2 id="details" seq-marker="2.2">技术线索分析</h2>
<h3 id="overview" seq-marker="2.2.1">年度对比总览</h3>
<whiteboard id="comparison-board" token="board-comparison"/>
<grid><column><img id="hc-2024" src="synthetic-hc-2024"/><img id="pm-2024" src="synthetic-pm-2024"/></column><column><img id="hc-2025" src="synthetic-hc-2025"/><img id="pm-2025" src="synthetic-pm-2025"/></column></grid>
<table id="overview-table"><thead><tr><th>技术</th><th>2025年变化相比2024</th><th>关键变化</th><th>变化解读</th></tr></thead><tbody><tr><td>Alpha</td><td>持平</td><td>变化</td><td>解读</td></tr><tr><td>Beta</td><td>新增</td><td>变化</td><td>解读</td></tr></tbody></table>
<h3 id="alpha" seq-marker="2.2.2">Alpha</h3>
<callout id="alpha-callout"><p>洞察<a href="#ref-g001">[G001]</a></p></callout>
<table id="alpha-table"><colgroup><col width="140"/><col width="190"/><col width="688"/></colgroup><thead><tr><th>技术</th><th>主题</th><th>内容</th></tr></thead><tbody>{detail_rows()}</tbody></table>
<h1 id="limits" seq-marker="3">方法与限制</h1><p>限制。</p>
<h1 id="references" seq-marker="4">参考文献</h1><p id="ref-g001">来源。</p>
</document>'''


def fetched(content=None, document_id="doc-1"):
    return {"ok": True, "data": {"document": {"document_id": document_id, "content": content or xml()}}}


class HcDeliveryValidatorTests(unittest.TestCase):
    def test_accepts_numbered_online_delivery(self):
        self.assertEqual([], validator.validate(manifest(), fetched()))

    def test_rejects_missing_overview_technology(self):
        content = xml().replace('<tr><td>Beta</td><td>新增</td><td>变化</td><td>解读</td></tr>', '')
        errors = validator.validate(manifest(), fetched(content))
        self.assertTrue(any("overview_table" in error and "Beta" in error for error in errors), errors)

    def test_rejects_misaligned_detail_table(self):
        content = xml().replace('rowspan="11"', 'rowspan="10"')
        errors = validator.validate(manifest(), fetched(content))
        self.assertTrue(any("rowspan" in error for error in errors), errors)

    def test_rejects_missing_native_numbering_online(self):
        content = xml().replace(' seq-marker="2.1"', '')
        errors = validator.validate(manifest(), fetched(content))
        self.assertTrue(any("seq-marker" in error for error in errors), errors)

    def test_rejects_board_without_token_online(self):
        content = xml().replace(' token="board-comparison"', '')
        errors = validator.validate(manifest(), fetched(content))
        self.assertTrue(any("comparison_board" in error and "token" in error for error in errors), errors)

    def test_rejects_image_without_loaded_resource(self):
        errors = validator.validate(manifest(), fetched(xml().replace(' src="synthetic-hc-2024"', '')))
        self.assertTrue(any("loaded image resource" in e for e in errors), errors)

    def test_rejects_fetch_for_a_different_document(self):
        errors = validator.validate(manifest(), fetched(document_id="doc-other"))
        self.assertTrue(any("document_id" in error for error in errors), errors)

    def test_rejects_broken_gartner_anchor(self):
        content = xml().replace('href="#ref-g001"', 'href="#missing"')
        errors = validator.validate(manifest(), fetched(content))
        self.assertTrue(any("Gartner citation" in error for error in errors), errors)

    def test_accepts_split_and_merged_source_names(self):
        data = manifest()
        data["source_reports"] = [
            {"year": 2024, "technologies": ["Alpha Legacy"]},
            {"year": 2025, "technologies": ["Alpha A", "Alpha B"]},
        ]
        data["technologies"] = [{
            "id": "alpha", "display_name": "Alpha",
            "names": {"2024": ["Alpha Legacy"], "2025": ["Alpha A", "Alpha B"]},
            "detail": True,
        }]
        content = xml().replace('<tr><td>Beta</td><td>新增</td><td>变化</td><td>解读</td></tr>', '')
        self.assertEqual([], validator.validate(data, fetched(content)))

    def test_accepts_5g_detail_heading_without_a_manual_number(self):
        data = manifest()
        data["source_reports"] = [
            {"year": 2024, "technologies": ["5G", "Beta"]},
            {"year": 2025, "technologies": ["5G", "Beta"]},
        ]
        data["technologies"][0]["display_name"] = "5G"
        data["technologies"][0]["names"] = {"2024": "5G", "2025": "5G"}
        self.assertEqual([], validator.validate(data, fetched(xml().replace("Alpha", "5G"))))

    def test_accepts_protocol_overview_heading_format(self):
        content = xml().replace("2025年变化相比2024", "2025 年变化（相比于 2024 年）")
        self.assertEqual([], validator.validate(manifest(), fetched(content)))

    def test_reports_bad_manifest_and_fetch_without_crashing(self):
        self.assertTrue(validator.validate({}, fetched()))
        self.assertTrue(validator.validate(manifest(), {"ok": True, "data": None}))
        for field in ("blocks", "document_id", "source_figures"):
            data = manifest()
            data.pop(field)
            self.assertTrue(validator.validate(data, fetched()))

    def test_preserves_standard_numbers_and_rejects_manual_heading_prefix(self):
        for name in ("6G", "802.11be"):
            data = manifest()
            for report in data["source_reports"]:
                report["technologies"][0] = name
            data["technologies"][0]["display_name"] = name
            data["technologies"][0]["names"] = {"2024": name, "2025": name}
            self.assertEqual([], validator.validate(data, fetched(xml().replace("Alpha", name))))
        errors = validator.validate(manifest(), fetched(xml().replace('>洞察总结</h1>', '>1. 洞察总结</h1>')))
        self.assertTrue(any("manual number" in e for e in errors), errors)

    def test_rejects_media_placed_after_references(self):
        media = '<whiteboard id="comparison-board" token="board-comparison"/>'
        content = xml().replace(media, '').replace('</document>', media + '</document>')
        errors = validator.validate(manifest(), fetched(content))
        self.assertTrue(any("comparison_board must precede" in e for e in errors), errors)

    def test_local_xml_does_not_require_document_id_or_clickable_references(self):
        data = manifest()
        data.pop("document_id")
        content = xml().replace('href="#ref-g001"', 'href="#missing"')
        local = {"ok": True, "data": {"document": {"content": content}}, "_local_only": True}
        self.assertEqual([], validator.validate(data, local))

    def test_rejects_blank_native_numbering_and_first_non_h1_heading(self):
        errors = validator.validate(manifest(), fetched(xml().replace('seq-marker="2.1"', 'seq-marker="   "')))
        self.assertTrue(any("seq-marker" in error for error in errors), errors)
        errors = validator.validate(manifest(), fetched(xml().replace('<h1 id="summary"', '<h2 id="summary"', 1).replace('</h1>\n<callout id="summary-callout"', '</h2>\n<callout id="summary-callout"', 1)))
        self.assertTrue(any("first heading" in error for error in errors), errors)

    def test_rejects_empty_exclusion_reason_and_wrong_detail_technology_name(self):
        data = manifest()
        data["technologies"][1]["exclusion_reason"] = " "
        self.assertTrue(any("exclusion_reason" in error for error in validator.validate(data, fetched())), validator.validate(data, fetched()))
        content = xml().replace('rowspan="11" vertical-align="middle">Alpha</td>', 'rowspan="11" vertical-align="middle">Third Party</td>', 1)
        errors = validator.validate(manifest(), fetched(content))
        self.assertTrue(any("technology cell" in error for error in errors), errors)

    def test_rejects_incomplete_or_undeclared_overview_rows_and_bad_widths(self):
        content = xml().replace('<tr><td>Beta</td><td>新增</td><td>变化</td><td>解读</td></tr>', '<tr><td>Alpha</td><td></td><td>变化</td><td>解读</td></tr>')
        errors = validator.validate(manifest(), fetched(content))
        self.assertTrue(any("overview_table" in error and ("empty" in error or "duplicate" in error) for error in errors), errors)
        errors = validator.validate(manifest(), fetched(xml().replace('width="140"', 'width="-100"')))
        self.assertTrue(any("widths" in error for error in errors), errors)

    def test_local_xml_skips_online_only_numbering_and_board_tokens(self):
        content = xml().replace(' seq-marker="1"', '').replace(' seq-marker="2"', '').replace(' seq-marker="2.1"', '').replace(' seq-marker="3"', '').replace(' seq-marker="4"', '').replace(' token="board-summary"', '').replace(' token="board-comparison"', '')
        local = {"ok": True, "data": {"document": {"document_id": "doc-1", "content": content}}, "_local_only": True}
        self.assertEqual([], validator.validate(manifest(), local))


if __name__ == "__main__":
    unittest.main()
