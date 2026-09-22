"""Modular Sync package for CCBA Legal Intelligence Platform (ADR 0050)."""

from __future__ import annotations

from .cdp_discovery import download_via_cdp_or_client, search_thuvienphapluat_via_cdp
from .drive_client import (
    GOOGLE_API_AVAILABLE,
    _import_google_api,
    get_credentials_dir,
    get_drive_service,
    migrate_drive_credentials,
)
from .drive_ingestor import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REGISTRY_PATH,
    DriveItem,
    GoogleDriveIngestor,
    sanitize_drive_filename,
)
from .drive_uploader import (
    clean_google_drive_folder,
    upload_to_google_drive,
)
from .engine import DEFAULT_DRIVE_FOLDER, LegalSyncEngine, sync_legal_assets
from .notebooklm_sync import sync_registry_to_notebooklm
from .utils import (
    calculate_md5,
    calculate_sha256,
    ensure_chrome_debug_port,
    is_port_open,
    safe_copy2,
    safe_remove,
    safe_rmtree,
)

__all__ = [
    "DEFAULT_DRIVE_FOLDER",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_REGISTRY_PATH",
    "DriveItem",
    "GOOGLE_API_AVAILABLE",
    "GoogleDriveIngestor",
    "LegalSyncEngine",
    "_import_google_api",
    "calculate_md5",
    "calculate_sha256",
    "clean_google_drive_folder",
    "download_via_cdp_or_client",
    "ensure_chrome_debug_port",
    "get_credentials_dir",
    "get_drive_service",
    "is_port_open",
    "migrate_drive_credentials",
    "safe_copy2",
    "safe_remove",
    "safe_rmtree",
    "sanitize_drive_filename",
    "search_thuvienphapluat_via_cdp",
    "sync_legal_assets",
    "sync_registry_to_notebooklm",
    "upload_to_google_drive",
]
