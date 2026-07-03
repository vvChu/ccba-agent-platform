from pydantic import BaseModel, Field
from typing import List, Any

class AuditFinding(BaseModel):
    """A standard representation of a detected design clash / coordination issue."""
    severity: str = "medium"  # high / medium / low
    location: str = ""
    disciplines: List[str] = Field(default_factory=list)
    description: str = ""
    recommendation: str = ""
    source: str = ""

class AuditReport(BaseModel):
    """A standard report representation of an audit pass on a specific level."""
    level: str
    ai_model: str
    quad_view_path: str = ""
    findings: List[AuditFinding] = Field(default_factory=list)
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
    def clashes(self) -> List[AuditFinding]:
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
