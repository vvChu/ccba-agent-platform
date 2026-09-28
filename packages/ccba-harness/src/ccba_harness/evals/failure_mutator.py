"""failure_mutator.py - Failure-Driven Provenance Mutation Engine (Sprint 4 / ADR-0059).

Translates structured provenance failure signals from evaluation reports into
deterministic, zero-LLM-token markdown guardrail cards using the statutory
in-memory flat index (LegalFlatIndex).
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .legal_index import LegalFlatIndex, load_legal_flat_index
from .models import EvalItem, EvalReport

logger = logging.getLogger(__name__)

DEFAULT_LEDGER_DIR = Path(".md/cache/eval_failure_ledger")

ALLOWED_FAILURE_SCORERS = frozenset({"legal_verbatim_provenance", "sha256_provenance"})

VALID_FAILURE_CODES = frozenset(
    {
        "NO_CITATION",
        "EXPIRED_UNACKNOWLEDGED",
        "UNKNOWN_DOCUMENT",
        "UNKNOWN_CLAUSE",
        "WRONG_TARGET",
    }
)


@dataclass(frozen=True)
class FailureSignal:
    """Structured failure signal extracted from an evaluation report."""

    code: str
    item_id: str
    scorer: str
    fingerprint: str
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FailureLedger:
    """Persistent ledger tracking unapplied failure signals for a skill."""

    skill_name: str
    content_sha256: str
    signals: tuple[FailureSignal, ...] = field(default_factory=tuple)


def calculate_signal_fingerprint(
    scorer: str,
    code: str,
    doc: str,
    clause: str,
    item_id: str,
) -> str:
    """Calculates deterministic SHA-256 fingerprint for a failure signal."""
    raw = f"{scorer.strip()}:{code.strip()}:{doc.strip()}:{clause.strip()}:{item_id.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _resolve_items_map(
    items: list[EvalItem] | Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    """Normalizes various item collections into an id -> metadata mapping."""
    if not items:
        return {}
    if isinstance(items, Mapping):
        res: dict[str, dict[str, Any]] = {}
        for k, v in items.items():
            if isinstance(v, EvalItem):
                res[k] = v.metadata
            elif isinstance(v, dict):
                res[k] = v.get("metadata", v)
            else:
                res[k] = {}
        return res

    res_list: dict[str, dict[str, Any]] = {}
    for item in items:
        if isinstance(item, EvalItem):
            res_list[item.id] = item.metadata
        elif isinstance(item, dict):
            cid = item.get("id", "")
            if cid:
                res_list[cid] = item.get("metadata", item)
    return res_list


def _parse_no_citation(
    item_id: str,
    scorer: str,
    item_meta: dict[str, Any],
    index: LegalFlatIndex,
) -> FailureSignal:
    """Builds a FailureSignal for NO_CITATION."""
    target_law = str(item_meta.get("target_law") or item_meta.get("law") or "")
    doc_obj = index.get_document(target_law) if target_law else None
    fields: dict[str, Any] = {"target_law": target_law}
    if doc_obj:
        fields.update(
            {
                "document_number": doc_obj.document_number,
                "title": doc_obj.title,
                "cong_bao_number": doc_obj.cong_bao_number,
                "pdf_sha256": doc_obj.pdf_sha256,
            }
        )
    fp = calculate_signal_fingerprint(scorer, "NO_CITATION", target_law, "", item_id)
    return FailureSignal(
        code="NO_CITATION",
        item_id=item_id,
        scorer=scorer,
        fingerprint=fp,
        fields=fields,
    )


def _parse_expired(
    item_id: str,
    scorer: str,
    raw: dict[str, Any],
    index: LegalFlatIndex,
) -> FailureSignal:
    """Builds a FailureSignal for EXPIRED_UNACKNOWLEDGED."""
    trap_doc = str(raw.get("trap_doc") or "")
    replacement = raw.get("replacement")
    if not replacement:
        _, replacement = index.is_expired_or_replaced(trap_doc)
    replacement_str = str(replacement or "")

    rep_doc = index.get_document(replacement_str) if replacement_str else None
    fields: dict[str, Any] = {
        "trap_doc": trap_doc,
        "replacement": replacement_str,
    }
    if rep_doc:
        fields.update(
            {
                "replacement_title": rep_doc.title,
                "replacement_cong_bao": rep_doc.cong_bao_number,
                "replacement_pdf_sha256": rep_doc.pdf_sha256,
            }
        )
    fp = calculate_signal_fingerprint(scorer, "EXPIRED_UNACKNOWLEDGED", trap_doc, "", item_id)
    return FailureSignal(
        code="EXPIRED_UNACKNOWLEDGED",
        item_id=item_id,
        scorer=scorer,
        fingerprint=fp,
        fields=fields,
    )


def _parse_unknown_document(
    item_id: str,
    scorer: str,
    raw: dict[str, Any],
) -> FailureSignal:
    """Builds a FailureSignal for UNKNOWN_DOCUMENT."""
    unknown_doc = str(raw.get("unknown_doc") or "")
    fp = calculate_signal_fingerprint(scorer, "UNKNOWN_DOCUMENT", unknown_doc, "", item_id)
    return FailureSignal(
        code="UNKNOWN_DOCUMENT",
        item_id=item_id,
        scorer=scorer,
        fingerprint=fp,
        fields={"unknown_doc": unknown_doc},
    )


def _parse_unknown_clause(
    item_id: str,
    scorer: str,
    raw: dict[str, Any],
    index: LegalFlatIndex,
) -> FailureSignal:
    """Builds a FailureSignal for UNKNOWN_CLAUSE."""
    doc_num = str(raw.get("doc") or "")
    fake_clause = str(raw.get("fake_clause") or "")
    doc_obj = index.get_document(doc_num) if doc_num else None
    valid_keys: list[str] = []
    if doc_obj:
        valid_keys = list(doc_obj.statutory_keys[:8])

    fields: dict[str, Any] = {
        "doc": doc_num,
        "fake_clause": fake_clause,
        "valid_keys": valid_keys,
    }
    fp = calculate_signal_fingerprint(scorer, "UNKNOWN_CLAUSE", doc_num, fake_clause, item_id)
    return FailureSignal(
        code="UNKNOWN_CLAUSE",
        item_id=item_id,
        scorer=scorer,
        fingerprint=fp,
        fields=fields,
    )


def _parse_wrong_target(
    item_id: str,
    scorer: str,
    raw: dict[str, Any],
    index: LegalFlatIndex,
) -> FailureSignal:
    """Builds a FailureSignal for WRONG_TARGET."""
    target_law = str(raw.get("target_law") or "")
    is_exp, rep = index.is_expired_or_replaced(target_law)
    effective_target = rep if (is_exp and rep) else target_law
    doc_obj = index.get_document(effective_target) if effective_target else None

    fields: dict[str, Any] = {
        "target_law": target_law,
        "effective_target": effective_target,
        "is_expired": is_exp,
    }
    if doc_obj:
        fields.update(
            {
                "title": doc_obj.title,
                "cong_bao_number": doc_obj.cong_bao_number,
                "pdf_sha256": doc_obj.pdf_sha256,
            }
        )
    fp = calculate_signal_fingerprint(scorer, "WRONG_TARGET", target_law, "", item_id)
    return FailureSignal(
        code="WRONG_TARGET",
        item_id=item_id,
        scorer=scorer,
        fingerprint=fp,
        fields=fields,
    )


def extract_failure_signals(
    report: EvalReport,
    items: list[EvalItem] | Mapping[str, Any] | None = None,
    index: LegalFlatIndex | None = None,
) -> list[FailureSignal]:
    """Extracts structured failure signals from an evaluation report (ADR-0059).

    Only processes allowed provenance scorers and maps raw_output dictionary
    structures to typed FailureSignal instances.
    """
    flat_index = index or load_legal_flat_index()
    items_map = _resolve_items_map(items)

    signals: list[FailureSignal] = []
    seen_fps: set[str] = set()

    for item_res in report.item_results:
        item_id = item_res.item_id
        item_meta = items_map.get(item_id, {})

        for score_res in item_res.scores:
            if score_res.scorer_name not in ALLOWED_FAILURE_SCORERS:
                continue
            if score_res.score >= 1.0 and not score_res.is_critical_fail:
                continue
            raw = score_res.raw_output
            if not isinstance(raw, dict):
                continue

            sig: FailureSignal | None = None
            if raw.get("citations_found") == 0:
                sig = _parse_no_citation(item_id, score_res.scorer_name, item_meta, flat_index)
            elif "trap_doc" in raw:
                sig = _parse_expired(item_id, score_res.scorer_name, raw, flat_index)
            elif "unknown_doc" in raw:
                sig = _parse_unknown_document(item_id, score_res.scorer_name, raw)
            elif "fake_clause" in raw and "doc" in raw:
                sig = _parse_unknown_clause(item_id, score_res.scorer_name, raw, flat_index)
            elif "target_law" in raw:
                sig = _parse_wrong_target(item_id, score_res.scorer_name, raw, flat_index)

            if sig and sig.fingerprint not in seen_fps:
                seen_fps.add(sig.fingerprint)
                signals.append(sig)

    # Multi-Key Deterministic Sorting
    signals.sort(key=lambda s: (s.scorer, s.code, s.item_id, s.fingerprint))
    return signals


def render_failure_patch(
    signal: FailureSignal,
    index: LegalFlatIndex | None = None,
) -> str:
    """Renders a zero-token markdown patch card for a failure signal (ADR-0059).

    Strictly obeys the Legal Verbatim Grounding Invariant: generates metadata
    citation cards only, without hallucinating statutory text.
    """
    fp_tag = f"<!-- failure_signal: {signal.fingerprint} -->"

    if signal.code == "NO_CITATION":
        law = signal.fields.get("target_law") or "Văn bản quy phạm pháp luật"
        cb = signal.fields.get("cong_bao_number") or "N/A"
        sha = signal.fields.get("pdf_sha256") or "N/A"
        title = signal.fields.get("title") or ""
        header = f"### ⚖️ Legal Verbatim Provenance (ADR-0059) — {law}\n{fp_tag}\n"
        body = (
            f"Bắt buộc viện dẫn căn cứ pháp luật có hiệu lực:\n"
            f"- **Văn bản**: `{law}`" + (f" - *{title}*" if title else "") + "\n"
            f"- **Công báo**: `{cb}`\n"
            f"- **Mã băm kiểm chuẩn (SHA-256)**: `{sha}`\n"
        )
        return header + body

    if signal.code == "EXPIRED_UNACKNOWLEDGED":
        trap = signal.fields.get("trap_doc") or "Văn bản cũ"
        rep = signal.fields.get("replacement") or "Văn bản thay thế"
        sha = signal.fields.get("replacement_pdf_sha256") or "N/A"
        header = f"### ⚖️ Anti-Trap Grounding (ADR-0059) — {trap}\n{fp_tag}\n"
        body = (
            f"Văn bản `{trap}` đã hết hiệu lực / được thay thế bởi `{rep}`. "
            f"Bắt buộc nêu rõ tình trạng hết hiệu lực và viện dẫn văn bản thay thế:\n"
            f"- **Văn bản thay thế**: `{rep}`\n"
            f"- **Mã băm kiểm chuẩn (SHA-256)**: `{sha}`\n"
        )
        return header + body

    if signal.code == "UNKNOWN_DOCUMENT":
        unk = signal.fields.get("unknown_doc") or "Không xác định"
        header = f"### ⚖️ Zero-Hallucination Guardrail (ADR-0059) — {unk}\n{fp_tag}\n"
        body = (
            f"Cấm viện dẫn văn bản `{unk}`. Số hiệu này không tồn tại trong Công báo "
            f"nước CHXHCN Việt Nam hoặc hệ thống quy chuẩn quốc gia. "
            f"Tuyệt đối không tự ý giả định hay bịa đặt văn bản thay thế.\n"
        )
        return header + body

    if signal.code == "UNKNOWN_CLAUSE":
        doc = signal.fields.get("doc") or "Văn bản"
        fake = signal.fields.get("fake_clause") or "Điều/Khoản không xác định"
        keys = signal.fields.get("valid_keys") or []
        keys_str = ", ".join(f"`{k}`" for k in keys) if keys else "chỉ mục điều khoản"
        header = f"### ⚖️ Zero-Hallucination Guardrail (ADR-0059) — {fake}\n{fp_tag}\n"
        body = (
            f"Điều khoản/Mục `{fake}` không tồn tại trong `{doc}`. "
            f"Chỉ được viện dẫn các điều khoản/khóa hợp lệ của văn bản này (ví dụ: {keys_str}).\n"
        )
        return header + body

    if signal.code == "WRONG_TARGET":
        tgt = signal.fields.get("effective_target") or signal.fields.get("target_law") or "Văn bản"
        cb = signal.fields.get("cong_bao_number") or "N/A"
        sha = signal.fields.get("pdf_sha256") or "N/A"
        header = f"### ⚖️ Statutory Alignment (ADR-0059) — {tgt}\n{fp_tag}\n"
        body = (
            f"Bắt buộc viện dẫn chính xác văn bản mục tiêu `{tgt}` theo phạm vi điều chỉnh nghiệp vụ.\n"
            f"- **Công báo**: `{cb}`\n"
            f"- **Mã băm kiểm chuẩn (SHA-256)**: `{sha}`\n"
        )
        return header + body

    return f"### ⚖️ Legal Grounding Guardrail (ADR-0059)\n{fp_tag}\n"


def is_signal_applied(content: str, signal: FailureSignal) -> bool:
    """Checks whether a failure signal has already been applied to content."""
    if signal.fingerprint in content:
        return True
    tag = f"<!-- failure_signal: {signal.fingerprint} -->"
    return tag in content


def get_unapplied_failure_signals(
    content: str,
    signals: list[FailureSignal],
) -> list[FailureSignal]:
    """Filters signals down to those not yet applied to the skill content."""
    return [s for s in signals if not is_signal_applied(content, s)]


def save_failure_ledger(
    skill_name: str,
    signals: list[FailureSignal],
    skill_content: str,
    ledger_dir: Path | str | None = None,
) -> Path:
    """Persists unapplied failure signals into a JSON ledger."""
    target_dir = Path(ledger_dir) if ledger_dir else DEFAULT_LEDGER_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / f"{skill_name}.json"

    content_sha = hashlib.sha256(skill_content.encode("utf-8")).hexdigest()
    data = {
        "skill_name": skill_name,
        "content_sha256": content_sha,
        "signals": [asdict(s) for s in signals],
    }
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return target_file


def load_failure_ledger(
    skill_name: str,
    ledger_dir: Path | str | None = None,
) -> FailureLedger | None:
    """Loads failure ledger for a skill from JSON cache if present."""
    target_dir = Path(ledger_dir) if ledger_dir else DEFAULT_LEDGER_DIR
    target_file = target_dir / f"{skill_name}.json"
    if not target_file.exists():
        return None

    try:
        with open(target_file, encoding="utf-8") as f:
            data = json.load(f)
        raw_signals = data.get("signals", [])
        signals = tuple(
            FailureSignal(
                code=s.get("code", ""),
                item_id=s.get("item_id", ""),
                scorer=s.get("scorer", ""),
                fingerprint=s.get("fingerprint", ""),
                fields=s.get("fields", {}),
            )
            for s in raw_signals
        )
        return FailureLedger(
            skill_name=data.get("skill_name", skill_name),
            content_sha256=data.get("content_sha256", ""),
            signals=signals,
        )
    except Exception as e:
        logger.warning(f"Không thể đọc failure ledger {target_file}: {e}")
        return None
