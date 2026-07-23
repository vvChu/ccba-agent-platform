"""Script cầu nối tự động đồng bộ pháp lý (Legal Auto-Sync Pipeline) cho CCBA.

Đồng bộ các văn bản pháp lý cục bộ lên Google NotebookLM Cloud RAG,
hỗ trợ tải file thông qua Chrome CDP (ccba-legal-intel) và lưu trữ tập trung trên Google Drive.
Tạo bởi CCBA.
"""

import argparse
import asyncio
import hashlib
import os
import socket
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

import yaml  # type: ignore

# Thêm path để import ccba_legal và notebooklm_helper

try:
    from ccba_legal import ChromeCDP, LegalIntelPipeline, trigger_download  # type: ignore
except ImportError:
    LegalIntelPipeline = None
    ChromeCDP = None
    trigger_download = None

try:
    import google.auth
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build  # type: ignore
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

import notebooklm_helper

DEFAULT_DRIVE_FOLDER = "1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2"


def calculate_md5(file_path: Path) -> str:
    """Tính mã MD5 hash của tệp tin để so khớp Google Drive."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def calculate_sha256(file_path: Path) -> str:
    """Tính mã SHA-256 hash của tệp tin để làm cache đối soát."""
    hash_sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()


def is_port_open(port: int) -> bool:
    """Kiểm tra xem cổng port có đang mở và lắng nghe không."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def ensure_chrome_debug_port() -> bool:
    """Tự động phát hiện và khởi chạy Google Chrome ở chế độ debug port 9222 nếu chưa bật."""
    if is_port_open(9222):
        return True

    print(
        "[Chrome Debug] Phát hiện cổng 9222 chưa hoạt động. Đang tự động khởi chạy Google Chrome..."
    )
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
        print(
            "[Chrome Debug Warning] Không tìm thấy đường dẫn cài đặt Google Chrome trên hệ thống."
        )
        return False

    try:
        # Khởi chạy Chrome ở chế độ debug
        # Chúng ta dùng user-data-dir riêng biệt để tránh xung đột với cửa sổ Chrome đang chạy bình thường của user
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

        # Chạy nền không chặn script
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Đợi tối đa 5 giây cho Chrome khởi động
        for _ in range(10):
            time.sleep(0.5)
            if is_port_open(9222):
                print(
                    "[Chrome Debug Success] Đã khởi chạy Google Chrome ở debug port 9222 thành công!"
                )
                return True

        print("[Chrome Debug Warning] Đã khởi chạy Chrome nhưng cổng 9222 vẫn không phản hồi.")
        return False
    except Exception as e:
        print(f"[Chrome Debug Error] Lỗi tự động khởi chạy Chrome: {e}")
        return False


def search_thuvienphapluat_via_cdp(query: str) -> str | None:
    """Tự động tìm kiếm link văn bản trên thuvienphapluat.vn thông qua Google Search bằng Chrome CDP."""
    if ChromeCDP is None:
        return None

    if not ensure_chrome_debug_port():
        print(
            "[Auto-Discovery Warning] Không thể kích hoạt hoặc kết nối tới cổng debug Chrome. Bỏ qua Auto-Discovery."
        )
        return None

    print(f"[Auto-Discovery] Đang tìm kiếm link Thư viện Pháp luật cho: {query}")
    try:
        cdp = ChromeCDP(port=9222)
        pages = cdp.get_pages()
        if not pages:
            print("[Auto-Discovery Warning] Không tìm thấy tab Chrome nào đang mở để kết nối CDP.")
            return None

        cdp.connect_tab(pages[0]["webSocketDebuggerUrl"])

        search_query = f'site:thuvienphapluat.vn "{query}"'
        search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"

        cdp.navigate(search_url)
        cdp.wait_ready()
        cdp.handle_cloudflare()

        # Chạy JS trích xuất link thuvienphapluat.vn/van-ban/ đầu tiên
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
            # Loại bỏ query params và hash
            link_clean = link.split("?")[0].split("#")[0]
            print(f"[Auto-Discovery Success] Tìm thấy liên kết: {link_clean}")
            return str(link_clean)

        print("[Auto-Discovery Info] Không tìm thấy link Thư viện Pháp luật trên Google.")
        return None
    except Exception as e:
        print(f"[Auto-Discovery Warning] Lỗi tìm kiếm Google CDP: {e}")
        return None


