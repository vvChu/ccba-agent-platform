"""test_sync_adr_matrix.py - Automated Unit & Governance Tests for Two-Tier ADR Matrix Compiler.

Tests:
1. Metadata parsing from YAML frontmatter, H1 headers, and filename fallbacks.
2. Skill radar cross-reference scanning across skills, workflows, and core docs.
3. Hub-level and Spoke-level Two-Tier Architecture Matrix compilation.
4. Non-destructive section preservation for custom Spoke domain notes & audits.
5. CI gate parity check mode (--check).
6. Environment detection (Hub vs Spoke).

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from scripts.sync_hub_adr_matrix import (
    compile_hub_adr_readme,
    compile_hub_traceability_matrix,
    compile_two_tier_adr_matrix,
    detect_environment,
    extract_preserved_sections,
    load_adrs_from_dir,
    parse_adr_file,
    run_pipeline,
    scan_skill_radar,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_parse_adr_file_frontmatter() -> None:
    """Verify parsing ADR with full YAML frontmatter."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        adr_file = tmp_path / "0042-test-adr.md"
        adr_file.write_text(
            """---
id: "ADR-0042"
title: "Test Architecture Decision with Frontmatter"
status: "ACCEPTED"
date: "2026-08-20"
supersedes: ["ADR-0010"]
---
# ADR 0042: Test Architecture Decision with Frontmatter

## Bối cảnh
Nội dung bối cảnh...
""",
            encoding="utf-8",
        )

        res = parse_adr_file(adr_file)
        assert res["num"] == 42
        assert res["num_str"] == "0042"
        assert res["title"] == "Test Architecture Decision with Frontmatter"
        assert res["status"] == "ACCEPTED"
        assert res["date"] == "2026-08-20"


def test_parse_adr_file_markdown_variations() -> None:
    """Verify parsing ADR from various markdown H1/H2 header patterns."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Variation 1: # 0055. Title format with status list
        f1 = tmp_path / "0055-ai-failover.md"
        f1.write_text(
            """# 0055. CCBA AI Multi-Tier Failover Matrix

* **Status:** Accepted
* **Date:** 2026-09-02
""",
            encoding="utf-8",
        )
        res1 = parse_adr_file(f1)
        assert res1["num"] == 55
        assert res1["num_str"] == "0055"
        assert "CCBA AI Multi-Tier Failover Matrix" in res1["title"]
        assert res1["status"] == "ACCEPTED"
        assert res1["date"] == "2026-09-02"

        # Variation 2: # ADR 0010: Title with Vietnamese status
        f2 = tmp_path / "0010-skills-integration.md"
        f2.write_text(
            """# ADR 0010: Phân Định Ranh Giới Kỹ Năng

## 1. Trạng Thái (Status)
**SUPERSEDED by ADR-0021** (2026-08-10)
""",
            encoding="utf-8",
        )
        res2 = parse_adr_file(f2)
        assert res2["num"] == 10
        assert res2["num_str"] == "0010"
        assert "Phân Định Ranh Giới Kỹ Năng" in res2["title"]
        assert res2["status"] == "SUPERSEDED"


def test_scan_skill_radar() -> None:
    """Verify scanning for ADR cross-references across mock skills and docs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # Setup mock directories
        skill_dir = root / ".agents" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text("Refers to ADR-0001 and ADR 0002.", encoding="utf-8")

        wf_dir = root / ".agents" / "workflows"
        wf_dir.mkdir(parents=True, exist_ok=True)
        (wf_dir / "test-wf.md").write_text("Conforms to ADR 0001.", encoding="utf-8")

        (root / "AGENTS.md").write_text("See ADR-0003 for details.", encoding="utf-8")

        mock_adrs = [
            {
                "num": 1,
                "num_str": "0001",
                "filename": "0001-test.md",
                "title": "T1",
                "status": "ACCEPTED",
            },
            {
                "num": 2,
                "num_str": "0002",
                "filename": "0002-test.md",
                "title": "T2",
                "status": "ACCEPTED",
            },
            {
                "num": 3,
                "num_str": "0003",
                "filename": "0003-test.md",
                "title": "T3",
                "status": "ACCEPTED",
            },
            {
                "num": 4,
                "num_str": "0004",
                "filename": "0004-test.md",
                "title": "T4",
                "status": "ACCEPTED",
            },
        ]

        radar = scan_skill_radar(mock_adrs, root)
        assert len(radar["0001"]) == 2  # skill + workflow
        assert len(radar["0002"]) == 1  # skill
        assert len(radar["0003"]) == 1  # AGENTS.md
        assert len(radar["0004"]) == 0  # no refs


