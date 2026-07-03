import asyncio
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore

from ._client import (
    HAS_NOTEBOOKLM,
    NetworkError,
    get_client,
)
from ._gc import check_quota_and_warn
from ._registry import (
    REGISTRY_FILE,
    clear_task_state,
    get_file_sha256,
    get_notebook_id_from_context,
    normalize_to_relative,
    read_registry,
    read_task_state,
    save_notebook_id_to_context,
    save_task_state,
    update_registry,
)
from ._security import run_maskara_gate


def run_docs_validator(file_path: str) -> None:
    """Chạy docs-validator để kiểm định chất lượng tài liệu."""
    candidates = [
        Path("scripts/validate_docs.py"),
        Path(__file__).parents[4] / "scripts" / "validate_docs.py",
        Path(__file__).parents[3] / "scripts" / "validate_docs.py",
    ]
    val_path = None
    for cand in candidates:
        if cand.exists():
            val_path = cand
            break

    if not val_path:
        print("[Warn] Không tìm thấy scripts/validate_docs.py. Bỏ qua kiểm định.", file=sys.stderr)
        return

    try:
        print("[Info] Đang chạy kiểm định chất lượng tài liệu qua Docs Validator...")
        file_dir = Path(file_path).parent
        result = subprocess.run(
            [sys.executable, str(val_path), str(file_dir)], capture_output=True, text=True
        )
        if result.returncode == 0:
            print("SUCCESS: Kiểm định chất lượng tài liệu ĐẠT CHUẨN!")
        else:
            print(
                f"[Warning] Docs Validator phát hiện vấn đề định dạng trong thư mục tài liệu:\n{result.stdout.strip()}",
                file=sys.stderr,
            )
    except Exception as e:
        print(f"[Warn] Không thể chạy validate_docs.py: {e}", file=sys.stderr)


def post_process_summary(
    out_file: Path, source_path: str, notebook_id: str, source_id: str, sha256: str
) -> None:
    """Thêm Frontmatter và Disclaimer/Attribution vào tài liệu tóm tắt Markdown đầu ra."""
    if not out_file.exists():
        return

    try:
        with open(out_file, encoding="utf-8") as f:
            content = f.read()

        # Bóc tách nếu file đã có sẵn frontmatter cũ
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()

        frontmatter = f"""---
source_url_or_path: "{source_path}"
notebook_id: "{notebook_id}"
source_id: "{source_id}"
extracted_at: "{datetime.datetime.now().isoformat()}"
sha256: "{sha256}"
---

"""
        disclaimer = """

---
*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
"""

        # Chỉ chèn disclaimer nếu chưa có
        if "*Tạo bởi CCBA" not in content:
            new_content = frontmatter + content + disclaimer
        else:
            clean_content = (
                content.split("---", 1)[0].strip()
                if "*Nội dung này được tạo bởi" in content
                else content
            )
            new_content = frontmatter + clean_content + disclaimer

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        print(f"[Warn] Không thể hậu xử lý file tóm tắt: {e}", file=sys.stderr)


async def get_source_id_by_path(
    client: Any, notebook_id: str, source_path: str, sha256: str
) -> str:
    """Tìm hoặc nạp nguồn, trả về source_id và cập nhật registry."""
    sources = await client.sources.list(notebook_id)
    target_source = None

    registry = read_registry()
    norm_path = normalize_to_relative(source_path)
    if norm_path in registry:
        registered_info = registry[norm_path]
        if registered_info.get("notebook_id") == notebook_id:
            target_source_id = registered_info.get("source_id")
            target_source = next((src for src in sources if src.id == target_source_id), None)

            # Kiểm tra nếu file đã bị thay đổi nội dung thì xóa nguồn cũ trên Cloud
            if target_source and registered_info.get("sha256") != sha256:
                try:
                    print(
                        f"[Info] Phát hiện thay đổi nội dung (SHA-256 mismatch). Đang xóa nguồn cũ '{target_source_id}'..."
                    )
                    await client.sources.delete(notebook_id, target_source_id)
                    target_source = None
                except Exception as ex:
                    print(f"[Warn] Lỗi xóa bản cũ: {ex}", file=sys.stderr)

    if not target_source:
        for src in sources:
            if source_path in getattr(src, "url", "") or source_path in getattr(src, "title", ""):
                target_source = src
                break

    if not target_source:
        upload_path, is_temp = run_maskara_gate(source_path)
        try:
            print(f"[Info] Đang nạp nguồn dữ liệu mới: '{source_path}'...")
            if source_path.startswith(("http://", "https://")):
                target_source = await client.sources.add_url(notebook_id, upload_path, wait=True)
            else:
                target_source = await client.sources.add_file(notebook_id, upload_path)
            update_registry(source_path, target_source.id, sha256, notebook_id)
        finally:
            if is_temp and Path(upload_path).exists():
                try:
                    Path(upload_path).unlink()
                except Exception:
                    pass

    return str(target_source.id)


