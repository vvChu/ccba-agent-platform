> [!WARNING]
> Tài liệu này mang tính chất lịch sử/nghiên cứu cũ.
> Cấu trúc thư mục và các sự kiện (lifecycle events) mô tả trong tài liệu có thể đã thay đổi hoặc khác biệt so với phiên bản Python của CAP hiện tại.

---
# Báo cáo Phân tích Tính năng ClaudeKit Marketing
## Đối tượng: `claudekit-marketing`
## Dự án đích: `ccba-agent-platform`

---

## 1. Khảo sát & Bản đồ thành phần (Recon & Map)

`claudekit-marketing` là một bộ tự động hóa marketing toàn diện bao gồm:
*   **32 Agents chuyên dụng**: Phục vụ các phễu Marketing TOFU, MOFU, BOFU và các vai trò hỗ trợ như Copywriter, UI/UX Designer.
*   **68 Skills**: Tích hợp đa phương tiện (AI Artist, Multimodal), Email (SendGrid, Resend), SEO, Analytics (GA4, GSC).
*   **Marketing Dashboard**: Một ứng dụng full-stack (Vue 3 + Hono + SQLite) quản lý Kanban chiến dịch, thư viện tài sản, và tối ưu hóa nội dung AI.

### Ma trận Tương thích kỹ thuật (Dependency & Stack Mapping)

| Thành phần nguồn | Hệ thống đích (ccba-agent-platform) | Trạng thái tích hợp | Rủi ro |
| :--- | :--- | :--- | :--- |
| **Hono & SQLite API** | `ccba-ai` (FastAPI / Python) | `CONFLICT` (Khác biệt ngôn ngữ JS vs Python) | Cần rewrite lại API sang Python FastAPI nếu muốn tích hợp trực tiếp. |
| **Vue 3 Dashboard** | Chưa có Frontend | `NEW` (Cần dựng UI mới) | Tải lượng bundle, cấu hình routing. |
| **MCP Integrations** | LiteLLM AI Gateway | `EXISTS` (Đã có AI Gateway ở cổng :8090) | Cần cấu hình thêm biến môi trường của các bên thứ ba (GA4, Ads). |
| **Marketing Skills (SEO, Email)** | Kỹ năng xử lý tài liệu / OCR | `NEW` (Có thể port làm các python tools) | Độ phức tạp khi tích hợp các thư viện bên thứ 3. |

---

## 2. Phân tích chi tiết (Analyze)

Bộ kỹ năng Marketing của ClaudeKit mang tính chuyên môn hóa cao về mặt content và phễu. Tuy nhiên, `ccba-agent-platform` hiện tại đang tập trung vào các tác vụ kỹ thuật, xử lý tài liệu (PDF, Excel) và nền tảng AI Gateway. 

Do đó, việc port trực tiếp toàn bộ 101+ skills và Dashboard Vue 3/Hono sẽ tạo ra lượng "code slop" rất lớn và vi phạm nguyên lý **KISS**. Phương án tối ưu là **chọn lọc các kỹ năng lõi** để tích hợp dưới dạng Python scripts hoặc MCP tools.

---

## 3. Khung phản biện & Thử thách (Challenge & Trade-offs)

### Các câu hỏi phản biện:
1.  **Mục tiêu sử dụng**: Dự án `ccba-agent-platform` thực sự có nhu cầu chạy chiến dịch Marketing tự động không, hay chỉ cần các kỹ năng phụ trợ như **Tối ưu SEO (SEO Audit)** và **Viết bài tự động (Copywriting)**?
2.  **Độ tương thích Stack**: API của Dashboard chạy bằng TypeScript (Hono). Chúng ta có nên duy trì một server TS song song hay viết lại các endpoints nghiệp vụ bằng Python để đồng nhất với `ccba-ai`?
3.  **Chi phí MCP**: Nhiều tính năng yêu cầu API Key của GA4, Google Ads, SendGrid. Việc hardcode hoặc cấu hình các API này có vi phạm bảo mật hệ thống?
4.  **Hiệu năng & Tài nguyên**: Việc import thêm 32 agents marketing có làm loãng danh mục agents hiện tại của nền tảng?
5.  **Duy trì codebase**: Mã nguồn Dashboard Vue 3 có thực sự cần thiết khi người dùng đang thao tác qua giao diện Antigravity IDE?

### Ma trận Quyết định Đề xuất:

| Quyết định thành phần | Giải pháp của ClaudeKit | Khuyến nghị cho CCBA Platform | Lý do (Trade-off) |
| :--- | :--- | :--- | :--- |
| **Dashboard UI** | Vue 3 + Hono + SQLite | **Bỏ qua (Hoặc dựng Handoff Report)** | Giảm thiểu dependency và tài nguyên chạy nền. |
| **MCP Integrations** | GA4, GSC, Slack, Discord | **Tích hợp chọn lọc** | Chỉ tích hợp Slack/Discord phục vụ log thông báo. |
| **SEO & Keywords Skill** | Kỹ năng SEO của Claude | **Port sang Python Tool** | Hữu ích cho các tác vụ viết tài liệu và tối ưu hóa từ khóa. |
| **Copywriting Agent** | Agent chuyên viết copy | **Tích hợp làm một System Prompt trong `ccba-ai`** | Tránh nhân bản Agent không cần thiết. |

---

## 4. Kế hoạch đề xuất (Proposed Handoff Plan)

Chúng tôi đề xuất thực hiện theo chế độ **`--compare`** và **Tích hợp chọn lọc** (không transplant nguyên khối):
1.  Dịch chuyển kỹ năng **SEO Audit và Keyword Research** thành 1 module Python trong `packages/ccba-pdf-prep` hoặc thư viện phụ trợ.
2.  Dịch chuyển kỹ năng **Brand Enforcement Hook** (kiểm tra nội dung có tuân thủ brand book) thành 1 hook script trong `scripts/hooks/`.
