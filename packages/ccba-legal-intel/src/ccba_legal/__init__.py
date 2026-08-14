"""ccba-legal-intel — Unified Legal Intelligence Platform.

Public Deep Seams:
    LegalIntelPipeline  — Crawl, parse, package legal documents end-to-end.
    LegalProcessor      — Legal advisory, conflict analysis, dispatch drafts.
    LegalSyncEngine     — Cloud sync of legal registry to NotebookLM.
"""

from .coordinator import (
    LegalIntelPipeline,
    LegalProcessor,
    LegalProcessResult,
    ensure_chrome_cdp_port,
)
from .crawler import (
    CookieVault,
    MockChromeCDP,
    TVPLSessionMutex,
)
from .monitor import TokenMonitor
from .registry import LegalRegistryManager
from .sync import LegalSyncEngine, calculate_md5, calculate_sha256

__all__ = [
    # === Deep Seams (Advertised Public Interface) ===
    "LegalIntelPipeline",
    "LegalProcessor",
    "LegalProcessResult",
    "LegalSyncEngine",
    "LegalRegistryManager",
    # === Infrastructure & Cross-Package Facilities ===
    "TVPLSessionMutex",
    "MockChromeCDP",
    "CookieVault",
    "TokenMonitor",
    "ensure_chrome_cdp_port",
    "calculate_md5",
    "calculate_sha256",
]
