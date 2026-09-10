from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
ROUTER = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")


def test_common_requests_have_one_explicit_authoritative_route():
    route_cases = {
        "读取 PDF、提炼": ("gartner-report-extraction", "extract"),
        "中文保真 PDF": ("gartner-pdf-zh-translation", "translate-pdf"),
        "解读单份 Hype Cycle": ("gartner-hype-cycle-analysis", "single-hc"),
        "比较同一 HC 的两个年度版本": ("gartner-hype-cycle-analysis", "annual-hc"),
        "解读单份 Magic Quadrant": ("gartner-magic-quadrant-analysis", "single-mq"),
        "比较同一市场多个 MQ 年度版本": ("gartner-magic-quadrant-analysis", "annual-mq"),
        "交叉洞察": ("gartner-hc-mq-insight", "cross-insight"),
        "章节、表格或飞书呈现稿": ("gartner-structured-presentation", "presentation"),
    }
    for request, (skill, mode) in route_cases.items():
        matching_lines = [
            line
            for line in ROUTER.splitlines()
            if request in line and f"`{skill}`" in line and mode in line
        ]
        assert len(matching_lines) == 1, (request, matching_lines)


def test_annual_comparison_is_only_an_explicit_compatibility_alias():
    assert "`gartner-annual-comparison` 是兼容入口" in ROUTER
    assert "gartner-annual-comparison" not in ROUTER.split("## 共享不变量", 1)[0].replace(
        "`gartner-annual-comparison` 是兼容入口", ""
    )
