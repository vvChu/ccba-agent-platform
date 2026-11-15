"""test_frontmatter_seam.py - Red/Green tests for PR-2b unified markdown frontmatter seam.

Verifies:
1. Public export of `FRONTMATTER_PATTERN`, `SkillFrontmatterSpec`, `parse_markdown_frontmatter` on `ccba_harness`.
2. Exact parsing of LF, CRLF, multi-line `re.DOTALL`, comments, missing, non-mapping, malformed YAML, and missing PyYAML.
3. Byte-exact preservation in `_tuner_mutator.preserve_yaml_frontmatter` without `yaml.dump`.
4. 3-tier fallback (`ccba_harness` -> `PyYAML` -> pure-stdlib) and sorted ordering in `scripts/spoke/find_skills.py`.
5. `_skill_frontmatter.py` module and AST function length budgets.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

import ccba_harness
from ccba_harness.peer_gate import check_ast_function_length

pytestmark = [pytest.mark.fast, pytest.mark.unit]
_REPO_ROOT = Path(__file__).resolve().parents[3]


def test_ccba_harness_exports_frontmatter_seam() -> None:
    """Verify FRONTMATTER_PATTERN, SkillFrontmatterSpec, and parse_markdown_frontmatter are public seams."""
    for sym in ("FRONTMATTER_PATTERN", "SkillFrontmatterSpec", "parse_markdown_frontmatter"):
        assert sym in ccba_harness.__all__, f"Missing {sym} in ccba_harness.__all__"
        assert hasattr(ccba_harness, sym), f"Missing {sym} attribute on ccba_harness"

    agents_md = (_REPO_ROOT / "packages" / "ccba-harness" / "AGENTS.md").read_text(encoding="utf-8")
    assert "parse_markdown_frontmatter" in agents_md
    assert "SkillFrontmatterSpec" in agents_md


def test_parse_markdown_frontmatter_variants() -> None:
    """Verify SkillFrontmatterSpec fields across LF, CRLF, comments, missing, and error cases."""
    parse_fn = ccba_harness.parse_markdown_frontmatter
    spec_cls = ccba_harness.SkillFrontmatterSpec

    lf_doc = (
        "---\n# comment\nname: ccba-demo\ndescription: >\n  line1\n  line2\n---\n# Heading\nBody"
    )
    spec = parse_fn(lf_doc)
    assert isinstance(spec, spec_cls)
    assert spec.has_frontmatter is True
    assert spec.error is None
    assert spec.metadata["name"] == "ccba-demo"
    assert "line1 line2" in spec.metadata["description"]
    assert (
        spec.raw_block == "---\n# comment\nname: ccba-demo\ndescription: >\n  line1\n  line2\n---"
    )
    assert spec.body == "# Heading\nBody"
    assert "# comment" in spec.raw_yaml

    crlf_doc = "---\r\nname: crlf-skill\r\n---\r\n\r\n# Body\r\n"
    crlf_spec = parse_fn(crlf_doc)
    assert crlf_spec.raw_block == "---\r\nname: crlf-skill\r\n---"
    assert crlf_spec.body == "\r\n# Body\r\n"

    missing_spec = parse_fn("# Plain\nBody")
    assert missing_spec.has_frontmatter is False
    assert missing_spec.metadata == {}
    assert missing_spec.raw_block == ""
    assert missing_spec.body == "# Plain\nBody"
    assert missing_spec.error is None

    bad_yaml_spec = parse_fn("---\nname: [broken\n---\n# Body")
    assert bad_yaml_spec.has_frontmatter is True
    assert bad_yaml_spec.metadata == {}
    assert bad_yaml_spec.error is not None and bad_yaml_spec.error.startswith("YAML_PARSE_ERROR:")

    non_dict_spec = parse_fn("---\n- item1\n- item2\n---\n# Body")
    assert non_dict_spec.has_frontmatter is True
    assert non_dict_spec.metadata == {}
    assert non_dict_spec.error == "NON_MAPPING_FRONTMATTER"

    no_yaml_spec = parse_fn(lf_doc, yaml_module=None)
    assert no_yaml_spec.has_frontmatter is True
    assert no_yaml_spec.error == "YAML_PACKAGE_MISSING"


def test_tuner_mutator_preserves_raw_frontmatter_bytes() -> None:
    """Verify preserve_yaml_frontmatter stitches raw_block byte-for-byte without yaml.dump."""
    from ccba_harness.evals._tuner_mutator import preserve_yaml_frontmatter

    orig = "---\r\n# keep comment\r\nname: sample\r\ndescription: >\r\n  multi line\r\n---\r\n\r\n# Old\r\n"
    edited = "---\r\nname: overwritten\r\n---\r\n# New Heading\r\nBody"
    merged = preserve_yaml_frontmatter(orig, edited)
    assert merged.startswith(
        "---\r\n# keep comment\r\nname: sample\r\ndescription: >\r\n  multi line\r\n---"
    )
    assert "overwritten" not in merged
    assert "# New Heading" in merged


def test_find_skills_three_tier_fallback_and_sorted_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify find_skills.py works with ccba_harness, PyYAML only, or pure stdlib, in sorted order."""
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    import scripts.spoke.find_skills as find_skills_mod

    skills_dir = tmp_path / ".agents" / "skills"
    for folder, sname, desc in (
        ("ccba-zeta", "ccba-zeta", "Zeta tool"),
        ("ccba-alpha", "ccba-alpha", "Alpha tool"),
    ):
        d = skills_dir / folder
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            f'---\nname: "{sname}"\ndescription: {desc}\ncommand: /{sname}\n---\n# {sname}\n',
            encoding="utf-8",
        )

    # Tier 3: Pure stdlib fallback (both ccba_harness and yaml missing)
    import yaml as real_yaml

    monkeypatch.setitem(sys.modules, "ccba_harness", None)
    monkeypatch.setitem(sys.modules, "yaml", None)
    monkeypatch.setattr(find_skills_mod, "yaml", None, raising=False)
    parsed = find_skills_mod.parse_frontmatter(skills_dir / "ccba-alpha" / "SKILL.md")
    assert parsed["name"] == "ccba-alpha"
    assert parsed["description"] == "Alpha tool"
    assert parsed["command"] == "/ccba-alpha"

    # Tier 2: ccba_harness missing, PyYAML available
    monkeypatch.setitem(sys.modules, "yaml", real_yaml)
    monkeypatch.setattr(find_skills_mod, "yaml", real_yaml, raising=False)
    importlib.invalidate_caches()
    parsed_t2 = find_skills_mod.parse_frontmatter(skills_dir / "ccba-zeta" / "SKILL.md")
    assert parsed_t2["name"] == "ccba-zeta"

    # Sorted iteration order regardless of inode ordering
    monkeypatch.setattr(find_skills_mod, "SKILLS_DIRS", [skills_dir])
    find_skills_mod.find_skills("")
    out = capsys.readouterr().out
    assert out.index("ccba-alpha") < out.index("ccba-zeta")


def test_compile_catalog_handles_triple_dash_in_scalar(tmp_path: Path) -> None:
    """Verify compile_catalog.extract_frontmatter handles YAML scalar values containing '---'."""
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    from scripts.governance.compile_catalog import extract_frontmatter

    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(
        '---\nname: ccba-demo\ndescription: "Stage A --- Stage B"\nbundle: _core\n---\n# Body\n',
        encoding="utf-8",
    )
    meta = extract_frontmatter(skill_md)
    assert meta["name"] == "ccba-demo"
    assert meta["description"] == "Stage A --- Stage B"


def test_skill_frontmatter_module_stays_within_budget() -> None:
    """Ensure _skill_frontmatter.py remains <= 450 LOC and <= 50 LOC per function."""
    mod_path = (
        _REPO_ROOT / "packages" / "ccba-harness" / "src" / "ccba_harness" / "_skill_frontmatter.py"
    )
    lines = len(mod_path.read_text(encoding="utf-8").splitlines())
    assert lines <= 450, f"_skill_frontmatter.py exceeded 450 LOC ({lines} LOC)"
    gate = check_ast_function_length([mod_path], max_lines=50)
    assert gate.passed, gate.stdout_tail
