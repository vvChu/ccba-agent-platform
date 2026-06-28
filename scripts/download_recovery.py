import re
import shutil
import sys
import time
from pathlib import Path

sys.path.append("d:/GitHubProjects/ccba-agent-platform/scripts")
from legal_intelligence import ChromeCDP


def handle_login(cdp: ChromeCDP) -> bool:
    """Detect login popup, fill in credentials, submit, handle multi-session warning, and return True if login was attempted."""
    js = """
    (() => {
        let tb = document.querySelector('#TB_window');
        if (!tb || tb.style.display === 'none') return "No popup";

        let inputs = Array.from(tb.querySelectorAll('input'));
        let text_inputs = inputs.filter(i => i.type === 'text');
        let pass_inputs = inputs.filter(i => i.type === 'password');
        let buttons = Array.from(tb.querySelectorAll('input[type="submit"], input[type="button"], button'));

        let user = text_inputs[0];
        let pass = pass_inputs[0];
        let login_btn = buttons.find(b => (b.value && b.value.includes('Đăng nhập')) || (b.innerText && b.innerText.includes('Đăng nhập')));

        if (user && pass && login_btn) {
            user.value = "vuvanchu119";
            pass.value = "ccba@ibst";
            login_btn.click();
            return "Attempted login click";
        }
        return "Inputs not found";
    })()
    """
    res = cdp.evaluate_js(js)
    if "Attempted login" in str(res):
        print("  [Login] Found login popup, autofilling credentials and submitting...")
        time.sleep(3)  # Wait for login action to trigger warning or reload

        # Check for multi-session login warning popup
        warning_js = """
        (() => {
            let agree_btn = Array.from(document.querySelectorAll('input, button, a')).find(el => {
                let txt = el.value || el.innerText || "";
                return txt.trim().toLowerCase() === 'đồng ý';
            });
            if (agree_btn) {
                agree_btn.click();
                return "Clicked Dong y";
            }
            return "No warning popup";
        })()
        """
        warn_res = cdp.evaluate_js(warning_js)
        print(f"  [Login Warning Check] Result: {warn_res}")
        if "Clicked Dong y" in str(warn_res):
            time.sleep(4)  # Wait for page reload after warning confirmation
        else:
            time.sleep(2)  # Wait for standard reload

        return True
    return False


def close_popup(cdp: ChromeCDP) -> bool:
    """Close any open ThickBox popup on the page."""
    js = """
    (() => {
        let closed = false;
        if (typeof tb_remove === 'function') {
            tb_remove();
            closed = true;
        } else {
            let tbClose = document.querySelector('#TB_closeWindowButton') || document.querySelector('[id*="TB_close"]');
            if (tbClose) {
                tbClose.click();
                closed = true;
            }
        }
        // Also check if TB_window is still visible
        let tb = document.querySelector('#TB_window');
        if (tb && tb.style.display !== 'none') {
            tb.style.display = 'none';
            let overlay = document.querySelector('#TB_overlay');
            if (overlay) overlay.style.display = 'none';
            closed = true;
        }
        return closed;
    })()
    """
    return bool(cdp.evaluate_js(js))


