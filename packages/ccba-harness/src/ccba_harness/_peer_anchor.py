"""_peer_anchor.py - Level-2/3 anchor patch engine and transactional byte-journal rollback (ADR-0063 / ADR-0065)."""

from __future__ import annotations

import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ._mutex import FileMutexLock
from ._peer_models import AnchorPatchPayload, AutoApplyResult
from .verifier import resolve_preset_commands


def extract_anchor_payload(text: str) -> AnchorPatchPayload | None:
    """Extracts and validates an AnchorPatchPayload from raw markdown or JSON string."""
    if not text:
        return None
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    raw_json = match.group(1) if match else text.strip()
    try:
        data = json.loads(raw_json)
        return AnchorPatchPayload.model_validate(data)
    except Exception:
        return None


def _prepare_single_file_patch(
    root_resolved: Path,
    file_patch: Any,
    target_files_seen: set[Path],
) -> tuple[Path, str, str]:
    """Validates a single file patch and returns (target_file, original_text, new_text)."""
    target_file = (root_resolved / file_patch.path).resolve()
    if not target_file.is_relative_to(root_resolved):
        raise ValueError(f"Path traversal detected in patch: {file_patch.path}")
    if target_file in target_files_seen:
        raise ValueError(f"Payload contains duplicate target file: {file_patch.path}")
    target_files_seen.add(target_file)
    if not target_file.exists():
        raise ValueError(f"Target patch file does not exist: {file_patch.path}")
    if not target_file.is_file():
        raise ValueError(f"Target patch path is not a regular file: {file_patch.path}")

    raw_bytes = target_file.read_bytes()
    actual_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    if actual_sha256.lower() != file_patch.blob_sha256.lower():
        raise ValueError(
            f"Anchor patch SHA-256 mismatch for {file_patch.path}: "
            f"expected {file_patch.blob_sha256}, got {actual_sha256}"
        )

    text = raw_bytes.decode("utf-8")
    new_text = text.replace("\r\n", "\n")
    for rep in file_patch.replacements:
        old_norm = rep.old.replace("\r\n", "\n")
        new_norm = rep.new.replace("\r\n", "\n")
        count = new_text.count(old_norm)
        if count == 0:
            raise ValueError(
                f"Target old anchor text not found in {file_patch.path}: '{old_norm[:50]}...'"
            )
        if count > 1:
            raise ValueError(
                f"Target old anchor text is not unique in {file_patch.path} (found {count} matches): '{old_norm[:50]}...'"
            )
        new_text = new_text.replace(old_norm, new_norm, 1)
    return target_file, text, new_text


def _commit_anchor_patch_writes(
    prepared_writes: list[tuple[Path, str, str]],
    backup: bool,
) -> list[Path]:
    """Commits prepared anchor patch writes atomically with rollback on write failure."""
    from . import peer as _peer_mod

    written_backups: dict[Path, str] = {}
    modified_paths: list[Path] = []
    try:
        for target_file, original_content, new_content in prepared_writes:
            written_backups[target_file] = original_content
            if backup:
                bak_file = target_file.with_suffix(target_file.suffix + ".bak")
                _peer_mod.atomic_write_text(bak_file, original_content)
            _peer_mod.atomic_write_text(target_file, new_content)
            modified_paths.append(target_file)
        return modified_paths
    except Exception as exc:
        rollback_errors: list[str] = []
        for failed_file, old_content in written_backups.items():
            try:
                _peer_mod.atomic_write_text(failed_file, old_content)
            except Exception as r_err:
                rollback_errors.append(f"{failed_file.name}: {r_err}")
        err_msg = f"Transaction aborted during write phase: {exc}"
        if rollback_errors:
            err_msg += f" (Rollback errors: {'; '.join(rollback_errors)})"
        raise ValueError(err_msg) from exc


def apply_anchor_patch(
    root: Path,
    payload: AnchorPatchPayload | dict[str, Any],
    dry_run: bool = False,
    backup: bool = False,
) -> list[Path]:
    """Applies a Level-2 anchor patch payload atomically with SHA-256 pre-verification and rollback (ADR-0063)."""
    patch = AnchorPatchPayload.model_validate(payload) if isinstance(payload, dict) else payload
    root_resolved = root.resolve()
    target_files_seen: set[Path] = set()
    prepared_writes = [
        _prepare_single_file_patch(root_resolved, fp, target_files_seen) for fp in patch.files
    ]
    if dry_run:
        return [target_file for target_file, _, _ in prepared_writes]
    return _commit_anchor_patch_writes(prepared_writes, backup)


