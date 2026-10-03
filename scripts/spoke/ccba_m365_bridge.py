#!/usr/bin/env python3
"""ccba_m365_bridge.py - Pure Python Outbound Bridge Worker for Microsoft 365 IDOP Integration.

Architecture & Governance:
- Part of CCBA Teamwork Multi-Agent Framework (ADR-0035, ADR-0043, ADR-0053, Issue #366).
- Implements pure Python integration with Microsoft 365 / SharePoint Online / Microsoft Graph.
- Decouples from legacy PowerShell/PnP dependencies.
- Enforces strict safety guardrails (ADR-0035 / ADR-0053): Zero-mutation dry-run default,
  proactive Token Bucket rate limiting (5 req/s), reactive HTTP 429 Retry-After throttling handler,
  and Dead-Letter Queue (DLQ) idempotent persistence for high-availability offline tolerance.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

try:
    import msal

    HAS_MSAL = True
except ImportError:
    msal = None  # type: ignore[assignment]
    HAS_MSAL = False

# Configure logging
logger = logging.getLogger("ccba_m365_bridge")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [M365-Bridge] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ==============================================================================
# 1. Configuration & Data Transfer Objects
# ==============================================================================


@dataclass
class BridgeConfig:
    """Configuration parameters for the M365 Outbound Bridge."""

    tenant_id: str = "d7aa4978-363e-47aa-a77e-7da957b32bf3"
    client_id: str = "c055c7a4-9150-4bd5-bf01-445c65467feb"
    client_credential: str | None = None
    cert_path: str | None = None
    cert_thumbprint: str | None = None
    cert_password: str | None = None
    sharepoint_url: str = "https://ibstbim.sharepoint.com/sites/idop"
    cde_site_url: str = "https://ibstbim.sharepoint.com/sites/iCDE"
    portal_site_url: str = "https://ibstbim.sharepoint.com"
    target_env: str = "DEV"  # DEV, TEST, PROD
    dry_run: bool = True  # Strict safety default (ADR-0035 / ADR-0053)
    rate_limit_rps: float = 5.0  # 5 requests per second max
    bucket_capacity: float = 5.0
    max_retries: int = 4
    backoff_factor: float = 1.5
    dlq_dir: Path = field(default_factory=lambda: Path(".system_generated/dlq"))
    timeout_seconds: float = 30.0

    @property
    def client_secret(self) -> str | None:
        """Backward-compatible alias for client_credential."""
        return self.client_credential

    @classmethod
    def from_env(cls) -> BridgeConfig:
        """Instantiates BridgeConfig loaded from environment variables with safe defaults."""
        dlq_path_str = os.getenv("CCBA_M365_DLQ_DIR", ".system_generated/dlq")
        dry_run_env = os.getenv("CCBA_M365_DRY_RUN", "true").lower() in ("1", "true", "yes")

        return cls(
            tenant_id=os.getenv(
                "IDOP_SP_TENANT",
                os.getenv("AZURE_TENANT_ID", "d7aa4978-363e-47aa-a77e-7da957b32bf3"),
            ),
            client_id=os.getenv(
                "IDOP_SP_CLIENT_ID",
                os.getenv("AZURE_CLIENT_ID", "c055c7a4-9150-4bd5-bf01-445c65467feb"),
            ),
            client_credential=os.getenv("IDOP_SP_CLIENT_SECRET", os.getenv("AZURE_CLIENT_SECRET")),
            cert_path=os.getenv("IDOP_SP_CERT_PATH", os.getenv("AZURE_CLIENT_CERTIFICATE_PATH")),
            cert_thumbprint=os.getenv("IDOP_PNP_CERT_THUMBPRINT"),
            cert_password=os.getenv("IDOP_SP_CERT_PASSWORD"),
            sharepoint_url=os.getenv("IDOP_SP_URL", "https://ibstbim.sharepoint.com/sites/idop"),
            cde_site_url=os.getenv("IDOP_CDE_URL", "https://ibstbim.sharepoint.com/sites/iCDE"),
            portal_site_url=os.getenv("IDOP_PORTAL_URL", "https://ibstbim.sharepoint.com"),
            target_env=os.getenv("IDOP_ENV", "DEV").upper(),
            dry_run=dry_run_env,
            rate_limit_rps=float(os.getenv("CCBA_M365_RATE_LIMIT", "5.0")),
            dlq_dir=Path(dlq_path_str),
        )


@dataclass
class SyncResult:
    """Outcome report for an individual synchronization operation."""

    success: bool
    status: str  # DRY_RUN_SUCCESS, SYNCED, THROTTLED, FAILED_STAGED_DLQ, ERROR
    item_id: str | None = None
    list_name: str = ""
    duration_ms: float = 0.0
    attempts: int = 1
    error_message: str | None = None
    dlq_path: str | None = None
    payload_summary: dict[str, Any] = field(default_factory=dict)


# ==============================================================================
# 2. Token Bucket Rate Limiter (Proactive 5 req/s Enforcer)
# ==============================================================================


class TokenBucketLimiter:
    """Thread-safe Token Bucket Rate Limiter to prevent SPO/Graph HTTP 429 Throttling.

    Ensures that burst requests do not exceed the configured capacity and average rate
    (default: 5.0 requests/second).
    """

    def __init__(self, rate: float = 5.0, capacity: float = 5.0):
        self.rate = max(0.1, rate)
        self.capacity = max(1.0, capacity)
        self.tokens = float(self.capacity)
        self.last_update = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0) -> float:
        """Acquires the specified number of tokens. Sleeps if insufficient tokens exist.

        Args:
            tokens: Number of tokens to consume (default 1.0).

        Returns:
            float: Number of seconds slept while waiting for tokens.
        """
        slept = 0.0
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now
            self.tokens = min(self.capacity, self.tokens + (elapsed * self.rate))

            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0

            deficit = tokens - self.tokens
            slept = deficit / self.rate
            self.tokens = 0.0
            self.last_update = now + slept

        if slept > 0:
            time.sleep(slept)
        return slept


# ==============================================================================
# 3. Entra ID App-Only Authentication Manager (MSAL)
# ==============================================================================


class M365AuthManager:
    """Handles Microsoft Entra ID App-Only Authentication via MSAL Python.

    Supports:
    1. Client Secret (ConfidentialClientApplication with client_secret).
    2. PEM Certificate (RFC 7523 JWT assertion with private key and thumbprint).
    3. In-memory token caching with auto-refresh before expiration.
    """

    def __init__(self, config: BridgeConfig):
        self.config = config
        self._app: Any | None = None
        self._token_cache: dict[str, tuple[str, float]] = {}  # scope -> (token, expire_timestamp)
        self._lock = threading.Lock()

    def _init_msal_app(self) -> Any:
        """Initializes the underlying MSAL ConfidentialClientApplication."""
        if not HAS_MSAL:
            raise RuntimeError(
                "Thư viện 'msal' chưa được cài đặt trong môi trường Python hiện tại. "
                "Cài đặt bằng lệnh: pip install msal httpx cryptography"
            )

        authority = f"https://login.microsoftonline.com/{self.config.tenant_id}"

        # Mode A: Certificate-based Authentication (PEM / RFC 7523)
        if self.config.cert_path:
            cert_file = Path(self.config.cert_path)
            if not cert_file.exists():
                raise FileNotFoundError(f"Certificate file not found: {self.config.cert_path}")

            with open(cert_file, encoding="utf-8") as f:
                pem_data = f.read()

            client_credential: dict[str, Any] = {"private_key": pem_data}
            if self.config.cert_thumbprint:
                client_credential["thumbprint"] = self.config.cert_thumbprint

            logger.info("Initializing MSAL with App-Only PEM Certificate (Client Assertion)")
            return msal.ConfidentialClientApplication(
                client_id=self.config.client_id,
                client_credential=client_credential,
                authority=authority,
            )

        # Mode B: Client Secret Authentication
        if self.config.client_secret:
            logger.info("Initializing MSAL with App-Only Client Secret")
            return msal.ConfidentialClientApplication(
                client_id=self.config.client_id,
                client_credential=self.config.client_secret,
                authority=authority,
            )

        # Mode C: Dry Run Mock
        if self.config.dry_run:
            logger.warning(
                "No credentials provided for M365AuthManager. Operating in Dry-Run Mock Mode."
            )
            return None

        raise ValueError(
            "Missing authentication credentials: Must provide either client_secret or cert_path."
        )

    def get_token(self, scope: str | None = None) -> str:
        """Acquires a valid Bearer token for the specified scope.

        Args:
            scope: Resource scope URI (default: SharePoint tenant scope or Graph).

        Returns:
            str: Valid Bearer Access Token.
        """
        target_scope = scope or f"{self.config.portal_site_url}/.default"
        now = time.time()

        # Check in-memory cache with 5-minute safety buffer
        with self._lock:
            if target_scope in self._token_cache:
                token, expires_at = self._token_cache[target_scope]
                if expires_at - now > 300:  # Valid for more than 5 minutes
                    return token

            if self.config.dry_run and not HAS_MSAL:
                mock_token = f"mock_bearer_token_{self.config.client_id[:8]}_{int(now)}"
                self._token_cache[target_scope] = (mock_token, now + 3600)
                return mock_token

            if self._app is None:
                self._app = self._init_msal_app()

            if self._app is None:  # Dry run fallback
                mock_token = f"mock_bearer_token_{self.config.client_id[:8]}_{int(now)}"
                self._token_cache[target_scope] = (mock_token, now + 3600)
                return mock_token

            logger.info("Acquiring fresh App-Only OAuth token for scope: %s", target_scope)
            result = self._app.acquire_token_for_client(scopes=[target_scope])

            if "access_token" in result:
                access_token = result["access_token"]
                expires_in = result.get("expires_in", 3599)
                self._token_cache[target_scope] = (access_token, now + expires_in)
                logger.info("Successfully acquired token (expires in %d seconds)", expires_in)
                return access_token

            error_desc = result.get("error_description", result.get("error", "Unknown MSAL error"))
            raise RuntimeError(f"Failed to acquire M365 App-Only auth response - {error_desc}")


# ==============================================================================
# 4. Dead-Letter Queue (DLQ) Manager (Zero-Data-Loss Offline Tolerance)
# ==============================================================================


class DeadLetterQueueManager:
    """Manages persistent Dead-Letter Queue storage for failed sync payloads.

    Conforms to ADR-0043: Staged Local queue guaranteeing zero-downtime and zero-data-loss.
    """

    def __init__(self, dlq_dir: Path):
        self.dlq_dir = dlq_dir
        self.archive_dir = dlq_dir / "archive"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Creates DLQ storage directories if they do not exist."""
        self.dlq_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def enqueue(
        self,
        entity_type: str,
        operation: str,
        target_list: str,
        payload: dict[str, Any],
        error_message: str,
        attempts: int,
    ) -> Path:
        """Persists a failed payload into an idempotent DLQ JSON file.

        Args:
            entity_type: Type of business entity (e.g., 'cde_document', 'contract').
            operation: Sync operation ('CREATE', 'UPDATE').
            target_list: SharePoint destination list name.
            payload: The exact JSON payload intended for sync.
            error_message: Reason for failure.
            attempts: Number of retry attempts made before enqueuing.

        Returns:
            Path: File path of the stored DLQ item.
        """
        now = datetime.now(timezone.utc)
        record_id = str(uuid.uuid4())
        filename = f"{entity_type}_{now.strftime('%Y%m%dT%H%M%SZ')}_{record_id[:8]}.json"
        target_file = self.dlq_dir / filename

        dlq_entry = {
            "id": record_id,
            "timestamp": now.isoformat(),
            "entity_type": entity_type,
            "operation": operation,
            "target_list": target_list,
            "payload": payload,
            "attempts": attempts,
            "error_message": error_message,
            "status": "STAGED_LOCAL",  # ADR-0043 state tag
        }

        # Atomic file write via temp file
        temp_file = target_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(dlq_entry, f, indent=2, ensure_ascii=False)
        temp_file.replace(target_file)

        logger.warning(
            "Enqueued failed %s payload to DLQ: %s (Error: %s)",
            entity_type,
            target_file.name,
            error_message,
        )
        return target_file

    def list_pending(self) -> list[Path]:
        """Lists all pending DLQ items sorted deterministically by filename."""
        if not self.dlq_dir.exists():
            return []
        items = [p for p in self.dlq_dir.glob("*.json") if p.is_file()]
        # Deterministic sorting (KISS / Multi-Key Invariant)
        return sorted(items, key=lambda p: p.name)

    def archive(self, dlq_file: Path) -> Path:
        """Moves a successfully replayed DLQ file to the archive folder."""
        dest = self.archive_dir / dlq_file.name
        dlq_file.replace(dest)
        logger.info("Archived resolved DLQ file: %s -> %s", dlq_file.name, dest.name)
        return dest


