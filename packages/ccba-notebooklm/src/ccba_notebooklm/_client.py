"""
CCBA NotebookLM Client and Auth configuration.
Handles Google accounts cookie authentication and mock adapter fallbacks.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    from notebooklm import NotebookLMClient
    from notebooklm.exceptions import NetworkError
    from notebooklm.rpc.types import (
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
    QuizQuantity = QuizDifficulty = SlideDeckFormat = SlideDeckLength = None
    ReportFormat = InfographicOrientation = InfographicDetail = InfographicStyle = None
    VideoFormat = VideoStyle = None
    NetworkError = Exception


# ---------------------------------------------------------------------------
# Mock Adapter Classes
# Provides in-memory implementation of the Google NotebookLM Cloud RPC endpoints.
# ---------------------------------------------------------------------------


class MockNotebook:
    def __init__(self, id: str, title: str) -> None:
        self.id = id
        self.title = title


class MockSource:
    def __init__(self, id: str, title: str, url: str = "") -> None:
        self.id = id
        self.title = title
        self.url = url
        self.content = "Mock Source Content"


class MockTask:
    def __init__(self, task_id: str) -> None:
        self.task_id = task_id


class MockMindmapResult:
    def __init__(self, mind_map: dict[str, Any]) -> None:
        self.mind_map = mind_map


class MockAccountTier:
    def __init__(self, tier: str = "standard", plan_name: str = "Standard Plan") -> None:
        self.tier = tier
        self.plan_name = plan_name


class MockNotebooksService:
    async def list(self) -> list[MockNotebook]:
        return [
            MockNotebook("nb-mock-1", "CAP_Spoke_Default"),
            MockNotebook("nb-mock-2", "CAP_Spoke_Testing"),
        ]

    async def create(self, title: str) -> MockNotebook:
        return MockNotebook("nb-mock-new", title)

    async def delete(self, notebook_id: str) -> None:
        pass


class MockSourcesService:
    async def list(self, notebook_id: str) -> list[MockSource]:
        return [
            MockSource("src-mock-1", "TCVN 2622-1995.pdf"),
            MockSource("src-mock-2", "Nghi_dinh_06_2021.md", url="https://vbpl.vn/ND_06_2021"),
        ]

    async def add_file(self, notebook_id: str, path: str) -> MockSource:
        p = Path(path)
        return MockSource("src-mock-file", p.name)

    async def add_url(self, notebook_id: str, url: str, wait: bool = True) -> MockSource:
        return MockSource("src-mock-url", url, url=url)

    async def delete(self, notebook_id: str, source_id: str) -> None:
        pass


class MockArtifactsService:
    async def generate_audio(self, notebook_id: str) -> MockTask:
        return MockTask("task-audio-1")

    async def download_audio(self, notebook_id: str, output_path: str) -> str:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"mock_audio_content")
        return str(p.absolute())

    async def generate_quiz(
        self, notebook_id: str, source_ids: list[str], quantity: Any, difficulty: Any
    ) -> MockTask:
        return MockTask("task-quiz-1")

    async def download_quiz(self, notebook_id: str, output_path: str, output_format: str = "json") -> str:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps([{"question": "Mock Question", "options": ["A", "B"], "answer": "A"}]),
            encoding="utf-8",
        )
        return str(p.absolute())

    async def generate_slide_deck(
        self,
        notebook_id: str,
        source_ids: list[str],
        language: str,
        slide_format: Any,
        slide_length: Any,
    ) -> MockTask:
        return MockTask("task-slides-1")

    async def download_slide_deck(
        self, notebook_id: str, output_path: str, output_format: str = "pdf"
    ) -> str:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"mock_pdf_slides_content")
        return str(p.absolute())

    async def generate_mind_map(self, notebook_id: str, source_ids: list[str]) -> MockMindmapResult:
        return MockMindmapResult({"root": "Mock Mindmap"})

    async def download_mind_map(self, notebook_id: str, output_path: str) -> str:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"root": "Mock Mindmap"}), encoding="utf-8")
        return str(p.absolute())

    async def generate_infographic(
        self, notebook_id: str, source_ids: list[str], orientation: Any, detail_level: Any, style: Any
    ) -> MockTask:
        return MockTask("task-info-1")

    async def download_infographic(self, notebook_id: str, output_path: str) -> str:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"mock_pdf_infographic_content")
        return str(p.absolute())

    async def generate_study_guide(self, notebook_id: str, source_ids: list[str]) -> MockTask:
        return MockTask("task-guide-1")

    async def download_report(self, notebook_id: str, output_path: str) -> str:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# Mock Study Guide\nContent here.", encoding="utf-8")
        return str(p.absolute())

    async def generate_data_table(
        self, notebook_id: str, source_ids: list[str], instructions: str
    ) -> MockTask:
        return MockTask("task-table-1")

    async def download_data_table(self, notebook_id: str, output_path: str) -> str:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("Col1,Col2\nVal1,Val2", encoding="utf-8")
        return str(p.absolute())

    async def generate_flashcards(
        self, notebook_id: str, source_ids: list[str], quantity: Any, difficulty: Any
    ) -> MockTask:
        return MockTask("task-flash-1")

    async def download_flashcards(
        self, notebook_id: str, output_path: str, output_format: str = "json"
    ) -> str:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps([{"front": "Front", "back": "Back"}]), encoding="utf-8")
        return str(p.absolute())

    async def generate_report(
        self, notebook_id: str, source_ids: list[str], report_format: Any, extra_instructions: str
    ) -> MockTask:
        return MockTask("task-report-1")

    async def generate_video(
        self, notebook_id: str, source_ids: list[str], video_format: Any, video_style: Any
    ) -> MockTask:
        return MockTask("task-video-1")

    async def download_video(self, notebook_id: str, output_path: str) -> str:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"mock_video_mp4_content")
        return str(p.absolute())

    async def wait_for_completion(self, notebook_id: str, task_id: str) -> None:
        pass


class MockSettingsService:
    async def get_account_tier(self) -> MockAccountTier:
        return MockAccountTier()


class MockNotebookLMClientAdapter:
    """Mock adapter mimicking a real NotebookLMClient."""

    def __init__(self) -> None:
        self.notebooks = MockNotebooksService()
        self.sources = MockSourcesService()
        self.artifacts = MockArtifactsService()
        self.settings = MockSettingsService()

    async def __aenter__(self) -> MockNotebookLMClientAdapter:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# Deep Seam Wrapper
# ---------------------------------------------------------------------------


class CCBANotebookLMClient:
    """Giao diện seam sâu bọc NotebookLMClient để hỗ trợ mock adapter và auto auth."""

    def __init__(self, client: Any, use_mock: bool = False) -> None:
        self._client = client
        self.use_mock = use_mock

    async def __aenter__(self) -> Any:
        return await self._client.__aenter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    @classmethod
    def from_storage(cls, path: str | None = None, use_mock: bool = False) -> CCBANotebookLMClient:
        """Khởi tạo client từ storage. Chuyển đổi sang mock adapter nếu cần thiết."""
        if use_mock:
            logger.info("Kích hoạt Mock NotebookLM Client (Không phát hiện AUTH cookie).")
            return cls(MockNotebookLMClientAdapter(), use_mock=True)

        if not HAS_NOTEBOOKLM or NotebookLMClient is None:
            logger.warning("Không tìm thấy thư viện notebooklm-py. Tự động chuyển sang Mock Client.")
            return cls(MockNotebookLMClientAdapter(), use_mock=True)

        try:
            real_client = (
                NotebookLMClient.from_storage(path=path) if path else NotebookLMClient.from_storage()
            )
            return cls(real_client, use_mock=False)
        except Exception as e:
            logger.warning("Khởi tạo Real Client lỗi (%s). Tự động chuyển sang Mock Client.", e)
            return cls(MockNotebookLMClientAdapter(), use_mock=True)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_temp_storage_path() -> Path:
    """Đường dẫn lưu trữ file Playwright cookie tạm thời."""
    scratch_dir = Path(".md/scratch")
    scratch_dir.mkdir(parents=True, exist_ok=True)
    return scratch_dir / "notebooklm_cookies.json"


def inject_auth_cookies() -> str | None:
    """Đọc biến môi trường và tạo file cookie tạm thời cho Playwright.

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
                    cookies.append(
                        {
                            "name": name,
                            "value": value,
                            "domain": ".google.com",
                            "path": "/",
                            "expires": -1,
                            "httpOnly": True,
                            "secure": True,
                            "sameSite": "Lax",
                        }
                    )
            storage_state = {"cookies": cookies, "origins": []}
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(storage_state, f, ensure_ascii=False, indent=2)
            print("[Info] Đã chuyển đổi và nạp auth từ NOTEBOOKLM_SESSION_COOKIE.")
            return str(temp_path.absolute())
        except Exception as e:
            print(f"[Warn] Lỗi phân tích NOTEBOOKLM_SESSION_COOKIE: {e}", file=sys.stderr)

    return None


