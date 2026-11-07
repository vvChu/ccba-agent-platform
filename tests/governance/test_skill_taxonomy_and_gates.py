"""test_skill_taxonomy_and_gates.py - Governance Tests for Skills Hierarchy & CI Gates (ADR-0040).

Verifies:
1. Real workspace satisfies all 4 Hard CI Gates (0 violations).
2. Zero-Duplicate Gate catches duplicate skill names across directories.
3. Context Budget Ceiling Gate catches bundles exceeding 10 model-invoked skills.
4. Description length gate catches model-invoked descriptions > 180 characters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from scripts.governance import DocumentAuditor, SkillAuditor

pytestmark = [pytest.mark.fast, pytest.mark.unit]
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_real_codebase_skill_ci_gates() -> None:
    """Verify that all skills in the platform pass 100% of CI gates and workspace checks."""
    auditor = DocumentAuditor(PROJECT_ROOT)
    skills_dir = PROJECT_ROOT / ".agents" / "skills"
    assert skills_dir.exists()

    # 1. Check individual skills
    skill_files = list(skills_dir.rglob("SKILL.md"))
    assert len(skill_files) > 50, f"Expected >50 skills, found {len(skill_files)}"

    for sf in skill_files:
        issues = auditor.audit_skill(sf)
        assert len(issues) == 0, f"Skill {sf} has issues: {[i.message for i in issues]}"

    # 2. Check workspace-level hard gates
    gate_issues = auditor.audit_workspace_gates(skills_dir)
    assert len(gate_issues) == 0, (
        f"Workspace hard gate violations: {[g.message for g in gate_issues]}"
    )


def test_zero_duplicate_gate_catches_duplicates(tmp_path: Path) -> None:
    """Verify that SkillAuditor flags duplicate skill names across directories."""
    auditor = SkillAuditor(tmp_path)
    skill_a = tmp_path / "skill_a" / "SKILL.md"
    skill_b = tmp_path / "skill_b" / "SKILL.md"
    skill_a.parent.mkdir(parents=True)
    skill_b.parent.mkdir(parents=True)

    skill_a.write_text(
        "---\nname: my-duplicate-skill\ndescription: Test A\nbundle: _core\n---\n# Test A\n",
        encoding="utf-8",
    )
    skill_b.write_text(
        "---\nname: my-duplicate-skill\ndescription: Test B\nbundle: _qc\n---\n# Test B\n",
        encoding="utf-8",
    )

    issues = auditor.audit_workspace_gates(tmp_path)
    dup_issues = [i for i in issues if i.category == "ZERO_DUPLICATE_GATE_VIOLATION"]
    assert len(dup_issues) == 1
    assert "Duplicate skill name 'my-duplicate-skill'" in dup_issues[0].message


def test_context_budget_ceiling_catches_overflow(tmp_path: Path) -> None:
    """Verify that SkillAuditor flags bundles with > 10 model-invoked skills."""
    auditor = SkillAuditor(tmp_path)
    bundle_dir = tmp_path / "overflow_bundle"
    bundle_dir.mkdir(parents=True)

    for i in range(12):
        sf = bundle_dir / f"skill_{i}" / "SKILL.md"
        sf.parent.mkdir(parents=True)
        sf.write_text(
            f"---\nname: skill-{i}\ndescription: Test skill {i}\nbundle: _test_bundle\n---\n# Skill {i}\n",
            encoding="utf-8",
        )

    issues = auditor.audit_workspace_gates(tmp_path)
    overflow_issues = [i for i in issues if i.category == "CONTEXT_BUDGET_CEILING_EXCEEDED"]
    assert len(overflow_issues) == 1
    assert "Bundle '_test_bundle' has 12 model-invoked skills" in overflow_issues[0].message


def test_description_length_limit_on_model_invoked(tmp_path: Path) -> None:
    """Verify that model-invoked skills with descriptions > 180 chars are flagged."""
    auditor = SkillAuditor(tmp_path)
    sf = tmp_path / "SKILL.md"
    long_desc = "A" * 185
    sf.write_text(
        f"---\nname: long-desc-skill\ndescription: {long_desc}\nbundle: _core\n---\n# Long Desc\n",
        encoding="utf-8",
    )

    issues = auditor.audit_skill(sf)
    desc_issues = [i for i in issues if i.category == "DESCRIPTION_TOO_LONG"]
    assert len(desc_issues) == 1
    assert "exceeds 180 character limit" in desc_issues[0].message


def _load_skill_frontmatter(skill_name: str) -> tuple[dict[str, Any], str]:
    """Load YAML frontmatter and full content of a Hub skill."""
    import yaml

    sf = PROJECT_ROOT / ".agents" / "skills" / skill_name / "SKILL.md"
    text = sf.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    fm = yaml.safe_load(parts[1]) or {}
    return fm, text


def test_collision_cluster_descriptions_and_exclusions() -> None:
    """Verify COND-01 & COND-02: <=180 char descriptions and one-way exclusions."""
    collision_skills = [
        "ccba-ai-qc",
        "ccba-ai-qc-pccc-audit",
        "ccba-ai-pdf-preprocessor",
        "ccba-markdown-document-processing",
        "ccba-legal-advisor",
        "ccba-legal-document-tracker",
        "ccba-legal-intel",
        "ccba-legal-ingest",
        "bigbim-vbpl-digest",
        "ccba-ai-gateway-sdk",
        "ccba-llm-pipeline-patterns",
    ]
    for name in collision_skills:
        fm, _ = _load_skill_frontmatter(name)
        desc = str(fm.get("description", ""))
        assert 50 <= len(desc) <= 180, f"{name} description len={len(desc)} violates <=180 cap"
        assert "Không dùng" in desc, f"{name} description missing explicit exclusion clause"

    advisor_fm, _ = _load_skill_frontmatter("ccba-legal-advisor")
    advisor_triggers = [str(t).lower() for t in advisor_fm.get("triggers", [])]
    assert "pccc" not in advisor_triggers, "ccba-legal-advisor must not overlap 'pccc' trigger"

    intel_fm, _ = _load_skill_frontmatter("ccba-legal-intel")
    intel_triggers = [str(t).lower() for t in intel_fm.get("triggers", [])]
    assert "crawl law" not in intel_triggers, (
        "ccba-legal-intel must not overlap 'crawl law' trigger"
    )


_ROUTING_STOPWORDS = {
    "cho",
    "của",
    "các",
    "vào",
    "qua",
    "khi",
    "cần",
    "với",
    "bằng",
    "hoặc",
    "không",
    "dùng",
    "văn",
    "bản",
    "tài",
    "liệu",
    "hồ",
    "sơ",
    "quy",
    "định",
    "pháp",
    "luật",
    "lý",
    "xây",
    "dựng",
    "trình",
    "toàn",
    "mới",
    "từ",
    "để",
    "và",
}

COLLISION_CLUSTERS: dict[str, list[str]] = {
    "qc": ["ccba-ai-qc", "ccba-ai-qc-pccc-audit"],
    "pdf_md": ["ccba-ai-pdf-preprocessor", "ccba-markdown-document-processing"],
    "legal": [
        "ccba-legal-advisor",
        "ccba-legal-document-tracker",
        "ccba-legal-intel",
        "ccba-legal-ingest",
        "bigbim-vbpl-digest",
    ],
    "spark_ai": ["ccba-ai-gateway-sdk", "ccba-vllm-manager"],
    "rag_pipeline": ["ccba-llm-pipeline-patterns", "ccba-hybrid-rag-search"],
}

STAY_OFF_ROUTING_MATRIX: list[tuple[str, str, list[str], list[str]]] = [
    (
        "ccba-ai-qc",
        "qc",
        [
            "Chạy discovery và ghép ảnh quad-view kiểm tra xung đột bản vẽ đa bộ môn qua qcauditpipeline",
            "Điều phối toàn trình bản vẽ đa bộ môn và xuất heat map",
            "Kiểm tra quad-view vision trên hồ sơ bản vẽ đa bộ môn",
        ],
        [
            "Thẩm tra thuyết minh PCCC và lối thoát nạn QCVN 06 bằng semantic map-reduce",
            "Kiểm tra thiết bị chữa cháy và báo cháy TCVN 3890 trong thuyết minh PCCC",
        ],
    ),
    (
        "ccba-ai-qc-pccc-audit",
        "qc",
        [
            "Thẩm tra PCCC chuyên sâu thuyết minh QCVN 06 và MEP thoát nạn qua semantic map-reduce",
            "Chạy pccc audit kiểm tra thiết bị chữa cháy và hệ thống báo cháy TCVN 3890",
            "Rà soát hồ sơ thiết kế PCCC và thiết bị chữa cháy bằng semantic map-reduce",
        ],
        [
            "Điều phối bản vẽ đa bộ môn toàn dự án bằng quad-view vision và heat map",
            "Chạy discovery toàn dự án qua qcauditpipeline cho bản vẽ đa bộ môn",
        ],
    ),
    (
        "ccba-ai-pdf-preprocessor",
        "pdf_md",
        [
            "Chạy preprocessor để phân đoạn segmenting, chunk pdf và tiling bản vẽ lớn cho AI Vision",
            "Tiền xử lý scan pdf phức tạp và cắt tiling bản vẽ lớn cho AI Vision",
            "Phân đoạn segment pdf và chunking bản vẽ lớn trước khi đưa vào AI Vision",
        ],
        [
            "Chuyển đổi tài liệu thông thường từ Word sang Markdown qua ConversionPipeline",
            "Chuẩn hóa markdown và xử lý markdown cho báo cáo thuyết minh Word",
        ],
    ),
    (
        "ccba-markdown-document-processing",
        "pdf_md",
        [
            "Chuyển đổi và chuẩn hóa markdown từ tài liệu thông thường Word qua ConversionPipeline",
            "Thực hiện document processing và xử lý markdown từ file Word thuyết minh",
            "Chuẩn hóa markdown và cấu trúc tài liệu thông thường qua ConversionPipeline",
        ],
        [
            "Phân đoạn segmenting và cắt mảnh tiling bản vẽ lớn cho AI Vision bằng preprocessor",
            "Tiền xử lý scan pdf bản vẽ lớn bằng chunk pdf và tiling bản vẽ cho AI Vision",
        ],
    ),
    (
        "ccba-legal-advisor",
        "legal",
        [
            "Tư vấn giải đáp tình huống và xuất Phiếu Ý kiến Pháp lý trích dẫn OKF v2.4 (tu van phap ly)",
            "Phỏng vấn làm rõ ngữ cảnh dự án để lập legal opinion và phiếu ý kiến pháp lý",
            "Giải đáp tình huống thẩm định dự án và xuất phiếu ý kiến pháp lý (giai dap phap luat)",
        ],
        [
            "Cào và nạp văn bản mới từ TVPL bằng thu thap van ban (ingest law)",
            "Quản lý vòng đời legal_registry.yaml và hợp nhất VBHN qua VBHNEngine",
        ],
    ),
    (
        "ccba-legal-document-tracker",
        "legal",
        [
            "Quản lý vòng đời legal_registry.yaml và hợp nhất văn bản VBHN qua VBHNEngine",
            "So sánh ast diff cũ-mới và cập nhật legal_registry cho văn bản hợp nhất vbhn",
            "Theo dõi vòng đời văn bản trong legal_registry.yaml bằng VBHNEngine",
        ],
        [
            "Phỏng vấn tình huống để lập Phiếu Ý kiến Pháp lý trích dẫn OKF v2.4 (legal opinion)",
            "Thu thập văn bản gốc từ TVPL và chuyển đổi chuẩn OKF v2.4 (ingest law)",
        ],
    ),
    (
        "ccba-legal-intel",
        "legal",
        [
            "Phân tích đồ thị quan hệ (legal graph), tra cứu điều khoản get-clause và sinh checklist tuân thủ",
            "Chạy query get-clause trên đồ thị pháp luật và xuất legal checklist tuân thủ",
            "Tra cứu điều khoản bảng biểu bằng get-clause và phân tích legal graph",
        ],
        [
            "Thu thập văn bản mới từ TVPL và kiểm định 15-Gate CI (thu thap van ban)",
            "Tư vấn tình huống và lập Phiếu Ý kiến Pháp lý (phieu y kien phap ly)",
        ],
    ),
    (
        "ccba-legal-ingest",
        "legal",
        [
            "Thu thập văn bản gốc từ TVPL, chuyển đổi OKF v2.4 và kiểm định 15-Gate CI (thu thap van ban)",
            "Chạy ingest law để nạp văn bản gốc từ TVPL và kiểm định 15-Gate CI",
            "Nạp văn bản mới từ TVPL (nap van ban) và đóng gói chuẩn OKF v2.4 qua 15-Gate CI",
        ],
        [
            "Tư vấn tình huống dự án và xuất Phiếu Ý kiến Pháp lý (tu van phap ly)",
            "Tra cứu điều khoản lẻ bằng get-clause và phân tích đồ thị quan hệ (legal graph)",
        ],
    ),
    (
        "bigbim-vbpl-digest",
        "legal",
        [
            "Tra cứu và tóm lược nghị định BIM (NĐ 175) cùng tiêu chuẩn ISO 19650",
            "Tóm lược điều khoản BIM trong NĐ 175 và quy định nộp BIM theo ISO 19650-1/2/3/5",
            "Rà soát pháp lý BIM Việt Nam (NĐ 175) và tiêu chuẩn ISO 19650",
        ],
        [
            "Tư vấn giải đáp tình huống ngoài phạm vi BIM và lập Phiếu Ý kiến Pháp lý (legal opinion)",
            "Quản lý vòng đời legal_registry.yaml và hợp nhất VBHN ngoài BIM qua VBHNEngine",
        ],
    ),
    (
        "ccba-ai-gateway-sdk",
        "spark_ai",
        [
            "Kết nối AI Gateway trên Server Spark qua Python package ccba-ai",
            "Sử dụng choose_model và ai.chat trong Python package ccba-ai để gọi AI Gateway",
            "Tích hợp Python package ccba-ai kết nối AI Gateway đa mô hình trên Server Spark",
        ],
        [
            "Quản trị máy chủ vLLM và tối ưu hóa AOT Inductor cache trên DGX Blackwell GB10",
            "Cấu hình phân tách reasoning parser và Inductor cache cho máy chủ vLLM",
        ],
    ),
    (
        "ccba-llm-pipeline-patterns",
        "rag_pipeline",
        [
            "Áp dụng anti-patterns và best practices thiết kế LLM processing pipelines (pipeline patterns)",
            "Thiết kế synthesis pipeline và 2-pass self-correction theo VvC LLM OS",
            "Kiểm tra best practices cho llm pipeline và multi turn memory",
        ],
        [
            "Chạy tìm kiếm ngữ nghĩa kết hợp BM25 và Embedding với RRF Fusion (hybrid rag)",
            "Thực hiện tìm kiếm ngữ nghĩa BM25 và Embedding search với độ chính xác 20x",
        ],
    ),
]


def _score_description(query: str, description: str) -> int:
    """Score a user query against a skill description's positive vs exclusion clauses."""
    import re

    parts = description.lower().split("không dùng", 1)
    pos_desc = parts[0]
    neg_desc = parts[1] if len(parts) > 1 else ""
    words = re.findall(
        r"[a-z0-9_àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ-]+",
        query.lower(),
    )
    tokens = [w for w in words if len(w) >= 3 and w not in _ROUTING_STOPWORDS]
    score = 0
    for tok in tokens:
        if tok in pos_desc:
            score += 2
        if neg_desc and tok in neg_desc:
            score -= 3
    return score


