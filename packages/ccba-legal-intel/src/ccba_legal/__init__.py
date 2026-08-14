"""ccba-legal-intel — Unified Legal Intelligence Platform.

Public Deep Seams:
    LegalIntelPipeline  — Crawl, parse, package legal documents end-to-end.
    LegalProcessor      — Legal advisory, conflict analysis, dispatch drafts.
    LegalSyncEngine     — Cloud sync of legal registry to NotebookLM.
"""

from .appendices import (
    AppendixSplitter,
    roman_to_decimal,
)
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
from .grounding import (
    LEGAL_DISCLAIMER,
    LegalGroundingGate,
    format_grounded_response,
    verify_legal_grounding,
)
from .monitor import TokenMonitor
from .registry import (
    LegalRegistryManager,
    format_citation,
    load_legal_registry,
    search_legal_registry,
)
from .sync import LegalSyncEngine, calculate_md5, calculate_sha256

__all__ = [
    # === Deep Seams (Advertised Public Interface) ===
    "LegalIntelPipeline",
    "LegalProcessor",
    "LegalProcessResult",
    "LegalSyncEngine",
    "LegalRegistryManager",
    "LegalGroundingGate",
    "AppendixSplitter",
    # === Domain Helper Seams ===
    "verify_legal_grounding",
    "format_grounded_response",
    "format_citation",
    "search_legal_registry",
    "load_legal_registry",
    "roman_to_decimal",
    "LEGAL_DISCLAIMER",
    # === Infrastructure & Cross-Package Facilities ===
    "TVPLSessionMutex",
    "MockChromeCDP",
    "CookieVault",
    "TokenMonitor",
    "ensure_chrome_cdp_port",
    "calculate_md5",
    "calculate_sha256",
]
