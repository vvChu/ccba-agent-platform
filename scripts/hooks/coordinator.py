"""Hook Coordinator for orchestrating lifecycle hooks across the CCBA Platform.

Manages hook registry, event dispatching, and aggregated exit-code computation.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from typing import Any

from .base import BaseHook, HookContext, HookResult
from .brand import BrandHook
from .naming import NamingHook
from .privacy import PrivacyHook
from .scout import ScoutBlockHook
from .session import SessionInitHook
from .simplify import SimplifyGateHook


class HookCoordinator:
    """Central manager for registering and executing lifecycle hooks."""

    def __init__(self) -> None:
        self._hooks: dict[str, list[BaseHook]] = {
            "session-init": [],
            "pre-tool": [],
            "post-tool": [],
            "user-prompt-submit": [],
        }

    def register_hook(self, event: str, hook: BaseHook) -> None:
        """Registers a hook instance for a specific lifecycle event."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(hook)

    def get_hooks(self, event: str) -> list[BaseHook]:
        """Returns the list of hooks registered for a given event."""
        return self._hooks.get(event, [])

    def run_event(
        self, event: str, payload_or_context: dict[str, Any] | HookContext
    ) -> tuple[int, list[HookResult]]:
        """Executes all registered hooks for the event and computes aggregate exit code.

        Args:
            event: Lifecycle event name.
            payload_or_context: Dictionary payload or initialized HookContext.

        Returns:
            Tuple of (max_exit_code, list_of_HookResult).
        """
        if isinstance(payload_or_context, HookContext):
            context = payload_or_context
        else:
            context = HookContext.from_payload(event, payload_or_context)

        hooks = self.get_hooks(event)
        results: list[HookResult] = []

        for hook in hooks:
            try:
                res = hook.execute(context)
                results.append(res)
            except Exception as e:
                err_res = HookResult(
                    name=hook.name,
                    exit_code=1,
                    message=f"Exception in hook '{hook.name}': {e}",
                    details={"error": str(e)},
                )
                results.append(err_res)

        max_code = max([r.exit_code for r in results], default=0)
        return max_code, results


def get_default_coordinator() -> HookCoordinator:
    """Constructs and returns a HookCoordinator pre-configured with all standard CCBA hooks."""
    coord = HookCoordinator()

    # Session Initialization
    coord.register_hook("session-init", SessionInitHook())

    # Pre-tool Execution Safeguards
    coord.register_hook("pre-tool", PrivacyHook())
    coord.register_hook("pre-tool", ScoutBlockHook())
    coord.register_hook("pre-tool", NamingHook())
    coord.register_hook("pre-tool", SimplifyGateHook())

    # Post-tool Execution Auditing
    coord.register_hook("post-tool", BrandHook())

    # Prompt Submission Gates
    coord.register_hook("user-prompt-submit", SimplifyGateHook())

    return coord
