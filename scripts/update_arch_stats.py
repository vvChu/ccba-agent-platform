import re
import sys
from pathlib import Path

# Force UTF-8 for stdout on Windows
sys.stdout.reconfigure(encoding="utf-8")

# Paths to count
SKILLS_DIR = Path(".agents/skills")
WORKFLOWS_DIR = Path(".agents/workflows")
PACKAGES_DIR = Path("packages")

# Files to update
DOCS_TO_UPDATE = [
    Path("README.md"),
    Path("PLATFORM.md"),
    Path(".github/copilot-instructions.md"),
    Path("CONTEXT.md"),
]


def get_counts():
    """Đếm số lượng thực tế từ hệ thống file."""
    # Count skills (directories inside .agents/skills)
    skill_count = 0
    if SKILLS_DIR.exists():
        skill_count = sum(
            1 for p in SKILLS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")
        )

    # Count workflows (markdown files inside .agents/workflows)
    workflow_count = 0
    if WORKFLOWS_DIR.exists():
        workflow_count = sum(1 for p in WORKFLOWS_DIR.glob("*.md"))

    # Count packages (directories inside packages/)
    package_count = 0
    if PACKAGES_DIR.exists():
        package_count = sum(
            1 for p in PACKAGES_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")
        )

    return {
        "SKILL_COUNT": str(skill_count),
        "WORKFLOW_COUNT": str(workflow_count),
        "PACKAGE_COUNT": str(package_count),
    }


def update_file(file_path: Path, counts: dict) -> bool:
    """Cập nhật các giá trị marker trong file. Trả về True nếu có thay đổi."""
    if not file_path.exists():
        return False

    content = file_path.read_text(encoding="utf-8")
    original_content = content

    for key, value in counts.items():
        # Pattern matches: <!-- KEY_START -->anything<!-- KEY_END -->
        pattern = re.compile(rf"(<!--\s*{key}_START\s*-->).*?(<!--\s*{key}_END\s*-->)", re.DOTALL)
        content = pattern.sub(rf"\g<1>{value}\g<2>", content)

    if content != original_content:
        file_path.write_text(content, encoding="utf-8")
        print(f"✅ Updated {file_path}")
        return True
    return False


def main():
    print("Thống kê Architecture Metrics...")
    counts = get_counts()
    for k, v in counts.items():
        print(f" - {k}: {v}")

    changed = False
    for doc in DOCS_TO_UPDATE:
        if update_file(doc, counts):
            changed = True

    if not changed:
        print("Không có thay đổi nào cần cập nhật.")
    else:
        print("Đã hoàn tất cập nhật tài liệu.")


if __name__ == "__main__":
    main()
