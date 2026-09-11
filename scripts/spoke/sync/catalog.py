"""catalog.py - Atomic Merge & Validation Engine for catalog.yaml.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import yaml


class CatalogMerger:
    """Atomic Merge & Validation Engine for catalog.yaml."""

    def __init__(self, target_path: Path) -> None:
        self.target_path = target_path

    def atomic_write(self, data: dict[str, Any]) -> bool:
        """Write YAML data atomically via temp file replace after safe validation."""
        unique_suffix = (
            f"{os.getpid()}_{threading.get_ident()}_{time.time_ns()}_{uuid.uuid4().hex[:8]}"
        )
        temp_file = self.target_path.parent / f".{self.target_path.name}.{unique_suffix}.tmp"
        try:
            self.target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_file, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True)

            # Validate generated YAML
            with open(temp_file, encoding="utf-8") as f:
                validated = yaml.safe_load(f)
                if validated is None and data != {}:
                    raise ValueError("Validation produced empty structure for non-empty data")

            # Atomic Replace with retry loop for Windows file-sharing collisions (WinError 32)
            max_retries = 10
            for attempt in range(max_retries):
                try:
                    os.replace(temp_file, self.target_path)
                    return True
                except PermissionError:
                    if attempt < max_retries - 1:
                        time.sleep(0.01 * (attempt + 1))
                    else:
                        raise
            return True
        except Exception as e:
            print(f"[CatalogMerger] Error during atomic write: {e}", file=sys.stderr)
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False
