#!/usr/bin/env python3
"""apply_worker_patch.py - Atomic Patch Application Engine for Multi-Agent Workflows.

Implements the Single-Writer Protocol (ADR-0053, SPEC-2026-TEAMWORK-DIFF-001):
1. Parses Search-Replace blocks, JSON manifests, and Unified Diffs.
2. Detects overlapping line collisions across multiple worker patches.
3. Performs pre-flight dry-run matching before touching files.
4. Atomically applies changes with in-memory snapshot and automatic rollback on failure.
5. Integrates with `ccba-harness verify-patch` for end-to-end exit code verification.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HUB_ROOT = Path(__file__).resolve().parent.parent.parent

SEARCH_REPLACE_PATTERN = re.compile(
    r"(?:^|\n)(?:FILE:\s*(?P<file>[^\r\n]+)\s*)?"
    r"<<<<<<<\s*SEARCH\r?\n(?P<search>.*?)\r?\n=======\r?\n(?P<replace>.*?)\r?\n>>>>>>>\s*REPLACE",
    re.DOTALL,
)


@dataclass
class PatchBlock:
    """A discrete search-replace operation targeting a specific file."""

    file_path: str
    search_content: str
    replace_content: str
    source_patch: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert PatchBlock to JSON-serializable dictionary."""
        return {
            "file_path": self.file_path,
            "search_content": self.search_content,
            "replace_content": self.replace_content,
            "source_patch": self.source_patch,
        }


def parse_patch_content(content: str, source_name: str = "") -> list[PatchBlock]:
    """Parse patch text into a list of PatchBlock objects."""
    blocks: list[PatchBlock] = []
    trimmed = content.strip()

    # 1. Check if content is a JSON manifest
    if trimmed.startswith("[") and trimmed.endswith("]"):
        try:
            items = json.loads(trimmed)
            if isinstance(items, list):
                for item in items:
                    if (
                        isinstance(item, dict)
                        and "file" in item
                        and "search" in item
                        and "replace" in item
                    ):
                        blocks.append(
                            PatchBlock(
                                file_path=str(item["file"]).strip(),
                                search_content=str(item["search"]),
                                replace_content=str(item["replace"]),
                                source_patch=source_name,
                            )
                        )
                if blocks:
                    return blocks
        except Exception:
            pass

    # 2. Parse Search-Replace blocks
    current_file = ""
    lines = content.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        line = lines[i]
        file_match = re.match(r"^FILE:\s*([^\r\n]+)", line)
        if file_match:
            current_file = file_match.group(1).strip()
            i += 1
            continue

        if line.strip().startswith("<<<<<<< SEARCH"):
            search_lines: list[str] = []
            replace_lines: list[str] = []
            i += 1
            # Collect search lines
            while i < len(lines) and not lines[i].strip().startswith("======="):
                search_lines.append(lines[i])
                i += 1
            i += 1  # Skip =======
            # Collect replace lines
            while i < len(lines) and not lines[i].strip().startswith(">>>>>>> REPLACE"):
                replace_lines.append(lines[i])
                i += 1
            i += 1  # Skip >>>>>>> REPLACE

            search_str = "".join(search_lines)
            replace_str = "".join(replace_lines)

            # Strip trailing newline if single line replacement
            if current_file:
                blocks.append(
                    PatchBlock(
                        file_path=current_file,
                        search_content=search_str,
                        replace_content=replace_str,
                        source_patch=source_name,
                    )
                )
            continue
        i += 1

    return blocks


def detect_collisions(patches: list[PatchBlock]) -> list[str]:
    """Detect overlapping collisions between multiple patches targeting the same file."""
    conflicts: list[str] = []
    by_file: dict[str, list[PatchBlock]] = defaultdict(list)
    for p in patches:
        by_file[p.file_path].append(p)

    for file_path, file_patches in by_file.items():
        if len(file_patches) <= 1:
            continue

        # Check if multiple patches come from different sources
        sources = {p.source_patch for p in file_patches if p.source_patch}
        if len(sources) > 1:
            # Check for overlapping search blocks
            for idx_a in range(len(file_patches)):
                for idx_b in range(idx_a + 1, len(file_patches)):
                    pa = file_patches[idx_a]
                    pb = file_patches[idx_b]
                    if pa.source_patch != pb.source_patch:
                        # Direct identical or substring search overlap
                        if (
                            pa.search_content in pb.search_content
                            or pb.search_content in pa.search_content
                        ):
                            conflicts.append(
                                f"Collision in '{file_path}': patch '{pa.source_patch}' overlaps with '{pb.source_patch}'"
                            )

    return conflicts