def download_via_cdp_or_client(url: str, dest_path: Path) -> bool:
    """Tải tệp tin tự động sử dụng Chrome CDP (ccba-legal-intel) hoặc client urllib."""
    # 1. Thử tải bằng Chrome CDP
    if ChromeCDP is not None and trigger_download is not None:
        try:
            ensure_chrome_debug_port()
            print(f"[CDP] Thử kết nối Chrome CDP trên port 9222 để tải: {url}")
            cdp = ChromeCDP(port=9222)
            pages = cdp.get_pages()
            if pages:
                # Lấy page đầu tiên đang mở
                cdp.connect_tab(pages[0]["webSocketDebuggerUrl"])
                cdp.navigate(url)
                cdp.wait_ready()
                cdp.handle_cloudflare()

                # trigger_download sẽ tải về và rename vào dest_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                success = trigger_download(cdp, dest_path.parent, dest_path.stem)
                if success:
                    print(f"[CDP] Tải file thành công: {dest_path.name}")
                    return True
        except Exception as e:
            print(f"[CDP Warning] Lỗi kết nối hoặc thực thi Chrome CDP: {e}")
            print("[CDP Warning] Thử fallback sang client tải trực tiếp...")

    # 2. Tải bằng client urllib thông thường
    try:
        import urllib.request

        print(f"[Urllib] Tải trực tiếp từ URL: {url}")
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response, open(dest_path, "wb") as out_file:
            out_file.write(response.read())
        print(f"[Urllib] Tải file thành công: {dest_path.name}")
        return True
    except Exception as e:
        print(f"[Error] Tải file từ internet thất bại: {e}")
        return False


def get_drive_service() -> Any:
    """Khởi tạo Drive API service sử dụng token cá nhân hoặc Application Default Credentials (ADC)."""
    if not GOOGLE_API_AVAILABLE:
        raise ImportError("Thiếu thư viện googleapiclient hoặc google-auth. Vui lòng cài đặt.")

    # 1. Thử nạp token cá nhân nếu có
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
                import shutil

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
                # Lưu lại token đã làm mới
                with open(token_path, "w", encoding="utf-8") as f:
                    f.write(credentials.to_json())
            return build("drive", "v3", credentials=credentials)
        except Exception as e:
            print(f"[Drive Warning] Lỗi nạp token cá nhân: {e}")
            print("[Drive Info] Thử fallback sang kiểm tra ADC mặc định...")

    # 2. Fallback sang ADC
    credentials, project = google.auth.default(scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=credentials)


def clean_google_drive_folder(folder_id: str) -> None:
    """Xóa sạch tất cả các tệp tin hiện tại trong thư mục Google Drive chung để làm sạch từ đầu."""
    try:
        service = get_drive_service()
        print(
            f"[Drive Cleanup] Đang truy vấn danh sách tệp tin trong thư mục Drive: {folder_id}..."
        )
        q = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(q=q, fields="files(id, name)").execute()
        files = results.get("files", [])
        if not files:
            print("[Drive Cleanup Info] Thư mục Drive đã sạch sẽ.")
            return

        print(f"[Drive Cleanup Info] Phát hiện {len(files)} tệp tin. Tiến hành xóa sạch...")
        for f in files:
            print(
                f"[Drive Cleanup Action] Đang xóa tệp trên Drive: '{f['name']}' (ID: {f['id']})..."
            )
            try:
                service.files().delete(fileId=f["id"]).execute()
            except Exception as del_err:
                print(f"[Drive Cleanup Warning] Không thể xóa tệp {f['id']}: {del_err}")
        print("[Drive Cleanup Success] Đã làm sạch thư mục Google Drive chung!")
    except Exception as e:
        print(f"[Drive Cleanup Warning] Lỗi khi dọn dẹp thư mục Drive: {e}")


