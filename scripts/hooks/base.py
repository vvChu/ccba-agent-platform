"""Core Typed Contracts & Base Abstractions for CCBA Lifecycle Hooks.

Defines standard data structures (HookContext, HookResult) and abstract BaseHook
interface for all lifecycle hooks across the platform.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

HookEvent = Literal["session-init", "pre-tool", "post-tool", "user-prompt-submit"]


@dataclass
class HookContext:
    """Encapsulates execution context and parameters for a lifecycle hook event."""

    event: str
    tool: str = ""
    path: str = ""
    args: str = ""
    cwd: str = ""
    status: str = ""
    raw_payload: dict[str, Any] = field(default_factory=dict)

    @property
    def is_approved(self) -> bool:
        """Checks whether the operation has explicit user approval via 'APPROVED:' keyword."""
        if self.path and self.path.startswith("APPROVED:"):
            return True
        if self.args and "APPROVED:" in self.args:
            return True
        if self.status and "APPROVED:" in self.status:
            return True
        return False

    @property
    def clean_path(self) -> str:
        """Returns the file path with 'APPROVED:' prefix stripped."""
        if self.path and self.path.startswith("APPROVED:"):
            return self.path.replace("APPROVED:", "", 1)
        return self.path

    @property
    def parsed_args(self) -> dict[str, Any]:
        """Returns JSON-decoded arguments dict or empty dict if unparsable."""
        if not self.args:
            return {}
        try:
            val = json.loads(self.args)
            return val if isinstance(val, dict) else {}
        except (ValueError, TypeError, json.JSONDecodeError):
            return {}

    @classmethod
    def from_payload(cls, event: str, payload: dict[str, Any] | None = None) -> HookContext:
        """Constructs a typed HookContext from a raw dictionary payload."""
        data = payload or {}
        return cls(
            event=event,
            tool=str(data.get("tool") or ""),
            path=str(data.get("path") or ""),
            args=str(data.get("args") or ""),
            cwd=str(data.get("cwd") or ""),
            status=str(data.get("status") or ""),
            raw_payload=data,
        )


@dataclass
class HookResult:
    """Standardized result returned by all hook executions."""

    name: str
    exit_code: int = 0  # 0 = PASS/ALLOW, 1 = WARN/CHECK_FAIL, 2 = BLOCK
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_blocked(self) -> bool:
        """True if the hook issued a hard block (exit_code == 2)."""
        return self.exit_code == 2

    @property
    def is_warning(self) -> bool:
        """True if the hook issued a warning (exit_code == 1)."""
        return self.exit_code == 1

    @property
    def is_passed(self) -> bool:
        """True if the hook passed without violations (exit_code == 0)."""
        return self.exit_code == 0


class BaseHook(ABC):
    """Abstract base class for all CCBA lifecycle hooks."""

    name: str = "base_hook"
    supported_events: tuple[str, ...] = ()

    @abstractmethod
    def execute(self, context: HookContext) -> HookResult:
        """Executes hook inspection and returns a typed HookResult.

        Args:
            context: The encapsulated HookContext.

        Returns:
            HookResult containing exit code, message, and diagnostic details.
        """
        raise NotImplementedError

    def __call__(self, context: HookContext) -> HookResult:
        """Allows calling hook instances as callables."""
        return self.execute(context)
