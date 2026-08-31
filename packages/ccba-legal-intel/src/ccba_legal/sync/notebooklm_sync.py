"""NotebookLM Cloud Synchronization Orchestrator."""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.sync.cdp_discovery import download_via_cdp_or_client, search_thuvienphapluat_via_cdp
from ccba_legal.sync.drive_uploader import (
    clean_google_drive_folder,
    get_drive_service,
    upload_to_google_drive,
)
from ccba_legal.sync.utils import calculate_sha256


def _import_notebooklm_client() -> Any:
    """Lazy import ccba_notebooklm.get_client (optional [cloud] dependency)."""
    try:
        from ccba_notebooklm import get_client
        return get_client
    except ImportError:
        return None


def auto_discover_doc_url(
    doc_key: str, doc_meta: dict[str, Any], registry_data: dict[str, Any]
) -> tuple[str | None, bool]:
    """Auto-discover download URL for a document via CDP Google Search."""
    search_term = doc_meta.get("title", doc_meta.get("short_name", doc_key))
    short_name = doc_meta.get("short_name", doc_key)
    registry_changed = False

    print(f"[Auto-Discovery] Tự động tìm kiếm link TVPL cho: {search_term}")
    download_url = search_thuvienphapluat_via_cdp(search_term)
    if not download_url:
        print(f"[Auto-Discovery] Thử lại tìm kiếm bằng tên ngắn: {short_name}")
        download_url = search_thuvienphapluat_via_cdp(short_name)

    if download_url:
        for category in ["laws", "decrees", "circulars", "standards"]:
            items = registry_data.get(category, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and item.get("id") == doc_key:
                        if not item.get("download_url"):
                            item["download_url"] = download_url
                            registry_changed = True
                            print(f"[Registry Auto-Save] Đăng ký download_url cho {doc_key}.")
    return download_url, registry_changed


async def sync_registry_to_notebooklm(
    registry_path: Path,
    sources_reg_path: Path,
    notebook_id: str,
    use_drive: bool,
    drive_folder_id: str,
    download_pdf: bool = False,
    clean_drive: bool = False,
) -> None:
    """Execute the full sync pipeline from local registry to NotebookLM Cloud."""
    get_client = _import_notebooklm_client()
    if get_client is None:
        print("[Error] ccba-notebooklm chưa được cài đặt. Chạy: pip install ccba-legal-intel[cloud]")
        return

    if not registry_path.exists():
        print(f"[Error] Không tìm thấy file registry tại: {registry_path}")
        return

    if clean_drive and use_drive:
        clean_google_drive_folder(drive_folder_id)

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

            if status == "superseded":
                print(f"[Skip] Văn bản hết hiệu lực: {doc_key} ({short_name})")
                continue

            actual_file_path = file_path
            target_filename = standard_filename
            drive_file_id = None
            is_pdf_flow = False

            if download_pdf and use_drive:
                pdf_filename = file_path.with_suffix(".pdf").name
                temp_pdf_path = Path(".md/scratch/temp_download.pdf")

                try:
                    service = get_drive_service()
                    q = f"'{drive_folder_id}' in parents and name = '{pdf_filename}' and trashed = false"
                    results = service.files().list(q=q, fields="files(id, name)").execute()
                    pdf_files = results.get("files", [])
                    if pdf_files:
                        drive_file_id = pdf_files[0]["id"]
                        print(f"[Drive Info] PDF '{pdf_filename}' đã tồn tại. ID: {drive_file_id}")
                except Exception as e:
                    print(f"[Drive Warning] Không thể quét PDF trên Drive: {e}")

                if not drive_file_id:
                    if not download_url:
                        discovered, changed = auto_discover_doc_url(doc_key, doc_meta, registry_data)
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

                        success = download_via_cdp_or_client(download_url, temp_pdf_path)
                        if success and temp_pdf_path.exists():
                            drive_file_id = upload_to_google_drive(temp_pdf_path, drive_folder_id, pdf_filename)
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

            if not is_pdf_flow:
                if not file_path.exists():
                    print(f"[File Verification] Thiếu file cục bộ cho {doc_key}: {file_path}")
                    if not download_url:
                        discovered, changed = auto_discover_doc_url(doc_key, doc_meta, registry_data)
                        download_url = discovered or ""
                        registry_changed = registry_changed or changed

                    if download_url:
                        print(f"[Download] Tải file từ URL: {download_url}")
                        success = download_via_cdp_or_client(download_url, file_path)
                        if not success:
                            print(f"[Warning] Vui lòng tải tệp vào: {file_path.resolve()}")
                            continue
                    else:
                        print(f"[Warning] Không có URL. Bổ sung tệp vào: {file_path.resolve()}")
                        continue

                actual_file_path = file_path
                target_filename = standard_filename

                if use_drive:
                    drive_file_id = upload_to_google_drive(actual_file_path, drive_folder_id, target_filename)

            local_sha = calculate_sha256(actual_file_path)
            cache_key = str(actual_file_path.resolve()) + ("_pdf" if is_pdf_flow else "")
            cache_info = sources_registry["sources"].get(cache_key, {})
            cached_source_id = cache_info.get("source_id", "")
            cached_sha = cache_info.get("sha256", "")

            norm_target = target_filename.lower().replace(".docx", "").replace(".pdf", "").replace(".xlsx", "")
            cloud_ids = cloud_source_map.get(norm_target, [])
            cloud_id_by_title = None

            if cached_source_id and cached_source_id in cloud_ids:
                cloud_id_by_title = cached_source_id
            elif cloud_ids:
                cloud_id_by_title = cloud_ids[0]

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
                            mime_type = "application/pdf" if is_pdf_flow else "application/vnd.google-apps.document"
                            source = await client.sources.add_drive(
                                notebook_id=notebook_id,
                                file_id=drive_file_id,
                                title=target_filename,
                                mime_type=mime_type,
                                wait=True,
                            )
                            source_id_to_use = source.id
                            print(f"[Upload Success] '{target_filename}' qua Drive → ID: {source_id_to_use}")
                        except Exception as drive_err:
                            print(f"[Drive RAG Warning] Nạp qua Drive thất bại: {drive_err}")
                            if actual_file_path.exists():
                                print(f"[Fallback] Nạp trực tiếp: {actual_file_path.name}...")
                                source = await client.sources.add_file(notebook_id, str(actual_file_path))
                                source_id_to_use = source.id
                                print(f"[Upload Success] '{target_filename}' trực tiếp → ID: {source_id_to_use}")
                            else:
                                raise drive_err
                    else:
                        source = await client.sources.add_file(notebook_id, str(actual_file_path))
                        source_id_to_use = source.id
                        print(f"[Upload Success] '{target_filename}' trực tiếp → ID: {source_id_to_use}")
                except Exception as e:
                    print(f"[Error] Nạp nguồn thất bại '{target_filename}': {e}")
                    continue

            sources_registry["sources"][cache_key] = {
                "source_id": source_id_to_use,
                "sha256": local_sha,
                "drive_file_id": drive_file_id,
            }
            active_cloud_source_ids.add(source_id_to_use)

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

        with open(sources_reg_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(sources_registry, f, allow_unicode=True)
        print("[Registry Update] Đã cập nhật sources_registry.yaml")

        if registry_changed:
            with open(registry_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(registry_data, f, allow_unicode=True, sort_keys=False)
            print(f"[Registry Auto-Save] Đã ghi đè download_url mới vào: {registry_path}")
