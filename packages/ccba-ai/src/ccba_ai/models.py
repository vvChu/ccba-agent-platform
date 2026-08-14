from typing import Any

from pydantic import BaseModel, Field


class ChatUsage(BaseModel):
    """Token usage metrics for an LLM completion."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResult(BaseModel):
    """Structured LLM completion result including content and execution telemetry."""

    content: str = ""
    model: str = ""
    usage: ChatUsage = Field(default_factory=ChatUsage)
    latency_ms: float = 0.0
    raw_response: Any = None


class AuditFinding(BaseModel):
    """A standard representation of a detected design clash / coordination issue."""

    severity: str = "medium"  # high / medium / low
    location: str = ""
    disciplines: list[str] = Field(default_factory=list)
    description: str = ""
    recommendation: str = ""
    source: str = ""


class AuditReport(BaseModel):
    """A standard report representation of an audit pass on a specific level."""

    level: str
    ai_model: str
    quad_view_path: str = ""
    findings: list[AuditFinding] = Field(default_factory=list)
    summary: str = ""
    raw_response: str = ""

    @property
    def finding_count(self) -> int:
        return len(self.findings)

    @property
    def clash_count(self) -> int:
        """Backward compatibility alias for finding_count."""
        return self.finding_count

    @property
    def high_severity_count(self) -> int:
        return sum(1 for f in self.findings if f.severity.lower() == "high")

    @property
    def clashes(self) -> list[AuditFinding]:
        """Backward compatibility property returning the findings."""
        return self.findings

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with calculated properties included."""
        d = self.model_dump()
        d["finding_count"] = self.finding_count
        d["clash_count"] = self.clash_count
        d["high_severity_count"] = self.high_severity_count
        # Ensure clashes is serialized as a list of dicts for backward compatibility
        d["clashes"] = [f.model_dump() for f in self.findings]
        return d


class SEOAuditResult(BaseModel):
    """Structured report of technical SEO compliance audit."""

    score: int = 100
    checks: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    file_name: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return self.model_dump()


class TeamTask(BaseModel):
    """Structured representation of a shared team task."""

    name: str
    owner: str = "None"
    status: str = "pending"  # pending | in-progress | completed

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return self.model_dump()


class PlanCreationResult(BaseModel):
    """Structured result of creating a new development plan."""

    status: str = "success"
    plan_title: str = ""
    plan_folder: str = ""
    plan_file: str = ""
    created_files: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return self.model_dump()


class PhaseUpdateResult(BaseModel):
    """Structured result of updating a plan phase status."""

    status: str = "success"
    phase_id: str = ""
    phase_name: str = ""
    old_status: str = ""
    new_status: str = ""
    plan_file: str = ""
    phase_file: str = ""
    phase_file_updated: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return self.model_dump()


class PlanPhaseData(BaseModel):
    """Data item representing a single phase in plan status."""

    id: str
    name: str
    status: str
    file: str


class PlanStatusResult(BaseModel):
    """Structured result of querying plan status and its phases."""

    title: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    phases: list[PlanPhaseData] = Field(default_factory=list)
    plan_file: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return self.model_dump()
