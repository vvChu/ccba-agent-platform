"""ccba_harness.cli - Command-Line Interface package for ccba-harness.

Employs PEP 562 lazy __getattr__ to provide 100% backward-compatible symbol re-exports
without incurring top-level startup import overhead.
"""

from __future__ import annotations

import importlib
from typing import Any

from .core import main

__all__ = [
    "main",
    "run_skill_validation_cli",
    "run_evaluate_gpi_cli",
    "run_eval_cli",
    "run_verify_doc_cli",
    "run_verify_patch_cli",
    "run_telemetry_cli",
    "run_peer_gate_cli",
    "run_blast_radius_cli",
    "run_explain_why_cli",
    "run_peer_watch_cli",
    "run_peer_dispatch_cli",
    "run_peer_co_review_cli",
    "run_apply_anchor_patch_cli",
    "find_workspace_root",
    "resolve_peer_exchange_dir",
]

_SYMBOL_MAP: dict[str, str] = {
    "run_skill_validation_cli": "ccba_harness.cli.commands.evals",
    "run_evaluate_gpi_cli": "ccba_harness.cli.commands.evals",
    "run_eval_cli": "ccba_harness.cli.commands.evals",
    "run_verify_doc_cli": "ccba_harness.cli.commands.verifier",
    "run_verify_patch_cli": "ccba_harness.cli.commands.verifier",
    "run_telemetry_cli": "ccba_harness.cli.commands.telemetry",
    "run_peer_gate_cli": "ccba_harness.cli.commands.peer",
    "run_peer_watch_cli": "ccba_harness.cli.commands.peer",
    "run_peer_dispatch_cli": "ccba_harness.cli.commands.peer",
    "run_peer_co_review_cli": "ccba_harness.cli.commands.peer",
    "run_apply_anchor_patch_cli": "ccba_harness.cli.commands.peer",
    "find_workspace_root": "ccba_harness.cli.commands.peer",
    "resolve_peer_exchange_dir": "ccba_harness.cli.commands.peer",
    "run_blast_radius_cli": "ccba_harness.cli.commands.architecture",
    "run_explain_why_cli": "ccba_harness.cli.commands.architecture",
}


def __getattr__(name: str) -> Any:
    """PEP 562 dynamic attribute loader for backward-compatible symbol re-exports."""
    if name in _SYMBOL_MAP:
        mod = importlib.import_module(_SYMBOL_MAP[name])
        attr = getattr(mod, name)
        # Cache in module globals for subsequent instant lookups
        globals()[name] = attr
        return attr
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