def test_extract_preserved_sections_marker() -> None:
    """Verify non-destructive preservation when explicit markers are present."""
    content = """# Title
## Tier 1
| table |

---
<!-- CUSTOM_SECTIONS_START -->
## 📌 Bảng Đối Soát Quy Chuẩn
| Quy chuẩn | Module |
| :--- | :--- |
| QCVN 06 | pccc |
<!-- CUSTOM_SECTIONS_END -->
"""
    preserved = extract_preserved_sections(content)
    assert "## 📌 Bảng Đối Soát Quy Chuẩn" in preserved
    assert "| QCVN 06 | pccc |" in preserved


def test_extract_preserved_sections_auto_heuristic() -> None:
    """Verify auto-capture heuristic for custom sections without explicit markers."""
    content = """# 🗺️ Living Architecture Traceability Matrix & Skill Radar
## 🏛️ CCBA Platform Architectural Decisions
| ADR | Title | Status |
| :--- | :--- | :--- |
| ADR 0001 | Title 1 | ACCEPTED |

## 📌 Custom Engineering Notes
Ghi chú kỹ thuật quan trọng của Spoke...
"""
    preserved = extract_preserved_sections(content)
    assert "## 📌 Custom Engineering Notes" in preserved
    assert "Ghi chú kỹ thuật quan trọng của Spoke..." in preserved
    assert "CCBA Platform Architectural Decisions" not in preserved


def test_compile_hub_adr_readme_and_matrix() -> None:
    """Verify compilation of Hub README and TRACEABILITY_MATRIX."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        readme_file = tmp_path / "README.md"
        matrix_file = tmp_path / "TRACEABILITY_MATRIX.md"

        hub_adrs = [
            {
                "num": 1,
                "num_str": "0001",
                "filename": "0001-test.md",
                "title": "Test ADR 1",
                "status": "ACCEPTED",
            },
            {
                "num": 2,
                "num_str": "0002",
                "filename": "0002-test.md",
                "title": "Test ADR 2",
                "status": "SUPERSEDED",
            },
        ]

        # Compile README
        readme_content = compile_hub_adr_readme(hub_adrs, readme_file)
        assert "Danh Mục Quyết Định Kiến Trúc (0001 — 0002)" in readme_content
        assert "[HUB-ADR 0001](0001-test.md)" in readme_content
        assert "✅ ACCEPTED" in readme_content
        assert "⚠️ SUPERSEDED" in readme_content

        # Compile TRACEABILITY_MATRIX
        matrix_radar = {"0001": [{"file": "AGENTS.md"}], "0002": []}
        matrix_content = compile_hub_traceability_matrix(
            hub_adrs, matrix_radar, matrix_file, preserved_content="## 📌 Hub Notes"
        )
        assert "CCBA Platform Architectural Decisions" in matrix_content
        assert "`AGENTS.md`" in matrix_content
        assert "*Chưa có liên kết trực tiếp*" in matrix_content
        assert "## 📌 Hub Notes" in matrix_content


def test_load_adrs_from_dir() -> None:
    """Verify loading ADRs from directory ignores README and TRACEABILITY_MATRIX."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        adr_dir = Path(tmp_dir)
        (adr_dir / "0001-alpha.md").write_text("# ADR 0001: Alpha\n", encoding="utf-8")
        (adr_dir / "0002-beta.md").write_text("# ADR 0002: Beta\n", encoding="utf-8")
        (adr_dir / "README.md").write_text("# Readme\n", encoding="utf-8")
        (adr_dir / "TRACEABILITY_MATRIX.md").write_text("# Matrix\n", encoding="utf-8")

        adrs = load_adrs_from_dir(adr_dir)
        assert len(adrs) == 2
        assert [a["num"] for a in adrs] == [1, 2]


