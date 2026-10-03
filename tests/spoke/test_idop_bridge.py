"""test_idop_bridge.py - Comprehensive Unit Tests for IDOPBridge & Spoke CLI IDOP Integration.

Architecture & Governance:
- ADR 0042 (Headless Python IDOPBridge SDK)
- ADR 0043 (Decoupled Resilience & Idempotent Replay)
- ADR 0060 (M365 Outbound Bridge & Rate Limiter)
- INV-SYNC-13 (IDOP Idempotent Replay & Composite Key)
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.spoke.ccba_m365_bridge import BridgeConfig, DeadLetterQueueManager, TokenBucketLimiter
from scripts.spoke.idop_bridge import IDOPBridge, compute_composite_key
from scripts.spoke.spoke_cli import SpokeCLI

# ==============================================================================
# 1. Composite Key Determinism & Invariance
# ==============================================================================


def test_composite_key_determinism():
    """Validates that composite key is strictly deterministic across whitespace and case variations."""
    key1 = compute_composite_key(
        project_code="DA-2026-DHVN",
        contract_id="HD-01/2026",
        stage_id="PGV-001",
        submittal_name="Bản vẽ mặt bằng tầng 1",
    )
    key2 = compute_composite_key(
        project_code=" da-2026-dhvn ",
        contract_id=" hd-01/2026 ",
        stage_id=" pgv-001 ",
        submittal_name=" bản vẽ mặt bằng tầng 1 ",
    )
    assert len(key1) == 64
    assert key1 == key2, "Composite key must be case-insensitive and whitespace-invariant"


def test_composite_key_distinguishes_submittals():
    """Validates that different tasks or submittals produce unique composite keys."""
    key1 = compute_composite_key("DA-2026", "HD-01", "TASK-A", "Bản vẽ 1")
    key2 = compute_composite_key("DA-2026", "HD-01", "TASK-B", "Bản vẽ 1")
    key3 = compute_composite_key("DA-2026", "HD-01", "TASK-A", "Bản vẽ 2")
    assert key1 != key2
    assert key1 != key3


# ==============================================================================
# 2. IDOPBridge Staging & Persistence
# ==============================================================================


def test_idop_bridge_stage_submittal(tmp_path: Path):
    """Validates staging of a submittal into .md/idop_staged/ as STAGED_LOCAL."""
    spoke_root = tmp_path / "spoke_project"
    spoke_root.mkdir()
    sample_file = spoke_root / "report.docx"
    sample_file.write_bytes(b"Mock report content 2026")

    bridge = IDOPBridge(spoke_root=spoke_root)
    submittal = bridge.stage(
        file_path=sample_file,
        task_id="PGV-2026-001",
        title="Báo cáo kiểm định",
        project_code="DA-2026-DHVN",
        contract_id="HD-10",
        author_name="Kỹ Sư Alpha",
    )

    assert submittal.status == "STAGED_LOCAL"
    assert submittal.file_name == "report.docx"
    assert len(submittal.composite_key) == 64
    assert submittal.file_size_bytes == len(b"Mock report content 2026")

    # Verify JSON persisted on disk
    staged_json = spoke_root / ".md" / "idop_staged" / f"{submittal.receipt_id}.json"
    assert staged_json.exists()

    with open(staged_json, encoding="utf-8") as f:
        data = json.load(f)
    assert data["composite_key"] == submittal.composite_key
    assert data["status"] == "STAGED_LOCAL"


def test_idop_bridge_list_staged(tmp_path: Path):
    """Validates listing staged submittals with filtering."""
    spoke_root = tmp_path / "spoke_project"
    spoke_root.mkdir()
    f1 = spoke_root / "doc1.pdf"
    f2 = spoke_root / "doc2.pdf"
    f1.write_bytes(b"content 1")
    f2.write_bytes(b"content 2")

    bridge = IDOPBridge(spoke_root=spoke_root)
    bridge.stage(f1, task_id="T1", title="Doc 1")
    bridge.stage(f2, task_id="T2", title="Doc 2")

    all_staged = bridge.list_staged()
    assert len(all_staged) == 2

    local_only = bridge.list_staged(status="STAGED_LOCAL")
    assert len(local_only) == 2

    synced_only = bridge.list_staged(status="SYNCED_SHAREPOINT")
    assert len(synced_only) == 0


# ==============================================================================
# 3. IDOPBridge Flush & Idempotent Replay
# ==============================================================================


def test_idop_bridge_flush_dry_run(tmp_path: Path):
    """Validates flush in dry-run mode (DEV sandbox) marks records as SYNCED_MOCK_SANDBOX."""
    spoke_root = tmp_path / "spoke_project"
    spoke_root.mkdir()
    f1 = spoke_root / "doc.pdf"
    f1.write_bytes(b"pdf data")

    config = BridgeConfig(dry_run=True, target_env="DEV")
    bridge = IDOPBridge(spoke_root=spoke_root, config=config)
    bridge.stage(f1, task_id="T1", title="Doc 1")

    res = bridge.flush(dry_run=True)
    assert res["total_pending"] == 1
    assert res["synced"] == 1
    assert res["failed"] == 0

    # Verify updated record on disk
    staged_records = bridge.list_staged()
    assert staged_records[0].status == "SYNCED_MOCK_SANDBOX"
    assert staged_records[0].sharepoint_item_id is not None
    assert staged_records[0].synced_at is not None

    # Idempotent replay: flushing again should find 0 pending records
    res2 = bridge.flush(dry_run=True)
    assert res2["total_pending"] == 0
    assert res2["synced"] == 0


def test_idop_bridge_intra_batch_deduplication(tmp_path: Path):
    """Validates that items with identical composite keys are deduplicated and persisted."""
    spoke_root = tmp_path / "spoke_project"
    spoke_root.mkdir()
    f1 = spoke_root / "file1.pdf"
    f2 = spoke_root / "file2.pdf"
    f1.write_bytes(b"data 1")
    f2.write_bytes(b"data 2")

    bridge = IDOPBridge(spoke_root=spoke_root)
    # Stage two submittals with same project_code, contract_id, task_id, and title
    s1 = bridge.stage(f1, task_id="SAME_TASK", title="Same Title", project_code="DA-1")
    s2 = bridge.stage(f2, task_id="SAME_TASK", title="Same Title", project_code="DA-1")

    assert s1.composite_key == s2.composite_key

    res = bridge.flush(dry_run=True)
    assert res["total_pending"] == 2
    assert res["synced"] == 1
    assert res["skipped"] == 1
    assert res["processed"] == 2

    # Verify on disk that s2 is now SKIPPED_DUPLICATE and NOT STAGED_LOCAL
    staged = {r.receipt_id: r for r in bridge.list_staged()}
    assert staged[s1.receipt_id].status == "SYNCED_MOCK_SANDBOX"
    assert staged[s2.receipt_id].status == "SKIPPED_DUPLICATE"

    # Subsequent flush must find 0 pending records (no duplicate re-sync)
    res2 = bridge.flush(dry_run=True)
    assert res2["total_pending"] == 0

    # Cross-batch deduplication: staging another submittal with identical key
    f3 = spoke_root / "file3.pdf"
    f3.write_bytes(b"data 3")
    s3 = bridge.stage(f3, task_id="SAME_TASK", title="Same Title", project_code="DA-1")
    assert s3.composite_key == s1.composite_key

    res3 = bridge.flush(dry_run=True)
    assert res3["total_pending"] == 1
    assert res3["synced"] == 0
    assert res3["skipped"] == 1
    assert bridge.list_staged(status="STAGED_LOCAL") == []


def test_idop_bridge_iso_doc_and_approval_status(tmp_path: Path):
    """Validates that custom iso_doc_name and approval_status are preserved in DTO and flush payload."""
    spoke_root = tmp_path / "spoke_project"
    spoke_root.mkdir()
    f1 = spoke_root / "report.pdf"
    f1.write_bytes(b"pdf data")

    bridge = IDOPBridge(spoke_root=spoke_root)
    s = bridge.stage(
        f1,
        task_id="TK-01",
        title="Báo cáo thẩm tra",
        iso_doc_name="CCBA-BC-01.pdf",
        approval_status="S3",
    )

    assert s.iso_doc_name == "CCBA-BC-01.pdf"
    assert s.approval_status == "S3"

    res = bridge.flush(dry_run=True)
    assert res["synced"] == 1


# ==============================================================================
# 4. SpokeCLI End-to-End Integration
# ==============================================================================


def test_spoke_cli_stage_and_flush(tmp_path: Path):
    """Validates full roundtrip of ccba-spoke stage and flush commands."""
    spoke_root = tmp_path / "spoke_project"
    spoke_root.mkdir()

    # Create workspace context
    md_dir = spoke_root / ".md"
    md_dir.mkdir()
    ctx_file = md_dir / "workspace_context.yaml"
    ctx_file.write_text(
        "project:\n"
        "  name: Test Project\n"
        "  project_code: DA-TEST\n"
        "  contract_id: HD-TEST-01\n"
        "  archetype: project_delivery\n"
        "  type: Phần mềm\n"
        "organizational_identity:\n"
        "  owner_name: Test Engineer\n"
        "  owner_email: test@ccba.vn\n",
        encoding="utf-8",
    )

    doc_file = spoke_root / "drawing.dwg"
    doc_file.write_bytes(b"AutoCAD binary data mock")

    cli = SpokeCLI(spoke_root=spoke_root)

    # 1. Run stage
    stage_exit = cli.stage(
        file_path=str(doc_file),
        task_id="DRAWING-01",
        title="Bản vẽ mặt bằng kết cấu",
    )
    assert stage_exit == 0

    staged_items = cli.bridge.list_staged(status="STAGED_LOCAL")
    assert len(staged_items) == 1
    assert staged_items[0].project_code == "DA-TEST"
    assert staged_items[0].contract_id == "HD-TEST-01"

    # 2. Run flush
    flush_exit = cli.flush(dry_run=True)
    assert flush_exit == 0

    remaining_pending = cli.bridge.list_staged(status="STAGED_LOCAL")
    assert len(remaining_pending) == 0


# ==============================================================================
# 5. Token Bucket Limiter & Dead Letter Queue (DLQ)
# ==============================================================================


def test_token_bucket_limiter():
    """Validates that TokenBucketLimiter operates accurately."""
    limiter = TokenBucketLimiter(rate=10.0, capacity=2.0)
    # First token should be acquired immediately
    wait1 = limiter.acquire()
    assert wait1 == 0.0

    # Second token should also be immediate within capacity
    wait2 = limiter.acquire()
    assert wait2 == 0.0


def test_dead_letter_queue_manager(tmp_path: Path):
    """Validates enqueueing and listing items in DLQ."""
    dlq_dir = tmp_path / "dlq"
    dlq = DeadLetterQueueManager(dlq_dir=dlq_dir)

    filepath = dlq.enqueue(
        entity_type="cde_document",
        operation="CREATE",
        target_list="CDEDocuments",
        payload={"Title": "Failed Doc"},
        error_message="HTTP 503 Service Unavailable",
        attempts=3,
    )

    assert filepath.exists()
    pending = dlq.list_pending()
    assert len(pending) == 1

    # Archive DLQ item
    dlq.archive(filepath)
    assert len(dlq.list_pending()) == 0