async def get_or_create_project_notebook(client: Any, project_name: str) -> str:
    """Lấy notebook_id hiện có hoặc tự tạo mới notebook chung cho dự án."""
    notebook_id = get_notebook_id_from_context()
    if notebook_id:
        try:
            notebooks = await client.notebooks.list()
            if any(nb.id == notebook_id for nb in notebooks):
                return notebook_id
        except Exception:
            pass

    title = f"CAP_Spoke_{project_name}"
    print(f"[Info] Đang tạo Notebook chung mới trên NotebookLM Cloud: '{title}'...")
    new_nb = await client.notebooks.create(title)
    save_notebook_id_to_context(new_nb.id)
    return str(new_nb.id)


async def handle_artifact_flow(
    task_type: str,
    source_path: str,
    output_dir: str,
    output_filename_pattern: str,
    generate_fn: Any,
    download_fn: Any,
    output_format: str = "",
) -> int:
    """Hàm điều phối tổng quát cho việc sinh, polling và download mọi loại Structured Artifacts."""
    if not HAS_NOTEBOOKLM:
        print("ERROR: Thư viện 'notebooklm-py' chưa được cài đặt.", file=sys.stderr)
        return 1

    project_name = Path(os.getcwd()).name
    sha256 = get_file_sha256(source_path)

    try:
        async with get_client() as client:
            notebook_id = await get_or_create_project_notebook(client, project_name)
            await check_quota_and_warn(client, notebook_id)

            source_id = await get_source_id_by_path(client, notebook_id, source_path, sha256)

            # Kiểm tra state chạy ngầm
            state = read_task_state()
            task_id = None
            if (
                state
                and state.get("notebook_id") == notebook_id
                and state.get("task_type") == task_type
                and state.get("source_id") == source_id
            ):
                created_at = datetime.datetime.fromisoformat(state["created_at"])
                if (datetime.datetime.now() - created_at).total_seconds() < 900:  # 15 min
                    print(
                        f"[Info] Phát hiện Task ID sinh {task_type} cũ đang chạy: {state['task_id']}"
                    )
                    print("[Info] Tiến hành khôi phục (resume) tiến trình polling...")
                    task_id = state["task_id"]

            if not task_id:
                print(f"[Info] Đang yêu cầu sinh {task_type} cho nguồn ID '{source_id}'...")
                status = await generate_fn(client, notebook_id, source_id)

                # Hỗ trợ trường hợp đặc biệt MindMapResult trả về kết quả trực tiếp không qua task_id
                if hasattr(status, "mind_map"):
                    out_path = Path(output_dir)
                    out_path.mkdir(parents=True, exist_ok=True)
                    filename = output_filename_pattern.format(source_id=source_id)
                    out_file = out_path / filename
                    print(f"[Info] Ghi mindmap trực tiếp về: {out_file.absolute()}...")
                    with open(out_file, "w", encoding="utf-8") as f_out:
                        json.dump(status.mind_map, f_out, ensure_ascii=False, indent=2)
                    print(f"SUCCESS: Ghi mindmap thành công về: {out_file.absolute()}")
                    return 0

                task_id = status.task_id
                save_task_state(notebook_id, task_id, source_id, task_type)
                print(
                    f"[Info] Google đang sinh {task_type} (Task ID: {task_id}). Quá trình có thể mất 1-5 phút..."
                )

            # Polling kiểm tra hoàn thành
            retry_count = 0
            max_network_retries = 5
            while True:
                try:
                    await client.artifacts.wait_for_completion(notebook_id, task_id)
                    break
                except NetworkError as net_err:
                    retry_count += 1
                    if retry_count > max_network_retries:
                        raise
                    sleep_time = 2**retry_count
                    print(
                        f"[Warn] Lỗi mạng tạm thời: {net_err}. Thử lại sau {sleep_time} giây...",
                        file=sys.stderr,
                    )
                    await asyncio.sleep(sleep_time)

            print(f"SUCCESS: Google đã tạo xong {task_type}!")
            clear_task_state()

            # Download file
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            filename = output_filename_pattern.format(source_id=source_id)
            out_file = out_path / filename

            print(f"[Info] Đang tải {task_type} về: {out_file.absolute()}...")
            if output_format:
                await download_fn(client, notebook_id, str(out_file), task_id, output_format)
            else:
                await download_fn(client, notebook_id, str(out_file), task_id)

            # QC nếu là Markdown
            if filename.endswith(".md"):
                post_process_summary(out_file, source_path, notebook_id, source_id, sha256)
                run_docs_validator(str(out_file))

            print(f"SUCCESS: Tải {task_type} thành công về: {out_file.absolute()}")
            return 0
    except Exception as e:
        print(f"ERROR: Tác vụ {task_type} thất bại. Chi tiết: {e}", file=sys.stderr)
        return 3


