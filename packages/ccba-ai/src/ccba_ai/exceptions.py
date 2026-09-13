import json
from enum import Enum
from typing import Any


class CCBAErrorCode(str, Enum):
    """Danh mục mã lỗi tập trung toàn hệ thống CCBA Platform."""

    # Lỗi kết nối và xác thực AI Gateway
    GATEWAY_AUTH_FAIL = "GATEWAY_AUTH_FAIL"
    RATE_LIMIT_HIT = "RATE_LIMIT_HIT"

    # Lỗi file và định dạng
    PDF_CORRUPTED = "PDF_CORRUPTED"
    FILE_SYNC_DELAY = "FILE_SYNC_DELAY"

    # Lỗi dependency và platform
    MISSING_DEPENDENCY = "MISSING_DEPENDENCY"
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"
    LOGGER_WRITE_FAIL = "LOGGER_WRITE_FAIL"

    # Lỗi không xác định
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


def format_error_json(
    code: CCBAErrorCode, message: str, suggestion: str, extra: dict[str, Any] | None = None
) -> str:
    """Định dạng phản hồi lỗi thành chuỗi JSON có cấu trúc chuẩn cho LLM Agents.

    Args:
        code: Mã lỗi từ Enum CCBAErrorCode.
        message: Thông điệp lỗi chi tiết.
        suggestion: Gợi ý phục hồi (recovery suggestion) để Agent tự sửa lỗi.
        extra: Dữ liệu bổ sung nếu có.

    Returns:
        Chuỗi JSON được format đẹp.
    """
    error_data: dict[str, Any] = {
        "status": "error",
        "error_code": code.value,
        "message": message,
        "recovery_suggestion": suggestion,
    }
    if extra:
        error_data["extra"] = extra

    return json.dumps(error_data, ensure_ascii=False, indent=2)


class CCBABaseException(Exception):
    """Exception cơ sở của CCBA Platform, tự động định dạng thông báo lỗi thành JSON."""

    def __init__(
        self, code: CCBAErrorCode, message: str, suggestion: str, extra: dict[str, Any] | None = None
    ) -> None:
        self.code = code
        self.message = message
        self.suggestion = suggestion
        self.extra = extra

        # Tạo chuỗi JSON định dạng chuẩn
        self.json_output = format_error_json(code, message, suggestion, extra)
        super().__init__(self.json_output)

    def to_json(self) -> str:
        """Trả về chuỗi JSON biểu diễn lỗi."""
        return self.json_output
