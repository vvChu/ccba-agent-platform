"""hydrator.py - Spoke Vault Hydration Engine for OKF v2.4 Legal Knowledge Bundles.

Provides multi-tier binary asset synchronization and cryptographic SHA-256 provenance
verification for cloned Spoke workspaces according to ADR 0035, ADR 0036, and ADR 0059.
"""

from __future__ import annotations

import dataclasses
import logging
import shutil
import subprocess
from enum import Enum
from pathlib import Path

import yaml

from ccba_legal.gdrive_vault import GoogleDriveVault, compute_file_sha256

logger = logging.getLogger(__name__)


class AssetStatus(str, Enum):
    """Lifecycle status of a binary asset in a bundle's sources/ directory."""

    UP_TO_DATE = "UP_TO_DATE"
    DOWNLOADED = "DOWNLOADED"
    UPLOADED = "UPLOADED"
    MISSING = "MISSING"
    HASH_MISMATCH = "HASH_MISMATCH"
    VAULT_UNAVAILABLE = "VAULT_UNAVAILABLE"
    ERROR = "ERROR"


@dataclasses.dataclass
class AssetHydrateResult:
    """Hydration result for an individual binary file."""

    asset_type: str  # 'pdf', 'docx', 'raw_scan'
    file_name: str
    expected_sha256: str
    actual_sha256: str | None = None
    status: AssetStatus = AssetStatus.MISSING
    message: str = ""
    vault_path: str = ""


@dataclasses.dataclass
class BundleHydrateResult:
    """Hydration result for a single legal document bundle."""

    doc_slug: str
    category: str
    bundle_dir: Path
    assets: list[AssetHydrateResult] = dataclasses.field(default_factory=list)
    success: bool = True

    @property
    def is_fully_hydrated(self) -> bool:
        """True if all assets are UP_TO_DATE, DOWNLOADED, or UPLOADED with verified SHA-256."""
        if not self.assets:
            return True
        return all(
            a.status in (AssetStatus.UP_TO_DATE, AssetStatus.DOWNLOADED, AssetStatus.UPLOADED)
            for a in self.assets
        )


@dataclasses.dataclass
class HydrateSummary:
    """Aggregated hydration metrics across multiple bundles."""

    total_bundles: int = 0
    fully_hydrated: int = 0
    partially_hydrated: int = 0
    unhydrated: int = 0
    total_assets: int = 0
    up_to_date_assets: int = 0
    downloaded_assets: int = 0
    uploaded_assets: int = 0
    missing_assets: int = 0
    failed_assets: int = 0
    bundle_results: list[BundleHydrateResult] = dataclasses.field(default_factory=list)


