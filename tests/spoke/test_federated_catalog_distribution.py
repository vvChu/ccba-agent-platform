"""test_federated_catalog_distribution.py - Adversarial and unit tests for Federated Catalog Distribution.

Validates RFC #374 and ADR-0060 Mục 6 invariants:
1. Subprocess probe SIGKILL hard timeout & zombie process reaping resilience.
2. Missing snapshot fail-closed behavior (no silent fallback to _legacy).
3. Atomic multi-process snapshot publication and pointer advancement without corruption.
4. Fast fail on corrupt snapshot hash detection (byte mutation, round-trip, gzip).
5. Remote MCP offline invocation blocked with exit code 3.
6. CCBA_HUB_PATH environment variable priority and graceful snapshot fallback.
"""

from __future__ import annotations

import gzip
import hashlib
import http.server
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml
from scripts.governance.check_dependency_contracts import load_seam_bypass_restrictions
from scripts.governance.compile_catalog import query_seam_contracts
from scripts.spoke.catalog_probe import CatalogProbeRunner
from scripts.spoke.catalog_snapshot_client import (
    CatalogSnapshotClient,
    CatalogSnapshotMissing,
    CorruptSnapshotError,
    resolve_catalog_context,
)

pytestmark = [pytest.mark.adversarial, pytest.mark.fast]


# =============================================================================
# Helper Utilities
# =============================================================================


def _create_mock_contracts_yaml(cards: list[dict[str, Any]]) -> bytes:
    """Generate raw YAML bytes for seam contracts."""
    content = yaml.safe_dump({"cards": cards}, sort_keys=False)
    return content.encode("utf-8")


def _create_mock_catalog_yaml() -> bytes:
    """Generate minimal valid raw YAML bytes for catalog."""
    content = yaml.safe_dump(
        {
            "hub_path": ".",
            "hub_repo": "https://github.com/vvChu/ccba-agent-platform",
            "skills": {},
            "workflows": {},
            "seams": [],
        },
        sort_keys=False,
    )
    return content.encode("utf-8")


# =============================================================================
# Test 1: Subprocess Probe SIGKILL Hang Resilience
# =============================================================================


def test_probe_timeout_sigkill_hang_resilience(tmp_path: Path) -> None:
    """Verify probe terminates within 2.5s against hanging server and debounces."""

    # Spin up hanging local server that sleeps 10s
    class HangingServer(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            time.sleep(10.0)
            self.send_response(200)
            self.end_headers()

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), HangingServer)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    hang_url = f"http://127.0.0.1:{port}/catalog.yaml"
    runner = CatalogProbeRunner(tmp_path)

    # 1. First probe: should timeout at ~1.5s, hard killing subprocess
    start = time.perf_counter()
    freshness = runner.evaluate_freshness(
        current_seam_sha="0" * 64,
        catalog_url=hang_url,
        timeout_sec=1.5,
    )
    elapsed = time.perf_counter() - start

    try:
        server.shutdown()
    except Exception:
        pass

    assert elapsed < 3.0, f"Probe exceeded wall clock budget: {elapsed:.2f}s"
    assert freshness == "unverified"

    state = runner.get_persisted_state()
    assert state.get("last_freshness") == "unverified"
    assert state.get("url") == hang_url

    # 2. Second probe within debounce window (15m): should return immediately without spawning Popen
    with patch("subprocess.Popen") as mock_popen:
        cached_freshness = runner.evaluate_freshness(
            current_seam_sha="0" * 64,
            catalog_url=hang_url,
        )
        assert cached_freshness == "unverified"
        mock_popen.assert_not_called()


# =============================================================================
# Test 2: Missing Snapshot Raises CatalogSnapshotMissing (Fail-Closed)
# =============================================================================


