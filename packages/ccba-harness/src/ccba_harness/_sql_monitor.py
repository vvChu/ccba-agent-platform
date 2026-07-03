"""
SQL and SQLite monitoring hooks for the harness sub-package.

Responsibilities:
- Sanitise SQL queries for ATTACH/VACUUM INTO path injection
- Wrap sqlite3.connect / sqlite3.Connection / Cursor to intercept calls
- Block access to sensitive database paths

Design note: ``_check_value_for_sensitive`` lives in ``harness/__init__.py``
until the file-monitor step migrates it.  We import it lazily inside
``_check_sql_query`` to avoid a circular import at module load time.
"""

from __future__ import annotations

import os
import re
import urllib.parse
from typing import Any

from ._state import (
    _HOOK_TOKEN,
    _check_in_hook,
    _get_active_guards,
    _local,
    _original_sqlite3_connect,
    _Originals,
)

# ---------------------------------------------------------------------------
# Pure SQL text utilities
# ---------------------------------------------------------------------------


def _strip_comments_from_sql(sql: str) -> str:
    """Remove SQL block and line comments from *sql*."""
    # First, strip block comments /* ... */
    # Replace with a space to preserve separation
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    # Then strip line comments -- ...
    sql = re.sub(r"--.*?(?=\r?\n|$)", " ", sql)
    return sql


def _extract_attached_db_paths(sql: str) -> list[str]:
    """Return a list of database paths referenced in ATTACH statements."""
    sql = _strip_comments_from_sql(sql)
    quoted = re.findall(r'(?i)\bATTACH\b\s+(?:DATABASE\s+)?([\'""])(.*?)\1', sql)
    paths = [q[1] for q in quoted]
    unquoted = re.findall(r'(?i)\bATTACH\b\s+(?:DATABASE\s+)?([^\s\'"]+)', sql)
    for p in unquoted:
        if p and not p.startswith(("'", '"')):
            if p.lower() != "database":
                paths.append(p)
    return paths


def _clean_and_decode_db_path(path: str) -> str:
    """URL-decode and normalise a database path string."""
    decoded = path
    for _ in range(10):
        next_decoded = urllib.parse.unquote(decoded)
        if next_decoded == decoded:
            break
        decoded = next_decoded
    if decoded.lower().startswith("file:"):
        decoded = decoded[5:]
        if decoded.startswith("///"):
            decoded = decoded[3:]
        elif decoded.startswith("//"):
            decoded = decoded[2:]
        if "?" in decoded:
            decoded = decoded.split("?")[0]
    return decoded


# ---------------------------------------------------------------------------
# Guard-aware DB path / query checkers
# ---------------------------------------------------------------------------


def _check_db_path(path_str: str) -> None:
    """Raise PermissionError if *path_str* points to a sensitive database."""
    guards = _get_active_guards()
    if not guards:
        return
    decoded = _clean_and_decode_db_path(path_str)
    for g in guards:
        if g._is_sensitive(decoded) and not g._is_approved(decoded):
            raise PermissionError(f"Access to sensitive database blocked: {path_str}")


def _check_sql_query(sql: Any) -> None:
    """Inspect *sql* and raise PermissionError for dangerous operations."""
    if sql is None:
        return
    try:
        sql_str = str(sql)
    except Exception:
        return
    sql_upper = sql_str.upper()

    if "VACUUM" in sql_upper and "INTO" in sql_upper:
        sql_clean = _strip_comments_from_sql(sql_str)
        for m in re.finditer(r"(?i)\bINTO\b\s*(?:'([^']*)'|\"([^\"]*)\"|([^\s;'\"]+))", sql_clean):
            path = m.group(1) or m.group(2) or m.group(3)
            if path:
                _check_db_path(path)

    # Block ATTACH expression / concatenation bypasses
    if "ATTACH" in sql_upper:
        guards = _get_active_guards()
        if guards:
            # Lazy import to avoid circular dependency
            try:
                from . import _check_value_for_sensitive as _cvs
            except (ImportError, AttributeError):
                _cvs = None

            if _cvs is not None:
                # Scan the entire query text for sensitive keywords
                try:
                    _cvs(sql_str, guards)
                except PermissionError as pe:
                    raise PermissionError(
                        f"Access to sensitive database blocked in ATTACH query: {pe}"
                    ) from pe

                # Strip concat operators, quotes, comments, parentheses, spaces
                sql_clean = _strip_comments_from_sql(sql_str)
                stripped = re.sub(r"[\s+|'\"(),;/\*#\-]+", "", sql_clean)
                try:
                    _cvs(stripped, guards)
                except PermissionError as pe:
                    raise PermissionError(
                        f"Access to sensitive database blocked in ATTACH query: {pe}"
                    ) from pe

        cleaned_sql = _strip_comments_from_sql(sql_str)
        match = re.search(r"(?i)\bATTACH\b\s+(?:DATABASE\s+)?(.*?)\bAS\b", cleaned_sql, re.DOTALL)
        if match:
            expr = match.group(1).strip()
            expr_upper = expr.upper()
            if "CHAR" in expr_upper and re.search(r"(?i)\bchar\s*\(", expr):
                raise PermissionError("SQLite ATTACH with char() is blocked")
            if "CAST" in expr_upper and re.search(r"(?i)\bcast\s*\(", expr):
                raise PermissionError("SQLite ATTACH with CAST() is blocked")
            if "||" in expr or "+" in expr:
                raise PermissionError("SQLite ATTACH with concatenation is blocked")
            if "(" in expr or ")" in expr:
                raise PermissionError("SQLite ATTACH with parentheses is blocked")
            if re.search(r"(?i)\bx\s*'", expr):
                raise PermissionError("SQLite ATTACH with hex literal is blocked")

        literals = re.findall(r"'([^']*)'|\"([^\"]*)\"", sql_str)
        lit_strings = []
        for g1, g2 in literals:
            lit_strings.append(g1 or g2 or "")
        for s in lit_strings:
            _check_db_path(s)
        concat_lits = "".join(lit_strings)
        _check_db_path(concat_lits)

    attached_paths = _extract_attached_db_paths(sql_str)
    for p in attached_paths:
        _check_db_path(p)


