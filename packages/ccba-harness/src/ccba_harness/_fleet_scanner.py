"""Sanitized cross-spoke telemetry scanning and aggregation helpers (ADR-0046, ADR-0058)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from ccba_maskara import redact_secrets_and_pii as _maskara_redact
except ImportError:
    _maskara_redact = None  # type: ignore[assignment]

# Default token budget heuristics per Spoke (e.g., 5M tokens per monthly cycle)
DEFAULT_SPOKE_BUDGET_TOKENS = 5_000_000

_HASHED_SPOKE_ID_RE = re.compile(r"^spoke-[0-9a-f]{16}$")
_UNIX_MACHINE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_.:/-])/(?:home|Users|root|mnt|var|tmp|opt)/[^\s\"'<>`|\\]+"
)
_WIN_MACHINE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/][^\s\"'<>`|]+")
_NOISY_TOOL_TOKENS: tuple[str, ...] = ("unknown", "error", "retry", "undefined")

# Standard agent built-ins and platform utilities excluded from Spoke domain innovations
STANDARD_BUILTIN_TOOLS: frozenset[str] = frozenset(
    {
        "run_command",
        "view_file",
        "view_file_outline",
        "view_code_item",
        "read_file",
        "write_file",
        "write_to_file",
        "edit_file",
        "replace_file_content",
        "multi_replace_file_content",
        "delete_file",
        "grep_search",
        "find_by_name",
        "list_dir",
        "manage_task",
        "send_message",
        "schedule",
        "invoke_subagent",
        "define_subagent",
        "manage_subagents",
        "generate_image",
        "read_url_content",
        "search_web",
        "ask_question",
        "call_mcp_tool",
        "list_resources",
        "read_resource",
        "gemini_search_docs",
        "gemini_get_doc",
        "update_focus",
        "update_steps",
        "run_workflow",
        "search_marketplace",
        "list_plugin_accounts",
        "swarm",
        "command_status",
        "send_command_input",
        "read_terminal",
        "browser_subagent",
        "notify_user",
    }
)


def compute_spoke_id(
    raw_spoke_id: str = "",
    project_name: str = "",
    project_path: str = "",
) -> str:
    """Compute a deterministic one-way SHA-256 spoke identifier (COND-SPOKE-HASH)."""
    candidate = (raw_spoke_id or "").strip().lower()
    if _HASHED_SPOKE_ID_RE.match(candidate):
        return candidate
    normalized_path = (project_path or "").strip().replace("\\", "/").rstrip("/").lower()
    seed = candidate or (project_name or "").strip().lower() or normalized_path or "unknown-spoke"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"spoke-{digest}"


def sanitize_telemetry_text(text: str) -> str:
    """Redact credentials, PII, and absolute machine paths via ccba-maskara at the Spoke edge."""
    if not text:
        return ""
    if _maskara_redact is not None:
        cleaned = _maskara_redact(text, dialect="bracket_suffix")
    else:
        from .evals._miner_catalog import redact_sensitive_info

        cleaned = redact_sensitive_info(text)
    cleaned = _UNIX_MACHINE_PATH_RE.sub("[PATH_REDACTED]", cleaned)
    cleaned = _WIN_MACHINE_PATH_RE.sub("[PATH_REDACTED]", cleaned)
    return cleaned


def _sanitize_tool_count_map(raw_map: Any) -> dict[str, int]:
    """Sanitize and normalize a tool count mapping into positive integer counts."""
    if not isinstance(raw_map, dict):
        return {}
    clean: dict[str, int] = {}
    for key, val in raw_map.items():
        name = sanitize_telemetry_text(str(key)).strip()
        if not name:
            continue
        try:
            count = int(val)
        except (TypeError, ValueError):
            continue
        if count > 0:
            clean[name] = clean.get(name, 0) + count
    return dict(sorted(clean.items()))


@dataclass
class SpokeTelemetrySummary:
    """Sanitized, aggregated telemetry metrics for a single Spoke project (ADR-0046).

    Note: ``project_name`` and ``project_path`` remain accepted by the constructor for
    in-memory backward compatibility, but are NEVER emitted in Hub/JSON/Markdown exports
    (COND-PII-EXPORT, COND-SPOKE-HASH).
    """

    spoke_id: str
    project_name: str = ""
    project_path: str = ""
    project_type: str = "Chưa phân loại"
    is_sandbox: bool = False
    is_online: bool = True
    last_sync: str = ""
    total_sessions: int = 0
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost_usd: float = 0.0
    tool_counts: dict[str, int] = field(default_factory=dict)
    tool_error_counts: dict[str, int] = field(default_factory=dict)
    budget_limit_tokens: int = DEFAULT_SPOKE_BUDGET_TOKENS
    budget_status: str = (
        "Compliant"  # Compliant, Warning, Exceeded, Offline / Cached, NO_DATA, PARSE_ERROR
    )

    @property
    def anonymized_spoke_id(self) -> str:
        """Return the deterministic one-way SHA-256 spoke identifier for safe Hub export."""
        return compute_spoke_id(self.spoke_id, self.project_name, self.project_path)

    def to_dict(self) -> dict[str, Any]:
        """Convert Spoke summary to a Maskara-sanitized dictionary with zero project paths/names."""
        return {
            "spoke_id": self.anonymized_spoke_id,
            "project_type": sanitize_telemetry_text(self.project_type),
            "is_sandbox": self.is_sandbox,
            "is_online": self.is_online,
            "last_sync": sanitize_telemetry_text(self.last_sync),
            "total_sessions": self.total_sessions,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "tool_counts": _sanitize_tool_count_map(self.tool_counts),
            "tool_error_counts": _sanitize_tool_count_map(self.tool_error_counts),
            "budget_limit_tokens": self.budget_limit_tokens,
            "budget_status": sanitize_telemetry_text(self.budget_status),
        }


def _collect_tool_innovations(
    spokes: list[SpokeTelemetrySummary],
    fleet_tool_counts: dict[str, int],
) -> tuple[dict[str, list[str]], dict[str, int], dict[str, int]]:
    """Aggregate custom domain tool counts, errors, and anonymized source Spokes."""
    tool_spokes_map: dict[str, list[str]] = {}
    tool_total_calls: dict[str, int] = {}
    tool_error_calls: dict[str, int] = {}
    for spoke in spokes:
        spoke_label = spoke.anonymized_spoke_id
        for raw_name, count in spoke.tool_counts.items():
            tool_name = sanitize_telemetry_text(raw_name).strip()
            if not tool_name or tool_name in STANDARD_BUILTIN_TOOLS:
                continue
            if tool_name not in tool_spokes_map:
                tool_spokes_map[tool_name] = []
                tool_total_calls[tool_name] = 0
                tool_error_calls[tool_name] = 0
            if spoke_label not in tool_spokes_map[tool_name]:
                tool_spokes_map[tool_name].append(spoke_label)
            tool_total_calls[tool_name] += count
        for raw_err_name, err_count in spoke.tool_error_counts.items():
            err_name = sanitize_telemetry_text(raw_err_name).strip()
            if err_name in tool_error_calls:
                tool_error_calls[err_name] += max(0, int(err_count))

    for raw_name, count in fleet_tool_counts.items():
        tool_name = sanitize_telemetry_text(raw_name).strip()
        if (
            tool_name
            and tool_name not in STANDARD_BUILTIN_TOOLS
            and tool_name not in tool_total_calls
        ):
            tool_total_calls[tool_name] = count
            tool_spokes_map[tool_name] = ["Fleet Aggregate"]
            tool_error_calls[tool_name] = 0
    return tool_spokes_map, tool_total_calls, tool_error_calls


def _is_noisy_tool_name(tool_name: str) -> bool:
    """Return True when tool name indicates placeholder, error, or retry noise."""
    lower = tool_name.lower()
    return any(tok in lower for tok in _NOISY_TOOL_TOKENS)


def _classify_innovations(
    tool_spokes_map: dict[str, list[str]],
    tool_total_calls: dict[str, int],
    candidate_threshold: int,
    tool_error_calls: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """Classify and deterministically sort domain innovation candidates, filtering retry loops."""
    errors_map = tool_error_calls or {}
    innovations: list[dict[str, Any]] = []
    for tool_name, total_calls in tool_total_calls.items():
        if _is_noisy_tool_name(tool_name):
            continue
        spoke_sources = sorted(tool_spokes_map.get(tool_name, []))
        error_calls = max(0, int(errors_map.get(tool_name, 0)))
        success_calls = max(0, total_calls - error_calls)
        is_retry_loop = error_calls > 0 and error_calls >= success_calls
        if is_retry_loop:
            promotion_status = "Retry / Error Loop (Excluded)"
            recommendation = (
                "High failure/retry ratio detected; inspect tool reliability before Hub promotion"
            )
        else:
            is_candidate = success_calls >= candidate_threshold or (
                len(spoke_sources) >= 2 and success_calls >= 2
            )
            promotion_status = (
                "Candidate for Hub Ingestion" if is_candidate else "Spoke Local Innovation"
            )
            recommendation = (
                "Recommend promoting to Hub Monorepo via ADR-0045 / ADR-0046 proposal "
                "(.agents/proposals/TEMPLATE.md)"
                if is_candidate
                else "Retain as Spoke local innovation until cross-project demand emerges"
            )
        innovations.append(
            {
                "tool_or_skill": tool_name,
                "total_calls": total_calls,
                "error_calls": error_calls,
                "success_calls": success_calls,
                "source_spokes": spoke_sources,
                "category": "Domain Innovation",
                "promotion_status": promotion_status,
                "recommendation": recommendation,
            }
        )
    innovations.sort(key=lambda x: (-x["success_calls"], -x["total_calls"], x["tool_or_skill"]))
    return innovations


def _format_fleet_markdown_summary(report: FleetTelemetryReport) -> list[str]:
    """Render Markdown sections 1 & 2 (Fleet rollup and domain distribution)."""
    lines = [
        f"# 🌐 CCBA Fleet-Wide Cross-Spoke Telemetry Report: `{sanitize_telemetry_text(report.hub_name)}`",
        "",
        "## 1. Enterprise Fleet Rollup",
        "",
        f"- **Total Registered Spokes:** {report.total_spokes} ({report.online_spokes} Online)",
        f"- **Total Fleet Tokens Consumed:** {report.total_fleet_tokens:,}",
        f"- **Total Prompt Tokens (Context):** {report.total_prompt_tokens:,}",
        f"- **Total Completion Tokens (Gen):** {report.total_completion_tokens:,}",
        f"- **Total Fleet Cost:** ${report.total_fleet_cost_usd:.4f} USD",
        "",
        "## 2. Project Distribution by Domain",
        "",
    ]
    for p_type, count in sorted(report.spokes_by_type.items()):
        lines.append(f"- **{sanitize_telemetry_text(p_type)}:** {count} project(s)")
    return lines


def _format_fleet_markdown_spokes(report: FleetTelemetryReport) -> list[str]:
    """Render Markdown section 3 (Spoke comparison matrix) with anonymized spoke_id only."""
    lines = [
        "",
        "## 3. Spoke Comparison Matrix",
        "",
        "| Spoke ID | Domain | Status | Sessions | Tokens Consumed | Cost (USD) | Budget Status |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for s in sorted(report.spokes, key=lambda x: (-x.total_tokens, x.anonymized_spoke_id)):
        status_badge = "Online" if s.is_online else "Offline"
        lines.append(
            f"| `{s.anonymized_spoke_id}` | {sanitize_telemetry_text(s.project_type)} | {status_badge} | "
            f"{s.total_sessions} | {s.total_tokens:,} | ${s.total_cost_usd:.4f} | "
            f"{sanitize_telemetry_text(s.budget_status)} |"
        )
    return lines


def _format_fleet_markdown_innovations(report: FleetTelemetryReport) -> list[str]:
    """Render Markdown section 4 (Top Spoke innovations table)."""
    lines = [
        "",
        "## 4. Top Spoke Innovations & Candidates for Hub Ingestion (ADR-0045, ADR-0046)",
        "",
        "| Tool / Custom Skill | Invocations | Source Spokes | Status | Recommendation |",
        "| :--- | :---: | :--- | :---: | :--- |",
    ]
    innovations = report.get_top_spoke_innovations()
    if not innovations:
        lines.append(
            "| _None_ | 0 | _No Spoke-local domain innovations detected_ | Compliant | Retain standard catalog |"
        )
        return lines
    for item in innovations:
        spokes_str = ", ".join(item["source_spokes"])
        lines.append(
            f"| `{item['tool_or_skill']}` | {item['total_calls']} | {spokes_str} | "
            f"{item['promotion_status']} | {item['recommendation']} |"
        )
    return lines


@dataclass
class FleetTelemetryReport:
    """Aggregated enterprise fleet telemetry report across multiple Spoke projects."""

    hub_name: str
    spokes: list[SpokeTelemetrySummary] = field(default_factory=list)
    total_spokes: int = 0
    online_spokes: int = 0
    total_fleet_tokens: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_fleet_cost_usd: float = 0.0
    spokes_by_type: dict[str, int] = field(default_factory=dict)
    fleet_tool_counts: dict[str, int] = field(default_factory=dict)
    top_spoke_innovations: list[dict[str, Any]] = field(default_factory=list)

    def get_top_spoke_innovations(self, candidate_threshold: int = 5) -> list[dict[str, Any]]:
        """Extract, rank, and classify cross-spoke tools and local innovations (ADR-0045, ADR-0046)."""
        tool_spokes_map, tool_total_calls, tool_error_calls = _collect_tool_innovations(
            self.spokes, self.fleet_tool_counts
        )
        return _classify_innovations(
            tool_spokes_map,
            tool_total_calls,
            candidate_threshold,
            tool_error_calls=tool_error_calls,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert fleet report to a Maskara-sanitized dictionary with anonymized spoke IDs."""
        return {
            "hub_name": sanitize_telemetry_text(self.hub_name),
            "total_spokes": self.total_spokes,
            "online_spokes": self.online_spokes,
            "total_fleet_tokens": self.total_fleet_tokens,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_fleet_cost_usd": round(self.total_fleet_cost_usd, 4),
            "spokes_by_type": {
                sanitize_telemetry_text(k): v for k, v in sorted(self.spokes_by_type.items())
            },
            "fleet_tool_counts": _sanitize_tool_count_map(self.fleet_tool_counts),
            "top_spoke_innovations": self.get_top_spoke_innovations(),
            "spokes": [s.to_dict() for s in self.spokes],
        }

    def to_markdown(self) -> str:
        """Format fleet report into clean, Maskara-sanitized GitHub-flavored Markdown."""
        lines = [
            *_format_fleet_markdown_summary(self),
            *_format_fleet_markdown_spokes(self),
            *_format_fleet_markdown_innovations(self),
        ]
        return sanitize_telemetry_text("\n".join(lines).strip()) + "\n"


