"""Recursive multi-encoding sensitivity detection helpers for HarnessGuard."""

from __future__ import annotations

import base64
import os
import re
import unicodedata
import zlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._guard import HarnessGuard

from ._file_path_utils import _is_text_sensitive, _safe_escape_decode
from ._state import HarnessState


def _assert_not_sensitive(text: str, guards: list[HarnessGuard], prefix: str) -> None:
    """Raise PermissionError if `text` is sensitive and unapproved by any active guard."""
    if _is_text_sensitive(text) and not any(g._is_approved(text) for g in guards):
        raise PermissionError(f"{prefix}: {text}")


def _decode_nfkc_bytes(raw: bytes) -> str:
    """Decode bytes as UTF-8 (ignoring invalid bytes) and apply NFKC normalization."""
    return unicodedata.normalize("NFKC", raw.decode("utf-8", errors="ignore"))


def _check_zlib_bytes(data: bytes, guards: list[HarnessGuard], prefix: str) -> None:
    """Decompress zlib payload if valid and reject if decompressed text is sensitive."""
    try:
        decomp = zlib.decompress(data)
        if decomp:
            _assert_not_sensitive(_decode_nfkc_bytes(decomp), guards, prefix)
    except PermissionError:
        raise
    except Exception:
        pass


def _extract_raw_str_and_bytes(val: Any) -> tuple[str, bytes] | None:
    """Convert incoming str/bytes value into NFKC-normalized str and UTF-8 bytes."""
    raw_str, raw_bytes = "", b""
    if isinstance(val, str):
        raw_str = unicodedata.normalize("NFKC", val)
        try:
            raw_bytes = raw_str.encode("utf-8")
        except Exception:
            pass
        return raw_str, raw_bytes
    if isinstance(val, bytes):
        raw_bytes = val
        try:
            raw_str = _decode_nfkc_bytes(val)
        except Exception:
            pass
        return raw_str, raw_bytes
    return None


def _check_fs_links_sensitive(raw_str: str, guards: list[HarnessGuard]) -> None:
    """Resolve symlinks and inode sensitivity for paths matching existing filesystem nodes."""
    try:
        if not raw_str:
            return
        try:
            canonical_path = os.path.realpath(raw_str)
        except Exception:
            canonical_path = raw_str
        for path_to_check in {raw_str, canonical_path}:
            if not os.path.exists(path_to_check):
                continue
            try:
                st = os.stat(path_to_check)
                if (st.st_dev, st.st_ino) in HarnessState.sensitive_inodes:
                    if not any(g._is_approved(path_to_check) for g in guards):
                        raise PermissionError(f"Access to sensitive file blocked: {path_to_check}")
            except PermissionError:
                raise
            except Exception:
                pass
            try:
                resolved_str = str(Path(path_to_check).resolve())
                if resolved_str != path_to_check:
                    _check_value_for_sensitive(resolved_str, guards)
            except PermissionError:
                raise
            except Exception:
                pass
    except PermissionError:
        raise
    except Exception:
        pass


def _check_base64_candidates(raw_str: str, decoded_str: str, guards: list[HarnessGuard]) -> None:
    """Scan raw and escape-decoded strings for base64 / compressed-base64 obfuscation."""
    try:
        candidates = {raw_str, decoded_str}
        if raw_str:
            candidates.add(re.sub(r"\s+", "", raw_str))
        if decoded_str:
            candidates.add(re.sub(r"\s+", "", decoded_str))
        for candidate_str in filter(None, candidates):
            for cand in re.findall(r"[A-Za-z0-9+/=]{4,}", re.sub(r"\s+", "", candidate_str)):
                for attempt in (cand, cand + "==", cand + "="):
                    try:
                        decoded = base64.b64decode(attempt)
                        if not decoded:
                            continue
                        _assert_not_sensitive(
                            _decode_nfkc_bytes(decoded),
                            guards,
                            "Access to sensitive keyword blocked in base64",
                        )
                        _check_zlib_bytes(
                            decoded,
                            guards,
                            "Access to sensitive keyword blocked in compressed base64",
                        )
                    except PermissionError:
                        raise
                    except Exception:
                        pass
    except PermissionError:
        raise
    except Exception:
        pass