def trigger_download(cdp: ChromeCDP, download_dir: Path, slug_name: str) -> bool:
    downloads_path = Path.home() / "Downloads"
    if not downloads_path.exists():
        downloads_path = Path("C:/Users/chuvu/Downloads")

    existing_downloads = {f.name for f in downloads_path.glob("*")}

    # Try clicking the download button
    click_js = """
    (() => {
        let a = Array.from(document.querySelectorAll('a')).find(lnk => lnk.innerText && lnk.innerText.includes('Văn bản tiếng Việt (docx)'));
        if (!a) a = Array.from(document.querySelectorAll('a')).find(lnk => lnk.innerText && lnk.innerText.includes('Văn bản tiếng Việt'));
        if (!a) a = Array.from(document.querySelectorAll('a')).find(lnk => lnk.innerText && lnk.innerText.includes('Tải bản PDF'));
        if (a) {
            a.click();
            return "Clicked: " + a.innerText;
        }
        return "No download link found";
    })()
    """
    res = cdp.evaluate_js(click_js)
    print(f"  [Action] Click download: {res}")
    if "No download" in str(res):
        return False

    # Wait and check if popup appears, if so try auto-login or close it once
    time.sleep(2)
    if handle_login(cdp):
        print("  [Action] Login submitted after click, waiting for reload...")
        cdp.wait_ready()
        cdp.handle_cloudflare()
        print("  [Action] Retrying click...")
        res_retry = cdp.evaluate_js(click_js)
        print(f"  [Action] Retry click result: {res_retry}")
    elif close_popup(cdp):
        print("  [Action] Closed popup detected after click, retrying click...")
        cdp.evaluate_js(click_js)

    start_time = time.time()
    while time.time() - start_time < 20:
        current_downloads = list(downloads_path.glob("*"))
        new_downloads = [f for f in current_downloads if f.name not in existing_downloads]
        if new_downloads:
            if any(f.suffix == ".crdownload" or f.name.endswith(".tmp") for f in new_downloads):
                time.sleep(1)
                continue

            completed_files = [f for f in new_downloads if f.suffix in [".docx", ".pdf", ".doc"]]
            if completed_files:
                target_file = completed_files[0]
                dest_file = download_dir / f"{slug_name}{target_file.suffix}"
                print(f"  [Success] Moving: {target_file.name} -> {dest_file.name}")
                shutil.move(str(target_file), str(dest_file))
                return True
        time.sleep(1)

    return False

def get_metadata(filepath: Path) -> tuple[str, str]:
    """Extract resource_uri and title from frontmatter of .md file."""
    content = filepath.read_text(encoding="utf-8")
    uri = ""
    title = filepath.stem
    # Find resource: <url>
    match_uri = re.search(r"resource:\s*(https?://[^\s\n\r]+)", content)
    if match_uri:
        uri = match_uri.group(1).strip()
    return uri, title

def main():
    bundle_dir = Path(".md/legal_docs/luat_xay_dung_2025_so_135_2025_qh15_toan_van_moi_nhat_moi_nhat")
    if not bundle_dir.exists():
        print("Bundle directory not found.")
        return

    # Find all md files
    md_files = [bundle_dir / f"{bundle_dir.name}.md"]
    md_files.extend(list((bundle_dir / "guiding_docs").glob("*.md")))

    cdp = ChromeCDP()
    pages = cdp.get_pages()
    if not pages:
        print("No open Chrome tabs found.")
        return
    ws_url = pages[0]["webSocketDebuggerUrl"]
    cdp.connect_tab(ws_url)

    print("\n=== STARTING DOWNLOAD RECOVERY ===")
    for md_file in md_files:
        if not md_file.exists():
            continue

        uri, slug = get_metadata(md_file)
        if not uri:
            continue

        # Check if docx or pdf exists
        dest_dir = md_file.parent
        has_file = any((dest_dir / f"{slug}{ext}").exists() for ext in [".docx", ".pdf", ".doc"])
        if has_file:
            print(f"[Exists] {slug} already has downloaded document file.")
            continue

        print(f"\n[Recovering] {slug} -> Navigating to {uri}")
        cdp.navigate(uri)
        cdp.wait_ready()
        cdp.handle_cloudflare()

        # Check if login popup is active initially
        if handle_login(cdp):
            print("  [Action] Login submitted on page load, waiting for reload...")
            cdp.wait_ready()
            cdp.handle_cloudflare()
        elif close_popup(cdp):
            print("  [Action] Closed initial popup.")

        # Try downloading
        success = trigger_download(cdp, dest_dir, slug)
        if not success:
            print(f"  [Failed] Could not download document for {slug}.")
            print("  [Manual Instruction] Please review the open Chrome window, verify registration/login popup and dismiss it, or download manually.")

    cdp.close()
    print("\n=== DOWNLOAD RECOVERY FINISHED ===")

if __name__ == "__main__":
    main()
