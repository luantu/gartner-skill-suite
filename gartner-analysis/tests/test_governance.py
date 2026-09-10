import re
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1].parent
GARTNER_SKILLS = sorted(SKILLS_ROOT.glob("gartner-*"))


def _local_refs(skill_dir: Path) -> set[str]:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    refs = set(re.findall(r"\[[^\]]+\]\(([^)#]+)\)", text))
    refs.update(re.findall(r"(?<![\w/])references/[A-Za-z0-9_.-]+\.md", text))
    return {ref for ref in refs if not ref.startswith(("http://", "https://", "#"))}


def test_declared_local_references_resolve_from_each_skill():
    missing = []
    for skill_dir in GARTNER_SKILLS:
        for ref in _local_refs(skill_dir):
            if not (skill_dir / ref).exists():
                missing.append(f"{skill_dir.name}: {ref}")
    assert not missing, "unresolved local references: " + ", ".join(missing)


def test_router_covers_translation_and_all_public_modes():
    router = (SKILLS_ROOT / "gartner-analysis" / "SKILL.md").read_text(encoding="utf-8")
    for skill_name in (
        "gartner-report-extraction",
        "gartner-pdf-zh-translation",
        "gartner-hype-cycle-analysis",
        "gartner-annual-comparison",
        "gartner-magic-quadrant-analysis",
        "gartner-hc-mq-insight",
        "gartner-structured-presentation",
    ):
        assert f"`{skill_name}`" in router


def test_extraction_does_not_claim_translation():
    text = (SKILLS_ROOT / "gartner-report-extraction" / "SKILL.md").read_text(
        encoding="utf-8"
    ).lower()
    assert "translate" not in text
    assert "翻译" not in text


def test_protocol_names_are_unique_across_gartner_skills():
    names: dict[str, list[Path]] = {}
    for skill_dir in GARTNER_SKILLS:
        for path in (skill_dir / "references").glob("*.md"):
            names.setdefault(path.name, []).append(path)
    duplicates = {
        name: paths for name, paths in names.items() if len(paths) > 1
    }
    assert not duplicates, "duplicate reference basenames: " + ", ".join(
        sorted(duplicates)
    )


def test_hc_owns_annual_mode_and_compatibility_alias_is_thin():
    hc = (SKILLS_ROOT / "gartner-hype-cycle-analysis" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    alias = (SKILLS_ROOT / "gartner-annual-comparison" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "annual-hc" in hc
    assert "gartner-hype-cycle-analysis" in alias
    assert len(alias.splitlines()) <= 35


def test_router_prompt_matches_route_table():
    yaml = (SKILLS_ROOT / "gartner-analysis" / "agents" / "openai.yaml").read_text(
        encoding="utf-8"
    )
    prompt = yaml.split("default_prompt:", 1)[1].split("\n", 1)[0]
    for term in ("提炼", "翻译", "HC", "MQ", "年度对比", "交叉洞察", "结构化呈现"):
        assert term in prompt


def test_specialist_invocation_policies_are_explicit():
    expected = {
        "gartner-analysis": True,
        "gartner-pdf-zh-translation": True,
        "gartner-report-extraction": False,
        "gartner-hype-cycle-analysis": False,
        "gartner-annual-comparison": False,
        "gartner-magic-quadrant-analysis": False,
        "gartner-hc-mq-insight": False,
        "gartner-structured-presentation": False,
    }
    for skill_name, allow_implicit in expected.items():
        yaml = (SKILLS_ROOT / skill_name / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        assert f"allow_implicit_invocation: {'true' if allow_implicit else 'false'}" in yaml


def test_cross_insight_is_domain_neutral_and_networking_is_opt_in():
    skill = (SKILLS_ROOT / "gartner-hc-mq-insight" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "domain_profile" in skill
    assert "通信设备方案厂商" not in skill
    networking = SKILLS_ROOT / "gartner-hc-mq-insight" / "references" / "domain-networking.md"
    assert networking.is_file()


def test_handoff_contract_is_present():
    contract = (
        SKILLS_ROOT
        / "gartner-analysis"
        / "references"
        / "routing-and-parameters.md"
    )
    assert contract.is_file()
    text = contract.read_text(encoding="utf-8")
    for field in (
        "report_type",
        "mode",
        "source_reports",
        "output_root",
        "target_vendor",
        "domain_profile",
        "evidence_status",
    ):
        assert field in text