def _check_base32_candidates(raw_str: str, decoded_str: str, guards: list[HarnessGuard]) -> None:
    """Scan raw and escape-decoded strings for base32-encoded sensitive keywords."""
    try:
        for candidate_str in filter(None, {raw_str, decoded_str}):
            cleaned = re.sub(r"\s+", "", candidate_str)
            for cand in re.findall(r"[A-Z2-7=]{4,}", cleaned, flags=re.IGNORECASE):
                for pad in ("", "====", "===", "==", "="):
                    try:
                        decoded = base64.b32decode((cand + pad).upper().encode("utf-8"))
                        if decoded:
                            _assert_not_sensitive(
                                _decode_nfkc_bytes(decoded),
                                guards,
                                "Access to sensitive keyword blocked in base32",
                            )
                    except PermissionError:
                        raise
                    except Exception:
                        pass
    except PermissionError:
        raise
    except Exception:
        pass


def _check_base85_candidates(raw_str: str, decoded_str: str, guards: list[HarnessGuard]) -> None:
    """Scan raw and escape-decoded strings for base85 and ascii85 obfuscation."""
    decoders = (
        (base64.b85decode, "Access to sensitive keyword blocked in base85"),
        (base64.a85decode, "Access to sensitive keyword blocked in a85"),
    )
    try:
        for candidate_str in filter(None, {raw_str, decoded_str}):
            cleaned = re.sub(r"\s+", "", candidate_str)
            for cand in re.findall(r"[A-Za-z0-9!#$%&()*+-;<=>?@^_`{|}~]{4,}", cleaned):
                for decoder_fn, msg_prefix in decoders:
                    try:
                        decoded = decoder_fn(cand)
                        if decoded:
                            _assert_not_sensitive(_decode_nfkc_bytes(decoded), guards, msg_prefix)
                    except PermissionError:
                        raise
                    except Exception:
                        pass
    except PermissionError:
        raise
    except Exception:
        pass


def _check_hex_candidates(raw_str: str, decoded_str: str, guards: list[HarnessGuard]) -> None:
    """Scan raw and escape-decoded strings for hex and zlib-hex obfuscated sensitive text."""
    try:
        for candidate_str in filter(None, {raw_str, decoded_str}):
            cleaned = re.sub(r"\s+", "", candidate_str)
            for cand in re.findall(r"[0-9a-fA-F]{4,}", cleaned):
                for trimmed in (cand, cand[1:] if len(cand) % 2 != 0 else cand):
                    try:
                        decoded = bytes.fromhex(trimmed)
                        if not decoded:
                            continue
                        _assert_not_sensitive(
                            _decode_nfkc_bytes(decoded),
                            guards,
                            "Access to sensitive keyword blocked in hex",
                        )
                        _check_zlib_bytes(
                            decoded, guards, "Access to sensitive keyword blocked in compressed hex"
                        )
                    except PermissionError:
                        raise
                    except Exception:
                        pass
    except PermissionError:
        raise
    except Exception:
        pass


def _safe_decode_escapes_to_str(raw_bytes: bytes) -> tuple[bytes, str]:
    """Run `_safe_escape_decode` on raw_bytes and return `(decoded_bytes, decoded_str)`."""
    if not raw_bytes:
        return b"", ""
    try:
        decoded_bytes = _safe_escape_decode(raw_bytes)
    except Exception:
        decoded_bytes = raw_bytes
    try:
        decoded_str = _decode_nfkc_bytes(decoded_bytes)
    except Exception:
        decoded_str = ""
    return decoded_bytes, decoded_str


def _check_value_for_sensitive(val: Any, guards: list[HarnessGuard]) -> None:
    """Recursively check str/bytes across raw, symlink, escape, base64/32/85, hex, and zlib."""
    if not val:
        return
    if isinstance(val, str) and val in HarnessState.sensitivity_cache:
        if HarnessState.sensitivity_cache[val]:
            if not any(g._is_approved(val) for g in guards):
                raise PermissionError(f"Access to sensitive keyword blocked (cached): {val}")
            return

    extracted = _extract_raw_str_and_bytes(val)
    if extracted is None:
        return
    raw_str, raw_bytes = extracted

    if raw_str:
        _assert_not_sensitive(raw_str, guards, "Access to sensitive keyword blocked")
    _check_fs_links_sensitive(raw_str, guards)

    decoded_bytes, decoded_str = _safe_decode_escapes_to_str(raw_bytes)
    if decoded_str and decoded_str != raw_str:
        _assert_not_sensitive(decoded_str, guards, "Access to sensitive keyword blocked")

    _check_base64_candidates(raw_str, decoded_str, guards)
    _check_base32_candidates(raw_str, decoded_str, guards)
    _check_base85_candidates(raw_str, decoded_str, guards)
    _check_hex_candidates(raw_str, decoded_str, guards)
    for candidate_bytes in filter(None, {raw_bytes, decoded_bytes}):
        _check_zlib_bytes(
            candidate_bytes, guards, "Access to sensitive keyword blocked in compressed data"
        )
