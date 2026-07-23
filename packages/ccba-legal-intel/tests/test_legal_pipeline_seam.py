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