async def extract_and_summarize(source_path: str, output_path: str) -> int:
    """Usecase 1: Import đa nguồn, đối soát SHA-256 hash và kết xuất tóm tắt cấu trúc sạch."""
    if not HAS_NOTEBOOKLM:
        print("ERROR: Thư viện 'notebooklm-py' chưa được cài đặt.", file=sys.stderr)
        return 1

    project_name = Path(os.getcwd()).name
    sha256 = get_file_sha256(source_path)
    registry = read_registry()
    upload_path, is_temp = run_maskara_gate(source_path)

    try:
        async with get_client() as client:
            notebook_id = await get_or_create_project_notebook(client, project_name)
            await check_quota_and_warn(client, notebook_id)

            source_id = None
            norm_path = normalize_to_relative(source_path)
            if norm_path in registry:
                registered_info = registry[norm_path]
                if (
                    registered_info.get("sha256") == sha256
                    and registered_info.get("notebook_id") == notebook_id
                ):
                    print(
                        f"[Info] Phát hiện nội dung trùng khớp trên Cloud (SHA-256 match). Tái sử dụng Source ID: {registered_info['source_id']}"
                    )
                    source_id = registered_info["source_id"]
                else:
                    old_id = registered_info.get("source_id")
                    try:
                        print(
                            f"[Info] Nội dung thay đổi (SHA-256 mismatch). Đang xóa nguồn cũ '{old_id}'..."
                        )
                        await client.sources.delete(notebook_id, old_id)
                    except Exception as ex:
                        print(f"[Warn] Lỗi xóa bản cũ: {ex}", file=sys.stderr)

            if not source_id:
                print(
                    f"[Info] Đang import nguồn dữ liệu: '{upload_path}' vào notebook '{notebook_id}'..."
                )
                if source_path.startswith(("http://", "https://")):
                    source = await client.sources.add_url(notebook_id, upload_path, wait=True)
                else:
                    source = await client.sources.add_file(notebook_id, upload_path)
                source_id = source.id
                print(f"SUCCESS: Nạp nguồn thành công! Source ID: {source_id}")

            update_registry(source_path, source_id, sha256, notebook_id)

            print(f"[Info] Đang yêu cầu NotebookLM tóm tắt tri thức từ nguồn '{source_id}'...")
            prompt = (
                "Hãy phân tích và viết một bản tóm tắt cấu trúc chi tiết từ tài liệu nguồn này. "
                "Bản tóm tắt bắt buộc phải liệt kê các quy trình, bước nghiệp vụ, định nghĩa cốt lõi, "
                "và các patterns nổi bật của tài liệu dưới dạng Markdown sạch sẽ."
            )
            result = await client.chat.ask(notebook_id, prompt, source_ids=[source_id])

            out_dir = Path(output_path)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"summary_{source_id}.md"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(result.answer)

            post_process_summary(out_file, source_path, notebook_id, source_id, sha256)
            run_docs_validator(str(out_file))

            print(f"SUCCESS: Đã kết xuất tóm tắt cấu trúc sạch về tệp tin: {out_file.absolute()}")
            return 0

    except Exception as e:
        print(f"ERROR: Quá trình import hoặc trích xuất thất bại. Chi tiết: {e}", file=sys.stderr)
        return 3
    finally:
        if is_temp and Path(upload_path).exists():
            try:
                Path(upload_path).unlink()
            except Exception:
                pass