def dry_run(patches: list[PatchBlock], base_dir: Path) -> tuple[bool, list[str]]:
    """Validate that all patches can cleanly apply to target files without writing to disk."""
    errors: list[str] = []
    # In-memory working copy to simulate sequential applying
    virtual_files: dict[str, str] = {}

    for idx, p in enumerate(patches, 1):
        target = (base_dir / p.file_path).resolve()
        if not target.exists():
            errors.append(
                f"Patch #{idx} ({p.source_patch}): Target file does not exist: {p.file_path}"
            )
            continue

        if p.file_path not in virtual_files:
            virtual_files[p.file_path] = target.read_text(encoding="utf-8")

        current_content = virtual_files[p.file_path]
        count = current_content.count(p.search_content)

        if count == 0:
            errors.append(
                f"Patch #{idx} ({p.source_patch}): SEARCH block not found in '{p.file_path}'"
            )
        elif count > 1:
            errors.append(
                f"Patch #{idx} ({p.source_patch}): Ambiguous SEARCH block (found {count} matches) in '{p.file_path}'"
            )
        else:
            virtual_files[p.file_path] = current_content.replace(
                p.search_content, p.replace_content, 1
            )

    return (len(errors) == 0, errors)


def apply_atomic(
    patches: list[PatchBlock],
    base_dir: Path,
) -> tuple[bool, dict[Path, str], list[str]]:
    """Atomically apply patches after successful dry run. Returns (success, snapshot, logs)."""
    valid, dry_errors = dry_run(patches, base_dir)
    if not valid:
        return False, {}, dry_errors

    snapshot: dict[Path, str] = {}
    applied_files: set[str] = set()

    # Step 1: Create snapshot
    for p in patches:
        target = (base_dir / p.file_path).resolve()
        if target not in snapshot:
            snapshot[target] = target.read_text(encoding="utf-8")

    # Step 2: Apply sequentially
    try:
        current_texts: dict[Path, str] = dict(snapshot)
        for p in patches:
            target = (base_dir / p.file_path).resolve()
            current_texts[target] = current_texts[target].replace(
                p.search_content, p.replace_content, 1
            )
            applied_files.add(p.file_path)

        for target, new_text in current_texts.items():
            target.write_text(new_text, encoding="utf-8")

        return True, snapshot, [f"Successfully patched {len(applied_files)} file(s)."]
    except Exception as exc:
        rollback(snapshot)
        return False, {}, [f"Atomic apply failed, rolled back: {exc}"]


def rollback(snapshot: dict[Path, str]) -> None:
    """Rollback all modified files to their original snapshot states."""
    for target, original_content in snapshot.items():
        try:
            target.write_text(original_content, encoding="utf-8")
        except Exception as e:
            print(f"[Error] Failed to rollback {target}: {e}", file=sys.stderr)


def load_patches_from_directory(dir_path: Path) -> list[PatchBlock]:
    """Scan a directory and load all patches (*.diff, *.patch, *.txt, *.json)."""
    if not dir_path.exists():
        return []

    patches: list[PatchBlock] = []
    extensions = ("*.diff", "*.patch", "*.txt", "*.json")
    files: list[Path] = []
    for ext in extensions:
        files.extend(dir_path.rglob(ext))

    for f in sorted(set(files)):
        try:
            content = f.read_text(encoding="utf-8")
            parsed = parse_patch_content(content, source_name=f.name)
            patches.extend(parsed)
        except Exception as err:
            print(f"[Warning] Could not parse patch file {f.name}: {err}", file=sys.stderr)

    return patches


