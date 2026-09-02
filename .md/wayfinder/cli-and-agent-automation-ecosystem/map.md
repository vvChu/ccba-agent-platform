# Bản Đồ Định Hướng: Hệ Sinh Thái CLI & Tự Động Hoá Agentic Cho CCBA Platform
`wayfinder:map` | Trạng thái: **Active (Đang thực hiện)**

---

## 🎯 1. Điểm Đích (Destination)

Thiết lập và chuẩn hoá toàn diện **Mô hình Kiềng 3 Chân (Tri-Tier Agentic Ecosystem)** cho CCBA Platform, giúp kỹ sư và các pipeline tự động đạt năng suất cao nhất:
1. **Interactive Layer (Antigravity IDE GUI):** Dành cho lập trình viên phát triển tính năng, lập kế hoạch sâu (Planning Mode), và duyệt trực quan Visual Diff.
2. **Autonomous Execution Layer (Antigravity CLI `agy` & Copilot CLI):** Hỗ trợ dòng lệnh siêu tốc (<15ms), tự động hoá Git commits, pre-commit security guards, và cron maintenance daemons.
3. **Core Resilient Engine (`ccba-ai` Python SDK):** Kết nối 55 models trên Server Spark (:8090) cùng 4-Tier Failover (Cloud Direct $\rightarrow$ Local Ollama $\rightarrow$ Deterministic Mock) cho toàn bộ Spoke/Hub pipelines.

---

## 📝 2. Ghi Chú & Ràng Buộc (Notes)

- **Nguyên tắc Hoạch định (Plan, don't do):** Tập trung chốt các quyết định kiến trúc, tiêu chuẩn hóa kịch bản, và cấu hình tái sử dụng trước khi triển khai đại trà.
- **Tận dụng tối đa công cụ sẵn có (Zero Bloat):** Sử dụng trực tiếp `agy.exe` (Go binary) và `gh.exe` (GitHub CLI) đã có sẵn trên máy, không viết lại CLI wrapper thừa thãi.
- **Tuân thủ Hiến pháp Layer 1:** Mọi script và hook tự động hoá đều phải tôn trọng quy chuẩn `AGENTS.md`, `rules/`, và cơ chế bảo mật Maskara.

---

## ✅ 3. Quyết Định Đã Chốt (Decisions So Far)

* [x] **[ADR 0055: Multi-Tier Failover Matrix & Mock Provider](../../../docs/adr/0055-ccba-ai-multi-tier-failover-and-mock-provider.md)**: Triển khai 4 tầng chuyển vùng dự phòng và Mock Engine in-memory cho `ccba-ai`, đạt 94/94 unit tests passed.
* [x] **[Lựa chọn Antigravity CLI (`agy`) thay thế Gemini CLI](../../../docs/adr/0055-ccba-ai-multi-tier-failover-and-mock-provider.md)**: `agy` khởi động tức thì (<15ms), đồng bộ 100% với `AGENTS.md`, custom skills `.agents/skills/`, hỗ trợ cả Gemini 3.7 và Claude Sonnet 4.6 Thinking.
* [x] **[Lựa chọn Copilot CLI (`gh copilot`) làm Terminal Helper](../../../docs/adr/0055-ccba-ai-multi-tier-failover-and-mock-provider.md)**: Tận dụng tài khoản GitHub `vvChu` để tra cứu cú pháp PowerShell/Git nhanh chóng.

---

## 🧭 4. Các Ticket Tại Biên Giới (Frontier Tickets)

Các ticket mở, sắc nét, không bị chặn và sẵn sàng thực thi:

| Mã Ticket | Tên Ticket | Loại | Trạng thái |
| :--- | :--- | :--- | :--- |
| **T01** | [Đóng gói PowerShell Productivity Suite (`ccba_aliases.ps1`)](./tickets/01_shell_aliases_and_dev_helpers.md) | `Prototype [HITL]` | 🟢 **Completed** |
| **T02** | [Pre-commit AI Guardrail (Đã có Maskara Hook)](./tickets/02_pre_commit_ai_guardrail.md) | `Task [AFK]` | ⛔ **Cancelled** (Duplicate) |
| **T03** | [Autonomous Docs Maintenance (Đã có CI Gates)](./tickets/03_autonomous_maintenance_daemon.md) | `Task [AFK]` | ⛔ **Cancelled** (Duplicate) |
| **T04** | [MCP Chaining từ CLI (Tính năng mặc định Native)](./tickets/04_mcp_chaining_on_cli.md) | `Prototype [HITL]` | ⛔ **Cancelled** (Native) |

---

## 🌫️ 5. Sương Mù Chiến Trận (Not Yet Specified)

Các vùng chưa thể phát biểu thành câu hỏi sắc nét, chờ kết quả từ các Frontier Tickets:
- **Cơ chế đồng bộ phiên giữa Spoke và Hub**: Làm thế nào để kỹ sư chạy `agy -c` trên Spoke repo mà vẫn tận dụng được shared context từ Hub mà không nhân bản dữ liệu?
- **Quota & Token Caching cho Cron Daemon**: Chiến lược lưu cache kết quả phân tích AST để tránh tiêu tốn quá nhiều tokens khi daemon quét định kỳ mỗi sáng.

---

## 🚫 6. Ngoài Phạm Vi (Out of Scope)

- Không viết lại CLI compiler hoặc binary mới (sử dụng 100% `agy` và `gh`).
- Không bypass cơ chế bảo mật (tất cả các script chạy tự động `--dangerously-skip-permissions` phải có ranh giới giới hạn chỉ sửa đổi tài liệu/docs, không được tự ý xóa database hay can thiệp production).
