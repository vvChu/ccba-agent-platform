from ccba_ai import AuditFinding, AuditReport


def test_audit_finding_initialization():
    finding = AuditFinding(
        severity="high",
        location="North elevator shaft, Column B1",
        disciplines=["Arch", "KC"],
        description="Pipes clashing with structural column",
        recommendation="Reroute pipe around the column",
        source="test_engine",
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
        AuditFinding(
            severity="medium", location="Loc B", disciplines=["Arch", "KC"], description="Clash 2"
        ),
        AuditFinding(severity="low", location="Loc C", disciplines=["PCCC"], description="Clash 3"),
    ]
    report = AuditReport(
        level="L2",
        ai_model="test-vision-model",
        quad_view_path="/path/to/quad.png",
        findings=findings,
        summary="Overall consistent but has 3 clashes.",
        raw_response="RAW",
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
        summary="Test summary",
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


def test_domain_dtos_initialization_and_serialization():
    from ccba_ai import (
        PhaseUpdateResult,
        PlanCreationResult,
        PlanPhaseData,
        PlanStatusResult,
        SEOAuditResult,
        TeamTask,
    )

    # 1. SEOAuditResult
    seo_res = SEOAuditResult(
        score=95,
        checks=["H1 count: 1"],
        issues=["Missing alt tag"],
        file_name="doc.md",
    )
    assert seo_res.score == 95
    assert seo_res.checks == ["H1 count: 1"]
    assert seo_res.issues == ["Missing alt tag"]
    assert seo_res.file_name == "doc.md"
    assert seo_res.to_dict()["score"] == 95

    # 2. TeamTask
    task = TeamTask(name="Task 1", owner="Alice", status="in-progress")
    assert task.name == "Task 1"
    assert task.owner == "Alice"
    assert task.status == "in-progress"
    assert task.to_dict()["status"] == "in-progress"

    # 3. PlanCreationResult
    plan_create = PlanCreationResult(
        status="success",
        plan_title="New Feature",
        plan_folder=".md/plans/feature",
        plan_file=".md/plans/feature/plan.md",
        created_files=["phase-01.md"],
    )
    assert plan_create.status == "success"
    assert plan_create.plan_title == "New Feature"
    assert plan_create.to_dict()["created_files"] == ["phase-01.md"]

    # 4. PhaseUpdateResult
    phase_update = PhaseUpdateResult(
        phase_id="01",
        phase_name="Core Logic",
        old_status="pending",
        new_status="completed",
        plan_file="plan.md",
        phase_file="phase-01.md",
        phase_file_updated=True,
    )
    assert phase_update.phase_id == "01"
    assert phase_update.new_status == "completed"
    assert phase_update.phase_file_updated is True

    # 5. PlanStatusResult
    plan_status = PlanStatusResult(
        title="Audit Pipeline",
        metadata={"branch": "main", "status": "in-progress"},
        phases=[
            PlanPhaseData(id="01", name="Prep", status="completed", file="phase-01.md"),
            PlanPhaseData(id="02", name="Audit", status="in-progress", file="phase-02.md"),
        ],
        plan_file="plan.md",
    )
    assert plan_status.title == "Audit Pipeline"
    assert len(plan_status.phases) == 2
    assert plan_status.phases[0].status == "completed"
    assert plan_status.to_dict()["metadata"]["status"] == "in-progress"

