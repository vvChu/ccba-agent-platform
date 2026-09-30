"""catalog_snapshot_client.py - Federated Spoke Catalog Snapshot Engine (ADR-0060 Mục 6).

Implements Tier 1 Zero-Latency Local Snapshot with content-addressed storage
and atomic plain text pointer (`current`) resolution.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "CatalogSnapshotClient",
    "CatalogSnapshotMissing",
    "CorruptSnapshotError",
    "resolve_catalog_context",
]

_HASH_TOKEN_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_HUB_CATALOG_REL_PATH = Path(".agents") / "skills" / "platform-loader" / "catalog.yaml"


class CatalogSnapshotMissing(RuntimeError):
    """Raised when neither a valid Hub filesystem nor a local snapshot pointer exists."""


class CorruptSnapshotError(RuntimeError):
    """Raised when snapshot files are missing, corrupted, or have hash mismatch with provenance."""


class CatalogSnapshotClient:
    """Manages content-addressed immutable snapshots and atomic pointer resolution."""

    def __init__(self, spoke_root: Path) -> None:
        self.spoke_root = spoke_root.resolve()
        self.cache_dir = self.spoke_root / ".agents" / "cache" / "hub-catalog"
        self.snapshots_dir = self.cache_dir / "snapshots"
        self.pointer_file = self.snapshots_dir / "current"

    def is_pointer_available(self) -> bool:
        """Check if current pointer file exists and is a regular file."""
        return self.pointer_file.is_file()

    def get_current_snapshot_id(self) -> str | None:
        """Read and validate the 64-hex snapshot ID token from current pointer file.

        Closes file handle immediately to ensure compatibility with Windows file sharing.
        """
        if not self.is_pointer_available():
            return None
        try:
            # Check lstat to prevent following symlinks outside snapshots directory
            os.lstat(self.pointer_file)
            if not os.path.isfile(self.pointer_file) or os.path.islink(self.pointer_file):
                return None
            token = self.pointer_file.read_text(encoding="utf-8").strip()
            if _HASH_TOKEN_PATTERN.match(token):
                return token
        except Exception:
            return None
        return None

    def load_active_snapshot(self) -> tuple[dict[str, Any], str, dict[str, Any], dict[str, Any]]:
        """Load and verify active snapshot pointed by current pointer.

        Returns:
            (seam_contracts_dict, seam_raw_sha256, catalog_dict, provenance_dict)

        Raises:
            CatalogSnapshotMissing: If current pointer or target snapshot directory is missing.
            CorruptSnapshotError: If bytes hash mismatches provenance or parsing fails.
        """
        snapshot_id = self.get_current_snapshot_id()
        if not snapshot_id:
            raise CatalogSnapshotMissing(
                "Không tìm thấy snapshot con trỏ 'current' hợp lệ tại Spoke. "
                "Vui lòng chạy 'ccba-init-spoke' hoặc nạp snapshot catalog."
            )

        snap_dir = self.snapshots_dir / snapshot_id
        if not snap_dir.is_dir():
            raise CatalogSnapshotMissing(
                f"Thư mục snapshot '{snapshot_id}' không tồn tại trên hệ thống tệp Spoke."
            )

        seam_file = snap_dir / "seam-contracts.yaml"
        catalog_file = snap_dir / "catalog.yaml"
        prov_file = snap_dir / ".catalog_provenance.json"

        if not seam_file.is_file() or not catalog_file.is_file() or not prov_file.is_file():
            raise CorruptSnapshotError(
                f"Snapshot '{snapshot_id}' bị thiếu tệp hợp đồng, catalog, hoặc provenance."
            )

        try:
            prov_data = yaml.safe_load(prov_file.read_text(encoding="utf-8")) or {}
        except Exception as e:
            raise CorruptSnapshotError(f"Tệp provenance bị lỗi định dạng: {e}") from e

        seam_bytes = seam_file.read_bytes()
        catalog_bytes = catalog_file.read_bytes()

        actual_seam_sha = hashlib.sha256(seam_bytes).hexdigest()
        actual_catalog_sha = hashlib.sha256(catalog_bytes).hexdigest()

        expected_seam_sha = prov_data.get("seam_contracts_sha256")
        expected_catalog_sha = prov_data.get("catalog_sha256")

        if actual_seam_sha != expected_seam_sha:
            raise CorruptSnapshotError(
                f"Lệch băm seam-contracts.yaml: thực tế {actual_seam_sha} != kỳ vọng {expected_seam_sha}"
            )
        if actual_catalog_sha != expected_catalog_sha:
            raise CorruptSnapshotError(
                f"Lệch băm catalog.yaml: thực tế {actual_catalog_sha} != kỳ vọng {expected_catalog_sha}"
            )

        # Content-addressed snapshot ID verification
        computed_snap_id = hashlib.sha256(seam_bytes + b"\n" + catalog_bytes).hexdigest()
        if computed_snap_id != snapshot_id:
            raise CorruptSnapshotError(
                f"Mã băm thư mục snapshot không khớp payload: {computed_snap_id} != {snapshot_id}"
            )

        try:
            seam_dict = yaml.safe_load(seam_bytes.decode("utf-8")) or {}
            catalog_dict = yaml.safe_load(catalog_bytes.decode("utf-8")) or {}
        except Exception as e:
            raise CorruptSnapshotError(
                f"Không thể phân tích cú pháp YAML trong snapshot: {e}"
            ) from e

        return seam_dict, actual_seam_sha, catalog_dict, prov_data

    def publish_snapshot(
        self,
        seam_bytes: bytes,
        catalog_bytes: bytes,
        source_url: str = "hub-fs",
        hub_commit: str | None = None,
    ) -> str:
        """Publish a new immutable raw-byte snapshot and atomically advance current pointer.

        Returns:
            New snapshot_id (64 hex string).
        """
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        snapshot_id = hashlib.sha256(seam_bytes + b"\n" + catalog_bytes).hexdigest()
        snap_dir = self.snapshots_dir / snapshot_id
        snap_dir.mkdir(parents=True, exist_ok=True)

        seam_sha256 = hashlib.sha256(seam_bytes).hexdigest()
        catalog_sha256 = hashlib.sha256(catalog_bytes).hexdigest()

        # 1. Write immutable payload files atomically inside snap_dir
        for filename, data_bytes in [
            ("seam-contracts.yaml", seam_bytes),
            ("catalog.yaml", catalog_bytes),
        ]:
            target = snap_dir / filename
            if not target.is_file():
                temp_p = snap_dir / f".{filename}.{os.getpid()}_{time.time_ns()}.tmp"
                temp_p.write_bytes(data_bytes)
                _atomic_replace_with_retry(temp_p, target)

        # 2. Write provenance metadata
        prov_file = snap_dir / ".catalog_provenance.json"
        if not prov_file.is_file():
            prov_data = {
                "schema": 1,
                "snapshot_id": snapshot_id,
                "seam_contracts_sha256": seam_sha256,
                "catalog_sha256": catalog_sha256,
                "hub_commit": hub_commit,
                "source_url": source_url,
                "fetched_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            temp_prov = snap_dir / f".prov.{os.getpid()}_{time.time_ns()}.tmp"
            temp_prov.write_text(yaml.safe_dump(prov_data), encoding="utf-8")
            _atomic_replace_with_retry(temp_prov, prov_file)

        # 3. Read previous pointer ID before update for retention
        old_id = self.get_current_snapshot_id()

        # 4. Atomically advance pointer file `current`
        temp_ptr = self.snapshots_dir / f".current.{os.getpid()}_{time.time_ns()}.tmp"
        temp_ptr.write_text(f"{snapshot_id}\n", encoding="utf-8")
        _atomic_replace_with_retry(temp_ptr, self.pointer_file)

        # 5. Retention policy: Keep current id and previous id, cleanup older snapshots
        self._prune_old_snapshots(keep_ids={snapshot_id, old_id} if old_id else {snapshot_id})

        return snapshot_id

    def _prune_old_snapshots(self, keep_ids: set[str], min_age_seconds: float = 300.0) -> None:
        """Prune snapshot directories older than retention limit, protecting active and recently created ones."""
        try:
            active_id = self.get_current_snapshot_id()
            if active_id:
                keep_ids.add(active_id)
            now = time.time()
            for item in self.snapshots_dir.iterdir():
                if item.is_dir() and _HASH_TOKEN_PATTERN.match(item.name):
                    if item.name not in keep_ids:
                        try:
                            # Protect snapshots created recently from concurrent writer race
                            if now - item.stat().st_mtime < min_age_seconds:
                                continue
                        except Exception:
                            continue
                        for sub in item.iterdir():
                            try:
                                sub.unlink(missing_ok=True)
                            except Exception:
                                pass
                        try:
                            item.rmdir()
                        except Exception:
                            pass
        except Exception:
            pass


def _atomic_replace_with_retry(src: Path, dst: Path, max_retries: int = 10) -> None:
    """Atomic file replacement with Windows file sharing collision retry."""
    for attempt in range(max_retries):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt < max_retries - 1:
                time.sleep(0.01 * (attempt + 1))
            else:
                raise
        except Exception:
            if src.is_file():
                try:
                    src.unlink(missing_ok=True)
                except Exception:
                    pass
            raise


def _check_hub_candidate(candidate: Path) -> bool:
    """Check if candidate path is a valid Hub directory with seam contracts and catalog."""
    try:
        seam_file = candidate / "seam-contracts.yaml"
        catalog_file = candidate / _HUB_CATALOG_REL_PATH
        return seam_file.is_file() and catalog_file.is_file()
    except Exception:
        return False


def resolve_catalog_context(
    project_root: Path = Path("."),
    hub_root_override: Path | None = None,
) -> tuple[dict[str, Any], str, dict[str, Any], str]:
    """Unified resolver for Seam Contracts and Catalog across Hub and Spoke.

    Resolution Priority:
    1. `hub_root_override`: Explicit Hub path parameter.
    2. `CCBA_HUB_PATH` / `HUB_PATH`: Environment variables pointing to physical Hub.
    3. `project_root`: If project root itself contains Hub seam-contracts and catalog.
    4. Spoke Snapshot Client: `.agents/cache/hub-catalog/snapshots/current`.

    Returns:
        (seam_dict, seam_raw_sha256, catalog_dict, source_type)
        where source_type is "hub_fs" or "snapshot".

    Raises:
        CatalogSnapshotMissing: If neither Hub nor valid local snapshot is available.
        CorruptSnapshotError: If snapshot bytes hash mismatches provenance.
    """
    proj = project_root.resolve()

    # 1. hub_root_override
    if hub_root_override:
        h_cand = hub_root_override.resolve()
        if _check_hub_candidate(h_cand):
            seam_file = h_cand / "seam-contracts.yaml"
            catalog_file = h_cand / _HUB_CATALOG_REL_PATH
            seam_bytes = seam_file.read_bytes()
            seam_sha = hashlib.sha256(seam_bytes).hexdigest()
            seam_data = yaml.safe_load(seam_bytes.decode("utf-8")) or {}
            cat_data = yaml.safe_load(catalog_file.read_text(encoding="utf-8")) or {}
            return seam_data, seam_sha, cat_data, "hub_fs"

    # 2. Environment Variables: CCBA_HUB_PATH, HUB_PATH
    for env_key in ("CCBA_HUB_PATH", "HUB_PATH"):
        env_val = os.environ.get(env_key)
        if env_val and env_val.strip():
            cand = Path(env_val.strip()).resolve()
            if _check_hub_candidate(cand):
                seam_file = cand / "seam-contracts.yaml"
                catalog_file = cand / _HUB_CATALOG_REL_PATH
                seam_bytes = seam_file.read_bytes()
                seam_sha = hashlib.sha256(seam_bytes).hexdigest()
                seam_data = yaml.safe_load(seam_bytes.decode("utf-8")) or {}
                cat_data = yaml.safe_load(catalog_file.read_text(encoding="utf-8")) or {}
                return seam_data, seam_sha, cat_data, "hub_fs"

    # 3. Check if project_root itself is the Hub
    if _check_hub_candidate(proj):
        seam_file = proj / "seam-contracts.yaml"
        catalog_file = proj / _HUB_CATALOG_REL_PATH
        seam_bytes = seam_file.read_bytes()
        seam_sha = hashlib.sha256(seam_bytes).hexdigest()
        seam_data = yaml.safe_load(seam_bytes.decode("utf-8")) or {}
        cat_data = yaml.safe_load(catalog_file.read_text(encoding="utf-8")) or {}
        return seam_data, seam_sha, cat_data, "hub_fs"

    # 4. Spoke Snapshot Client
    client = CatalogSnapshotClient(proj)
    if client.is_pointer_available():
        seam_dict, seam_sha, cat_dict, _ = client.load_active_snapshot()
        return seam_dict, seam_sha, cat_dict, "snapshot"

    # 5. Fail-Closed
    raise CatalogSnapshotMissing(
        f"Không tìm thấy Hub hợp lệ tại CCBA_HUB_PATH và chưa có snapshot catalog tại '{proj}'. "
        "Vui lòng chạy 'ccba-init-spoke' hoặc nạp snapshot."
    )