def get_git_toplevel(cwd: Path | str | None = None) -> Path | None:
    """Resolves the git repository top-level root directory (COND-LEVEL3-ROOT)."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=True,
        )
        top = res.stdout.strip()
        if top:
            return Path(top).resolve()
    except Exception:
        pass
    return None


def _recover_single_anchor_txn(txn_path: Path, backup_dir: Path) -> bool:
    """Restores a single interrupted anchor transaction directory if uncommitted."""
    from . import peer as _peer_mod

    journal_file = txn_path / "journal.json"
    commit_marker = txn_path / "commit.marker"
    aborted_marker = txn_path / "aborted.marker"
    if not (journal_file.exists() and not commit_marker.exists() and not aborted_marker.exists()):
        return False
    try:
        journal_data = json.loads(journal_file.read_text(encoding="utf-8"))
        target_root = Path(journal_data.get("root", str(backup_dir.parent.parent.parent))).resolve()
        for f_entry in journal_data.get("files", []):
            rel_p = f_entry.get("path")
            backup_fname = f_entry.get("backup_filename")
            if not rel_p or not backup_fname:
                continue
            backup_file = txn_path / backup_fname
            if backup_file.exists():
                _peer_mod.atomic_write_bytes(
                    (target_root / rel_p).resolve(), backup_file.read_bytes()
                )
        aborted_marker.write_text(
            f"Recovered at {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


def recover_pending_anchor_transactions(
    backup_dir: Path | None = None,
    root: Path | None = None,
) -> list[str]:
    """Scans and recovers interrupted anchor transactions from disk pre-images (COND-LEVEL3-TXN)."""
    if backup_dir is None:
        effective_root = root or get_git_toplevel() or Path.cwd()
        backup_dir = effective_root / ".md" / "backups" / "anchor-txn"
    if not backup_dir.exists() or not backup_dir.is_dir():
        return []
    recovered_txns: list[str] = []
    for txn_path in sorted(backup_dir.iterdir(), key=lambda p: p.name):
        if not txn_path.is_dir() or txn_path.name.startswith("."):
            continue
        if _recover_single_anchor_txn(txn_path, backup_dir):
            recovered_txns.append(txn_path.name)
    return recovered_txns


def _resolve_auto_apply_root(root: Path | str | None) -> Path:
    """Resolves and validates workspace git root for auto_apply_and_verify_patch."""
    if root is None:
        effective_root = get_git_toplevel()
        if effective_root is None:
            raise ValueError(
                "Root directory resolution failed: current working directory is not inside a git repository."
            )
        return effective_root
    effective_root = Path(root).resolve()
    if get_git_toplevel(effective_root) is None:
        raise ValueError(f"Specified root is not inside a git repository: {effective_root}")
    return effective_root


def _journal_anchor_preimages(
    effective_root: Path,
    patch: AnchorPatchPayload,
    txn_dir: Path,
    txn_id: str,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Validates patch in dry_run mode and records pre-image raw bytes into txn_dir."""
    from . import peer as _peer_mod

    preimage_sha256: dict[str, str] = {}
    journal_files: list[dict[str, Any]] = []
    txn_dir.mkdir(parents=True, exist_ok=False)
    try:
        apply_anchor_patch(root=effective_root, payload=patch, dry_run=True, backup=False)
        for idx, file_patch in enumerate(patch.files):
            target_file = (effective_root / file_patch.path).resolve()
            raw_bytes = target_file.read_bytes()
            current_sha = hashlib.sha256(raw_bytes).hexdigest()
            preimage_sha256[file_patch.path] = current_sha
            backup_filename = f"file_{idx}.bin"
            (txn_dir / backup_filename).write_bytes(raw_bytes)
            journal_files.append(
                {
                    "index": idx,
                    "path": file_patch.path,
                    "blob_sha256": current_sha,
                    "backup_filename": backup_filename,
                }
            )
        journal_data = {
            "txn_id": txn_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "root": str(effective_root),
            "files": journal_files,
        }
        _peer_mod.atomic_write_text(txn_dir / "journal.json", json.dumps(journal_data, indent=2))
        return preimage_sha256, journal_files
    except Exception as exc:
        shutil.rmtree(txn_dir, ignore_errors=True)
        raise ValueError(f"Pre-apply validation failed: {exc}") from exc


def _rollback_from_journal(
    effective_root: Path,
    txn_dir: Path,
    journal_files: list[dict[str, Any]],
    verify_sha: bool = True,
) -> bool:
    """Restores pre-image raw bytes from txn_dir journal and optionally verifies SHA-256."""
    from . import peer as _peer_mod

    rollback_ok = True
    for f_entry in journal_files:
        try:
            t_file = (effective_root / f_entry["path"]).resolve()
            b_file = txn_dir / f_entry["backup_filename"]
            _peer_mod.atomic_write_bytes(t_file, b_file.read_bytes())
            if verify_sha:
                restored_sha = hashlib.sha256(t_file.read_bytes()).hexdigest()
                if restored_sha.lower() != f_entry["blob_sha256"].lower():
                    rollback_ok = False
        except Exception:
            rollback_ok = False
    return rollback_ok


