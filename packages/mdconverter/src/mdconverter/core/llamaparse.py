"""
LlamaParse converter for scanned PDFs and complex documents.

Uses LlamaCloud API for high-quality parsing of scanned documents.
"""

import asyncio
import time
from pathlib import Path

import httpx

from mdconverter.config import get_settings
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
        self.api_key = api_key or get_settings().llama_cloud_api_key
        self.base_url = "https://api.cloud.llamaindex.ai/api/parsing"

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
            async with httpx.AsyncClient(timeout=300) as client:
                # Upload file
                job_id = await self._upload_file(client, source_path)
                if not job_id:
                    return ConversionResult(
                        source_path=source_path,
                        status=ConversionStatus.FAILED,
                        tool_used="llamaparse",
                        duration_seconds=time.time() - start_time,
                        error_message="Failed to upload file",
                    )

                # Wait for processing
                content = await self._wait_for_result(client, job_id)
            if not content:
                return ConversionResult(
                    source_path=source_path,
                    status=ConversionStatus.FAILED,
                    tool_used="llamaparse",
                    duration_seconds=time.time() - start_time,
                    error_message="Processing failed or timed out",
                )

            # H1: Extract VN Legal metadata if applicable
            metadata = self._extract_metadata(content, source_path)

            # Save result
            output_path = self.get_output_path(source_path)
            final_content = self.add_frontmatter(
                content, source_path, "llamaparse", metadata=metadata
            )
            await asyncio.to_thread(output_path.write_text, final_content, "utf-8")

            return ConversionResult(
                source_path=source_path,
                output_path=output_path,
                status=ConversionStatus.SUCCESS,
                tool_used="llamaparse",
                content=final_content,
                quality_score=self._calculate_quality(final_content, base_score=70),
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

    async def _upload_file(self, client: httpx.AsyncClient, file_path: Path) -> str | None:
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

            response = await client.post(
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

    async def _wait_for_result(self, client: httpx.AsyncClient, job_id: str, max_wait: int = 300) -> str | None:
        """Wait for processing to complete and return markdown content."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        start = time.time()
        poll_interval = 2.0  # Start with 2 seconds
        max_poll_interval = 10.0  # Cap at 10 seconds
        while time.time() - start < max_wait:
            response = await client.get(
                f"{self.base_url}/job/{job_id}",
                headers=headers,
            )

            if response.status_code != 200:
                return None

            result = response.json()
            status = result.get("status")

            if status == "SUCCESS":
                # Get the markdown result
                result_response = await client.get(
                    f"{self.base_url}/job/{job_id}/result/markdown",
                    headers=headers,
                )
                if result_response.status_code == 200:
                    markdown: str = result_response.json().get("markdown", "")
                    return markdown
                return None

            elif status == "ERROR":
                return None

            # Still processing, wait with exponential backoff
            await asyncio.sleep(poll_interval)
            poll_interval = min(poll_interval * 1.5, max_poll_interval)

        return None  # Timeout

    @staticmethod
    def _extract_metadata(content: str, source_path: Path) -> dict[str, str] | None:
        """Extract VN Legal metadata if applicable, else return None."""
        from mdconverter.plugins.vn_legal.detector import is_legal_document
        from mdconverter.plugins.vn_legal.metadata import extract_vn_legal_metadata

        if is_legal_document(content):
            return extract_vn_legal_metadata(content, source_path)
        return None