def test_detect_environment() -> None:
    """Verify environment detection between Hub and Spoke."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        # Case 1: Spoke with workspace_context.yaml pointing to external hub
        hub_mock = root / "central_hub"
        hub_mock.mkdir(parents=True, exist_ok=True)
        spoke_mock = root / "my_spoke"
        spoke_mock.mkdir(parents=True, exist_ok=True)
        ws_file = spoke_mock / ".md" / "workspace_context.yaml"
        ws_file.parent.mkdir(parents=True, exist_ok=True)
        ws_file.write_text(f"hub_path: {hub_mock}\n", encoding="utf-8")

        mode, detected_hub, detected_spoke = detect_environment(spoke_mock)
        assert mode == "spoke"
        assert detected_hub.resolve() == hub_mock.resolve()
        assert detected_spoke is not None
        assert detected_spoke.resolve() == spoke_mock.resolve()


def test_compile_two_tier_adr_matrix() -> None:
    """Verify compilation of Two-Tier matrix containing Hub Platform ADRs and Spoke Domain ADRs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_file = Path(tmp_dir) / "TRACEABILITY_MATRIX.md"

        hub_adrs = [
            {
                "num": 1,
                "num_str": "0001",
                "filename": "0001-hub-base.md",
                "title": "Hub Base ADR",
                "status": "ACCEPTED",
            }
        ]
        spoke_adrs = [
            {
                "num": 1,
                "num_str": "0001",
                "filename": "0001-domain-prov.md",
                "title": "Domain Provenance ADR",
                "status": "ACCEPTED",
            }
        ]
        hub_matrix = {"0001": [{"file": "AGENTS.md"}]}
        spoke_matrix = {"0001": [{"file": ".agents/skills/legal-ingest/SKILL.md"}]}

        compiled = compile_two_tier_adr_matrix(
            hub_adrs,
            spoke_adrs,
            hub_matrix,
            spoke_matrix,
            out_file,
            preserved_content="## 📌 Preserved Spoke Custom Table",
        )

        assert "## 🏛️ Tier 1 — Platform Constitution (Hub ADRs)" in compiled
        assert "HUB-ADR 0001" in compiled
        assert "Hub Base ADR" in compiled
        assert "## 🌐 Tier 2 — Domain-Specific Architecture Decisions (Spoke ADRs)" in compiled
        assert "Domain ADR 0001" in compiled
        assert "Domain Provenance ADR" in compiled
        assert "## 📌 Preserved Spoke Custom Table" in compiled
        assert out_file.exists()


def test_run_pipeline_hub_and_spoke() -> None:
    """Verify end-to-end pipeline in both Hub mode and Spoke mode."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        hub_dir = root / "hub"
        spoke_dir = root / "spoke"

        (hub_dir / "docs" / "adr").mkdir(parents=True, exist_ok=True)
        (spoke_dir / "docs" / "adr").mkdir(parents=True, exist_ok=True)

        # Create 1 Hub ADR
        (hub_dir / "docs" / "adr" / "0001-hub-adr.md").write_text(
            "# ADR 0001: Hub Base\n\n## 1. Trạng Thái (Status)\n**ACCEPTED**\n",
            encoding="utf-8",
        )

        # Create 1 Spoke ADR
        (spoke_dir / "docs" / "adr" / "0001-spoke-domain.md").write_text(
            "# ADR 0001: Spoke Domain\n\n## 1. Trạng Thái (Status)\n**ACCEPTED**\n",
            encoding="utf-8",
        )

        # 1. Run Hub pipeline
        success_hub = run_pipeline(hub_dir=hub_dir, spoke_dir=None)
        assert success_hub is True
        assert (hub_dir / "docs" / "adr" / "README.md").exists()
        assert (hub_dir / "docs" / "adr" / "TRACEABILITY_MATRIX.md").exists()

        # 2. Check mode on Hub (should pass)
        check_hub = run_pipeline(hub_dir=hub_dir, spoke_dir=None, check_mode=True)
        assert check_hub is True

        # 3. Run Spoke pipeline
        success_spoke = run_pipeline(hub_dir=hub_dir, spoke_dir=spoke_dir)
        assert success_spoke is True
        spoke_matrix_file = spoke_dir / "docs" / "adr" / "TRACEABILITY_MATRIX.md"
        assert spoke_matrix_file.exists()
        content = spoke_matrix_file.read_text(encoding="utf-8")
        assert "Tier 1 — Platform Constitution" in content
        assert "Tier 2 — Domain-Specific" in content
        assert "Hub Base" in content
        assert "Spoke Domain" in content

        # 4. Check mode on Spoke (should pass)
        check_spoke = run_pipeline(hub_dir=hub_dir, spoke_dir=spoke_dir, check_mode=True)
        assert check_spoke is True


def test_parse_adr_file_with_hub_adr_prefix() -> None:
    """Verify parsing ADR with HUB-ADR frontmatter ID and H1 title."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # 1. Frontmatter with HUB-ADR-0058
        f1 = tmp_path / "HUB-ADR-0058-charter-alignment.md"
        f1.write_text(
            """---
id: "HUB-ADR-0058"
title: "Charter Alignment and Live Mirroring"
status: "ACCEPTED"
date: "2026-09-08"
---
# HUB-ADR 0058: Charter Alignment and Live Mirroring

## 1. Trạng Thái (Status)
**ACCEPTED**
""",
            encoding="utf-8",
        )
        res1 = parse_adr_file(f1)
        assert res1["num"] == 58
        assert res1["num_str"] == "0058"
        assert res1["title"] == "Charter Alignment and Live Mirroring"
        assert res1["status"] == "ACCEPTED"
        assert res1["date"] == "2026-09-08"

        # 2. Markdown H1 with # HUB-ADR 0042:
        f2 = tmp_path / "0042-test.md"
        f2.write_text(
            """# HUB-ADR 0042: Scoped Decision

* **Status:** Accepted
* **Date:** 2026-08-20
""",
            encoding="utf-8",
        )
        res2 = parse_adr_file(f2)
        assert res2["num"] == 42
        assert res2["num_str"] == "0042"
        assert "Scoped Decision" in res2["title"]

        # 3. Markdown H1 with hyphenated headings (# ADR-0021: and # HUB-ADR-0058:)
        f3 = tmp_path / "0021-dual-mode.md"
        f3.write_text(
            """# ADR-0021: Dual-Mode Workspace & BIGBIM Skills Retention

## Status
Accepted — 2026-07-19
""",
            encoding="utf-8",
        )
        res3 = parse_adr_file(f3)
        assert res3["num"] == 21
        assert res3["title"] == "Dual-Mode Workspace & BIGBIM Skills Retention"

        f4 = tmp_path / "0058-hard-completion-lock.md"
        f4.write_text(
            """# HUB-ADR-0058: Hard Completion Lock Pattern

## Status
Accepted
""",
            encoding="utf-8",
        )
        res4 = parse_adr_file(f4)
        assert res4["num"] == 58
        assert res4["title"] == "Hard Completion Lock Pattern"


