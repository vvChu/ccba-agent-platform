"""LegalSyncEngine Facade Class."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
    """Deep module coordinating local legal registry sync, Chrome CDP discovery, and cloud drives."""

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