# ---------------------------------------------------------------------------
# sqlite3 wrappers
# ---------------------------------------------------------------------------


class _WrappedCursor:
    """Thin cursor wrapper that inspects every SQL statement before execution."""

    def __init__(self, original_cursor: Any) -> None:
        self._orig_cursor = original_cursor

    def execute(self, sql: Any, *args: Any, **kwargs: Any) -> Any:
        _check_sql_query(sql)
        res = self._orig_cursor.execute(sql, *args, **kwargs)
        if res is self._orig_cursor:
            return self
        return res

    def executemany(self, sql: Any, *args: Any, **kwargs: Any) -> Any:
        _check_sql_query(sql)
        res = self._orig_cursor.executemany(sql, *args, **kwargs)
        if res is self._orig_cursor:
            return self
        return res

    def executescript(self, sql_script: Any, *args: Any, **kwargs: Any) -> Any:
        _check_sql_query(sql_script)
        res = self._orig_cursor.executescript(sql_script, *args, **kwargs)
        if res is self._orig_cursor:
            return self
        return res

    def __getattr__(self, name: str) -> Any:
        return getattr(self._orig_cursor, name)

    def __iter__(self) -> Any:
        return iter(self._orig_cursor)


class _Wrappedsqlite3Connection(_Originals.sqlite3_Connection):
    """sqlite3.Connection subclass that enforces path and SQL guards."""

    def __init__(self, database: Any, *args: Any, **kwargs: Any) -> None:
        if _check_in_hook():
            super().__init__(database, *args, **kwargs)
            return

        guards = _get_active_guards()
        if not guards:
            super().__init__(database, *args, **kwargs)
            return

        _local.__dict__["in_hook"] = _HOOK_TOKEN
        try:
            if database is not None:
                db_str = (
                    os.fspath(database)
                    if isinstance(database, (str, bytes, os.PathLike))
                    else str(database)
                )
                if isinstance(db_str, bytes):
                    db_str = db_str.decode("utf-8", errors="replace")

                if db_str != ":memory:" and db_str.lower() != ":memory:":
                    _check_db_path(db_str)
            super().__init__(database, *args, **kwargs)
        finally:
            _local.__dict__["in_hook"] = None

    def execute(self, sql: Any, *args: Any, **kwargs: Any) -> Any:
        _check_sql_query(sql)
        return super().execute(sql, *args, **kwargs)

    def executemany(self, sql: Any, *args: Any, **kwargs: Any) -> Any:
        _check_sql_query(sql)
        return super().executemany(sql, *args, **kwargs)

    def executescript(self, sql_script: Any, *args: Any, **kwargs: Any) -> Any:
        _check_sql_query(sql_script)
        return super().executescript(sql_script, *args, **kwargs)

    def cursor(self, *args: Any, **kwargs: Any) -> Any:
        cursor_obj = super().cursor(*args, **kwargs)
        return _WrappedCursor(cursor_obj)


def _wrapped_sqlite3_connect(*args: Any, **kwargs: Any) -> Any:
    """Replacement for ``sqlite3.connect`` that enforces DB path guards."""
    if _check_in_hook():
        return _original_sqlite3_connect(*args, **kwargs)

    guards = _get_active_guards()
    if not guards:
        return _original_sqlite3_connect(*args, **kwargs)

    _local.__dict__["in_hook"] = _HOOK_TOKEN
    try:
        database = args[0] if len(args) > 0 else kwargs.get("database")
        if database is not None:
            db_str = os.fspath(database)
            if isinstance(db_str, bytes):
                db_str = db_str.decode("utf-8", errors="replace")

            if db_str != ":memory:" and db_str.lower() != ":memory:":
                _check_db_path(db_str)

        kwargs["factory"] = _Wrappedsqlite3Connection
        return _original_sqlite3_connect(*args, **kwargs)
    finally:
        _local.__dict__["in_hook"] = None
