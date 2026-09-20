---
name: ccba-chrome-debug
description: Quản trị vòng đời Chrome CDP (Port 9222), Chrome DevTools MCP, Persistent Profile và công cụ /browser cho Antigravity & CCBA Platform.
user-invocable: true
command: /ccba-chrome-debug
when_to_use: Sử dụng khi cần khởi chạy, kiểm tra sức khỏe, hoặc giải phóng Chrome Debugger; gỡ lỗi kết nối /browser, hoặc cấu hình domain trong allowlist.
category: dev-tools
gpi:
  s: 4.0
  k: 3.0
  a: 2.0
  p: 1.0
keywords:
- chrome-debug
- cdp
- browser
- /browser
- chrome-devtools
- allowlist
- remote-debugging
license: Apache-2.0
metadata:
  author: CCBA Hub
  version: 1.0.0
disable-model-invocation: true
bundle: _software
tier: kernel
triggers:
- ccba-chrome-debug
- chrome debug
- cdp port 9222
- browser tools
- mở chrome debug
- kiểm tra kết nối browser
---

# Kỹ Năng Quản Trị Trình Duyệt Chrome AI Debug (`ccba-chrome-debug`)

Kỹ năng này chuẩn hóa hạ tầng điều khiển và tương tác trình duyệt Google Chrome thông qua **Chrome DevTools Protocol (CDP)**, phục vụ công cụ `/browser`, subagent browser, Chrome DevTools MCP Server và các tác vụ tự động hóa web chuyên sâu (SharePoint CCBA, TVPL VIP Crawler, Google Workspace, UI Testing).

---

## 🏛️ Kiến Trúc & Các Bất Biến Cốt Lõi (Invariants)

1. **Cổng Chuẩn Duy Nhất (Strict Port 9222 SSOT):**
   - Cổng `9222` là Single Source of Truth cho toàn bộ kết nối CDP và MCP.
   - Cấm nhảy cổng động khi 9222 bận; thay vào đó, hệ thống hỗ trợ chẩn đoán PID đang chiếm cổng và tự phục hồi (Auto-Healing).
2. **Bắt Buộc Bắt Tay WebSocket (`--remote-allow-origins=*`):**
   - Trên Chrome hiện đại (Chrome 111+ đến 153+), cờ này bắt buộc phải có để các client local (Node.js, Python, WebSocket) không bị từ chối với mã lỗi `403 Forbidden`.
3. **Khóa Chặt Địa Chỉ Loopback (`127.0.0.1`):**
   - Trình duyệt debug bắt buộc chỉ lắng nghe trên `127.0.0.1`, tuyệt đối cấm cấu hình `--remote-debugging-address=0.0.0.0` để bảo vệ phiên làm việc trước các rủi ro mạng LAN/WAN.
4. **Hợp Nhất Persistent Profile (`~/.gemini/antigravity-browser-profile`):**
   - Sử dụng một profile lưu trữ lâu dài dùng chung duy nhất cho toàn bộ hệ thống. Toàn bộ cookie, phiên đăng nhập (SharePoint `ibstbim.sharepoint.com`, Google, TVPL VIP) được bảo toàn vĩnh viễn.
5. **Dừng An Toàn Có Chọn Lọc (Selective Safe Termination):**
   - Khi giải phóng cổng hoặc tắt phiên debug, script chỉ tắt các tiến trình Chrome thuộc AI Debug Mode, bảo vệ tuyệt đối các cửa sổ Chrome cá nhân thông thường của người dùng.

---

## 🛠️ Bộ Công Cụ & Hướng Dẫn Vận Hành 1-Click

