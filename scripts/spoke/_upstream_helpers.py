"""Declarative governance, license classification, and report hygiene helpers for Upstream Radar."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

_CANONICAL_YAML = Path(__file__).resolve().parents[2] / ".md/knowledge/upstream_sources.yaml"
_RX_MODE = r"--(?:port|improve|copy-raw)\b"
_RX_NEG_LIC = re.compile(
    r"\b(?:not|no|without|unlike|except)\s+(?:under\s+|licensed\s+under\s+|subject\s+to\s+|a\s+)?"
    r"(?:the\s+)?(?:mit|apache|bsd|isc|0bsd|unlicense)(?:[-_ ]?2(?:\.0)?)?\s*(?:license)?\b"
)
_AFFIRMATIVE_GRANTS = (
    "permission is hereby granted",
    "permission to use, copy, modify",
    "redistribution and use in source and binary forms",
    "licensed under the apache license",
    "apache license, version 2.0",
    "this is free and unencumbered software",
)
_GOV_KWS = ("rule", "protocol", "governance", "guideline", "standard", "documentation-management")
_SKILL_CATS = {"engineering", "productivity", "misc", "in-progress", "deprecated"}
_RX_WF = re.compile(r"^(?:claude/|\.agents?/)?workflows/([^/]+)\.md$")
_RX_SK = re.compile(
    r"^(?:(claude/skills|\.agents?/skills|skills)/)?(.+?)/(SKILL\.md|references/[^/]+\.md|scripts/.+)$"
)


def _read_yaml_dict(path: Path) -> dict[str, Any]:
    """Read YAML file into dictionary or return empty dict on failure."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, yaml.YAMLError):
        return {}


def load_governance_config(cfg: Path, amap: dict[str, str] | None = None) -> dict[str, Any]:
    """Load declarative aliases, license_rules, report_hygiene, and triage_ledger from YAML."""
    base = _read_yaml_dict(_CANONICAL_YAML)
    raw = base if cfg == _CANONICAL_YAML else {**base, **_read_yaml_dict(cfg)}
    ra, blr, rlr = raw.get("aliases"), base.get("license_rules"), raw.get("license_rules")
    a_d = ra if isinstance(ra, dict) else {}
    al = {str(k).strip().lower(): str(v).strip() for k, v in a_d.items()}
    if amap is not None:
        for k, v in al.items():
            amap.setdefault(k, v)
    s_map: dict[str, set[str]] = {}
    for s in [*(base.get("sources") or []), *(raw.get("sources") or [])]:
        if isinstance(s, dict):
            nm, tp = str(s.get("name", "")).strip(), str(s.get("type", "")).strip()
            if nm and tp:
                s_map.setdefault(nm, {nm}).add(tp)
                s_map.setdefault(tp, {tp}).add(nm)
    m_lr = {**(blr if isinstance(blr, dict) else {}), **(rlr if isinstance(rlr, dict) else {})}
    rules = {str(k): [str(p) for p in v] for k, v in m_lr.items() if isinstance(v, list) and v}
    hyg, led = raw.get("report_hygiene"), raw.get("triage_ledger")
    h_d = hyg if isinstance(hyg, dict) else {}
    t_led = [e for e in led if isinstance(e, dict)] if isinstance(led, list) else []
    return {
        "aliases": al,
        "source_aliases": s_map,
        "license_rules": rules,
        "report_hygiene": h_d,
        "triage_ledger": t_led,
    }