def _finalize_auto_apply_decision(
    root: Path,
    txn_dir: Path,
    txn_id: str,
    preset: str,
    keep_backups: bool,
    mod_paths: list[Path],
    preimage_sha: dict[str, str],
    j_files: list[dict[str, Any]],
    v_rep: Any,
) -> AutoApplyResult:
    """Finalizes commit marker or executes verified byte rollback after verification gate."""
    rel_mod = [str(p.relative_to(root)) if p.is_relative_to(root) else str(p) for p in mod_paths]
    common = {
        "preimage_sha256": preimage_sha,
        "report": v_rep,
        "transaction_id": txn_id,
        "modified_files": rel_mod,
    }
    if v_rep.all_passed:
        (txn_dir / "commit.marker").write_text("committed", encoding="utf-8")
        if not keep_backups:
            shutil.rmtree(txn_dir, ignore_errors=True)
        msg = f"Patch successfully applied and verified with preset '{preset}'."
        return AutoApplyResult(
            success=True, gate_verdict="GATE_PASS", rollback_proven=False, summary=msg, **common
        )

    rb_ok = _rollback_from_journal(root, txn_dir, j_files, True)
    if rb_ok:
        (txn_dir / "rollback.marker").write_text("clean", encoding="utf-8")
        if not keep_backups:
            shutil.rmtree(txn_dir, ignore_errors=True)
    tail = (
        "Workspace rolled back cleanly."
        if rb_ok
        else f"AND byte rollback verification mismatch! Transaction preserved at {txn_dir}."
    )
    msg = (
        f"Verification failed ({v_rep.failed_count}/{v_rep.total_commands} commands failed). {tail}"
    )
    return AutoApplyResult(
        success=False, gate_verdict="GATE_FAIL", rollback_proven=rb_ok, summary=msg, **common
    )


def _execute_locked_patch_transaction(
    root: Path,
    patch: AnchorPatchPayload,
    txn_dir: Path,
    txn_id: str,
    preset: str,
    timeout: float,
    keep_backups: bool,
    extra_commands: Sequence[str] | None,
) -> AutoApplyResult:
    """Executes journaled patch commit, verification gate, and rollback under FileMutexLock."""
    from . import peer as _peer_mod

    preimage_sha, j_files = _journal_anchor_preimages(root, patch, txn_dir, txn_id)
    fail_kw = {
        "gate_verdict": "GATE_FAIL",
        "preimage_sha256": preimage_sha,
        "transaction_id": txn_id,
    }
    try:
        mod_paths = apply_anchor_patch(root=root, payload=patch, dry_run=False, backup=False)
    except Exception as exc:
        rb_ok = _rollback_from_journal(root, txn_dir, j_files, False)
        if rb_ok and not keep_backups:
            shutil.rmtree(txn_dir, ignore_errors=True)
        msg = f"Disk commit aborted: {exc}. Workspace rolled back {'cleanly' if rb_ok else 'WITH ERRORS'}."
        return AutoApplyResult(success=False, rollback_proven=rb_ok, summary=msg, **fail_kw)

    cmds = list(extra_commands or [])
    if preset == "ci":
        cmds.append(f"{sys.executable} -m pytest packages/ccba-harness/tests/test_peer*.py -q")
    try:
        v_rep = _peer_mod.verify_patch_execution(
            preset=preset, cwd=root, timeout=timeout, commands=cmds or None
        )
    except Exception as v_err:
        rb_ok = _rollback_from_journal(root, txn_dir, j_files, True)
        msg = f"Verification execution crashed: {v_err}. Workspace rolled back {'cleanly' if rb_ok else 'WITH ERRORS'}."
        return AutoApplyResult(success=False, rollback_proven=rb_ok, summary=msg, **fail_kw)
    return _finalize_auto_apply_decision(
        root, txn_dir, txn_id, preset, keep_backups, mod_paths, preimage_sha, j_files, v_rep
    )


def auto_apply_and_verify_patch(
    root: Path | str | None,
    patch_payload: AnchorPatchPayload | dict[str, Any],
    verify_preset: str = "ci",
    timeout: float = 180.0,
    keep_backups: bool = False,
    extra_commands: Sequence[str] | None = None,
) -> AutoApplyResult:
    """Atomically applies anchor patch with pre-image byte journaling, verification, and rollback (ADR-0065)."""
    effective_root = _resolve_auto_apply_root(root)
    patch = (
        AnchorPatchPayload.model_validate(patch_payload)
        if isinstance(patch_payload, dict)
        else patch_payload
    )
    if not patch.files:
        raise ValueError("Anchor patch payload contains no files to patch.")
    resolve_preset_commands(preset=verify_preset)
    recover_pending_anchor_transactions(root=effective_root)

    backup_base = effective_root / ".md" / "backups" / "anchor-txn"
    backup_base.mkdir(parents=True, exist_ok=True)
    txn_id = f"txn_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    txn_dir = backup_base / txn_id
    if txn_dir.exists():
        raise ValueError(f"Transaction backup directory already exists: {txn_dir}")
    for fp in patch.files:
        t_path = (effective_root / fp.path).resolve()
        if t_path == txn_dir.resolve() or txn_dir.resolve().is_relative_to(t_path):
            raise ValueError(f"Payload target collides with transaction directory: {fp.path}")

    with FileMutexLock(backup_base / ".lock"):
        return _execute_locked_patch_transaction(
            effective_root,
            patch,
            txn_dir,
            txn_id,
            verify_preset,
            timeout,
            keep_backups,
            extra_commands,
        )
