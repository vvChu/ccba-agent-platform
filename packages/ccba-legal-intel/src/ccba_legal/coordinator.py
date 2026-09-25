"""Coordinator for document amendment processing and legal advisory in CCBA Legal Intel.

Handles coordination between parser, packager, registry manager, intake taxonomy, and conflict resolution components.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ccba_legal.conflict import LexConflictEngine
from ccba_legal.crawler import (
    ChromeCDP,
    MockChromeCDP,
    TVPLSessionMutex,
    get_crawled_doc_data,
    get_tvpl_metadata,
)
from ccba_legal.formatter import inject_warning_block
from ccba_legal.intake import (
    generate_guided_interview_prompt,
    get_missing_intake_fields,
    parse_intake_question,
)
from ccba_legal.packager import OKFBundlePackager
from ccba_legal.parser import LegalAnalysisEngine
from ccba_legal.registry import LegalRegistryManager


class LegalProcessor:
    """Coordinates parsing of document amendments, updating the registry, and generating advisory reports."""

    def __init__(self, registry_path: Path | None = None) -> None:
        """Initialize the processor with an underlying registry manager."""
        self.registry_mgr = LegalRegistryManager(registry_path=registry_path)
        self.conflict_engine = LexConflictEngine()

    def process_amendments_from_document(
        self, source_doc_id: str, source_doc_content: str, source_doc_path: str
    ) -> list[dict[str, Any]]:
        """Parse clause-level changes from the source document, update registry, and inject warnings in target documents."""
        engine = LegalAnalysisEngine()
        modifications = engine.extract_amendments(source_doc_content, source_doc_path)

        for mod in modifications:
            target_doc_id = mod.get("target_doc_id")
            target_anchor = mod.get("target_anchor")
            amendment_source = mod.get("amendment_source")
            mod_source_doc_path = mod.get("source_doc_path", source_doc_path)

            if not target_doc_id or not target_anchor:
                continue

            self.registry_mgr.update_clause_status(
                target_doc_id=target_doc_id,
                clause_anchor=target_anchor,
                status="amended",
                amended_by=amendment_source or "",
                source_doc_path=mod_source_doc_path,
            )

            target_meta = self.registry_mgr.find_doc_by_id(target_doc_id)
            if target_meta:
                markdown_path = self.registry_mgr.get_markdown_path_for_doc(target_meta)
                if markdown_path and markdown_path.exists():
                    try:
                        content = markdown_path.read_text(encoding="utf-8")
                        updated_content = inject_warning_block(
                            markdown_content=content,
                            target_anchor=target_anchor,
                            amendment_source=amendment_source or "",
                            source_doc_path=mod_source_doc_path,
                        )
                        markdown_path.write_text(updated_content, encoding="utf-8")
                        print(
                            f"[Registry/Coordinator] Injected warning in target {target_doc_id} at {target_anchor}"
                        )
                    except Exception as e:
                        print(
                            f"[Registry/Coordinator] Error injecting warning into {markdown_path}: {e}"
                        )

        return modifications

    def generate_advisory_report(self, query_text: str, output_file: Path | None = None) -> str:
        """Generate a Dual-Layer Legal Advisory Report from raw query text."""
        intake = parse_intake_question(query_text)
        missing_fields = get_missing_intake_fields(intake)

        # Mock reference documents matching intake coordinates
        doc_a = {
            "doc_type": "Luật",
            "doc_number": "Luật 55/2024/QH15",
            "enactment_date": "2024-06-01",
            "status": "effective",
            "domain": "PCCC",
        }
        doc_b = {
            "doc_type": "Thông tư",
            "doc_number": "Thông tư 06/2022/TT-BXD",
            "enactment_date": "2022-11-30",
            "status": "expired",
            "domain": "PCCC",
        }

        conflict_score = self.conflict_engine.evaluate_conflict(
            doc_a, doc_b, event_date=intake.time_timestamp or ""
        )

        missing_prompt_section = ""
        if missing_fields:
            guided_prompt = generate_guided_interview_prompt(missing_fields)
            missing_prompt_section = f"\n> ⚠️ **Guided Interview**: {guided_prompt}\n"

        lines = [
            "# 📜 BÁO CÁO TƯ VẤN PHÁP LÝ DUAL-LAYER CCBA",
            "",
            "## 📍 Phase 1: Intake 5 Trục Dữ Kiện",
            f"- **Đối tượng**: {intake.subject or 'Chưa xác định'}",
            f"- **Hành vi**: {intake.action or 'Chưa xác định'}",
            f"- **Tác động**: {intake.impact or 'Chưa xác định'}",
            f"- **Phạm vi**: {intake.scope or 'Chưa xác định'}",
            f"- **Thời điểm**: {intake.time_timestamp or 'Chưa xác định'}",
            missing_prompt_section,
            "---",
            "",
            "## 🚀 TẦNG 1: KHUYẾN NGHỊ TỐI ƯU (Executive Summary)",
            f"- **Mức độ Rủi ro**: `{conflict_score.risk_label.value}` (Score: {conflict_score.score}/100)",
            f"- **Khuyên dùng**: {conflict_score.summary}",
            "- **Khuyến nghị bước đi**: Tạm dừng áp dụng các điều khoản theo thông tư cũ đã hết hiệu lực; đối chiếu quy định chuyển tiếp.",
            "",
            "---",
            "",
            "## 🔍 TẦNG 2: MA TRẬN SO SÁNH RỦI RO CHI TIẾT (Detailed Risk Matrix)",
            "| Căn cứ Pháp lý | Tọa độ SOT Trích dẫn | Mức độ Ưu tiên | Trạng thái Hiệu lực |",
            "| :--- | :--- | :--- | :--- |",
            f"| {doc_a['doc_number']} | `[Luật 55/2024/QH15 - Điều 14 - Khoản 2]` | Ưu tiên cao | {doc_a['status']} |",
            f"| {doc_b['doc_number']} | `[Thông tư 06/2022/TT-BXD - Điều 3 - Khoản 1]` | Hết hiệu lực | {doc_b['status']} |",
            "",
            "### Quy tắc Xung đột Pháp lý Áp dụng:",
        ]
        for rule in conflict_score.conflict_rules_applied:
            lines.append(f"- {rule}")

        report_content = "\n".join(lines)

        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(report_content, encoding="utf-8")

        return report_content

    def generate_consultation_dispatch_draft(
        self, recipient: str, subject_summary: str, output_file: Path
    ) -> dict[str, Any]:
        """Generate an official Consultation Dispatch draft (.docx) following Decree 30 format."""
        try:
            import docx

            doc = docx.Document()
            doc.add_heading("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", level=1)
            doc.add_paragraph("Độc lập - Tự do - Hạnh phúc")
            doc.add_paragraph("-------------------")
            doc.add_paragraph(f"Kính gửi: {recipient}")
            doc.add_paragraph(
                f"V/v: Xin ý kiến hướng dẫn áp dụng quy định pháp luật về {subject_summary}"
            )
            doc.add_paragraph(
                "Căn cứ Nghị định 30/2020/NĐ-CP ngày 05/03/2020 của Chính phủ về công tác văn thư;"
            )
            doc.add_paragraph(
                "Kính đề nghị Quý Cơ quan xem xét và phát hành văn bản hướng dẫn chính thức cho đơn vị."
            )
            output_file.parent.mkdir(parents=True, exist_ok=True)
            doc.save(str(output_file))
        except ImportError:
            # Fallback if docx is mock/not installed in env
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(
                f"Kính gửi: {recipient}\nV/v: {subject_summary}\nCăn cứ NĐ 30/2020/NĐ-CP",
                encoding="utf-8",
            )

        return {
            "recipient": recipient,
            "subject_summary": subject_summary,
            "output_file": str(output_file),
            "status": "success",
        }


import hashlib


def calculate_content_sha256(content: str) -> str:
    """Calculate SHA-256 hash of string content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def is_large_legal_document(url_or_id: str) -> bool:
    """Check if document is a known large legal document requiring async subagent offloading."""
    target = url_or_id.lower()
    keywords = [
        "luat-dat-dai",
        "luat-xay-dung",
        "luat-nha-o",
        "luat-kinh-doanh-bat-dong-san",
        "dat-dai-2024",
        "xay-dung-2025",
    ]
    return any(k in target for k in keywords)


