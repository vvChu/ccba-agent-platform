"""storage.py - Three-tier storage, caching, attached package extraction, and SHA-256 computation."""

from __future__ import annotations

import hashlib
import os
import shutil
import time
import zipfile
from pathlib import Path

from ccba_legal.cdp import ChromeCDP, HeadlessEnvironmentError, _check_is_headless
from ccba_legal.registry import resolve_project_root


def _compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _wait_for_file(
    target_dir: Path,
    fallback_dir: Path,
    slug_name: str,
    extensions: list[str],
    timeout_sec: int = 25,
    start_time: float | None = None,
) -> bool:
    """Wait for file download to complete either in target_dir (CDP direct) or fallback_dir."""
    init_time = time.time()
    min_mtime = start_time if start_time is not None else (init_time - 2.0)
    existing_fallback = {f.name for f in fallback_dir.glob("*")} if fallback_dir.exists() else set()
    while time.time() - init_time < timeout_sec:
        for ext in extensions:
            target_f = target_dir / f"{slug_name}{ext}"
            if target_f.exists() and target_f.stat().st_size > 0:
                return True
        for f in target_dir.glob("*"):
            if (
                f.suffix in extensions
                and not f.name.endswith(".crdownload")
                and not f.name.endswith(".tmp")
            ):
                if f.stat().st_mtime >= min_mtime or time.time() - f.stat().st_mtime < (
                    timeout_sec + 5
                ):
                    dest = target_dir / f"{slug_name}{f.suffix}"
                    if f != dest:
                        try:
                            shutil.move(str(f), str(dest))
                        except Exception:
                            pass
                    return True
        if fallback_dir.exists():
            for f in fallback_dir.glob("*"):
                if (
                    f.suffix in extensions
                    and not f.name.endswith(".crdownload")
                    and not f.name.endswith(".tmp")
                ):
                    if (f.stat().st_mtime >= min_mtime) or (
                        f.name not in existing_fallback and time.time() - f.stat().st_mtime < 30
                    ):
                        dest = target_dir / f"{slug_name}{f.suffix}"
                        try:
                            shutil.move(str(f), str(dest))
                            return True
                        except Exception:
                            pass
        time.sleep(0.8)
    return False


def _download_attached_packages(
    cdp: ChromeCDP, target_dir: Path, fallback_dir: Path, slug_name: str
) -> list[str]:
    """Scan and download attached packages (.zip, .rar, .xlsx) in 'FILE ĐƯỢC ĐÍNH KÈM' section."""
    attach_dir = target_dir / "attachments"
    attach_dir.mkdir(parents=True, exist_ok=True)
    cdp.set_download_behavior(attach_dir)

    click_attach_js = """
    (() => {
        let links = Array.from(document.querySelectorAll('a')).filter(a => {
            let txt = (a.innerText || '').toLowerCase();
            let href = (a.href || '').toLowerCase();
            let parentTxt = (a.parentElement ? a.parentElement.innerText : '').toLowerCase();
            return txt.includes('phu luc') || txt.includes('phụ lục') ||
                   href.includes('attachedfile') || href.includes('.zip') ||
                   href.includes('.rar') || parentTxt.includes('đính kèm');
        });
        if (links.length > 0) {
            links.forEach(l => l.click());
            return 'Clicked ' + links.length + ' attachment links';
        }
        return 'No attachment links';
    })()
    """
    try:
        res = cdp.evaluate_js(click_attach_js)
        print(f"[LegalIntel] Trigger attachments action: {res}")
        time.sleep(3.0)
    except Exception as e:
        print(f"[LegalIntel] Error triggering attachments: {e}")

    downloaded = []
    candidates = list(attach_dir.glob("*")) + (
        list(fallback_dir.glob("*.zip")) if fallback_dir.exists() else []
    )
    for f in candidates:
        if (
            f.suffix in (".zip", ".rar", ".xlsx", ".docx", ".doc")
            and not f.name.endswith(".crdownload")
            and not f.name.endswith(".tmp")
        ):
            if time.time() - f.stat().st_mtime < 30:
                dest = attach_dir / f.name
                if f != dest:
                    try:
                        shutil.move(str(f), str(dest))
                    except Exception:
                        pass
                downloaded.append(str(dest.resolve()))
                if dest.suffix == ".zip":
                    try:
                        with zipfile.ZipFile(dest, "r") as zf:
                            zf.extractall(attach_dir)
                            print(f"[LegalIntel] Extracted attachment ZIP: {dest.name}")
                    except Exception as e:
                        print(f"[LegalIntel] Error extracting ZIP: {e}")
    return downloaded


