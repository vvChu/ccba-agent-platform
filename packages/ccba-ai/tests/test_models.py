from ccba_ai import AuditFinding, AuditReport


def test_audit_finding_initialization():
    finding = AuditFinding(
        severity="high",
        location="North elevator shaft, Column B1",
        disciplines=["Arch", "KC"],
        description="Pipes clashing with structural column",
        recommendation="Reroute pipe around the column",
        source="test_engine"
    )
    assert finding.severity == "high"
    assert finding.location == "North elevator shaft, Column B1"
    assert finding.disciplines == ["Arch", "KC"]
    assert finding.description == "Pipes clashing with structural column"
    assert finding.recommendation == "Reroute pipe around the column"
    assert finding.source == "test_engine"

def test_audit_report_initialization():
    findings = [
        AuditFinding(severity="high", location="Loc A", disciplines=["MEP"], description="Clash 1"),
        AuditFinding(severity="medium", location="Loc B", disciplines=["Arch", "KC"], description="Clash 2"),
        AuditFinding(severity="low", location="Loc C", disciplines=["PCCC"], description="Clash 3")
    ]
    report = AuditReport(
        level="L2",
        ai_model="test-vision-model",
        quad_view_path="/path/to/quad.png",
        findings=findings,
        summary="Overall consistent but has 3 clashes.",
        raw_response="RAW"
    )

    assert report.level == "L2"
    assert report.ai_model == "test-vision-model"
    assert report.quad_view_path == "/path/to/quad.png"
    assert len(report.findings) == 3
    assert report.summary == "Overall consistent but has 3 clashes."
    assert report.raw_response == "RAW"

    # Test computed properties
    assert report.finding_count == 3
    assert report.clash_count == 3  # Backward compatibility alias
    assert report.high_severity_count == 1
    assert len(report.clashes) == 3  # Backward compatibility property

def test_audit_report_to_dict_serialization():
    findings = [
        AuditFinding(severity="high", location="Loc A", disciplines=["MEP"], description="Clash 1")
    ]
    report = AuditReport(
        level="L1",
        ai_model="test-model",
        quad_view_path="/path/to/quad.png",
        findings=findings,
        summary="Test summary"
    )

    d = report.to_dict()
    assert d["level"] == "L1"
    assert d["ai_model"] == "test-model"
    assert d["quad_view_path"] == "/path/to/quad.png"
    assert d["finding_count"] == 1
    assert d["clash_count"] == 1
    assert d["high_severity_count"] == 1
    assert d["summary"] == "Test summary"

    # Check clashes array serialization
    assert isinstance(d["clashes"], list)
    assert len(d["clashes"]) == 1
    assert d["clashes"][0]["severity"] == "high"
    assert d["clashes"][0]["location"] == "Loc A"
    assert d["clashes"][0]["disciplines"] == ["MEP"]