async def query_rag(source_path: str, prompt: str) -> int:
    """Usecase 2: Truy vấn RAG cô lập trên một tài liệu nguồn cụ thể."""
    if not HAS_NOTEBOOKLM:
        print("ERROR: Thư viện 'notebooklm-py' chưa được cài đặt.", file=sys.stderr)
        return 1

    project_name = Path(os.getcwd()).name
    sha256 = get_file_sha256(source_path)
    upload_path, is_temp = run_maskara_gate(source_path)

    try:
        async with get_client() as client:
            notebook_id = await get_or_create_project_notebook(client, project_name)
            await check_quota_and_warn(client, notebook_id)

            sources = await client.sources.list(notebook_id)
            target_source = None

            registry = read_registry()
            norm_path = normalize_to_relative(source_path)
            if norm_path in registry:
                registered_info = registry[norm_path]
                if registered_info.get("notebook_id") == notebook_id:
                    target_source_id = registered_info.get("source_id")
                    target_source = next(
                        (src for src in sources if src.id == target_source_id), None
                    )

            if not target_source:
                for src in sources:
                    if source_path in getattr(src, "url", "") or source_path in getattr(
                        src, "title", ""
                    ):
                        target_source = src
                        break

            if not target_source:
                print(f"[Info] Không tìm thấy nguồn có sẵn, đang nạp nguồn mới: '{source_path}'...")
                if source_path.startswith(("http://", "https://")):
                    target_source = await client.sources.add_url(
                        notebook_id, upload_path, wait=True
                    )
                else:
                    target_source = await client.sources.add_file(notebook_id, upload_path)
                update_registry(source_path, target_source.id, sha256, notebook_id)

            target_id = target_source.id
            print(f"[Info] Đang gửi câu hỏi RAG cô lập tới nguồn ID '{target_id}'...")

            result = await client.chat.ask(
                notebook_id=notebook_id, question=prompt, source_ids=[target_id]
            )

            print("\n=== 📋 CÂU TRẢ LỜI CỦA NOTEBOOKLM ===")
            print(result.answer)
            print("=====================================\n")
            return 0

    except Exception as e:
        print(f"ERROR: Truy vấn RAG thất bại. Chi tiết: {e}", file=sys.stderr)
        return 3
    finally:
        if is_temp and Path(upload_path).exists():
            try:
                Path(upload_path).unlink()
            except Exception:
                pass


async def list_notebooks() -> int:
    """Liệt kê tất cả các notebook hiện có trên Cloud."""
    if not HAS_NOTEBOOKLM:
        print(
            "ERROR: Thư viện 'notebooklm-py' chưa được cài đặt. Vui lòng chạy: pip install notebooklm-py",
            file=sys.stderr,
        )
        return 1

    try:
        async with get_client() as client:
            notebooks = await client.notebooks.list()
            if not notebooks:
                print("Không tìm thấy Sổ tay (Notebook) nào trên tài khoản Cloud.")
                return 0
            print(f"\n{'STT':<5} | {'Notebook Title':<45} | {'Notebook ID':<40}")
            print("-" * 100)
            for idx, nb in enumerate(notebooks, 1):
                nb_title = str(nb.title) if nb.title else "Untitled Notebook"
                nb_id = str(nb.id) if nb.id else "Unknown ID"
                print(f"{idx:<5} | {nb_title:<45} | {nb_id:<40}")
            print()
            return 0
    except Exception as e:
        print(f"ERROR: Liệt kê notebook thất bại. Chi tiết: {e}", file=sys.stderr)
        return 3


async def delete_notebook(notebook_id: str) -> int:
    """Xóa notebook trên Cloud và cập nhật context cục bộ."""
    if not HAS_NOTEBOOKLM:
        print("ERROR: Thư viện 'notebooklm-py' chưa được cài đặt.", file=sys.stderr)
        return 1

    try:
        async with get_client() as client:
            print(f"[Info] Đang yêu cầu xóa Notebook ID '{notebook_id}' khỏi Cloud...")
            await client.notebooks.delete(notebook_id)

            # Reset context cục bộ nếu trùng ID vừa xóa
            context_nb_id = get_notebook_id_from_context()
            if context_nb_id == notebook_id:
                save_notebook_id_to_context("")
                print("[Info] Đã gỡ bỏ Notebook ID khỏi workspace_context.yaml.")

            print("SUCCESS: Xóa Notebook thành công!")
            return 0
    except Exception as e:
        print(f"ERROR: Xóa notebook thất bại. Chi tiết: {e}", file=sys.stderr)
        return 3


