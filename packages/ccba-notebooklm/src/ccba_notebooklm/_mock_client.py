from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
    def __init__(self, client: MockNotebookLMClientAdapter) -> None:
        self._client = client

    async def list(self) -> list[MockNotebook]:
        return [MockNotebook(nb["id"], nb["title"]) for nb in self._client._notebooks]

    async def create(self, title: str) -> MockNotebook:
        nb_id = f"nb-mock-{len(self._client._notebooks) + 1}"
        new_nb = {"id": nb_id, "title": title}
        self._client._notebooks.append(new_nb)
        self._client._sources[nb_id] = []
        return MockNotebook(nb_id, title)

    async def delete(self, notebook_id: str) -> None:
        self._client._notebooks = [nb for nb in self._client._notebooks if nb["id"] != notebook_id]
        self._client._sources.pop(notebook_id, None)


class MockSourcesService:
    def __init__(self, client: MockNotebookLMClientAdapter) -> None:
        self._client = client

    async def list(self, notebook_id: str) -> list[MockSource]:
        srcs = self._client._sources.get(notebook_id, [])
        return [MockSource(s["id"], s["title"], s["url"]) for s in srcs]

    async def add_file(self, notebook_id: str, path: str) -> MockSource:
        p = Path(path)
        src_id = "src-mock-file"
        new_src = {"id": src_id, "title": p.name, "url": ""}
        if notebook_id not in self._client._sources:
            self._client._sources[notebook_id] = []
        if not any(s["id"] == src_id for s in self._client._sources[notebook_id]):
            self._client._sources[notebook_id].append(new_src)
        return MockSource(src_id, p.name)

    async def add_url(self, notebook_id: str, url: str, wait: bool = True) -> MockSource:
        src_id = "src-mock-url"
        new_src = {"id": src_id, "title": url, "url": url}
        if notebook_id not in self._client._sources:
            self._client._sources[notebook_id] = []
        if not any(s["id"] == src_id for s in self._client._sources[notebook_id]):
            self._client._sources[notebook_id].append(new_src)
        return MockSource(src_id, url, url=url)

    async def delete(self, notebook_id: str, source_id: str) -> None:
        if notebook_id in self._client._sources:
            self._client._sources[notebook_id] = [
                s for s in self._client._sources[notebook_id] if s["id"] != source_id
            ]


class MockArtifactsService:
    def __init__(self, client: MockNotebookLMClientAdapter) -> None:
        self._client = client

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

    async def download_quiz(
        self, notebook_id: str, output_path: str, output_format: str = "json"
    ) -> str:
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
        self,
        notebook_id: str,
        source_ids: list[str],
        orientation: Any,
        detail_level: Any,
        style: Any,
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
    def __init__(self, client: MockNotebookLMClientAdapter) -> None:
        self._client = client

    async def get_account_tier(self) -> MockAccountTier:
        return MockAccountTier()

    async def get_account_limits(self) -> Any:
        class MockLimits:
            source_limit = 50

        return MockLimits()


class MockChatResult:
    def __init__(self, answer: str) -> None:
        self.answer = answer


class MockChatService:
    def __init__(self, client: MockNotebookLMClientAdapter) -> None:
        self._client = client

    async def ask(self, notebook_id: str, question: str, source_ids: list[str]) -> MockChatResult:
        return MockChatResult(f"Mock Answer for: {question}")


class MockNotebookLMClientAdapter:
    """Mock adapter mimicking a real NotebookLMClient with in-memory state."""

    def __init__(self) -> None:
        self._notebooks = [
            {"id": "nb-mock-1", "title": "CAP_Spoke_Default"},
            {"id": "nb-mock-2", "title": "CAP_Spoke_Testing"},
        ]
        self._sources = {
            "nb-mock-1": [
                {"id": "src-mock-1", "title": "TCVN 2622-1995.pdf", "url": ""},
                {
                    "id": "src-mock-2",
                    "title": "Nghi_dinh_06_2021.md",
                    "url": "https://vbpl.vn/ND_06_2021",
                },
            ],
            "nb-mock-2": [],
        }
        self.notebooks = MockNotebooksService(self)
        self.sources = MockSourcesService(self)
        self.artifacts = MockArtifactsService(self)
        self.settings = MockSettingsService(self)
        self.chat = MockChatService(self)

    async def __aenter__(self) -> MockNotebookLMClientAdapter:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass
