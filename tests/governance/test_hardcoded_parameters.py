#!/usr/bin/env python3
"""tests/governance/test_hardcoded_parameters.py

Unit tests for scripts/governance/check_hardcoded_parameters.py:
Verifies AST detection of raw model strings, hardcoded network IPs, and machine paths.
"""

from __future__ import annotations

from pathlib import Path

from scripts.governance.check_hardcoded_parameters import (
    check_file_content,
    is_whitelisted_file,
)


def test_detects_raw_model_string_in_call() -> None:
    code = """
def run_task():
    res = ai.chat("test", model="gemini-3.1-pro-high")
    return res
"""
    violations = check_file_content(Path("src/service.py"), code)
    assert len(violations) == 1
    assert violations[0].rule_name == "RawModelStringViolation"
    assert "gemini-3.1-pro-high" in violations[0].message


def test_allows_model_archetype_or_choose_model() -> None:
    code = """
from ccba_ai.routing import ModelArchetype, choose_model

def run_task():
    res1 = ai.chat("test", model=ModelArchetype.STANDARD)
    res2 = ai.chat("test", model=choose_model("fast"))
    return res1, res2
"""
    violations = check_file_content(Path("src/service.py"), code)
    assert len(violations) == 0


def test_allows_raw_model_with_annotation() -> None:
    code = """
def run_task():
    res = ai.chat("test", model="gemini-3.1-pro-high")  # ccba:allow-raw-model
    return res
"""
    violations = check_file_content(Path("src/service.py"), code)
    assert len(violations) == 0


def test_whitelists_routing_module() -> None:
    path = Path("packages/ccba-ai/src/ccba_ai/routing.py")
    assert is_whitelisted_file(path) is True


def test_whitelists_test_files() -> None:
    path = Path("packages/ccba-ai/tests/test_client.py")
    assert is_whitelisted_file(path) is True


def test_detects_hardcoded_ip() -> None:
    code = """
def connect():
    url = "http://100.83.192.30:8090/v1/chat"
    return url
"""
    violations = check_file_content(Path("src/adapter.py"), code)
    assert len(violations) == 1
    assert violations[0].rule_name == "HardcodedNetworkIPViolation"
    assert "100.83.192.30" in violations[0].message


def test_allows_ip_with_annotation() -> None:
    code = """
def connect():
    url = "http://100.83.192.30:8090/v1/chat"  # ccba:allow-raw-ip
    return url
"""
    violations = check_file_content(Path("src/adapter.py"), code)
    assert len(violations) == 0


def test_allows_localhost_and_loopback() -> None:
    code = """
def connect():
    url1 = "http://127.0.0.1:8000/v1"
    url2 = "http://0.0.0.0:8080"
    url3 = "http://localhost:8090"
    return url1, url2, url3
"""
    violations = check_file_content(Path("src/adapter.py"), code)
    assert len(violations) == 0


def test_detects_hardcoded_windows_drive_path() -> None:
    code = """
from pathlib import Path

def get_bin():
    return Path(r"C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe")
"""
    violations = check_file_content(Path("src/media.py"), code)
    assert len(violations) == 1
    assert violations[0].rule_name == "HardcodedMachinePathViolation"


def test_allows_windows_path_with_annotation() -> None:
    code = """
from pathlib import Path

def get_bin():
    return Path(r"C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe")  # ccba:allow-machine-path
"""
    violations = check_file_content(Path("src/media.py"), code)
    assert len(violations) == 0
