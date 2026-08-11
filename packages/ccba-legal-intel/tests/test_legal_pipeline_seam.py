"""Unit tests for LegalIntelPipeline deep seam."""

from pathlib import Path

from ccba_legal.coordinator import LegalIntelPipeline, LegalProcessResult
from ccba_legal.crawler import MockChromeCDP


def test_legal_intel_pipeline_initialization() -> None:
    """Verify LegalIntelPipeline can be initialized with custom CDP client."""
    mock_cdp = MockChromeCDP()
    pipeline = LegalIntelPipeline(cdp_client=mock_cdp)

    assert pipeline.cdp == mock_cdp


def test_legal_intel_pipeline_process_document_mock(tmp_path: Path) -> None:
    """Verify process_document executes end-to-end via LegalIntelPipeline using MockChromeCDP."""
    mock_cdp = MockChromeCDP()
    mock_cdp.connect_tab("ws://127.0.0.1:9222/mock")

    pipeline = LegalIntelPipeline(
        cdp_client=mock_cdp,
        output_dir=tmp_path,
        use_mutex=False,  # Bypass lock file during unit test
    )

    url = "https://thuvienphapluat.vn/van-ban/PCCC/Luat-Phong-chay-va-chua-chay-2024-55-2024-QH15-590000.aspx"
    result = pipeline.process_document(url_or_id=url, force_refresh=True)

    assert isinstance(result, LegalProcessResult)
    assert result.status in ("success", "mocked")
    assert result.doc_id != ""
    assert result.bundle_path is not None or result.metadata != {}


def test_ensure_chrome_cdp_port_helper() -> None:
    """Verify ensure_chrome_cdp_port checks or auto-detects Chrome CDP port."""
    from ccba_legal.coordinator import ensure_chrome_cdp_port

    # Port 9222 check should return a boolean status without raising exception
    res = ensure_chrome_cdp_port(9222)
    assert isinstance(res, bool)


def test_legal_intel_pipeline_process_document_full_mock(tmp_path: Path) -> None:
    """Verify process_document with MockChromeCDP processes metadata and creates OKF bundle."""
    mock_cdp = MockChromeCDP()
    mock_cdp.connect_tab("ws://127.0.0.1:9222/mock")
    mock_cdp.set_mock_metadata(
        {
            "document_number": "55/2024/QH15",
            "type": "Luật",
            "issued_by": "Quốc hội",
            "signer": "Trần Thanh Mẫn",
            "issued_date": "2024-11-27",
            "status": "Còn hiệu lực",
            "relations": {},
        }
    )
    mock_cdp.set_mock_body_text("Nội dung chi tiết Luật Phòng cháy và chữa cháy 2024")

    pipeline = LegalIntelPipeline(
        cdp_client=mock_cdp,
        output_dir=tmp_path,
        use_mutex=False,
    )

    url = "https://thuvienphapluat.vn/van-ban/PCCC/Luat-55-2024-QH15.aspx"
    result = pipeline.process_document(url_or_id=url)

    assert result.status in ("success", "mocked")
    assert result.doc_id == "Luat-55-2024-QH15"
    assert result.bundle_path is not None
    assert result.error is None


def test_legal_intel_pipeline_error_handling(tmp_path: Path) -> None:
    """Verify process_document captures exceptions gracefully into LegalProcessResult."""

    class ErrorCDP(MockChromeCDP):
        def navigate(self, url: str) -> None:
            raise RuntimeError("Simulated network navigation failure")

    error_cdp = ErrorCDP()
    error_cdp.connect_tab("ws://127.0.0.1:9222/mock")

    pipeline = LegalIntelPipeline(
        cdp_client=error_cdp,
        output_dir=tmp_path,
        use_mutex=False,
    )

    url = "https://thuvienphapluat.vn/van-ban/PCCC/Luat-Fail-Test.aspx"
    result = pipeline.process_document(url_or_id=url)

    assert result.status == "failed"
    assert result.bundle_path is None
    assert result.error is not None
    assert "Simulated network navigation failure" in result.error


def test_legal_intel_pipeline_sha256_delta_caching(tmp_path: Path) -> None:
    """Verify process_document returns cached result on subsequent calls when force_refresh is False."""
    mock_cdp = MockChromeCDP()
    mock_cdp.connect_tab("ws://127.0.0.1:9222/mock")

    pipeline = LegalIntelPipeline(
        cdp_client=mock_cdp,
        output_dir=tmp_path,
        use_mutex=False,
    )

    url = "https://thuvienphapluat.vn/van-ban/PCCC/Luat-Cache-Test-55-2024.aspx"

    # First call: process and create bundle
    res1 = pipeline.process_document(url_or_id=url, force_refresh=True)
    assert res1.status in ("success", "mocked")
    assert res1.bundle_path is not None

    # Second call without force_refresh: should hit cache
    res2 = pipeline.process_document(url_or_id=url, force_refresh=False)
    assert res2.status == "cached"
    assert res2.bundle_path == res1.bundle_path


def test_legal_intel_pipeline_large_doc_async_offloading(tmp_path: Path) -> None:
    """Verify process_document detects large documents and offloads to ccba-research subagent when requested."""
    mock_cdp = MockChromeCDP()
    mock_cdp.connect_tab("ws://127.0.0.1:9222/mock")

    pipeline = LegalIntelPipeline(
        cdp_client=mock_cdp,
        output_dir=tmp_path,
        use_mutex=False,
    )

    large_url = (
        "https://thuvienphapluat.vn/van-ban/Bat-dong-san/Luat-Dat-dai-2024-31-2024-QH15.aspx"
    )
    result = pipeline.process_document(url_or_id=large_url, async_offload=True)

    assert result.status == "offloaded_to_subagent"
    assert "ccba-research" in (result.error or "") or "ccba-research" in str(result.metadata)


def test_legal_intel_pipeline_run_cli(tmp_path: Path) -> None:
    """Verify run_cli parses positional and optional flags correctly."""
    mock_cdp = MockChromeCDP()
    mock_cdp.connect_tab("ws://127.0.0.1:9222/mock")

    pipeline = LegalIntelPipeline(
        cdp_client=mock_cdp,
        output_dir=tmp_path,
        use_mutex=False,
    )

    # 1. Missing target should return 1
    assert pipeline.run_cli([]) == 1

    # 2. Positional argument
    url = "https://thuvienphapluat.vn/van-ban/PCCC/Luat-CLI-Positional-Test.aspx"
    assert pipeline.run_cli([url, "--force"]) == 0

    # 3. Named option --url
    assert pipeline.run_cli(["--url", url, "--force"]) == 0
