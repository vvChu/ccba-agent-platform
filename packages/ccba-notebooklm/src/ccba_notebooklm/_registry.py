import datetime
import hashlib
import sys
from pathlib import Path
from typing import Any

import yaml  # type: ignore

CONTEXT_FILE = Path(".md/workspace_context.yaml")
REGISTRY_FILE = Path(".md/data/sources_registry.yaml")
TASK_STATE_FILE = Path(".md/scratch/notebooklm_task_state.yaml")


def normalize_to_relative(filepath: str) -> str:
    """Normalize file paths to repo-relative format for portability."""
    if filepath.startswith(("http://", "https://")):
        return filepath
    try:
        p = Path(filepath)
        if p.is_absolute():
            try:
                # Try making it relative to Path.cwd()
                return str(p.relative_to(Path.cwd())).replace("\\", "/")
            except ValueError:
                pass
    except Exception:
        pass
    return filepath.replace("\\", "/")


def get_file_sha256(filepath: str) -> str:
    """Tính mã SHA-256 của file cục bộ hoặc URL."""
    if filepath.startswith(("http://", "https://")):
        return hashlib.sha256(filepath.encode("utf-8")).hexdigest()

    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def read_registry() -> dict[str, Any]:
    """Đọc dữ liệu từ registry cục bộ."""
    if not REGISTRY_FILE.exists():
        return {}
    try:
        with open(REGISTRY_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not data:
                return {}
            # Normalize all keys to relative forward-slash paths
            return {normalize_to_relative(k): v for k, v in data.items()}
    except Exception:
        return {}


def update_registry(file_path: str, source_id: str, sha256: str, notebook_id: str) -> None:
    """Cập nhật thông tin file vào registry."""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    registry = read_registry()
    norm_path = normalize_to_relative(file_path)
    registry[norm_path] = {
        "source_id": source_id,
        "sha256": sha256,
        "notebook_id": notebook_id,
        "updated_at": datetime.datetime.now().isoformat(),
    }
    try:
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(registry, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        print(f"[Warn] Không thể ghi registry: {e}", file=sys.stderr)


def get_notebook_id_from_context() -> str | None:
    """Đọc notebook_id từ workspace_context.yaml nếu tồn tại."""
    if not CONTEXT_FILE.exists():
        return None
    try:
        with open(CONTEXT_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data and "project" in data:
                val = data["project"].get("notebook_id")
                return str(val) if val else None
            return None
    except Exception:
        return None


def save_notebook_id_to_context(notebook_id: str) -> None:
    """Lưu notebook_id ngược lại workspace_context.yaml."""
    data: dict[str, Any] = {}
    if CONTEXT_FILE.exists():
        try:
            with open(CONTEXT_FILE, encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    data = loaded
        except Exception:
            pass

    try:
        if "project" not in data:
            data["project"] = {}
        data["project"]["notebook_id"] = notebook_id

        CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONTEXT_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        print(f"[Warn] Không thể lưu notebook_id vào context file: {e}", file=sys.stderr)


def read_task_state() -> dict[str, Any] | None:
    """Đọc tệp state tác vụ đang sinh ngầm."""
    if not TASK_STATE_FILE.exists():
        return None
    try:
        with open(TASK_STATE_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return dict(data) if isinstance(data, dict) else None
    except Exception:
        return None


def save_task_state(notebook_id: str, task_id: str, source_id: str, task_type: str) -> None:
    """Lưu tệp state tác vụ để có thể resume."""
    TASK_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "notebook_id": notebook_id,
        "task_id": task_id,
        "source_id": source_id,
        "task_type": task_type,
        "created_at": datetime.datetime.now().isoformat(),
    }
    try:
        with open(TASK_STATE_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(state, f, allow_unicode=True, default_flow_style=False)
    except Exception as e:
        print(f"[Warn] Không thể ghi state task: {e}", file=sys.stderr)


def clear_task_state() -> None:
    """Xóa tệp state sau khi hoàn thành."""
    if TASK_STATE_FILE.exists():
        try:
            TASK_STATE_FILE.unlink()
        except Exception:
            pass
