"""LegalSyncEngine Facade Class (ADR 0050)."""

from __future__ import annotations

import logging
import os
import re
import shutil
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from ccba_legal.registry import LegalRegistryManager, load_legal_registry
from ccba_legal.sync.cdp_discovery import (
    download_via_cdp_or_client,
    search_thuvienphapluat_via_cdp,
)
from ccba_legal.sync.drive_client import (
    _import_google_api,
    get_drive_service,
)
from ccba_legal.sync.drive_uploader import (
    clean_google_drive_folder,
    upload_to_google_drive,
)
from ccba_legal.sync.notebooklm_sync import (
    _import_notebooklm_client,
    sync_registry_to_notebooklm,
)
from ccba_legal.sync.utils import (
    _is_link_or_junction,
    calculate_md5,
    calculate_sha256,
    is_port_open,
    safe_copy2,
    safe_remove,
)

logger = logging.getLogger(__name__)

DEFAULT_DRIVE_FOLDER = "1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2"
RAW_GITHUB_BASE = os.environ.get(
    "CCBA_LEGAL_CDN_URL", "https://raw.githubusercontent.com/vvChu/ccba-legal-knowledge/main"
)
DEFAULT_NETWORK_TIMEOUT = 5.0
DEFAULT_USER_AGENT = "CCBA-Legal-ThinClient/1.0"
CORE_BUNDLE_FILES = ("document_normative.md", "clauses.json", "metadata.yaml")


