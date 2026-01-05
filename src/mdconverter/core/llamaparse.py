"""
LlamaParse converter for scanned PDFs and complex documents.

Uses LlamaCloud API for high-quality parsing of scanned documents.
"""

import asyncio
import time
from pathlib import Path

import httpx

from mdconverter.config import settings
from mdconverter.core.base import BaseConverter, ConversionResult, ConversionStatus


class LlamaParseConverter(BaseConverter):
    """Document converter using LlamaParse API."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".epub"}

    def __init__(
        self,
        output_dir: Path | None = None,
        api_key: str | None = None,
    ) -> None:
        """Initialize LlamaParse converter."""
        super().__init__(output_dir)
        self.api_key = api_key or settings.llama_cloud_api_key
        self.base_url = "https://api.cloud.llamaindex.ai/api/parsing"
        self.client = httpx.AsyncClient(timeout=300)

    def supports(self, file_extension: str) -> bool:
        """Check if extension is supported."""
        return file_extension.lower() in self.SUPPORTED_EXTENSIONS

    def is_available(self) -> bool:
        """Check if LlamaParse API is available (API key configured)."""
        return bool(self.api_key)

    async def convert(self, source_path: Path) -> ConversionResult:
        """Convert document using LlamaParse API."""
        start_time = time.time()

        if not source_path.exists():
            return ConversionResult(
                source_path=source_path,
                status=ConversionStatus.FAILED,
                error_message=f"File not found: {source_path}",
            )

        if not self.is_available():
            return ConversionResult(
                source_path=source_path,
                status=ConversionStatus.FAILED,
                error_message="LlamaParse API key not configured",
            )

        if not self.supports(source_path.suffix):
            return ConversionResult(
                source_path=source_path,
                status=ConversionStatus.SKIPPED,
                error_message=f"Unsupported extension: {source_path.suffix}",
            )

        try:
            # Upload file
            job_id = await self._upload_file(source_path)
            if not job_id:
                return ConversionResult(
                    source_path=source_path,
                    status=ConversionStatus.FAILED,
                    tool_used="llamaparse",
                    duration_seconds=time.time() - start_time,
                    error_message="Failed to upload file",
                )

            # Wait for processing
            content = await self._wait_for_result(job_id)
            if not content:
                return ConversionResult(
                    source_path=source_path,
                    status=ConversionStatus.FAILED,
                    tool_used="llamaparse",
                    duration_seconds=time.time() - start_time,
                    error_message="Processing failed or timed out",
                )

            # Save result
            output_path = self.get_output_path(source_path)
            final_content = self.add_frontmatter(content, source_path, "llamaparse")
            output_path.write_text(final_content, encoding="utf-8")

            return ConversionResult(
                source_path=source_path,
                output_path=output_path,
                status=ConversionStatus.SUCCESS,
                tool_used="llamaparse",
                content=final_content,
                quality_score=self._calculate_quality(final_content),
                duration_seconds=time.time() - start_time,
            )

        except Exception as e:
            return ConversionResult(
                source_path=source_path,
                status=ConversionStatus.FAILED,
                tool_used="llamaparse",
                duration_seconds=time.time() - start_time,
                error_message=str(e),
            )

    async def _upload_file(self, file_path: Path) -> str | None:
        """Upload file to LlamaParse API and return job ID."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f)}
            data = {
                "result_type": "markdown",
                "parsing_instruction": "Extract all content as markdown. Preserve tables and structure.",
            }

            response = await self.client.post(
                f"{self.base_url}/upload",
                headers=headers,
                files=files,
                data=data,
            )

        if response.status_code != 200:
            return None

        result = response.json()
        job_id: str | None = result.get("id")
        return job_id

    async def _wait_for_result(self, job_id: str, max_wait: int = 300) -> str | None:
        """Wait for processing to complete and return markdown content."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        start = time.time()
        start = time.time()
        while time.time() - start < max_wait:
            response = await self.client.get(
                f"{self.base_url}/job/{job_id}",
                headers=headers,
            )

            if response.status_code != 200:
                return None

            result = response.json()
            status = result.get("status")

            if status == "SUCCESS":
                # Get the markdown result
                result_response = await self.client.get(
                    f"{self.base_url}/job/{job_id}/result/markdown",
                    headers=headers,
                )
                if result_response.status_code == 200:
                    markdown: str = result_response.json().get("markdown", "")
                    return markdown
                return None

            elif status == "ERROR":
                return None

            # Still processing, wait and retry
            await asyncio.sleep(2)

        return None  # Timeout

    def _calculate_quality(self, content: str) -> int:
        """Calculate quality score (0-100)."""
        score = 70  # LlamaParse base score is higher

        # Length bonus
        if len(content) > 1000:
            score += 5
        if len(content) > 5000:
            score += 5

        # Structure bonus
        if "##" in content:
            score += 5
        if "###" in content:
            score += 5

        # Table bonus
        if "|" in content and "-|-" in content:
            score += 5

        # Clean content bonus (no weird characters)
        weird_chars = sum(1 for c in content if ord(c) > 65535)
        if weird_chars == 0:
            score += 5

        return min(score, 100)
