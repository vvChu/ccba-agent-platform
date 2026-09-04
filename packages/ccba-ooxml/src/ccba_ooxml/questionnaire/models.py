"""Data models for CCBA Dual-Track Questionnaire Engine v2.0.

Defines the structure for questionnaire metadata, questions (both hypothesis matrix
and open-ended), options, and resolution logs.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class QuestionType(str, Enum):
    """Classification of questionnaire question types."""

    HYPOTHESIS_MATRIX = "hypothesis_matrix"
    OPEN_ENDED = "open_ended"


@dataclass
class QuestionOption:
    """A single option within a hypothesis matrix question."""

    key: str  # "A", "B", "C", "D", etc.
    label: str  # Description of this option
    trade_off: str = ""  # Trade-off summary (cost, schedule, risk, performance)
    is_recommended: bool = False  # True if flagged as Standard / CCBA Recommended (⭐)
    is_selected: bool = False  # True if chosen by client/partner


@dataclass
class QuestionItem:
    """A question entry within the questionnaire."""

    id: int  # Sequential question number (1, 2, 3...)
    title: str  # Short description of the question / technical decision
    why_it_matters: str = ""  # Background rationale / impact of decision
    q_type: QuestionType = QuestionType.HYPOTHESIS_MATRIX
    options: list[QuestionOption] = field(default_factory=list)
    freeform_reply: str = ""  # Text reply for OPEN_ENDED questions
    client_note: str = ""  # Custom notes / feedback from client

    def get_option(self, key: str) -> QuestionOption | None:
        """Find an option by its key (case-insensitive)."""
        clean_key = key.strip().upper()
        for opt in self.options:
            if opt.key.strip().upper() == clean_key:
                return opt
        return None

    def select_option(self, key: str) -> None:
        """Select one option and unselect all others (idempotent single choice)."""
        clean_key = key.strip().upper()
        target = self.get_option(clean_key)
        if not target:
            valid_keys = [opt.key for opt in self.options]
            raise ValueError(
                f"Option '{clean_key}' not found in Question {self.id}. Valid options: {valid_keys}"
            )
        for opt in self.options:
            opt.is_selected = (opt.key.strip().upper() == clean_key)


@dataclass
class QuestionnaireMetadata:
    """Metadata describing the questionnaire context, parties, and status."""

    title: str = "BẢNG HỎI LẤY Ý KIẾN THIẾT KẾ"
    project_name: str = ""
    doc_code: str = ""
    sender: str = ""
    recipient: str = ""
    purpose: str = ""
    track: str = "delivery"  # "platform" or "delivery"
    status: str = "PENDING"  # "PENDING" or "RESOLVED"
    deadline: str = ""
    created_at: str = ""
    resolved_at: str = ""
    resolved_by: str = ""


@dataclass
class QuestionnaireData:
    """Complete questionnaire data bundle containing metadata, context, and questions."""

    metadata: QuestionnaireMetadata = field(default_factory=QuestionnaireMetadata)
    context: str = ""
    instructions: str = ""
    questions: list[QuestionItem] = field(default_factory=list)
    additional_notes: str = ""

    def get_question(self, qid: int) -> QuestionItem | None:
        """Find a question by its 1-indexed ID."""
        for q in self.questions:
            if q.id == qid:
                return q
        return None
