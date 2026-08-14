"""Architecture Metrics and Document Markers Updater.

Scans the filesystem for current skill, workflow, and package counts,
and updates registered markdown documentation markers (<!-- KEY_START -->...<!-- KEY_END -->).

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


class ArchStatsUpdater:
    """Calculates architecture metrics and updates documentation markers."""

    DEFAULT_DOCS = [
        Path("README.md"),
        Path("PLATFORM.md"),
        Path(".github/copilot-instructions.md"),
        Path("CONTEXT.md"),
        Path(".md/knowledge/CONTEXT.md"),
    ]

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.skills_dir = self.project_root / ".agents" / "skills"
        self.workflows_dir = self.project_root / ".agents" / "workflows"
        self.packages_dir = self.project_root / "packages"

    def get_counts(self) -> dict[str, str]:
        """Scans the repository and returns count strings for skills, workflows, and packages."""
        skill_count = 0
        if self.skills_dir.exists():
            skill_count = sum(
                1 for p in self.skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
            )

        workflow_count = 0
        if self.workflows_dir.exists():
            workflow_count = sum(1 for p in self.workflows_dir.glob("*.md"))

        package_count = 0
        if self.packages_dir.exists():
            package_count = sum(
                1 for p in self.packages_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
            )

        return {
            "SKILL_COUNT": str(skill_count),
            "WORKFLOW_COUNT": str(workflow_count),
            "PACKAGE_COUNT": str(package_count),
        }

    def update_file(self, file_path: Path, counts: dict[str, str]) -> bool:
        """Updates markers in a single file. Returns True if file was modified."""
        target = file_path if file_path.is_absolute() else self.project_root / file_path
        if not target.exists():
            return False

        try:
            content = target.read_text(encoding="utf-8")
        except Exception:
            return False

        original_content = content

        for key, value in counts.items():
            pattern = re.compile(
                rf"(<!--\s*{key}_START\s*-->).*?(<!--\s*{key}_END\s*-->)", re.DOTALL
            )
            content = pattern.sub(rf"\g<1>{value}\g<2>", content)

        if content != original_content:
            target.write_text(content, encoding="utf-8")
            print(f"✅ Updated markers in {target.name}")
            return True
        return False

    def update_all_documents(
        self, docs: list[Path] | None = None
    ) -> tuple[dict[str, str], list[Path]]:
        """Updates all configured documents and returns (counts, list_of_modified_files)."""
        counts = self.get_counts()
        target_docs = docs or self.DEFAULT_DOCS
        modified = []

        for doc in target_docs:
            if self.update_file(doc, counts):
                modified.append(doc)

        return counts, modified


def update_arch_metrics(project_root: Path | None = None) -> tuple[dict[str, str], list[Path]]:
    """Convenience helper function to calculate and update architecture statistics."""
    updater = ArchStatsUpdater(project_root=project_root)
    return updater.update_all_documents()


def main() -> None:
    """CLI entry point with safe stream configuration."""
    if sys.platform == "win32":
        import io

        try:
            if isinstance(sys.stdout, io.TextIOWrapper):
                sys.stdout.reconfigure(encoding="utf-8")
            if isinstance(sys.stderr, io.TextIOWrapper):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("Thống kê Architecture Metrics...")
    updater = ArchStatsUpdater()
    counts, modified = updater.update_all_documents()

    for k, v in counts.items():
        print(f" - {k}: {v}")

    if not modified:
        print("Không có thay đổi nào cần cập nhật.")
    else:
        print(f"Đã hoàn tất cập nhật {len(modified)} tệp tài liệu.")


if __name__ == "__main__":
    main()
