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
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])

# Attempt import of FastMCP
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:

    class _DummyFastMCP:
        """Fallback mock when 'mcp' optional package is not installed."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def tool(self, *args: Any, **kwargs: Any) -> Callable[[F], F]:
            def decorator(func: F) -> F:
                return func

            return decorator

        def run(self, *args: Any, **kwargs: Any) -> None:
            print(
                "[Error] Anthropic 'mcp' package is not installed. Run 'uv sync' or 'pip install mcp' first.",
                file=sys.stderr,
            )
            sys.exit(1)

    FastMCP = _DummyFastMCP  # type: ignore[misc,assignment]

# Import services from ccba_ai
# Expose scripts folder for idop_scaffolder import
import importlib.util

from ccba_ai import services
from ccba_ai.hooks import PrivacyGuardHook

idop_scaffolder = None
cwd_scripts = Path.cwd() / "scripts" / "idop_scaffolder.py"
if cwd_scripts.exists():
    try:
        spec = importlib.util.spec_from_file_location("idop_scaffolder", cwd_scripts)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            idop_scaffolder = module
    except Exception:
        pass

# Initialize FastMCP Server
mcp = FastMCP("ccba-mcp-server")

LOG_DIR = Path(".md") / "logs"
LOG_FILE = LOG_DIR / "mcp_server.log"


def log(msg: str) -> None:
    """Write timestamped message to .md/logs/mcp_server.log."""
    try:
        if not LOG_DIR.exists():
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        pass


def _scan_output(result: Any, guard: PrivacyGuardHook) -> None:
    """Recursively scan output content for API keys."""
    if isinstance(result, str):
        guard.check_content(result)
    elif isinstance(result, (dict, list)):
        try:
            guard.check_content(json.dumps(result, ensure_ascii=False))
        except Exception:
            pass


def privacy_protected(func: F) -> F:
    """Decorator to scan all inputs and outputs for sensitive API keys."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        guard = PrivacyGuardHook()
        # Scan inputs
        for arg in args:
            if isinstance(arg, str):
                guard.check_content(arg)
        for _k, v in kwargs.items():
            if isinstance(v, str):
                guard.check_content(v)

        if inspect.iscoroutinefunction(func):

            async def async_wrapper() -> Any:
                result = await func(*args, **kwargs)
                _scan_output(result, guard)
                return result

            return async_wrapper()
        else:
            result = func(*args, **kwargs)
            _scan_output(result, guard)
            return result

    return cast(F, wrapper)


# ==========================================
# 1. Nhóm Tra cứu & Hệ thống (System Tools)
# ==========================================


@mcp.tool()
@privacy_protected
def search_vietnamese_laws(query: str) -> str:
    """Tra cứu văn bản pháp luật xây dựng Việt Nam qua LegalKnowledgeEngine (ADR 0035, ADR 0050, RULE-3.1).

    Args:
        query: Từ khóa hoặc số hiệu văn bản (ví dụ: Nghị định 217, Luật Xây dựng 2025, QCVN 06:2022)
    """
    log(f"Tool search_vietnamese_laws called with query='{query}'")
    if not query or not query.strip():
        return "Vui lòng nhập từ khóa hoặc số hiệu văn bản pháp luật cần tra cứu."
    try:
        from ccba_legal import LegalKnowledgeEngine

        engine = LegalKnowledgeEngine()
        results = engine.search(query, top_k=5)
        if not results:
            return f"Không tìm thấy văn bản pháp luật phù hợp với từ khóa '{query}' trong CSDL Master Registry."

        lines = [f"Kết quả tra cứu pháp luật cho từ khóa '{query}':"]
        for idx, doc in enumerate(results, 1):
            doc_id = doc.get("id") or doc.get("document_number", "")
            title = doc.get("title", "")
            status = doc.get("status", "ACTIVE")
            is_superseded = doc.get("is_superseded", False)
            lines.append(f"{idx}. [{status}] {doc_id}: {title}")
            if is_superseded:
                replacement = doc.get("suggested_replacement", "N/A")
                lines.append(
                    f"   ⚠️ CẢNH BÁO RULE-3.1: Văn bản đã hết hiệu lực. Thay thế bởi: {replacement}"
                )
            if doc.get("lifecycle_warning"):
                lines.append(f"   ⚠️ Lưu ý: {doc.get('lifecycle_warning')}")
            if doc.get("notes"):
                lines.append(f"   Ghi chú: {doc.get('notes')}")
        return "\n".join(lines)
    except ImportError:
        return "Lỗi: Thư viện ccba-legal-intel chưa được cài đặt để tra cứu văn bản pháp luật."
    except Exception as e:
        return f"Lỗi khi tra cứu văn bản pháp luật: {e}"


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
def create_plan(title: str, phases: list[str]) -> dict[str, Any]:
    """Khởi tạo một kế hoạch triển khai (plan) mới với các phase cụ thể.

    Args:
        title: Tiêu đề của kế hoạch (ví dụ: 'Nâng cấp bảo mật hệ thống')
        phases: Danh sách tên các phase (ví dụ: ['Khảo sát', 'Phát triển', 'Kiểm thử'])
    """
    log(f"Tool create_plan called with title='{title}'")
    try:
        return cast(dict[str, Any], services.create_plan(title, phases))
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
@privacy_protected
def update_phase_status(plan_file: str, phase_id: str, status: str) -> dict[str, Any]:
    """Cập nhật trạng thái của một phase trong kế hoạch triển khai.

    Args:
        plan_file: Đường dẫn tương đối hoặc tuyệt đối tới file plan.md
        phase_id: Mã định danh của phase (ví dụ: '01', '02')
        status: Trạng thái mới cần đặt ('pending', 'in-progress', 'completed')
    """
    log(f"Tool update_phase_status called for {plan_file} (Phase {phase_id} -> {status})")
    try:
        return cast(dict[str, Any], services.update_phase_status(plan_file, phase_id, status))
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
@privacy_protected
def get_plan_status(plan_file: str) -> dict[str, Any]:
    """Truy xuất thông tin chi tiết và tiến độ của kế hoạch triển khai.

    Args:
        plan_file: Đường dẫn tương đối hoặc tuyệt đối tới file plan.md
    """
    log(f"Tool get_plan_status called for {plan_file}")
    try:
        return cast(dict[str, Any], services.get_plan_status(plan_file))
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==========================================
# 3. Nhóm Team Coordinator (Điều phối multi-agent)
# ==========================================