class SpokeHydrator:
    """Orchestrates binary asset hydration and cryptographic integrity verification."""

    def __init__(
        self,
        spoke_root: Path | str,
        vault_client: GoogleDriveVault | None = None,
        rclone_remote: str = "gdrive:",
    ) -> None:
        """Initialize the SpokeHydrator.

        Args:
            spoke_root: Root directory of the Spoke repository.
            vault_client: Optional GoogleDriveVault instance.
            rclone_remote: Name of the rclone remote for Cloud Vault fallback.
        """
        self.spoke_root = Path(spoke_root).resolve()
        self.legal_docs_dir = self.spoke_root / "legal_docs"
        self.vault_client = vault_client or GoogleDriveVault()
        self.rclone_remote = rclone_remote
        self._rclone_available = shutil.which("rclone") is not None

    def find_bundles(
        self,
        category: str | None = None,
        cohorts: list[str] | None = None,
    ) -> list[Path]:
        """Find bundle directories matching category or cohorts filter.

        Args:
            category: Optional category filter ('01_vbpl', '02_qcvn', '03_tcvn').
            cohorts: Optional list of doc slugs to filter.

        Returns:
            List of Path objects pointing to matching bundle directories.
        """
        cohort_set = set(cohorts) if cohorts else None
        categories = [category] if category else ["01_vbpl", "02_qcvn", "03_tcvn"]
        found: list[Path] = []

        for cat in categories:
            cat_dir = self.legal_docs_dir / cat
            if not cat_dir.is_dir():
                continue
            for doc_dir in sorted(cat_dir.iterdir()):
                if not doc_dir.is_dir():
                    continue
                meta_file = doc_dir / "metadata.yaml"
                if not meta_file.exists():
                    continue
                if cohort_set and doc_dir.name not in cohort_set:
                    continue
                found.append(doc_dir)

        return found

    def inspect_bundle_assets(self, bundle_dir: Path) -> list[AssetHydrateResult]:
        """Inspect expected assets declared in bundle's metadata.yaml.

        Args:
            bundle_dir: Path to the OKF bundle directory.

        Returns:
            List of AssetHydrateResult descriptors.
        """
        meta_file = bundle_dir / "metadata.yaml"
        if not meta_file.exists():
            return []

        try:
            meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
        except Exception as e:
            logger.error(f"Failed to read {meta_file}: {e}")
            return []

        doc_slug = bundle_dir.name
        category = bundle_dir.parent.name
        results: list[AssetHydrateResult] = []

        # 1. Inspect source_assets (OKF v2.4 standard)
        source_assets = meta.get("source_assets")
        if isinstance(source_assets, dict):
            for asset_type, info in source_assets.items():
                if not isinstance(info, dict):
                    continue
                sha = str(info.get("sha256", "")).strip().lower()
                vault_path = str(
                    info.get(
                        "vault_path",
                        f"CCBA_Legal_Vault/{category}/{doc_slug}/{doc_slug}.{asset_type}",
                    )
                )

                if asset_type == "pdf":
                    file_name = f"{doc_slug}.pdf"
                elif asset_type == "docx":
                    file_name = f"{doc_slug}.docx"
                elif asset_type == "raw_scan":
                    file_name = f"{doc_slug}_raw_scan.pdf"
                else:
                    file_name = Path(vault_path).name or f"{doc_slug}_{asset_type}"

                results.append(
                    AssetHydrateResult(
                        asset_type=asset_type,
                        file_name=file_name,
                        expected_sha256=sha,
                        vault_path=vault_path,
                    )
                )

        # 2. Fallback to legacy fields if source_assets not provided
        if not results:
            pdf_sha = str(meta.get("pdf_sha256", "")).strip().lower()
            pdf_path_str = meta.get("pdf_path")
            if pdf_sha and pdf_path_str:
                fname = Path(pdf_path_str).name
                results.append(
                    AssetHydrateResult(
                        asset_type="pdf",
                        file_name=fname,
                        expected_sha256=pdf_sha,
                        vault_path=f"CCBA_Legal_Vault/{category}/{doc_slug}/{fname}",
                    )
                )

        return results

    def verify_asset_local(self, bundle_dir: Path, asset: AssetHydrateResult) -> AssetHydrateResult:
        """Verify if an asset exists locally and validate its SHA-256 hash.

        Args:
            bundle_dir: Path to the bundle.
            asset: AssetHydrateResult to verify.

        Returns:
            Updated AssetHydrateResult.
        """
        sources_dir = bundle_dir / "sources"
        local_file = sources_dir / asset.file_name

        if not local_file.exists():
            asset.status = AssetStatus.MISSING
            asset.message = f"File missing in {sources_dir.name}/"
            return asset

        actual_sha = compute_file_sha256(local_file).lower()
        asset.actual_sha256 = actual_sha

        if not asset.expected_sha256:
            # No expected hash in metadata, accept as up to date with warning
            asset.status = AssetStatus.UP_TO_DATE
            asset.message = "File exists (no reference hash in metadata.yaml)"
            return asset

        if actual_sha == asset.expected_sha256:
            asset.status = AssetStatus.UP_TO_DATE
            asset.message = "SHA-256 match confirmed"
        else:
            asset.status = AssetStatus.HASH_MISMATCH
            asset.message = f"Hash mismatch: actual={actual_sha[:10]}... != expected={asset.expected_sha256[:10]}..."

        return asset

    def hydrate_asset(
        self,
        bundle_dir: Path,
        asset: AssetHydrateResult,
        force: bool = False,
        dry_run: bool = False,
    ) -> AssetHydrateResult:
        """Hydrate a single asset from Cloud Vault or fallback sources.

        Args:
            bundle_dir: Path to the bundle directory.
            asset: The asset descriptor.
            force: Force re-download even if file exists.
            dry_run: If True, only inspect without downloading.

        Returns:
            Updated AssetHydrateResult with final status.
        """
        sources_dir = bundle_dir / "sources"
        sources_dir.mkdir(parents=True, exist_ok=True)
        local_file = sources_dir / asset.file_name

        # First check local status
        self.verify_asset_local(bundle_dir, asset)
        if asset.status == AssetStatus.UP_TO_DATE and not force:
            return asset

        if dry_run:
            if asset.status == AssetStatus.MISSING:
                asset.message = "Missing (dry-run, download skipped)"
            elif asset.status == AssetStatus.HASH_MISMATCH:
                asset.message = "Hash mismatch (dry-run, re-download skipped)"
            return asset

        # Prepare temporary download target
        tmp_file = sources_dir / f"{asset.file_name}.tmp_download"
        download_success = False

        # --- Tier 2A: Cloud Vault Download via rclone CLI ---
        if self._rclone_available and asset.vault_path:
            rclone_src = f"{self.rclone_remote}{asset.vault_path}"
            cmd = [
                "rclone",
                "copyto",
                "--non-interactive",
                "--contimeout",
                "5s",
                "--timeout",
                "15s",
                rclone_src,
                str(tmp_file),
            ]
            logger.debug(f"Running rclone: {' '.join(cmd)}")
            try:
                res = subprocess.run(cmd, capture_output=True, timeout=20)
                if res.returncode == 0 and tmp_file.exists() and tmp_file.stat().st_size > 0:
                    download_success = True
            except (subprocess.TimeoutExpired, Exception) as e:
                logger.warning(f"rclone copyto failed or timed out for {asset.file_name}: {e}")
                if tmp_file.exists():
                    tmp_file.unlink(missing_ok=True)

        # --- Tier 2B: Cloud Vault Fallback via GoogleDriveVault API (Read-Only) ---
        if not download_success and self.vault_client.is_available():
            try:
                category = bundle_dir.parent.name
                doc_slug = bundle_dir.name
                target_folder_id = self.vault_client.find_vault_folder(category, doc_slug)
                if target_folder_id and self.vault_client.service:
                    q = f"name = '{asset.file_name}' and '{target_folder_id}' in parents and trashed = false"
                    res = (
                        self.vault_client.service.files()
                        .list(q=q, fields="files(id)", spaces="drive")
                        .execute()
                    )
                    files = res.get("files", [])
                    if files:
                        file_id = files[0]["id"]
                        if self.vault_client.download_asset(file_id, tmp_file):
                            download_success = True
            except Exception as e:
                logger.warning(f"GoogleDriveVault API download failed for {asset.file_name}: {e}")
                if tmp_file.exists():
                    tmp_file.unlink(missing_ok=True)

        if not download_success:
            asset.status = AssetStatus.VAULT_UNAVAILABLE
            asset.message = f"Asset not found in Cloud Vault ({asset.vault_path})"
            if tmp_file.exists():
                tmp_file.unlink(missing_ok=True)
            return asset

        # --- Cryptographic SHA-256 Verification Gate ---
        try:
            downloaded_sha = compute_file_sha256(tmp_file).lower()
            asset.actual_sha256 = downloaded_sha

            if asset.expected_sha256 and downloaded_sha != asset.expected_sha256:
                tmp_file.unlink(missing_ok=True)
                asset.status = AssetStatus.HASH_MISMATCH
                asset.message = (
                    f"Integrity Failed: downloaded={downloaded_sha[:10]}... "
                    f"!= expected={asset.expected_sha256[:10]}..."
                )
                logger.error(f"Cryptographic check failed for {asset.file_name}!")
                return asset

            # Atomic promotion
            shutil.move(str(tmp_file), str(local_file))
            asset.status = AssetStatus.DOWNLOADED
            if not asset.expected_sha256:
                asset.message = (
                    "Successfully hydrated (warning: no expected SHA-256 in metadata.yaml)"
                )
            else:
                asset.message = "Successfully hydrated and SHA-256 verified"
            return asset

        except Exception as e:
            if tmp_file.exists():
                tmp_file.unlink(missing_ok=True)
            asset.status = AssetStatus.ERROR
            asset.message = f"Hydration verification exception: {e}"
            logger.exception(f"Error verifying {asset.file_name}")
            return asset

    def push_asset(
        self,
        bundle_dir: Path,
        asset: AssetHydrateResult,
        dry_run: bool = False,
    ) -> AssetHydrateResult:
        """Push a local asset to Cloud Vault (rclone with GoogleDriveVault API fallback).

        Args:
            bundle_dir: Path to the OKF bundle directory.
            asset: AssetHydrateResult representing the asset to push.
            dry_run: If True, simulate upload without modifying remote.

        Returns:
            Updated AssetHydrateResult with upload status.
        """
        local_file = bundle_dir / "sources" / asset.file_name
        if not local_file.exists():
            asset.status = AssetStatus.MISSING
            asset.message = f"Local source file not found: {local_file}"
            return asset

        actual_sha = compute_file_sha256(local_file).lower()
        asset.actual_sha256 = actual_sha

        if asset.expected_sha256 and actual_sha != asset.expected_sha256:
            asset.status = AssetStatus.HASH_MISMATCH
            asset.message = (
                f"Integrity check failed before push: local={actual_sha[:10]}... "
                f"!= expected={asset.expected_sha256[:10]}..."
            )
            logger.error(f"Cannot push corrupted file {asset.file_name}!")
            return asset

        if dry_run:
            asset.status = AssetStatus.UPLOADED
            asset.message = f"Dry-run: would upload to {asset.vault_path}"
            return asset

        remote_target = f"{self.rclone_remote}{asset.vault_path}"
        upload_success = False

        # --- Tier 1: Rclone Fast Copyto ---
        cmd = [
            "rclone",
            "copyto",
            str(local_file),
            remote_target,
            "--non-interactive",
            "--contimeout",
            "5s",
            "--timeout",
            "30s",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                upload_success = True
        except (subprocess.TimeoutExpired, Exception) as e:
            logger.warning(f"rclone copyto failed for {asset.file_name}: {e}")

        # --- Tier 2: GoogleDriveVault API Fallback ---
        if not upload_success and self.vault_client.is_available():
            try:
                category = bundle_dir.parent.name
                doc_slug = bundle_dir.name
                up_res = self.vault_client.upload_asset(local_file, category, doc_slug)
                if up_res.get("status") == "synced":
                    upload_success = True
            except Exception as e:
                logger.warning(f"GoogleDriveVault API upload failed for {asset.file_name}: {e}")

        if upload_success:
            asset.status = AssetStatus.UPLOADED
            asset.message = f"Successfully uploaded to Cloud Vault ({asset.vault_path})"
        else:
            asset.status = AssetStatus.ERROR
            asset.message = f"Failed to upload to Cloud Vault ({asset.vault_path})"

        return asset

    def hydrate_bundle(
        self,
        bundle_dir: Path,
        force: bool = False,
        verify_only: bool = False,
        dry_run: bool = False,
        push: bool = False,
    ) -> BundleHydrateResult:
        """Hydrate or push all declared assets for a single bundle.

        Args:
            bundle_dir: Path to the OKF bundle directory.
            force: Force re-download even if file exists.
            verify_only: Only verify local files without downloading.
            dry_run: Inspect without downloading/uploading.
            push: If True, push local files to Cloud Vault.

        Returns:
            BundleHydrateResult with asset breakdown.
        """
        category = bundle_dir.parent.name
        doc_slug = bundle_dir.name
        assets = self.inspect_bundle_assets(bundle_dir)

        result = BundleHydrateResult(
            doc_slug=doc_slug,
            category=category,
            bundle_dir=bundle_dir,
            assets=[],
        )

        for asset in assets:
            if push:
                processed_asset = self.push_asset(bundle_dir, asset, dry_run=dry_run)
            elif verify_only:
                processed_asset = self.verify_asset_local(bundle_dir, asset)
            else:
                processed_asset = self.hydrate_asset(
                    bundle_dir, asset, force=force, dry_run=dry_run
                )
            result.assets.append(processed_asset)

        result.success = result.is_fully_hydrated
        return result

    def hydrate_all(
        self,
        category: str | None = None,
        cohorts: list[str] | None = None,
        force: bool = False,
        verify_only: bool = False,
        dry_run: bool = False,
        push: bool = False,
    ) -> HydrateSummary:
        """Hydrate, verify, or push multiple bundles across the repository.

        Args:
            category: Optional category filter.
            cohorts: Optional list of doc slugs.
            force: Force re-download.
            verify_only: Only verify local status.
            dry_run: Dry-run without network writes.
            push: Push local assets to Cloud Vault.

        Returns:
            HydrateSummary with aggregated statistics.
        """
        bundle_dirs = self.find_bundles(category=category, cohorts=cohorts)
        summary = HydrateSummary(total_bundles=len(bundle_dirs))

        for b_dir in bundle_dirs:
            b_res = self.hydrate_bundle(
                b_dir, force=force, verify_only=verify_only, dry_run=dry_run, push=push
            )
            summary.bundle_results.append(b_res)

            if b_res.is_fully_hydrated:
                summary.fully_hydrated += 1
            elif any(
                a.status in (AssetStatus.UP_TO_DATE, AssetStatus.DOWNLOADED, AssetStatus.UPLOADED)
                for a in b_res.assets
            ):
                summary.partially_hydrated += 1
            else:
                summary.unhydrated += 1

            for a in b_res.assets:
                summary.total_assets += 1
                if a.status == AssetStatus.UP_TO_DATE:
                    summary.up_to_date_assets += 1
                elif a.status == AssetStatus.DOWNLOADED:
                    summary.downloaded_assets += 1
                elif a.status == AssetStatus.UPLOADED:
                    summary.uploaded_assets += 1
                elif a.status == AssetStatus.MISSING:
                    summary.missing_assets += 1
                else:
                    summary.failed_assets += 1

        return summary