Bộ script tiện ích được lưu trữ tập trung tại `C:\Users\chuvu\.gemini\antigravity\bin\`:

| Tiện ích | Định dạng | Mục đích sử dụng |
| :--- | :---: | :--- |
| **Desktop Shortcut** | `.lnk` | Lối tắt `Chrome (AI Debug Mode)` trên Desktop để mở nhanh trình duyệt với 1 nhấp đúp chuột. |
| **`Launch-Chrome-Debug`** | `.cmd` / `.ps1` | Khởi chạy Chrome CDP port 9222, tự dọn dẹp file `LOCK` cũ và xác thực kết nối HTTP `/json/version`. |
| **`Test-Chrome-Debug`** | `.ps1` | Kiểm tra sức khỏe toàn diện: TCP 9222, HTTP handshake, WebSocketDebuggerUrl, danh sách tabs, MCP config, Allowlist. |
| **`Stop-Chrome-Debug`** | `.cmd` / `.ps1` | Dừng an toàn phiên Chrome Debug, giải phóng cổng 9222 và xóa file `LOCK` tồn đọng mà không ảnh hưởng Chrome thường. |

### Cách Kích hoạt Nhanh

```powershell
# Khởi chạy phiên Chrome Debug:
pwsh -File "C:\Users\chuvu\.gemini\antigravity\bin\Launch-Chrome-Debug.ps1"

# Kiểm tra sức khỏe kết nối:
pwsh -File "C:\Users\chuvu\.gemini\antigravity\bin\Test-Chrome-Debug.ps1"

# Dừng an toàn phiên làm việc:
pwsh -File "C:\Users\chuvu\.gemini\antigravity\bin\Stop-Chrome-Debug.ps1"
```

---

## 🔌 Tích Hợp Chrome DevTools MCP

Hệ thống đã được tích hợp gói chính thức `chrome-devtools-mcp` (v1.9.0) của Google Chrome Team trong `mcp_config.json`:

```json
"chrome-devtools": {
  "command": "node",
  "args": [
    "C:\\Users\\chuvu\\AppData\\Roaming\\npm\\node_modules\\chrome-devtools-mcp\\build\\src\\bin\\chrome-devtools-mcp.js",
    "--browserUrl",
    "http://127.0.0.1:9222",
    "--no-usage-statistics"
  ]
}
```

Giúp mọi Agent trong phiên làm việc có thể:
- **Thanh tra & tương tác:** `navigate_page`, `click`, `fill_form`, `hover`.
- **Giám sát:** `list_console_messages`, `list_network_requests`.
- **Trực quan hóa:** `take_screenshot`, `take_snapshot`.

---

## 🛡️ Quản Trị Danh Sách Tên Miền Cho Phép (`browserAllowlist.txt`)

Hai tệp cấu hình allowlist được đồng bộ tại:
- `~/.gemini/antigravity/browserAllowlist.txt`
- `~/.gemini/antigravity-ide/browserAllowlist.txt`

Bao quát 64+ domain trọng yếu:
- **Microsoft 365 / CCBA:** `ibstbim.sharepoint.com`, `login.microsoftonline.com`, `office.com`.
- **Pháp lý & Đấu thầu:** `thuvienphapluat.vn`, `luatvietnam.vn`, `chinhphu.vn`, `xaydung.gov.vn`, `dauthau.mpi.gov.vn`.
- **Google & AI:** `google.com`, `drive.google.com`, `gemini.google.com`, `anthropic.com`, `openai.com`.

---

## 💡 Mẹo Tối Ưu Hóa Trải Nghiệm (Pro-Tips)

1. **Cài tiện ích Chặn Quảng cáo / Cookie Popups:**
   - Cài đặt **uBlock Origin** hoặc **I don't care about cookies** trên profile này để tránh các popup che khuất nút bấm khi Agent tự động click.
2. **Can thiệp Thủ công Linh hoạt (Human-in-the-Loop):**
   - Khi gặp mã OTP SMS hoặc CAPTCHA phức tạp, người dùng có thể nhập trực tiếp trên cửa sổ Chrome AI Debug; Agent sẽ ngay lập tức tiếp tục tác vụ mà không bị gián đoạn.
