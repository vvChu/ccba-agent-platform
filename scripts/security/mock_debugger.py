#!/usr/bin/env python3
"""
Self-Healing Mock Debugger for ccba-agent-platform.
Runs a Python script, captures any traceback, and uses AI Gateway
to analyze the root cause and automatically suggest or apply a fix.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from ccba_ai import ai



def run_target_script(script_path: Path, args: list) -> tuple[int, str, str]:
    """Execute the target Python script and return returncode, stdout, and stderr."""
    cmd = [sys.executable, str(script_path)] + args
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired as e:
        return -1, "", f"Execution timed out: {e}"
    except Exception as e:
        return -1, "", f"Failed to execute script: {e}"


def analyze_error(script_path: Path, stderr: str) -> str:
    """Use AI Gateway to analyze the traceback and recommend a fix."""
    try:
        source_code = script_path.read_text(encoding="utf-8")
    except Exception as e:
        source_code = f"Could not read source code: {e}"

    prompt = f"""
    Bạn là một kỹ sư Python chuyên nghiệp, đang thực thi quy trình chẩn đoán lỗi sâu (diagnosing-bugs discipline).
    Một kịch bản chạy thử nghiệm đã bị lỗi crash. Hãy phân tích vết lỗi (traceback) và mã nguồn.

    Đường dẫn tệp lỗi: {script_path}

    Vết lỗi (Traceback/Stderr):
    \"\"\"
    {stderr}
    \"\"\"

    Mã nguồn hiện tại:
    ```python
    {source_code}
    ```

    Hãy phản hồi ngắn gọn bằng tiếng Việt, cấu trúc theo quy chuẩn chẩn đoán lỗi chuyên sâu:

    1. 🔍 Phân tích Nguyên nhân gốc rễ (Root Cause Analysis).
    2. 📊 Danh sách 3-5 giả định xếp hạng (Ranked Hypotheses) có tính chất kiểm chứng được (Falsifiable):
       - Định dạng: "Nếu giả định <X> đúng, việc thay đổi <Y> sẽ làm lỗi biến mất / thay đổi <Z> sẽ làm lỗi nặng hơn."
    3. 🎯 Đề xuất thiết lập vòng lặp phản hồi (Feedback Loop Recommendation):
       - Đề xuất cách viết test case hoặc kịch bản chạy tối thiểu (nhanh, deterministic, agent-runnable) để tái hiện lỗi này.
    4. 🛠️ Đề xuất sửa đổi (Proposed Patch/Diff) cho giả định khả thi nhất.
    5. 🧪 Gợi ý mối nối kiểm thử hồi quy (Regression Test Seam):
       - Đề xuất vị trí viết kiểm thử hồi quy (seam) để khóa lỗi này vĩnh viễn.
    """

    try:
        print("[Mock Debugger] Requesting AI Gateway analysis...")
        reply = ai.chat(prompt)
        return reply
    except Exception as e:
        return f"Error calling AI Gateway: {e}"


def main() -> None:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="CCBA Self-Healing Mock Debugger")

    parser.add_argument("script", help="Path to the Python script to run and debug")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments to pass to the script")

    args = parser.parse_args()
    script_path = Path(args.script)

    if not script_path.exists():
        print(f"[Mock Debugger] Error: Script '{args.script}' not found.")
        sys.exit(1)

    print(f"[Mock Debugger] Running target script: \x1b[36m{script_path.name}\x1b[0m...")
    ret_code, stdout, stderr = run_target_script(script_path, args.args)

    if ret_code == 0:
        print(
            "\x1b[32m[Mock Debugger] Script executed successfully with exit code 0. No debugging needed.\x1b[0m"
        )
        if stdout:
            print("\nStdout:")
            print(stdout)
        sys.exit(0)

    print(f"\x1b[31m[Mock Debugger] Script crashed with exit code {ret_code}!\x1b[0m")
    if stdout:
        print("\nStdout:")
        print(stdout)
    if stderr:
        print("\nStderr/Traceback:")
        print(stderr)

    print("\n" + "=" * 60)
    print("🧠 TỰ ĐỘNG PHÂN TÍCH LỖI VÀ ĐỀ XUẤT SỬA ĐỔI")
    print("=" * 60)

    analysis = analyze_error(script_path, stderr)
    print(analysis)
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
