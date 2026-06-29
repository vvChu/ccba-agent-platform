"""
Model Context Protocol (MCP) Server for ccba-agent-platform.
Exposes rich, JSON-first tools using the Anthropic MCP Python SDK (FastMCP).
Integrates Privacy Guard middleware to block API key leaks.
"""

import functools
import inspect
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Attempt import of FastMCP
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("[Error] Anthropic 'mcp' package is not installed. Run 'uv sync' first.", file=sys.stderr)
    sys.exit(1)

# Import services from ccba_ai
from ccba_ai import services
from ccba_ai.hooks import PrivacyGuardHook

# Expose scripts folder for idop_scaffolder import
cwd_scripts = Path.cwd() / "scripts"
if cwd_scripts.exists() and str(cwd_scripts) not in sys.path:
    sys.path.append(str(cwd_scripts))

try:
    import idop_scaffolder
except ImportError:
    idop_scaffolder = None

# Initialize FastMCP Server
mcp = FastMCP("ccba-mcp-server")

LOG_DIR = Path(".md")
LOG_FILE = LOG_DIR / "mcp_server.log"


def log(msg: str):
    """Write timestamped message to .md/mcp_server.log."""
    try:
        if not LOG_DIR.exists():
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        pass


def _scan_output(result, guard):
    """Recursively scan output content for API keys."""
    if isinstance(result, str):
        guard.check_content(result)
    elif isinstance(result, (dict, list)):
        try:
            guard.check_content(json.dumps(result, ensure_ascii=False))
        except Exception:
            pass


