"""Unit tests for CCBA Platform console scripts and repaired import paths."""

import importlib


def test_repaired_log_eval_miner_imports():
    """Verify log_eval_miner module re-exports mine_logs_and_export correctly."""
    from scripts.eval.log_eval_miner import mine_logs_and_export as deep_miner
    from scripts.log_eval_miner import mine_logs_and_export as shim_miner

    assert callable(deep_miner)
    assert callable(shim_miner)
    assert deep_miner is shim_miner


def test_repaired_legal_sync_imports():
    """Verify legal_sync module re-exports GOOGLE_API_AVAILABLE and get_drive_service."""
    from scripts.legal_sync import GOOGLE_API_AVAILABLE as shim_flag
    from scripts.legal_sync import get_drive_service as shim_get

    from ccba_legal.sync import GOOGLE_API_AVAILABLE as deep_flag
    from ccba_legal.sync import get_drive_service as deep_get

    assert isinstance(deep_flag, bool)
    assert isinstance(shim_flag, bool)
    assert deep_flag == shim_flag
    assert callable(deep_get)
    assert callable(shim_get)


def test_console_scripts_entry_points_resolvable():
    """Verify all pyproject.toml console script target functions exist and are callable."""
    targets = [
        ("scripts.eval.run_harness_evals", "main"),
        ("scripts.eval.run_isolated_tests", "main"),
        ("scripts.spoke.compile_knowledge", "main"),
        ("scripts.legal.legal_sync", "main"),
        ("scripts.validation.audit_pr_comments", "main"),
        ("scripts.spoke.find_skills", "main"),
        ("scripts.validation.seo_audit", "main"),
    ]

    for module_name, func_name in targets:
        mod = importlib.import_module(module_name)
        func = getattr(mod, func_name, None)
        assert func is not None, f"Missing function {func_name} in {module_name}"
        assert callable(func), f"Attribute {func_name} in {module_name} is not callable"
