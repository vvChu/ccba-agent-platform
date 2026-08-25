"""Modular Sync package for CCBA Legal Intelligence Platform."""

from __future__ import annotations

from .cdp_discovery import download_via_cdp_or_client, search_thuvienphapluat_via_cdp
from .drive_uploader import (
    GOOGLE_API_AVAILABLE,
    clean_google_drive_folder,
    get_drive_service,
    upload_to_google_drive,
)
from .engine import DEFAULT_DRIVE_FOLDER, LegalSyncEngine
from .notebooklm_sync import sync_registry_to_notebooklm
from .utils import (
    calculate_md5,
    calculate_sha256,
    ensure_chrome_debug_port,
    is_port_open,
)

__all__ = [
    "DEFAULT_DRIVE_FOLDER",
    "calculate_md5",
    "calculate_sha256",
    "is_port_open",
    "ensure_chrome_debug_port",
    "GOOGLE_API_AVAILABLE",
    "get_drive_service",
    "clean_google_drive_folder",
    "upload_to_google_drive",
    "search_thuvienphapluat_via_cdp",
    "download_via_cdp_or_client",
    "sync_registry_to_notebooklm",
    "LegalSyncEngine",
]