def upload_to_google_drive(file_path: Path, folder_id: str, target_name: str) -> str | None:
    """Tải tệp tin lên Google Drive chung, hỗ trợ chống trùng lặp (Deduplication)."""
    try:
        service = get_drive_service()
    except Exception as e:
        print(
            f"[Drive Warning] Không thể khởi tạo Google Drive Service: {e}. Fallback sang nạp cục bộ..."
        )
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

        # Quét kiểm tra trùng lặp trên Drive
        # Nếu tệp được chuyển đổi định dạng, Google Drive sẽ tự động cắt phần mở rộng (.docx, .xlsx)
        # Vì vậy, khi quét trùng lặp phải tìm kiếm cả tên gốc và tên sau khi cắt phần mở rộng.
        name_without_ext = Path(target_name).stem if google_mime else target_name
        q = f"'{folder_id}' in parents and (name = '{target_name}' or name = '{name_without_ext}') and trashed = false"
        results = service.files().list(q=q, fields="files(id, name, md5Checksum)").execute()
        files = results.get("files", [])

        if files:
            existing_file = files[0]
            existing_id = existing_file["id"]
            existing_md5 = existing_file.get("md5Checksum", "")
            local_md5 = calculate_md5(file_path)

            if existing_md5 == local_md5:
                print(
                    f"[Drive Deduplicate] Tệp '{target_name}' đã tồn tại trên Drive với nội dung trùng khớp. Bỏ qua upload."
                )
                try:
                    service.permissions().create(
                        fileId=existing_id, body={"type": "anyone", "role": "reader"}
                    ).execute()
                except Exception as share_err:
                    print(f"[Drive Share Warning] Không thể set public cho file: {share_err}")
                return str(existing_id)

            # Khác nội dung ➔ cập nhật đè lên tệp cũ
            print(
                f"[Drive Update] Tệp '{target_name}' đã thay đổi nội dung. Thực hiện ghi đè lên file_id: {existing_id}"
            )
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
                print(f"[Drive Share Warning] Không thể set public cho file: {share_err}")
            return str(file_id)

        # Chưa có tệp ➔ upload mới
        print(f"[Drive Upload] Đang upload tệp '{target_name}' lên thư mục Drive: {folder_id}")
        file_metadata_new: dict[str, Any] = {"name": target_name, "parents": [folder_id]}
        if google_mime:
            file_metadata_new["mimeType"] = google_mime
        media = MediaFileUpload(str(file_path), mimetype=local_mime, resumable=True)
        file = service.files().create(body=file_metadata_new, media_body=media, fields="id").execute()
        file_id = file.get("id")
        try:
            service.permissions().create(
                fileId=file_id, body={"type": "anyone", "role": "reader"}
            ).execute()
        except Exception as share_err:
            print(f"[Drive Share Warning] Không thể set public cho file: {share_err}")
        return str(file_id)

    except HttpError as e:
        if e.resp.status == 403:
            print("\n[Drive Error 403] Lỗi Forbidden chi tiết từ Google:")
            try:
                import json

                err_data = json.loads(e.content.decode("utf-8"))
                print(json.dumps(err_data, indent=2, ensure_ascii=False))
            except Exception:
                print(e.content.decode("utf-8") if e.content else e)
            print("Tự động fallback sang luồng nạp file trực tiếp lên NotebookLM Cloud...\n")
        else:
            print(f"[Drive Warning] Lỗi gọi API Google Drive: {e}")
        return None
    except Exception as e:
        print(f"[Drive Warning] Lỗi tải tệp lên Drive: {e}")
        return None


