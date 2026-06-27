"""
Lightweight MCP Server for ccba-agent-platform.
Exposes search_vietnamese_laws and get_gateway_status tools via JSON-RPC stdin/stdout.
"""

import sys
import json
import traceback
from pathlib import Path
from datetime import datetime

# Force UTF-8 on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

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


def search_vietnamese_laws(query: str) -> str:
    """Mock search for Vietnamese construction laws and regulations."""
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


def get_gateway_status() -> str:
    """Check AI Gateway (LiteLLM) health status and mock models list."""
    from ccba_ai.client import AIClient
    try:
        client = AIClient()
        models = client.models()
        return f"AI Gateway Status: ONLINE.\nAvailable Models: {', '.join(models)}"
    except Exception as e:
        return f"AI Gateway Status: OFFLINE. Error details: {e}"


def handle_request(req):
    req_id = req.get("id")
    method = req.get("method")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "ccba-mcp-server",
                    "version": "1.0.0"
                }
            },
            "id": req_id
        }
        
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {
                        "name": "search_vietnamese_laws",
                        "description": "Tra cứu văn bản pháp luật xây dựng Việt Nam",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Từ khóa tra cứu (ví dụ: Nghị định 175, Luật Xây dựng)"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_gateway_status",
                        "description": "Kiểm tra kết nối và danh sách model của AI Gateway",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            },
            "id": req_id
        }
        
    elif method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "search_vietnamese_laws":
                query = arguments.get("query", "")
                result_text = search_vietnamese_laws(query)
            elif tool_name == "get_gateway_status":
                result_text = get_gateway_status()
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{tool_name}' not found."
                    },
                    "id": req_id
                }
                
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                },
                "id": req_id
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error executing tool: {e}"
                },
                "id": req_id
            }
            
    # Default fallback for other protocol methods
    return {
        "jsonrpc": "2.0",
        "result": {},
        "id": req_id
    }


def main():
    """Main input loop reading from stdin."""
    log("[ccba-mcp-server] Starting server loop...")
    
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            log(f"[ccba-mcp-server] Received request: {line.strip()}")
            req = json.loads(line)
            resp = handle_request(req)
            log(f"[ccba-mcp-server] Sending response: {json.dumps(resp)}")
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            log(f"[ccba-mcp-server] Error in request loop: {e}")
            try:
                tb = traceback.format_exc()
                log(f"[ccba-mcp-server] Traceback:\n{tb}")
            except Exception:
                pass


if __name__ == "__main__":
    main()