def classify_license_text(text: str, rules: dict[str, list[str]] | None = None) -> tuple[str, str]:
    """Classify combined repository license text into PERMISSIVE, COPYLEFT, PROPRIETARY, UNKNOWN."""
    active = rules or load_governance_config(_CANONICAL_YAML)["license_rules"]
    low = text.lower()
    if any(re.search(p, low) for p in active.get("dual_copyleft_regex", [])):
        return "COPYLEFT", "Dual MIT/GPL — cần xác nhận nhánh cấp phép tại Pha 1 /ccba-xia"
    if any(re.search(p, low) for p in active.get("dual_permissive_regex", [])):
        return "PERMISSIVE", "Dual Permissive License (Tự do sử dụng)"
    if any(re.search(p, low) for p in active.get("copyleft_regex", [])):
        return "COPYLEFT", "GPL/AGPL/LGPL/MPL (Rủi ro sao chép mã nguồn)"
    clean_perm = _RX_NEG_LIC.sub(" ", low)
    has_prop = any(tok in low for tok in active.get("proprietary_tokens", []))
    has_grant = any(g in clean_perm for g in _AFFIRMATIVE_GRANTS)
    if (not has_prop or has_grant) and any(
        tok in clean_perm for tok in active.get("permissive_tokens", [])
    ):
        if "mit license" in clean_perm or "permission is hereby granted" in clean_perm:
            return "PERMISSIVE", "MIT License (Tự do sử dụng)"
        lbl = (
            "Apache 2.0"
            if "apache license" in clean_perm
            else "BSD"
            if "bsd" in clean_perm
            else "ISC/0BSD"
        )
        return "PERMISSIVE", f"{lbl} License (Tự do sử dụng)"
    if has_prop:
        return "PROPRIETARY", "Bản quyền đóng (Không được sao chép)"
    return "UNKNOWN", "Custom license: cần kiểm tra thủ công"


def clamp_license_policy(result: dict[str, Any], license_type: str, xia_cmd: str) -> dict[str, Any]:
    """Clamp evaluation result according to PERMISSIVE, COMMERCIAL_LICENSED, or restricted rules."""
    if license_type == "PERMISSIVE":
        return result
    if license_type == "COMMERCIAL_LICENSED":
        steps = [
            re.sub(r"--copy-raw\b", "--port", str(s)) for s in result.get("actionable_steps", [])
        ]
        raw_xia = str(result.get("xia_command", xia_cmd))
        return {
            **result,
            "xia_command": re.sub(r"--copy-raw\b", "--port", raw_xia),
            "actionable_steps": steps,
        }
    steps = [re.sub(_RX_MODE, "--compare", str(s)) for s in result.get("actionable_steps", [])]
    out = {**result, "should_port": False, "color_override": "🟠", "xia_command": xia_cmd}
    out.update(status_override="COMPARE ONLY — LICENSE RESTRICTED", actionable_steps=steps)
    return out


def purge_legacy_clamped_cache(cache: dict[str, Any]) -> dict[str, Any]:
    """Purge legacy pre-v2 marketing/engineer or post-clamp COMPARE ONLY cache entries."""
    cleaned: dict[str, Any] = {}
    for k, v in cache.items():
        if not k.startswith("v2:"):
            if k.startswith(("marketing:", "engineer:", "claudekit-")):
                continue
            if (
                isinstance(v, dict)
                and v.get("status_override") == "COMPARE ONLY — LICENSE RESTRICTED"
            ):
                continue
        cleaned[k] = v
    return cleaned


def _is_closed_in_ledger(part: str, closed_pairs: set[tuple[str, str]]) -> bool:
    """Return True if a recommendation markdown block matches an ADOPTED/DECLINED ledger entry."""
    m_sk = re.search(r"^###\s+[^\n]*Skill:\s+`([^`]+)`", part)
    m_rp = re.search(r"\*\*Kho chứa nguồn\*\*:\s+`([^`]+)`", part)
    if not (m_sk and m_rp):
        return False
    rp, sk = m_rp.group(1).strip(), m_sk.group(1).strip()
    norm_sk = "." if sk.endswith(" (corpus)") else sk
    return (rp, sk) in closed_pairs or (rp, norm_sk) in closed_pairs


