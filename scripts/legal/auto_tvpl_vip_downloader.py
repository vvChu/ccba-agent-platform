"""Automated TVPL VIP login and document crawler/downloader via Chrome CDP."""

import subprocess
import sys
import time
from pathlib import Path

# Force UTF-8 encoding on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from ccba_legal.crawler import ChromeCDP, get_tvpl_credentials


def run_auto_crawler():
    username, password = get_tvpl_credentials()
    print("[AutoTVPL] Starting Chrome browser on debug port 9222...")
    chrome_cmd = [
        "cmd.exe",
        "/c",
        "start",
        "chrome",
        "--remote-debugging-port=9222",
        "--user-data-dir=C:\\temp\\chrome_dev",
        "https://thuvienphapluat.vn/dang-nhap.aspx",
    ]
    subprocess.Popen(chrome_cmd)
    time.sleep(4)

    cdp = ChromeCDP(port=9222)
    pages = cdp.get_pages()
    if not pages:
        print("[AutoTVPL] Failed to connect to Chrome on port 9222.")
        return False

    ws_url = pages[0]["webSocketDebuggerUrl"]
    cdp.connect_tab(ws_url)

    # 1. Login to TVPL
    print(f"[AutoTVPL] Performing VIP Login for user '{username}'...")
    login_js = f"""
    (() => {{
        let userInp = document.querySelector('#txtUser') || document.querySelector('input[name*="User"]') || document.querySelector('input[type="text"]');
        let passInp = document.querySelector('#txtPassword') || document.querySelector('input[name*="Pass"]') || document.querySelector('input[type="password"]');
        let btnSubmit = document.querySelector('#btLogin') || document.querySelector('button[type="submit"]') || document.querySelector('input[type="submit"]');

        if (userInp && passInp) {{
            userInp.value = "{username}";
            passInp.value = "{password}";
            if (btnSubmit) {{
                btnSubmit.click();
                return "Login submitted";
            }}
        }}
        return "Login fields not found or already logged in";
    }})()
    """

    login_res = cdp.evaluate_js(login_js)
    print(f"[AutoTVPL] Login action result: {login_res}")
    time.sleep(4)

    # Check for multi-session warning popup ("Đồng ý")
    agree_js = """
    (() => {
        let agree_btn = Array.from(document.querySelectorAll('input, button, a')).find(el => {
            let txt = (el.value || el.innerText || "").trim().toLowerCase();
            return txt === 'đồng ý' || txt === 'dong y';
        });
        if (agree_btn) {
            agree_btn.click();
            return "Clicked Dong y";
        }
        return "No multi-session warning";
    })()
    """
    agree_res = cdp.evaluate_js(agree_js)
    print(f"[AutoTVPL] Multi-session check result: {agree_res}")
    time.sleep(3)

    # 2. Navigate to QCVN 06:2022/BXD target page
    target_url = "https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/Thong-tu-06-2022-TT-BXD-Quy-chuan-ky-thuat-quoc-gia-an-toan-chay-cho-nha-va-cong-trinh-545229.aspx"
    print(f"[AutoTVPL] Navigating to target QCVN 06:2022 URL: {target_url}")
    cdp.send_command("Page.navigate", {"url": target_url})
    time.sleep(5)

    title = cdp.evaluate_js("document.title")
    curr_url = cdp.evaluate_js("window.location.href")
    print(f"[AutoTVPL] Document Page Title: {title}")
    print(f"[AutoTVPL] Current Page URL: {curr_url}")

    # Extract text content from main doc container
    extract_js = """
    (() => {
        let el = document.querySelector('#divContentDoc') || document.querySelector('.contentDoc') || document.body;
        return el ? el.innerText : "";
    })()
    """
    extracted_text = cdp.evaluate_js(extract_js)
    print(f"[AutoTVPL] Extracted content length: {len(extracted_text)} characters.")

    if (
        len(extracted_text) > 1000
        and "Thứ trưởng" in extracted_text
        or "Bộ Xây dựng" in extracted_text
        or "Quy chuẩn" in extracted_text
    ):
        out_dir = Path("d:/GitHubProjects/ccba-agent-platform/.md/legal_docs/qcvn_06_2022_bxd")
        out_dir.mkdir(parents=True, exist_ok=True)
        concept_file = out_dir / "concept.md"

        full_markdown = f"""# QCVN 06:2022/BXD — QUY CHUẨN KỸ THUẬT QUỐC GIA VỀ AN TOÀN CHÁY CHO NHÀ VÀ CÔNG TRÌNH

*(Toàn văn tải về từ Thư viện Pháp luật VIP vuvanchu119 - Ngày {time.strftime("%d/%m/%Y")})*

---

{extracted_text}
"""
        concept_file.write_text(full_markdown, encoding="utf-8")
        print(f"[AutoTVPL] Successfully wrote full-text concept to {concept_file.resolve()}")
        cdp.close()
        return True

    cdp.close()
    print("[AutoTVPL] Navigation completed.")
    return False


if __name__ == "__main__":
    run_auto_crawler()
