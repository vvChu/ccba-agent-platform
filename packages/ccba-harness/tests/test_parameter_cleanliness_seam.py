"""Red/Green TDD tests for stdlib parameter & cleanliness seam (WF-05 / PR-3a)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.fast, pytest.mark.unit]

_IPV4_RE = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")


def test_is_statutory_clause_match_golden_corpus() -> None:
    """Verify statutory citation exemptions vs real IPv4 candidates."""
    from ccba_harness import is_statutory_clause_match

    statutory_lines = [
        'body = """5.1.1.1  Việc trang bị cấp nước chữa cháy ngoài nhà.',
        "Các cửa đi phải phù hợp tại 3.2.1.1.",
        "Yêu cầu ngăn cách tuân thủ 2.4.3.3.",
        "Áp dụng theo Điều 1.2.3.4 của QCVN 06.",
        "Xem Mục 2.1.3.4 để tính toán.",
        "Quy định tại Khoản 3.1.2.4 và Bảng 4.1.2.1.",
        "QCVN 3.2.1.1 quy định chiều rộng.",
        "TCVN 1.2.3.4 áp dụng cho kết cấu.",
        "### 1.2.3.4 Tiêu đề điều khoản",
    ]
    for line in statutory_lines:
        matches = list(_IPV4_RE.finditer(line))
        assert matches, f"Expected 4-part dotted clause in: {line}"
        for match in matches:
            assert is_statutory_clause_match(line, match) is True, (
                f"Expected statutory match for {match.group(1)} in {line!r}"
            )

    ip_a = "100.83." + "192.30"
    non_statutory_lines = [
        f'GATEWAY = "http://{ip_a}:8090"',
        'INTERNAL_HOST = "10.0.1.5"',
        'PUBLIC_DNS = "8.8.8.8"',
    ]
    for line in non_statutory_lines:
        matches = list(_IPV4_RE.finditer(line))
        assert matches
        for match in matches:
            assert is_statutory_clause_match(line, match) is False, (
                f"Did not expect statutory match for {match.group(1)} in {line!r}"
            )


def test_scan_raw_ip_and_exemptions(tmp_path: Path) -> None:
    """Verify IPv4 leak detection, loopback/DNS/version/statutory exemptions, and markers."""
    from ccba_harness import scan_parameter_cleanliness

    ip_a = "100.83." + "192.30"
    ip_b = "100.64." + "0.1"
    target = tmp_path / "net_cfg.py"
    sample = (
        f'"""Docstring IP {ip_a} ignored."""\n'
        f"# Comment IP {ip_a} ignored\n"
        'QCVN_TEXT = """5.1.1.1  Cấp nước ngoài nhà.\n'
        "Phù hợp tại 3.2.1.1 và Điều 1.2.3.4.\n"
        'Tuân thủ Mục 2.1.3.4 và Bảng 4.1.2.1."""\n'
        'SCHEMA_VERSION = "15.0.0.0"\n'
        'LOCAL = "http://127.0.0.1:8000"\n'
        'BIND = "0.0.0.0"\n'
        'DNS = ("8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1", "255.255.255.255")\n'
        "EXEMPT_MULTILINE = (\n"
        '    "http://198.51.100.42:8090"\n'
        ")  # ccba:allow-raw-ip\n"
        f'LEAK_A = "http://{ip_a}:8090/v1"\n'
        f'LEAK_B = "{ip_b}"\n'
    )
    target.write_text(sample, encoding="utf-8")

    violations = scan_parameter_cleanliness(target, rules=("raw_ip",))
    assert [(v.line_number, v.rule_name) for v in violations] == [
        (13, "HardcodedNetworkIPViolation"),
        (14, "HardcodedNetworkIPViolation"),
    ]
    assert ip_a in violations[0].message
    assert ip_b in violations[1].message


def test_scan_raw_model_and_aliases(tmp_path: Path) -> None:
    """Verify raw LLM detection vs approved aliases, AST docstrings, and markers."""
    from ccba_harness import scan_parameter_cleanliness

    target = tmp_path / "models_cfg.py"
    code = (
        '"""Module docstring mentioning gpt-4o and gemini-3-flash."""\n'
        'ALIAS_LOCAL = "qwen-local-primary"\n'
        'ALIAS_SHORT = "qwen-local"\n'
        'ALIAS_OCR = "ocr-primary"\n'
        'ALIAS_RAG = "rag-core"\n'
        "EXEMPT = (\n"
        '    "claude-"  # ccba:allow-raw-model\n'
        '    "haiku-4"\n'
        ")\n"
        'BAD_1 = "gemini-3.1-pro-high"\n'
        'BAD_2 = "gpt-4o"\n'
        'BAD_3 = "openai/gemma-4-26b-a4b-it"\n'
        'BAD_4 = "deepseek-v3"\n'
    )
    target.write_text(code, encoding="utf-8")

    violations = scan_parameter_cleanliness(target, rules=("raw_model",))
    assert [v.line_number for v in violations] == [10, 11, 12, 13]
    assert all(v.rule_name == "RawModelStringViolation" for v in violations)

    file_exempt = tmp_path / "bench_models.py"
    file_exempt.write_text('# ccba:allow-raw-model-file\nMODEL = "gpt-4o"\n', encoding="utf-8")
    assert scan_parameter_cleanliness(file_exempt, rules=("raw_model",)) == []