def prune_stale_recommendations(rec_file: Path, cfg_file: Path | None = None) -> int:
    """Prune legacy/closed triage_ledger blocks solely within AUTO-GENERATED markers."""
    if not rec_file.exists():
        return 0
    content = rec_file.read_text(encoding="utf-8")
    pat = r"(<!-- AUTO-GENERATED-START -->\s*)(.*?)(\s*<!-- AUTO-GENERATED-END -->)"
    m = re.search(pat, content, re.DOTALL)
    if not m:
        return 0
    cfg = load_governance_config(cfg_file or _CANONICAL_YAML)
    hyg, s_aliases = cfg["report_hygiene"], cfg.get("source_aliases", {})
    closed: set[tuple[str, str]] = set()
    for e in cfg.get("triage_ledger", []):
        if str(e.get("status", "")).strip().upper() in {"ADOPTED", "DECLINED"}:
            src, up = str(e.get("source", "")).strip(), str(e.get("upstream_path", "")).strip()
            for alias_src in s_aliases.get(src, {src}):
                closed.add((alias_src, up))
    stale_toks = tuple(str(x) for x in hyg.get("stale_block_tokens", []))
    rest_mks = tuple(str(x) for x in hyg.get("restricted_license_markers", []))
    old_h, new_h = "### 🟢 [RECOMMEND PORT]", "### 🟠 [COMPARE ONLY — LICENSE RESTRICTED]"
    kept, pruned = [], 0
    for part in (p.strip() for p in re.split(r"\n---\n?", m.group(2).strip()) if p.strip()):
        if part.startswith("### ") and (
            any(t in part for t in stale_toks) or _is_closed_in_ledger(part, closed)
        ):
            pruned += 1
            continue
        if part.startswith("### ") and any(mk in part for mk in rest_mks):
            part = re.sub(_RX_MODE, "--compare", part.replace(old_h, new_h))
        kept.append(part)
    body = content[: m.start(2)] + "\n\n---\n\n".join(kept) + content[m.end(2) :]
    rec_file.write_text(body, encoding="utf-8")
    return pruned