def _fetch_remote_file_atomic(
    url: str,
    dest_path: Path,
    timeout: float = DEFAULT_NETWORK_TIMEOUT,
    user_agent: str = DEFAULT_USER_AGENT,
) -> bool:
    """Download a remote file atomically via temporary file and replace (Grok C1/C2).

    Args:
        url: Remote HTTP/HTTPS URL.
        dest_path: Destination local file path.
        timeout: Network timeout in seconds.
        user_agent: Custom User-Agent header.

    Returns:
        True if successfully downloaded and placed, False otherwise.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dest_path.with_suffix(f"{dest_path.suffix}.tmp_{os.getpid()}")
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if getattr(resp, "status", 200) != 200:
                return False
            data = resp.read()
        tmp_path.write_bytes(data)
        tmp_path.replace(dest_path)
        return True
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        logger.debug("Failed to stream %s to %s: %s", url, dest_path, e)
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        return False


class LegalSyncEngine:
    """Deep module coordinating local legal registry sync, Chrome CDP discovery, cloud drives and Spoke distribution (ADR 0050)."""

    def __init__(self, project_root: Path | None = None) -> None:
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = project_root

    def calculate_file_hashes(self, file_path: Path) -> dict[str, str]:
        """Compute both MD5 and SHA256 for a target file."""
        return {
            "md5": calculate_md5(file_path),
            "sha256": calculate_sha256(file_path),
        }

    def verify_environment(self) -> dict[str, bool]:
        """Verify environment dependencies."""
        google_available, *_ = _import_google_api()
        try:
            from ccba_legal.crawler import ChromeCDP

            has_cdp = ChromeCDP is not None
        except ImportError:
            has_cdp = False

        return {
            "google_api": google_available,
            "chrome_cdp": has_cdp,
            "chrome_port_open": is_port_open(9222),
            "notebooklm": _import_notebooklm_client() is not None,
        }

    def search_thuvienphapluat_via_cdp(self, query: str) -> str | None:
        """Search for a legal document URL on thuvienphapluat.vn via Google Search using Chrome CDP."""
        return search_thuvienphapluat_via_cdp(query)

    def download_via_cdp_or_client(self, url: str, dest_path: Path) -> bool:
        """Download a file using Chrome CDP (preferred) or urllib fallback."""
        return download_via_cdp_or_client(url, dest_path)

    def get_drive_service(self) -> Any:
        """Initialize Drive API service using personal token or ADC fallback."""
        return get_drive_service()

    def clean_google_drive_folder(self, folder_id: str) -> None:
        """Delete all files in a Google Drive folder for a clean slate."""
        clean_google_drive_folder(folder_id)

    def upload_to_google_drive(
        self, file_path: Path, folder_id: str, target_name: str
    ) -> str | None:
        """Upload a file to Google Drive with deduplication support."""
        return upload_to_google_drive(file_path, folder_id, target_name)

    async def sync_registry_to_notebooklm(
        self,
        registry_path: Path,
        sources_reg_path: Path,
        notebook_id: str,
        use_drive: bool,
        drive_folder_id: str,
        download_pdf: bool = False,
        clean_drive: bool = False,
    ) -> None:
        """Execute the full sync pipeline from local registry to NotebookLM Cloud."""
        await sync_registry_to_notebooklm(
            registry_path=registry_path,
            sources_reg_path=sources_reg_path,
            notebook_id=notebook_id,
            use_drive=use_drive,
            drive_folder_id=drive_folder_id,
            download_pdf=download_pdf,
            clean_drive=clean_drive,
        )

    def _find_corpus_in_hub_registry(self, hub_p: Path) -> Path | None:
        """Searches spoke_registry files under hub_p for the canonical legal knowledge corpus."""
        for reg_name in ("spoke_registry_decrypted.yaml", "spoke_registry.yaml"):
            spoke_reg = hub_p / ".md" / "data" / reg_name
            if not spoke_reg.is_file():
                continue
            try:
                reg_content = yaml.safe_load(spoke_reg.read_text(encoding="utf-8")) or {}
                for sp in reg_content.get("spokes", []):
                    if not isinstance(sp, dict):
                        continue
                    sp_name = str(sp.get("name", "")).lower()
                    if "legal-knowledge" in sp_name or sp.get("archetype") == "knowledge_corpus":
                        p_str = sp.get("path")
                        if p_str:
                            cand = Path(p_str)
                            if cand.exists() and (
                                (cand / "legal_docs").exists()
                                or (cand / ".md" / "data" / "legal_registry.yaml").exists()
                            ):
                                return cand.resolve()
            except Exception:
                pass
        return None

    def _resolve_hub_from_workspace_ctx(self) -> Path | None:
        """Extracts hub_path from .md/workspace_context.yaml or .agents/workspace_context.yaml."""
        for ctx_name in (".md/workspace_context.yaml", ".agents/workspace_context.yaml"):
            local_ctx = self.project_root / ctx_name
            if not local_ctx.is_file():
                continue
            try:
                ctx_data = yaml.safe_load(local_ctx.read_text(encoding="utf-8")) or {}
                proj_data = ctx_data.get("project", {}) if isinstance(ctx_data, dict) else {}
                hub_val = ctx_data.get("hub_path") or (
                    proj_data.get("hub_path") if isinstance(proj_data, dict) else None
                )
                hub_str = ""
                if isinstance(hub_val, dict):
                    os_k = "windows" if os.name == "nt" else "linux"
                    hub_str = str(hub_val.get(os_k) or hub_val.get("posix") or "")
                elif isinstance(hub_val, str):
                    hub_str = hub_val
                is_win_drive = bool(re.match(r"^[A-Za-z]:[\\/]", hub_str))
                if hub_str and not (os.name != "nt" and is_win_drive):
                    hub_p = Path(hub_str)
                    return hub_p if hub_p.is_absolute() else (self.project_root / hub_p).resolve()
            except (OSError, yaml.YAMLError) as e:
                logger.debug("Lỗi khi đọc file cấu hình hub/workspace: %s", e)
        return None

    def _find_corpus_in_default_candidates(self) -> Path | None:
        """Checks standard sibling and home directory locations for ccba-legal-knowledge."""
        candidates = [
            self.project_root.parent / "ccba-legal-knowledge",
            self.project_root / ".." / "ccba-legal-knowledge",
            Path("D:/GitHubProjects/ccba-legal-knowledge"),  # ccba:allow-machine-path
            Path("C:/GitHubProjects/ccba-legal-knowledge"),  # ccba:allow-machine-path
            Path.home() / "GitHubProjects" / "ccba-legal-knowledge",
            Path.home() / "ccba-legal-knowledge",
        ]
        for cand in candidates:
            try:
                resolved = cand.resolve()
                if resolved.exists() and (
                    (resolved / "legal_docs").exists()
                    or (resolved / ".md" / "data" / "legal_registry.yaml").exists()
                ):
                    return resolved
            except OSError:
                continue
        if (self.project_root / "legal_docs").exists():
            return self.project_root.resolve()
        return None

    def find_local_knowledge_corpus(self, explicit_path: Path | None = None) -> Path | None:
        """Discover the canonical Knowledge Corpus Spoke (ccba-legal-knowledge) on local machine (ADR 0050)."""
        if explicit_path and explicit_path.exists():
            return explicit_path.resolve()

        env_path = os.environ.get("CCBA_LEGAL_KNOWLEDGE_PATH") or os.environ.get(
            "CCBA_LEGAL_CORPUS_PATH"
        )
        if env_path and Path(env_path).exists():
            p = Path(env_path)
            if (p / "legal_docs").exists():
                return p.resolve()
            return p.parent.resolve() if p.name == "legal_docs" else p.resolve()

        for env_hub_key in ("CCBA_HUB_PATH", "HUB_PATH"):
            env_hub = os.environ.get(env_hub_key)
            if env_hub:
                found = self._find_corpus_in_hub_registry(Path(env_hub).resolve())
                if found:
                    return found

        ctx_hub = self._resolve_hub_from_workspace_ctx()
        if ctx_hub:
            found = self._find_corpus_in_hub_registry(ctx_hub)
            if found:
                return found

        return self._find_corpus_in_default_candidates()

    def _resolve_sync_dest_root(self, target_dir: Path | str | None) -> Path:
        """Resolves destination root directory for OKF bundles."""
        if target_dir:
            return Path(target_dir)
        is_master = self.project_root.name.lower() == "ccba-legal-knowledge"
        if not is_master:
            for ctx_dir in (self.project_root / ".agents", self.project_root / ".md"):
                ctx_path = ctx_dir / "workspace_context.yaml"
                if ctx_path.is_file():
                    try:
                        ctx = yaml.safe_load(ctx_path.read_text(encoding="utf-8")) or {}
                        proj = ctx.get("project", {}) if isinstance(ctx, dict) else {}
                        if isinstance(proj, dict) and (
                            str(proj.get("name", "")).lower() == "ccba-legal-knowledge"
                            or proj.get("is_master") is True
                        ):
                            is_master = True
                            break
                    except Exception:
                        pass
        return (
            (self.project_root / "legal_docs")
            if is_master
            else (self.project_root / ".md" / "legal_docs")
        )

    def _copy_local_corpus_bundles(
        self, corpus_path: Path, dest_root: Path, doc_ids: list[str] | None
    ) -> list[str]:
        """Copies matching OKF bundles from local corpus_path into dest_root."""
        synced_bundles: list[str] = []
        source_legal_docs = corpus_path / "legal_docs"
        if not source_legal_docs.exists():
            return synced_bundles
        norm_ids = [re.sub(r"[\s\-_/.]+", "", d.lower()) for d in (doc_ids or [])]
        for cat in ("01_vbpl", "02_qcvn", "03_tcvn", "04_appendices"):
            cat_dir = source_legal_docs / cat
            if not cat_dir.exists():
                continue
            for bundle_dir in sorted(cat_dir.iterdir()):
                if not bundle_dir.is_dir():
                    continue
                slug = bundle_dir.name
                if norm_ids:
                    norm_slug = re.sub(r"[\s\-_/.]+", "", slug.lower())
                    if not any(nid in norm_slug for nid in norm_ids):
                        continue
                target_bundle = dest_root / cat / slug
                target_bundle.mkdir(parents=True, exist_ok=True)
                for item in bundle_dir.iterdir():
                    dest_item = target_bundle / item.name
                    if item.is_dir():
                        if dest_item.is_file() or _is_link_or_junction(dest_item):
                            safe_remove(dest_item)
                        shutil.copytree(
                            item, dest_item, dirs_exist_ok=True, copy_function=safe_copy2
                        )
                    else:
                        if dest_item.is_dir():
                            safe_remove(dest_item)
                        safe_copy2(item, dest_item)
                synced_bundles.append(f"{cat}/{slug}")
        return synced_bundles

    def _merge_local_corpus_registry(
        self, corpus_path: Path, update_registry: bool
    ) -> dict[str, int]:
        """Merges master legal_registry.yaml from local corpus_path when update_registry is True."""
        summary: dict[str, int] = {"updated": 0, "added": 0, "preserved": 0}
        if not update_registry:
            return summary
        master_reg_path = corpus_path / ".md" / "data" / "legal_registry.yaml"
        if not master_reg_path.exists():
            master_reg_path = corpus_path / "legal_registry.yaml"
        if master_reg_path.exists():
            master_data = load_legal_registry(master_reg_path)
            local_mgr = LegalRegistryManager(
                self.project_root / ".md" / "data" / "legal_registry.yaml"
            )
            summary = local_mgr.merge_with_master_registry(master_data, backup=True)
        return summary

    def pull_latest_okf_bundles(
        self,
        target_dir: Path | str | None = None,
        doc_ids: list[str] | None = None,
        source_corpus_dir: Path | str | None = None,
        update_registry: bool = True,
        pull_assets: bool = True,
    ) -> dict[str, Any]:
        """Pull and synchronize OKF v2.4 legal bundles into Spoke with Non-Destructive Registry Merge (ADR 0050)."""
        dest_root = self._resolve_sync_dest_root(target_dir)
        explicit = Path(source_corpus_dir) if source_corpus_dir else None
        corpus_path = self.find_local_knowledge_corpus(explicit)

        if corpus_path:
            try:
                if (corpus_path / "legal_docs").resolve() == dest_root.resolve():
                    return {
                        "status": "success",
                        "mode": "master_corpus_preserved",
                        "tier": "tier_1_local_corpus",
                        "source": str(corpus_path),
                        "target": str(dest_root),
                        "bundles_synced": [],
                        "registry_merge": {"updated": 0, "added": 0, "preserved": 0},
                    }
            except OSError:
                pass

        if pull_assets:
            dest_root.mkdir(parents=True, exist_ok=True)
        if not corpus_path:
            return self._sync_from_remote_cdn(
                dest_root=dest_root,
                doc_ids=doc_ids,
                update_registry=update_registry,
                pull_assets=pull_assets,
            )

        synced_bundles = (
            self._copy_local_corpus_bundles(corpus_path, dest_root, doc_ids) if pull_assets else []
        )
        registry_merge_summary = self._merge_local_corpus_registry(corpus_path, update_registry)
        return {
            "status": "success",
            "tier": "tier_1_local_corpus",
            "source": str(corpus_path),
            "target": str(dest_root),
            "bundles_synced": synced_bundles,
            "registry_merge": registry_merge_summary,
        }

    def _fetch_remote_registry(
        self, update_registry: bool
    ) -> tuple[dict[str, Any], dict[str, int]]:
        """Fetch remote master registry from CDN and merge if requested."""
        remote_reg_url = f"{RAW_GITHUB_BASE}/.md/data/legal_registry.yaml"
        tmp_remote_reg = self.project_root / ".md" / "data" / ".remote_registry.tmp.yaml"
        reg_downloaded = _fetch_remote_file_atomic(remote_reg_url, tmp_remote_reg)
        if not reg_downloaded:
            remote_reg_url = f"{RAW_GITHUB_BASE}/legal_registry.yaml"
            reg_downloaded = _fetch_remote_file_atomic(remote_reg_url, tmp_remote_reg)

        if not reg_downloaded:
            raise urllib.error.URLError(
                "Unable to fetch canonical legal_registry.yaml from remote CDN"
            )

        master_data = load_legal_registry(tmp_remote_reg)
        tmp_remote_reg.unlink(missing_ok=True)

        merge_summary = {"updated": 0, "added": 0, "preserved": 0}
        if update_registry:
            local_mgr = LegalRegistryManager(
                self.project_root / ".md" / "data" / "legal_registry.yaml"
            )
            merge_summary = local_mgr.merge_with_master_registry(master_data, backup=True)
        return master_data, merge_summary

    def _resolve_remote_sync_items(
        self, master_data: dict[str, Any], doc_ids: list[str] | None
    ) -> list[dict[str, str]]:
        """Resolve and filter document items from registry according to doc_ids."""
        items: list[dict[str, str]] = []
        categories_map = {
            "laws": "01_vbpl",
            "decrees": "01_vbpl",
            "circulars": "01_vbpl",
            "decisions": "01_vbpl",
            "qcvn": "02_qcvn",
            "tcvn": "03_tcvn",
            "standards": "03_tcvn",
            "appendices": "04_appendices",
            "documents": "01_vbpl",
        }
        norm_ids = [re.sub(r"[\s\-_/.]+", "", d.lower()) for d in (doc_ids or [])]

        for sec, cat in categories_map.items():
            docs = master_data.get(sec, [])
            if not isinstance(docs, list):
                continue
            for d in docs:
                if not isinstance(d, dict):
                    continue
                slug = str(d.get("slug") or d.get("id") or "").strip().lower()
                doc_num = str(d.get("document_number") or "").strip().lower()
                if not slug:
                    continue
                if norm_ids:
                    clean_slug = re.sub(r"[\s\-_/.]+", "", slug)
                    clean_num = re.sub(r"[\s\-_/.]+", "", doc_num)
                    if not any(
                        nid in clean_slug or (clean_num and nid in clean_num) for nid in norm_ids
                    ):
                        continue
                items.append({"category": cat, "slug": slug})

        items.sort(key=lambda x: (x["category"], x["slug"]))
        return items

    def _stream_single_bundle(
        self, cat: str, slug: str, dest_root: Path, pull_assets: bool
    ) -> bool:
        """Stream a single OKF bundle from remote CDN with cache checking."""
        target_bundle = dest_root / cat / slug
        if (target_bundle / "metadata.yaml").is_file() and (
            target_bundle / "clauses.json"
        ).is_file():
            return True

        if not pull_assets:
            return False

        target_bundle.mkdir(parents=True, exist_ok=True)
        all_core_ok = True
        for fname in CORE_BUNDLE_FILES:
            file_url = f"{RAW_GITHUB_BASE}/legal_docs/{cat}/{slug}/{fname}"
            ok = _fetch_remote_file_atomic(file_url, target_bundle / fname)
            if not ok and fname in ("document_normative.md", "metadata.yaml"):
                all_core_ok = False

        meta_path = target_bundle / "metadata.yaml"
        if meta_path.is_file():
            try:
                with open(meta_path, encoding="utf-8") as mf:
                    mdata = yaml.safe_load(mf) or {}
                for tbl in mdata.get("tables", []):
                    if isinstance(tbl, str) and tbl.endswith(".md"):
                        tbl_url = f"{RAW_GITHUB_BASE}/legal_docs/{cat}/{slug}/tables/{tbl}"
                        _fetch_remote_file_atomic(tbl_url, target_bundle / "tables" / tbl)
            except Exception:
                pass
        return all_core_ok

    def _sync_from_remote_cdn(
        self,
        dest_root: Path,
        doc_ids: list[str] | None = None,
        update_registry: bool = True,
        pull_assets: bool = True,
    ) -> dict[str, Any]:
        """Tier 2: Remote Streaming Sync for Thin Clients via GitHub Raw CDN (ADR-0026 / ADR-0050)."""
        synced_bundles: list[str] = []
        try:
            master_data, reg_summary = self._fetch_remote_registry(update_registry)
            items = self._resolve_remote_sync_items(master_data, doc_ids)

            for item in items:
                cat, slug = item["category"], item["slug"]
                if self._stream_single_bundle(cat, slug, dest_root, pull_assets):
                    synced_bundles.append(f"{cat}/{slug}")

            return {
                "status": "success",
                "tier": "tier_2_remote_streaming",
                "source": RAW_GITHUB_BASE,
                "target": str(dest_root),
                "bundles_synced": synced_bundles,
                "registry_merge": reg_summary,
            }
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            logger.warning("Không thể kết nối đến kho tri thức từ xa: %s", e)
            return {
                "status": "degraded_offline",
                "tier": "tier_3_cloud_rag_fallback",
                "error_reason": "network_unreachable_or_timeout",
                "message": (
                    "💡 Không tìm thấy kho tri thức cục bộ và không thể tải qua Remote Streaming.\n"
                    "👉 Hướng dẫn khắc phục:\n"
                    '   1. Thiết lập biến môi trường trạm: export CCBA_LEGAL_KNOWLEDGE_PATH="/path/to/ccba-legal-knowledge"\n'
                    "   2. Hoặc sử dụng Cloud RAG (NotebookLM): ccba-legal query --cloud --notebook-id <id>"
                ),
                "target": str(dest_root),
                "bundles_synced": [],
                "registry_merge": {"updated": 0, "added": 0, "preserved": 0},
            }


def sync_legal_assets(
    target_dir: Path | str | None = None,
    doc_ids: list[str] | None = None,
    source_corpus_dir: Path | str | None = None,
    update_registry: bool = True,
    project_root: Path | None = None,
    pull_assets: bool = True,
) -> dict[str, Any]:
    """Convenience helper to synchronize legal assets into Spoke (ADR 0050)."""
    engine = LegalSyncEngine(project_root=project_root)
    return engine.pull_latest_okf_bundles(
        target_dir=target_dir,
        doc_ids=doc_ids,
        source_corpus_dir=source_corpus_dir,
        update_registry=update_registry,
        pull_assets=pull_assets,
    )