async def share_notebook(notebook_id: str | None) -> int:
    """Bật chế độ chia sẻ công khai và lấy URL chia sẻ Notebook."""
    if not HAS_NOTEBOOKLM:
        print("ERROR: Thư viện 'notebooklm-py' chưa được cài đặt.", file=sys.stderr)
        return 1

    project_name = Path(os.getcwd()).name
    try:
        async with get_client() as client:
            if not notebook_id:
                notebook_id = await get_or_create_project_notebook(client, project_name)

            print(f"[Info] Đang kích hoạt chế độ chia sẻ cho Notebook ID '{notebook_id}'...")
            await client.sharing.set_public(notebook_id, True)
            share_url = client.notebooks.get_share_url(notebook_id)

            print("\nSUCCESS: Kích hoạt chia sẻ thành công!")
            print(f"🔗 Share URL: {share_url}\n")
            return 0
    except Exception as e:
        print(f"ERROR: Chia sẻ notebook thất bại. Chi tiết: {e}", file=sys.stderr)
        return 3


async def list_sources(notebook_id: str | None) -> int:
    """Liệt kê các nguồn trong Notebook của dự án."""
    if not HAS_NOTEBOOKLM:
        print("ERROR: Thư viện 'notebooklm-py' chưa được cài đặt.", file=sys.stderr)
        return 1

    project_name = Path(os.getcwd()).name
    try:
        async with get_client() as client:
            if not notebook_id:
                notebook_id = await get_or_create_project_notebook(client, project_name)

            sources = await client.sources.list(notebook_id)
            if not sources:
                print(f"Notebook ID '{notebook_id}' đang trống, chưa có nguồn nào.")
                return 0

            print(f"\n{'STT':<5} | {'Source Title/URL':<50} | {'Source ID':<40}")
            print("-" * 105)
            for idx, src in enumerate(sources, 1):
                title = getattr(src, "url", None) or getattr(src, "title", None) or "Unknown Source"
                title_str = str(title)
                src_id = str(src.id) if src.id else "Unknown ID"
                print(f"{idx:<5} | {title_str:<50} | {src_id:<40}")
            print()
            return 0
    except Exception as e:
        print(f"ERROR: Liệt kê nguồn thất bại. Chi tiết: {e}", file=sys.stderr)
        return 3


async def delete_source(source_id: str, notebook_id: str | None) -> int:
    """Xóa nguồn khỏi notebook trên Cloud và tự dọn dẹp registry cục bộ."""
    if not HAS_NOTEBOOKLM:
        print("ERROR: Thư viện 'notebooklm-py' chưa được cài đặt.", file=sys.stderr)
        return 1

    project_name = Path(os.getcwd()).name
    try:
        async with get_client() as client:
            if not notebook_id:
                notebook_id = await get_or_create_project_notebook(client, project_name)

            print(
                f"[Info] Đang yêu cầu xóa nguồn ID '{source_id}' khỏi notebook '{notebook_id}'..."
            )
            await client.sources.delete(notebook_id, source_id)

            # Cập nhật registry cục bộ
            registry = read_registry()
            to_delete_key = None
            for key, info in registry.items():
                if isinstance(info, dict) and info.get("source_id") == source_id:
                    to_delete_key = key
                    break

            if to_delete_key:
                del registry[to_delete_key]
                try:
                    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
                        yaml.safe_dump(registry, f, allow_unicode=True, default_flow_style=False)
                    print(f"[Info] Đã gỡ bản ghi nguồn '{to_delete_key}' khỏi registry cục bộ.")
                except Exception as ex:
                    print(f"[Warn] Lỗi cập nhật registry: {ex}", file=sys.stderr)

            print("SUCCESS: Xóa nguồn tài liệu thành công!")
            return 0
    except Exception as e:
        print(f"ERROR: Xóa nguồn tài liệu thất bại. Chi tiết: {e}", file=sys.stderr)
        return 3