def check_github_archived(remote_url: str, *, _allow_in_pytest: bool = False) -> bool:
    """Query GitHub REST API via gh CLI to detect archived upstream repositories."""
    if os.environ.get("PYTEST_CURRENT_TEST") and not _allow_in_pytest:
        return False
    m = re.match(r"https?://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", remote_url.strip())
    if not m or not shutil.which("gh"):
        return False
    try:
        res = subprocess.run(
            ["gh", "api", f"repos/{m.group(1)}/{m.group(2)}", "--jq", ".archived"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=5,
            check=False,
        )
        return res.returncode == 0 and res.stdout.strip().lower() == "true"
    except (subprocess.SubprocessError, OSError):
        return False


def collapse_diff_resources(
    raw_lines: list[str], repo_path: Path
) -> list[tuple[str, str, str, list[tuple[str, bool]]]]:
    """Collapse git diff lines into unique (name, res_type, primary_rel, touched_files) items."""
    parsed: list[tuple[str, bool]] = []
    skill_dirs: set[str] = set()
    for ln in raw_lines:
        if not ln.strip():
            continue
        if "\t" in ln:
            parts = ln.split("\t")
            st, rel = parts[0].strip(), parts[-1].strip()
            if st.startswith("D"):
                continue
            acmr = st[:1] in {"A", "C", "M", "R"}
        else:
            rel, acmr = ln.strip(), False
        if ".md/scratch/" in rel or any(
            p in {".git", "node_modules", "__pycache__", "tests", "__tests__", "fixtures"}
            for p in Path(rel).parts
        ):
            continue
        parsed.append((rel, acmr))
        if rel.endswith("/SKILL.md"):
            skill_dirs.add(rel[: -len("/SKILL.md")])

    grouped: dict[tuple[str, str], tuple[str, list[tuple[str, bool]]]] = {}
    for rel, acmr in parsed:
        wf_m = _RX_WF.match(rel)
        if wf_m:
            nm = wf_m.group(1)
            rt = "governance_rule" if any(k in nm.lower() for k in _GOV_KWS) else "workflow"
            grouped.setdefault((rt, nm), (rel, []))[1].append((rel, acmr))
            continue
        sk_m = _RX_SK.match(rel)
        if not sk_m:
            continue
        pfx, sub, leaf = sk_m.group(1), sk_m.group(2), sk_m.group(3)
        sdir = f"{pfx}/{sub}" if pfx else sub
        if (
            leaf != "SKILL.md"
            and sdir not in skill_dirs
            and not (repo_path / sdir / "SKILL.md").is_file()
        ):
            continue
        sp = sub.split("/")
        nm = sp[-1] if len(sp) == 2 and sp[0] in _SKILL_CATS else sub
        grouped.setdefault(("skill", nm), (f"{sdir}/SKILL.md", []))[1].append((rel, acmr))
    return [(nm, rt, pri, files) for (rt, nm), (pri, files) in grouped.items()]


_SKIP_DIRS = {".git", "node_modules", ".md", "__pycache__", ".venv"}


def _visible_children(folder: Path, dirs_only: bool = True) -> list[Path]:
    """Return deterministically sorted non-hidden children excluding _SKIP_DIRS."""
    items = [p for p in folder.iterdir() if not p.name.startswith(".") and p.name not in _SKIP_DIRS]
    return sorted((p for p in items if p.is_dir() == dirs_only), key=lambda p: p.name)


def build_corpus_digest(repo_path: Path) -> str:
    """Build deterministic Level 1-2 directory & extension summary capped at <= 30 lines."""
    if not repo_path.is_dir():
        return f"# Corpus Digest: {repo_path.name}\n(missing repository)"
    lines = [f"# Corpus Digest: {repo_path.name}"]
    rfiles = [p.name for p in _visible_children(repo_path, dirs_only=False)]
    if rfiles:
        lines.append(f"- root files ({len(rfiles)}): {', '.join(rfiles[:5])}")
    for d1 in _visible_children(repo_path, dirs_only=True)[:28]:
        exts: dict[str, int] = {}
        lvl2 = [p.name for p in _visible_children(d1, dirs_only=True)[:3]]
        for f in d1.rglob("*"):
            if f.is_file() and not any(part in _SKIP_DIRS for part in f.relative_to(d1).parts):
                ext = f.suffix.lower() or "<no-ext>"
                exts[ext] = exts.get(ext, 0) + 1
        top = ", ".join(
            f"{k}:{v}" for k, v in sorted(exts.items(), key=lambda x: (-x[1], x[0]))[:3]
        )
        sub = f" [subdirs: {', '.join(lvl2)}]" if lvl2 else ""
        lines.append(f"- {d1.name}/ ({sum(exts.values())} files; {top or 'empty'}){sub}")
    return "\n".join(lines[:30] if len(lines) > 1 else [*lines, "(empty repository)"])


def evaluate_triage_gate(
    ledger: list[dict[str, Any]],
    repo_keys: set[str],
    up_path: str,
    target: str | None,
    repo_path: Path,
    head_sha: str,
    git_rel: str,
) -> tuple[str, dict[str, Any] | None]:
    """Evaluate triage_ledger state: returns ('SKIP'|'PROCEED'|'DEFERRED'|'DELTA_UNKNOWN', entry)."""
    hits = [
        e
        for e in ledger
        if str(e.get("source", "")).strip() in repo_keys
        and str(e.get("upstream_path", "")).strip() == up_path
        and (not target or not e.get("target") or str(e.get("target", "")).strip() == target)
    ]
    if not hits:
        return "PROCEED", None
    exact = [e for e in hits if target and str(e.get("target", "")).strip() == target]
    entry = exact[0] if exact else hits[0]
    st = str(entry.get("status", "")).strip().upper()
    rev = str(entry.get("reviewed_sha", "")).strip()
    if st == "DEFERRED":
        return "DEFERRED", entry
    if st not in {"ADOPTED", "DECLINED"}:
        return "PROCEED", entry
    if not rev or not head_sha or not (repo_path / ".git").exists():
        return "DELTA_UNKNOWN", entry
    try:
        cmd = ["git", "diff", "--quiet", rev, head_sha, "--", git_rel]
        rc = subprocess.run(cmd, cwd=str(repo_path), capture_output=True, timeout=10).returncode
        return (
            ("SKIP", entry)
            if rc == 0
            else ("PROCEED", entry)
            if rc == 1
            else ("DELTA_UNKNOWN", entry)
        )
    except (subprocess.SubprocessError, OSError):
        return "DELTA_UNKNOWN", entry


def make_delta_unknown_result(up_path: str, entry: dict[str, Any], xia_cmd: str) -> dict[str, Any]:
    """Construct an orange DELTA UNKNOWN recommendation block when reviewed_sha cannot be diffed."""
    rev = str(entry.get("reviewed_sha", "?"))
    tgt = str(entry.get("target") or "_core")
    st = str(entry.get("status", "?"))
    return {
        "should_port": False,
        "status_override": "DELTA UNKNOWN",
        "color_override": "🟠",
        "score": 50,
        "recommended_tier": f"Ledger Check -> {tgt}",
        "target_bundle": "_core",
        "disable_model_invocation": True,
        "python_compatibility_assessment": "Không thể xác minh git diff từ reviewed_sha.",
        "reason": f"DELTA UNKNOWN: Mục `{up_path}` ({st}) không đối chiếu được SHA `{rev}`.",
        "actionable_steps": [f"Chạy `{xia_cmd}` hoặc fetch lịch sử để kiểm tra từ `{rev}`"],
        "xia_command": xia_cmd,
    }


def upsert_triage_ledger_yaml(cfg_path: Path, entry: dict[str, str]) -> bool:
    """Surgically upsert a triage_ledger entry in YAML while preserving all comments."""
    fields = ("source", "upstream_path", "target", "status", "reviewed_sha", "reason")
    item_txt = "\n".join(
        f"{'  - ' if i == 0 else '    '}{k}: {json.dumps(entry.get(k, ''), ensure_ascii=False)}"
        for i, k in enumerate(fields)
    )
    raw = cfg_path.read_text(encoding="utf-8") if cfg_path.exists() else ""
    m_sec = re.search(r"^triage_ledger:\s*$", raw, re.MULTILINE)
    if not m_sec:
        new_raw = (raw.rstrip() + f"\n\ntriage_ledger:\n{item_txt}\n").lstrip("\n")
    else:
        m_nx = re.search(r"^[A-Za-z0-9_-]+:\s*", raw[m_sec.end() :], re.MULTILINE)
        s_end = m_sec.end() + m_nx.start() if m_nx else len(raw)
        sec = raw[m_sec.end() : s_end]
        key = (entry["source"], entry["upstream_path"], entry["target"])
        done = False
        for m_it in re.finditer(r"(?m)^  - .*?(?=^  - |\Z)", sec, re.DOTALL):
            ld = yaml.safe_load(m_it.group(0))
            row = ld[0] if isinstance(ld, list) and ld and isinstance(ld[0], dict) else {}
            if (row.get("source"), row.get("upstream_path"), row.get("target")) == key:
                nl = "\n" if m_it.group(0).endswith("\n") else ""
                sec = sec[: m_it.start()] + item_txt + nl + sec[m_it.end() :]
                done = True
                break
        tail = sec if done else sec.rstrip("\n") + f"\n{item_txt}\n"
        new_raw = raw[: m_sec.end()] + tail + raw[s_end:]
    if not isinstance(yaml.safe_load(new_raw), dict):
        return False
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(new_raw, encoding="utf-8")
    return True