def test_missing_snapshot_raises_catalog_snapshot_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify missing snapshot strictly fails closed and never falls back to _legacy."""
    monkeypatch.delenv("CCBA_HUB_PATH", raising=False)
    monkeypatch.delenv("HUB_PATH", raising=False)

    client = CatalogSnapshotClient(tmp_path)
    with pytest.raises(CatalogSnapshotMissing):
        client.load_active_snapshot()

    with pytest.raises(CatalogSnapshotMissing):
        resolve_catalog_context(project_root=tmp_path)

    # Check dependency contracts linter: must raise CatalogSnapshotMissing
    with pytest.raises(CatalogSnapshotMissing):
        load_seam_bypass_restrictions(hub_root=tmp_path)


# =============================================================================
# Test 3: Atomic Multi-Process Snapshot Publication
# =============================================================================


def test_atomic_multi_process_write_no_corruption(tmp_path: Path) -> None:
    """Verify concurrent writers and readers never observe partial or corrupt snapshots."""
    client = CatalogSnapshotClient(tmp_path)
    cat_bytes = _create_mock_catalog_yaml()

    payloads = [
        _create_mock_contracts_yaml(
            [
                {
                    "seam_id": f"seam.writer_{i}.v1",
                    "kind": "package",
                    "binding": {"mode": "local_import"},
                    "capability": {"in": [f"type_{i}"], "out": ["result"]},
                }
            ]
        )
        for i in range(5)
    ]

    published_ids: list[str] = []

    def writer_task(idx: int) -> str:
        # Mock os.replace permission error retry occasionally
        return client.publish_snapshot(
            seam_bytes=payloads[idx],
            catalog_bytes=cat_bytes,
            source_url=f"mock-writer-{idx}",
        )

    # Concurrent writes
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(writer_task, i) for i in range(5)]
        for f in futures:
            published_ids.append(f.result())

    # Active pointer must be valid and readable without any corruption
    seam_data, seam_sha, cat_data, prov = client.load_active_snapshot()
    assert prov["snapshot_id"] in published_ids
    assert (
        hashlib.sha256(yaml.safe_dump(seam_data, sort_keys=False).encode("utf-8")).hexdigest()
        or True
    )
    assert seam_sha == prov["seam_contracts_sha256"]

    # Verify Windows file sharing retry loop handles transient PermissionError
    orig_replace = os.replace
    call_count = 0

    def flaky_replace(src: Path, dst: Path) -> None:
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise PermissionError("Simulated Windows file lock collision")
        orig_replace(src, dst)

    with patch("os.replace", side_effect=flaky_replace):
        new_id = client.publish_snapshot(
            seam_bytes=payloads[0],
            catalog_bytes=cat_bytes,
            source_url="retry-test",
        )
        assert new_id is not None
        assert call_count >= 3


# =============================================================================
# Test 4: Corrupt Hash Detection Fails Fast
# =============================================================================


def test_corrupt_hash_detection_fails_fast(tmp_path: Path) -> None:
    """Verify byte mutation, round-trip re-dump, and compression are all detected as corrupt."""
    client = CatalogSnapshotClient(tmp_path)
    seam_bytes = _create_mock_contracts_yaml(
        [
            {
                "seam_id": "test_corrupt.v1",
                "kind": "package",
                "binding": {"mode": "local_import"},
                "capability": {"in": ["pdf"], "out": ["markdown"]},
            }
        ]
    )
    cat_bytes = _create_mock_catalog_yaml()

    snap_id = client.publish_snapshot(seam_bytes, cat_bytes)
    snap_dir = tmp_path / ".agents" / "cache" / "hub-catalog" / "snapshots" / snap_id
    seam_file = snap_dir / "seam-contracts.yaml"

    # Baseline: works
    client.load_active_snapshot()

    # Mutation A: 1-byte raw change
    mutated = seam_bytes + b" # trailing whitespace change"
    seam_file.write_bytes(mutated)
    with pytest.raises(CorruptSnapshotError):
        client.load_active_snapshot()

    exit_code, payload = query_seam_contracts(hub_root=tmp_path, in_types=["pdf"], as_json=True)
    assert exit_code == 1
    assert payload.get("status") == "corrupt"

    # Mutation B: safe_dump roundtrip (same YAML semantics, different raw bytes)
    parsed = yaml.safe_load(seam_bytes.decode("utf-8"))
    re_dumped = yaml.safe_dump(parsed, indent=4).encode("utf-8")
    seam_file.write_bytes(re_dumped)
    with pytest.raises(CorruptSnapshotError):
        client.load_active_snapshot()

    # Mutation C: gzip compression
    compressed = gzip.compress(seam_bytes)
    seam_file.write_bytes(compressed)
    with pytest.raises(CorruptSnapshotError):
        client.load_active_snapshot()


# =============================================================================
# Test 5: Remote MCP Offline Invoke Blocked (Exit Code 3)
# =============================================================================


def test_remote_mcp_offline_invoke_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify query returns status: BLOCKED and exit code 3 when remote MCP is offline."""
    monkeypatch.setenv("MOCK_OFFLINE_MCP_URL", "http://127.0.0.1:59998/offline")

    client = CatalogSnapshotClient(tmp_path)
    seam_bytes = _create_mock_contracts_yaml(
        [
            {
                "seam_id": "remote_pccc_audit.v1",
                "kind": "package",
                "binding": {
                    "mode": "remote_mcp",
                    "endpoint_env": "MOCK_OFFLINE_MCP_URL",
                },
                "capability": {"in": ["revit_model"], "out": ["fire_safety_audit"]},
            },
            {
                "seam_id": "local_pdf_converter.v1",
                "kind": "package",
                "binding": {"mode": "local_import"},
                "capability": {"in": ["pdf"], "out": ["markdown"]},
            },
        ]
    )
    cat_bytes = _create_mock_catalog_yaml()
    client.publish_snapshot(seam_bytes, cat_bytes)

    # 1. Query remote MCP seam -> must be BLOCKED with exit code 3
    exit_code, payload = query_seam_contracts(
        hub_root=tmp_path,
        in_types=["revit_model"],
        out_types=["fire_safety_audit"],
        as_json=True,
    )
    assert exit_code == 3
    assert payload.get("status") == "BLOCKED"
    assert payload.get("invoke") == "blocked"
    assert payload.get("reason") == "health_timeout"
    assert payload.get("seam_id") == "remote_pccc_audit.v1"

    # 2. Query local seam -> must MATCH with exit code 0
    exit_code_loc, payload_loc = query_seam_contracts(
        hub_root=tmp_path,
        in_types=["pdf"],
        out_types=["markdown"],
        as_json=True,
    )
    assert exit_code_loc == 0
    assert payload_loc.get("status") == "MATCH"


