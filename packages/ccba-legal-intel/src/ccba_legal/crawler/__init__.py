"""Modular Crawler package for CCBA Legal Intelligence Platform."""

from __future__ import annotations

from ccba_legal.cdp import (
    ChromeCDP,
    ChromeCDPError,
    HeadlessEnvironmentError,
    MockChromeCDP,
    _check_is_headless,
)
from ccba_legal.registry import load_relation_synonyms as _load_relation_synonyms
from ccba_legal.registry import resolve_project_root
from ccba_legal.session import (
    CookieVault,
    TVPLCrawlFailedException,
    TVPLRateLimiter,
    TVPLSessionMutex,
    check_vip_session_health,
    get_tvpl_credentials,
    log_session_audit,
    sleep_with_jitter,
    verify_tvpl_vip_status,
)
from ccba_legal.storage import (
    _check_aws_s3,
    _check_google_drive,
    _check_shared_drive,
)
from ccba_legal.tvpl_parser import (
    _derive_doc_slug,
    _extract_gazette_metadata,
    _parse_tvpl_date,
    get_crawled_doc_data,
    get_tvpl_metadata,
)

from .batch_crawler import TVPLBatchCrawler
from .engine import TVPLCrawler, TVPLCrawlerEngine
from .providers import (
    LegalDocProvider,
    MockLegalDocProvider,
    TVPLVIPDocProvider,
)
from .tier_downloader import (
    _cache_downloaded_file,
    _check_tier_1_local_and_cache,
    download_three_tier,
    load_relation_synonyms,
    trigger_download,
)

__all__ = [
    "LegalDocProvider",
    "MockLegalDocProvider",
    "TVPLVIPDocProvider",
    "TVPLCrawlerEngine",
    "TVPLCrawler",
    "TVPLBatchCrawler",
    "download_three_tier",
    "load_relation_synonyms",
    "trigger_download",
    "ChromeCDP",
    "ChromeCDPError",
    "HeadlessEnvironmentError",
    "MockChromeCDP",
    "CookieVault",
    "TVPLCrawlFailedException",
    "TVPLRateLimiter",
    "TVPLSessionMutex",
    "check_vip_session_health",
    "get_tvpl_credentials",
    "log_session_audit",
    "sleep_with_jitter",
    "verify_tvpl_vip_status",
    "get_crawled_doc_data",
    "get_tvpl_metadata",
    "resolve_project_root",
    "_check_is_headless",
    "_check_tier_1_local_and_cache",
    "_check_shared_drive",
    "_check_google_drive",
    "_check_aws_s3",
    "_cache_downloaded_file",
]