def _resolve_budget_status(tot_tok: int, budget_limit: int) -> str:
    """Resolve Compliant / Warning / Exceeded status for a token total vs budget."""
    if tot_tok > budget_limit:
        return "Exceeded"
    if tot_tok > (budget_limit * 0.8):
        return "Warning"
    return "Compliant"


def _parse_summary_json(
    summary_file: Path,
    meta: tuple[str, str, bool, str],
) -> SpokeTelemetrySummary | None:
    """Parse pre-compiled `.md/data/telemetry_summary.json` into a SpokeTelemetrySummary."""
    hashed_id, project_type, is_sandbox, last_sync = meta
    try:
        data = json.loads(summary_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None
        tot_tok = int(data.get("total_tokens", 0))
        b_limit = int(data.get("budget_limit_tokens", DEFAULT_SPOKE_BUDGET_TOKENS))
        return SpokeTelemetrySummary(
            spoke_id=hashed_id,
            project_name="",
            project_path="",
            project_type=sanitize_telemetry_text(project_type),
            is_sandbox=is_sandbox,
            is_online=True,
            last_sync=sanitize_telemetry_text(last_sync),
            total_sessions=int(data.get("total_sessions", 1)),
            total_tokens=tot_tok,
            prompt_tokens=int(data.get("prompt_tokens", 0)),
            completion_tokens=int(data.get("completion_tokens", 0)),
            total_cost_usd=float(data.get("total_cost_usd", 0.0)),
            tool_counts=_sanitize_tool_count_map(data.get("tool_counts", {})),
            tool_error_counts=_sanitize_tool_count_map(data.get("tool_error_counts", {})),
            budget_limit_tokens=b_limit,
            budget_status=_resolve_budget_status(tot_tok, b_limit),
        )
    except Exception:
        return None


def _parse_swarm_dashboard_html(
    report_html: Path,
    meta: tuple[str, str, bool, str],
) -> SpokeTelemetrySummary | None:
    """Extract sanitized JSON metrics embedded in `.md/reports/swarm_telemetry_dashboard.html`."""
    hashed_id, project_type, is_sandbox, last_sync = meta
    try:
        content = report_html.read_text(encoding="utf-8")
        marker_start = '<script id="telemetry-data" type="application/json">'
        marker_end = "</script>"
        if marker_start not in content or marker_end not in content:
            return None
        s_idx = content.index(marker_start) + len(marker_start)
        e_idx = content.index(marker_end, s_idx)
        parsed = json.loads(content[s_idx:e_idx].strip())
        if not isinstance(parsed, dict):
            return None
        swarm_tools: dict[str, int] = {}
        for sub in parsed.get("subagents", []):
            if isinstance(sub, dict):
                for t_name, count in (sub.get("tool_counts") or {}).items():
                    swarm_tools[t_name] = swarm_tools.get(t_name, 0) + int(count)
        tot_tok = int(parsed.get("total_swarm_tokens", 0))
        b_limit = DEFAULT_SPOKE_BUDGET_TOKENS
        return SpokeTelemetrySummary(
            spoke_id=hashed_id,
            project_name="",
            project_path="",
            project_type=sanitize_telemetry_text(project_type),
            is_sandbox=is_sandbox,
            is_online=True,
            last_sync=sanitize_telemetry_text(last_sync),
            total_sessions=max(1, int(parsed.get("total_subagents", 1))),
            total_tokens=tot_tok,
            prompt_tokens=int(parsed.get("total_prompt_tokens", 0)),
            completion_tokens=int(parsed.get("total_completion_tokens", 0)),
            total_cost_usd=float(parsed.get("total_cost_usd", 0.0)),
            tool_counts=_sanitize_tool_count_map(swarm_tools),
            budget_limit_tokens=b_limit,
            budget_status=_resolve_budget_status(tot_tok, b_limit),
        )
    except Exception:
        return None


def scan_spoke_telemetry(spoke_dict: dict[str, Any]) -> SpokeTelemetrySummary:
    """Scan and safely extract Maskara-sanitized telemetry from a single Spoke (fail-closed)."""
    project_name = str(spoke_dict.get("name", ""))
    project_path_str = str(spoke_dict.get("path", ""))
    project_type = sanitize_telemetry_text(str(spoke_dict.get("project_type", "Chưa phân loại")))
    last_sync = sanitize_telemetry_text(str(spoke_dict.get("last_sync", "")))
    is_sandbox = bool(spoke_dict.get("is_sandbox", False))
    hashed_id = compute_spoke_id(
        str(spoke_dict.get("spoke_id", "")), project_name, project_path_str
    )
    meta = (hashed_id, project_type, is_sandbox, last_sync)

    p = Path(project_path_str)
    if not project_path_str or not p.exists() or not p.is_dir():
        return SpokeTelemetrySummary(
            spoke_id=hashed_id,
            project_type=project_type,
            is_sandbox=is_sandbox,
            is_online=False,
            last_sync=last_sync,
            budget_status="Offline / Cached",
        )

    parse_failed = False
    summary_file = p / ".md" / "data" / "telemetry_summary.json"
    if summary_file.exists():
        parsed_summary = _parse_summary_json(summary_file, meta)
        if parsed_summary is not None:
            return parsed_summary
        parse_failed = True

    report_html = p / ".md" / "reports" / "swarm_telemetry_dashboard.html"
    if report_html.exists():
        parsed_html = _parse_swarm_dashboard_html(report_html, meta)
        if parsed_html is not None:
            return parsed_html
        parse_failed = True

    return SpokeTelemetrySummary(
        spoke_id=hashed_id,
        project_type=project_type,
        is_sandbox=is_sandbox,
        is_online=False,
        last_sync=last_sync,
        budget_status="PARSE_ERROR" if parse_failed else "NO_DATA",
    )


def _load_registered_spokes(
    root: Path,
    spokes_list: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Resolve spoke metadata list either from explicit override or encrypted registry."""
    if spokes_list is not None:
        return spokes_list
    try:
        from scripts.spoke.decrypt_spoke_registry import get_registered_spokes

        return get_registered_spokes(root)
    except Exception:
        return []


def aggregate_fleet_telemetry(
    hub_root: Path | None = None,
    spokes_list: list[dict[str, Any]] | None = None,
) -> FleetTelemetryReport:
    """Aggregate Maskara-sanitized telemetry figures across the entire enterprise Spoke fleet."""
    root = hub_root or Path.cwd()
    registered = _load_registered_spokes(root, spokes_list)
    summaries: list[SpokeTelemetrySummary] = []
    spokes_by_type: dict[str, int] = {}
    fleet_tools: dict[str, int] = {}

    for s_info in registered:
        summary = scan_spoke_telemetry(s_info)
        summaries.append(summary)
        p_type = summary.project_type or "Chưa phân loại"
        spokes_by_type[p_type] = spokes_by_type.get(p_type, 0) + 1
        for t_name, count in summary.tool_counts.items():
            fleet_tools[t_name] = fleet_tools.get(t_name, 0) + count

    report = FleetTelemetryReport(
        hub_name=sanitize_telemetry_text(root.name),
        spokes=summaries,
        total_spokes=len(summaries),
        online_spokes=sum(1 for s in summaries if s.is_online),
        total_fleet_tokens=sum(s.total_tokens for s in summaries),
        total_prompt_tokens=sum(s.prompt_tokens for s in summaries),
        total_completion_tokens=sum(s.completion_tokens for s in summaries),
        total_fleet_cost_usd=sum(s.total_cost_usd for s in summaries),
        spokes_by_type=spokes_by_type,
        fleet_tool_counts=fleet_tools,
    )
    report.top_spoke_innovations = report.get_top_spoke_innovations()
    return report
