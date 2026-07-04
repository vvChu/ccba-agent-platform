#!/usr/bin/env python3
"""Script to automatically refresh and update metadata of existing documents in legal_registry.yaml from TVPL."""

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import requests
import yaml

# Add packages and scripts to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "packages" / "ccba-legal-intel"))

# Enforce UTF-8 output on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from ccba_legal import ChromeCDP, get_tvpl_metadata


def is_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def ensure_chrome_debug_port() -> bool:
    if is_port_open(9222):
        return True

    print("[Chrome Debug] Detecting port 9222 is closed. Attempting to start Google Chrome...")
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]

    chrome_path = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_path = path
            break

    if not chrome_path:
        print("[Chrome Debug Warning] Google Chrome installation not found.")
        return False

    try:
        user_data_dir = os.path.join(
            os.path.expanduser("~"), ".gemini", "antigravity", "chrome-debug-profile"
        )
        os.makedirs(user_data_dir, exist_ok=True)

        cmd = [
            chrome_path,
            "--remote-debugging-port=9222",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
        ]

        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        for _ in range(10):
            time.sleep(0.5)
            if is_port_open(9222):
                print("[Chrome Debug Success] Google Chrome launched successfully on port 9222!")
                return True

        print("[Chrome Debug Warning] Chrome started but port 9222 is not responding.")
        return False
    except Exception as e:
        print(f"[Chrome Debug Error] Error launching Chrome: {e}")
        return False


def main():
    registry_path = Path(__file__).parent.parent / ".md" / "knowledge" / "legal_registry.yaml"
    if not registry_path.exists():
        # Fallback to local cwd
        registry_path = Path(".md/knowledge/legal_registry.yaml")

    with open(registry_path, encoding="utf-8") as f:
        registry_data = yaml.safe_load(f) or {}

    if not ensure_chrome_debug_port():
        print("Error: Could not launch or connect to Chrome on debug port 9222.")
        sys.exit(1)

    cdp = ChromeCDP()
    pages = cdp.get_pages()
    if not pages:
        requests.get("http://127.0.0.1:9222/json/new")
        pages = cdp.get_pages()

    ws_url = pages[0]["webSocketDebuggerUrl"]
    print(f"[Metadata Sync] Connecting to tab WebSocket: {ws_url}")
    cdp.connect_tab(ws_url)

    try:
        updated_any = False
        for category in ["laws", "decrees", "circulars", "standards"]:
            items = registry_data.get(category, [])
            if not isinstance(items, list):
                continue

            for item in items:
                doc_id = item.get("id")
                url = item.get("download_url") or item.get("source_url")

                if not url or "thuvienphapluat.vn" not in url:
                    continue

                print(f"\n[Metadata Sync] Processing {doc_id} using URL: {url}")
                try:
                    tvpl_meta = get_tvpl_metadata(cdp, url)
                    if tvpl_meta:
                        # Sanity check: verify ID numbers match to avoid wrong mock URL redirects
                        id_parts = doc_id.split("-")
                        if len(id_parts) >= 3:
                            num_part = id_parts[1]
                            year_part = id_parts[2]
                            actual_doc_num = tvpl_meta.get("document_number", "")
                            if num_part not in actual_doc_num or year_part not in actual_doc_num:
                                print(
                                    f"  [Skip Update] Mismatch: expected ID containing {num_part} and {year_part}, got actual document number: '{actual_doc_num}' (likely a mock URL redirecting to a different page)"
                                )
                                continue

                        print(f"  -> Successfully extracted metadata for {doc_id}.")

                        # Update fields
                        if tvpl_meta.get("effective_date"):
                            item["effective_date"] = tvpl_meta["effective_date"]
                            print(f"  [Update] effective_date: {tvpl_meta['effective_date']}")
                        if tvpl_meta.get("issued_date"):
                            item["issued_date"] = tvpl_meta["issued_date"]
                            print(f"  [Update] issued_date: {tvpl_meta['issued_date']}")
                        if tvpl_meta.get("document_number"):
                            item["document_number"] = tvpl_meta["document_number"]
                            print(f"  [Update] document_number: {tvpl_meta['document_number']}")
                        if tvpl_meta.get("signer"):
                            item["signer"] = tvpl_meta["signer"]
                        if tvpl_meta.get("issued_by"):
                            item["issued_by"] = tvpl_meta["issued_by"]
                        if tvpl_meta.get("relations"):
                            non_empty_relations = {
                                k: v for k, v in tvpl_meta["relations"].items() if v
                            }
                            if non_empty_relations:
                                item["relations"] = non_empty_relations
                                print(
                                    f"  [Update] relations: updated legal relations graph ({len(non_empty_relations)} links)"
                                )

                        # Map status
                        tvpl_status = tvpl_meta.get("status", "").lower()
                        if "còn hiệu lực" in tvpl_status:
                            item["status"] = "current"
                        elif "hết hiệu lực" in tvpl_status:
                            item["status"] = "superseded"
                        elif "chưa có hiệu lực" in tvpl_status:
                            item["status"] = "enacted"

                        updated_any = True
                except Exception as e:
                    print(f"  [Error] Failed to get metadata for {doc_id}: {e}")

        if updated_any:
            # Write back
            with open(registry_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(registry_data, f, allow_unicode=True, sort_keys=False)
            print("\n[Metadata Sync Success] legal_registry.yaml has been updated successfully!")

            # Copy to skill resources
            skill_res_path = Path(
                ".agents/skills/legal-document-tracker/resources/legal_registry.yaml"
            )
            if skill_res_path.parent.exists():
                try:
                    shutil.copy(str(registry_path), str(skill_res_path))
                    print(
                        "[Metadata Sync Info] Successfully synced legal_registry.yaml to skill folder."
                    )
                except Exception as e:
                    print(f"[Metadata Sync Warning] Failed to copy to skill folder: {e}")
        else:
            print("\n[Metadata Sync] No updates were made to the registry.")

    finally:
        cdp.close()


if __name__ == "__main__":
    main()