def get_client() -> CCBANotebookLMClient:
    """Tạo đối tượng client với các thiết lập auth phù hợp."""
    cookie_path = inject_auth_cookies()
    env_cookie = os.environ.get("NOTEBOOKLM_SESSION_COOKIE")
    env_json = os.environ.get("NOTEBOOKLM_COOKIES_JSON")
    use_mock = not (env_cookie or env_json)

    return CCBANotebookLMClient.from_storage(path=cookie_path, use_mock=use_mock)


async def check_auth() -> int:
    """Kiểm tra trạng thái đăng nhập NotebookLM."""
    client_instance = get_client()
    if client_instance.use_mock:
        print("[Info] SUCCESS: Chế độ giả lập (Mock Mode) hoạt động bình thường!")
        print("[Info] Subscription Tier: mock (Mock Standard Plan)")
        return 0

    if not HAS_NOTEBOOKLM:
        print(
            "ERROR: Thư viện 'notebooklm-py' chưa được cài đặt. Vui lòng chạy: pip install notebooklm-py",
            file=sys.stderr,
        )
        return 1

    try:
        async with client_instance as client:
            await client.notebooks.list()
            print("SUCCESS: Kết nối và xác thực thành công với Google NotebookLM Cloud!")
            tier = await client.settings.get_account_tier()
            print(f"[Info] Subscription Tier: {tier.tier} ({tier.plan_name or 'Standard Plan'})")
            return 0
    except Exception as e:
        print(
            f"ERROR_AUTH: Session cookie đã hết hạn hoặc không tồn tại. Vui lòng chạy 'python -m notebooklm login' trên trình duyệt để đăng nhập lại. Chi tiết: {e}",
            file=sys.stderr,
        )
        return 2
