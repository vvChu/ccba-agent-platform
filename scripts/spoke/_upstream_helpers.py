"""Declarative governance, license classification, and report hygiene helpers for Upstream Radar."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

_CANONICAL_YAML = Path(__file__).resolve().parents[2] / ".md/knowledge/upstream_sources.yaml"
_RX_MODE = r"--(?:port|improve|copy-raw)\b"
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
    m_lr = {**(blr if isinstance(blr, dict) else {}), **(rlr if isinstance(rlr, dict) else {})}
    rules = {str(k): [str(p) for p in v] for k, v in m_lr.items() if isinstance(v, list) and v}
    hyg, led = raw.get("report_hygiene"), raw.get("triage_ledger")
    h_d = hyg if isinstance(hyg, dict) else {}
    t_led = [e for e in led if isinstance(e, dict)] if isinstance(led, list) else []
    return {"aliases": al, "license_rules": rules, "report_hygiene": h_d, "triage_ledger": t_led}


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
    if any(tok in low for tok in active.get("permissive_tokens", [])):
        if "mit license" in low or "permission is hereby granted" in low:
            return "PERMISSIVE", "MIT License (Tự do sử dụng)"
        lbl = "Apache 2.0" if "apache license" in low else "BSD" if "bsd" in low else "ISC/0BSD"
        return "PERMISSIVE", f"{lbl} License (Tự do sử dụng)"
    if any(tok in low for tok in active.get("proprietary_tokens", [])):
        return "PROPRIETARY", "Bản quyền đóng (Không được sao chép)"
    return "UNKNOWN", "Custom license: cần kiểm tra thủ công"


def clamp_license_policy(result: dict[str, Any], license_type: str, xia_cmd: str) -> dict[str, Any]:
    """Clamp evaluation result to --compare when repository license is not PERMISSIVE."""
    if license_type == "PERMISSIVE":
        return result
    steps = [re.sub(_RX_MODE, "--compare", str(s)) for s in result.get("actionable_steps", [])]
    out = {**result, "should_port": False, "color_override": "🟠", "xia_command": xia_cmd}
    out.update(status_override="COMPARE ONLY — LICENSE RESTRICTED", actionable_steps=steps)
    return out


def prune_stale_recommendations(rec_file: Path) -> int:
    """Prune legacy simulated/ADR-0040/duplicate blocks solely within AUTO-GENERATED markers."""
    if not rec_file.exists():
        return 0
    content = rec_file.read_text(encoding="utf-8")
    pat = r"(<!-- AUTO-GENERATED-START -->\s*)(.*?)(\s*<!-- AUTO-GENERATED-END -->)"
    m = re.search(pat, content, re.DOTALL)
    if not m:
        return 0
    hyg = load_governance_config(_CANONICAL_YAML)["report_hygiene"]
    stale_toks = tuple(str(x) for x in hyg.get("stale_block_tokens", []))
    rest_mks = tuple(str(x) for x in hyg.get("restricted_license_markers", []))
    old_h, new_h = "### 🟢 [RECOMMEND PORT]", "### 🟠 [COMPARE ONLY — LICENSE RESTRICTED]"
    kept, pruned = [], 0
    for part in (p.strip() for p in re.split(r"\n---\n?", m.group(2).strip()) if p.strip()):
        if part.startswith("### ") and any(t in part for t in stale_toks):
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
        if any(x in rel for x in (".git/", "node_modules/", ".md/scratch/")):
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
