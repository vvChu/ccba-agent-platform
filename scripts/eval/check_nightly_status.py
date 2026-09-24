#!/usr/bin/env python3
"""check_nightly_status.py - Unified 4-Layer Telemetry & System Health Inspector.

Provides real-time inspection across the 3 nightly runner phases, heartbeat state,
legacy log mining fallback, and 5-Pillar document health (ADR-0035, ADR-0043, ADR-0058).
"""

from __future__ import annotations

import argparse
import fcntl
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure project root and ccba-harness are on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
harness_src = PROJECT_ROOT / "packages" / "ccba-harness" / "src"
if harness_src.exists() and str(harness_src) not in sys.path:
    sys.path.insert(0, str(harness_src))

try:
    from ccba_harness.evals.daemon import resolve_canonical_root
except ImportError:

    def resolve_canonical_root(root: Path) -> Path:
        return root.resolve()


logger = logging.getLogger("ccba.eval.status")


def check_lock_status(lock_path: Path) -> tuple[bool, str]:
    """Inspects the process mutex lock (/tmp/ccba_nightly_runner.lock) non-blockingly.

    Args:
        lock_path: Path to the flock lock file.

    Returns:
        tuple[bool, str]: (is_locked, reason)
    """
    if not lock_path.exists():
        return False, "LOCK_FILE_ABSENT"

    try:
        # Try opening to test flock
        f = open(lock_path)
    except Exception as e:
        return True, f"LOCK_FILE_UNREADABLE ({e})"

    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Successfully locked -> nobody else holds it
        fcntl.flock(f, fcntl.LOCK_UN)
        f.close()
        return False, "UNLOCKED"
    except (BlockingIOError, OSError):
        f.close()
        return True, "LOCKED_BY_ACTIVE_PROCESS"
    except Exception as e:
        f.close()
        return True, f"LOCK_CHECK_ERROR ({e})"


