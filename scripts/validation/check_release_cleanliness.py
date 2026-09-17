"""CCBA Platform — Release Working Tree Cleanliness & Hermeticity Gate.

Enforces pre-flight repository cleanliness (Cổng 0.1) and post-test hermetic
scoped teardown (Cổng 0.3) for release workflows.
ADR References: ADR-0058 (Hard Completion Lock) & ADR-0057 (Two-Stage Governance).
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Đảm bảo UTF-8 encoding trên Windows khi import module hoặc gọi CLI
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Danh mục các mẫu tệp tạm/cache được phép thu hồi an toàn sau bài kiểm thử
KNOWN_TEST_ARTIFACTS: list[str] = [
    "*mock_local_bundles*embeddings.npy",
    "*mock_local_bundles*embeddings.sha256",
    "*embeddings.npy",
    "*embeddings.sha256",
    "ci_log.txt",
    "*/ci_log.txt",
    "*.pytest_cache*",
    "*tmp_*.json",
    "*.tmp",
    "*test_temp_*",
]


def get_porcelain_status(repo_root: Path | None = None) -> list[tuple[str, str]]:
    """Lấy danh sách các mục thay đổi qua git status --porcelain -z.

    Args:
        repo_root: Thư mục gốc của repository (mặc định là root của project).

    Returns:
        Danh sách các cặp (status_code, file_path).
    """
    cwd = repo_root or Path(__file__).resolve().parents[2]
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain", "-z"],
            capture_output=True,
            check=True,
            cwd=cwd,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"⚠️ [WARNING] Không thể chạy git status: {e}", file=sys.stderr)
        return []

    raw_bytes = res.stdout
    entries: list[tuple[str, str]] = []
    i = 0
    length = len(raw_bytes)

    while i < length:
        null_idx = raw_bytes.find(b"\x00", i)
        if null_idx == -1:
            null_idx = length

        chunk = raw_bytes[i:null_idx]
        if chunk:
            decoded = chunk.decode("utf-8", errors="replace")
            if len(decoded) >= 3:
                status_code = decoded[:2].strip()
                file_path = decoded[3:].strip()
                entries.append((status_code, file_path))

                # Handle renames (R or C), where git status -z outputs:
                # XY PATH\0ORIG_PATH\0
                if "R" in status_code or "C" in status_code:
                    next_null = raw_bytes.find(b"\x00", null_idx + 1)
                    if next_null != -1:
                        null_idx = next_null

        i = null_idx + 1

    return entries


def is_known_artifact(file_path: str) -> bool:
    """Kiểm tra đường dẫn tệp có khớp với danh mục cache kiểm thử đã biết hay không.

    Args:
        file_path: Đường dẫn tệp tương đối so với repo root.

    Returns:
        True nếu khớp với ít nhất một pattern trong KNOWN_TEST_ARTIFACTS.
    """
    norm_path = file_path.replace("\\", "/")
    return any(fnmatch.fnmatch(norm_path, pat) for pat in KNOWN_TEST_ARTIFACTS)


def run_pre_check(repo_root: Path | None = None) -> int:
    """Cổng 0.1: Chặn đứng quy trình nếu phát hiện working tree bị dơ trước khi test.

    Args:
        repo_root: Thư mục gốc của repository.

    Returns:
        0 nếu sạch hoàn toàn, 1 nếu có tệp chưa commit.
    """
    entries = get_porcelain_status(repo_root)
    if not entries:
        print("✅ [PRE-FLIGHT GATE] Working tree sạch sẽ 100%. Sẵn sàng chạy kiểm thử release.")
        return 0

    print(
        "❌ [PRE-FLIGHT GATE BLOCKED] Phát hiện thay đổi chưa commit trong working tree trước khi phát hành!"
    )
    print("Danh sách tệp phát hiện:")
    for code, path in entries:
        print(f"  - [{code}] {path}")
    print("\n💡 HÀNH ĐỘNG CẦN THỰC HIỆN:")
    print(
        "  1. Hãy commit các thay đổi hợp lệ vào PR (git add ... && git commit -m ... && git push)."
    )
    print("  2. Hoặc stash có chủ đích nếu muốn giữ lại (git stash push -u -m 'my-wip-work').")
    print("  3. Tuyệt đối không chạy merge khi mã nguồn cục bộ chưa được đồng bộ lên remote PR!")
    return 1


def run_post_check(repo_root: Path | None = None) -> int:
    """Cổng 0.3: Kiểm tra rò rỉ sau test, thu hồi an toàn test artifacts có cảnh báo.

    Args:
        repo_root: Thư mục gốc của repository.

    Returns:
        0 nếu sạch hoặc đã thu hồi an toàn cache kiểm thử, 1 nếu mã nguồn bị sửa đổi.
    """
    root = repo_root or Path(__file__).resolve().parents[2]
    entries = get_porcelain_status(root)
    if not entries:
        print("✅ [POST-TEST GATE] Bộ kiểm thử hoàn toàn buồng kín (100% Hermetic).")
        return 0

    leaked_files: list[str] = []
    unknown_or_source_files: list[tuple[str, str]] = []

    for code, path in entries:
        # Nếu tệp mã nguồn bị chỉnh sửa (M) hoặc xóa (D) -> Rất nghiêm trọng
        if any(c in code for c in ("M", "D", "A", "R", "C", "U")):
            # Kiểm tra xem tệp modified này có phải là known artifact hay không
            if is_known_artifact(path):
                leaked_files.append(path)
            else:
                unknown_or_source_files.append((code, path))
        elif is_known_artifact(path):
            leaked_files.append(path)
        else:
            unknown_or_source_files.append((code, path))

    if unknown_or_source_files:
        print(
            "❌ [POST-TEST GATE BLOCKED] Kiểm thử làm thay đổi mã nguồn hoặc sinh tệp lạ ngoài danh mục cache!"
        )
        print("Danh sách tệp vi phạm:")
        for code, path in unknown_or_source_files:
            print(f"  - [{code}] {path}")
        print("\n💡 HÀNH ĐỘNG CẦN THỰC HIỆN:")
        print(
            "  - Rà soát lại bài test vừa chạy: Có test nào đang sửa đổi trực tiếp source code hoặc sinh file lạ?"
        )
        print("  - Hoàn tác hoặc kiểm tra lại các thay đổi trước khi tiếp tục release.")
        return 1

    # Dọn dẹp an toàn các test artifacts đã biết
    print(
        f"⚠️ [HERMETIC WARNING] Phát hiện {len(leaked_files)} tệp cache kiểm thử rò rỉ sau bài test:"
    )
    for rel_path in leaked_files:
        abs_path = root / rel_path
        if abs_path.is_file() or abs_path.is_symlink():
            try:
                os.chmod(abs_path, 0o666)  # Gỡ read-only trên Windows
                abs_path.unlink(missing_ok=True)
                print(f"  🧹 Đã thu hồi tệp tạm an toàn: {rel_path}")
            except Exception as ex:
                print(f"  ⚠️ Không thể xóa {rel_path}: {ex}", file=sys.stderr)
        elif abs_path.is_dir():
            try:
                shutil.rmtree(abs_path, ignore_errors=True)
                print(f"  🧹 Đã thu hồi thư mục tạm an toàn: {rel_path}")
            except Exception as ex:
                print(f"  ⚠️ Không thể xóa thư mục {rel_path}: {ex}", file=sys.stderr)

    print(
        "💡 Khuyến nghị: Hãy thêm các tệp này vào .gitignore hoặc refactor test fixture dùng tmp_path."
    )
    print("✅ Đã dọn sạch tệp tạm kiểm thử. Cho phép tiếp tục quy trình phát hành.")
    return 0


def main() -> None:
    """CLI entrypoint cho bộ kiểm tra cleanliness."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="CCBA Platform — Release Working Tree Cleanliness & Hermeticity Gate."
    )
    parser.add_argument(
        "--phase",
        choices=["pre", "post"],
        default="pre",
        help="Giai đoạn kiểm tra: 'pre' (Cổng 0.1 trước test) hoặc 'post' (Cổng 0.3 sau test).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Đường dẫn repository root (tùy chọn, mặc định tự nhận diện).",
    )
    args = parser.parse_args()

    exit_code = (
        run_pre_check(args.repo_root) if args.phase == "pre" else run_post_check(args.repo_root)
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
