"""Centralized DOM Selectors and ASP.NET identifiers for TVPL (Thư Viện Pháp Luật)."""

from __future__ import annotations


class TVPLSelectors:
    """Single Source of Truth for TVPL web automation DOM selectors."""

    # Login form inputs
    USERNAME_SELECTORS: list[str] = [
        "#usernameTextBox",
        "#l_txtUser",
        "#txtUserName",
        "input[placeholder*='Tên đăng nhập']",
        "#TB_window input[type='text']",
    ]
    PASSWORD_SELECTORS: list[str] = [
        "#passwordTextBox",
        "#l_txtPass",
        "#txtPassword",
        "input[placeholder*='Mật khẩu']",
        "#TB_window input[type='password']",
    ]
    LOGIN_BUTTON_SELECTORS: list[str] = [
        "#loginButton",
        "#btLogin",
        "input[value='Đăng nhập']",
    ]

    # Session verification labels
    USER_LABELS: list[str] = [
        "#ctl00_Header1_lblMemberName",
        "#ctl00_Header_lblTenDangNhap",
        ".user-name",
        "a[href*='thong-tin-ca-nhan']",
        "a[href*='dangxuat']",
    ]

    # Multi-session popup confirmation keywords
    CONFIRM_KEYWORDS: list[str] = ["đồng ý", "tiếp tục", "dong y"]

    # Search form inputs
    SEARCH_INPUT_SELECTORS: list[str] = [
        "#txtKeyWord",
        "input[name='serch']",
    ]
    SEARCH_BUTTON_SELECTORS: list[str] = [
        "#btnKeyWordHome",
        "input[value='Tìm kiếm']",
    ]

    # Tab 7 download postback elements
    TAB7_LINK = "#aTabTaiVe"
    DOCX_POSTBACK_KEY = "vietnameseHyperLink_Docx"
    PDF_POSTBACK_KEY = "vietnameseHyperLink_Pdf"

    # Attachment filter exclusions (promo / tutorials / navigation)
    EXCLUDED_ATTACHMENT_PATTERNS: list[str] = [
        "/bieumau",
        "dmca.com",
        "step=step",
        "dangky",
        "thong-tin-ca-nhan",
        "facebook.com",
        "google.com",
        "gdvreg",
    ]

    @classmethod
    def get_user_js_query(cls) -> str:
        """Construct JS expression checking for active VIP user label."""
        import json

        selectors_js = " || ".join(
            f"document.querySelector({json.dumps(s)})" for s in cls.USER_LABELS
        )
        return f"({selectors_js})"

    @classmethod
    def get_login_inputs_js(cls) -> str:
        """Construct JS expression selecting username, password, and login button."""
        import json

        u_js = " || ".join(
            f"document.querySelector({json.dumps(s)})" for s in cls.USERNAME_SELECTORS
        )
        p_js = " || ".join(
            f"document.querySelector({json.dumps(s)})" for s in cls.PASSWORD_SELECTORS
        )
        b_js = " || ".join(
            f"document.querySelector({json.dumps(s)})" for s in cls.LOGIN_BUTTON_SELECTORS
        )
        btn_query = json.dumps("input[type='button'], input[type='submit'], button")
        return (
            f"let user = {u_js};\n"
            f"let pass = {p_js};\n"
            f"let login_btn = {b_js} || Array.from(document.querySelectorAll({btn_query})).find(b => (b.value && b.value.includes('Đăng nhập')) || (b.innerText && b.innerText.includes('Đăng nhập')));"
        )

    @classmethod
    def get_multi_session_confirm_js(cls) -> str:
        """Construct JS expression to resolve TVPL multi-session warning popup by clicking visible confirm button."""
        import json

        confirm_kw_js = json.dumps(cls.CONFIRM_KEYWORDS)
        return f"""
        (() => {{
            let keywords = {confirm_kw_js};
            let isVisible = (el) => {{
                if (!el) return false;
                let cur = el;
                while (cur && cur.nodeType === 1) {{
                    let st = window.getComputedStyle(cur);
                    if (st.display === 'none' || st.visibility === 'hidden') return false;
                    cur = cur.parentElement;
                }}
                return true;
            }};
            let activeDialogs = Array.from(document.querySelectorAll('.ui-dialog, #TB_window')).filter(isVisible);
            for (let d of activeDialogs) {{
                let btns = Array.from(d.querySelectorAll('button, input[type="button"], input[type="submit"], a'));
                let btn = btns.find(b => isVisible(b) && keywords.some(kw => (b.innerText || b.value || '').trim().toLowerCase().includes(kw)));
                if (btn) {{
                    btn.click();
                    return 'Clicked Dong y: ' + (btn.innerText || btn.value || '').trim();
                }}
            }}
            let allBtns = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"], a')).filter(isVisible);
            let agreeBtn = allBtns.find(b => keywords.some(kw => (b.innerText || b.value || '').trim().toLowerCase().includes(kw)));
            if (agreeBtn) {{
                agreeBtn.click();
                return 'Clicked Dong y: ' + (agreeBtn.innerText || agreeBtn.value || '').trim();
            }}
            if (typeof ContinueLogin === 'function') {{
                ContinueLogin();
                return 'Called ContinueLogin()';
            }}
            return 'No warning popup';
        }})()
        """
