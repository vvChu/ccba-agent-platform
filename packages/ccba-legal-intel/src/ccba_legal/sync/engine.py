"""LegalSyncEngine Facade Class (ADR 0050)."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.registry import LegalRegistryManager, load_legal_registry
from ccba_legal.sync.cdp_discovery import (
    download_via_cdp_or_client,
    search_thuvienphapluat_via_cdp,
)
from ccba_legal.sync.drive_uploader import (
    _import_google_api,
    clean_google_drive_folder,
    get_drive_service,
    upload_to_google_drive,
)
from ccba_legal.sync.notebooklm_sync import (
    _import_notebooklm_client,
    sync_registry_to_notebooklm,
)
from ccba_legal.sync.utils import (
    calculate_md5,
    calculate_sha256,
    is_port_open,
)

DEFAULT_DRIVE_FOLDER = "1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2"


class LegalSyncEngine:
    """Deep module coordinating local legal registry sync, Chrome CDP discovery, cloud drives and Spoke distribution (ADR 0050)."""

    def __init__(self, project_root: Path | None = None) -> None:
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root

    def calculate_file_hashes(self, file_path: Path) -> dict[str, str]:
        """Compute both MD5 and SHA256 for a target file."""
        return {
            "md5": calculate_md5(file_path),
            "sha256": calculate_sha256(file_path),
        }

    def verify_environment(self) -> dict[str, bool]:
        """Verify environment dependencies."""
        google_available, *_ = _import_google_api()
        try:
            from ccba_legal.crawler import ChromeCDP

            has_cdp = ChromeCDP is not None
        except ImportError:
            has_cdp = False

        return {
            "google_api": google_available,
            "chrome_cdp": has_cdp,
            "chrome_port_open": is_port_open(9222),
            "notebooklm": _import_notebooklm_client() is not None,
        }

    def search_thuvienphapluat_via_cdp(self, query: str) -> str | None:
        """Search for a legal document URL on thuvienphapluat.vn via Google Search using Chrome CDP."""
        return search_thuvienphapluat_via_cdp(query)

    def download_via_cdp_or_client(self, url: str, dest_path: Path) -> bool:
        """Download a file using Chrome CDP (preferred) or urllib fallback."""
        return download_via_cdp_or_client(url, dest_path)

    def get_drive_service(self) -> Any:
        """Initialize Drive API service using personal token or ADC fallback."""
        return get_drive_service()

    def clean_google_drive_folder(self, folder_id: str) -> None:
        """Delete all files in a Google Drive folder for a clean slate."""
        clean_google_drive_folder(folder_id)

    def upload_to_google_drive(
        self, file_path: Path, folder_id: str, target_name: str
    ) -> str | None:
        """Upload a file to Google Drive with deduplication support."""
        return upload_to_google_drive(file_path, folder_id, target_name)

    async def sync_registry_to_notebooklm(
        self,
        registry_path: Path,
        sources_reg_path: Path,
        notebook_id: str,
        use_drive: bool,
        drive_folder_id: str,
        download_pdf: bool = False,
        clean_drive: bool = False,
    ) -> None:
        """Execute the full sync pipeline from local registry to NotebookLM Cloud."""
        await sync_registry_to_notebooklm(
            registry_path=registry_path,
            sources_reg_path=sources_reg_path,
            notebook_id=notebook_id,
            use_drive=use_drive,
            drive_folder_id=drive_folder_id,
            download_pdf=download_pdf,
            clean_drive=clean_drive,
        )

    def find_local_knowledge_corpus(self, explicit_path: Path | None = None) -> Path | None:
        """Discover the canonical Knowledge Corpus Spoke (ccba-legal-knowledge) on local machine (ADR 0050)."""
        if explicit_path and explicit_path.exists():
            return explicit_path.resolve()

        env_path = os.environ.get("CCBA_LEGAL_KNOWLEDGE_PATH")
        if env_path:
            p = Path(env_path)
            if p.exists():
                return p.resolve()

        candidates = [
            self.project_root.parent / "ccba-legal-knowledge",
            self.project_root / ".." / "ccba-legal-knowledge",
            Path("D:/GitHubProjects/ccba-legal-knowledge"),
            Path("C:/GitHubProjects/ccba-legal-knowledge"),
            Path.home() / "GitHubProjects" / "ccba-legal-knowledge",
            Path.home() / "ccba-legal-knowledge",
        ]

        for cand in candidates:
            try:
                resolved = cand.resolve()
                if resolved.exists() and (
                    (resolved / "legal_docs").exists()
                    or (resolved / ".md" / "data" / "legal_registry.yaml").exists()
                ):
                    return resolved
            except Exception:
                continue

        # Check if project_root itself contains legal_docs
        if (self.project_root / "legal_docs").exists():
            return self.project_root.resolve()

        return None

    def pull_latest_okf_bundles(
        self,
        target_dir: Path | str | None = None,
        doc_ids: list[str] | None = None,
        source_corpus_dir: Path | str | None = None,
        update_registry: bool = True,
    ) -> dict[str, Any]:
        """Pull and synchronize OKF v2.4 legal bundles into Spoke with Non-Destructive Registry Merge (ADR 0050).

        Args:
            target_dir: Destination directory for OKF bundles (default: '.md/legal_docs' for consuming spokes, 'legal_docs' for master spoke).
            doc_ids: Optional list of specific document IDs/numbers to sync. If None, syncs all available.
            source_corpus_dir: Optional explicit path to ccba-legal-knowledge repository.
            update_registry: Whether to perform Non-Destructive Additive Merge on local legal_registry.yaml.

        Returns:
            Dictionary reporting sync status, tier used, synced bundle slugs, and registry merge counts.
        """
        if target_dir:
            dest_root = Path(target_dir)
        else:
            is_master = self.project_root.name == "ccba-legal-knowledge"
            if not is_master:
                ctx_path = self.project_root / ".md" / "workspace_context.yaml"
                if ctx_path.is_file():
                    try:
                        with open(ctx_path, encoding="utf-8") as f:
                            ctx = yaml.safe_load(f) or {}
                        proj = ctx.get("project", {}) if isinstance(ctx, dict) else {}
                        if isinstance(proj, dict) and (
                            proj.get("name") == "ccba-legal-knowledge"
                            or proj.get("archetype") == "knowledge_corpus"
                        ):
                            is_master = True
                    except Exception:
                        pass
            dest_root = (self.project_root / "legal_docs") if is_master else (self.project_root / ".md" / "legal_docs")
        dest_root.mkdir(parents=True, exist_ok=True)

        explicit = Path(source_corpus_dir) if source_corpus_dir else None
        corpus_path = self.find_local_knowledge_corpus(explicit)

        synced_bundles: list[str] = []
        registry_merge_summary: dict[str, int] = {"updated": 0, "added": 0, "preserved": 0}

        if corpus_path:
            # Tier 1: Local Knowledge Corpus Sync (0s Offline Speed)
            source_legal_docs = corpus_path / "legal_docs"
            if source_legal_docs.exists():
                categories = ["01_vbpl", "02_qcvn", "03_tcvn", "04_appendices"]
                for cat in categories:
                    cat_dir = source_legal_docs / cat
                    if not cat_dir.exists():
                        continue
                    for bundle_dir in sorted(cat_dir.iterdir()):
                        if not bundle_dir.is_dir():
                            continue
                        slug = bundle_dir.name

                        # Filter by doc_ids if specified
                        if doc_ids:
                            norm_ids = [re.sub(r"[\s\-_/.]+", "", d.lower()) for d in doc_ids]
                            norm_slug = re.sub(r"[\s\-_/.]+", "", slug.lower())
                            if not any(nid in norm_slug for nid in norm_ids):
                                continue

                        target_bundle = dest_root / cat / slug
                        target_bundle.mkdir(parents=True, exist_ok=True)

                        # Copy bundle assets
                        for item in bundle_dir.iterdir():
                            if item.is_dir():
                                dest_subdir = target_bundle / item.name
                                if dest_subdir.exists():
                                    shutil.rmtree(dest_subdir)
                                shutil.copytree(item, dest_subdir)
                            else:
                                shutil.copy2(item, target_bundle / item.name)

                        synced_bundles.append(f"{cat}/{slug}")

            # Merge master registry
            if update_registry:
                master_reg_path = corpus_path / ".md" / "data" / "legal_registry.yaml"
                if not master_reg_path.exists():
                    master_reg_path = corpus_path / "legal_registry.yaml"

                if master_reg_path.exists():
                    master_data = load_legal_registry(master_reg_path)
                    local_mgr = LegalRegistryManager(
                        self.project_root / ".md" / "data" / "legal_registry.yaml"
                    )
                    registry_merge_summary = local_mgr.merge_with_master_registry(
                        master_data, backup=True
                    )

            return {
                "status": "success",
                "tier": "tier_1_local_corpus",
                "source": str(corpus_path),
                "target": str(dest_root),
                "bundles_synced": synced_bundles,
                "registry_merge": registry_merge_summary,
            }
        else:
            # Tier 2: Cloud Vault Fallback
            return {
                "status": "fallback_cloud_vault",
                "tier": "tier_2_cloud_vault",
                "message": (
                    "Thư mục tri thức 'ccba-legal-knowledge' cục bộ chưa được tìm thấy. "
                    f"Có thể tải bản phát hành đóng gói từ Google Drive Legal Vault (Folder ID: {DEFAULT_DRIVE_FOLDER})."
                ),
                "target": str(dest_root),
                "bundles_synced": [],
                "registry_merge": registry_merge_summary,
            }


def sync_legal_assets(
    target_dir: Path | str | None = None,
    doc_ids: list[str] | None = None,
    source_corpus_dir: Path | str | None = None,
    update_registry: bool = True,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Convenience helper to synchronize legal assets into Spoke (ADR 0050)."""
    engine = LegalSyncEngine(project_root=project_root)
    return engine.pull_latest_okf_bundles(
        target_dir=target_dir,
        doc_ids=doc_ids,
        source_corpus_dir=source_corpus_dir,
        update_registry=update_registry,
    )
