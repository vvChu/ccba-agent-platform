"""Script to execute Ticket 01: Initializing ccba-legal-knowledge Spoke repository."""

import sys
from pathlib import Path

import yaml


def init_spoke() -> None:
    spoke_dir = Path("D:/GitHubProjects/ccba-legal-knowledge")

    spoke_dir.mkdir(parents=True, exist_ok=True)
    print(f"[Ticket 01] Initializing Knowledge Spoke at: {spoke_dir.resolve()}")

    # 1. Create workspace_context.yaml
    context_data = {
        "project": {
            "name": "ccba-legal-knowledge",
            "type": "knowledge-spoke",
            "mode": "delivery",
            "is_hub": False,
            "hub_path": "D:/GitHubProjects/ccba-agent-platform",
        },
        "agents": {"primary_domain": "legal-compliance", "language": "vi"},
    }
    context_file = spoke_dir / "workspace_context.yaml"
    context_file.write_text(
        yaml.dump(context_data, allow_unicode=True, default_flow_style=False), encoding="utf-8"
    )
    print(" ✅ Created workspace_context.yaml (project.mode: delivery)")

    # 2. Create AGENTS.md
    agents_md = """# CCBA Legal Knowledge Spoke — Workspace Constitution

> [!IMPORTANT]
> **Đây là Repository Spoke Tri thức Pháp lý chính quy của CCBA Agent Platform.**
> Tất cả dữ liệu tri thức được đóng gói theo tiêu chuẩn OKF v2.0 Native-First.

## Quy tắc Vận hành Spoke:
1. **Mô hình Đường dẫn Nông (Shallow Path):** Thư mục `legal_docs/` nằm tại Cấp 1 của Spoke. `legal_registry.yaml` nằm tại Root.
2. **Reuse-First Gate:** Mọi thao tác cập nhật dữ liệu phải đồng bộ với Hub (`ccba-agent-platform`).
3. **Độc lập Mã nguồn:** Không chứa code ứng dụng, tập trung 100% cho OKF Markdown Bundles và RAG Metadata.
"""
    (spoke_dir / "AGENTS.md").write_text(agents_md, encoding="utf-8")
    print(" ✅ Created AGENTS.md constitution")

    # 3. Create README.md
    readme_md = """# 📚 CCBA Legal Knowledge Spoke

Cơ sở dữ liệu Tri thức Pháp luật và Quy chuẩn Kỹ thuật Xây dựng chính quy của CCBA Agent Platform.

## Cấu trúc Thư mục Tri thức (`legal_docs/`):
- `legal_docs/REGULATION_QCVN/` — Các Quy chuẩn Kỹ thuật Quốc gia (QCVN 04, QCVN 06...)
- `legal_docs/STANDARD_TCVN/` — Các Tiêu chuẩn Quốc gia (TCVN 3890...)
- `legal_docs/LAW_LUAT/` — Các Luật Quốc hội (Luật Xây dựng 2025...)
- `legal_docs/DECREE_NGHI_DINH/` — Các Nghị định Hướng dẫn (NĐ 217/2026...)
"""
    (spoke_dir / "README.md").write_text(readme_md, encoding="utf-8")
    print(" ✅ Created README.md")

    # 4. Create shallow legal_docs structure
    legal_docs = spoke_dir / "legal_docs"
    (legal_docs / "REGULATION_QCVN").mkdir(parents=True, exist_ok=True)
    (legal_docs / "STANDARD_TCVN").mkdir(parents=True, exist_ok=True)
    (legal_docs / "LAW_LUAT").mkdir(parents=True, exist_ok=True)
    (legal_docs / "DECREE_NGHI_DINH").mkdir(parents=True, exist_ok=True)
    print(" ✅ Created shallow legal_docs/ hierarchy")

    # 5. Create Root legal_registry.yaml
    root_registry = spoke_dir / "legal_registry.yaml"
    reg_data = {
        "version": "2.0.0",
        "updated_at": "2026-07-26",
        "documents": [
            {
                "id": "QCVN-04-2021-BXD",
                "title": "QCVN 04:2021/BXD — Quy chuẩn kỹ thuật quốc gia về Nhà chung cư",
                "category": "REGULATION_QCVN",
                "bundle_path": "legal_docs/REGULATION_QCVN/qcvn_04_2021_bxd",
            },
            {
                "id": "QCVN-06-2022-BXD",
                "title": "QCVN 06:2022/BXD — Quy chuẩn kỹ thuật quốc gia về An toàn cháy cho nhà và công trình",
                "category": "REGULATION_QCVN",
                "bundle_path": "legal_docs/REGULATION_QCVN/qcvn_06_2022_bxd",
            },
        ],
    }
    root_registry.write_text(
        yaml.dump(reg_data, allow_unicode=True, default_flow_style=False), encoding="utf-8"
    )
    print(" ✅ Created Root legal_registry.yaml")


if __name__ == "__main__":
    if sys.platform == "win32":
        import io

        try:
            if isinstance(sys.stdout, io.TextIOWrapper):
                sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    init_spoke()