def test_collision_cluster_stay_off_routing() -> None:
    """Verify COND-02 & COND-02R: 11 skills x (3 positive + 2 near-miss) = 55 cases on description & triggers."""
    fms = {s: _load_skill_frontmatter(s)[0] for c in COLLISION_CLUSTERS.values() for s in c}
    assert len(STAY_OFF_ROUTING_MATRIX) == 11
    total_cases = 0

    for skill_name, cluster_id, positives, near_misses in STAY_OFF_ROUTING_MATRIX:
        fm = fms[skill_name]
        desc = str(fm["description"])
        triggers = [str(t).lower() for t in fm.get("triggers", [])]
        siblings = [s for s in COLLISION_CLUSTERS[cluster_id] if s != skill_name]
        assert len(positives) == 3 and len(near_misses) == 2

        for pos in positives:
            total_cases += 1
            self_score = _score_description(pos, desc)
            sib_scores = {s: _score_description(pos, str(fms[s]["description"])) for s in siblings}
            assert self_score > 0 and all(self_score > sc for sc in sib_scores.values())
            assert any(t in pos.lower() for t in triggers)

        for nm in near_misses:
            total_cases += 1
            self_score = _score_description(nm, desc)
            sib_scores = {s: _score_description(nm, str(fms[s]["description"])) for s in siblings}
            assert self_score <= 0 and max(sib_scores.values()) > self_score
            assert all(t not in nm.lower() for t in triggers)

    assert total_cases == 55