def _check_tier_1_local_and_cache(
    download_dir: Path, slug_name: str, extensions: list[str]
) -> bool:
    """Check target folder and local cache folder for the file."""
    for ext in extensions:
        target_path = download_dir / f"{slug_name}{ext}"
        if target_path.exists() and target_path.stat().st_size > 0:
            print(
                f"[download_three_tier] [Tier 1] File already exists in target folder: {target_path}"
            )
            return True

    project_root = resolve_project_root()
    cache_dir = project_root / ".md" / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    for ext in extensions:
        cache_path = cache_dir / f"{slug_name}{ext}"
        if cache_path.exists() and cache_path.stat().st_size > 0:
            dest_path = download_dir / f"{slug_name}{ext}"
            try:
                shutil.copy2(cache_path, dest_path)
                print(
                    f"[download_three_tier] [Tier 1] Restored from cache folder: {cache_path} -> {dest_path}"
                )
                return True
            except Exception as e:
                print(f"[download_three_tier] [Tier 1] Error copying from cache folder: {e}")
    return False


def _check_shared_drive(download_dir: Path, slug_name: str, extensions: list[str]) -> bool:
    """Check SHARED_DRIVE_DIR env path for the file."""
    shared_drive_env = os.environ.get("SHARED_DRIVE_DIR")
    if not shared_drive_env:
        return False
    shared_drive_path = Path(shared_drive_env)
    if not shared_drive_path.exists():
        return False

    for ext in extensions:
        src_file = shared_drive_path / f"{slug_name}{ext}"
        if src_file.exists() and src_file.stat().st_size > 0:
            dest_path = download_dir / f"{slug_name}{ext}"
            try:
                shutil.copy2(src_file, dest_path)
                print(
                    f"[download_three_tier] [Tier 2] Copied from SHARED_DRIVE_DIR: {src_file} -> {dest_path}"
                )
                return True
            except Exception as e:
                print(f"[download_three_tier] [Tier 2] Error copying from SHARED_DRIVE_DIR: {e}")
    return False


