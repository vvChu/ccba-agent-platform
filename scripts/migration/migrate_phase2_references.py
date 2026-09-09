"""migrate_phase2_references.py - Automation script for Milestone 3 Reference Harmonization.

Transfers 34 micro-skills (GPI < 12.0) into references/*.md of their owning Master Skills,
updates Master Skill triggers and Progressive Disclosure indexes, preserves auxiliary resources,
and removes the deprecated micro-skill directories.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"

# 34 Mappings: (micro_skill, master_skill, target_reference_filename, description)
MIGRATION_MAPPINGS: list[dict[str, str]] = [
    {
        "micro": "ccba-docx",
        "master": "ccba-xu-ly-van-phong",
        "target_ref": "docx_engine_guide.md",
        "desc": "Hướng dẫn chi tiết chèn nhận xét (comments) và theo dõi thay đổi (tracked changes) trong tài liệu Word",
    },
    {
        "micro": "ccba-viet-chuyen-nghiep",
        "master": "ccba-copywriting",
        "target_ref": "viet_chuyen_nghiep_rules.md",
        "desc": "Cẩm nang quy tắc ngữ pháp, văn phong chuyên nghiệp và kiểm tra chất lượng bài viết",
    },
    {
        "micro": "ccba-discard-feature",
        "master": "ccba-implement",
        "target_ref": "discard_feature_sop.md",
        "desc": "Quy trình chuẩn thao tác Git hủy bỏ tính năng an toàn",
    },
    {
        "micro": "ccba-mock-debugger",
        "master": "ccba-diagnosing-bugs",
        "target_ref": "mock_debugging_patterns.md",
        "desc": "Mẫu hình mock dữ liệu và tạo ca kiểm thử mô phỏng khi chẩn đoán lỗi phần mềm",
    },
    {
        "micro": "ccba-pccc-cdt-tuthamdinh",
        "master": "ccba-ai-qc-pccc-audit",
        "target_ref": "sop_cdt_tu_tham_dinh.md",
        "desc": "Danh mục SOP tự thẩm tra hồ sơ thiết kế PCCC cho Chủ đầu tư",
    },
    {
        "micro": "ccba-pccc-thamdinh-congan",
        "master": "ccba-ai-qc-pccc-audit",
        "target_ref": "sop_tham_dinh_congan.md",
        "desc": "Danh mục SOP thẩm duyệt thiết kế PCCC với Cơ quan Công an PCCC",
    },
    {
        "micro": "ccba-pccc-thamdinh-cqxd",
        "master": "ccba-ai-qc-pccc-audit",
        "target_ref": "sop_tham_tra_cqxd.md",
        "desc": "Danh mục SOP thẩm tra quy chuẩn xây dựng và an toàn cháy với Sở Xây dựng",
    },
    {
        "micro": "ccba-update-legal-registry",
        "master": "ccba-legal-document-tracker",
        "target_ref": "registry_sync_guide.md",
        "desc": "Quy trình đồng bộ định kỳ legal registry và cập nhật cơ sở dữ liệu văn bản pháp lý",
    },
    {
        "micro": "ccba-setup-pre-commit",
        "master": "ccba-setup-skills",
        "target_ref": "pre_commit_setup.md",
        "desc": "Hướng dẫn cấu hình pre-commit linter hooks và bảo vệ mã nguồn",
    },
    {
        "micro": "ccba-setup-ts-deep-modules",
        "master": "ccba-setup-skills",
        "target_ref": "ts_deep_modules.md",
        "desc": "Hướng dẫn thiết lập dependency-cruiser và kiểm soát ranh giới module sâu TypeScript",
    },
    {
        "micro": "ccba-long-form-writer",
        "master": "ccba-academic-writing",
        "target_ref": "long_form_chunking.md",
        "desc": "Kỹ thuật phân chia chương mục và viết bài học thuật dung lượng lớn",
    },
    {
        "micro": "ccba-docs-validator",
        "master": "ccba-docs-manager",
        "target_ref": "markdown_hallucination_check.md",
        "desc": "Quy trình kiểm tra tính xác thực của tài liệu Markdown, ngăn ngừa ảo ảnh thông tin",
    },
    {
        "micro": "ccba-propose-to-hub",
        "master": "ccba-contribute-to-hub",
        "target_ref": "propose_to_hub.md",
        "desc": "Quy trình đề xuất kỹ năng/tính năng mới từ Spoke lên Hub trung tâm",
    },
    {
        "micro": "ccba-wait-what",
        "master": "ccba-ask",
        "target_ref": "clarification_patterns.md",
        "desc": "Mẫu câu và kỹ thuật phỏng vấn làm rõ ngữ cảnh khi gặp yêu cầu mơ hồ",
    },
    {
        "micro": "ccba-wizard",
        "master": "ccba-init-spoke",
        "target_ref": "interactive_wizard.md",
        "desc": "Kịch bản hướng dẫn tương tác từng bước khi khởi tạo dự án Spoke mới",
    },
    {
        "micro": "ccba-prototype",
        "master": "ccba-implement",
        "target_ref": "prototyping_patterns.md",
        "desc": "Mẫu hình tạo spike / prototype nhanh để kiểm chứng giải pháp kỹ thuật",
    },
    {
        "micro": "ccba-resolving-merge-conflicts",
        "master": "ccba-git-guardrails",
        "target_ref": "merge_conflict_resolution.md",
        "desc": "Cẩm nang giải quyết xung đột mã nguồn Git merge an toàn",
    },
    {
        "micro": "ccba-create-pr",
        "master": "ccba-contribute-to-hub",
        "target_ref": "pull_request_guide.md",
        "desc": "Hướng dẫn kiểm tra chất lượng và tạo Pull Request chuẩn mực",
    },
    {
        "micro": "ccba-improve-codebase-architecture",
        "master": "ccba-codebase-design",
        "target_ref": "codebase_refactor_guide.md",
        "desc": "Cẩm nang rà soát module sâu và tái cấu trúc kiến trúc mã nguồn",
    },
    {
        "micro": "ccba-server-deploy",
        "master": "ccba-init-spoke",
        "target_ref": "server_deployment.md",
        "desc": "Hướng dẫn triển khai cấu hình server và hạ tầng phục vụ Agent",
    },
    {
        "micro": "ccba-to-tickets",
        "master": "ccba-to-spec",
        "target_ref": "spec_decomposition.md",
        "desc": "Kỹ thuật phân rã tài liệu đặc tả thành danh mục nhiệm vụ (tickets) chi tiết",
    },
    {
        "micro": "ccba-to-questionnaire",
        "master": "ccba-to-spec",
        "target_ref": "interactive_questionnaire.md",
        "desc": "Kỹ thuật xây dựng bảng khảo sát thu thập yêu cầu từ người dùng",
    },
    {
        "micro": "ccba-writing-great-skills",
        "master": "ccba-build-skill",
        "target_ref": "skill_authoring_guide.md",
        "desc": "Cẩm nang hướng dẫn kỹ sư biên soạn tệp chỉ dẫn SKILL.md chuẩn mực",
    },
    {
        "micro": "ccba-review-skill",
        "master": "ccba-build-skill",
        "target_ref": "skill_review_checklist.md",
        "desc": "Bảng kiểm định chất lượng và tuân thủ thể chế ADR-0057 cho kỹ năng",
    },
    {
        "micro": "ccba-review-proposal",
        "master": "ccba-contribute-to-hub",
        "target_ref": "proposal_review_sop.md",
        "desc": "Quy trình chuẩn SOP thẩm định các đề xuất Pull Request từ Spoke gửi lên Hub",
    },
    {
        "micro": "ccba-architecture-sync",
        "master": "ccba-adr-lifecycle",
        "target_ref": "architecture_sync_guide.md",
        "desc": "Quy trình đồng bộ tài liệu kiến trúc với ma trận ADR và bộ số liệu hệ thống",
    },
    {
        "micro": "ccba-triage",
        "master": "ccba-issue-to-hub",
        "target_ref": "issue_triage_flow.md",
        "desc": "Quy trình phân loại, gắn nhãn và sàng lọc sự cố kỹ thuật (issues)",
    },
    {
        "micro": "ccba-sync-upstream",
        "master": "ccba-update-spoke",
        "target_ref": "upstream_sync_guide.md",
        "desc": "Hướng dẫn kiểm tra và kéo cập nhật tính năng mới từ Hub về dự án Spoke",
    },
    {
        "micro": "ccba-teach",
        "master": "ccba-seminar-builder",
        "target_ref": "interactive_teaching.md",
        "desc": "Mẫu hình giảng dạy tương tác trong các buổi seminar và đào tạo nội bộ",
    },
    {
        "micro": "ccba-show-me",
        "master": "ccba-excalidraw-diagram",
        "target_ref": "visual_concepts.md",
        "desc": "Hướng dẫn trực quan hóa giải thuật, sơ đồ dữ liệu qua Excalidraw",
    },
    {
        "micro": "ccba-skills-eval",
        "master": "ccba-eval-gate",
        "target_ref": "evaluations_guide.md",
        "desc": "Hướng dẫn thiết lập bộ kiểm thử benchmark và đánh giá độ chính xác của kỹ năng",
    },
    {
        "micro": "ccba-loop-me",
        "master": "ccba-grilling",
        "target_ref": "workflow_looping.md",
        "desc": "Kỹ thuật phỏng vấn vòng lặp chuyên sâu nhằm khai thác tường tận yêu cầu quy trình",
    },
    {
        "micro": "ccba-brainstorm",
        "master": "ccba-ask",
        "target_ref": "brainstorm_templates.md",
        "desc": "Khung mẫu câu hỏi định hướng tư duy và giải pháp sáng tạo",
    },
    {
        "micro": "ccba-sequential-thinking",
        "master": "ccba-research",
        "target_ref": "sequential_thinking_method.md",
        "desc": "Phương pháp tư duy suy luận tuần tự nhiều bước (Sequential Thinking)",
    },
]


def extract_frontmatter_and_body(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and return (dict, body)."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        fm = yaml.safe_load(parts[1])
        return (fm if isinstance(fm, dict) else {}), parts[2].strip()
    except Exception:
        return {}, parts[2].strip()


def migrate_single_micro_skill(item: dict[str, str]) -> None:
    """Migrate one micro-skill into its master skill's references."""
    micro_name = item["micro"]
    master_name = item["master"]
    target_ref = item["target_ref"]
    desc = item["desc"]

    micro_dir = SKILLS_DIR / micro_name
    master_dir = SKILLS_DIR / master_name

    if not micro_dir.exists():
        print(f"[Skip] Micro-skill '{micro_name}' does not exist on disk.")
        return

    if not master_dir.exists():
        raise RuntimeError(f"Master skill '{master_name}' not found on disk!")

    master_refs_dir = master_dir / "references"
    master_refs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Read micro SKILL.md
    micro_skill_file = micro_dir / "SKILL.md"
    micro_content = micro_skill_file.read_text(encoding="utf-8")
    fm, body = extract_frontmatter_and_body(micro_content)

    title = fm.get("name") or micro_name
    micro_desc = fm.get("description") or desc

    # 2. Write references/<target_ref>
    ref_file_path = master_refs_dir / target_ref
    ref_header = f"""# {title} — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** {desc}
> **Mô tả gốc:** {micro_desc}

---

"""
    full_ref_content = ref_header + body + "\n"
    ref_file_path.write_text(full_ref_content, encoding="utf-8")
    print(f"[Migrate] Created {ref_file_path.relative_to(REPO_ROOT)}")

    # 3. Transfer auxiliary files
    _transfer_auxiliary_files(micro_name, micro_dir, master_dir, master_refs_dir)

    # 4. Remove micro-skill directory
    shutil.rmtree(micro_dir)
    print(f"[Cleanup] Removed directory .agents/skills/{micro_name}")