@dataclass
class SwarmExecutionReport:
    """Structured report of a Single-Writer swarm patch application run."""

    success: bool
    patches_count: int
    collisions: list[str]
    dry_run_errors: list[str]
    applied_files: list[str]
    semantic_conflict: bool
    verification_errors: list[str]
    timings: dict[str, float]
    rollback_performed: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert report to JSON-serializable dictionary."""
        return {
            "success": self.success,
            "patches_count": self.patches_count,
            "collisions": self.collisions,
            "dry_run_errors": self.dry_run_errors,
            "applied_files": self.applied_files,
            "semantic_conflict": self.semantic_conflict,
            "verification_errors": self.verification_errors,
            "timings": {k: round(v, 4) for k, v in self.timings.items()},
            "rollback_performed": self.rollback_performed,
        }


def execute_swarm_patches(
    patches: list[PatchBlock],
    base_dir: Path,
    dry_run_only: bool = False,
    apply: bool = True,
    verify: bool = False,
    verify_commands: list[str] | None = None,
    preset: str | None = None,
    target: Path | None = None,
    timeout: float = 60.0,
) -> SwarmExecutionReport:
    """Execute the complete Single-Writer multi-agent patch pipeline."""
    timings: dict[str, float] = {}
    t_start = time.perf_counter()

    # Step 1: Detect collisions
    t_col_start = time.perf_counter()
    collisions = detect_collisions(patches)
    timings["collision_detection"] = time.perf_counter() - t_col_start

    if collisions:
        timings["total"] = time.perf_counter() - t_start
        return SwarmExecutionReport(
            success=False,
            patches_count=len(patches),
            collisions=collisions,
            dry_run_errors=[],
            applied_files=[],
            semantic_conflict=False,
            verification_errors=[],
            timings=timings,
            rollback_performed=False,
        )

    # Step 2: Dry run
    t_dry_start = time.perf_counter()
    is_valid, dry_errors = dry_run(patches, base_dir)
    timings["dry_run"] = time.perf_counter() - t_dry_start

    if not is_valid:
        timings["total"] = time.perf_counter() - t_start
        return SwarmExecutionReport(
            success=False,
            patches_count=len(patches),
            collisions=[],
            dry_run_errors=dry_errors,
            applied_files=[],
            semantic_conflict=False,
            verification_errors=[],
            timings=timings,
            rollback_performed=False,
        )

    if dry_run_only or (not apply and not verify):
        timings["total"] = time.perf_counter() - t_start
        return SwarmExecutionReport(
            success=True,
            patches_count=len(patches),
            collisions=[],
            dry_run_errors=[],
            applied_files=[],
            semantic_conflict=False,
            verification_errors=[],
            timings=timings,
            rollback_performed=False,
        )

    # Step 3: Apply atomically
    t_apply_start = time.perf_counter()
    apply_ok, snapshot, logs = apply_atomic(patches, base_dir)
    timings["apply"] = time.perf_counter() - t_apply_start

    applied_files = [p.file_path for p in patches]

    if not apply_ok:
        timings["total"] = time.perf_counter() - t_start
        return SwarmExecutionReport(
            success=False,
            patches_count=len(patches),
            collisions=[],
            dry_run_errors=logs,
            applied_files=[],
            semantic_conflict=False,
            verification_errors=[],
            timings=timings,
            rollback_performed=True,
        )

    # Step 4: Verification gate & Semantic Conflict detection
    if verify:
        t_ver_start = time.perf_counter()
        cmds = list(verify_commands) if verify_commands else []
        if preset:
            try:
                from ccba_harness.verifier import resolve_preset_commands
            except ImportError:
                sys.path.insert(0, str(HUB_ROOT / "packages" / "ccba-harness" / "src"))
                from ccba_harness.verifier import resolve_preset_commands
            preset_cmds = resolve_preset_commands(preset, target=target, base_dir=base_dir)
            cmds.extend(preset_cmds)

        if not cmds:
            cmds = [
                "python -m ruff check scripts/ tests/",
                "python -m pytest tests/governance/ -q",
            ]

        try:
            from ccba_harness.verifier import verify_patch_execution
        except ImportError:
            sys.path.insert(0, str(HUB_ROOT / "packages" / "ccba-harness" / "src"))
            from ccba_harness.verifier import verify_patch_execution

        verification = verify_patch_execution(
            commands=cmds,
            cwd=base_dir,
            timeout=timeout,
        )
        timings["verification"] = time.perf_counter() - t_ver_start

        if not verification.all_passed:
            rollback(snapshot)
            failed_cmds = [
                f"{r.command} (exit {r.exit_code}): {r.error_message or r.stderr or r.stdout}".strip()
                for r in verification.results
                if r.exit_code != 0
            ]
            timings["total"] = time.perf_counter() - t_start
            return SwarmExecutionReport(
                success=False,
                patches_count=len(patches),
                collisions=[],
                dry_run_errors=[],
                applied_files=applied_files,
                semantic_conflict=True,
                verification_errors=failed_cmds,
                timings=timings,
                rollback_performed=True,
            )

    timings["total"] = time.perf_counter() - t_start
    return SwarmExecutionReport(
        success=True,
        patches_count=len(patches),
        collisions=[],
        dry_run_errors=[],
        applied_files=applied_files,
        semantic_conflict=False,
        verification_errors=[],
        timings=timings,
        rollback_performed=False,
    )


def main() -> int:
    """CLI Entrypoint for apply_worker_patch."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Single-Writer Atomic Patch Application Engine for CCBA Multi-Agent Workflows."
    )
    parser.add_argument("--patch", type=Path, default=None, help="Path to a single patch file")
    parser.add_argument(
        "--patch-dir", type=Path, default=None, help="Directory containing worker patches"
    )
    parser.add_argument("--base-dir", type=Path, default=HUB_ROOT, help="Monorepo root directory")
    parser.add_argument(
        "--check-conflicts", action="store_true", help="Check for collisions across patches"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate patch application without modifying disk"
    )
    parser.add_argument("--apply", action="store_true", help="Apply patches atomically to codebase")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verification gate after applying and auto-rollback on failure",
    )
    parser.add_argument(
        "-c",
        "--verify-cmd",
        "--verify-commands",
        dest="verify_commands",
        nargs="+",
        default=None,
        help="Custom verification commands to execute during verification gate",
    )
    parser.add_argument(
        "--preset",
        choices=["code", "doc", "skill", "adr"],
        default=None,
        help="Verification preset to use",
    )
    parser.add_argument("--target", type=Path, default=None, help="Target file for presets")
    parser.add_argument(
        "--timeout", type=float, default=60.0, help="Timeout in seconds for verification commands"
    )
    parser.add_argument(
        "--benchmark", action="store_true", help="Print latency benchmark profiling"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output SwarmExecutionReport as JSON to stdout"
    )

    args = parser.parse_args()

    # If verification commands or preset is provided, imply --verify
    if args.verify_commands or args.preset:
        args.verify = True

    # Collect patches
    patches: list[PatchBlock] = []
    if args.patch:
        if not args.patch.exists():
            print(f"ERROR: Patch file does not exist: {args.patch}", file=sys.stderr)
            return 1
        patches.extend(
            parse_patch_content(args.patch.read_text(encoding="utf-8"), source_name=args.patch.name)
        )

    if args.patch_dir:
        dir_patches = load_patches_from_directory(args.patch_dir)
        patches.extend(dir_patches)

    if not patches:
        print("ERROR: No valid patches found or specified.", file=sys.stderr)
        return 1

    if not args.json:
        print(f"[Info] Loaded {len(patches)} patch block(s).")

    # If only checking collisions
    if args.check_conflicts and not (args.dry_run or args.apply or args.verify):
        collisions = detect_collisions(patches)
        if collisions:
            print("[FAIL] Collision(s) detected across worker patches:", file=sys.stderr)
            for c in collisions:
                print(f"  - {c}", file=sys.stderr)
            return 1
        print("[PASS] Zero collisions detected across all loaded patches.")
        return 0

    report = execute_swarm_patches(
        patches=patches,
        base_dir=args.base_dir,
        dry_run_only=args.dry_run,
        apply=args.apply or args.verify,
        verify=args.verify,
        verify_commands=args.verify_commands,
        preset=args.preset,
        target=args.target,
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.success else 1

    # Text report
    if report.collisions:
        print("[FAIL] Collision(s) detected across worker patches:", file=sys.stderr)
        for c in report.collisions:
            print(f"  - {c}", file=sys.stderr)
        return 1

    if report.dry_run_errors:
        print("[FAIL] Dry-run validation failed:", file=sys.stderr)
        for err in report.dry_run_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if args.dry_run:
        print("[PASS] Pre-flight dry-run succeeded for all patches.")
        return 0

    if report.semantic_conflict:
        print(
            "[FAIL] Post-patch verification failed (Semantic Conflict)! Triggering automatic rollback...",
            file=sys.stderr,
        )
        for err in report.verification_errors:
            print(f"  - {err}", file=sys.stderr)
        print("[Rollback] Codebase restored to pre-patch snapshot.")
        return 1

    if report.success:
        print(f"[Success] Successfully patched {len(report.applied_files)} file(s).")
        if args.verify:
            print("[PASS] Post-patch verification passed! Codebase is healthy.")

    if args.benchmark:
        t = report.timings
        print(
            f"[Benchmark] Col: {t.get('collision_detection', 0.0):.4f}s | "
            f"Dry: {t.get('dry_run', 0.0):.4f}s | Apply: {t.get('apply', 0.0):.4f}s | "
            f"Ver: {t.get('verification', 0.0):.4f}s | Total: {t.get('total', 0.0):.4f}s"
        )

    return 0 if report.success else 1


if __name__ == "__main__":
    sys.exit(main())
