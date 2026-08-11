"""sync.py - Legal Auto-Sync Pipeline Deep Module.

Provides `LegalSyncEngine` for automated synchronization of legal documents,
Google Drive integration, Chrome CDP crawling, and NotebookLM cloud indexing.

This is the single source of truth for all legal sync logic — scripts/legal_sync.py
is a thin CLI wrapper that delegates to this module.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

import hashlib
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.parse
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

try:
    from .crawler import ChromeCDP, trigger_download
except ImportError:
    ChromeCDP = None  # type: ignore[assignment, misc]
    trigger_download = None  # type: ignore[assignment]


DEFAULT_DRIVE_FOLDER = "1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2"


# ---------------------------------------------------------------------------
# Standalone utility functions (kept at module level for backward compat)
# ---------------------------------------------------------------------------

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 hash of file for Google Drive matching."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of file for local cache audit."""
    hash_sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()


def is_port_open(port: int) -> bool:
    """Check if TCP port is active."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def ensure_chrome_debug_port() -> bool:
    """Detect and launch Google Chrome in debug port 9222 mode if inactive."""
    if is_port_open(9222):
        return True

    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]

    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break

    if not chrome_path:
        return False

    try:
        user_data_dir = os.path.join(
            os.path.expanduser("~"), ".gemini", "antigravity", "chrome-debug-profile"
        )
        os.makedirs(user_data_dir, exist_ok=True)

        cmd = [
            chrome_path,
            "--remote-debugging-port=9222",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        for _ in range(10):
            time.sleep(0.5)
            if is_port_open(9222):
                return True
        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Lazy import helpers for optional dependencies
# ---------------------------------------------------------------------------

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


def _import_notebooklm_client() -> Any:
    """Lazy import ccba_notebooklm.get_client (optional [cloud] dependency).

    Returns:
        The get_client callable, or None if not installed.
    """
    try:
        from ccba_notebooklm import get_client
        return get_client
    except ImportError:
        return None


# ---------------------------------------------------------------------------
# LegalSyncEngine — Deep Module
# ---------------------------------------------------------------------------

class LegalSyncEngine:
    """Deep module coordinating local legal registry sync, Chrome CDP discovery, and cloud drives.

    Consolidates all sync logic behind a small interface:
    - ``sync_registry_to_notebooklm()`` — full pipeline
    - ``search_thuvienphapluat_via_cdp()`` — auto-discovery
    - ``upload_to_google_drive()`` — Drive upload with dedup
    - ``verify_environment()`` — dependency health check
    """

    def __init__(self, project_root: Path | None = None) -> None:
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root

    # -- Hash utilities --

    def calculate_file_hashes(self, file_path: Path) -> dict[str, str]:
        """Compute both MD5 and SHA256 for a target file."""
        return {
            "md5": calculate_md5(file_path),
            "sha256": calculate_sha256(file_path),
        }

    def verify_environment(self) -> dict[str, bool]:
        """Verify environment dependencies."""
        google_available, *_ = _import_google_api()
        return {
            "google_api": google_available,
            "chrome_cdp": ChromeCDP is not None,
            "chrome_port_open": is_port_open(9222),
            "notebooklm": _import_notebooklm_client() is not None,
        }

    # -- Chrome CDP Auto-Discovery --

    def search_thuvienphapluat_via_cdp(self, query: str) -> str | None:
        """Search for a legal document URL on thuvienphapluat.vn via Google Search using Chrome CDP."""
        if ChromeCDP is None:
            return None

        if not ensure_chrome_debug_port():
            print(
                "[Auto-Discovery Warning] Không thể kích hoạt hoặc kết nối tới cổng debug Chrome."
            )
            return None

        print(f"[Auto-Discovery] Đang tìm kiếm link Thư viện Pháp luật cho: {query}")
        try:
            cdp = ChromeCDP(port=9222)
            pages = cdp.get_pages()
            if not pages:
                print("[Auto-Discovery Warning] Không tìm thấy tab Chrome nào đang mở.")
                return None

            cdp.connect_tab(pages[0]["webSocketDebuggerUrl"])

            search_query = f'site:thuvienphapluat.vn "{query}"'
            search_url = (
                f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"
            )

            cdp.navigate(search_url)
            cdp.wait_ready()
            cdp.handle_cloudflare()

            js_extract_link = """
            (() => {
                let links = Array.from(document.querySelectorAll('a'))
                    .map(a => a.href || "")
                    .filter(href => href.includes('thuvienphapluat.vn/van-ban/'));
                return links.length > 0 ? links[0] : null;
            })()
            """
            link = cdp.evaluate_js(js_extract_link)
            if link:
                link_clean = link.split("?")[0].split("#")[0]
                print(f"[Auto-Discovery Success] Tìm thấy liên kết: {link_clean}")
                return str(link_clean)

            print("[Auto-Discovery Info] Không tìm thấy link Thư viện Pháp luật trên Google.")
            return None
        except Exception as e:
            print(f"[Auto-Discovery Warning] Lỗi tìm kiếm Google CDP: {e}")
            return None

    def download_via_cdp_or_client(self, url: str, dest_path: Path) -> bool:
        """Download a file using Chrome CDP (preferred) or urllib fallback."""
        # 1. Try Chrome CDP
        if ChromeCDP is not None and trigger_download is not None:
            try:
                ensure_chrome_debug_port()
                print(f"[CDP] Thử kết nối Chrome CDP trên port 9222 để tải: {url}")
                cdp = ChromeCDP(port=9222)
                pages = cdp.get_pages()
                if pages:
                    cdp.connect_tab(pages[0]["webSocketDebuggerUrl"])
                    cdp.navigate(url)
                    cdp.wait_ready()
                    cdp.handle_cloudflare()
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    success = trigger_download(cdp, dest_path.parent, dest_path.stem)
                    if success:
                        print(f"[CDP] Tải file thành công: {dest_path.name}")
                        return True
            except Exception as e:
                print(f"[CDP Warning] Lỗi kết nối hoặc thực thi Chrome CDP: {e}")
                print("[CDP Warning] Thử fallback sang client tải trực tiếp...")

        # 2. Fallback to urllib
        try:
            import urllib.request

            print(f"[Urllib] Tải trực tiếp từ URL: {url}")
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            req = urllib.request.Request(url, headers=headers)
            with (
                urllib.request.urlopen(req, timeout=20) as response,
                open(dest_path, "wb") as out_file,
            ):
                out_file.write(response.read())
            print(f"[Urllib] Tải file thành công: {dest_path.name}")
            return True
        except Exception as e:
            print(f"[Error] Tải file từ internet thất bại: {e}")
            return False

    # -- Google Drive Integration --

    def get_drive_service(self) -> Any:
        """Initialize Drive API service using personal token or ADC fallback."""
        available, google_auth, Request, Credentials, build, HttpError, _ = (
            _import_google_api()
        )
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
        credentials, _project = google_auth.default(
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build("drive", "v3", credentials=credentials)

    def clean_google_drive_folder(self, folder_id: str) -> None:
        """Delete all files in a Google Drive folder for a clean slate."""
        try:
            service = self.get_drive_service()
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

    def upload_to_google_drive(
        self, file_path: Path, folder_id: str, target_name: str
    ) -> str | None:
        """Upload a file to Google Drive with deduplication support."""
        _, _, _, _, _, HttpError, MediaFileUpload = _import_google_api()
        try:
            service = self.get_drive_service()
        except Exception as e:
            print(f"[Drive Warning] Không thể khởi tạo Google Drive Service: {e}.")
            return None

        try:
            ext = file_path.suffix.lower()
            if ext == ".pdf":
                local_mime = "application/pdf"
                google_mime = "application/pdf"
            elif ext in [".docx", ".doc"]:
                local_mime = (
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                google_mime = "application/vnd.google-apps.document"
            elif ext in [".xlsx", ".xls"]:
                local_mime = (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                google_mime = "application/vnd.google-apps.spreadsheet"
            else:
                local_mime = "application/octet-stream"
                google_mime = None

            # Deduplication check
            name_without_ext = Path(target_name).stem if google_mime else target_name
            q = (
                f"'{folder_id}' in parents and "
                f"(name = '{target_name}' or name = '{name_without_ext}') "
                f"and trashed = false"
            )
            results = (
                service.files().list(q=q, fields="files(id, name, md5Checksum)").execute()
            )
            files = results.get("files", [])

            if files:
                existing_file = files[0]
                existing_id = existing_file["id"]
                existing_md5 = existing_file.get("md5Checksum", "")
                local_md5 = calculate_md5(file_path)

                if existing_md5 == local_md5:
                    print(
                        f"[Drive Deduplicate] Tệp '{target_name}' trùng khớp. Bỏ qua upload."
                    )
                    try:
                        service.permissions().create(
                            fileId=existing_id, body={"type": "anyone", "role": "reader"}
                        ).execute()
                    except Exception as share_err:
                        print(f"[Drive Share Warning] Không thể set public: {share_err}")
                    return str(existing_id)

                # Content changed → overwrite
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

            # New upload
            print(f"[Drive Upload] Đang upload '{target_name}' lên Drive: {folder_id}")
            file_metadata_new: dict[str, Any] = {"name": target_name, "parents": [folder_id]}
            if google_mime:
                file_metadata_new["mimeType"] = google_mime
            media = MediaFileUpload(str(file_path), mimetype=local_mime, resumable=True)
            file = (
                service.files()
                .create(body=file_metadata_new, media_body=media, fields="id")
                .execute()
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

    # -- NotebookLM Cloud Sync (main orchestration) --

    def _auto_discover_url(
        self, doc_key: str, doc_meta: dict[str, Any], registry_data: dict[str, Any]
    ) -> tuple[str | None, bool]:
        """Auto-discover download URL for a document via CDP Google Search.

        Returns:
            Tuple of (discovered_url_or_None, registry_changed_flag).
        """
        search_term = doc_meta.get("title", doc_meta.get("short_name", doc_key))
        short_name = doc_meta.get("short_name", doc_key)
        registry_changed = False

        print(f"[Auto-Discovery] Tự động tìm kiếm link TVPL cho: {search_term}")
        download_url = self.search_thuvienphapluat_via_cdp(search_term)
        if not download_url:
            print(f"[Auto-Discovery] Thử lại tìm kiếm bằng tên ngắn: {short_name}")
            download_url = self.search_thuvienphapluat_via_cdp(short_name)

        if download_url:
            # Update registry data in-place
            for category in ["laws", "decrees", "circulars", "standards"]:
                items = registry_data.get(category, [])
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and item.get("id") == doc_key:
                            if not item.get("download_url"):
                                item["download_url"] = download_url
                                registry_changed = True
                                print(
                                    f"[Registry Auto-Save] Đăng ký download_url cho {doc_key}."
                                )
        return download_url, registry_changed

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
        """Execute the full sync pipeline from local registry to NotebookLM Cloud.

        This is the main orchestration method that:
        1. Reads local legal registry YAML
        2. Queries existing Cloud sources
        3. For each document: downloads, uploads to Drive, syncs to NotebookLM
        4. Cleans up superseded documents from Cloud
        5. Saves updated registry caches
        """
        get_client = _import_notebooklm_client()
        if get_client is None:
            print(
                "[Error] ccba-notebooklm chưa được cài đặt. "
                "Chạy: pip install ccba-legal-intel[cloud]"
            )
            return

        if not registry_path.exists():
            print(f"[Error] Không tìm thấy file registry tại: {registry_path}")
            return

        if clean_drive and use_drive:
            self.clean_google_drive_folder(drive_folder_id)

        # Load registries
        with open(registry_path, encoding="utf-8") as f:
            registry_data = yaml.safe_load(f) or {}

        sources_registry: dict[str, Any] = {}
        if sources_reg_path.exists():
            with open(sources_reg_path, encoding="utf-8") as f:
                sources_registry = yaml.safe_load(f) or {}
        if "sources" not in sources_registry:
            sources_registry["sources"] = {}

        active_cloud_source_ids: set[str] = set()
        registry_changed = False

        async with get_client() as client:
            # Query existing cloud sources
            print("[Cloud State] Đang truy vấn danh sách nguồn trên NotebookLM Cloud...")
            try:
                cloud_sources = await client.sources.list(notebook_id)
                cloud_source_map: dict[str, list[str]] = defaultdict(list)
                for s in cloud_sources:
                    norm_title = (
                        s.title.lower()
                        .replace(".docx", "")
                        .replace(".pdf", "")
                        .replace(".xlsx", "")
                    )
                    cloud_source_map[norm_title].append(s.id)
                print(f"[Cloud State] Phát hiện {len(cloud_sources)} nguồn trên Cloud.")
            except Exception as e:
                print(f"[Error] Không thể đọc danh sách nguồn từ NotebookLM: {e}")
                return

            # Build unified document map
            documents = dict(registry_data.get("documents", {}))
            for category in ["laws", "decrees", "circulars", "standards"]:
                items = registry_data.get(category, [])
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    doc_id = item.get("id")
                    if doc_id:
                        extracted_file_path = ""
                        local_files = item.get("local_files", [])
                        if local_files and isinstance(local_files, list):
                            first_file = local_files[0]
                            if isinstance(first_file, dict):
                                dir_path = first_file.get("path", "")
                                files = first_file.get("files", [])
                                if files and isinstance(files, list):
                                    extracted_file_path = os.path.join(
                                        dir_path, str(files[0])
                                    )
                            elif isinstance(first_file, str):
                                extracted_file_path = first_file

                        documents[doc_id] = {
                            "status": item.get("status", "draft"),
                            "title": item.get("title", doc_id),
                            "short_name": item.get("short_name", doc_id),
                            "file_path": item.get("file_path", extracted_file_path),
                            "download_url": item.get(
                                "download_url", item.get("source_url", "")
                            ),
                        }

            # Process each document
            for doc_key, doc_meta in documents.items():
                status = doc_meta.get("status", "draft")
                file_path_str = doc_meta.get("file_path", "")
                download_url = doc_meta.get("download_url", "")
                short_name = doc_meta.get("short_name", doc_key)

                if not file_path_str:
                    continue

                file_path = Path(file_path_str)
                standard_filename = file_path.name

                # Skip superseded documents
                if status == "superseded":
                    print(f"[Skip] Văn bản hết hiệu lực: {doc_key} ({short_name})")
                    continue

                actual_file_path = file_path
                target_filename = standard_filename
                drive_file_id = None
                is_pdf_flow = False

                # PDF flow (download + Drive upload)
                if download_pdf and use_drive:
                    pdf_filename = file_path.with_suffix(".pdf").name
                    temp_pdf_path = Path(".md/scratch/temp_download.pdf")

                    # Check if PDF already on Drive
                    try:
                        service = self.get_drive_service()
                        q = (
                            f"'{drive_folder_id}' in parents and "
                            f"name = '{pdf_filename}' and trashed = false"
                        )
                        results = (
                            service.files().list(q=q, fields="files(id, name)").execute()
                        )
                        pdf_files = results.get("files", [])
                        if pdf_files:
                            drive_file_id = pdf_files[0]["id"]
                            print(
                                f"[Drive Info] PDF '{pdf_filename}' đã tồn tại. "
                                f"ID: {drive_file_id}"
                            )
                    except Exception as e:
                        print(f"[Drive Warning] Không thể quét PDF trên Drive: {e}")

                    if not drive_file_id:
                        if not download_url:
                            discovered, changed = self._auto_discover_url(
                                doc_key, doc_meta, registry_data
                            )
                            download_url = discovered or ""
                            registry_changed = registry_changed or changed

                        if download_url:
                            print(f"[Download PDF] Tải PDF gốc từ: {download_url}")
                            temp_pdf_path.parent.mkdir(parents=True, exist_ok=True)
                            if temp_pdf_path.exists():
                                try:
                                    os.remove(temp_pdf_path)
                                except Exception:
                                    pass

                            success = self.download_via_cdp_or_client(
                                download_url, temp_pdf_path
                            )
                            if success and temp_pdf_path.exists():
                                drive_file_id = self.upload_to_google_drive(
                                    temp_pdf_path, drive_folder_id, pdf_filename
                                )
                                try:
                                    os.remove(temp_pdf_path)
                                except Exception as e:
                                    print(f"[Warning] Không thể xóa tệp tạm PDF: {e}")
                            else:
                                print("[Warning] Tải PDF thất bại. Fallback sang docx cục bộ...")
                        else:
                            print("[Warning] Không tìm thấy URL PDF. Fallback sang docx cục bộ...")

                    if drive_file_id:
                        is_pdf_flow = True
                        target_filename = pdf_filename

                # Local file flow (or PDF fallback)
                if not is_pdf_flow:
                    if not file_path.exists():
                        print(f"[File Verification] Thiếu file cục bộ cho {doc_key}: {file_path}")
                        if not download_url:
                            discovered, changed = self._auto_discover_url(
                                doc_key, doc_meta, registry_data
                            )
                            download_url = discovered or ""
                            registry_changed = registry_changed or changed

                        if download_url:
                            print(f"[Download] Tải file từ URL: {download_url}")
                            success = self.download_via_cdp_or_client(download_url, file_path)
                            if not success:
                                print(f"[Warning] Vui lòng tải tệp vào: {file_path.resolve()}")
                                continue
                        else:
                            print(f"[Warning] Không có URL. Bổ sung tệp vào: {file_path.resolve()}")
                            continue

                    actual_file_path = file_path
                    target_filename = standard_filename

                    if use_drive:
                        drive_file_id = self.upload_to_google_drive(
                            actual_file_path, drive_folder_id, target_filename
                        )

                # Cache deduplication on Cloud
                local_sha = calculate_sha256(actual_file_path)
                cache_key = str(actual_file_path.resolve()) + ("_pdf" if is_pdf_flow else "")
                cache_info = sources_registry["sources"].get(cache_key, {})
                cached_source_id = cache_info.get("source_id", "")
                cached_sha = cache_info.get("sha256", "")

                norm_target = (
                    target_filename.lower()
                    .replace(".docx", "")
                    .replace(".pdf", "")
                    .replace(".xlsx", "")
                )
                cloud_ids = cloud_source_map.get(norm_target, [])
                cloud_id_by_title = None

                if cached_source_id and cached_source_id in cloud_ids:
                    cloud_id_by_title = cached_source_id
                elif cloud_ids:
                    cloud_id_by_title = cloud_ids[0]

                # Clean duplicate sources
                for extra_id in cloud_ids:
                    if extra_id != cloud_id_by_title:
                        print(f"[Cleanup Duplicate] Xóa nguồn trùng lặp thừa (ID: {extra_id})...")
                        try:
                            await client.sources.delete(notebook_id, extra_id)
                        except Exception:
                            pass

                need_upload = True
                source_id_to_use = ""

                if cloud_id_by_title:
                    if cached_source_id == cloud_id_by_title and cached_sha == local_sha:
                        need_upload = False
                        source_id_to_use = cached_source_id
                        print(f"[Sync Match] '{target_filename}' đã khớp. Bỏ qua.")
                    else:
                        print(f"[Sync Mismatch] Lệch hash/cache cho '{target_filename}'. Gỡ bản cũ...")
                        try:
                            await client.sources.delete(notebook_id, cloud_id_by_title)
                        except Exception:
                            pass

                if need_upload:
                    print(f"[Upload NotebookLM] Đang nạp nguồn: {target_filename}")
                    try:
                        if drive_file_id:
                            try:
                                mime_type = (
                                    "application/pdf"
                                    if is_pdf_flow
                                    else "application/vnd.google-apps.document"
                                )
                                source = await client.sources.add_drive(
                                    notebook_id=notebook_id,
                                    file_id=drive_file_id,
                                    title=target_filename,
                                    mime_type=mime_type,
                                    wait=True,
                                )
                                source_id_to_use = source.id
                                print(
                                    f"[Upload Success] '{target_filename}' qua Drive → "
                                    f"ID: {source_id_to_use}"
                                )
                            except Exception as drive_err:
                                print(f"[Drive RAG Warning] Nạp qua Drive thất bại: {drive_err}")
                                if actual_file_path.exists():
                                    print(f"[Fallback] Nạp trực tiếp: {actual_file_path.name}...")
                                    source = await client.sources.add_file(
                                        notebook_id, str(actual_file_path)
                                    )
                                    source_id_to_use = source.id
                                    print(
                                        f"[Upload Success] '{target_filename}' trực tiếp → "
                                        f"ID: {source_id_to_use}"
                                    )
                                else:
                                    raise drive_err
                        else:
                            source = await client.sources.add_file(
                                notebook_id, str(actual_file_path)
                            )
                            source_id_to_use = source.id
                            print(
                                f"[Upload Success] '{target_filename}' trực tiếp → "
                                f"ID: {source_id_to_use}"
                            )
                    except Exception as e:
                        print(f"[Error] Nạp nguồn thất bại '{target_filename}': {e}")
                        continue

                # Save cache
                sources_registry["sources"][cache_key] = {
                    "source_id": source_id_to_use,
                    "sha256": local_sha,
                    "drive_file_id": drive_file_id,
                }
                active_cloud_source_ids.add(source_id_to_use)

            # Cleanup superseded/deleted sources from Cloud
            print("[Cloud Cleanup] Kiểm tra dọn dẹp nguồn hết hiệu lực trên Cloud...")
            for s_title, s_ids in cloud_source_map.items():
                for s_id in s_ids:
                    if s_id not in active_cloud_source_ids:
                        is_superseded_or_deleted = True
                        for _doc_key, doc_meta in documents.items():
                            doc_status = doc_meta.get("status", "draft")
                            doc_fp = doc_meta.get("file_path", "")
                            if doc_fp:
                                std_stem = Path(doc_fp).stem
                                s_title_stem = Path(s_title).stem
                                if std_stem == s_title_stem and doc_status != "superseded":
                                    is_superseded_or_deleted = False
                                    break
                        if is_superseded_or_deleted:
                            print(f"[Cleanup] Xóa nguồn hết hiệu lực: {s_title} (ID: {s_id})")
                            try:
                                await client.sources.delete(notebook_id, s_id)
                            except Exception as e:
                                print(f"[Cleanup Error] Không thể xóa source {s_id}: {e}")

            # Save registries
            with open(sources_reg_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(sources_registry, f, allow_unicode=True)
            print("[Registry Update] Đã cập nhật sources_registry.yaml")

            if registry_changed:
                with open(registry_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(registry_data, f, allow_unicode=True, sort_keys=False)
                print(f"[Registry Auto-Save] Đã ghi đè download_url mới vào: {registry_path}")
