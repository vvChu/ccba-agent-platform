"""Declarative governance, license classification, and report hygiene helpers for Upstream Radar."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

_CANONICAL_YAML = Path(__file__).resolve().parents[2] / ".md/knowledge/upstream_sources.yaml"
_RX_MODE = r"--(?:port|improve|copy-raw)\b"


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
