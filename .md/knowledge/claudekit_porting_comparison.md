# Feature Comparison: ClaudeKit-Engineer Porting & Adaptation
## Source: claudekit-engineer (.md/claudekit_architectural_study.md)
## Local Project: ccba-agent-platform

Dưới đây là báo cáo so sánh, đánh giá tính tương thích và đề xuất port chọn lọc các tính năng từ `claudekit-engineer` sang `ccba-agent-platform` theo quy trình đánh giá gác cổng của công cụ kiểm tra cập nhật `check_claudekit_updates.py`.

---

## 📊 Head-to-Head Comparison & Gap Analysis

| Aspect | ClaudeKit-Engineer | ccba-agent-platform (Local) | Gaps & Adaptation Strategy |
| --- | --- | --- | --- |
| **1. Hook System** | Hệ thống hook Node.js (`SessionStart`, `PreToolUse`, v.v.) cấu hình qua `settings.json`. Enforce naming convention bằng JS. | Chốt chặn Python (`scripts/hooks/brand_enforcement.py`) kết hợp với hook runner đơn giản. | **Đã hoàn thành**: Phù hợp 100% với kiến trúc gọn nhẹ (KISS). Không cần chuyển dịch Node.js hooks phức tạp. |
| **2. State Persistence** | Lưu trạng thái qua `plan.md` (bảng Kanban) và tệp `latest.md` xoay vòng. Dùng CLI `ck plan` để ghi nhận trạng thái. | Lưu trạng thái qua `task.md` (Markdown checklists) và `implementation_plan.md` / `walkthrough.md`. | **Đã hoàn thành**: Checklists đơn giản có tính ổn định cao hơn trên Windows, tránh được lỗi phân tích cú pháp bảng. |
| **3. Document Recalc** | Tích hợp macro gỡ lỗi Excel (`xlsx/recalc.py`) dùng LibreOffice. | Tích hợp [xlsx_recalc.py](file:///D:/GitHubProjects/ccba-agent-platform/packages/ccba-pdf-prep/src/ccba_pdf_prep/document_skills/xlsx_recalc.py) với cơ chế fallback tự động sang `openpyxl`. | **Đã hoàn thành**: Đã gia cố khối ngoại lệ an toàn phòng ngừa lỗi phân quyền trên Windows. |
| **4. MCP Server** | Expose toàn bộ các tool của 87+ skills cho Claude qua giao thức MCP. | Bộ MCP Server cục bộ [mcp_server.py](file:///D:/GitHubProjects/ccba-agent-platform/packages/ccba-ai/src/ccba_ai/mcp_server.py) dùng cho tra cứu VBPL và AI Gateway. | **Đang phát triển**: Đã expose thành công các công cụ tra cứu luật. Log kết nối được đẩy ra tệp riêng. |
| **5. Multi-Agent Coor.** | Các Agent chuyên biệt phối hợp thông qua `TaskList` API và `SendMessage`. | Bộ điều phối multi-agent qua `team_coordinator.py`. | **Đã hoàn thành**: Điều phối đồng bộ dựa trên luồng file-based task an toàn. |

---

## 🧠 Challenge Framework (5 Câu hỏi phản biện cốt lõi)

### Q1: Có nên port toàn bộ 87+ kỹ năng của ClaudeKit sang không?
*   **Phản biện**: Không. Hầu hết các kỹ năng của ClaudeKit Engineer liên quan đến các framework phát triển web cụ thể (Next.js, Turborepo, Shopify, Shopify CLI...) hoặc các công cụ không thuộc mục tiêu cốt lõi của CCBA (như phát triển AI Video qua Remotion).
*   **Giải pháp**: Áp dụng nguyên tắc **Reuse-First** và **KISS**. Chỉ port chọn lọc các công cụ liên quan đến xử lý tài liệu, tự động gỡ lỗi và tra cứu tri thức.

### Q2: Cơ chế tự động gỡ lỗi (`mock-debugger`) có cần thiết kế phức tạp như của ClaudeKit?
*   **Phản biện**: Không cần. Thay vì tạo ra các sub-agent riêng biệt để phân tích mã lỗi, việc viết một script Python gọn nhẹ kết nối trực tiếp với AI Gateway là tối ưu nhất cho hiệu năng và độ ổn định trên Windows.
*   **Giải pháp**: Chúng ta đã triển khai thành công [mock_debugger.py](file:///D:/GitHubProjects/ccba-agent-platform/scripts/mock_debugger.py) theo hướng tối giản này.

### Q3: Có nên sử dụng cơ sở dữ liệu Vector DB cho MCP Server tra cứu luật không?
*   **Phản biện**: Trong giai đoạn đầu, lượng văn bản luật xây dựng Việt Nam còn ít, việc duy trì một Vector Database (như Chroma/Qdrant) chạy ngầm sẽ tiêu tốn tài nguyên và tăng độ phức tạp cài đặt.
*   **Giải pháp**: Tạm thời sử dụng cơ chế tra cứu mock kết hợp tìm kiếm từ khóa Regex chính xác. Khi quy mô văn bản tăng lên, ta sẽ tích hợp tìm kiếm BM25 + RAG SQLite cục bộ.

### Q4: Multi-agent coordination trên Windows có gặp rủi ro xung đột khóa tệp tin (File Locking)?
*   **Phản biện**: Có. Windows có cơ chế khóa tệp rất nghiêm ngặt đối với các tiến trình chạy song song ghi đè chung một file Markdown.
*   **Giải pháp**: Chúng ta thiết kế luồng điều phối đồng bộ tuần tự (Sequential/Task-based) thay vì chạy bất đồng bộ hoàn toàn để loại bỏ xung đột ghi file.

### Q5: Việc tách biệt cấu hình từ cấm / thương hiệu ra file riêng có làm chậm tốc độ xử lý của hooks không?
*   **Phản biện**: Việc đọc file YAML liên tục mỗi khi chạy hook có thể gây độ trễ nhỏ (khoảng vài mili-giây).
*   **Giải pháp**: Sử dụng cơ chế cache biến cấu hình hoặc fallback sang cấu hình tĩnh mặc định nếu tệp cấu hình không thay đổi hoặc gặp lỗi phân quyền.

---

## 🎯 Recommendation & Handoff Plan
1.  **Duy trì kiến trúc hiện tại**: Các tính năng cốt lõi (Hooks, Debugger, State, Multi-agent) đã được port và cấu hình idiomatically (hợp lý hóa) cho Windows & Python stack của CCBA.
2.  **Kế hoạch tiếp theo**: Nâng cấp bộ MCP Server cục bộ để tự động nạp cơ sở dữ liệu văn bản luật dạng tệp phẳng thay vì hardcode.