def _transfer_auxiliary_files(
    micro_name: str, micro_dir: Path, master_dir: Path, master_refs_dir: Path
) -> None:
    """Handle special auxiliary files per micro-skill."""
    if micro_name == "ccba-docx":
        for fname in ["docx-js.md", "ooxml.md", "LICENSE.txt"]:
            src = micro_dir / fname
            if src.exists():
                shutil.copy2(src, master_refs_dir / fname)
    elif micro_name == "ccba-viet-chuyen-nghiep":
        src_res = micro_dir / "resources"
        if src_res.exists():
            dst_res = master_refs_dir / "viet_chuyen_nghiep"
            if dst_res.exists():
                shutil.rmtree(dst_res)
            shutil.copytree(src_res, dst_res)
    elif micro_name == "ccba-setup-pre-commit":
        src_tpl = micro_dir / "resources" / ".pre-commit-config.yaml.template"
        if src_tpl.exists():
            shutil.copy2(src_tpl, master_refs_dir / ".pre-commit-config.yaml.template")
    elif micro_name == "ccba-setup-ts-deep-modules":
        src_cfg = micro_dir / "dependency-cruiser.config.cjs"
        if src_cfg.exists():
            shutil.copy2(src_cfg, master_refs_dir / "dependency-cruiser.config.cjs")
    elif micro_name == "ccba-wizard":
        src_sh = micro_dir / "template.sh"
        if src_sh.exists():
            shutil.copy2(src_sh, master_refs_dir / "template.sh")
    elif micro_name == "ccba-prototype":
        for fname in ["LOGIC.md", "UI.md"]:
            src = micro_dir / fname
            if src.exists():
                shutil.copy2(src, master_refs_dir / f"prototype_{fname.lower()}")
    elif micro_name == "ccba-improve-codebase-architecture":
        src_rep = micro_dir / "HTML-REPORT.md"
        if src_rep.exists():
            shutil.copy2(src_rep, master_refs_dir / "html_report_template.md")
    elif micro_name == "ccba-writing-great-skills":
        src_glo = micro_dir / "GLOSSARY.md"
        if src_glo.exists():
            shutil.copy2(src_glo, master_refs_dir / "skill_glossary.md")
    elif micro_name == "ccba-triage":
        src_sub_refs = micro_dir / "references"
        if src_sub_refs.exists():
            for f in src_sub_refs.iterdir():
                if f.is_file():
                    shutil.copy2(f, master_refs_dir / f.name.lower())
    elif micro_name == "ccba-teach":
        src_sub_refs = micro_dir / "references"
        if src_sub_refs.exists():
            for f in src_sub_refs.iterdir():
                if f.is_file():
                    shutil.copy2(f, master_refs_dir / f"teach_{f.name.lower()}")
    elif micro_name == "ccba-brainstorm":
        src_res = micro_dir / "resources"
        if src_res.exists():
            for f in src_res.iterdir():
                if f.is_file():
                    shutil.copy2(f, master_refs_dir / f.name)
    elif micro_name == "ccba-sequential-thinking":
        src_sub_refs = micro_dir / "references"
        if src_sub_refs.exists():
            for f in src_sub_refs.iterdir():
                if f.is_file():
                    shutil.copy2(f, master_refs_dir / f"sequential_{f.name}")
        src_scripts = micro_dir / "scripts"
        if src_scripts.exists():
            dst_scripts = master_refs_dir / "sequential_scripts"
            if dst_scripts.exists():
                shutil.rmtree(dst_scripts)
            shutil.copytree(src_scripts, dst_scripts)


