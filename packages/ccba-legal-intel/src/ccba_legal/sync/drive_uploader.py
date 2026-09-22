"""Google Drive OAuth Authentication and Media Uploader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ccba_legal.sync.drive_client import (
    GOOGLE_API_AVAILABLE,
    _import_google_api,
    get_credentials_dir,
    get_drive_service,
    migrate_drive_credentials,
)
from ccba_legal.sync.utils import calculate_md5


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


__all__ = [
    "GOOGLE_API_AVAILABLE",
    "_import_google_api",
    "clean_google_drive_folder",
    "get_credentials_dir",
    "get_drive_service",
    "migrate_drive_credentials",
    "upload_to_google_drive",
]

