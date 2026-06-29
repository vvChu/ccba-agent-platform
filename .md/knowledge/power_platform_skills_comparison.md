# Feature Comparison: Microsoft Power Platform AI Skills
## Source: microsoft/power-platform-skills (https://github.com/microsoft/power-platform-skills)
## Local Project: ccba-agent-platform (IDOP Integration)

Dưới đây là báo cáo phân tích, đối soát và đánh giá tính tương thích của kho lưu trữ mẫu **`microsoft/power-platform-skills`** đối với hệ sinh thái **SharePoint IDOP** của chúng ta dưới quy trình đối soát so sánh `assess_upstream_features.py`.

---

## 📊 Head-to-Head Comparison & Gap Analysis

| Aspect | Microsoft Power Platform Skills | ccba-agent-platform (IDOP Scaffolder) | Gaps & Adaptation Strategy |
| --- | --- | --- | --- |
| **1. Target Runtime** | Cấu hình cho GitHub Copilot CLI và Claude Code (giao diện `/plugin`). | Cấu hình cho Antigravity IDE (giao diện Custom Slash Commands `/ccba-*`). | **Khác biệt nền tảng**: Cần chuyển đổi tệp đặc tả XML/JSON của họ thành định nghĩa [SKILL.md](file:///D:/GitHubProjects/ccba-agent-platform/.agent/skills/_core/idop-scaffolder/SKILL.md) chuẩn của Antigravity. |
| **2. Data Layer** | Tập trung mạnh vào **Microsoft Dataverse** (Schemas, Plugins, Queries). | Tập trung vào **SharePoint Online** (SharePoint Lists & Libraries) làm Data Layer. | **Khác biệt nghiệp vụ**: IDOP của CCBA dùng SharePoint Lists (CRM, Contracts...) vì tính tối ưu chi phí. Chúng ta không cần port phần Dataverse mà tập trung vào phần cấu trúc CDE. |
| **3. CLI Wrapper** | Sử dụng **Power Platform CLI (PAC CLI)** cho việc xác thực, quản lý môi trường, và push Code Apps. | Tương tác thông qua script [idop_scaffolder.py](file:///D:/GitHubProjects/ccba-agent-platform/scripts/idop_scaffolder.py) sinh cấu trúc và PnP PowerShell. | **Tích hợp tiềm năng**: Có thể học tập cách họ gọi lệnh `pac auth` và `pac package` để tích hợp việc đóng gói ứng dụng trực tiếp từ CLI. |
| **4. Code Apps Support** | Hỗ trợ scaffold và build React/TypeScript Code Apps. | Khởi tạo cấu trúc React/Vite/TS Code Apps với giao diện CCBA Dashboard cao cấp. | **Đã song hành**: Chúng ta đã tích hợp thành công bộ sinh tương đương tại chỗ dựa trên template chuẩn của Microsoft. |

---

## 🧠 Challenge Framework (5 Câu hỏi phản biện cốt lõi)

### Q1: Có nên cài đặt trực tiếp bộ kỹ năng của Microsoft vào máy không?
*   **Phản biện**: Không. Bộ kỹ năng của Microsoft thiết kế cho GitHub Copilot và Claude Code với các tệp tin cấu hình đóng kín. Cài đặt trực tiếp sẽ không tương thích với Antigravity và không kế thừa được tri thức nội bộ của CCBA (như chuẩn ISO 19650 hay các từ cấm thương hiệu).
*   **Giải pháp**: Chỉ tham chiếu thiết kế và viết lại các chỉ dẫn tương đương dưới dạng Custom Skills trong thư mục `.agent/skills/`.

### Q2: Dataverse vs SharePoint Lists - Đâu là lựa chọn tối ưu cho IDOP?
*   **Phản biện**: Dataverse mạnh về bảo mật cấp hàng và quan hệ dữ liệu phức tạp nhưng chi phí bản quyền (Premium Licensing) cực kỳ đắt đỏ đối với quy mô doanh nghiệp Full Enterprise của CCBA. SharePoint Lists được tích hợp sẵn trong Microsoft 365, hoàn toàn miễn phí phụ trội.
*   **Giải pháp**: Giữ nguyên thiết kế sử dụng SharePoint Lists + PnP PowerShell, không port các tính năng liên quan đến Dataverse.

### Q3: Bộ kỹ năng của Microsoft gọi lệnh xác thực `pac auth` như thế nào để an toàn?
*   **Phản biện**: Không bao giờ được lưu trữ thông tin đăng nhập (Credentials) trong code của Skill.
*   **Giải pháp**: Tương tự như quy tắc **Global Rule 3**, mọi lệnh gọi PAC CLI của Agent phải yêu cầu lập trình viên xác thực trước trên máy chủ hoặc sử dụng các biến môi trường hệ thống.

### Q4: Quy trình CI/CD cho Power Platform của họ có gì đáng học hỏi?
*   **Phản biện**: Microsoft duy trì một repo riêng là `powerplatform-actions` cho GitHub Actions. Việc tích hợp CI/CD trực tiếp vào Agent Platform sẽ làm phình to kiến trúc.
*   **Giải pháp**: Chỉ tích hợp các lệnh đóng gói cục bộ (`pac solution pack`), còn việc push lên production sẽ do các workflow CI/CD của hệ thống Gitlab/Github đảm nhận.

### Q5: Có thể tích hợp Copilot Studio (Power Virtual Agents) vào Platform của CCBA không?
*   **Phản biện**: Copilot Studio là một nền tảng low-code chatbot đắt đỏ và độc lập. Agent Platform của chúng ta (LiteLLM/Spark GPU Server) đã có sẵn 22 mô hình AI mạnh mẽ, miễn phí hoàn toàn.
*   **Giải pháp**: Không tích hợp Copilot Studio. Sử dụng trực tiếp SDK `ccba-ai` để điều phối AI.

---

## 🎯 Đề xuất Hành động (Handoff Plan)
1.  **Duy trì chuẩn hóa SharePoint**: Giữ nguyên luồng sinh SharePoint Lists PnP và CDE.
2.  **Mở rộng PAC CLI**: Trong tương lai, bổ sung thêm các lệnh đóng gói tự động (`pac solution pack`) vào `idop_scaffolder.py` bằng cách tham chiếu cách viết wrapper của Microsoft.