def privacy_protected(func):
    """Decorator to scan all inputs and outputs for sensitive API keys."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        guard = PrivacyGuardHook()
        # Scan inputs
        for arg in args:
            if isinstance(arg, str):
                guard.check_content(arg)
        for _k, v in kwargs.items():
            if isinstance(v, str):
                guard.check_content(v)

        if inspect.iscoroutinefunction(func):

            async def async_wrapper():
                result = await func(*args, **kwargs)
                _scan_output(result, guard)
                return result

            return async_wrapper()
        else:
            result = func(*args, **kwargs)
            _scan_output(result, guard)
            return result

    return wrapper


# ==========================================
# 1. Nhóm Tra cứu & Hệ thống (System Tools)
# ==========================================


@mcp.tool()
@privacy_protected
def search_vietnamese_laws(query: str) -> str:
    """Tra cứu văn bản pháp luật xây dựng Việt Nam.

    Args:
        query: Từ khóa hoặc số hiệu văn bản (ví dụ: Nghị định 175, Luật Xây dựng)
    """
    log(f"Tool search_vietnamese_laws called with query='{query}'")
    query_lower = query.lower()
    if "175" in query_lower or "nghị định 175" in query_lower:
        return (
            "Nghị định 175/2024/NĐ-CP hướng dẫn Luật Nhà ở về cải tạo, xây dựng lại nhà chung cư.\n"
            "Điều 5: Nguyên tắc cải tạo, xây dựng lại nhà chung cư.\n"
            "Điều 12: Đăng ký lựa chọn chủ đầu tư dự án cải tạo xây dựng lại."
        )
    elif "luật xây dựng" in query_lower or "lxd" in query_lower:
        return (
            "Luật Xây dựng số 50/2014/QH13 và Luật sửa đổi bổ sung số 62/2020/QH14.\n"
            "Điều 54: Phân loại, phân cấp công trình xây dựng.\n"
            "Điều 82: Phê duyệt thiết kế kỹ thuật, thiết kế bản vẽ thi công."
        )
    else:
        return f"Không tìm thấy văn bản cụ thể cho từ khóa '{query}'. Vui lòng tra cứu tại CSDL Luật Việt Nam hoặc Thư viện Pháp luật."


@mcp.tool()
@privacy_protected
def get_gateway_status() -> str:
    """Kiểm tra trạng thái kết nối và danh sách model của AI Gateway."""
    log("Tool get_gateway_status called")
    from ccba_ai.client import AIClient

    try:
        client = AIClient()
        models = client.models()
        return f"AI Gateway Status: ONLINE.\nAvailable Models: {', '.join(models)}"
    except Exception as e:
        return f"AI Gateway Status: OFFLINE. Error details: {e}"


# ==========================================
# 2. Nhóm Plan Manager (Quản lý Kế hoạch)
# ==========================================


@mcp.tool()
@privacy_protected
def create_plan(title: str, phases: list[str]) -> dict:
    """Khởi tạo một kế hoạch triển khai (plan) mới với các phase cụ thể.

    Args:
        title: Tiêu đề của kế hoạch (ví dụ: 'Nâng cấp bảo mật hệ thống')
        phases: Danh sách tên các phase (ví dụ: ['Khảo sát', 'Phát triển', 'Kiểm thử'])
    """
    log(f"Tool create_plan called with title='{title}'")
    try:
        return services.create_plan(title, phases)
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
@privacy_protected
def update_phase_status(plan_file: str, phase_id: str, status: str) -> dict:
    """Cập nhật trạng thái của một phase trong kế hoạch triển khai.

    Args:
        plan_file: Đường dẫn tương đối hoặc tuyệt đối tới file plan.md
        phase_id: Mã định danh của phase (ví dụ: '01', '02')
        status: Trạng thái mới cần đặt ('pending', 'in-progress', 'completed')
    """
    log(f"Tool update_phase_status called for {plan_file} (Phase {phase_id} -> {status})")
    try:
        return services.update_phase_status(plan_file, phase_id, status)
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
@privacy_protected
def get_plan_status(plan_file: str) -> dict:
    """Truy xuất thông tin chi tiết và tiến độ của kế hoạch triển khai.

    Args:
        plan_file: Đường dẫn tương đối hoặc tuyệt đối tới file plan.md
    """
    log(f"Tool get_plan_status called for {plan_file}")
    try:
        return services.get_plan_status(plan_file)
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==========================================
# 3. Nhóm Team Coordinator (Điều phối multi-agent)
# ==========================================


@mcp.tool()
@privacy_protected
def list_tasks() -> list[dict]:
    """Lấy danh sách toàn bộ công việc (tasks) trong database điều phối multi-agent."""
    log("Tool list_tasks called")
    try:
        return services.load_tasks()
    except Exception as e:
        return [{"status": "error", "message": str(e)}]


@mcp.tool()
@privacy_protected
def add_task(name: str, owner: str | None = None) -> dict:
    """Thêm một công việc mới vào cơ sở dữ liệu điều phối multi-agent.

    Args:
        name: Tên của công việc (phải là duy nhất)
        owner: Tên Agent đảm nhận công việc (không bắt buộc)
    """
    log(f"Tool add_task called with name='{name}', owner='{owner}'")
    try:
        return services.add_task(name, owner)
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
@privacy_protected
def claim_task(name: str, owner: str) -> dict:
    """Đăng ký nhận một công việc để thực thi.

    Args:
        name: Tên công việc muốn nhận
        owner: Tên Agent thực thi nhận công việc
    """
    log(f"Tool claim_task called: {owner} claims '{name}'")
    try:
        return services.claim_task(name, owner)
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
@privacy_protected
def complete_task(name: str) -> dict:
    """Đánh dấu hoàn thành một công việc trong database điều phối.

    Args:
        name: Tên công việc đã hoàn thành
    """
    log(f"Tool complete_task called for '{name}'")
    try:
        return services.complete_task(name)
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==========================================
# 4. Nhóm SEO Audit (Rà soát SEO)
# ==========================================


@mcp.tool()
@privacy_protected
def run_seo_audit(file_path: str) -> dict:
    """Chạy phân tích kỹ thuật SEO cho tệp Markdown hoặc HTML.

    Args:
        file_path: Đường dẫn tương đối hoặc tuyệt đối tới file cần quét
    """
    log(f"Tool run_seo_audit called for {file_path}")
    try:
        return services.audit_file(file_path)
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==========================================
# 5. Nhóm IDOP Scaffolder (Khởi tạo dự án)
# ==========================================


@mcp.tool()
@privacy_protected
def scaffold_idop_project(
    output_dir: str = "./CDE",
    app_dir: str = "./src/idop-app",
    scaffold_cde: bool = True,
    scaffold_lists: bool = True,
    scaffold_workflows: bool = True,
    scaffold_react_app: bool = False,
    pack_solution: bool = False,
    solution_name: str = "IDOP_Solution",
) -> str:
    """Tạo nhanh bộ khung dự án CDE, SharePoint IDOP Lists, Power Automate, và React App.

    Args:
        output_dir: Đường dẫn thư mục đầu ra CDE (mặc định: './CDE')
        app_dir: Thư mục đầu ra cho React App (mặc định: './src/idop-app')
        scaffold_cde: Có tạo cấu trúc thư mục CDE không (mặc định: True)
        scaffold_lists: Có tạo schema SharePoint Lists không (mặc định: True)
        scaffold_workflows: Có tạo thiết kế Power Automate workflow không (mặc định: True)
        scaffold_react_app: Có khởi tạo dự án React/Vite/TS Code App không (mặc định: False)
        pack_solution: Có đóng gói SharePoint Solution zip không (mặc định: False)
        solution_name: Tên gói Solution (mặc định: 'IDOP_Solution')
    """
    log(
        f"Tool scaffold_idop_project called (output_dir={output_dir}, react_app={scaffold_react_app})"
    )
    if not idop_scaffolder:
        return "Error: idop_scaffolder module could not be imported. Ensure scripts/idop_scaffolder.py exists."

    out_abs = os.path.abspath(output_dir)
    app_abs = os.path.abspath(app_dir)

    reports = []
    try:
        if scaffold_cde:
            idop_scaffolder.scaffold_cde(out_abs)
            reports.append("- Cấu trúc thư mục CDE: Đã khởi tạo.")

        if scaffold_lists:
            idop_scaffolder.scaffold_lists(out_abs)
            reports.append("- SharePoint Lists Schema & PnP Scripts: Đã khởi tạo.")

        if scaffold_workflows:
            idop_scaffolder.scaffold_workflows(out_abs)
            reports.append("- Power Automate flow definitions: Đã khởi tạo.")

        if scaffold_react_app:
            idop_scaffolder.scaffold_app(app_abs)
            reports.append(f"- React + Vite + TS Code App: Đã khởi tạo tại {app_dir}")

        if pack_solution:
            idop_scaffolder.pack_solution(out_abs, solution_name, "CCBA", "ccba")
            reports.append(f"- Đóng gói Solution zip '{solution_name}': Đã hoàn thành.")

        return "Scaffolding dự án IDOP thành công:\n" + "\n".join(reports)
    except Exception as e:
        return f"Error executing scaffolding: {e}"


# ==========================================
# 6. Nhóm MD Convert (Chuyển đổi tài liệu)
# ==========================================


@mcp.tool()
@privacy_protected
async def convert_document(file_path: str, output_dir: str | None = None) -> dict:
    """Chuyển đổi tài liệu (PDF, DOCX) sang Markdown bằng bộ pipeline mdconverter.

    Args:
        file_path: Đường dẫn tệp tài liệu cần chuyển đổi (ví dụ: 'document.pdf')
        output_dir: Thư mục lưu file markdown kết quả (mặc định: cùng thư mục file gốc)
    """
    log(f"Tool convert_document called for {file_path}")
    try:
        from mdconverter.core.base import ConversionTool
        from mdconverter.core.pipeline import ConversionPipeline

        path = Path(file_path)
        if not path.is_absolute():
            path = Path.cwd() / path

        if not path.exists():
            return {"status": "error", "message": f"File {file_path} not found."}

        out_path = Path(output_dir) if output_dir else None
        if out_path and not out_path.is_absolute():
            out_path = Path.cwd() / out_path

        pipeline = ConversionPipeline(tool=ConversionTool.AUTO, output_dir=out_path)

        result = await pipeline.process_file(path)

        return {
            "status": "success" if result.is_success else "failed",
            "source_file": str(result.source_path),
            "output_file": str(result.output_path) if result.output_path else None,
            "tool_used": result.tool_used,
            "error_message": result.error_message,
            "metadata": result.metadata,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def main():
    """Main Entry Point for launching the FastMCP Server."""
    log("[ccba-mcp-server] Starting FastMCP Server...")
    mcp.run()


if __name__ == "__main__":
    main()