def update_master_skill_docs() -> None:
    """Update triggers and Level 3 Progressive Disclosure index in Master Skills."""
    # Group mappings by master
    master_groups: dict[str, list[dict[str, str]]] = {}
    for item in MIGRATION_MAPPINGS:
        master_groups.setdefault(item["master"], []).append(item)

    for master_name, items in master_groups.items():
        master_skill_file = SKILLS_DIR / master_name / "SKILL.md"
        content = master_skill_file.read_text(encoding="utf-8")
        fm, body = extract_frontmatter_and_body(content)

        # 1. Update triggers
        triggers = fm.get("triggers") or []
        if isinstance(triggers, str):
            triggers = [triggers]
        triggers_set = {t.lower(): t for t in triggers}

        for item in items:
            micro_alias = item["micro"]
            triggers_set[micro_alias.lower()] = micro_alias
            clean_alias = micro_alias.replace("ccba-", "")
            triggers_set[clean_alias.lower()] = clean_alias

        fm["triggers"] = list(triggers_set.values())

        # 2. Build or update Progressive Disclosure section in body
        section_marker = "## Progressive Disclosure & Reference Index (Level 3)"
        table_rows = []
        for item in items:
            ref_path = f"references/{item['target_ref']}"
            desc = item["desc"]
            table_rows.append(f"| `{ref_path}` | {desc} |")

        table_content = "\n".join(table_rows)

        if section_marker in body:
            existing_part, rest = body.split(section_marker, 1)
            next_h2 = rest.find("\n## ")
            if next_h2 != -1:
                sec_body = rest[:next_h2]
                tail = rest[next_h2:]
            else:
                sec_body = rest
                tail = ""

            for row in table_rows:
                ref_key = row.split("|")[1].strip()
                if ref_key not in sec_body:
                    sec_body += "\n" + row

            new_body = existing_part + section_marker + sec_body + tail
        else:
            progressive_section = f"""

## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
{table_content}
"""
            new_body = body.rstrip() + "\n" + progressive_section

        # Re-assemble frontmatter
        fm_yaml = yaml.dump(fm, allow_unicode=True, sort_keys=False).strip()
        new_full_content = f"---\n{fm_yaml}\n---\n\n{new_body.lstrip()}\n"
        master_skill_file.write_text(new_full_content, encoding="utf-8")
        print(f"[Master Skill] Updated triggers & Level 3 Index in {master_name}/SKILL.md")


def main() -> None:
    """Execute fleet-wide Phase 2 reference migration."""
    print("=== CCBA FLEET SKILLS MIGRATION: PHASE 2 (MILESTONE 3) ===")
    for item in MIGRATION_MAPPINGS:
        migrate_single_micro_skill(item)

    print("\n--- Updating Master Skills Progressive Disclosure & Triggers ---")
    update_master_skill_docs()
    print("\n[Done] All 34 micro-skills successfully migrated to Level 3 References.")


if __name__ == "__main__":
    main()
