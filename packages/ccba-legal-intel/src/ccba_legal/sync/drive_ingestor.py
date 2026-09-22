"""Google Drive Multi-Scope Knowledge Ingestor & Deduplication Engine.

Provides multi-scope scanning (My Drive, Shared with Me, Shared Drives),
recursive shared folder traversal, Google Shortcut resolution, format
conversion (Google Docs -> PDF), and 2-tier deduplication (pre-download
metadata match + post-download SHA-256 provenance stamping).
"""

from __future__ import annotations

import datetime
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.sync.drive_client import get_drive_service
from ccba_legal.sync.utils import calculate_sha256

logger = logging.getLogger(__name__)

# Supported document extensions and MIME types
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls"}
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
GOOGLE_SHORTCUT_MIME = "application/vnd.google-apps.shortcut"
GOOGLE_FOLDER_MIME = "application/vnd.google-apps.folder"

DEFAULT_REGISTRY_PATH = Path(".md/extracted_docs/gdrive/gdrive_registry.yaml")
DEFAULT_OUTPUT_DIR = Path(".md/extracted_docs/gdrive")


def sanitize_drive_filename(name: str) -> str:
    """Sanitize filename from Google Drive, stripping invalid filesystem characters."""
    sanitized = re.sub(r'[\\/*?:"<>|]', "_", name)
    sanitized = sanitized.strip().strip(".")
    return sanitized or "unnamed_document"


