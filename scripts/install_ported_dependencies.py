"""Script cài đặt tự động dependencies cho các kỹ năng được port từ ClaudeKit.

Cài đặt các Node.js packages (docx) và Python packages (python-docx, Pillow, pypdf, google-genai)
phù hợp với môi trường Windows và môi trường ảo .venv cục bộ.
"""

# Khắc phục lỗi mã hóa Unicode trên Windows Console
import io
import os
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def check_command_exists(cmd: str) -> bool:
    """Kiểm tra một lệnh hệ thống có tồn tại hay không.

    Args:
        cmd: Tên lệnh cần kiểm tra.

    Returns:
        True nếu lệnh tồn tại, ngược lại là False.
    """
    return shutil.which(cmd) is not None


def install_python_packages(packages: list[str]) -> bool:
    """Cài đặt các gói Python vào môi trường ảo .venv hiện tại.

    Args:
        packages: Danh sách các gói cần cài đặt.

    Returns:
        True nếu cài đặt thành công, ngược lại là False.
    """
    print(f"[Python] Đang cài đặt các gói: {', '.join(packages)}...")

    # Xác định đường dẫn pip trong môi trường ảo
    venv_pip = os.path.join(".venv", "Scripts", "pip.exe")
    if not os.path.exists(venv_pip):
        # Fallback về pip hệ thống nếu không tìm thấy .venv
        venv_pip = "pip"
        print("[Python] Cảnh báo: Không tìm thấy môi trường ảo .venv. Sử dụng pip hệ thống.")

    try:
        cmd = [venv_pip, "install", "--upgrade"] + packages
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("[Python] Cài đặt thành công!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[Python] Lỗi cài đặt gói: {e}")
        print(f"[Python] Chi tiết lỗi:\n{e.stderr}")
        return False


def install_nodejs_packages() -> bool:
    """Cài đặt các gói Node.js cần thiết cục bộ.

    Returns:
        True nếu cài đặt thành công hoặc đã có sẵn, ngược lại là False.
    """
    if not check_command_exists("npm"):
        print("[Node.js] Cảnh báo: Không tìm thấy npm trên hệ thống. Bỏ qua cài đặt Node.js packages.")
        print("[Node.js] Vui lòng cài đặt Node.js thủ công nếu cần dùng các tính năng docx-js.")
        return False

    print("[Node.js] Đang cài đặt thư viện 'docx' cục bộ...")
    try:
        # Chạy npm install cục bộ tại thư mục gốc dự án
        cmd = ["npm.cmd" if os.name == "nt" else "npm", "install", "docx", "--no-audit", "--no-fund"]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("[Node.js] Cài đặt thành công thư viện 'docx'!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[Node.js] Lỗi cài đặt npm: {e}")
        print(f"[Node.js] Chi tiết lỗi:\n{e.stderr}")
        return False


def install_playwright_browsers() -> bool:
    """Tải trình duyệt Chromium cho Playwright với cơ chế bọc lỗi an toàn."""
    print("[Playwright] Đang chuẩn bị tải trình duyệt Chromium...")

    # Xác định executable của playwright
    playwright_exe = os.path.join(".venv", "Scripts", "playwright.exe")
    use_uv = check_command_exists("uv")

    if use_uv:
        cmd = ["uv", "run", "playwright", "install", "chromium"]
    elif os.path.exists(playwright_exe):
        cmd = [playwright_exe, "install", "chromium"]
    else:
        cmd = ["playwright", "install", "chromium"]

    try:
        print(f"[Playwright] Chạy lệnh: {' '.join(cmd)}")
        # Thiết lập timeout 120s tránh treo vô hạn nếu mạng chậm
        subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)
        print("[Playwright] Tải trình duyệt Chromium thành công!")
        return True
    except subprocess.TimeoutExpired:
        print("[Playwright] Cảnh báo: Quá thời gian (Timeout 120s) khi tải Chromium do kết nối chậm.")
        return False
    except subprocess.CalledProcessError as e:
        print("[Playwright] Cảnh báo: Lỗi mạng hoặc lỗi hệ thống khi tải Chromium.")
        print(f"[Playwright] Chi tiết lỗi: {e}")
        if e.stderr:
            print(f"[Playwright] Stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"[Playwright] Cảnh báo: Không thể khởi chạy lệnh tải trình duyệt: {e}")
        return False


def main() -> None:
    """Hàm chạy chính của script."""
    print("=== CCBA PORTED SKILLS DEPENDENCY INSTALLER ===")

    python_success = install_python_packages([
        "python-docx", "Pillow", "pypdf", "google-genai",
        "python-pptx", "playwright"
    ])
    node_success = install_nodejs_packages()

    playwright_success = False
    if python_success:
        playwright_success = install_playwright_browsers()

    print("\n=== KẾT QUẢ CÀI ĐẶT ===")
    print(f"- Python Packages: {'Thành công' if python_success else 'Thất bại hoặc Cảnh báo'}")
    print(f"- Node.js Packages: {'Thành công' if node_success else 'Bỏ qua hoặc Thất bại'}")
    print(f"- Playwright Browser: {'Thành công' if playwright_success else 'Bỏ qua hoặc Cảnh báo'}")

    if python_success:
        print("\nHệ thống đã sẵn sàng chạy các kỹ năng được port!")
    else:
        print("\nHệ thống có thể gặp lỗi khi chạy một số kỹ năng do thiếu thư viện Python.")


if __name__ == "__main__":
    main()
