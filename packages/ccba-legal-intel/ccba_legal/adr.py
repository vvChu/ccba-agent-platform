import datetime
import subprocess
from pathlib import Path


class ADRGenerator:
    """Automatic Architecture Decision Record (ADR) generator for ccba-agent-platform.
    Scans git diff for significant architectural changes and records decisions in .md/adr/.
    """

    def __init__(self, repo_dir: str | None = None) -> None:
        if repo_dir:
            self.repo_dir = Path(repo_dir).resolve()
        else:
            self.repo_dir = Path("d:/GitHubProjects/ccba-agent-platform").resolve()
        self.adr_dir = self.repo_dir / ".md" / "adr"

    def get_git_diff_summary(self) -> str:
        """Get summary of git status and diff changes."""
        try:
            # Check staged and unstaged changes
            res_status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.repo_dir),
                capture_output=True,
                text=True,
                check=True,
            )
            return res_status.stdout
        except Exception as e:
            return f"Error running git status: {e}"

    def detect_architectural_changes(self) -> list[str]:
        """Detect if there are changes to packages, dependencies, config files, or database files."""
        changes = []
        summary = self.get_git_diff_summary()
        if not summary:
            return []

        lines = summary.splitlines()
        for line in lines:
            if len(line) < 4:
                continue
            status = line[:2].strip()
            filepath = line[3:]

            # Identify key files or directories
            if "pyproject.toml" in filepath:
                changes.append(f"Dependency/Config modified: {filepath} ({status})")
            elif "catalog.yaml" in filepath or "manifest.json" in filepath:
                changes.append(f"Platform Catalog/Manifest modified: {filepath} ({status})")
            elif filepath.endswith(".db") or filepath.endswith(".sqlite"):
                changes.append(f"Database schema/file modified: {filepath} ({status})")
            elif "packages/" in filepath and filepath.endswith(".py"):
                changes.append(f"Core Package modified: {filepath} ({status})")

        return changes

    def generate_adr(
        self, title: str, context: str, decision: str, consequences: str
    ) -> Path | None:
        """Create a new ADR markdown file in the .md/adr/ directory."""
        if not self.adr_dir.exists():
            self.adr_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() else "_" for c in title.lower()).strip("_")
        safe_title = "_".join(filter(None, safe_title.split("_")))[:40]

        filename = f"adr_{timestamp}_{safe_title}.md"
        adr_file = self.adr_dir / filename

        adr_content = f"""# ADR: {title}

- **Ngày tạo**: {now.strftime("%Y-%m-%d %H:%M:%S")}
- **Trạng thái**: Accepted

## 1. Bối cảnh (Context / Problem)
{context}

## 2. Quyết định (Decision)
{decision}

## 3. Hệ quả & Đánh đổi (Consequences & Trade-offs)
{consequences}
"""
        try:
            adr_file.write_text(adr_content, encoding="utf-8")
            return adr_file
        except Exception:
            return None
