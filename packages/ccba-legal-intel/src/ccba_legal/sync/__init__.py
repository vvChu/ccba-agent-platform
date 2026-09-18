"""Modular Sync package for CCBA Legal Intelligence Platform (ADR 0050)."""

from __future__ import annotations

from .cdp_discovery import download_via_cdp_or_client, search_thuvienphapluat_via_cdp
from .drive_uploader import (
    GOOGLE_API_AVAILABLE,
    clean_google_drive_folder,
    get_credentials_dir,
    get_drive_service,
    migrate_drive_credentials,
    upload_to_google_drive,
)
from .engine import DEFAULT_DRIVE_FOLDER, LegalSyncEngine, sync_legal_assets
from .notebooklm_sync import sync_registry_to_notebooklm
from .utils import (
    _is_link_or_junction,
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
    "_is_link_or_junction",
    "calculate_md5",
    "calculate_sha256",
    "is_port_open",
    "ensure_chrome_debug_port",
    "safe_copy2",
    "safe_remove",
    "safe_rmtree",
    "GOOGLE_API_AVAILABLE",
    "get_credentials_dir",
    "get_drive_service",
    "migrate_drive_credentials",
    "clean_google_drive_folder",
    "upload_to_google_drive",
    "search_thuvienphapluat_via_cdp",
    "download_via_cdp_or_client",
    "sync_registry_to_notebooklm",
    "LegalSyncEngine",
    "sync_legal_assets",
]