@mcp.tool()
@privacy_protected
def list_tasks() -> list[dict[str, Any]]:
    """Lấy danh sách toàn bộ công việc (tasks) trong database điều phối multi-agent."""
    log("Tool list_tasks called")
    try:
        return cast(list[dict[str, Any]], services.load_tasks())
    except Exception as e:
        return [{"status": "error", "message": str(e)}]


@mcp.tool()
@privacy_protected
def add_task(name: str, owner: str | None = None) -> dict[str, Any]:
    """Thêm một công việc mới vào cơ sở dữ liệu điều phối multi-agent.

    Args:
        name: Tên của công việc (phải là duy nhất)
        owner: Tên Agent đảm nhận công việc (không bắt buộc)
    """
    log(f"Tool add_task called with name='{name}', owner='{owner}'")
    try:
        return cast(dict[str, Any], services.add_task(name, owner))
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
@privacy_protected
def claim_task(name: str, owner: str) -> dict[str, Any]:
    """Đăng ký nhận một công việc để thực thi.

    Args:
        name: Tên công việc muốn nhận
        owner: Tên Agent thực thi nhận công việc
    """
    log(f"Tool claim_task called: {owner} claims '{name}'")
    try:
        return cast(dict[str, Any], services.claim_task(name, owner))
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
@privacy_protected
def complete_task(name: str) -> dict[str, Any]:
    """Đánh dấu hoàn thành một công việc trong database điều phối.

    Args:
        name: Tên công việc đã hoàn thành
    """
    log(f"Tool complete_task called for '{name}'")
    try:
        return cast(dict[str, Any], services.complete_task(name))
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==========================================
# 4. Nhóm SEO Audit (Rà soát SEO)
# ==========================================


@mcp.tool()
@privacy_protected
def run_seo_audit(file_path: str) -> dict[str, Any]:
    """Chạy phân tích kỹ thuật SEO cho tệp Markdown hoặc HTML.

    Args:
        file_path: Đường dẫn tương đối hoặc tuyệt đối tới file cần quét
    """
    log(f"Tool run_seo_audit called for {file_path}")
    try:
        return cast(dict[str, Any], services.audit_file(file_path))
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
async def convert_document(file_path: str, output_dir: str | None = None) -> dict[str, Any]:
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


# =============================================================================
# Conditional Legal RAG Tool — ADR 0044 (Tier 0 ← Tier 1 dynamic import)
# Only registered when ccba-legal-intel is installed.
# =============================================================================
try:
    from ccba_legal.federated_rag import query_ground_truth as _query_gt

    @mcp.tool()
    @privacy_protected
    def query_legal_ground_truth(
        query: str,
        domain: str | None = None,
        top_k: int = 5,
    ) -> str:
        """Tra cứu read-only kho tri thức pháp lý OKF v2.4 (HITL — ADR 0010).

        Tool này chỉ trả về kết quả tra cứu. Không tự động kích hoạt
        hành động tiếp theo. Khi cần đối chiếu sâu, hãy đề xuất
        lệnh /ccba-research cho người dùng xác nhận.

        Args:
            query: Câu truy vấn pháp lý (ví dụ: "thẩm định PCCC").
            domain: Bộ lọc lĩnh vực (ví dụ: "PCCC", "xây dựng").
            top_k: Số lượng kết quả tối đa trả về.

        Returns:
            Kết quả tra cứu dạng JSON string.
        """
        import json as _json

        results = _query_gt(query, domain=domain, top_k=top_k)
        return _json.dumps(results, ensure_ascii=False, indent=2)
except ImportError:
    pass  # ccba-legal-intel not installed — tool not registered


def _configure_utf8_streams() -> None:
    """Configure UTF-8 output streams on Windows.

    Must only be called at process entrypoint (main), never at module import
    time, to avoid breaking Pytest stream capture.
    """
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def main() -> None:
    """Main Entry Point for launching the FastMCP Server."""
    _configure_utf8_streams()
    log("[ccba-mcp-server] Starting FastMCP Server...")
    mcp.run()


if __name__ == "__main__":
    main()
