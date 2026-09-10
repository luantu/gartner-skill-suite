import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_VALIDATOR = SKILL_ROOT / "scripts" / "validate_outputs.py"
TRANSLATION_VALIDATOR = SKILL_ROOT / "scripts" / "validate_translation_coverage.py"


def run_script(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def translation(title: str, pages: int = 2) -> str:
    body = [f"# {title}", "", "> 翻译说明：逐页保真翻译。", ""]
    for page in range(1, pages + 1):
        body.extend(
            [
                f"## 原文第 {page} 页",
                "",
                f"本页保留 Gartner G0084000{page}、50% 与 IEEE 802.11bn。",
                "",
            ]
        )
    return "\n".join(body)


def analysis(kind: str) -> str:
    object_name = "HC" if kind == "HC" else "MQ"
    return f"""# Gartner {object_name} 结构化分析

## 1 总结概述

本报告只分析 {object_name}。

## 2 Gartner 年度核心结论

结论见 Gartner 原文「[G001](#ref-g001)」。

## 3 年度变化总览

变化事实。

## 4 完整变化底表

| 对象 | 变化 |
|---|---|
| Example | Changed |

## 5 关键变化详细分析

<!-- change-priority: P0 -->
### 5.1 重大变化

- 变化事实：发生变化。
- Gartner 证据：「[G001](#ref-g001)」
- Gartner 结论：方向明确。
- 外部证据：「[S001](#ref-s001)」「[V001](#ref-v001)」
- 支持程度：一致。
- 限制：仍需观察。
<!-- /change -->

## 6 方法限制

样本有限。

## 7 参考文献

<a id="ref-g001"></a>「G001」Gartner 原始报告，本地 PDF，第 1 页，核心证据片段。

<!-- source-meta: S001 | publisher=IEEE | relationship=independent | canonical=https://example.com/standard -->
<a id="ref-s001"></a>「S001」IEEE 标准，发布者：IEEE。2026，[链接](https://example.com/standard)，核心证据片段。

<!-- source-meta: V001 | publisher=Vendor | relationship=vendor | canonical=https://example.com/vendor -->
<a id="ref-v001"></a>「V001」Vendor 技术文档，发布者：Vendor。2026，[链接](https://example.com/vendor)，核心证据片段。
"""


def analysis_without_major_changes(kind: str) -> str:
    content = analysis(kind)
    start = content.index("<!-- change-priority: P0 -->")
    end = content.index("<!-- /change -->", start) + len("<!-- /change -->")
    return (
        content[:start]
        + "<!-- no-p0-p1: 完整底表复核后，全部变化均归类为 P2/P3。 -->"
        + content[end:]
    )


def insight(target_vendor: str | None = None) -> str:
    headings = [
        "总结概述",
        "HC×MQ 信号映射矩阵",
        "双报告支持的核心趋势",
        "外部证据的支持、修正与反证",
        "行业竞争结构、产品架构与交付模式影响",
        "对行业、用户与厂商的启示",
        "触发条件、领先指标与反向信号",
    ]
    lines = ["# Gartner HC×MQ 交叉洞察与趋势解读", ""]
    for number, heading in enumerate(headings, start=1):
        lines.extend([f"## {number} {heading}", ""])
        if number == 3:
            lines.extend(
                [
                    "<!-- insight: core -->",
                    "### 3.1 核心趋势",
                    "HC 信号：「[G001](#ref-g001)」",
                    "MQ 信号：「[G002](#ref-g002)」",
                    "外部证据：「[S001](#ref-s001)」",
                    "变化机制：<推理> 基于三类证据形成机制判断。",
                    "行业影响：<推理> 竞争结构发生变化。",
                    "行业、用户与厂商启示：<推理> 调整产品与交付重点。",
                    "<!-- /insight -->",
                    "",
                ]
            )
        else:
            lines.extend(["<推理> 基于 HC 与 MQ 证据形成判断。", ""])
    if target_vendor:
        lines.extend([f"## 8 {target_vendor} 对标", "", "<推理> 指定厂商能力差距与行动建议。", ""])
    lines.extend(["## 9 参考文献与分析研判说明", ""])
    lines.extend(
        [
            '<a id="ref-g001"></a>「G001」Gartner HC，本地 PDF，第 1 页。核心证据片段：HC signal。',
            "",
            '<a id="ref-g002"></a>「G002」Gartner MQ，本地 PDF，第 1 页。核心证据片段：MQ signal。',
            "",
            '<!-- source-meta: S001 | publisher=IEEE | relationship=independent | canonical=https://example.com/standard -->',
            '<a id="ref-s001"></a>「S001」IEEE 标准，发布者：IEEE。2026，[链接](https://example.com/standard)。核心证据片段：standard signal。',
        ]
    )
    return "\n".join(lines)


def single_year_analysis(kind: str) -> str:
    return f"""# Gartner {kind} 单年结构化提炼

## 1 总结概述

单年总结。

## 2 Gartner 单年核心结论

结论见「[G001](#ref-g001)」。

## 3 完整结构化底表

| 对象 | 内容 |
|---|---|
| Example | Detail |

## 4 重点内容详细提炼

忠实提炼，不构造年度变化。

## 5 方法限制

单年报告不能用于年度变化判断。

## 6 参考文献

<a id="ref-g001"></a>「G001」Gartner 原始报告，本地 PDF，第 1 页。核心证据片段：single-year signal。
"""


class OutputValidatorTests(unittest.TestCase):
    def make_full_package(self, root: Path) -> None:
        files = {
            "01-HC-2025-中文保真翻译.md": translation("HC 2025"),
            "02-HC-2026-中文保真翻译.md": translation("HC 2026"),
            "03-MQ-2025-中文保真翻译.md": translation("MQ 2025"),
            "04-MQ-2026-中文保真翻译.md": translation("MQ 2026"),
            "05-HC-2025-2026-结构化分析.md": analysis("HC"),
            "06-MQ-2025-2026-结构化分析.md": analysis("MQ"),
            "07-HC-MQ-2025-2026-交叉洞察与趋势解读.md": insight(),
        }
        for name, content in files.items():
            (root / name).write_text(content, encoding="utf-8")

    def test_accepts_complete_seven_document_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_accepts_legacy_cross_insight_heading_and_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "07-HC-MQ-2025-2026-交叉洞察与趋势解读.md"
            legacy = path.read_text(encoding="utf-8").replace(
                "对行业、用户与厂商的启示", "对通信设备方案厂商的启示"
            ).replace(
                "行业、用户与厂商启示：", "通信设备方案厂商启示："
            )
            path.write_text(legacy, encoding="utf-8")
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_extra_combined_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            (root / "Gartner-Combined-Summary.md").write_text("# 综合摘要", encoding="utf-8")
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unexpected Markdown", result.stdout + result.stderr)

    def test_rejects_analysis_content_in_translation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "01-HC-2025-中文保真翻译.md"
            path.write_text(path.read_text(encoding="utf-8") + "\n## 趋势解读\n<推理>。", encoding="utf-8")
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("translation contains analysis", result.stdout + result.stderr)

    def test_rejects_vendor_strategy_in_hc_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "05-HC-2025-2026-结构化分析.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\n## 对通信设备方案厂商的启示\n建议投入。\n",
                encoding="utf-8",
            )
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("analysis contains vendor strategy", result.stdout + result.stderr)

    def test_rejects_inline_vendor_strategy_in_hc_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "05-HC-2025-2026-结构化分析.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "本报告只分析 HC。",
                    "通信设备方案厂商应该投入 AI 产品路线图。",
                ),
                encoding="utf-8",
            )
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("analysis contains vendor strategy", result.stdout + result.stderr)

    def test_rejects_reverse_order_vendor_strategy_statement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "05-HC-2025-2026-结构化分析.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "本报告只分析 HC。",
                    "建议通信设备方案厂商投入 AI 产品路线图。",
                ),
                encoding="utf-8",
            )
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("analysis contains vendor strategy", result.stdout + result.stderr)

    def test_rejects_mq_content_in_hc_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "05-HC-2025-2026-结构化分析.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "本报告只分析 HC。",
                    "Magic Quadrant 的 Leaders 象限也说明了这一点。",
                ),
                encoding="utf-8",
            )
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("HC analysis contains MQ content", result.stdout + result.stderr)

    def test_rejects_chinese_hc_terms_in_mq_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "06-MQ-2025-2026-结构化分析.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "本报告只分析 MQ。",
                    "该技术处于期望膨胀期，主流采用年限缩短。",
                ),
                encoding="utf-8",
            )
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("MQ analysis contains HC content", result.stdout + result.stderr)

    def test_rejects_incomplete_core_insight_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "07-HC-MQ-2025-2026-交叉洞察与趋势解读.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "变化机制：<推理> 基于三类证据形成机制判断。\n",
                    "",
                ),
                encoding="utf-8",
            )
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("core insight 1 missing field", result.stdout + result.stderr)

    def test_rejects_empty_core_insight_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "07-HC-MQ-2025-2026-交叉洞察与趋势解读.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "行业影响：<推理> 竞争结构发生变化。",
                    "行业影响：   ",
                ),
                encoding="utf-8",
            )
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("core insight 1 empty field", result.stdout + result.stderr)

    def test_rejects_duplicate_external_source_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "05-HC-2025-2026-结构化分析.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "publisher=Vendor | relationship=vendor | canonical=https://example.com/vendor",
                    "publisher=IEEE | relationship=vendor | canonical=https://example.com/standard",
                ),
                encoding="utf-8",
            )
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("external sources are not independent", result.stdout + result.stderr)

    def test_rejects_source_meta_canonical_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "05-HC-2025-2026-结构化分析.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "[链接](https://example.com/vendor)",
                    "[链接](https://example.com/standard)",
                ),
                encoding="utf-8",
            )
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("canonical URL does not match", result.stdout + result.stderr)

    def test_rejects_invalid_source_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "05-HC-2025-2026-结构化分析.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "relationship=independent",
                    "relationship=friendly",
                ),
                encoding="utf-8",
            )
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid relationship", result.stdout + result.stderr)

    def test_rejects_reversed_years(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2026",
                "2025",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ascending order", result.stdout + result.stderr)

    def test_allows_vendor_section_only_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "07-HC-MQ-2025-2026-交叉洞察与趋势解读.md"
            path.write_text(insight("Example Networking Vendor"), encoding="utf-8")

            without_vendor = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(without_vendor.returncode, 0)
            self.assertIn("target vendor section", without_vendor.stdout + without_vendor.stderr)

            with_vendor = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
                "--target-vendor",
                "Example Networking Vendor",
            )
            self.assertEqual(with_vendor.returncode, 0, with_vendor.stdout + with_vendor.stderr)

    def test_accepts_hc_pair_partial_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "01-HC-2025-中文保真翻译.md").write_text(translation("HC 2025"), encoding="utf-8")
            (root / "02-HC-2026-中文保真翻译.md").write_text(translation("HC 2026"), encoding="utf-8")
            (root / "05-HC-2025-2026-结构化分析.md").write_text(analysis("HC"), encoding="utf-8")
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "hc",
                "--years",
                "2025",
                "2026",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_accepts_mq_pair_partial_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "03-MQ-2025-中文保真翻译.md").write_text(translation("MQ 2025"), encoding="utf-8")
            (root / "04-MQ-2026-中文保真翻译.md").write_text(translation("MQ 2026"), encoding="utf-8")
            (root / "06-MQ-2025-2026-结构化分析.md").write_text(analysis("MQ"), encoding="utf-8")
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "mq",
                "--years",
                "2025",
                "2026",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_accepts_single_hc_without_change_sections(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "01-HC-2026-中文保真翻译.md").write_text(translation("HC 2026"), encoding="utf-8")
            (root / "05-HC-2026-单年结构化提炼.md").write_text(single_year_analysis("HC"), encoding="utf-8")
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "single-hc",
                "--years",
                "2026",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_accepts_explicit_no_p0_p1_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "01-HC-2025-中文保真翻译.md").write_text(translation("HC 2025"), encoding="utf-8")
            (root / "02-HC-2026-中文保真翻译.md").write_text(translation("HC 2026"), encoding="utf-8")
            (root / "05-HC-2025-2026-结构化分析.md").write_text(
                analysis_without_major_changes("HC"), encoding="utf-8"
            )
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "hc",
                "--years",
                "2025",
                "2026",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_unsourced_quantitative_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "05-HC-2025-2026-结构化分析.md"
            content = path.read_text(encoding="utf-8").replace(
                "本报告只分析 HC。",
                "市场部署量增长 50%。",
            )
            path.write_text(content, encoding="utf-8")
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsourced quantitative claim", result.stdout + result.stderr)

    def test_rejects_reference_without_core_evidence_excerpt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_full_package(root)
            path = root / "06-MQ-2025-2026-结构化分析.md"
            content = path.read_text(encoding="utf-8").replace(
                "，核心证据片段。",
                "。",
                1,
            )
            path.write_text(content, encoding="utf-8")
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "full",
                "--years",
                "2025",
                "2026",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing core evidence excerpt", result.stdout + result.stderr)

    def test_accepts_single_mq_without_change_sections(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "03-MQ-2026-中文保真翻译.md").write_text(translation("MQ 2026"), encoding="utf-8")
            (root / "06-MQ-2026-单年结构化提炼.md").write_text(single_year_analysis("MQ"), encoding="utf-8")
            result = run_script(
                OUTPUT_VALIDATOR,
                str(root),
                "--mode",
                "single-mq",
                "--years",
                "2026",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class TranslationCoverageTests(unittest.TestCase):
    def test_accepts_page_and_numeric_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            translated = root / "translated.md"
            source.write_text(
                "Page 1 Gartner G00840001 50% IEEE 802.11bn\n"
                "Page 2 Gartner G00840002 20-50% 2026\n",
                encoding="utf-8",
            )
            translated.write_text(translation("样例", pages=2) + "\n20-50% 2026\n", encoding="utf-8")
            result = run_script(
                TRANSLATION_VALIDATOR,
                "--source",
                str(source),
                "--translation",
                str(translated),
                "--expected-pages",
                "2",
                "--term",
                "IEEE 802.11bn",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_rejects_missing_page_and_number(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            translated = root / "translated.md"
            source.write_text("Page 1 50%\nPage 2 2026\n", encoding="utf-8")
            translated.write_text("# 翻译\n\n## 原文第 1 页\n保留 50%。\n", encoding="utf-8")
            result = run_script(
                TRANSLATION_VALIDATOR,
                "--source",
                str(source),
                "--translation",
                str(translated),
                "--expected-pages",
                "2",
            )
            self.assertNotEqual(result.returncode, 0)
            combined = result.stdout + result.stderr
            self.assertIn("missing page anchors", combined)
            self.assertIn("missing numeric tokens", combined)

    def test_rejects_missing_duplicate_numeric_occurrence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            translated = root / "translated.md"
            source.write_text("Page 1 adoption 50% and target 50%\n", encoding="utf-8")
            translated.write_text("# 翻译\n\n## 原文第 1 页\n采用率 50%。\n", encoding="utf-8")
            result = run_script(
                TRANSLATION_VALIDATOR,
                "--source",
                str(source),
                "--translation",
                str(translated),
                "--expected-pages",
                "1",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing numeric tokens", result.stdout + result.stderr)

    def test_rejects_numbers_mapped_to_wrong_source_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.txt"
            translated = root / "translated.md"
            source.write_text("Page 1 value 10%\nPage 2 value 20%\n", encoding="utf-8")
            translated.write_text(
                "# 翻译\n\n## 原文第 1 页\n数值 20%。\n\n## 原文第 2 页\n数值 10%。\n",
                encoding="utf-8",
            )
            result = run_script(
                TRANSLATION_VALIDATOR,
                "--source",
                str(source),
                "--translation",
                str(translated),
                "--expected-pages",
                "2",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("page 1", result.stdout + result.stderr)
            self.assertIn("missing numeric tokens", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
