"""Google Drive Cloud Binary Vault Client for CCBA Legal Intelligence (ADR 0035).

Manages binary assets (PDFs and DOCX source documents) in Google Drive Vault,
linking them immutably with Git repositories via SHA-256 and Web View URLs.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]

DEFAULT_SA_PATH = Path.home() / ".ccba" / "credentials" / "service_account.json"
DEFAULT_TOKEN_PATH = Path.home() / ".ccba" / "credentials" / "drive_token.json"
VAULT_ROOT_NAME = "CCBA_Legal_Vault"


def compute_file_sha256(file_path: Path | str) -> str:
    """Compute standard SHA-256 hex digest for a file."""
    path = Path(file_path)
    if not path.exists():
        return ""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class GoogleDriveVault:
    """Multi-tier Google Drive Vault Client for Legal Knowledge Repository."""

    def __init__(self, credentials_path: Path | str | None = None) -> None:
        self.credentials_path = Path(credentials_path) if credentials_path else None
        self._service: Any | None = None
        self._root_folder_id: str | None = None

    @property
    def service(self) -> Any | None:
        """Lazy-initialize Google Drive API v3 Service."""
        if self._service is None:
            self._service = self._init_drive_service()
        return self._service

    def is_available(self) -> bool:
        """Check if Google Drive API credentials are valid and connection is active."""
        try:
            return self.service is not None
        except Exception as e:
            logger.debug(f"Google Drive Vault unavailable: {e}")
            return False

    def _init_drive_service(self) -> Any | None:
        """Initialize Google Drive Service with multi-tier credentials resolution."""
        import os
        try:
            import google.auth
            from google.oauth2 import service_account
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
        except ImportError:
            logger.warning("google-api-python-client or google-auth not installed.")
            return None

        # 1. Try dedicated authorized user token file (~/.ccba/credentials/drive_token.json)
        token_file = self.credentials_path or DEFAULT_TOKEN_PATH
        if token_file and Path(token_file).exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
                return build("drive", "v3", credentials=creds, cache_discovery=False)
            except Exception as e:
                logger.warning(f"Failed to load drive_token.json at {token_file}: {e}")

        # 2. Try Service Account Key (for Shared Drives and Server Automation)
        sa_file = self.credentials_path or Path(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", DEFAULT_SA_PATH))
        if sa_file and Path(sa_file).exists():
            try:
                creds = service_account.Credentials.from_service_account_file(str(sa_file), scopes=SCOPES)
                return build("drive", "v3", credentials=creds, cache_discovery=False)
            except Exception as e:
                logger.warning(f"Failed to load Service Account at {sa_file}: {e}")


        # 3. Try Application Default Credentials (ADC) with Drive Scope
        try:
            creds, _ = google.auth.default(scopes=SCOPES)
            return build("drive", "v3", credentials=creds, cache_discovery=False)
        except Exception as e:
            logger.debug(f"ADC with Drive scope failed: {e}")

        return None


    def get_or_create_folder(self, folder_name: str, parent_id: str | None = None) -> str | None:
        """Get existing folder ID by name or create a new one under parent_id."""
        if not self.service:
            return None

        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        try:
            response = self.service.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute()
            files = response.get("files", [])
            if files:
                return files[0]["id"]

            # Create folder
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_id:
                file_metadata["parents"] = [parent_id]

            folder = self.service.files().create(
                body=file_metadata,
                fields="id",
                supportsAllDrives=True,
            ).execute()
            return folder.get("id")
        except Exception as e:
            logger.error(f"Error getting/creating folder '{folder_name}': {e}")
            return None

    def ensure_vault_structure(self, category: str, doc_slug: str) -> str | None:
        """Ensure full directory hierarchy exists: CCBA_Legal_Vault/<category>/<doc_slug>/."""
        import os
        if not self.service:
            return None

        # 1. Root Vault Folder (check DRIVE_FOLDER_ID in env or default root)
        env_root_id = os.environ.get("DRIVE_FOLDER_ID")
        root_id = env_root_id if env_root_id else self.get_or_create_folder(VAULT_ROOT_NAME)
        if not root_id:
            return None

        # 2. Category Folder (01_vbpl, 02_qcvn, 03_tcvn)
        cat_id = self.get_or_create_folder(category, parent_id=root_id)
        if not cat_id:
            return None

        # 3. Document Folder
        doc_id = self.get_or_create_folder(doc_slug, parent_id=cat_id)
        return doc_id

    def upload_asset(
        self,
        local_path: Path | str,
        category: str,
        doc_slug: str,
        make_public_read: bool = True,
        convert_to_gdoc: bool = True,
    ) -> dict[str, Any]:
        """Upload a local PDF or DOCX file to the Google Drive Vault.
        
        If convert_to_gdoc is True, Word files (.docx/.doc) are automatically converted
        into native Google Docs format for seamless Google NotebookLM ingestion.
        """
        path = Path(local_path)
        if not path.exists():
            return {"error": f"File not found: {path}"}

        sha256 = compute_file_sha256(path)
        size_kb = round(path.stat().st_size / 1024, 1)

        if not self.service:
            return {
                "sha256": sha256,
                "size_kb": size_kb,
                "file_name": path.name,
                "vault_path": f"{VAULT_ROOT_NAME}/{category}/{doc_slug}/{path.name}",
                "status": "local_offline_mode",
            }

        try:
            from googleapiclient.http import MediaFileUpload

            target_folder_id = self.ensure_vault_structure(category, doc_slug)
            if not target_folder_id:
                return {
                    "sha256": sha256,
                    "size_kb": size_kb,
                    "file_name": path.name,
                    "vault_path": f"{VAULT_ROOT_NAME}/{category}/{doc_slug}/{path.name}",
                    "status": "local_offline_mode",
                }

            is_word_doc = path.suffix.lower() in [".docx", ".doc"]
            source_mime = (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                if is_word_doc
                else "application/pdf"
            )
            target_name = path.stem if (is_word_doc and convert_to_gdoc) else path.name

            # Check if file already exists in folder
            q = f"name = '{target_name}' and '{target_folder_id}' in parents and trashed = false"
            res = self.service.files().list(
                q=q,
                fields="files(id, webViewLink)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute()
            files = res.get("files", [])

            if files:
                file_id = files[0]["id"]
                view_url = files[0].get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view")
                media = MediaFileUpload(str(path), mimetype=source_mime, resumable=True)
                self.service.files().update(
                    fileId=file_id,
                    media_body=media,
                    supportsAllDrives=True,
                ).execute()
            else:
                # Create new file (with auto-conversion to Google Docs if word doc)
                file_metadata: dict[str, Any] = {
                    "name": target_name,
                    "parents": [target_folder_id],
                }
                if is_word_doc and convert_to_gdoc:
                    file_metadata["mimeType"] = "application/vnd.google-apps.document"

                media = MediaFileUpload(str(path), mimetype=source_mime, resumable=True)
                created = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, webViewLink",
                    supportsAllDrives=True,
                ).execute()
                file_id = created.get("id")
                view_url = created.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view")

                if make_public_read and file_id:
                    try:
                        self.service.permissions().create(
                            fileId=file_id,
                            body={"type": "anyone", "role": "reader"},
                            supportsAllDrives=True,
                        ).execute()
                    except Exception as pe:
                        logger.debug(f"Could not set public read permission: {pe}")



            return {
                "sha256": sha256,
                "size_kb": size_kb,
                "file_name": path.name,
                "gdrive_file_id": file_id,
                "gdrive_view_url": view_url,
                "vault_path": f"{VAULT_ROOT_NAME}/{category}/{doc_slug}/{path.name}",
                "status": "synced",
            }
        except Exception as e:
            logger.error(f"Failed to upload {path} to Drive Vault: {e}")
            return {
                "sha256": sha256,
                "size_kb": size_kb,
                "file_name": path.name,
                "vault_path": f"{VAULT_ROOT_NAME}/{category}/{doc_slug}/{path.name}",
                "status": f"upload_error: {e}",
            }

    def download_asset(self, file_id: str, dest_path: Path | str) -> Path | None:
        """Download an asset from Google Drive Vault to local path."""
        if not self.service:
            return None

        try:
            from googleapiclient.http import MediaIoBaseDownload

            dest = Path(dest_path)
            dest.parent.mkdir(parents=True, exist_ok=True)

            request = self.service.files().get_media(fileId=file_id)
            with open(dest, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            return dest
        except Exception as e:
            logger.error(f"Failed to download asset {file_id}: {e}")
            return None