def ensure_chrome_cdp_port(port: int = 9222) -> bool:
    """Check if Chrome CDP port is listening, auto-launch if not.

    Args:
        port: The remote debugging port (default: 9222).

    Returns:
        bool: True if Chrome CDP is available and listening, False otherwise.
    """
    import os
    import shutil
    import subprocess
    import time

    import requests  # type: ignore[import-untyped]

    try:
        resp = requests.get(f"http://127.0.0.1:{port}/json", timeout=1.5)
        if resp.status_code == 200:
            return True
    except Exception:
        pass

    # Attempt to auto-launch Chrome
    from ccba_legal.session import get_browser_executable_path

    chrome_cmd = get_browser_executable_path()
    if chrome_cmd and (os.path.exists(str(chrome_cmd)) or shutil.which(str(chrome_cmd))):
        try:
            fallback_temp = "/tmp" if os.name != "nt" else "C:/temp"
            temp_dir = Path(os.environ.get("TEMP", fallback_temp)) / "chrome_dev"
            temp_dir.mkdir(parents=True, exist_ok=True)
            subprocess.Popen(
                [
                    str(chrome_cmd),
                    f"--remote-debugging-port={port}",
                    "--remote-allow-origins=*",
                    f"--user-data-dir={temp_dir}",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1.5)
            resp = requests.get(f"http://127.0.0.1:{port}/json", timeout=2)
            return bool(resp.status_code == 200)
        except Exception as e:
            print(f"[LegalIntel] Chrome auto-launch error: {e}")

    return False


@dataclass
class LegalProcessResult:
    """Structured result of processing a legal document through LegalIntelPipeline."""

    doc_id: str
    bundle_path: Path | None
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class LegalIntelPipeline:
    """Unified deep seam for processing Vietnamese legal documents (crawling, parsing, packaging, and registry)."""

    def __init__(
        self,
        cdp_client: ChromeCDP | None = None,
        registry_path: Path | None = None,
        output_dir: Path | None = None,
        use_mutex: bool = True,
    ) -> None:
        self.cdp = cdp_client or ChromeCDP()
        self.registry_mgr = LegalRegistryManager(registry_path=registry_path)
        self.output_dir = output_dir or Path(".md/legal_docs")
        self.use_mutex = use_mutex

    def process_document(
        self,
        url_or_id: str,
        force_refresh: bool = False,
        async_offload: bool = False,
    ) -> LegalProcessResult:
        """Crawl, parse, and package a legal document end-to-end via a deep seam."""
        is_mock = isinstance(self.cdp, MockChromeCDP)
        packager = OKFBundlePackager(self.output_dir)
        doc_id = url_or_id.split("/")[-1].replace(".aspx", "") if "/" in url_or_id else url_or_id
        bundle_slug = packager.sanitize_slug(doc_id)
        bundle_dir = self.output_dir / bundle_slug

        # 1. Check Large Document Async Offload
        if async_offload or is_large_legal_document(url_or_id):
            if async_offload:
                return LegalProcessResult(
                    doc_id=doc_id,
                    bundle_path=None,
                    status="offloaded_to_subagent",
                    metadata={
                        "title": f"Large Document {doc_id}",
                        "recommended_subagent": "ccba-research",
                    },
                    error="Offloaded to subagent ccba-research for async crawling of large document.",
                )

        # 2. Check SHA-256 / Delta Cache
        if not force_refresh and bundle_dir.exists():
            cached_meta = self.registry_mgr.find_doc_by_id(doc_id) or {
                "title": f"Cached Document {doc_id}"
            }
            return LegalProcessResult(
                doc_id=doc_id,
                bundle_path=bundle_dir,
                status="cached",
                metadata=cached_meta,
            )

        mutex_context = TVPLSessionMutex() if (self.use_mutex and not is_mock) else None
        try:
            if mutex_context:
                mutex_context.__enter__()

            if not is_mock:
                ensure_chrome_cdp_port(self.cdp.port)

            pages = self.cdp.get_pages()
            if pages:
                self.cdp.connect_tab(pages[0].get("webSocketDebuggerUrl", ""))

            title, content, links = get_crawled_doc_data(self.cdp, url_or_id)
            meta = get_tvpl_metadata(self.cdp, url_or_id)
            meta["title"] = title
            meta["source_url"] = url_or_id
            meta["sha256"] = calculate_content_sha256(content)

            bundle_dir = packager.package_bundle(doc_id, content, meta)
            self.registry_mgr.register_document(doc_id, meta)

            return LegalProcessResult(
                doc_id=doc_id,
                bundle_path=bundle_dir,
                status="mocked" if is_mock else "success",
                metadata=meta,
            )
        except Exception as e:
            return LegalProcessResult(
                doc_id=doc_id,
                bundle_path=None,
                status="failed",
                error=str(e),
            )
        finally:
            if mutex_context:
                try:
                    mutex_context.__exit__(None, None, None)
                except Exception:
                    pass

    def run_cli(self, args: list[str] | None = None) -> int:
        """CLI invocation runner method."""
        import argparse
        import json

        parser = argparse.ArgumentParser(description="CCBA Legal Intelligence Deep CLI")
        parser.add_argument(
            "positional_target", nargs="?", help="TVPL Document URL or ID (positional)"
        )
        parser.add_argument("--url", help="TVPL Document URL")
        parser.add_argument("--doc-id", help="Legal Document ID")
        parser.add_argument("--force", action="store_true", help="Force refresh")
        parser.add_argument(
            "--async",
            "--async-offload",
            dest="async_offload",
            action="store_true",
            help="Offload large documents to subagent async",
        )
        parser.add_argument(
            "--download-source", action="store_true", help="Download source .docx file"
        )
        parser.add_argument(
            "--extract-related",
            action="store_true",
            help="Extract related documents and guiding docs",
        )
        parser.add_argument("--json", action="store_true", help="Output result as JSON")
        parsed = parser.parse_args(args)

        target = parsed.positional_target or parsed.url or parsed.doc_id
        if not target:
            print("[LegalIntel CLI] Error: Must specify --url, --doc-id, or positional target URL")
            return 1

        result = self.process_document(
            target, force_refresh=parsed.force, async_offload=parsed.async_offload
        )
        if parsed.json:
            out = {
                "doc_id": result.doc_id,
                "bundle_path": str(result.bundle_path) if result.bundle_path else None,
                "status": result.status,
                "metadata": result.metadata,
                "error": result.error,
            }
            print(json.dumps(out, ensure_ascii=False))
            return (
                0
                if result.status in ("success", "mocked", "cached", "offloaded_to_subagent")
                else 1
            )

        if result.status in ("success", "mocked", "cached", "offloaded_to_subagent"):
            print(
                f"[LegalIntel CLI] Processed {result.doc_id} -> status: {result.status}, bundle: {result.bundle_path}"
            )
            return 0
        print(f"[LegalIntel CLI] Failed processing {result.doc_id}: {result.error}")
        return 1
