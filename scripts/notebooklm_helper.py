#!/usr/bin/env python
"""
Helper script bọc các tính năng của notebooklm-py phục vụ cho CCBA Agent Platform.
Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng
"""

import argparse
import asyncio
import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import skill_generator
import yaml  # type: ignore

# Cấu hình UTF-8 cho console đầu ra trên Windows để tránh lỗi mã hóa ký tự tiếng Việt
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Thử import thư viện notebooklm-py và các types
try:
    from notebooklm import NotebookLMClient  # type: ignore
    from notebooklm.exceptions import NetworkError  # type: ignore
    from notebooklm.rpc.types import (  # type: ignore
        InfographicDetail,
        InfographicOrientation,
        InfographicStyle,
        QuizDifficulty,
        QuizQuantity,
        ReportFormat,
        SlideDeckFormat,
        SlideDeckLength,
        VideoFormat,
        VideoStyle,
    )
    HAS_NOTEBOOKLM = True
except ImportError:
    NotebookLMClient = None
    HAS_NOTEBOOKLM = False
    # Mock classes to pass syntax parser
    QuizQuantity = QuizDifficulty = SlideDeckFormat = SlideDeckLength = None
    ReportFormat = InfographicOrientation = InfographicDetail = InfographicStyle = None
    VideoFormat = VideoStyle = None

CONTEXT_FILE = Path(".md/workspace_context.yaml")
REGISTRY_FILE = Path(".md/knowledge/sources_registry.yaml")
TASK_STATE_FILE = Path(".md/scratch/notebooklm_task_state.yaml")

# ==========================================
# 1. HỖ TRỢ THƯ MỤC TRI THỨC & REGISTRY
# ==========================================