@dataclass
class DriveItem:
    """Represents an item discovered from Google Drive."""

    id: str
    name: str
    mime_type: str
    size_bytes: int = 0
    modified_time: str = ""
    md5_checksum: str | None = None
    sha256: str | None = None
    scope: str = "my-drive"
    web_view_link: str = ""
    is_folder: bool = False
    is_shortcut: bool = False
    target_id: str | None = None
    parent_id: str | None = None

    def is_supported(self) -> bool:
        """Check whether the item is supported for knowledge ingestion."""
        if self.is_folder:
            return False
        if self.mime_type == GOOGLE_DOC_MIME:
            return True
        ext = Path(self.name).suffix.lower()
        return ext in SUPPORTED_EXTENSIONS

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class GoogleDriveIngestor:
    """Multi-scope Google Drive Ingestion and Deduplication Engine."""

    def __init__(
        self,
        service: Any = None,
        registry_path: Path | None = None,
        output_dir: Path | None = None,
    ) -> None:
        """Initialize GoogleDriveIngestor.

        Args:
            service: Optional pre-configured Google Drive service resource.
            registry_path: Path to gdrive_registry.yaml.
            output_dir: Root output directory for downloaded assets.
        """
        self.service = service
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.registry_path = registry_path or (
            DEFAULT_REGISTRY_PATH if output_dir is None else self.output_dir / "gdrive_registry.yaml"
        )
        self.registry: dict[str, Any] = self._load_registry()

    def _get_service(self) -> Any:
        """Lazy-initialize or return Drive service."""
        if self.service is None:
            self.service = get_drive_service()
        return self.service

    def _load_registry(self) -> dict[str, Any]:
        """Load registry from YAML file."""
        if not self.registry_path.exists():
            return {"files": {}, "last_updated": ""}
        try:
            with open(self.registry_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    data.setdefault("files", {})
                    return data
        except Exception as e:
            logger.warning(f"Lỗi đọc registry {self.registry_path}: {e}")
        return {"files": {}, "last_updated": ""}

    def save_registry(self) -> None:
        """Save registry to YAML file atomically."""
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            self.registry["last_updated"] = datetime.datetime.now(
                datetime.timezone.utc
            ).isoformat()
            with open(self.registry_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.registry, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            logger.error(f"Lỗi ghi registry {self.registry_path}: {e}")

    def _item_from_api_dict(self, data: dict[str, Any], scope: str) -> DriveItem:
        """Parse raw API dictionary into DriveItem."""
        mime = data.get("mimeType", "")
        is_folder = mime == GOOGLE_FOLDER_MIME
        is_shortcut = mime == GOOGLE_SHORTCUT_MIME
        target_id = None
        if is_shortcut:
            shortcut_details = data.get("shortcutDetails", {})
            target_id = shortcut_details.get("targetId")

        raw_size = data.get("size")
        size_bytes = int(raw_size) if raw_size is not None else 0

        parents = data.get("parents", [])
        parent_id = parents[0] if parents else None

        return DriveItem(
            id=data.get("id", ""),
            name=data.get("name", ""),
            mime_type=mime,
            size_bytes=size_bytes,
            modified_time=data.get("modifiedTime", ""),
            md5_checksum=data.get("md5Checksum"),
            scope=scope,
            web_view_link=data.get("webViewLink", ""),
            is_folder=is_folder,
            is_shortcut=is_shortcut,
            target_id=target_id,
            parent_id=parent_id,
        )

    def scan_my_drive(
        self, folder_id: str | None = None, recursive: bool = True
    ) -> list[DriveItem]:
        """Scan items in user's My Drive.

        Args:
            folder_id: Optional specific folder ID. If None, queries all owned files.
            recursive: Whether to traverse subfolders if folder_id is specified.

        Returns:
            List of DriveItem objects.
        """
        service = self._get_service()
        items: list[DriveItem] = []

        if folder_id is not None:
            # Traversal starting from folder_id
            folders_to_scan = [folder_id]
            seen_folders = set(folders_to_scan)

            while folders_to_scan:
                curr_folder = folders_to_scan.pop(0)
                q = f"'{curr_folder}' in parents and trashed = false"
                page_token = None
                while True:
                    kwargs: dict[str, Any] = {
                        "q": q,
                        "fields": "nextPageToken, files(id, name, mimeType, size, modifiedTime, md5Checksum, webViewLink, shortcutDetails, parents)",
                        "pageSize": 100,
                        "supportsAllDrives": True,
                        "includeItemsFromAllDrives": True,
                    }
                    if page_token:
                        kwargs["pageToken"] = page_token

                    resp = service.files().list(**kwargs).execute()
                    for f in resp.get("files", []):
                        item = self._item_from_api_dict(f, scope="my-drive")
                        items.append(item)
                        if recursive:
                            if item.is_folder and item.id not in seen_folders:
                                seen_folders.add(item.id)
                                folders_to_scan.append(item.id)
                            elif item.is_shortcut and item.target_id and item.target_id not in seen_folders:
                                shortcut_details = f.get("shortcutDetails", {})
                                if shortcut_details.get("targetMimeType") == GOOGLE_FOLDER_MIME:
                                    seen_folders.add(item.target_id)
                                    folders_to_scan.append(item.target_id)

                    page_token = resp.get("nextPageToken")
                    if not page_token:
                        break
        else:
            # Query all files owned by user in My Drive
            q = "trashed = false and 'me' in owners"
            page_token = None
            while True:
                kwargs = {
                    "q": q,
                    "fields": "nextPageToken, files(id, name, mimeType, size, modifiedTime, md5Checksum, webViewLink, shortcutDetails, parents)",
                    "pageSize": 100,
                    "supportsAllDrives": True,
                    "includeItemsFromAllDrives": True,
                }
                if page_token:
                    kwargs["pageToken"] = page_token

                resp = service.files().list(**kwargs).execute()
                for f in resp.get("files", []):
                    items.append(self._item_from_api_dict(f, scope="my-drive"))

                page_token = resp.get("nextPageToken")
                if not page_token:
                    break

        return items

    def scan_shared_with_me(self) -> list[DriveItem]:
        """Scan items shared directly with the user, with recursive folder expansion.

        Returns:
            List of DriveItem objects.
        """
        service = self._get_service()
        items: list[DriveItem] = []
        folders_to_expand: list[str] = []
        seen_folders: set[str] = set()

        q = "sharedWithMe = true and trashed = false"
        page_token = None
        while True:
            kwargs: dict[str, Any] = {
                "q": q,
                "fields": "nextPageToken, files(id, name, mimeType, size, modifiedTime, md5Checksum, webViewLink, shortcutDetails, parents)",
                "pageSize": 100,
                "supportsAllDrives": True,
                "includeItemsFromAllDrives": True,
            }
            if page_token:
                kwargs["pageToken"] = page_token

            resp = service.files().list(**kwargs).execute()
            for f in resp.get("files", []):
                item = self._item_from_api_dict(f, scope="shared-with-me")
                items.append(item)
                if item.is_folder and item.id not in seen_folders:
                    seen_folders.add(item.id)
                    folders_to_expand.append(item.id)
                elif item.is_shortcut and item.target_id and item.target_id not in seen_folders:
                    shortcut_details = f.get("shortcutDetails", {})
                    if shortcut_details.get("targetMimeType") == GOOGLE_FOLDER_MIME:
                        seen_folders.add(item.target_id)
                        folders_to_expand.append(item.target_id)

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        # Recursive expansion of shared folders
        while folders_to_expand:
            curr_folder = folders_to_expand.pop(0)
            sub_q = f"'{curr_folder}' in parents and trashed = false"
            sub_token = None
            while True:
                kwargs = {
                    "q": sub_q,
                    "fields": "nextPageToken, files(id, name, mimeType, size, modifiedTime, md5Checksum, webViewLink, shortcutDetails, parents)",
                    "pageSize": 100,
                    "supportsAllDrives": True,
                    "includeItemsFromAllDrives": True,
                }
                if sub_token:
                    kwargs["pageToken"] = sub_token

                resp = service.files().list(**kwargs).execute()
                for f in resp.get("files", []):
                    item = self._item_from_api_dict(f, scope="shared-with-me")
                    items.append(item)
                    if item.is_folder and item.id not in seen_folders:
                        seen_folders.add(item.id)
                        folders_to_expand.append(item.id)
                    elif item.is_shortcut and item.target_id and item.target_id not in seen_folders:
                        shortcut_details = f.get("shortcutDetails", {})
                        if shortcut_details.get("targetMimeType") == GOOGLE_FOLDER_MIME:
                            seen_folders.add(item.target_id)
                            folders_to_expand.append(item.target_id)

                sub_token = resp.get("nextPageToken")
                if not sub_token:
                    break

        return items

    def scan_shared_drives(self) -> list[DriveItem]:
        """Scan items across all Shared Drives accessible to the user.

        Returns:
            List of DriveItem objects.
        """
        service = self._get_service()
        items: list[DriveItem] = []

        q = "trashed = false"
        page_token = None
        while True:
            kwargs: dict[str, Any] = {
                "q": q,
                "corpora": "allDrives",
                "includeItemsFromAllDrives": True,
                "supportsAllDrives": True,
                "fields": "nextPageToken, files(id, name, mimeType, size, modifiedTime, md5Checksum, webViewLink, shortcutDetails, parents)",
                "pageSize": 100,
            }
            if page_token:
                kwargs["pageToken"] = page_token

            try:
                resp = service.files().list(**kwargs).execute()
            except Exception as e:
                logger.warning(f"Không thể quét Shared Drives qua corpora='allDrives': {e}")
                break

            for f in resp.get("files", []):
                items.append(self._item_from_api_dict(f, scope="shared-drives"))

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        return items

    def resolve_shortcut(self, item: DriveItem) -> DriveItem:
        """Resolve a Google Shortcut to its real underlying target item.

        Args:
            item: A DriveItem with is_shortcut=True.

        Returns:
            Resolved DriveItem, or the original item if resolution fails.
        """
        if not item.is_shortcut or not item.target_id:
            return item

        service = self._get_service()
        try:
            data = (
                service.files()
                .get(
                    fileId=item.target_id,
                    fields="id, name, mimeType, size, modifiedTime, md5Checksum, webViewLink",
                    supportsAllDrives=True,
                )
                .execute()
            )
            resolved = self._item_from_api_dict(data, scope=item.scope)
            # Inherit original shortcut name if desired, but keep target data
            if not resolved.name:
                resolved.name = item.name
            return resolved
        except Exception as e:
            logger.warning(f"Lỗi phân giải shortcut {item.id} -> {item.target_id}: {e}")
            return item

    def should_download(self, item: DriveItem, local_dest: Path) -> bool:
        """Pre-download deduplication: check if file is already synced and unchanged.

        Args:
            item: DriveItem candidate.
            local_dest: Destination path on local disk.

        Returns:
            True if download is needed; False if it can be skipped.
        """
        if not local_dest.exists():
            return True
        if local_dest.stat().st_size == 0 and (item.size_bytes or 0) > 0:
            return True

        files_registry = self.registry.get("files", {})
        if item.id not in files_registry:
            return True

        entry = files_registry[item.id]
        reg_mod = entry.get("modified_time")
        reg_md5 = entry.get("md5_checksum")

        # If modifiedTime matches
        if item.modified_time and reg_mod == item.modified_time:
            # If MD5 is provided, verify it
            if item.md5_checksum is not None:
                return reg_md5 != item.md5_checksum
            # For Google Docs without MD5, modifiedTime match is sufficient
            return False

        return True

    def download_item(
        self,
        item: DriveItem,
        dest_dir: Path | None = None,
        force: bool = False,
    ) -> Path | None:
        """Download a DriveItem and record post-download cryptographic SHA-256 provenance.

        Args:
            item: Item to download.
            dest_dir: Target folder. Defaults to self.output_dir.
            force: If True, bypasses pre-download cache check.

        Returns:
            Path to downloaded local file, or None if skipped/failed.
        """
        if item.is_folder:
            return None

        # Resolve shortcut if necessary
        resolved_item = self.resolve_shortcut(item) if item.is_shortcut else item
        if resolved_item.is_folder:
            return None

        target_dir = dest_dir or self.output_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        raw_name = resolved_item.name
        is_gdoc = resolved_item.mime_type == GOOGLE_DOC_MIME
        if is_gdoc and not raw_name.lower().endswith(".pdf"):
            raw_name = f"{raw_name}.pdf"
        target_name = sanitize_drive_filename(raw_name)

        local_path = target_dir / target_name

        # Prevent collision if a file with the same name belongs to another item ID
        files_registry = self.registry.get("files", {})
        existing_owner_id = next(
            (
                fid
                for fid, finfo in files_registry.items()
                if finfo.get("local_path") == str(local_path.resolve())
            ),
            None,
        )
        if existing_owner_id and existing_owner_id != resolved_item.id:
            stem = Path(target_name).stem
            suffix = Path(target_name).suffix
            target_name = f"{stem}_{resolved_item.id[:8]}{suffix}"
            local_path = target_dir / target_name

        # 1. Pre-download check
        if not force and not self.should_download(resolved_item, local_path):
            logger.info(f"⏭️ Bỏ qua {target_name} (Đã có trong registry và không đổi)")
            return local_path

        service = self._get_service()
        try:
            logger.info(f"⬇️ Đang tải '{target_name}' (ID: {resolved_item.id})...")
            if is_gdoc:
                # Export Google Docs to PDF
                request = service.files().export_media(
                    fileId=resolved_item.id,
                    mimeType="application/pdf",
                )
                content = request.execute()
            else:
                # Direct binary download
                request = service.files().get_media(
                    fileId=resolved_item.id,
                    supportsAllDrives=True,
                )
                content = request.execute()

            local_path.write_bytes(content)

            # 2. Post-download SHA-256 calculation & Registry update
            sha256_hash = calculate_sha256(local_path)
            resolved_item.sha256 = sha256_hash

            self.registry.setdefault("files", {})[resolved_item.id] = {
                "name": target_name,
                "original_name": resolved_item.name,
                "mime_type": resolved_item.mime_type,
                "size_bytes": local_path.stat().st_size,
                "modified_time": resolved_item.modified_time,
                "md5_checksum": resolved_item.md5_checksum,
                "sha256": sha256_hash,
                "scope": resolved_item.scope,
                "web_view_link": resolved_item.web_view_link,
                "local_path": str(local_path.resolve()),
                "synced_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
            self.save_registry()
            logger.info(f"✅ Đã tải thành công: {target_name} (SHA-256: {sha256_hash[:12]}...)")
            return local_path

        except Exception as e:
            logger.error(f"❌ Thất bại khi tải {resolved_item.id} ({target_name}): {e}")
            return None

    def ingest(
        self,
        scope: str = "all",
        folder_id: str | None = None,
        dest_dir: Path | None = None,
        dry_run: bool = False,
        force: bool = False,
    ) -> dict[str, Any]:
        """Orchestrate multi-scope scanning and download ingestion.

        Args:
            scope: One of 'all', 'my-drive', 'shared', 'drives'.
            folder_id: Optional root folder ID for my-drive.
            dest_dir: Target output directory.
            dry_run: If True, only scans and returns metrics without downloading.
            force: If True, forces redownloading all matching items.

        Returns:
            Dictionary with execution statistics and item details.
        """
        all_candidates: list[DriveItem] = []

        if scope in ("all", "my-drive"):
            logger.info("🔍 Đang quét My Drive...")
            all_candidates.extend(self.scan_my_drive(folder_id=folder_id))

        if scope in ("all", "shared"):
            logger.info("🔍 Đang quét Shared with me...")
            all_candidates.extend(self.scan_shared_with_me())

        if scope in ("all", "drives"):
            logger.info("🔍 Đang quét Shared Drives...")
            all_candidates.extend(self.scan_shared_drives())

        # Deduplicate items by ID from different queries
        unique_items_map: dict[str, DriveItem] = {}
        for item in all_candidates:
            if item.id not in unique_items_map:
                unique_items_map[item.id] = item

        # Filter supported files and resolve shortcuts (deduplicating by resolved item id)
        supported_items_by_id: dict[str, DriveItem] = {}
        for item in unique_items_map.values():
            if item.is_folder:
                continue
            actual_item = self.resolve_shortcut(item) if item.is_shortcut else item
            if actual_item.is_folder:
                continue
            if actual_item.is_supported() and actual_item.id not in supported_items_by_id:
                supported_items_by_id[actual_item.id] = actual_item
        supported_items = list(supported_items_by_id.values())

        stats: dict[str, Any] = {
            "scope": scope,
            "total_scanned": len(unique_items_map),
            "supported_found": len(supported_items),
            "downloaded": 0,
            "skipped": 0,
            "failed": 0,
            "items": [],
        }

        if dry_run:
            logger.info(f"🔎 [DRY-RUN] Phát hiện {len(supported_items)} tệp tin phù hợp.")
            stats["items"] = [i.to_dict() for i in supported_items]
            return stats

        target_dir = dest_dir or self.output_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        for item in supported_items:
            raw_name = item.name
            is_gdoc = item.mime_type == GOOGLE_DOC_MIME
            if is_gdoc and not raw_name.lower().endswith(".pdf"):
                raw_name = f"{raw_name}.pdf"
            target_name = sanitize_drive_filename(raw_name)
            local_dest = target_dir / target_name

            should_dl = force or self.should_download(item, local_dest)
            if not should_dl:
                stats["skipped"] += 1
                stats["items"].append({"id": item.id, "name": target_name, "status": "skipped"})
                continue

            res_path = self.download_item(item, dest_dir=target_dir, force=force)
            if res_path:
                stats["downloaded"] += 1
                stats["items"].append({
                    "id": item.id,
                    "name": target_name,
                    "status": "downloaded",
                    "sha256": item.sha256,
                    "path": str(res_path),
                })
            else:
                stats["failed"] += 1
                stats["items"].append({"id": item.id, "name": target_name, "status": "failed"})

        return stats


__all__ = [
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_REGISTRY_PATH",
    "DriveItem",
    "GOOGLE_DOC_MIME",
    "GOOGLE_FOLDER_MIME",
    "GOOGLE_SHORTCUT_MIME",
    "GoogleDriveIngestor",
    "SUPPORTED_EXTENSIONS",
    "sanitize_drive_filename",
]