async def sync_registry_to_notebooklm(
    registry_path: Path,
    sources_reg_path: Path,
    notebook_id: str,
    use_drive: bool,
    drive_folder_id: str,
    download_pdf: bool = False,
    clean_drive: bool = False,
) -> None:
    """Thực hiện toàn trình luồng đồng bộ từ Registry cục bộ lên Cloud."""
    if not registry_path.exists():
        print(f"[Error] Không tìm thấy file registry pháp lý tại: {registry_path}")
        return

    if clean_drive and use_drive:
        clean_google_drive_folder(drive_folder_id)

    # Load legal_registry.yaml
    with open(registry_path, encoding="utf-8") as f:
        registry_data = yaml.safe_load(f) or {}

    # Load sources_registry.yaml
    sources_registry: dict[str, Any] = {}
    if sources_reg_path.exists():
        with open(sources_reg_path, encoding="utf-8") as f:
            sources_registry = yaml.safe_load(f) or {}

    if "sources" not in sources_registry:
        sources_registry["sources"] = {}

    active_cloud_source_ids: set[str] = set()
    registry_changed = False

    async with notebooklm_helper.get_client() as client:
        # Lấy danh sách nguồn thực tế trên Cloud
        print("[Cloud State] Đang truy vấn danh sách nguồn thực tế trên NotebookLM Cloud...")
        try:
            cloud_sources = await client.sources.list(notebook_id)
            from collections import defaultdict

            cloud_source_map = defaultdict(list)
            for s in cloud_sources:
                norm_title = (
                    s.title.lower().replace(".docx", "").replace(".pdf", "").replace(".xlsx", "")
                )
                cloud_source_map[norm_title].append(s.id)
            print(f"[Cloud State] Phát hiện {len(cloud_sources)} nguồn đang tồn tại trên Cloud.")
        except Exception as e:
            print(f"[Error] Không thể kết nối hoặc đọc danh sách nguồn từ NotebookLM: {e}")
            return

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
                                extracted_file_path = os.path.join(dir_path, str(files[0]))
                        elif isinstance(first_file, str):
                            extracted_file_path = first_file

                    documents[doc_id] = {
                        "status": item.get("status", "draft"),
                        "title": item.get("title", doc_id),
                        "short_name": item.get("short_name", doc_id),
                        "file_path": item.get("file_path", extracted_file_path),
                        "download_url": item.get("download_url", item.get("source_url", "")),
                    }

        for doc_key, doc_meta in documents.items():
            status = doc_meta.get("status", "draft")
            file_path_str = doc_meta.get("file_path", "")
            download_url = doc_meta.get("download_url", "")
            short_name = doc_meta.get("short_name", doc_key)

            if not file_path_str:
                continue

            file_path = Path(file_path_str)
            standard_filename = file_path.name

            # 1. Nếu văn bản đã hết hiệu lực (superseded) ➔ Bỏ qua hoặc chuẩn bị xóa khỏi Cloud
            if status == "superseded":
                print(f"[Skip] Văn bản hết hiệu lực: {doc_key} ({short_name})")
                continue

            actual_file_path = file_path
            target_filename = standard_filename
            drive_file_id = None
            is_pdf_flow = False

            # 2. Xử lý luồng tải PDF gốc tạm thời (nếu được kích hoạt và sử dụng Drive)
            if download_pdf and use_drive:
                pdf_filename = file_path.with_suffix(".pdf").name
                temp_pdf_path = Path(".md/scratch/temp_download.pdf")

                # Quét kiểm tra xem file PDF đã có trên Drive chưa
                try:
                    service = get_drive_service()
                    q = f"'{drive_folder_id}' in parents and name = '{pdf_filename}' and trashed = false"
                    results = service.files().list(q=q, fields="files(id, name)").execute()
                    files = results.get("files", [])
                    if files:
                        drive_file_id = files[0]["id"]
                        print(
                            f"[Drive Info] Tệp PDF '{pdf_filename}' đã tồn tại trên Drive. Sử dụng file_id: {drive_file_id}"
                        )
                except Exception as e:
                    print(f"[Drive Warning] Không thể quét tìm PDF trên Drive: {e}")

                if not drive_file_id:
                    # Chưa có trên Drive ➔ Tiến hành tìm kiếm tự động nếu thiếu download_url
                    if not download_url:
                        search_term = doc_meta.get("title", short_name)
                        print(
                            f"[Auto-Discovery] Không có download_url. Đang tự động tìm kiếm link Thư viện Pháp luật cho: {search_term}"
                        )
                        download_url = search_thuvienphapluat_via_cdp(search_term)
                        if not download_url:
                            # Fallback search theo short_name
                            print(f"[Auto-Discovery] Thử lại tìm kiếm bằng tên ngắn: {short_name}")
                            download_url = search_thuvienphapluat_via_cdp(short_name)

                        if download_url:
                            # Cập nhật ngược lại registry_data
                            for category in ["laws", "decrees", "circulars", "standards"]:
                                items = registry_data.get(category, [])
                                if isinstance(items, list):
                                    for item in items:
                                        if isinstance(item, dict) and item.get("id") == doc_key:
                                            if not item.get("download_url"):
                                                item["download_url"] = download_url
                                                registry_changed = True
                                                print(
                                                    f"[Registry Auto-Save] Đăng ký download_url động cho {doc_key} trong registry cache."
                                                )

                    # Tiến hành tải tạm và upload
                    if download_url:
                        print(f"[Download PDF] Đang tải bản PDF gốc tạm thời từ: {download_url}")
                        temp_pdf_path.parent.mkdir(parents=True, exist_ok=True)
                        if temp_pdf_path.exists():
                            try:
                                os.remove(temp_pdf_path)
                            except Exception:
                                pass

                        success = download_via_cdp_or_client(download_url, temp_pdf_path)
                        if success and temp_pdf_path.exists():
                            # Upload lên Drive
                            print(
                                f"[Drive Upload] Đang upload tệp PDF '{pdf_filename}' lên Drive..."
                            )
                            drive_file_id = upload_to_google_drive(
                                temp_pdf_path, drive_folder_id, pdf_filename
                            )
                            # Xóa file tạm cục bộ ngay lập tức
                            try:
                                os.remove(temp_pdf_path)
                            except Exception as e:
                                print(f"[Warning] Không thể xóa tệp tạm PDF local: {e}")
                        else:
                            print(
                                "[Warning] Tải tệp PDF thất bại. Tự động fallback sang nạp file docx cục bộ..."
                            )
                    else:
                        print(
                            "[Warning] Không tìm thấy URL tải bản PDF qua Auto-Discovery. Tự động fallback sang nạp file docx cục bộ..."
                        )

                if drive_file_id:
                    is_pdf_flow = True
                    target_filename = pdf_filename

            # 3. Luồng nạp docx/tệp gốc cục bộ (hoặc khi nạp PDF thất bại/tắt)
            if not is_pdf_flow:
                # Kiểm tra file cục bộ
                if not file_path.exists():
                    print(
                        f"[File Verification] Thiếu file cục bộ cho {doc_key}. Đường dẫn khai báo: {file_path}"
                    )
                    if not download_url:
                        search_term = doc_meta.get("title", short_name)
                        print(
                            f"[Auto-Discovery] Thiếu file và không có download_url. Đang tự động tìm kiếm link Thư viện Pháp luật cho: {search_term}"
                        )
                        download_url = search_thuvienphapluat_via_cdp(search_term)
                        if not download_url:
                            # Fallback search theo short_name
                            print(f"[Auto-Discovery] Thử lại tìm kiếm bằng tên ngắn: {short_name}")
                            download_url = search_thuvienphapluat_via_cdp(short_name)

                        if download_url:
                            # Cập nhật ngược lại registry_data
                            for category in ["laws", "decrees", "circulars", "standards"]:
                                items = registry_data.get(category, [])
                                if isinstance(items, list):
                                    for item in items:
                                        if isinstance(item, dict) and item.get("id") == doc_key:
                                            if not item.get("download_url"):
                                                item["download_url"] = download_url
                                                registry_changed = True
                                                print(
                                                    f"[Registry Auto-Save] Đăng ký download_url động cho {doc_key} trong registry cache."
                                                )

                    if download_url:
                        print(f"[Download] Đang tự động tải file từ URL: {download_url}")
                        success = download_via_cdp_or_client(download_url, file_path)
                        if not success:
                            print(
                                f"[Warning] Vui lòng tự tải tệp tin và lưu vào: {file_path.resolve()}"
                            )
                            continue
                    else:
                        print(
                            f"[Warning] Không có URL tải. Vui lòng bổ sung tệp tin vào: {file_path.resolve()}"
                        )
                        continue

                actual_file_path = file_path
                target_filename = standard_filename

                if use_drive:
                    drive_file_id = upload_to_google_drive(
                        actual_file_path, drive_folder_id, target_filename
                    )

            # Tính SHA-256 local
            local_sha = calculate_sha256(actual_file_path)

            # 4. Kiểm định trùng lặp trên Cloud (Self-healing & Deduplicate)
            cache_key = str(actual_file_path.resolve()) + ("_pdf" if is_pdf_flow else "")
            cache_info = sources_registry["sources"].get(cache_key, {})
            cached_source_id = cache_info.get("source_id", "")
            cached_sha = cache_info.get("sha256", "")

            # Lấy danh sách ID trùng tên trên Cloud
            norm_target = (
                target_filename.lower()
                .replace(".docx", "")
                .replace(".pdf", "")
                .replace(".xlsx", "")
            )
            cloud_ids = cloud_source_map.get(norm_target, [])
            cloud_id_by_title = None

            # Ưu tiên khớp ID đã cache
            if cached_source_id and cached_source_id in cloud_ids:
                cloud_id_by_title = cached_source_id
            elif cloud_ids:
                cloud_id_by_title = cloud_ids[0]

            # Xóa các bản trùng lặp thừa (nếu có)
            for extra_id in cloud_ids:
                if extra_id != cloud_id_by_title:
                    print(
                        f"[Cleanup Duplicate] Phát hiện nguồn trùng lặp thừa trên Cloud cho '{target_filename}'. Tiến hành xóa (ID: {extra_id})..."
                    )
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
                    print(
                        f"[Sync Match] Nguồn '{target_filename}' đã đồng bộ khớp hoàn toàn. Bỏ qua."
                    )
                else:
                    # Trùng tên trên Cloud nhưng lệch hash hoặc cache ➔ Xóa nguồn cũ trên Cloud để nạp bản mới
                    print(
                        f"[Sync Mismatch] Phát hiện lệch hash/cache cho '{target_filename}'. Đang gỡ bản cũ trên Cloud..."
                    )
                    try:
                        await client.sources.delete(notebook_id, cloud_id_by_title)
                    except Exception:
                        pass

            if need_upload:
                print(f"[Upload NotebookLM] Đang nạp nguồn: {target_filename}")
                try:
                    if drive_file_id:
                        try:
                            # Thử nạp qua Google Drive trước
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
                                f"[Upload Success] Đã nạp nguồn '{target_filename}' qua Google Drive ➔ ID: {source_id_to_use}"
                            )
                        except Exception as drive_err:
                            print(f"[Drive RAG Warning] Nạp nguồn qua Drive thất bại: {drive_err}")
                            if actual_file_path.exists():
                                print(
                                    f"[Drive RAG Fallback] Thử fallback nạp trực tiếp file cục bộ: {actual_file_path.name}..."
                                )
                                source = await client.sources.add_file(
                                    notebook_id, str(actual_file_path)
                                )
                                source_id_to_use = source.id
                                print(
                                    f"[Upload Success] Đã nạp nguồn '{target_filename}' trực tiếp thành công ➔ ID: {source_id_to_use}"
                                )
                            else:
                                raise drive_err
                    else:
                        # Nạp trực tiếp file local
                        source = await client.sources.add_file(notebook_id, str(actual_file_path))
                        source_id_to_use = source.id
                        print(
                            f"[Upload Success] Đã nạp nguồn '{target_filename}' trực tiếp thành công ➔ ID: {source_id_to_use}"
                        )
                except Exception as e:
                    print(f"[Error] Nạp nguồn thất bại hoàn toàn '{target_filename}': {e}")
                    continue

            # Lưu lại thông tin cache
            sources_registry["sources"][cache_key] = {
                "source_id": source_id_to_use,
                "sha256": local_sha,
                "drive_file_id": drive_file_id,
            }
            active_cloud_source_ids.add(source_id_to_use)

        # 5. Dọn dẹp các tệp superseded hoặc bị xóa khỏi registry trên Cloud
        print("[Cloud Cleanup] Đang kiểm tra dọn dẹp các nguồn hết hiệu lực trên Cloud...")
        for s_title, s_ids in cloud_source_map.items():
            for s_id in s_ids:
                if s_id not in active_cloud_source_ids:
                    # Kiểm tra xem đây có phải là văn bản superseded trong registry không
                    # Hoặc tệp tin không còn được đăng ký
                    is_superseded_or_deleted = True

                    # Quét đối chiếu ngược
                    for _doc_key, doc_meta in documents.items():
                        status = doc_meta.get("status", "draft")
                        file_path_str = doc_meta.get("file_path", "")
                        if file_path_str:
                            # So sánh phần thân tên tệp (stem) để hỗ trợ cả docx lẫn pdf
                            std_name_stem = Path(file_path_str).stem
                            s_title_stem = Path(s_title).stem
                            if std_name_stem == s_title_stem and status != "superseded":
                                is_superseded_or_deleted = False
                                break

                    if is_superseded_or_deleted:
                        print(
                            f"[Cleanup] Xóa nguồn hết hiệu lực khỏi Cloud: {s_title} (ID: {s_id})"
                        )
                        try:
                            await client.sources.delete(notebook_id, s_id)
                        except Exception as e:
                            print(f"[Cleanup Error] Không thể xóa source {s_id}: {e}")

        # Ghi lại tệp registry sources
        with open(sources_reg_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(sources_registry, f, allow_unicode=True)
        print("[Registry Update] Đã cập nhật tệp sources_registry.yaml")

        if registry_changed:
            with open(registry_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(registry_data, f, allow_unicode=True, sort_keys=False)
            print(
                f"[Registry Auto-Save] Đã ghi đè cập nhật download_url mới vào file: {registry_path}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tự động đồng bộ pháp lý (Legal Auto-Sync Pipeline) cho CCBA"
    )
    parser.add_argument(
        "--registry",
        default=".md/data/legal_registry.yaml",
        help="Đường dẫn file registry pháp lý cục bộ",
    )
    parser.add_argument(
        "--sources-registry",
        default=".md/data/sources_registry.yaml",
        help="Đường dẫn file registry ánh xạ source NotebookLM",
    )
    parser.add_argument(
        "--notebook-id", required=True, help="ID của Google NotebookLM Notebook đích"
    )
    parser.add_argument(
        "--use-drive", action="store_true", help="Kích hoạt luồng nạp gián tiếp qua Google Drive"
    )
    parser.add_argument(
        "--drive-folder",
        default=DEFAULT_DRIVE_FOLDER,
        help="ID thư mục Google Drive chung mục tiêu",
    )
    parser.add_argument(
        "--download-pdf",
        action="store_true",
        help="Tải bản PDF gốc tạm thời và upload lên Google Drive chung",
    )
    parser.add_argument(
        "--clean-drive",
        action="store_true",
        help="Làm sạch toàn bộ tệp tin trong thư mục Google Drive chung trước khi đồng bộ",
    )

    args = parser.parse_args()

    # Đọc cấu hình từ environment nếu có
    notebook_id = args.notebook_id or os.environ.get("NOTEBOOKLM_NOTEBOOK_ID")
    if not notebook_id:
        print(
            "[Error] Thiếu Notebook ID. Vui lòng cung cấp qua tham số --notebook-id hoặc biến môi trường NOTEBOOKLM_NOTEBOOK_ID."
        )
        sys.exit(1)

    registry_path = Path(args.registry)
    sources_reg_path = Path(args.sources_registry)

    asyncio.run(
        sync_registry_to_notebooklm(
            registry_path=registry_path,
            sources_reg_path=sources_reg_path,
            notebook_id=notebook_id,
            use_drive=args.use_drive,
            drive_folder_id=args.drive_folder,
            download_pdf=args.download_pdf,
            clean_drive=args.clean_drive,
        )
    )


if __name__ == "__main__":
    main()
