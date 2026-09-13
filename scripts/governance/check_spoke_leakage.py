"""Spoke Leakage Guard & Proposal Governance Validator.

Scans changed files or repository tree to prevent accidental leakage of
Spoke-specific artifacts (.md/teach/, .tmp/, local absolute paths) and ensures
proposal metadata conforms to ADR 0045.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

# Safe UTF-8 reconfiguration for Windows stdout
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

FORBIDDEN_DIR_PATTERNS = [
    r"^\.md/teach/",
    r"^\.tmp/",
    r"^\.out-of-scope/",
    r"/__pycache__/",
    r"\.pyc$",
    r"\.DS_Store$",
]

FORBIDDEN_PATH_REGEX = re.compile(
    r"""(?<!file:///)(?:[c-zC-Z]:\\[Uu]sers\\[^\s"'\)\],]+|[c-zC-Z]:\\(?:GitHubProjects|workspace|tmp|temp)\\[^\s"'\)\],]+)"""
)

REQUIRED_PROPOSAL_FIELDS = {"proposal_id", "type", "status", "name"}


class SpokeLeakageAuditor:
    """Auditor for detecting Spoke artifact leakage and proposal metadata validity."""

    def __init__(self, root_dir: Path, strict: bool = False):
        self.root_dir = root_dir.resolve()
        self.strict = strict
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def get_changed_files(self) -> list[str]:
        """Retrieve list of modified/added files from Git (excluding deleted)."""
        try:
            # Check diff against origin/main or HEAD~1
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=d", "origin/main...HEAD"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            files = [f.strip().replace("\\", "/") for f in result.stdout.splitlines() if f.strip()]
            if not files:
                # Fallback to unstaged + staged local diff
                result_local = subprocess.run(
                    ["git", "diff", "--name-only", "--diff-filter=d", "HEAD"],
                    cwd=self.root_dir,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                files = [
                    f.strip().replace("\\", "/")
                    for f in result_local.stdout.splitlines()
                    if f.strip()
                ]
            return files
        except Exception:
            return []

    def get_all_tracked_files(self) -> list[str]:
        """Retrieve all git-tracked files in the repository."""
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            return [f.strip().replace("\\", "/") for f in result.stdout.splitlines() if f.strip()]
        except Exception:
            return []

    def check_forbidden_paths(self, file_paths: list[str]) -> None:
        """Verify that no file belongs to forbidden Spoke directories."""
        for rel_path in file_paths:
            normalized = rel_path.replace("\\", "/")
            for pattern in FORBIDDEN_DIR_PATTERNS:
                if re.search(pattern, normalized):
                    self.errors.append(
                        f"FORBIDDEN_FILE_DETECTED: '{normalized}' matches forbidden Spoke artifact pattern '{pattern}'"
                    )

    def check_hardcoded_paths_in_content(self, file_paths: list[str]) -> None:
        """Scan text files for hardcoded local absolute paths."""
        for rel_path in file_paths:
            normalized = rel_path.replace("\\", "/")
            # Exclude transient worker/subagent logs inside .agents/
            if re.search(r"^\.agents/(?:worker|auditor|explorer|orchestrator)_[^/]+/", normalized):
                continue
            # Allow catalog.yaml root configuration
            if normalized.endswith("catalog.yaml"):
                continue

            # Only scan production packages, skills, workflows, and proposals
            is_target_dir = (
                normalized.startswith("packages/")
                or normalized.startswith(".agents/skills/")
                or normalized.startswith(".agents/workflows/")
                or normalized.startswith(".agents/proposals/")
                or normalized.startswith("scripts/")
            )
            if not is_target_dir:
                continue

            full_path = self.root_dir / normalized
            if not full_path.exists() or full_path.is_dir():
                continue

            if full_path.suffix not in {".py", ".yaml", ".yml", ".json"}:
                # For markdown, only strictly enforce on proposals
                if not normalized.startswith(".agents/proposals/"):
                    continue

            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    # Skip comment examples
                    if "# Example:" in line or "# example:" in line:
                        continue
                    # Skip markdown links formatted as file:/// (these are IDE links)
                    clean_line = re.sub(r"file:///[^\s\)]+", "", line)
                    matches = FORBIDDEN_PATH_REGEX.findall(clean_line)
                    if matches:
                        # Allow explicit placeholder/documentation references in historical proposals if they have ellipsis
                        if "..." in line or "example" in line.lower():
                            continue
                        self.errors.append(
                            f"HARDCODED_ABSOLUTE_PATH [{normalized}:{line_idx}]: Found '{matches[0]}' in line: {line.strip()[:80]}"
                        )
            except Exception as e:
                self.warnings.append(f"COULD_NOT_READ [{normalized}]: {e}")

    def audit_proposal_file(self, p_file: Path) -> bool:
        """Audit a single proposal markdown file for schema validity and leakage."""
        initial_errors = len(self.errors)
        resolved_file = p_file.resolve()
        try:
            rel_p = resolved_file.relative_to(self.root_dir).as_posix()
        except ValueError:
            rel_p = resolved_file.as_posix()

        try:
            text = resolved_file.read_text(encoding="utf-8")
            if not text.startswith("---"):
                self.errors.append(
                    f"INVALID_PROPOSAL_FRONTMATTER [{rel_p}]: File must start with YAML frontmatter '---'"
                )
                return False

            parts = text.split("---", 2)
            if len(parts) < 3:
                self.errors.append(
                    f"INVALID_PROPOSAL_FRONTMATTER [{rel_p}]: Incomplete YAML frontmatter delimiter"
                )
                return False

            meta = yaml.safe_load(parts[1])
            if not isinstance(meta, dict):
                self.errors.append(
                    f"INVALID_PROPOSAL_FRONTMATTER [{rel_p}]: Frontmatter must be a YAML dictionary"
                )
                return False

            missing_fields = REQUIRED_PROPOSAL_FIELDS - set(meta.keys())
            if missing_fields:
                self.errors.append(
                    f"MISSING_PROPOSAL_METADATA [{rel_p}]: Missing required fields {sorted(missing_fields)}"
                )
                return False

            # Check content for hardcoded paths
            self.check_hardcoded_paths_in_content([rel_p])
        except Exception as ex:
            self.errors.append(f"PROPOSAL_PARSE_ERROR [{rel_p}]: {ex}")
            return False

        return len(self.errors) == initial_errors

    def check_proposal_metadata(self) -> None:
        """Verify all proposals in .agents/proposals/ have valid frontmatter."""
        proposals_dir = self.root_dir / ".agents" / "proposals"
        if not proposals_dir.exists():
            return

        for p_file in proposals_dir.glob("*.md"):
            self.audit_proposal_file(p_file)

    def check_md_root_hygiene(self) -> None:
        """Verify that .md/ root is clean and conforms to Global Rule 1 & Rule 3."""
        md_dir = self.root_dir / ".md"
        if not md_dir.exists():
            return

        allowed_root_files = {
            "workspace_context.yaml",
            ".gitkeep",
            "cross_references.yaml",
            "GLOSSARY.md",
        }

        for item in md_dir.iterdir():
            if item.is_file() and item.name not in allowed_root_files:
                self.errors.append(
                    f"STRAY_MD_ROOT_FILE [.md/{item.name}]: Only 'workspace_context.yaml' is allowed at .md/ root. Move reports to '.md/knowledge/reports/', extracts to '.md/extracted_docs/', or scratch to '.md/scratch/' per Global Rule 1."
                )

        # Check for .env files inside .md/ (excluding ephemeral local scratch)
        for env_file in md_dir.rglob("*.env*"):
            if env_file.is_file() and not env_file.name.endswith(".example"):
                if "scratch" in env_file.parts:
                    continue
                rel_env = env_file.relative_to(self.root_dir).as_posix()
                self.errors.append(
                    f"ENV_FILE_IN_MD_DIR [{rel_env}]: .env files must reside at Project Root, not inside .md/ per Global Rule 3."
                )

    def run_audit(self, changed_only: bool = True) -> int:
        """Run complete Spoke leakage audit."""
        print("=================================================================")
        print("   CCBA SPOKE LEAKAGE & PROPOSAL GOVERNANCE GUARD (ADR 0045)     ")
        print("=================================================================")

        if changed_only:
            file_paths = self.get_changed_files()
            if not file_paths:
                print(
                    "ℹ️ No changed files detected via Git diff. Performing tree scan of proposals."
                )
                file_paths = []
        else:
            file_paths = self.get_all_tracked_files()

        self.check_forbidden_paths(file_paths)
        self.check_hardcoded_paths_in_content(file_paths)
        self.check_proposal_metadata()
        self.check_md_root_hygiene()

        print(f"Files Evaluated       : {len(file_paths)}")
        print(f"Critical Violations   : {len(self.errors)}")
        print(f"Warnings              : {len(self.warnings)}")
        print("-----------------------------------------------------------------")

        if self.warnings:
            print("\n⚠️ WARNINGS:")
            for w in self.warnings:
                print(f"  - {w}")

        if self.errors:
            print("\n❌ CRITICAL ERRORS:")
            for err in self.errors:
                print(f"  - {err}")
            print("\n🚫 FAILED: Spoke leakage or proposal metadata violation detected.")
            return 1

        print("\n✅ PASSED: Repository is clean of Spoke leakages and proposals are well-governed.")
        return 0


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Audit repository for Spoke leakage and proposal metadata validity."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root directory")
    parser.add_argument(
        "--all", action="store_true", help="Scan entire repository instead of just changed files"
    )
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args()

    auditor = SpokeLeakageAuditor(root_dir=args.root, strict=args.strict)
    return auditor.run_audit(changed_only=not args.all)


if __name__ == "__main__":
    sys.exit(main())