def _check_google_drive(download_dir: Path, slug_name: str, extensions: list[str]) -> bool:
    """Check Google Drive for the file and download if found."""
    try:
        import sys

        project_root = resolve_project_root()
        if str(project_root) not in sys.path:
            sys.path.append(str(project_root))
        from .sync import GOOGLE_API_AVAILABLE, get_drive_service

        if not GOOGLE_API_AVAILABLE:
            return False

        drive_service = get_drive_service()
        drive_folder_id = os.environ.get("DRIVE_FOLDER_ID", "1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2")
        for ext in extensions:
            file_name = f"{slug_name}{ext}"
            q = f"name = '{file_name}' and trashed = false"
            if drive_folder_id:
                q += f" and '{drive_folder_id}' in parents"

            results = drive_service.files().list(q=q, fields="files(id, name)").execute()
            files = results.get("files", [])
            if not files:
                continue

            file_id = files[0]["id"]
            dest_path = download_dir / file_name
            print(
                f"[download_three_tier] [Tier 2] Downloading {file_name} from Google Drive (ID: {file_id}) -> {dest_path}"
            )

            from googleapiclient.http import MediaIoBaseDownload

            request = drive_service.files().get_media(fileId=file_id)
            try:
                with open(dest_path, "wb") as f:
                    downloader = MediaIoBaseDownload(f, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                print(
                    f"[download_three_tier] [Tier 2] Successfully downloaded {file_name} from Google Drive."
                )
                return True
            except Exception as e:
                if dest_path.exists():
                    try:
                        dest_path.unlink()
                    except Exception:
                        pass
                raise e
    except Exception as e:
        print(f"[download_three_tier] [Tier 2] Google Drive API check failed: {e}")
    return False


def _check_aws_s3(download_dir: Path, slug_name: str, extensions: list[str]) -> bool:
    """Check AWS S3 bucket for the file and download if found."""
    try:
        import boto3
        from botocore.exceptions import ClientError

        bucket_name = os.environ.get("AWS_BUCKET_NAME") or os.environ.get("S3_BUCKET")
        if not bucket_name:
            return False

        s3_client = boto3.client("s3")
        for ext in extensions:
            file_name = f"{slug_name}{ext}"
            dest_path = download_dir / file_name
            try:
                print(
                    f"[download_three_tier] [Tier 2] Checking S3 bucket '{bucket_name}' for key '{file_name}'..."
                )
                s3_client.download_file(bucket_name, file_name, str(dest_path))
                print(
                    f"[download_three_tier] [Tier 2] Successfully downloaded {file_name} from S3."
                )
                return True
            except ClientError as ce:
                if ce.response["Error"]["Code"] in ["404", "NoSuchKey"]:
                    continue
                print(f"[download_three_tier] [Tier 2] S3 download error: {ce}")
    except ImportError:
        pass
    except Exception as e:
        print(f"[download_three_tier] [Tier 2] S3 check failed: {e}")
    return False


def _cache_downloaded_file(download_dir: Path, slug_name: str, extensions: list[str]) -> None:
    """Save the downloaded file to local cache folder."""
    project_root = resolve_project_root()
    cache_dir = project_root / ".md" / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    for ext in extensions:
        target_path = download_dir / f"{slug_name}{ext}"
        if target_path.exists():
            cache_path = cache_dir / f"{slug_name}{ext}"
            try:
                shutil.copy2(target_path, cache_path)
                print(f"[download_three_tier] [Tier 3] Cached file: {target_path} -> {cache_path}")
            except Exception as e:
                print(f"[download_three_tier] [Tier 3] Error copying file to cache: {e}")
            break


def download_three_tier(cdp: ChromeCDP, download_dir: Path, slug_name: str) -> bool:
    """Download a file using a three-tier fallback logic."""
    from ccba_legal.crawler import trigger_download

    extensions = [".docx", ".pdf", ".doc"]

    # --- Tier 1: Local & Cache Directory ---
    if _check_tier_1_local_and_cache(download_dir, slug_name, extensions):
        return True

    # --- Tier 2: Shared Drive, Google Drive & AWS S3 ---
    if _check_shared_drive(download_dir, slug_name, extensions):
        return True
    if _check_google_drive(download_dir, slug_name, extensions):
        return True
    if _check_aws_s3(download_dir, slug_name, extensions):
        return True

    # --- Tier 3: Direct Chrome CDP Crawl with Headless/CI-CD Exit Guard ---
    if _check_is_headless():
        raise HeadlessEnvironmentError(
            f"Blocked: Headless/CI-CD environment detected. Cannot download '{slug_name}' from TVPL."
        )

    print(
        f"[download_three_tier] [Tier 3] Fallback to direct Chrome CDP crawl for '{slug_name}'..."
    )
    res = trigger_download(cdp, download_dir, slug_name)
    success = res.get("success", False) if isinstance(res, dict) else bool(res)
    if success:
        _cache_downloaded_file(download_dir, slug_name, extensions)
    return success