def get_file_sha256(filepath: str) -> str:
    """Tính mã SHA-256 của file cục bộ hoặc URL."""
    if filepath.startswith(("http://", "https://")):
        return hashlib.sha256(filepath.encode("utf-8")).hexdigest()

    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def read_registry() -> dict[str, Any]:
    """Đọc dữ liệu từ registry cục bộ."""
    if not REGISTRY_FILE.exists():
        return {}
    try:
        with open(REGISTRY_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return dict(data) if data else {}
    except Exception:
        return {}

def update_registry(file_path: str, source_id: str, sha256: str, notebook_id: str) -> None:
    """Cập nhật thông tin file vào registry."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    registry = read_registry()
    registry[file_path] = {
        "source_id": source_id,
        "sha256": sha256,
        "notebook_id": notebook_id,
        "updated_at": datetime.datetime.now().isoformat()
    }
    try:
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(registry, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        print(f"[Warn] Không thể ghi registry: {e}", file=sys.stderr)

def get_notebook_id_from_context() -> str | None:
    """Đọc notebook_id từ workspace_context.yaml nếu tồn tại."""
    if not CONTEXT_FILE.exists():
        return None
    try:
        with open(CONTEXT_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data and "project" in data:
                val = data["project"].get("notebook_id")
                return str(val) if val else None
            return None
    except Exception:
        return None

def save_notebook_id_to_context(notebook_id: str) -> None:
    """Lưu notebook_id ngược lại workspace_context.yaml."""
    data: dict[str, Any] = {}
    if CONTEXT_FILE.exists():
        try:
            with open(CONTEXT_FILE, encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    data = loaded
        except Exception:
            pass

    try:
        if "project" not in data:
            data["project"] = {}
        data["project"]["notebook_id"] = notebook_id

        CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        print(f"[Warn] Không thể lưu notebook_id vào context file: {e}", file=sys.stderr)

# ==========================================
# 2. XỬ LÝ AUTHENTICATION (HEADLESS AUTH)
# ==========================================

def get_temp_storage_path() -> Path:
    """Đường dẫn lưu trữ file Playwright cookie tạm thời."""
    scratch_dir = Path(".md/scratch")
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir / "notebooklm_cookies.json"

def inject_auth_cookies() -> str | None:
    """
    Đọc biến môi trường và tạo file cookie tạm thời cho Playwright.
    Trả về đường dẫn file cookies JSON nếu thành công, None nếu dùng mặc định.
    """
    env_cookie = os.environ.get("NOTEBOOKLM_SESSION_COOKIE")
    env_json = os.environ.get("NOTEBOOKLM_COOKIES_JSON")
    temp_path = get_temp_storage_path()

    if env_json:
        try:
            data = json.loads(env_json)
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("[Info] Đã nạp cấu hình auth từ NOTEBOOKLM_COOKIES_JSON.")
            return str(temp_path.absolute())
        except Exception as e:
            print(f"[Warn] Lỗi phân tích NOTEBOOKLM_COOKIES_JSON: {e}", file=sys.stderr)

    if env_cookie:
        try:
            cookies = []
            for part in env_cookie.split(";"):
                if "=" in part:
                    name, value = part.strip().split("=", 1)
                    cookies.append({
                        "name": name,
                        "value": value,
                        "domain": ".google.com",
                        "path": "/",
                        "expires": -1,
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "Lax"
                    })
            storage_state = {
                "cookies": cookies,
                "origins": []
            }
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(storage_state, f, ensure_ascii=False, indent=2)
            print("[Info] Đã chuyển đổi và nạp auth từ NOTEBOOKLM_SESSION_COOKIE.")
            return str(temp_path.absolute())
        except Exception as e:
            print(f"[Warn] Lỗi phân tích NOTEBOOKLM_SESSION_COOKIE: {e}", file=sys.stderr)

    return None

def get_client() -> Any:
    """Tạo đối tượng client với các thiết lập auth phù hợp."""
    cookie_path = inject_auth_cookies()
    if cookie_path:
        return NotebookLMClient.from_storage(path=cookie_path)
    return NotebookLMClient.from_storage()

# ==========================================
# 3. QUẢN LÝ QUOTA & GARBAGE COLLECTION
# ==========================================

async def run_garbage_collection(client: Any, notebook_id: str, sources: list[Any]) -> None:
    """Quét và dọn dẹp các nguồn không còn liên kết cục bộ để giải phóng Quota."""
    registry = read_registry()
    registered_ids = {info["source_id"] for info in registry.values() if isinstance(info, dict) and "source_id" in info}

    print("[Info] Bắt đầu dọn dẹp nguồn mồ côi (Garbage Collection)...")
    for src in sources:
        if src.id not in registered_ids:
            try:
                print(f"[Info] Đang xóa nguồn cũ không còn dùng trên Cloud: Title='{src.title}', ID='{src.id}'...")
                await client.sources.delete(notebook_id, src.id)
            except Exception as e:
                print(f"[Warn] Không thể xóa nguồn '{src.id}': {e}", file=sys.stderr)

async def check_quota_and_warn(client: Any, notebook_id: str) -> None:
    """Kiểm tra Subscription Tier và cảnh báo sớm về Quota."""
    try:
        tier = await client.settings.get_account_tier()
        limits = await client.settings.get_account_limits()
        print(f"[Info] NotebookLM Account Tier: {tier.tier} ({tier.plan_name or 'Standard Plan'})")

        # Hạn mức mặc định nếu không có limit cụ thể
        source_limit = limits.source_limit if limits.source_limit is not None else 50

        sources = await client.sources.list(notebook_id)
        current_sources_count = len(sources)

        print(f"[Info] Hạn mức nguồn tài liệu tối đa của tài khoản: {source_limit}")
        print(f"[Info] Số lượng nguồn hiện tại trong Notebook: {current_sources_count}/{source_limit}")

        if current_sources_count >= source_limit * 0.9:
            print(f"\n[WARNING] Số lượng nguồn trong notebook sắp đạt giới hạn ({current_sources_count}/{source_limit})!", file=sys.stderr)
            await run_garbage_collection(client, notebook_id, sources)
    except Exception as e:
        print(f"[Warn] Không thể kiểm tra quota: {e}", file=sys.stderr)

# ==========================================
# 4. CHỐT CHẶN BẢO MẬT MASKARA GATE
# ==========================================

def run_maskara_gate(source_path: str) -> tuple[str, bool]:
    """
    Kiểm tra bảo mật file cục bộ qua Maskara.
    Trả về: (đường dẫn_file_để_upload, có_phải_file_tạm_không)
    """
    if source_path.startswith(("http://", "https://")):
        return source_path, False

    try:
        import importlib.util
        maskara_path = Path(__file__).parent / "maskara.py"
        if not maskara_path.exists():
            raise ImportError("maskara.py not found")
        spec = importlib.util.spec_from_file_location("maskara", maskara_path)
        if spec is None or spec.loader is None:
            raise ImportError("Could not load spec for maskara")
        maskara = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(maskara)
    except Exception as e:
        print(f"[Warn] Thư viện maskara.py không import được: {e}. Bỏ qua chốt chặn bảo mật.", file=sys.stderr)
        return source_path, False

    file_p = Path(source_path)
    if not file_p.exists():
        return source_path, False

    if maskara.is_binary(file_p):
        return source_path, False

    try:
        print(f"[Info] Đang quét bảo mật file '{source_path}' qua Maskara Gate...")
        with open(file_p, "rb") as file_io:
            original_bytes = file_io.read()

        try:
            content = original_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = original_bytes.decode("latin-1")

        findings = maskara.detect_secrets_in_text(content, str(file_p), "notebooklm")

        if findings:
            critical_findings = [f for f in findings if f.get("severity") in ("critical", "high")]
            if any(f.get("rule_id") in ("openai-api-key", "anthropic-api-key", "github-token", "google-api-key") for f in critical_findings):
                print(f"\n[CRITICAL SECURITY ERROR] Phát hiện API Key nhạy cảm trong file '{source_path}'!", file=sys.stderr)
                for finding in critical_findings:
                    print(f"  - {finding.get('name')}: Dòng {finding.get('line')}", file=sys.stderr)
                raise ValueError("Tiến trình upload bị CHẶN vì lý do an toàn thông tin.")

            print(f"[Warning] Phát hiện {len(findings)} thông tin nhạy cảm. Đang che giấu (redact)...")
            rewritten_bytes, num_redacted = maskara.apply_raw_redactions(original_bytes, findings)

            scratch_dir = Path(".md/scratch/redacted")
            scratch_dir.mkdir(parents=True, exist_ok=True)
            temp_redacted_file = scratch_dir / f"redacted_{file_p.name}"
            with open(temp_redacted_file, "wb") as file_out:
                file_out.write(rewritten_bytes)

            print(f"[Info] Đã làm sạch file và xuất tệp tạm: {temp_redacted_file}")
            return str(temp_redacted_file.absolute()), True
    except Exception as e:
        if "CHẶN" in str(e) or "an toàn thông tin" in str(e):
            raise
        print(f"[Warn] Lỗi khi chạy Maskara Gate: {e}", file=sys.stderr)

    return source_path, False

# ==========================================
# 5. KHÔI PHỤC TIẾN TRÌNH AUDIO/TASK STATE
# ==========================================

def read_task_state() -> dict[str, Any] | None:
    """Đọc tệp state tác vụ đang sinh ngầm."""
    if not TASK_STATE_FILE.exists():
        return None
    try:
        with open(TASK_STATE_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return dict(data) if isinstance(data, dict) else None
    except Exception:
        return None

def save_task_state(notebook_id: str, task_id: str, source_id: str, task_type: str) -> None:
    """Lưu tệp state tác vụ để có thể resume."""
    TASK_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "notebook_id": notebook_id,
        "task_id": task_id,
        "source_id": source_id,
        "task_type": task_type,
        "created_at": datetime.datetime.now().isoformat()
    }
    try:
        with open(TASK_STATE_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(state, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        print(f"[Warn] Không thể ghi state task: {e}", file=sys.stderr)

def clear_task_state() -> None:
    """Xóa tệp state sau khi hoàn thành."""
    if TASK_STATE_FILE.exists():
        try:
            TASK_STATE_FILE.unlink()
        except Exception:
            pass

# ==========================================
# 6. ĐỒNG BỘ TRI THỨC VÀ HẬU XỬ LÝ (QC)
# ==========================================

def run_docs_validator(file_path: str) -> None:
    """Chạy docs-validator để kiểm định chất lượng tài liệu."""
    try:
        print("[Info] Đang chạy kiểm định chất lượng tài liệu qua Docs Validator...")
        file_dir = Path(file_path).parent
        result = subprocess.run(
            [sys.executable, "scripts/validate_docs.py", str(file_dir)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("SUCCESS: Kiểm định chất lượng tài liệu ĐẠT CHUẨN!")
        else:
            print(f"[Warning] Docs Validator phát hiện vấn đề định dạng trong thư mục tài liệu:\n{result.stdout.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"[Warn] Không thể chạy validate_docs.py: {e}", file=sys.stderr)

def post_process_summary(out_file: Path, source_path: str, notebook_id: str, source_id: str, sha256: str) -> None:
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
            clean_content = content.split("---", 1)[0].strip() if "*Nội dung này được tạo bởi" in content else content
            new_content = frontmatter + clean_content + disclaimer

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        print(f"[Warn] Không thể hậu xử lý file tóm tắt: {e}", file=sys.stderr)

# ==========================================
# 7. CƠ CHẾ ĐIỀU PHỐI DỮ LIỆU NGUỒN CỐT LÕI
# ==========================================

async def get_source_id_by_path(client: Any, notebook_id: str, source_path: str, sha256: str) -> str:
    """Tìm hoặc nạp nguồn, trả về source_id và cập nhật registry."""
    sources = await client.sources.list(notebook_id)
    target_source = None

    registry = read_registry()
    if source_path in registry:
        registered_info = registry[source_path]
        if registered_info.get("notebook_id") == notebook_id:
            target_source_id = registered_info.get("source_id")
            target_source = next((src for src in sources if src.id == target_source_id), None)

            # Kiểm tra nếu file đã bị thay đổi nội dung thì xóa nguồn cũ trên Cloud
            if target_source and registered_info.get("sha256") != sha256:
                try:
                    print(f"[Info] Phát hiện thay đổi nội dung (SHA-256 mismatch). Đang xóa nguồn cũ '{target_source_id}'...")
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

async def handle_artifact_flow(
    task_type: str,
    source_path: str,
    output_dir: str,
    output_filename_pattern: str,
    generate_fn: Any,
    download_fn: Any,
    output_format: str = ""
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
            if state and state.get("notebook_id") == notebook_id and state.get("task_type") == task_type and state.get("source_id") == source_id:
                created_at = datetime.datetime.fromisoformat(state["created_at"])
                if (datetime.datetime.now() - created_at).total_seconds() < 900:  # 15 min
                    print(f"[Info] Phát hiện Task ID sinh {task_type} cũ đang chạy: {state['task_id']}")
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
                print(f"[Info] Google đang sinh {task_type} (Task ID: {task_id}). Quá trình có thể mất 1-5 phút...")

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
                    sleep_time = 2 ** retry_count
                    print(f"[Warn] Lỗi mạng tạm thời: {net_err}. Thử lại sau {sleep_time} giây...", file=sys.stderr)
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

# ==========================================
# 8. CÁC HÀM CORE THỰC THI (CLI COMMANDS)
# ==========================================

async def check_auth() -> int:
    """Kiểm tra trạng thái đăng nhập NotebookLM."""
    if not HAS_NOTEBOOKLM:
        print("ERROR: Thư viện 'notebooklm-py' chưa được cài đặt. Vui lòng chạy: pip install notebooklm-py", file=sys.stderr)
        return 1

    try:
        async with get_client() as client:
            await client.notebooks.list()
            print("SUCCESS: Kết nối và xác thực thành công với Google NotebookLM Cloud!")
            tier = await client.settings.get_account_tier()
            print(f"[Info] Subscription Tier: {tier.tier} ({tier.plan_name or 'Standard Plan'})")
            return 0
    except Exception as e:
        print(f"ERROR_AUTH: Session cookie đã hết hạn hoặc không tồn tại. Vui lòng chạy 'python -m notebooklm login' trên trình duyệt để đăng nhập lại. Chi tiết: {e}", file=sys.stderr)
        return 2

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
            if source_path in registry:
                registered_info = registry[source_path]
                if registered_info.get("sha256") == sha256 and registered_info.get("notebook_id") == notebook_id:
                    print(f"[Info] Phát hiện nội dung trùng khớp trên Cloud (SHA-256 match). Tái sử dụng Source ID: {registered_info['source_id']}")
                    source_id = registered_info["source_id"]
                else:
                    old_id = registered_info.get("source_id")
                    try:
                        print(f"[Info] Nội dung thay đổi (SHA-256 mismatch). Đang xóa nguồn cũ '{old_id}'...")
                        await client.sources.delete(notebook_id, old_id)
                    except Exception as ex:
                        print(f"[Warn] Lỗi xóa bản cũ: {ex}", file=sys.stderr)

            if not source_id:
                print(f"[Info] Đang import nguồn dữ liệu: '{upload_path}' vào notebook '{notebook_id}'...")
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
            if source_path in registry:
                registered_info = registry[source_path]
                if registered_info.get("notebook_id") == notebook_id:
                    target_source_id = registered_info.get("source_id")
                    target_source = next((src for src in sources if src.id == target_source_id), None)

            if not target_source:
                for src in sources:
                    if source_path in getattr(src, "url", "") or source_path in getattr(src, "title", ""):
                        target_source = src
                        break

            if not target_source:
                print(f"[Info] Không tìm thấy nguồn có sẵn, đang nạp nguồn mới: '{source_path}'...")
                if source_path.startswith(("http://", "https://")):
                    target_source = await client.sources.add_url(notebook_id, upload_path, wait=True)
                else:
                    target_source = await client.sources.add_file(notebook_id, upload_path)
                update_registry(source_path, target_source.id, sha256, notebook_id)

            target_id = target_source.id
            print(f"[Info] Đang gửi câu hỏi RAG cô lập tới nguồn ID '{target_id}'...")

            result = await client.chat.ask(
                notebook_id=notebook_id,
                question=prompt,
                source_ids=[target_id]
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

# ==========================================
# 8.2 CÁC LỆNH QUẢN TRỊ MỚI BỔ SUNG (CRUD CLI)
# ==========================================

async def list_notebooks() -> int:
    """Liệt kê tất cả các notebook hiện có trên Cloud."""
    if not HAS_NOTEBOOKLM:
        print("ERROR: Thư viện 'notebooklm-py' chưa được cài đặt. Vui lòng chạy: pip install notebooklm-py", file=sys.stderr)
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

            print(f"[Info] Đang yêu cầu xóa nguồn ID '{source_id}' khỏi notebook '{notebook_id}'...")
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

# ==========================================
# 9. MAPPING FUNCTIONS CHO CLI ENUMS
# ==========================================

def map_quiz_quantity(q: str) -> Any:
    q_map = {"fewer": QuizQuantity.FEWER, "standard": QuizQuantity.STANDARD}
    return q_map.get(q.lower(), QuizQuantity.STANDARD)

def map_quiz_difficulty(d: str) -> Any:
    d_map = {"easy": QuizDifficulty.EASY, "medium": QuizDifficulty.MEDIUM, "hard": QuizDifficulty.HARD}
    return d_map.get(d.lower(), QuizDifficulty.MEDIUM)

def map_slide_format(f: str) -> Any:
    f_map = {"detailed": SlideDeckFormat.DETAILED_DECK, "presenter": SlideDeckFormat.PRESENTER_SLIDES}
    return f_map.get(f.lower(), SlideDeckFormat.DETAILED_DECK)

def map_slide_length(slide_len: str) -> Any:
    l_map = {"default": SlideDeckLength.DEFAULT, "short": SlideDeckLength.SHORT}
    return l_map.get(slide_len.lower(), SlideDeckLength.DEFAULT)

def map_info_orientation(o: str) -> Any:
    o_map = {"portrait": InfographicOrientation.PORTRAIT, "landscape": InfographicOrientation.LANDSCAPE}
    return o_map.get(o.lower(), InfographicOrientation.PORTRAIT)

def map_info_detail(d: str) -> Any:
    d_map = {"default": InfographicDetail.DEFAULT, "summary": InfographicDetail.SUMMARY, "detailed": InfographicDetail.DETAILED}
    return d_map.get(d.lower(), InfographicDetail.DEFAULT)

def map_info_style(s: str) -> Any:
    s_map = {"modern": InfographicStyle.MODERN, "minimal": InfographicStyle.MINIMAL, "colorful": InfographicStyle.COLORFUL}
    return s_map.get(s.lower(), InfographicStyle.MODERN)

def map_report_format(f: str) -> Any:
    f_map = {"briefing_doc": ReportFormat.BRIEFING_DOC, "study_guide": ReportFormat.STUDY_GUIDE, "blog_post": ReportFormat.BLOG_POST, "custom": ReportFormat.CUSTOM}
    return f_map.get(f.lower(), ReportFormat.BRIEFING_DOC)

def map_video_format(f: str) -> Any:
    f_map = {"explainer": VideoFormat.EXPLAINER, "brief": VideoFormat.BRIEF, "cinematic": VideoFormat.CINEMATIC}
    return f_map.get(f.lower(), VideoFormat.EXPLAINER)

def map_video_style(s: str) -> Any:
    s_map = {"modern": VideoStyle.MODERN, "classic": VideoStyle.CLASSIC}
    return s_map.get(s.lower(), VideoStyle.MODERN)

# ==========================================
# 10. HÀM MAIN VÀ CLI PARSER
# ==========================================

def main() -> int:
    parser = argparse.ArgumentParser(description="CCBA Platform NotebookLM Helper Wrapper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command check-auth
    subparsers.add_parser("check-auth", help="Kiểm tra trạng thái đăng nhập Google")

    # Sub-command extract
    parser_extract = subparsers.add_parser("extract", help="Import nguồn và kết xuất tóm tắt")
    parser_extract.add_argument("--source", required=True, help="URL Youtube/Web hoặc đường dẫn file cục bộ")
    parser_extract.add_argument("--output", default=".md/extracted_docs/summaries/", help="Thư mục đầu ra")

    # Sub-command query
    parser_query = subparsers.add_parser("query", help="Truy vấn RAG cô lập nguồn")
    parser_query.add_argument("--source", required=True, help="Tài liệu nguồn cần lọc RAG")
    parser_query.add_argument("--prompt", required=True, help="Câu hỏi truy vấn")

    # Sub-command audio
    parser_audio = subparsers.add_parser("audio", help="Sinh và tải Podcast Audio Overview")
    parser_audio.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_audio.add_argument("--output", default=".md/scratch/audio/", help="Thư mục lưu tệp mp3")

    # Sub-command quiz
    parser_quiz = subparsers.add_parser("quiz", help="Sinh quiz trắc nghiệm từ tài liệu")
    parser_quiz.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_quiz.add_argument("--output", default=".md/scratch/quizzes/", help="Thư mục lưu tệp json")
    parser_quiz.add_argument("--quantity", choices=["fewer", "standard"], default="standard", help="Số lượng câu hỏi")
    parser_quiz.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium", help="Độ khó")

    # Sub-command slides
    parser_slides = subparsers.add_parser("slides", help="Sinh Slide thuyết trình dạng PDF")
    parser_slides.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_slides.add_argument("--output", default=".md/scratch/slides/", help="Thư mục lưu tệp pdf")
    parser_slides.add_argument("--format", choices=["detailed", "presenter"], default="detailed", help="Định dạng slide")
    parser_slides.add_argument("--length", choices=["default", "short"], default="default", help="Độ dài")
    parser_slides.add_argument("--language", default="en", help="Ngôn ngữ sinh slide")

    # Sub-command mindmap
    parser_mindmap = subparsers.add_parser("mindmap", help="Sinh sơ đồ tư duy dạng JSON")
    parser_mindmap.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_mindmap.add_argument("--output", default=".md/scratch/mindmaps/", help="Thư mục lưu tệp json")

    # Sub-command infographic
    parser_infographic = subparsers.add_parser("infographic", help="Sinh Infographic dạng PDF")
    parser_infographic.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_infographic.add_argument("--output", default=".md/scratch/infographics/", help="Thư mục lưu")
    parser_infographic.add_argument("--orientation", choices=["portrait", "landscape"], default="portrait", help="Hướng khổ giấy")
    parser_infographic.add_argument("--detail", choices=["default", "summary", "detailed"], default="default", help="Mức chi tiết")
    parser_infographic.add_argument("--style", choices=["modern", "minimal", "colorful"], default="modern", help="Phong cách thiết kế")

    # Sub-command study-guide
    parser_guide = subparsers.add_parser("study-guide", help="Sinh cẩm nang học tập dạng PDF")
    parser_guide.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_guide.add_argument("--output", default=".md/scratch/study_guides/", help="Thư mục lưu")

    # Sub-command data-table
    parser_table = subparsers.add_parser("data-table", help="Trích xuất bảng dữ liệu cấu trúc dạng CSV")
    parser_table.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_table.add_argument("--output", default=".md/scratch/data_tables/", help="Thư mục lưu")
    parser_table.add_argument("--instructions", default="", help="Chỉ dẫn thêm để trích xuất bảng")

    # Sub-command flashcards
    parser_flash = subparsers.add_parser("flashcards", help="Sinh thẻ ghi nhớ dạng JSON")
    parser_flash.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_flash.add_argument("--output", default=".md/scratch/flashcards/", help="Thư mục lưu")
    parser_flash.add_argument("--quantity", choices=["fewer", "standard"], default="standard")
    parser_flash.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium")

    # Sub-command report
    parser_report = subparsers.add_parser("report", help="Sinh báo cáo chuyên sâu dạng Markdown/PDF")
    parser_report.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_report.add_argument("--output", default=".md/scratch/reports/", help="Thư mục lưu")
    parser_report.add_argument("--format", choices=["briefing_doc", "study_guide", "blog_post", "custom"], default="briefing_doc")
    parser_report.add_argument("--instructions", default="")

    # Sub-command video
    parser_video = subparsers.add_parser("video", help="Sinh video tóm tắt dạng MP4")
    parser_video.add_argument("--source", required=True, help="Tài liệu nguồn")
    parser_video.add_argument("--output", default=".md/scratch/videos/", help="Thư mục lưu")
    parser_video.add_argument("--format", choices=["explainer", "brief", "cinematic"], default="explainer")
    parser_video.add_argument("--style", choices=["modern", "classic"], default="modern")

    # CLI LỆNH QUẢN TRỊ (CRUD CLI)

    # Sub-command list-notebooks
    subparsers.add_parser("list-notebooks", help="Liệt kê tất cả các notebook hiện có")

    # Sub-command delete-notebook
    parser_del_nb = subparsers.add_parser("delete-notebook", help="Xóa một notebook cụ thể")
    parser_del_nb.add_argument("--notebook-id", required=True, help="Notebook ID cần xóa")

    # Sub-command share-notebook
    parser_share = subparsers.add_parser("share-notebook", help="Kích hoạt chia sẻ notebook và lấy Share URL")
    parser_share.add_argument("--notebook-id", default=None, help="Notebook ID (tùy chọn)")

    # Sub-command list-sources
    parser_list_src = subparsers.add_parser("list-sources", help="Liệt kê các nguồn trong notebook")
    parser_list_src.add_argument("--notebook-id", default=None, help="Notebook ID (tùy chọn)")

    # Sub-command delete-source
    parser_del_src = subparsers.add_parser("delete-source", help="Xóa một nguồn cụ thể")
    parser_del_src.add_argument("--source-id", required=True, help="Source ID cần xóa")
    parser_del_src.add_argument("--notebook-id", default=None, help="Notebook ID (tùy chọn)")

    # Sub-command create-skill
    parser_create_skill = subparsers.add_parser("create-skill", help="Tự động tạo Skill từ tệp Python script")
    parser_create_skill.add_argument("--script", required=True, help="Đường dẫn file script Python nguồn")
    parser_create_skill.add_argument("--name", default=None, help="Tên Skill muốn tạo (tùy chọn)")

    # Sub-command sync-skills
    subparsers.add_parser("sync-skills", help="Đồng bộ tự động các cli_spec.yaml từ scripts")

    args = parser.parse_args()

    # Set event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        if args.command == "check-auth":
            return int(loop.run_until_complete(check_auth()))
        elif args.command == "extract":
            return int(loop.run_until_complete(extract_and_summarize(args.source, args.output)))
        elif args.command == "query":
            return int(loop.run_until_complete(query_rag(args.source, args.prompt)))
        elif args.command == "audio":
            return int(loop.run_until_complete(handle_artifact_flow(
                task_type="audio",
                source_path=args.source,
                output_dir=args.output,
                output_filename_pattern="audio_overview_{source_id}.mp3",
                generate_fn=lambda c, nb, src: c.artifacts.generate_audio(nb),
                download_fn=lambda c, nb, out, tid: c.artifacts.download_audio(nb, out)
            )))
        elif args.command == "quiz":
            qty = map_quiz_quantity(args.quantity)
            diff = map_quiz_difficulty(args.difficulty)
            return int(loop.run_until_complete(handle_artifact_flow(
                task_type="quiz",
                source_path=args.source,
                output_dir=args.output,
                output_filename_pattern="quiz_{source_id}.json",
                generate_fn=lambda c, nb, src: c.artifacts.generate_quiz(nb, source_ids=[src], quantity=qty, difficulty=diff),
                download_fn=lambda c, nb, out, tid, fmt: c.artifacts.download_quiz(nb, out, output_format=fmt),
                output_format="json"
            )))
        elif args.command == "slides":
            fmt = map_slide_format(args.format)
            length = map_slide_length(args.length)
            return int(loop.run_until_complete(handle_artifact_flow(
                task_type="slides",
                source_path=args.source,
                output_dir=args.output,
                output_filename_pattern="slides_{source_id}.pdf",
                generate_fn=lambda c, nb, src: c.artifacts.generate_slide_deck(nb, source_ids=[src], language=args.language, slide_format=fmt, slide_length=length),
                download_fn=lambda c, nb, out, tid, fmt: c.artifacts.download_slide_deck(nb, out, output_format=fmt),
                output_format="pdf"
            )))
        elif args.command == "mindmap":
            return int(loop.run_until_complete(handle_artifact_flow(
                task_type="mindmap",
                source_path=args.source,
                output_dir=args.output,
                output_filename_pattern="mindmap_{source_id}.json",
                generate_fn=lambda c, nb, src: c.artifacts.generate_mind_map(nb, source_ids=[src]),
                download_fn=lambda c, nb, out, tid: c.artifacts.download_mind_map(nb, out)
            )))
        elif args.command == "infographic":
            orient = map_info_orientation(args.orientation)
            det = map_info_detail(args.detail)
            sty = map_info_style(args.style)
            return int(loop.run_until_complete(handle_artifact_flow(
                task_type="infographic",
                source_path=args.source,
                output_dir=args.output,
                output_filename_pattern="infographic_{source_id}.pdf",
                generate_fn=lambda c, nb, src: c.artifacts.generate_infographic(nb, source_ids=[src], orientation=orient, detail_level=det, style=sty),
                download_fn=lambda c, nb, out, tid: c.artifacts.download_infographic(nb, out)
            )))
        elif args.command == "study-guide":
            return int(loop.run_until_complete(handle_artifact_flow(
                task_type="study-guide",
                source_path=args.source,
                output_dir=args.output,
                output_filename_pattern="study_guide_{source_id}.md",
                generate_fn=lambda c, nb, src: c.artifacts.generate_study_guide(nb, source_ids=[src]),
                download_fn=lambda c, nb, out, tid: c.artifacts.download_report(nb, out)
            )))
        elif args.command == "data-table":
            return int(loop.run_until_complete(handle_artifact_flow(
                task_type="data-table",
                source_path=args.source,
                output_dir=args.output,
                output_filename_pattern="data_table_{source_id}.csv",
                generate_fn=lambda c, nb, src: c.artifacts.generate_data_table(nb, source_ids=[src], instructions=args.instructions),
                download_fn=lambda c, nb, out, tid: c.artifacts.download_data_table(nb, out)
            )))
        elif args.command == "flashcards":
            qty = map_quiz_quantity(args.quantity)
            diff = map_quiz_difficulty(args.difficulty)
            return int(loop.run_until_complete(handle_artifact_flow(
                task_type="flashcards",
                source_path=args.source,
                output_dir=args.output,
                output_filename_pattern="flashcards_{source_id}.json",
                generate_fn=lambda c, nb, src: c.artifacts.generate_flashcards(nb, source_ids=[src], quantity=qty, difficulty=diff),
                download_fn=lambda c, nb, out, tid, fmt: c.artifacts.download_flashcards(nb, out, output_format=fmt),
                output_format="json"
            )))
        elif args.command == "report":
            fmt = map_report_format(args.format)
            return int(loop.run_until_complete(handle_artifact_flow(
                task_type="report",
                source_path=args.source,
                output_dir=args.output,
                output_filename_pattern="report_{source_id}.md",
                generate_fn=lambda c, nb, src: c.artifacts.generate_report(nb, source_ids=[src], report_format=fmt, extra_instructions=args.instructions),
                download_fn=lambda c, nb, out, tid: c.artifacts.download_report(nb, out)
            )))
        elif args.command == "video":
            fmt = map_video_format(args.format)
            sty = map_video_style(args.style)
            return int(loop.run_until_complete(handle_artifact_flow(
                task_type="video",
                source_path=args.source,
                output_dir=args.output,
                output_filename_pattern="video_{source_id}.mp4",
                generate_fn=lambda c, nb, src: c.artifacts.generate_video(nb, source_ids=[src], video_format=fmt, video_style=sty),
                download_fn=lambda c, nb, out, tid: c.artifacts.download_video(nb, out)
            )))
        # MAPPING CÁC LỆNH QUẢN TRỊ
        elif args.command == "list-notebooks":
            return int(loop.run_until_complete(list_notebooks()))
        elif args.command == "delete-notebook":
            return int(loop.run_until_complete(delete_notebook(args.notebook_id)))
        elif args.command == "share-notebook":
            return int(loop.run_until_complete(share_notebook(args.notebook_id)))
        elif args.command == "list-sources":
            return int(loop.run_until_complete(list_sources(args.notebook_id)))
        elif args.command == "delete-source":
            return int(loop.run_until_complete(delete_source(args.source_id, args.notebook_id)))
        elif args.command == "create-skill":
            return int(skill_generator.create_skill_from_script(args.script, args.name))
        elif args.command == "sync-skills":
            return int(skill_generator.sync_all_skills())
    finally:
        loop.close()

    return 1

if __name__ == "__main__":
    sys.exit(main())
