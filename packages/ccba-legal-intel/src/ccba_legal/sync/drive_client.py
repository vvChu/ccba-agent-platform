"""Google Drive Infrastructure Client & Authentication Service Factory.

Provides decoupled authentication, token persistence, credential migration,
and Drive API service instantiation for CCBA Platform.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _import_google_api() -> tuple[bool, Any, Any, Any, Any, Any, Any]:
    """Lazy import Google API client libraries.

    Returns:
        Tuple of (available, google_auth, Request, Credentials, build, HttpError, MediaFileUpload).
    """
    try:
        import google.auth
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaFileUpload

        return True, google.auth, Request, Credentials, build, HttpError, MediaFileUpload
    except ImportError:
        return False, None, None, None, None, None, None


GOOGLE_API_AVAILABLE, *_ = _import_google_api()


def get_credentials_dir() -> Path:
    """Read credentials directory from environment variable or user home.

    Returns:
        Path to CCBA credentials directory (~/.ccba/credentials or $CCBA_CREDENTIALS_DIR).
    """
    env_dir = os.environ.get("CCBA_CREDENTIALS_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".ccba" / "credentials"


def migrate_drive_credentials(target_dir: Path | None = None) -> None:
    """Migrate legacy credentials from .md/scratch/ to credentials directory.

    Args:
        target_dir: Optional destination directory. Defaults to get_credentials_dir().
    """
    dest_dir = target_dir or get_credentials_dir()
    old_secrets = Path(".md/scratch/client_secrets.json")
    old_token = Path(".md/scratch/drive_token.json")

    if not (old_secrets.exists() or old_token.exists()):
        return

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"[Drive Warning] Không thể tạo thư mục credentials: {e}")
        return

    for old_file, target_name in [
        (old_secrets, "client_secrets.json"),
        (old_token, "drive_token.json"),
    ]:
        if not old_file.exists():
            continue
        target_file = dest_dir / target_name
        if not target_file.exists():
            try:
                shutil.move(str(old_file), str(target_file))
                logger.info(f"[Drive Info] Tự động di trú {target_name} sang: {target_file}")
            except Exception as e:
                logger.warning(f"[Drive Warning] Lỗi di trú {target_name}: {e}")
        else:
            try:
                old_file.unlink()
            except Exception:
                pass


def get_drive_service() -> Any:
    """Initialize Drive API service using personal token or ADC fallback.

    Returns:
        Resource object representing Google Drive API v3 client.

    Raises:
        ImportError: When google-api-python-client or google-auth is not installed.
    """
    available, google_auth, Request, Credentials, build, HttpError, _ = _import_google_api()
    if not available:
        raise ImportError(
            "Thiếu thư viện googleapiclient hoặc google-auth. "
            "Cài đặt: pip install ccba-legal-intel[cloud]"
        )

    # 1. Try personal token
    migrate_drive_credentials()
    token_path = get_credentials_dir() / "drive_token.json"
    if not token_path.exists():
        legacy_token = Path(".md/scratch/drive_token.json")
        if legacy_token.exists():
            token_path = legacy_token

    if token_path.exists():
        try:
            credentials = Credentials.from_authorized_user_file(
                str(token_path), scopes=["https://www.googleapis.com/auth/drive"]
            )
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                with open(token_path, "w", encoding="utf-8") as f:
                    f.write(credentials.to_json())
            return build("drive", "v3", credentials=credentials)
        except Exception as e:
            logger.warning(f"[Drive Warning] Lỗi nạp token cá nhân: {e}")
            logger.info("[Drive Info] Thử fallback sang kiểm tra ADC mặc định...")

    # 2. Fallback to ADC
    credentials, _project = google_auth.default(scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=credentials)


__all__ = [
    "GOOGLE_API_AVAILABLE",
    "_import_google_api",
    "get_credentials_dir",
    "get_drive_service",
    "migrate_drive_credentials",
]