def test_skill_radar_hub_prefix_isolation() -> None:
    """Verify that scan_skill_radar isolates HUB-ADR-XXXX from Spoke domain ADRs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        skills_dir = root / ".agents" / "skills" / "test-skill"
        skills_dir.mkdir(parents=True, exist_ok=True)

        # Skill referencing both HUB-ADR-0033 and domain ADR-0010
        (skills_dir / "SKILL.md").write_text(
            """---
name: test-skill
conforms_to:
- HUB-ADR-0033
- ADR-0010
---
# Test Skill
References HUB-ADR-0033 for hygiene and ADR-0010 for domain logic.
""",
            encoding="utf-8",
        )

        spoke_adrs = [
            {"num": 33, "num_str": "0033", "filename": "0033-spoke-domain.md", "title": "Spoke 33"},
            {"num": 10, "num_str": "0010", "filename": "0010-spoke-domain.md", "title": "Spoke 10"},
        ]
        hub_adrs = [
            {"num": 33, "num_str": "0033", "filename": "0033-hub-hygiene.md", "title": "Hub 33"},
            {"num": 10, "num_str": "0010", "filename": "0010-hub-rag.md", "title": "Hub 10"},
        ]

        # 1. Spoke mode (is_hub=False): MUST NOT match HUB-ADR-0033 to Spoke ADR 0033!
        spoke_matrix = scan_skill_radar(spoke_adrs, root, is_hub=False)
        assert spoke_matrix["0033"] == [], "Spoke ADR 0033 should NOT be matched to HUB-ADR-0033!"
        assert len(spoke_matrix["0010"]) == 1, "Spoke ADR 0010 should be matched to ADR-0010."

        # 2. Strict Hub mode (scanning Spoke files for Hub ADRs): MUST match HUB-ADR-0033, but MUST NOT match bare ADR-0010!
        hub_matrix_strict = scan_skill_radar(hub_adrs, root, is_hub=True, strict_hub_prefix=True)
        assert len(hub_matrix_strict["0033"]) == 1, (
            "Hub ADR 0033 should be matched to HUB-ADR-0033."
        )
        assert hub_matrix_strict["0010"] == [], (
            "Hub ADR 0010 should NOT match bare ADR-0010 in Spoke context!"
        )

        # 3. Legacy Hub mode (internal Hub repo): matches both HUB-ADR-0033 and legacy bare ADR-0010
        hub_matrix_legacy = scan_skill_radar(hub_adrs, root, is_hub=True, strict_hub_prefix=False)
        assert len(hub_matrix_legacy["0033"]) == 1
        assert len(hub_matrix_legacy["0010"]) == 1


def test_compiled_readme_and_matrix_use_hub_adr_labels() -> None:
    """Verify that generated Hub README and TRACEABILITY_MATRIX use HUB-ADR prefix."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        adr_list = [
            {
                "num": 58,
                "num_str": "0058",
                "filename": "0058-live-collab.md",
                "title": "Live Collaboration",
                "status": "ACCEPTED",
            }
        ]
        matrix = {"0058": [{"file": "AGENTS.md"}]}

        readme_file = tmp_path / "README.md"
        matrix_file = tmp_path / "TRACEABILITY_MATRIX.md"

        readme_content = compile_hub_adr_readme(adr_list, readme_file)
        assert "[HUB-ADR 0058]" in readme_content

        matrix_content = compile_hub_traceability_matrix(adr_list, matrix, matrix_file)
        assert "[HUB-ADR 0058]" in matrix_content
