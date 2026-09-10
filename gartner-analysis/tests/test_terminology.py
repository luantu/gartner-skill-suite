import json
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = SKILL_ROOT.parent
TERMINOLOGY = SKILL_ROOT / "references" / "analysis-terminology.json"
VALIDATOR = SKILL_ROOT / "scripts" / "validate_terminology.py"


def test_shared_terminology_has_distinct_hc_and_maturity_values():
    data = json.loads(TERMINOLOGY.read_text(encoding="utf-8"))
    assert data["hype_cycle_stages"]["Innovation Trigger"] == "技术萌芽期"
    assert data["maturity"]["Embryonic"] == "萌芽"
    assert data["hype_cycle_stages"]["Innovation Trigger"] != data["maturity"]["Embryonic"]


def test_translator_loads_shared_terminology_file():
    translator = (
        SKILLS_ROOT / "gartner-pdf-zh-translation" / "scripts" / "translate_gartner_pdf.py"
    ).read_text(encoding="utf-8")
    assert "analysis-terminology.json" in translator
    assert "PHASE_BILINGUAL" in translator


def test_active_resources_pass_terminology_validator():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_protected_technology_terms_are_present_in_shared_glossary():
    data = json.loads(TERMINOLOGY.read_text(encoding="utf-8"))
    protected = data["protected_technology_terms"]
    for term in (
        "CPO",
        "LPO",
        "OBO",
        "NPO",
        "OCS",
        "QKD",
        "NaaS",
        "SD-WAN",
        "Photonic AI Interconnect",
        "Network Digital Twin",
        "AI Network Fabric",
        "Supplemental Coverage From Space (SCS)",
        "Coffee Shop Networking",
        "Identity-First Security",
        "Postquantum Cryptography",
    ):
        assert term in protected


def test_forbidden_literal_translations_are_blocked():
    data = json.loads(TERMINOLOGY.read_text(encoding="utf-8"))
    forbidden = data["forbidden_technology_variants"]
    for variant in (
        "封装光网络",
        "共封装光",
        "线性可插拔光",
        "量子密钥分发",
        "网络即服务",
        "软件定义广域网",
        "后量子密码学",
        "安全服务边缘",
    ):
        assert variant in forbidden


def test_protocol_requires_original_technology_names():
    protocol = (
        SKILL_ROOT / "references" / "analysis-translation-content-protocol.md"
    ).read_text(encoding="utf-8")
    assert "技术项标题必须保留英文原名" in protocol
    assert "Technology (English)" in protocol