# ==============================================================================
# 5. SharePoint HTTP Client (HTTP 429 Throttling & Retry Engine)
# ==============================================================================


class SharePointClient:
    """Robust HTTP Client for SharePoint REST API and Microsoft Graph API.

    Features:
    - Proactive rate limiting via TokenBucketLimiter (5 req/s).
    - Throttling handling: Reads 'Retry-After' header on HTTP 429 or 503.
    - Exponential backoff with jitter on transient network/server errors.
    - Strict dry-run enforcement to prevent unintentional tenant mutations.
    """

    def __init__(self, config: BridgeConfig, auth_manager: M365AuthManager):
        self.config = config
        self.auth = auth_manager
        self.limiter = TokenBucketLimiter(
            rate=config.rate_limit_rps, capacity=config.bucket_capacity
        )
        self.http_client = httpx.Client(
            timeout=config.timeout_seconds,
            headers={
                "Accept": "application/json;odata=nometadata",
                "Content-Type": "application/json",
            },
        )

    def _execute_with_retry(
        self,
        method: str,
        url: str,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Executes an HTTP request with proactive rate-limiting and reactive retry on 429/5xx."""
        req_headers = headers or {}
        attempt = 0

        while attempt < self.config.max_retries:
            attempt += 1

            # Proactive Token Bucket rate limit
            wait_token = self.limiter.acquire(1.0)
            if wait_token > 0.05:
                logger.debug("Proactive rate limit throttle: waited %.3fs", wait_token)

            try:
                response = self.http_client.request(
                    method=method,
                    url=url,
                    json=json_data,
                    headers=req_headers,
                )

                # Case 1: Throttled by SharePoint Online (HTTP 429 or 503)
                if response.status_code in (429, 503):
                    retry_after_header = response.headers.get("Retry-After")
                    if retry_after_header:
                        try:
                            delay = float(retry_after_header)
                        except ValueError:
                            delay = self.config.backoff_factor**attempt
                    else:
                        delay = self.config.backoff_factor**attempt

                    # Add jitter to avoid thundering herd
                    jitter = random.uniform(0.5, 1.5)
                    total_delay = delay + jitter

                    logger.warning(
                        "HTTP %d Throttled by SharePoint! Header Retry-After: %s. Backing off for %.2fs (Attempt %d/%d)",
                        response.status_code,
                        retry_after_header,
                        total_delay,
                        attempt,
                        self.config.max_retries,
                    )
                    time.sleep(total_delay)
                    continue

                # Case 2: Transient server errors (500, 502, 504)
                if response.status_code in (500, 502, 504):
                    delay = (self.config.backoff_factor**attempt) + random.uniform(0.1, 0.5)
                    logger.warning(
                        "Transient server error %d. Retrying in %.2fs (Attempt %d/%d)",
                        response.status_code,
                        delay,
                        attempt,
                        self.config.max_retries,
                    )
                    time.sleep(delay)
                    continue

                return response

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.NetworkError) as net_err:
                delay = (self.config.backoff_factor**attempt) + random.uniform(0.2, 1.0)
                logger.warning(
                    "Network error on %s %s: %s. Retrying in %.2fs (Attempt %d/%d)",
                    method,
                    url,
                    str(net_err),
                    delay,
                    attempt,
                    self.config.max_retries,
                )
                time.sleep(delay)

        raise RuntimeError(f"Exceeded max retries ({self.config.max_retries}) for {method} {url}")

    def create_list_item(
        self, site_url: str, list_name: str, fields: dict[str, Any]
    ) -> tuple[bool, str | None, str | None]:
        """Creates an item in a SharePoint list via REST API.

        Args:
            site_url: Absolute URL of the target site (e.g. https://ibstbim.sharepoint.com/sites/idop).
            list_name: Internal name of the list (e.g. CDEDocuments).
            fields: Dictionary of field internal names to values.

        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (Success, item_id, error_message).
        """
        # Strict ADR-0035 / ADR-0053 Safety Guardrail
        if self.config.dry_run:
            mock_id = f"DRYRUN-{uuid.uuid4().hex[:8]}"
            logger.info(
                "[DRY-RUN] Safely bypassed real POST to %s/lists/%s. Mock Item ID: %s. Payload keys: %s",
                site_url,
                list_name,
                mock_id,
                list(fields.keys()),
            )
            return True, mock_id, None

        endpoint = f"{site_url.rstrip('/')}/_api/web/lists/getbytitle('{list_name}')/items"
        bearer_jwt = self.auth.get_token()
        headers = {
            "Authorization": f"Bearer {bearer_jwt}",
            "Accept": "application/json;odata=nometadata",
            "Content-Type": "application/json",
        }

        try:
            response = self._execute_with_retry("POST", endpoint, json_data=fields, headers=headers)
            if response.status_code in (200, 201):
                res_data = response.json()
                item_id = str(res_data.get("Id", res_data.get("ID", "")))
                logger.info("Successfully created item in %s: ID %s", list_name, item_id)
                return True, item_id, None

            err_msg = f"HTTP {response.status_code}: {response.text}"
            logger.error("Failed to create item in %s: %s", list_name, err_msg)
            return False, None, err_msg

        except Exception as ex:
            logger.error("Exception during create_list_item in %s: %s", list_name, str(ex))
            return False, None, str(ex)


# ==============================================================================
# 6. CDE Document Outbound Sync Service
# ==============================================================================


class CdeDocumentSyncService:
    """Specialized worker for synchronizing ISO 19650 CDE Documents to SharePoint Online."""

    REQUIRED_FIELDS = ("Title",)
    ALLOWED_APPROVAL_STATUS = ("S0", "S1", "S2", "S3", "A1")

    def __init__(self, config: BridgeConfig):
        self.config = config
        self.auth = M365AuthManager(config)
        self.client = SharePointClient(config, self.auth)
        self.dlq = DeadLetterQueueManager(config.dlq_dir)

    def validate_cde_payload(self, doc_data: dict[str, Any]) -> list[str]:
        """Validates payload against CDEDocuments schema requirements."""
        errors: list[str] = []
        for req in self.REQUIRED_FIELDS:
            if not doc_data.get(req):
                errors.append(f"Missing required field: '{req}'")

        status = doc_data.get("ApprovalStatus")
        if status and status not in self.ALLOWED_APPROVAL_STATUS:
            errors.append(
                f"Invalid ApprovalStatus '{status}'. Must be one of {self.ALLOWED_APPROVAL_STATUS}"
            )

        return errors

    def sync_cde_document(
        self,
        doc_data: dict[str, Any],
        dry_run: bool | None = None,
    ) -> SyncResult:
        """Synchronizes an ISO 19650 document entry into the CDEDocuments list.

        Args:
            doc_data: Field mapping according to cde_documents.json schema.
            dry_run: Optional override for safety dry-run flag.

        Returns:
            SyncResult: Structured result of the sync operation.
        """
        start_time = time.monotonic()
        is_dry_run = self.config.dry_run if dry_run is None else dry_run

        # 1. Validation Gate
        validation_errors = self.validate_cde_payload(doc_data)
        if validation_errors:
            err_text = "; ".join(validation_errors)
            logger.error("Payload validation failed: %s", err_text)
            return SyncResult(
                success=False,
                status="VALIDATION_ERROR",
                list_name="CDEDocuments",
                duration_ms=(time.monotonic() - start_time) * 1000,
                error_message=err_text,
                payload_summary={"Title": doc_data.get("Title")},
            )

        # 2. Target Site: CDEDocuments resides in the IDOP Operations Engine site
        target_site = self.config.sharepoint_url
        list_name = "CDEDocuments"

        # Format SharePoint field payload
        sp_fields: dict[str, Any] = {
            "Title": doc_data["Title"],
            "ProjectCode": doc_data.get("ProjectCode", ""),
            "Originator": doc_data.get("Originator", "CCBA"),
            "ZoneVolume": doc_data.get("ZoneVolume", ""),
            "LevelLocation": doc_data.get("LevelLocation", ""),
            "DocumentCode": doc_data.get("DocumentCode", ""),
            "IsoDocumentName": doc_data.get("IsoDocumentName", ""),
            "ApprovalStatus": doc_data.get("ApprovalStatus", "S0"),
            "Version": doc_data.get("Version", "P01.01"),
        }

        # Optional FileUrl (Hyperlink format)
        if "FileUrl" in doc_data and doc_data["FileUrl"]:
            url_val = doc_data["FileUrl"]
            if isinstance(url_val, str):
                sp_fields["FileUrl"] = {
                    "Url": url_val,
                    "Description": doc_data.get("IsoDocumentName", "Link"),
                }
            elif isinstance(url_val, dict):
                sp_fields["FileUrl"] = url_val

        # Execute Sync via SharePointClient
        if is_dry_run:
            duration_ms = (time.monotonic() - start_time) * 1000
            mock_id = f"DRYRUN-{uuid.uuid4().hex[:8]}"
            logger.info(
                "[DRY-RUN SUCCESS] Document '%s' simulated sync. ID: %s", doc_data["Title"], mock_id
            )
            return SyncResult(
                success=True,
                status="DRY_RUN_SUCCESS",
                item_id=mock_id,
                list_name=list_name,
                duration_ms=duration_ms,
                payload_summary=sp_fields,
            )

        success, item_id, error_msg = self.client.create_list_item(
            target_site, list_name, sp_fields
        )
        duration_ms = (time.monotonic() - start_time) * 1000

        if success:
            return SyncResult(
                success=True,
                status="SYNCED",
                item_id=item_id,
                list_name=list_name,
                duration_ms=duration_ms,
                payload_summary=sp_fields,
            )

        # Fallback to Dead-Letter Queue on failure
        dlq_file = self.dlq.enqueue(
            entity_type="cde_document",
            operation="CREATE",
            target_list=list_name,
            payload=sp_fields,
            error_message=error_msg or "Unknown error",
            attempts=self.config.max_retries,
        )

        return SyncResult(
            success=False,
            status="FAILED_STAGED_DLQ",
            list_name=list_name,
            duration_ms=duration_ms,
            error_message=error_msg,
            dlq_path=str(dlq_file),
            payload_summary=sp_fields,
        )

    def replay_dlq(self) -> dict[str, Any]:
        """Replays all pending items in the Dead-Letter Queue."""
        pending_files = self.dlq.list_pending()
        logger.info("Found %d pending DLQ items to replay", len(pending_files))

        replayed_count = 0
        failed_count = 0

        for file_path in pending_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    entry = json.load(f)

                target_list = entry.get("target_list", "CDEDocuments")
                payload = entry.get("payload", {})

                logger.info("Replaying DLQ item %s (%s)...", file_path.name, target_list)
                if self.config.dry_run:
                    logger.info("[DRY-RUN] Simulating DLQ replay for %s", file_path.name)
                    replayed_count += 1
                    continue

                target_site = self.config.sharepoint_url
                success, item_id, err = self.client.create_list_item(
                    target_site, target_list, payload
                )
                if success:
                    self.dlq.archive(file_path)
                    replayed_count += 1
                else:
                    logger.warning("DLQ replay failed for %s: %s", file_path.name, err)
                    failed_count += 1

            except Exception as ex:
                logger.error("Error reading/replaying DLQ file %s: %s", file_path.name, str(ex))
                failed_count += 1

        return {
            "total_pending": len(pending_files),
            "replayed": replayed_count,
            "failed": failed_count,
        }


# ==============================================================================
# 7. Command Line Interface (CLI Runner)
# ==============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Builds the argument parser for standalone execution."""
    parser = argparse.ArgumentParser(
        description="CCBA M365 Outbound Bridge Worker (pure Python MSAL + HTTPX)"
    )
    parser.add_argument(
        "--health", action="store_true", help="Perform health check and print configuration."
    )
    parser.add_argument(
        "--sync-sample", action="store_true", help="Sync a sample ISO 19650 CDE Document."
    )
    parser.add_argument(
        "--replay-dlq", action="store_true", help="Replay all pending Dead-Letter Queue items."
    )
    parser.add_argument(
        "--list-dlq", action="store_true", help="List all pending Dead-Letter Queue items."
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Disable dry-run safety lock (CAUTION: mutates live SPO).",
    )
    return parser


def main() -> int:
    """Entry point for CLI execution."""
    parser = build_parser()
    args = parser.parse_args()

    config = BridgeConfig.from_env()
    if args.live:
        # User explicitly requested live mode
        config.dry_run = False
        logger.warning("⚠️  LIVE MODE ENABLED: Outbound requests will mutate SharePoint Online.")
    else:
        config.dry_run = True

    service = CdeDocumentSyncService(config)

    if args.health:
        print("\n=== CCBA M365 Outbound Bridge Health Report ===")
        print(f"Tenant ID:         {config.tenant_id}")
        print(f"Client ID:         {config.client_id}")
        print(
            f"Auth Method:       {'PEM Certificate' if config.cert_path else 'Client Secret' if config.client_secret else 'Mock / Unconfigured'}"
        )
        print(f"MSAL Installed:    {HAS_MSAL}")
        print(f"Dry Run Mode:      {config.dry_run}")
        print(f"Rate Limiter:      {config.rate_limit_rps} req/sec (Token Bucket)")
        print(f"SharePoint URL:    {config.sharepoint_url}")
        print(f"CDE Site URL:      {config.cde_site_url}")
        print(f"DLQ Directory:     {config.dlq_dir.resolve()}")
        print(f"Pending DLQ Items: {len(service.dlq.list_pending())}")
        print("===============================================\n")
        return 0

    if args.list_dlq:
        items = service.dlq.list_pending()
        print(f"\nPending DLQ items ({len(items)}):")
        for item in items:
            print(f"  - {item.name}")
        return 0

    if args.replay_dlq:
        results = service.replay_dlq()
        print(f"\nDLQ Replay Results: {json.dumps(results, indent=2)}")
        return 0

    if args.sync_sample:
        sample_doc = {
            "Title": "Bản vẽ mặt bằng kiến trúc tầng 1 - Khối A",
            "ProjectCode": "DA-2026-DHVN",
            "Originator": "CCBA",
            "ZoneVolume": "BLK-A",
            "LevelLocation": "LV-01",
            "DocumentCode": "AR-DWG-001",
            "IsoDocumentName": "DA2026-CCBA-BLK_A-01-DR-A-0001",
            "ApprovalStatus": "S1",
            "Version": "P01.01",
            "FileUrl": f"{config.cde_site_url}/Shared Documents/01_WIP/DA2026-CCBA-BLK_A-01-DR-A-0001.dwg",
        }
        print("\nSubmitting Sample CDE Document Sync...")
        result = service.sync_cde_document(sample_doc)
        print(
            f"Sync Result: Status={result.status}, ItemID={result.item_id}, Duration={result.duration_ms:.2f}ms"
        )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