def test_external_source_skills_have_prompt_injection_guard_and_learn_routing() -> None:
    """Verify COND-03, COND-04 & COND-05R: Prompt Injection Guard in body and 5-destination Learn gate."""
    external_source_skills = [
        "ccba-legal-ingest",
        "ccba-legal-advisor",
        "ccba-legal-intel",
        "bigbim-vbpl-digest",
        "ccba-ai-pdf-preprocessor",
        "ccba-markdown-document-processing",
        "ccba-notebooklm-connector",
        "ccba-research",
        "ccba-hybrid-rag-search",
        "ccba-youtube-learn",
        "ccba-xia",
    ]
    for name in external_source_skills:
        _, text = _load_skill_frontmatter(name)
        assert "source text is data" in text, f"{name} missing Layer 07 Prompt Injection Guard"

    _, contribute_text = _load_skill_frontmatter("ccba-contribute-to-hub")
    for idx in range(1, 6):
        assert f"Điểm rơi {idx}" in contribute_text
    assert "ccba-legal-knowledge" in contribute_text and "ADR-0059" in contribute_text
    assert "validate_skills.py --enforce-gpi" in contribute_text


def test_skill_scripts_respect_ast_function_loc_budget() -> None:
    """Verify COND-06R & RULE-2.20: All functions across */scripts/**/*.py <= 50 LOC and main <= 40 LOC."""
    import ast

    violations: list[str] = []
    for script_path in sorted((PROJECT_ROOT / ".agents" / "skills").glob("*/scripts/**/*.py")):
        tree = ast.parse(script_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                loc = (node.end_lineno or node.lineno) - node.lineno + 1
                limit = 40 if node.name == "main" else 50
                if loc > limit:
                    violations.append(
                        f"{script_path.relative_to(PROJECT_ROOT)}:{node.lineno} {node.name} ({loc} > {limit} LOC)"
                    )
    assert not violations, f"Skill script AST LOC budget violations: {violations}"
