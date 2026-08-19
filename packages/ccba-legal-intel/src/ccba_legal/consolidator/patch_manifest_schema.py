"""Patch Manifest YAML Schema and Dataclasses for Legislative Consolidation."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
import yaml


class DocMode(str, Enum):
    """Document hierarchy mode for AST parsing."""
    QCVN = "qcvn"
    TCVN = "tcvn"
    LUAT = "luat"
    NGHI_DINH = "nghi_dinh"
    THONG_TU = "thong_tu"


class PatchAction(str, Enum):
    """Actions applicable to AST nodes during patching."""
    REPLACE = "REPLACE"
    INSERT_AFTER = "INSERT_AFTER"
    INSERT_BEFORE = "INSERT_BEFORE"
    APPEND = "APPEND"
    INSERT_RANGE_AFTER = "INSERT_RANGE_AFTER"
    REPEAL = "REPEAL"
    SUSPEND = "SUSPEND"
    SUBSTITUTE_PHRASE = "SUBSTITUTE_PHRASE"


class DefectSeverity(str, Enum):
    """Compliance audit defect severity."""
    CRITICAL_DEFECT = "CRITICAL_DEFECT"
    WARNING_NOTICE = "WARNING_NOTICE"
    INFORMATIVE = "INFORMATIVE"


@dataclass
class PatchItem:
    """Individual patch instruction adhering to OKF v2.0."""
    action: PatchAction
    target_anchor: str
    citation: str
    new_anchor: str | None = None
    new_anchors: list[str] = field(default_factory=list)
    new_content_inline: str | None = None
    new_content_source: str | None = None
    old_text_anchor: str | None = None
    old_phrase: str | None = None
    new_phrase: str | None = None
    defect_severity: DefectSeverity = DefectSeverity.WARNING_NOTICE
    jurisdiction: str | None = None
    grace_period_end: str | None = None
    source_pdf_page: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PatchItem":
        action_val = data.get("action", "REPLACE")
        if isinstance(action_val, str):
            action = PatchAction(action_val.upper())
        else:
            action = action_val

        sev_val = data.get("defect_severity", "WARNING_NOTICE")
        if isinstance(sev_val, str):
            sev = DefectSeverity(sev_val.upper())
        else:
            sev = sev_val

        return cls(
            action=action,
            target_anchor=str(data.get("target_anchor", "")),
            citation=str(data.get("citation", "")),
            new_anchor=data.get("new_anchor"),
            new_anchors=data.get("new_anchors", []),
            new_content_inline=data.get("new_content_inline"),
            new_content_source=data.get("new_content_source"),
            old_text_anchor=data.get("old_text_anchor"),
            old_phrase=data.get("old_phrase"),
            new_phrase=data.get("new_phrase"),
            defect_severity=sev,
            jurisdiction=data.get("jurisdiction"),
            grace_period_end=data.get("grace_period_end"),
            source_pdf_page=data.get("source_pdf_page"),
        )

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "action": self.action.value,
            "target_anchor": self.target_anchor,
            "citation": self.citation,
            "defect_severity": self.defect_severity.value,
        }
        if self.new_anchor:
            res["new_anchor"] = self.new_anchor
        if self.new_anchors:
            res["new_anchors"] = self.new_anchors
        if self.new_content_inline:
            res["new_content_inline"] = self.new_content_inline
        if self.new_content_source:
            res["new_content_source"] = self.new_content_source
        if self.old_text_anchor:
            res["old_text_anchor"] = self.old_text_anchor
        if self.old_phrase:
            res["old_phrase"] = self.old_phrase
        if self.new_phrase:
            res["new_phrase"] = self.new_phrase
        if self.jurisdiction:
            res["jurisdiction"] = self.jurisdiction
        if self.grace_period_end:
            res["grace_period_end"] = self.grace_period_end
        if self.source_pdf_page:
            res["source_pdf_page"] = self.source_pdf_page
        return res


@dataclass
class PatchManifest:
    """Complete patch manifest specifying all delta modifications."""
    target_doc_id: str
    amending_doc_id: str
    doc_mode: DocMode
    title: str = ""
    official_citation: str = ""
    effective_date: str = ""
    default_cong_bao_number: str = "373/2026"
    default_jurisdiction: str = "CQXD"
    patches: list[PatchItem] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PatchManifest":
        mode_val = data.get("doc_mode", "qcvn")
        if isinstance(mode_val, str):
            doc_mode = DocMode(mode_val.lower())
        else:
            doc_mode = mode_val

        patches_data = data.get("patches", [])
        patches = [PatchItem.from_dict(p) for p in patches_data]

        return cls(
            target_doc_id=str(data.get("target_doc_id", "")),
            amending_doc_id=str(data.get("amending_doc_id", "")),
            doc_mode=doc_mode,
            title=str(data.get("title", "")),
            official_citation=str(data.get("official_citation", "")),
            effective_date=str(data.get("effective_date", "")),
            default_cong_bao_number=str(data.get("default_cong_bao_number", "373/2026")),
            default_jurisdiction=str(data.get("default_jurisdiction", "CQXD")),
            patches=patches,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_doc_id": self.target_doc_id,
            "amending_doc_id": self.amending_doc_id,
            "doc_mode": self.doc_mode.value,
            "title": self.title,
            "official_citation": self.official_citation,
            "effective_date": self.effective_date,
            "patches": [p.to_dict() for p in self.patches],
        }

    def validate(self) -> list[str]:
        """Validate internal consistency of the patch manifest."""
        errors: list[str] = []
        if not self.target_doc_id:
            errors.append("Missing target_doc_id")
        if not self.amending_doc_id:
            errors.append("Missing amending_doc_id")
        if not self.patches:
            errors.append("Manifest contains 0 patches")

        for idx, p in enumerate(self.patches):
            if not p.target_anchor:
                errors.append(f"Patch #{idx+1} ({p.action.value}): missing target_anchor")
            if not p.citation:
                errors.append(f"Patch #{idx+1} ({p.action.value}): missing citation")
            if p.action in (PatchAction.INSERT_AFTER, PatchAction.INSERT_BEFORE) and not p.new_anchor:
                errors.append(f"Patch #{idx+1} ({p.action.value}): missing new_anchor")
            if p.action == PatchAction.INSERT_RANGE_AFTER and not p.new_anchors:
                errors.append(f"Patch #{idx+1} (INSERT_RANGE_AFTER): missing new_anchors list")
            if p.action == PatchAction.SUBSTITUTE_PHRASE and (not p.old_phrase or not p.new_phrase):
                errors.append(f"Patch #{idx+1} (SUBSTITUTE_PHRASE): missing old_phrase or new_phrase")
        return errors


def load_manifest(yaml_path: Path | str) -> PatchManifest:
    """Load and validate a PatchManifest from a YAML file."""
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML manifest structure in {path}")

    manifest = PatchManifest.from_dict(data)
    errors = manifest.validate()
    if errors:
        raise ValueError(f"Manifest validation failed ({len(errors)} errors):\n" + "\n".join(f"- {e}" for e in errors))

    return manifest
