# Feature Comparison: ClaudeKit Hook System vs CCBA Platform
## Source: claudekit-engineer (claudekit-engineer/claude/hooks/)
## Local Project: ccba-agent-platform (Unified Hook Lifecycle)

Báo cáo phân tích và so sánh hệ thống Hook Lifecycle của ClaudeKit đối với nền tảng CCBA Agent Platform theo quy trình `/ccba-kit xia`.

---

## 📊 Head-to-Head Comparison & Gap Analysis

| Aspect | ClaudeKit Hook System (Source) | ccba-agent-platform (Local) | Recommendation & Porting Strategy |
| --- | --- | --- | --- |
| **1. Hook Registry** | Cấu hình trong `settings.json` ánh xạ các sự kiện CLI sang kịch bản `.cjs`. | Chưa có hệ thống hook trung tâm; việc kiểm soát hành vi dựa vào System Prompt. | **Cần bổ sung**: Xây dựng hệ thống cấu hình `hooks.json` tương đương cho nền tảng. |
| **2. Interception Points** | Hỗ trợ 5 điểm chặn: `SessionStart`, `UserPromptSubmit`, `SubagentStart`, `PreToolUse`, `PostToolUse`. | Chỉ chặn được ở mức MCP Server (khi gọi tool) hoặc IDE level. | **Kiến trúc đề xuất**: Triển khai Python-based middleware chặn trước/sau khi thực thi các custom skills. |
| **3. Safety Guardrails** | `privacy-block.cjs` (quét API Keys) và `scout-block.cjs` (bảo vệ kiến trúc). | Chặn rò rỉ dữ liệu thông qua skill `accidental-data-loss-prevention`. | **Nâng cấp**: Port cơ chế quét Regex của `privacy-block` để ngăn ghi đè API Keys vào file `.py` hoặc `.md`. |
| **4. State Synchronization** | `session-state.cjs` và `plan-format-kanban.cjs` cập nhật trạng thái ra tệp Markdown. | Sử dụng `plan_manager.py` chạy thủ công hoặc cập nhật qua `/ccba-plan`. | **Tích hợp**: Tự động gọi `plan_manager.py` sau mỗi lần skill thực thi thành công. |

---

## 🧠 Challenge Framework (Phản biện thiết kế)

### Q1: Có nên cài đặt môi trường chạy Node.js cho các hook cjs trên máy Windows của CCBA không?
*   **Phản biện**: Không. Windows xử lý khóa tệp tin rất nghiêm ngặt. Việc gọi thêm luồng phụ chạy Node.js chỉ để kiểm tra trước khi ghi file sẽ làm giảm hiệu năng đáng kể (overhead từ 0.5s - 1.5s mỗi công cụ) và dễ lỗi lock file.
*   **Giải pháp**: Viết lại các logic Hook bằng Python trực tiếp trong nhân của `packages/ccba-ai` hoặc thông qua các class decorator.

### Q2: Cơ chế ngăn chặn rò rỉ API Keys (`privacy-block`) có thực sự cần thiết không?
*   **Phản biện**: Rất cần thiết. Đặc biệt là khi làm việc với nhiều LLM và Cloud API. Rất dễ xảy ra tình trạng AI vô tình ghi đè API Key lấy từ biến môi trường vào các file cấu hình dự án rồi commit lên Git.
*   **Giải pháp**: Triển khai một lớp kiểm định Regex chặn các chuỗi dạng `AIzaSy...` (Gemini), `sk-...` (OpenAI) trước khi thực thi công cụ viết file.

### Q3: Có nên đồng bộ hóa tự động Kanban/Plan (`plan-format-kanban`) sau mỗi công cụ?
*   **Phản biện**: Tự động hóa quá mức có thể làm hỏng file kế hoạch nếu LLM hiểu sai ngữ cảnh của tool.
*   **Giải pháp**: Giữ nguyên cơ chế tương tác thông qua `plan_manager.py` và chỉ tự động cập nhật khi phase kết thúc rõ ràng.

---

## 🎯 Đề xuất Tích hợp (Handoff Plan)

1.  **Dự án mục tiêu**: Tạo mới modul `ccba_ai/hooks/` bên trong package [ccba-ai](file:///D:/GitHubProjects/ccba-agent-platform/packages/ccba-ai).
2.  **Hook Đầu tiên (Privacy Guard)**: Triển khai bộ lọc pre-write chặn ghi đè API Keys.
3.  **Tích hợp Platform**: Khai báo tệp cấu hình `hooks.yaml` tại thư mục gốc Spoke để kích hoạt/tắt các bộ lọc này.