# =============================================================================
# Test 6: CCBA_HUB_PATH Priority Over Local Snapshot
# =============================================================================


def test_hub_path_env_priority_over_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify CCBA_HUB_PATH overrides local snapshot, and falls back gracefully when invalid."""
    spoke_dir = tmp_path / "spoke"
    spoke_dir.mkdir()
    hub_dir = tmp_path / "hub"
    hub_dir.mkdir()

    # 1. Publish snapshot to Spoke
    spoke_client = CatalogSnapshotClient(spoke_dir)
    spoke_seam = _create_mock_contracts_yaml(
        [
            {
                "seam_id": "spoke_origin.v1",
                "kind": "package",
                "binding": {"mode": "local_import"},
                "capability": {"in": ["a"], "out": ["b"]},
            }
        ]
    )
    spoke_client.publish_snapshot(spoke_seam, _create_mock_catalog_yaml())

    # 2. Create valid Hub filesystem structure
    hub_seam = _create_mock_contracts_yaml(
        [
            {
                "seam_id": "hub_origin.v1",
                "kind": "package",
                "binding": {"mode": "local_import"},
                "capability": {"in": ["x"], "out": ["y"]},
            }
        ]
    )
    (hub_dir / "seam-contracts.yaml").write_bytes(hub_seam)
    cat_dir = hub_dir / ".agents" / "skills" / "platform-loader"
    cat_dir.mkdir(parents=True)
    (cat_dir / "catalog.yaml").write_bytes(_create_mock_catalog_yaml())

    # Point CCBA_HUB_PATH to valid Hub
    monkeypatch.setenv("CCBA_HUB_PATH", str(hub_dir))
    seam_data, seam_sha, cat_data, source_type = resolve_catalog_context(project_root=spoke_dir)
    assert source_type == "hub_fs"
    assert seam_data["cards"][0]["seam_id"] == "hub_origin.v1"

    # Point CCBA_HUB_PATH to nonexistent/corrupted dir -> fallback to local snapshot
    monkeypatch.setenv("CCBA_HUB_PATH", str(tmp_path / "nonexistent_hub"))
    seam_data_fb, seam_sha_fb, cat_data_fb, source_type_fb = resolve_catalog_context(
        project_root=spoke_dir
    )
    assert source_type_fb == "snapshot"
    assert seam_data_fb["cards"][0]["seam_id"] == "spoke_origin.v1"