def test_scan_machine_paths_spaces_yaml_posix_and_fallback(tmp_path: Path) -> None:
    """Verify Windows paths with spaces, unquoted YAML, POSIX toggle, and AST/fallback docstrings."""
    from ccba_harness import scan_parameter_cleanliness

    win_space = r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
    py_file = tmp_path / "paths_sample.py"
    py_file.write_text(
        r'r"""Docstring C:\ignored."""' + "\n"
        'DELIM = \'"""\'\n'
        'SP_TOKENS = ("/:f:/g/", "/:v:/r/")\n'
        f'FFMPEG = r"{win_space}"\n'
        'DRIVE_ONLY = r"D:"\n'
        'TRAILING = "D:\\\\"\n'
        'EXEMPT = r"D:\\data"  # ccba:allow-machine-path\n'
        'POSIX_LEAK = "/home/alice/workspace"\n',
        encoding="utf-8",
    )

    win_only = scan_parameter_cleanliness(py_file, rules=("machine_path",), check_posix_home=False)
    assert [v.line_number for v in win_only] == [4, 5, 6]
    assert all(v.rule_name == "HardcodedMachinePathViolation" for v in win_only)

    with_posix = scan_parameter_cleanliness(py_file, rules=("machine_path",), check_posix_home=True)
    assert [v.line_number for v in with_posix] == [4, 5, 6, 8]

    yaml_file = tmp_path / "workspace_context.yaml"
    yaml_file.write_text(
        "project:\n  name: spoke_test\nhub_path: D:\\ccba-agent-platform\nother: C:/tools\n",
        encoding="utf-8",
    )
    yaml_violations = scan_parameter_cleanliness(yaml_file, rules=("machine_path",))
    assert [v.line_number for v in yaml_violations] == [3, 4]

    broken_py = tmp_path / "broken_sample.py"
    broken_py.write_text(
        "def broken(:\n"
        r'    """Single-line C:\ignored"""' + "\n"
        '    """Multi-line\n'
        r'    closing D:\ignored"""' + "\n"
        '    LEAK = r"D:\\real\\leak"\n',
        encoding="utf-8",
    )
    broken_violations = scan_parameter_cleanliness(broken_py, rules=("machine_path",))
    assert [v.line_number for v in broken_violations] == [5]


def test_scan_directory_prunes_venv_by_path_segments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify segment-based directory pruning excludes relative .venv and tests trees."""
    from ccba_harness import scan_parameter_cleanliness

    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / ".venv" / "lib" / "pkg.py").write_text('X = "gpt-4o"\n', encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "sample.py").write_text('X = "gpt-4o"\n', encoding="utf-8")
    (tmp_path / "src").mkdir()
    bad = tmp_path / "src" / "app.py"
    bad.write_text('MODEL = "gpt-4o"\n', encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    violations = scan_parameter_cleanliness(Path("."))
    assert len(violations) == 1
    assert violations[0].file_path.resolve() == bad.resolve()


def test_stdlib_parameter_cleanliness_isolated_without_package_or_yaml(tmp_path: Path) -> None:
    """Verify _parameter_cleanliness.py loads and runs cleanly with ccba_harness=None & yaml=None."""
    mod_path = (
        Path(__file__).resolve().parents[1] / "src" / "ccba_harness" / "_parameter_cleanliness.py"
    )
    assert mod_path.is_file()

    target = tmp_path / "isolated_case.py"
    target.write_text(
        'SAFE_QCVN = "QCVN 3.2.1.1"\nBAD_MODEL = "gpt-4o"\nBAD_WIN = r"C:\\Program Files\\tool.exe"\n',
        encoding="utf-8",
    )

    script = (
        "import importlib.util, json, sys\n"
        "from pathlib import Path\n"
        "sys.modules['ccba_harness'] = None\n"
        "sys.modules['yaml'] = None\n"
        f"spec = importlib.util.spec_from_file_location('_parameter_cleanliness', r'{mod_path}')\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "sys.modules['_parameter_cleanliness'] = mod\n"
        "spec.loader.exec_module(mod)\n"
        f"res = mod.scan_parameter_cleanliness(Path(r'{target}'))\n"
        "print(json.dumps([(v.line_number, v.rule_name) for v in res]))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )
    assert (
        proc.stdout.strip()
        == '[[2, "RawModelStringViolation"], [3, "HardcodedMachinePathViolation"]]'
    )
