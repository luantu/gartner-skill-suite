import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).parents[1]
SKILLS_ROOT = SKILL_ROOT.parent
SPECIALISTS = {
    "gartner-report-extraction": "extract",
    "gartner-hype-cycle-analysis": "Hype Cycle",
    "gartner-magic-quadrant-analysis": "Magic Quadrant",
    "gartner-hc-mq-insight": "交叉洞察",
    "gartner-structured-presentation": "结构化呈现",
}


class SkillStructureTests(unittest.TestCase):
    def test_router_is_concise_and_routes_every_specialist(self):
        router = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(router.split()), 400)
        for skill_name in SPECIALISTS:
            self.assertIn(f"`{skill_name}`", router)

    def test_specialists_have_valid_frontmatter_and_discriminating_scope(self):
        for skill_name, keyword in SPECIALISTS.items():
            path = SKILLS_ROOT / skill_name / "SKILL.md"
            self.assertTrue(path.is_file(), path)
            text = path.read_text(encoding="utf-8")
            self.assertRegex(text, rf"(?m)^name: {re.escape(skill_name)}$")
            self.assertRegex(text, r"(?m)^description: Use when .+")
            self.assertIn(keyword, text)

    def test_feishu_is_optional_and_markdown_remains_source(self):
        router = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        protocol = (SKILL_ROOT / "references" / "analysis-feishu-output.md").read_text(encoding="utf-8")
        presentation = (SKILLS_ROOT / "gartner-structured-presentation" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("默认先输出并验证 Markdown", router)
        self.assertIn("只有用户明确要求", protocol)
        self.assertIn("禁止 `overwrite`", protocol)
        self.assertIn("feishu-doc-optimizer", protocol)
        self.assertIn("feishu-doc-optimizer", presentation)

    def test_document_wide_parallel_information_uses_real_bullets(self):
        protocol = (SKILL_ROOT / "references" / "analysis-feishu-output.md").read_text(encoding="utf-8")
        presentation = (SKILLS_ROOT / "gartner-structured-presentation" / "references" / "presentation-contract.md").read_text(encoding="utf-8")
        optimizer_path = SKILLS_ROOT / "feishu-doc-optimizer" / "SKILL.md"
        texts = [protocol, presentation]
        if optimizer_path.is_file():
            texts.append(optimizer_path.read_text(encoding="utf-8"))
        for text in texts:
            self.assertIn("全文", text)
            self.assertIn("并列信息容器", text)
            self.assertIn("[Gartner 原文]", text)
            self.assertIn("真实 `<ul><li>`", text)
            self.assertIn("分号", text)

    def test_structured_presentation_has_mq_and_hc_contracts(self):
        protocol = (SKILLS_ROOT / "gartner-structured-presentation" / "references" / "presentation-contract.md").read_text(encoding="utf-8")
        for term in ["关键变化", "Top 5", "厂商变化", "持续存在技术", "Priority Matrix", "技术线索分析"]:
            self.assertIn(term, protocol)
        self.assertIn("最多 5", protocol)

    def test_hc_technology_detail_table_keeps_columns_semantically_aligned(self):
        protocol = (SKILLS_ROOT / "gartner-structured-presentation" / "references" / "presentation-contract.md").read_text(encoding="utf-8")
        self.assertIn("| **Technology (English)** | 技术 | **Technology (English)** |", protocol)
        self.assertIn("|  | 技术成熟度 |", protocol)
        self.assertIn("|  | 优先级矩阵 |", protocol)
        self.assertIn("|  | 市场渗透率 |", protocol)
        self.assertIn("|  | 业务影响 |", protocol)
        self.assertIn("第一列只放技术名称", protocol)
        self.assertIn("第二列只放主题名称", protocol)
        self.assertIn("第三列只放该主题的内容", protocol)
        self.assertIn("不得固定为 `h6`", protocol)
        self.assertIn("表头居中", protocol)
        self.assertIn("单元格垂直居中", protocol)
        self.assertIn("Sample Vendors", protocol)

    def test_mq_contract_requires_two_year_comparison_and_reference_style_blocks(self):
        protocol = (SKILLS_ROOT / "gartner-structured-presentation" / "references" / "presentation-contract.md").read_text(encoding="utf-8")
        for term in ["2025 年位置", "2026 年位置", "主要变化", "h4", "h5", "h6", "不得生成年度关键变化"]:
            self.assertIn(term, protocol)

    def test_mq_position_table_and_vendor_analysis_table_are_separate(self):
        protocol = (SKILLS_ROOT / "gartner-structured-presentation" / "references" / "presentation-contract.md").read_text(encoding="utf-8")
        self.assertIn("关键变化章节内", protocol)
        self.assertIn("1.2 厂商分析章节", protocol)
        self.assertIn("厂商 | 总结 | 优势 | 劣势", protocol)
        self.assertIn("不得合并两张表", protocol)

    def test_mq_change_heading_is_directly_numbered_1_1(self):
        protocol = (SKILLS_ROOT / "gartner-structured-presentation" / "references" / "presentation-contract.md").read_text(encoding="utf-8")
        skill = (SKILLS_ROOT / "gartner-structured-presentation" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`1.1 关键变化`", protocol)
        self.assertNotIn("1.1 关键变化洞察", protocol)
        self.assertIn("去除“关键变化洞察”标题", skill)


if __name__ == "__main__":
    unittest.main()