def detect_nightly_processes() -> list[dict[str, Any]]:
    """Scans for active nightly runner and daemon processes without third-party deps.

    Returns:
        list[dict[str, Any]]: List of running processes with pid, cmd, and phase role.
    """
    my_pid = os.getpid()
    active_procs: list[dict[str, Any]] = []

    # Priority 1: Direct /proc inspection (Linux standard, fast < 10ms)
    proc_dir = Path("/proc")
    if proc_dir.exists() and proc_dir.is_dir():
        for p in proc_dir.iterdir():
            if not p.name.isdigit():
                continue
            pid = int(p.name)
            if pid == my_pid:
                continue
            try:
                cmdline_bytes = (p / "cmdline").read_bytes()
                cmdline = (
                    cmdline_bytes.replace(b"\x00", b" ").decode("utf-8", errors="ignore").strip()
                )
                if not cmdline:
                    continue

                role = _match_process_role(cmdline)
                if role:
                    active_procs.append({"pid": pid, "cmd": cmdline, "role": role})
            except Exception:
                continue
        return active_procs

    # Priority 2: Fallback to 'ps' command if /proc is not mounted
    try:
        res = subprocess.run(
            ["ps", "-eo", "pid,args"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines()[1:]:
                parts = line.strip().split(None, 1)
                if len(parts) < 2:
                    continue
                pid_str, cmdline = parts[0], parts[1]
                if not pid_str.isdigit():
                    continue
                pid = int(pid_str)
                if pid == my_pid:
                    continue
                role = _match_process_role(cmdline)
                if role:
                    active_procs.append({"pid": pid, "cmd": cmdline, "role": role})
    except Exception:
        pass

    return active_procs


def _is_pid_alive(pid: int) -> bool:
    """Checks if a process with given PID is currently alive on the system."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def _match_process_role(cmdline: str) -> str | None:
    """Classifies a command line string into a Nightly Cron role."""
    if "nightly_tuner_daemon.py" in cmdline or "ccba_harness.evals.daemon" in cmdline:
        return "PHASE_3_MULTI_SKILL_TUNER"
    if (
        "doc_refactor_daemon.py" in cmdline
        or "compact_session_learnings.py" in cmdline
        or "ccba_harness.docs.daemon" in cmdline
    ):
        return "PHASE_2_DOC_HEALTH_AUDIT"
    if "run_nightly_telemetry.py" in cmdline:
        return "PHASE_1_SPOKE_LEGAL_TELEMETRY"
    if "run_nightly_tuner.sh" in cmdline:
        return "CRON_WRAPPER_RUNNER"
    return None


def classify_overall_phase(active_procs: list[dict[str, Any]], is_locked: bool) -> str:
    """Determines the overarching execution phase of the nightly system."""
    roles = {p["role"] for p in active_procs}
    if "PHASE_3_MULTI_SKILL_TUNER" in roles:
        return "PHASE_3_MULTI_SKILL_TUNER"
    if "PHASE_2_DOC_HEALTH_AUDIT" in roles:
        return "PHASE_2_DOC_HEALTH_AUDIT"
    if "PHASE_1_SPOKE_LEGAL_TELEMETRY" in roles:
        return "PHASE_1_SPOKE_LEGAL_TELEMETRY"
    if "CRON_WRAPPER_RUNNER" in roles:
        return "CRON_WRAPPER_ACTIVE"
    if is_locked:
        return "LOCKED_MUTEX_BUSY"
    return "IDLE"


def read_heartbeat_telemetry(project_root: Path) -> dict[str, Any] | None:
    """Reads live tuner heartbeat JSON from canonical root or ephemeral worktree.

    Args:
        project_root: Repository root path.

    Returns:
        dict[str, Any] | None: Parsed heartbeat data or None if absent/corrupted.
    """
    canonical_root = resolve_canonical_root(project_root)
    candidates = [
        project_root / ".md" / "telemetry" / "tuner_heartbeat.json",
        canonical_root / ".md" / "telemetry" / "tuner_heartbeat.json",
        project_root
        / ".worktrees"
        / "nightly-runner"
        / ".md"
        / "telemetry"
        / "tuner_heartbeat.json",
        canonical_root
        / ".worktrees"
        / "nightly-runner"
        / ".md"
        / "telemetry"
        / "tuner_heartbeat.json",
    ]
    for base in {project_root / ".worktrees", canonical_root / ".worktrees"}:
        if base.is_dir():
            for wt_hb in base.glob("*/.md/telemetry/tuner_heartbeat.json"):
                if wt_hb not in candidates:
                    candidates.append(wt_hb)

    newest_file: Path | None = None
    newest_mtime = -1.0

    for cand in candidates:
        if cand.exists() and cand.is_file():
            try:
                mtime = cand.stat().st_mtime
                if mtime > newest_mtime:
                    newest_mtime = mtime
                    newest_file = cand
            except Exception:
                pass

    if not newest_file:
        return None

    try:
        content = newest_file.read_text(encoding="utf-8")
        data = json.loads(content)
        if isinstance(data, dict):
            data["source_file"] = str(newest_file)
            data["source"] = "heartbeat_json"
            return data
        return None
    except Exception as e:
        logger.warning(f"Failed to parse heartbeat file {newest_file}: {e}")
        return None


def mine_legacy_log(log_path: Path, max_tail_bytes: int = 16_000_000) -> dict[str, Any] | None:
    """Mines the tail of nightly_cron.log as Layer 3 fallback for running or past sessions.

    Args:
        log_path: Path to .md/logs/nightly_cron.log
        max_tail_bytes: Maximum trailing bytes to inspect for efficiency.

    Returns:
        dict[str, Any] | None: Inferred tuner state or None if log is empty/missing.
    """
    if not log_path.exists() or not log_path.is_file():
        return None

    try:
        file_size = log_path.stat().st_size
        if file_size == 0:
            return None

        # Read tail if file is large
        with open(log_path, "rb") as f:
            if file_size > max_tail_bytes:
                f.seek(file_size - max_tail_bytes)
            raw_data = f.read()

        text = raw_data.decode("utf-8", errors="replace")
        lines = text.splitlines()

        # Locate the beginning of the most recent nightly batch
        start_idx = 0
        started_seen = False
        for i in range(len(lines) - 1, -1, -1):
            if "🔍 Đã phát hiện" in lines[i] and "kỹ năng trong catalog" in lines[i]:
                start_idx = i
                started_seen = True
                break
            if "[CCBA Nightly Auto-Tuner Daemon] Starting at" in lines[i]:
                start_idx = i
                started_seen = True
                break

        run_lines = lines[start_idx:]

        # 1. Total skills count - search across run_lines
        total_skills = 0
        for line in run_lines:
            m_total = re.search(r"Đã phát hiện (\d+) kỹ năng", line)
            if m_total:
                total_skills = int(m_total.group(1))
                break

        # 2. Track skills scanned and current skill
        skills_seen: list[str] = []
        current_skill: str | None = None
        current_iteration: str | None = None
        last_decision: str | None = None
        commits: list[dict[str, str]] = []
        revert_count = 0
        keep_count = 0
        is_halted = False
        is_completed = False

        for line in run_lines:
            m_skill = re.search(r"⚡ --- Tối ưu hóa Kỹ năng: ([\w\-]+) ---", line)
            if m_skill:
                s_name = m_skill.group(1)
                if s_name not in skills_seen:
                    skills_seen.append(s_name)
                current_skill = s_name
                current_iteration = None

            m_iter = re.search(r"🔄 --- Iteration (\d+/\d+) ---", line)
            if m_iter:
                current_iteration = m_iter.group(1)

            m_commit = re.search(r"Git Commit thành công: [\'\"](.*?)[\'\"]", line)
            if m_commit:
                commits.append({"skill": current_skill or "unknown", "detail": m_commit.group(1)})

            m_dec = re.search(r"📌 Quyết định \[(KEEP|REVERT)\]: (.*)", line)
            if m_dec:
                last_decision = f"[{m_dec.group(1)}] {m_dec.group(2)}"
                if m_dec.group(1) == "KEEP":
                    keep_count += 1
                else:
                    revert_count += 1

            if "Nightly Tuner Early Halt" in line:
                is_halted = True
            elif "Đã lưu báo cáo:" in line:
                is_completed = True

        if not skills_seen and not commits and total_skills == 0:
            if started_seen:
                return {
                    "source": "log_mining",
                    "status": "INITIALIZING",
                    "current_skill": None,
                    "current_index": 0,
                    "total_skills": 0,
                    "total_commits": 0,
                    "current_iteration": None,
                    "last_decision": None,
                    "commits": [],
                    "reverted_trials": 0,
                    "kept_trials": 0,
                    "log_path": str(log_path),
                }
            return None

        status = "IN_PROGRESS"
        if is_halted:
            status = "HALTED"
        elif is_completed:
            status = "COMPLETED"

        return {
            "source": "log_mining",
            "status": status,
            "current_skill": current_skill,
            "current_index": len(skills_seen),
            "total_skills": total_skills or len(skills_seen),
            "total_commits": len(commits),
            "current_iteration": current_iteration,
            "last_decision": last_decision,
            "commits": commits,
            "reverted_trials": revert_count,
            "kept_trials": keep_count,
            "log_path": str(log_path),
        }
    except Exception as e:
        logger.warning(f"Error while mining legacy log {log_path}: {e}")
        return None


def inspect_doc_health(
    project_root: Path,
    allow_live_audit: bool = True,
    force_live_audit: bool = False,
) -> dict[str, Any]:
    """Inspects the 5-Pillar Document Health state via cache or on-the-fly audit.

    Args:
        project_root: Repository root path.
        allow_live_audit: If True and cache missing, executes live audit.
        force_live_audit: If True, bypasses cache and re-audits live.

    Returns:
        dict[str, Any]: Document health audit details.
    """
    canonical_root = resolve_canonical_root(project_root)
    cache_path = project_root / ".md" / "telemetry" / "doc_health_report.json"
    if not cache_path.is_file():
        canonical_cache = canonical_root / ".md" / "telemetry" / "doc_health_report.json"
        if canonical_cache.is_file():
            cache_path = canonical_cache

    # Step 1: Check cache report if not forced live
    if not force_live_audit and cache_path.exists() and cache_path.is_file():
        try:
            content = cache_path.read_text(encoding="utf-8")
            data = json.loads(content)
            health = data.get("health", data)
            raw_pillars = health.get("bloated_pillars", [])
            bloated_count = sum(
                1
                for p in raw_pillars
                if (p.get("is_bloated") if isinstance(p, dict) else getattr(p, "is_bloated", False))
            )
            return {
                "source": "cache_file",
                "timestamp": data.get("timestamp"),
                "is_healthy": health.get("is_healthy", False),
                "total_docs_scanned": health.get("total_docs_scanned", 0),
                "total_pillars_count": len(raw_pillars),
                "bloated_pillars_count": bloated_count,
                "file_bloat_violations": health.get("file_bloat_violations", []),
                "zero_deletion_violations": health.get("zero_deletion_violations", []),
                "grounding_failures": health.get("grounding_failures", []),
                "cache_file": str(cache_path),
            }
        except Exception as e:
            logger.warning(f"Could not load doc health cache {cache_path}: {e}")

    # Step 2: Live On-the-Fly Audit Fallback
    if allow_live_audit or force_live_audit:
        try:
            from ccba_harness.docs.daemon import DocAutoEvolutionEngine

            engine = DocAutoEvolutionEngine(root=project_root)
            health_rep = engine.audit_all_documents()
            bloated_count = sum(1 for p in health_rep.bloated_pillars if p.is_bloated)
            return {
                "source": "live_audit",
                "timestamp": datetime.now().isoformat(),
                "is_healthy": health_rep.is_healthy,
                "total_docs_scanned": health_rep.total_docs_scanned,
                "total_pillars_count": len(health_rep.bloated_pillars),
                "bloated_pillars_count": bloated_count,
                "file_bloat_violations": health_rep.file_bloat_violations,
                "zero_deletion_violations": health_rep.zero_deletion_violations,
                "grounding_failures": health_rep.grounding_failures,
            }
        except Exception as e:
            return {
                "source": "live_audit_failed",
                "error": str(e),
                "is_healthy": False,
            }

    return {
        "source": "skipped",
        "message": "Cache report absent and live audit disabled via --quick.",
        "is_healthy": None,
    }


def build_unified_status(
    project_root: Path,
    lock_path: Path,
    log_path: Path,
    force_live_doc: bool = False,
    quick_mode: bool = False,
) -> dict[str, Any]:
    """Assembles all 4 inspection layers into a coherent telemetry payload."""
    # Layer 1: Process & Mutex
    is_locked, lock_reason = check_lock_status(lock_path)
    active_procs = detect_nightly_processes()
    overall_phase = classify_overall_phase(active_procs, is_locked)

    layer1 = {
        "is_locked": is_locked,
        "lock_file": str(lock_path),
        "lock_reason": lock_reason,
        "overall_phase": overall_phase,
        "active_processes": active_procs,
    }

    # Layer 2 & Layer 3: Heartbeat Telemetry & Log Mining Fallback
    hb_data = read_heartbeat_telemetry(project_root)
    tuner_telemetry: dict[str, Any] | None = None

    active_tuner_pids = [p["pid"] for p in active_procs if p["role"] == "PHASE_3_MULTI_SKILL_TUNER"]
    hb_pid = hb_data.get("pid") if hb_data else None

    # Priority 1: If a Phase 3 tuner is actively running but heartbeat belongs to an older/unrelated PID or is absent
    if active_tuner_pids and (not hb_data or hb_pid not in active_tuner_pids):
        tuner_telemetry = mine_legacy_log(log_path)
        if tuner_telemetry:
            tuner_telemetry["is_active"] = True
            tuner_telemetry["active_pid"] = active_tuner_pids[0]
        else:
            tuner_telemetry = {
                "source": "process_detection",
                "status": "INITIALIZING",
                "is_active": True,
                "active_pid": active_tuner_pids[0],
                "current_skill": None,
                "current_index": 0,
                "total_skills": 0,
                "total_commits": 0,
            }
    elif hb_data:
        hb_status = hb_data.get("status", "UNKNOWN")
        is_pid_alive = (
            any(p["pid"] == hb_pid for p in active_procs) or _is_pid_alive(hb_pid)
            if hb_pid
            else False
        )

        if hb_status in ("IN_PROGRESS", "STARTED") and not is_pid_alive:
            hb_data["status"] = "STALE_OR_CRASHED"
            hb_data["is_active"] = False
        else:
            hb_data["is_active"] = is_pid_alive

        tuner_telemetry = hb_data
    else:
        # Fallback to Layer 3: Log Mining
        tuner_telemetry = mine_legacy_log(log_path)
        if tuner_telemetry:
            tuner_telemetry["is_active"] = overall_phase == "PHASE_3_MULTI_SKILL_TUNER"

    # Layer 4: 5-Pillar Document Health
    allow_live_audit = not quick_mode
    doc_health = inspect_doc_health(
        project_root,
        allow_live_audit=allow_live_audit,
        force_live_audit=force_live_doc,
    )

    return {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(project_root),
        "layer1_process": layer1,
        "layer2_3_tuner": tuner_telemetry,
        "layer4_doc_health": doc_health,
    }


def format_cli_report(status: dict[str, Any]) -> str:
    """Formats the unified status into a human-readable CLI report."""
    l1 = status["layer1_process"]
    tuner = status["layer2_3_tuner"]
    doc = status["layer4_doc_health"]

    lines: list[str] = [
        "================================================================================",
        "🌙 CCBA NIGHTLY UNIFIED TELEMETRY & SYSTEM HEALTH MONITOR",
        "================================================================================",
        f"🕒 Thời gian kiểm tra: {status['timestamp']}",
        f"📂 Thư mục dự án:      {status['project_root']}",
        "",
        "--- [TẦNG 1: TIẾN TRÌNH & MUTEX RUNNER] ---",
        f"• Trạng thái Mutex Lock:  {'🔒 ĐANG BẬN (LOCKED)' if l1['is_locked'] else '🔓 SẴN SÀNG (FREE)'} ({l1['lock_file']})",
        f"• Pha thực thi hiện tại:   ⚡ {l1['overall_phase']}",
    ]

    if l1["active_processes"]:
        lines.append("• Tiến trình đang chạy:")
        for p in l1["active_processes"]:
            cmd_snippet = f"{p['cmd'][:90]}..." if len(p["cmd"]) > 90 else p["cmd"]
            lines.append(f"  - [PID {p['pid']}] ({p['role']}): {cmd_snippet}")
    else:
        lines.append("• Không có tiến trình Nightly nào đang hoạt động.")

    lines.append("")
    lines.append("--- [TẦNG 2 & 3: TIẾN ĐỘ AUTO-TUNER DAEMON] ---")
    if tuner:
        src_label = (
            "JSON Heartbeat" if tuner.get("source") == "heartbeat_json" else "Log-Mining Fallback"
        )
        status_label = tuner.get("status", "UNKNOWN")
        curr_idx = tuner.get("current_index") or 0
        tot_skills = tuner.get("total_skills") or 0
        pct = (curr_idx / tot_skills * 100) if tot_skills > 0 else 0.0

        lines.extend(
            [
                f"• Nguồn dữ liệu:          📡 {src_label}",
                f"• Trạng thái nhịp tim:     {status_label} (Active: {'🟢 YES' if tuner.get('is_active') else '⚪ NO'})",
                f"• Kỹ năng đang xử lý:     ⚡ {tuner.get('current_skill') or 'None'} ({curr_idx}/{tot_skills} - {pct:.1f}%)",
                f"• Tổng Git Commits:       💾 {tuner.get('total_commits') or 0} commits",
            ]
        )
        if tuner.get("current_iteration"):
            lines.append(f"• Vòng lặp hiện tại:       🔄 Iteration {tuner['current_iteration']}")
        if tuner.get("last_decision"):
            lines.append(f"• Quyết định gần nhất:     📌 {tuner['last_decision']}")
        if tuner.get("total_tokens"):
            lines.append(f"• Token tiêu thụ:          🪙 {tuner['total_tokens']:,}")

        # List improved skills if available
        commits_list = tuner.get("commits") or []
        if commits_list:
            lines.append("• Các kỹ năng đã commit thành công:")
            for c in commits_list:
                lines.append(f"  - `{c.get('skill')}`: {c.get('detail')}")
        elif tuner.get("summaries"):
            improved = [s for s in tuner["summaries"] if s.get("commits_kept", 0) > 0]
            if improved:
                lines.append("• Các kỹ năng đã commit thành công:")
                for s in improved:
                    b_score = s.get("baseline_score") or 0.0
                    f_score = s.get("final_score") or 0.0
                    c_kept = s.get("commits_kept") or 0
                    lines.append(
                        f"  - `{s.get('skill_name')}`: {b_score:.1f}% ➔ {f_score:.1f}% (+{c_kept} commits)"
                    )
    else:
        lines.append(
            "• Không phát hiện dữ liệu nhịp tim Tuner nào (Chưa từng chạy hoặc đã bị dọn dẹp)."
        )

    lines.append("")
    lines.append("--- [TẦNG 4: SỨC KHỎE TÀI LIỆU (5 TRỤ CỘT DOC HEALTH)] ---")
    if doc.get("source") == "skipped":
        lines.append(f"• Trạng thái:              ⚪ Bỏ qua ({doc.get('message')})")
    elif doc.get("source") == "live_audit_failed":
        lines.append(f"• Trạng thái:              ❌ Lỗi kiểm toán: {doc.get('error')}")
    else:
        is_healthy = doc.get("is_healthy", False)
        health_icon = "🟢 100% HEALTHY" if is_healthy else "⚠️ CẢNH BÁO VI PHẠM"
        src_tag = "Cache File" if doc.get("source") == "cache_file" else "Live AST Engine"
        zd_violations = doc.get("zero_deletion_violations") or []
        zd_str = "✅ 0 vi phạm" if not zd_violations else f"⚠️ {len(zd_violations)} vi phạm"
        gf_failures = doc.get("grounding_failures") or []
        gf_str = "✅ 0 lỗi liên kết" if not gf_failures else f"⚠️ {len(gf_failures)} lỗi"

        bloated_count = doc.get("bloated_pillars_count") or 0
        tot_pillars = doc.get("total_pillars_count") or 5
        bloat_suffix = "(Chuẩn)" if bloated_count == 0 else "⚠️ Đầy"

        lines.extend(
            [
                f"• Nguồn kiểm toán:         📄 {src_tag}",
                f"• Tình trạng 5 Trụ Cột:    {health_icon}",
                f"• Tài liệu đã quét:        📚 {doc.get('total_docs_scanned') or 0} documents",
                f"• Trụ cột đầy (Bloated):   🏛️ {bloated_count}/{tot_pillars} pillars {bloat_suffix}",
                f"• Zero-Deletion Guard:     {zd_str}",
                f"• AST Symbol Grounding:    {gf_str}",
            ]
        )

    lines.append("================================================================================")
    return "\n".join(lines)


def main() -> None:
    """CLI Entrypoint for check_nightly_status.py."""
    parser = argparse.ArgumentParser(
        description="Unified 4-Layer Nightly Telemetry & Doc Health Inspector (ADR-0035, ADR-0058)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full telemetry payload as valid formatted JSON.",
    )
    parser.add_argument(
        "--live-doc-health",
        action="store_true",
        help="Force on-the-fly AST audit of all documents instead of using cache.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Fast mode: skip live doc health audit if disk cache is absent.",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Override repository root path (default: auto-detected).",
    )
    parser.add_argument(
        "--lock-file",
        type=str,
        default="/tmp/ccba_nightly_runner.lock",
        help="Override path to mutex lock file.",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Override path to nightly cron log file.",
    )

    args = parser.parse_args()

    project_root = Path(args.root).resolve() if args.root else PROJECT_ROOT
    lock_path = Path(args.lock_file)
    canonical_root = resolve_canonical_root(project_root)
    if args.log_file:
        log_path = Path(args.log_file)
    else:
        log_path = project_root / ".md" / "logs" / "nightly_cron.log"
        if not log_path.is_file():
            canonical_log = canonical_root / ".md" / "logs" / "nightly_cron.log"
            if canonical_log.is_file():
                log_path = canonical_log

    status_data = build_unified_status(
        project_root=project_root,
        lock_path=lock_path,
        log_path=log_path,
        force_live_doc=args.live_doc_health,
        quick_mode=args.quick,
    )

    if args.json:
        print(json.dumps(status_data, indent=2, ensure_ascii=False, default=str))
    else:
        print(format_cli_report(status_data))


if __name__ == "__main__":
    main()
