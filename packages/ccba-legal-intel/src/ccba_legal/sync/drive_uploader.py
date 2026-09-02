"""Google Drive OAuth Authentication and Media Uploader."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from ccba_legal.sync.utils import calculate_md5


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


def get_drive_service() -> Any:
    """Initialize Drive API service using personal token or ADC fallback."""
    available, google_auth, Request, Credentials, build, HttpError, _ = _import_google_api()
    if not available:
        raise ImportError(
            "Thiếu thư viện googleapiclient hoặc google-auth. "
            "Cài đặt: pip install ccba-legal-intel[cloud]"
        )

    # 1. Try personal token
    old_token = Path(".md/scratch/drive_token.json")
    token_dir = Path.home() / ".ccba" / "credentials"
    env_dir = os.environ.get("CCBA_CREDENTIALS_DIR")
    if env_dir:
        token_dir = Path(env_dir)

    token_path = token_dir / "drive_token.json"

    if old_token.exists():
        if not token_path.exists():
            try:
                token_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_token), str(token_path))
                print(f"[Drive Info] Tự động di trú token cá nhân sang: {token_path}")
            except Exception as e:
                print(f"[Drive Warning] Lỗi di trú token: {e}")
                token_path = old_token
        else:
            try:
                old_token.unlink()
            except Exception:
                pass

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
            print(f"[Drive Warning] Lỗi nạp token cá nhân: {e}")
            print("[Drive Info] Thử fallback sang kiểm tra ADC mặc định...")

    # 2. Fallback to ADC
    credentials, _project = google_auth.default(scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=credentials)


def clean_google_drive_folder(folder_id: str) -> None:
    """Delete all files in a Google Drive folder for a clean slate."""
    try:
        service = get_drive_service()
        print(f"[Drive Cleanup] Đang truy vấn danh sách tệp tin trong Drive: {folder_id}...")
        q = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(q=q, fields="files(id, name)").execute()
        files = results.get("files", [])
        if not files:
            print("[Drive Cleanup Info] Thư mục Drive đã sạch sẽ.")
            return

        print(f"[Drive Cleanup Info] Phát hiện {len(files)} tệp tin. Tiến hành xóa sạch...")
        for f in files:
            print(f"[Drive Cleanup Action] Đang xóa: '{f['name']}' (ID: {f['id']})...")
            try:
                service.files().delete(fileId=f["id"]).execute()
            except Exception as del_err:
                print(f"[Drive Cleanup Warning] Không thể xóa tệp {f['id']}: {del_err}")
        print("[Drive Cleanup Success] Đã làm sạch thư mục Google Drive chung!")
    except Exception as e:
        print(f"[Drive Cleanup Warning] Lỗi khi dọn dẹp thư mục Drive: {e}")


def upload_to_google_drive(file_path: Path, folder_id: str, target_name: str) -> str | None:
    """Upload a file to Google Drive with deduplication support."""
    _, _, _, _, _, HttpError, MediaFileUpload = _import_google_api()
    try:
        service = get_drive_service()
    except Exception as e:
        print(f"[Drive Warning] Không thể khởi tạo Google Drive Service: {e}.")
        return None

    try:
        ext = file_path.suffix.lower()
        if ext == ".pdf":
            local_mime = "application/pdf"
            google_mime = "application/pdf"
        elif ext in [".docx", ".doc"]:
            local_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            google_mime = "application/vnd.google-apps.document"
        elif ext in [".xlsx", ".xls"]:
            local_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            google_mime = "application/vnd.google-apps.spreadsheet"
        else:
            local_mime = "application/octet-stream"
            google_mime = None

        name_without_ext = Path(target_name).stem if google_mime else target_name
        q = (
            f"'{folder_id}' in parents and "
            f"(name = '{target_name}' or name = '{name_without_ext}') "
            f"and trashed = false"
        )
        results = service.files().list(q=q, fields="files(id, name, md5Checksum)").execute()
        files = results.get("files", [])

        if files:
            existing_file = files[0]
            existing_id = existing_file["id"]
            existing_md5 = existing_file.get("md5Checksum", "")
            local_md5 = calculate_md5(file_path)

            if existing_md5 == local_md5:
                print(f"[Drive Deduplicate] Tệp '{target_name}' trùng khớp. Bỏ qua upload.")
                try:
                    service.permissions().create(
                        fileId=existing_id, body={"type": "anyone", "role": "reader"}
                    ).execute()
                except Exception as share_err:
                    print(f"[Drive Share Warning] Không thể set public: {share_err}")
                return str(existing_id)

            print(f"[Drive Update] Tệp '{target_name}' đã thay đổi. Ghi đè file_id: {existing_id}")
            media = MediaFileUpload(str(file_path), mimetype=local_mime, resumable=True)
            file_metadata: dict[str, Any] = {}
            if google_mime:
                file_metadata["mimeType"] = google_mime
            updated_file = (
                service.files()
                .update(fileId=existing_id, body=file_metadata, media_body=media)
                .execute()
            )
            file_id = updated_file.get("id")
            try:
                service.permissions().create(
                    fileId=file_id, body={"type": "anyone", "role": "reader"}
                ).execute()
            except Exception as share_err:
                print(f"[Drive Share Warning] Không thể set public: {share_err}")
            return str(file_id)

        print(f"[Drive Upload] Đang upload '{target_name}' lên Drive: {folder_id}")
        file_metadata_new: dict[str, Any] = {"name": target_name, "parents": [folder_id]}
        if google_mime:
            file_metadata_new["mimeType"] = google_mime
        media = MediaFileUpload(str(file_path), mimetype=local_mime, resumable=True)
        file = (
            service.files().create(body=file_metadata_new, media_body=media, fields="id").execute()
        )
        file_id = file.get("id")
        try:
            service.permissions().create(
                fileId=file_id, body={"type": "anyone", "role": "reader"}
            ).execute()
        except Exception as share_err:
            print(f"[Drive Share Warning] Không thể set public: {share_err}")
        return str(file_id)

    except Exception as e:
        if HttpError is not None and isinstance(e, HttpError):
            if e.resp.status == 403:
                print("\n[Drive Error 403] Lỗi Forbidden chi tiết từ Google:")
                try:
                    err_data = json.loads(e.content.decode("utf-8"))
                    print(json.dumps(err_data, indent=2, ensure_ascii=False))
                except Exception:
                    print(e.content.decode("utf-8") if e.content else e)
                print("Fallback sang luồng nạp file trực tiếp lên NotebookLM Cloud...\n")
            else:
                print(f"[Drive Warning] Lỗi gọi API Google Drive: {e}")
        else:
            print(f"[Drive Warning] Lỗi tải tệp lên Drive: {e}")
        return None
