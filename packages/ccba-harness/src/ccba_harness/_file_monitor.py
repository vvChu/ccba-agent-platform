"""File system hook wrappers and thin facade for HarnessGuard file monitoring."""

from __future__ import annotations

import os
from typing import Any

from ._file_ast_scanner import _scan_ast_nodes
from ._file_path_utils import (
    _get_workspace_files,
    _is_text_sensitive,
    _looks_like_path,
    _safe_escape_decode,
    _safe_record_written_file,
    _scan_for_sensitive_inodes,
)
from ._file_sensitive_eval import _check_value_for_sensitive
from ._state import (
    _HOOK_TOKEN,
    HarnessState,
    _check_in_hook,
    _get_active_guards,
    _Originals,
)


def _run_checked_open(
    orig_fn: Any,
    file: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """Enforce guard file-access checks around an original open callable."""
    if getattr(HarnessState.local, "in_hook", None) is _HOOK_TOKEN:
        return orig_fn(file, *args, **kwargs)
    guards = _get_active_guards()
    if not guards:
        return orig_fn(file, *args, **kwargs)
    HarnessState.local.__dict__["in_hook"] = _HOOK_TOKEN
    try:
        for g in guards:
            g._check_file_access(file, args, kwargs)
        return orig_fn(file, *args, **kwargs)
    finally:
        HarnessState.local.__dict__["in_hook"] = None


def _wrapped_builtins_open(file: Any, *args: Any, **kwargs: Any) -> Any:
    """Hooked wrapper around `builtins.open`."""
    return _run_checked_open(_Originals.builtins_open, file, args, kwargs)


def _wrapped_io_open(file: Any, *args: Any, **kwargs: Any) -> Any:
    """Hooked wrapper around `io.open`."""
    return _run_checked_open(_Originals.io_open, file, args, kwargs)


def _wrapped__io_open(file: Any, *args: Any, **kwargs: Any) -> Any:
    """Hooked wrapper around `_io.open`."""
    return _run_checked_open(_Originals._io_open, file, args, kwargs)


def _decode_fspath(path: Any) -> str:
    """Convert any os.PathLike / bytes / str path into a decoded str."""
    file_str = os.fspath(path)
    return file_str.decode("utf-8", errors="replace") if isinstance(file_str, bytes) else file_str


def _wrapped_os_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
    """Hooked wrapper around `os.open` enforcing sensitivity and write tracking."""
    if _check_in_hook():
        return int(_Originals.os_open(path, flags, *args, **kwargs))
    guards = _get_active_guards()
    if not guards:
        return int(_Originals.os_open(path, flags, *args, **kwargs))
    HarnessState.local.__dict__["in_hook"] = _HOOK_TOKEN
    try:
        file_str = _decode_fspath(path)
        for g in guards:
            if g._is_sensitive(file_str) and not g._is_approved(file_str):
                raise PermissionError(f"Access to sensitive file blocked: {file_str}")
        if (flags & (os.O_WRONLY | os.O_RDWR)) != 0:
            for g in guards:
                _safe_record_written_file(g, file_str)
        return int(_Originals.os_open(path, flags, *args, **kwargs))
    finally:
        HarnessState.local.__dict__["in_hook"] = None


def _run_dst_path_mutation(
    orig_fn: Any,
    src: Any,
    dst: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> None:
    """Enforce guard sensitivity checks on destination path mutations (`rename`/`replace`)."""
    if _check_in_hook():
        orig_fn(src, dst, *args, **kwargs)
        return
    guards = _get_active_guards()
    if not guards:
        orig_fn(src, dst, *args, **kwargs)
        return
    HarnessState.local.__dict__["in_hook"] = _HOOK_TOKEN
    try:
        dst_str = _decode_fspath(dst)
        for g in guards:
            if g._is_sensitive(dst_str) and not g._is_approved(dst_str):
                raise PermissionError(f"Access to sensitive file blocked: {dst_str}")
        for g in guards:
            _safe_record_written_file(g, dst_str)
        orig_fn(src, dst, *args, **kwargs)
    finally:
        HarnessState.local.__dict__["in_hook"] = None


def _wrapped_os_rename(src: Any, dst: Any, *args: Any, **kwargs: Any) -> None:
    """Hooked wrapper around `os.rename`."""
    _run_dst_path_mutation(_Originals.os_rename, src, dst, args, kwargs)


def _wrapped_os_replace(src: Any, dst: Any, *args: Any, **kwargs: Any) -> None:
    """Hooked wrapper around `os.replace`."""
    _run_dst_path_mutation(_Originals.os_replace, src, dst, args, kwargs)


class _WrappedFileIO(_Originals.io_FileIO):  # type: ignore[valid-type,misc]
    """Hooked subclass wrapper around `io.FileIO`."""

    def __init__(self, file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> None:
        if _check_in_hook():
            super().__init__(file, mode, *args, **kwargs)
            return
        guards = _get_active_guards()
        if not guards:
            super().__init__(file, mode, *args, **kwargs)
            return
        HarnessState.local.__dict__["in_hook"] = _HOOK_TOKEN
        try:
            for g in guards:
                g._check_file_access(file, (mode,), kwargs)
            super().__init__(file, mode, *args, **kwargs)
        finally:
            HarnessState.local.__dict__["in_hook"] = None


class _Wrapped_io_FileIO(_Originals._io_FileIO):  # type: ignore[misc]
    """Hooked subclass wrapper around `_io.FileIO`."""

    def __init__(self, file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> None:
        if _check_in_hook():
            super().__init__(file, mode, *args, **kwargs)
            return
        guards = _get_active_guards()
        if not guards:
            super().__init__(file, mode, *args, **kwargs)
            return
        HarnessState.local.__dict__["in_hook"] = _HOOK_TOKEN
        try:
            for g in guards:
                g._check_file_access(file, (mode,), kwargs)
            super().__init__(file, mode, *args, **kwargs)
        finally:
            HarnessState.local.__dict__["in_hook"] = None


def _run_link_creation(
    orig_fn: Any,
    src: Any,
    dst: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """Enforce guard sensitivity checks on both link source and destination."""
    if _check_in_hook():
        return orig_fn(src, dst, *args, **kwargs)
    guards = _get_active_guards()
    if not guards:
        return orig_fn(src, dst, *args, **kwargs)
    HarnessState.local.__dict__["in_hook"] = _HOOK_TOKEN
    try:
        src_str, dst_str = _decode_fspath(src), _decode_fspath(dst)
        for g in guards:
            if g._is_sensitive(src_str) and not g._is_approved(src_str):
                raise PermissionError(f"Access to sensitive file blocked: {src_str}")
            if g._is_sensitive(dst_str) and not g._is_approved(dst_str):
                raise PermissionError(f"Access to sensitive file blocked: {dst_str}")
        for g in guards:
            _safe_record_written_file(g, dst_str)
        return orig_fn(src, dst, *args, **kwargs)
    finally:
        HarnessState.local.__dict__["in_hook"] = None


def _wrapped_os_link(src: Any, dst: Any, *args: Any, **kwargs: Any) -> Any:
    """Hooked wrapper around `os.link`."""
    return _run_link_creation(_Originals.os_link, src, dst, args, kwargs)


def _wrapped_os_symlink(src: Any, dst: Any, *args: Any, **kwargs: Any) -> Any:
    """Hooked wrapper around `os.symlink`."""
    return _run_link_creation(_Originals.os_symlink, src, dst, args, kwargs)


__all__ = [
    "_check_value_for_sensitive",
    "_get_workspace_files",
    "_is_text_sensitive",
    "_looks_like_path",
    "_safe_escape_decode",
    "_safe_record_written_file",
    "_scan_ast_nodes",
    "_scan_for_sensitive_inodes",
    "_wrapped__io_open",
    "_wrapped_builtins_open",
    "_Wrapped_io_FileIO",
    "_wrapped_io_open",
    "_wrapped_os_link",
    "_wrapped_os_open",
    "_wrapped_os_rename",
    "_wrapped_os_replace",
    "_wrapped_os_symlink",
    "_WrappedFileIO",
]
