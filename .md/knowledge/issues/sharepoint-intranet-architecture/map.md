# 🗺️ Wayfinding Map: Kiến Trúc & Phát Triển Intranet SharePoint Online (Microsoft 365)

> **Mã định danh:** `issue/sharepoint-intranet-architecture`  
> **Trạng thái:** `Active / Charting`  
> **Cập nhật gần nhất:** 2026-08-15 11:40:00 (+07:00)  
> **Kế thừa ngữ cảnh:** [`.md/scratch/handoffs/handoff-20260815-113800.md`](file:///d:/GitHubProjects/ccba-agent-platform/.md/scratch/handoffs/handoff-20260815-113800.md)

---

## 1. Điểm Đích (Destination)

Xác lập hoàn chỉnh toàn bộ đặc tả kiến trúc, công nghệ mở rộng (SPFx/Azure Serverless), cấu trúc thông tin (Information Architecture), mô hình bảo mật phân quyền (Entra ID & Purview) và lộ trình triển khai chi tiết cho hệ thống **Intranet Doanh nghiệp Hiện đại trên nền tảng SharePoint Online & Microsoft 365**, tích hợp liền mạch với hệ sinh thái CCBA Agent Platform và sẵn sàng bàn giao sang giai đoạn lập trình thực thi (`/ccba-implement`).

---

## 2. Ghi Chú & Kỹ Năng Bổ Trợ (Notes & Skills)

* **Kỹ năng phối hợp:**
  * [`wayfinder`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/wayfinder/SKILL.md) $\rightarrow$ Điều phối bản đồ và mở rộng Frontier.
  * [`grilling`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/grilling/SKILL.md) & [`domain-modeling`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/domain-modeling/SKILL.md) $\rightarrow$ Stress-test chốt quyết định và cập nhật `CONTEXT.md` / ADRs.
  * [`ccba-prototype`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-prototype/SKILL.md) $\rightarrow$ Dựng mẫu thử trực quan cho Viva Dashboard ACEs.
  * [`to-spec`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/to-spec/SKILL.md) $\rightarrow$ Biên soạn `spec-sharepoint-intranet.md` khi bản đồ hội tụ.
* **Nguyên tắc:** Tập trung chốt các **Quyết định (Decisions)** kỹ thuật, giải tỏa vùng mờ (Fog), không tự ý code thực thi khi chưa hoàn tất vạch đường.

---

## 3. Quyết Định Đã Chốt (Decisions So Far)

* [x] **[Quy chuẩn Flat Topology & Hub Sites]**: Loại bỏ 100% Subsites; sử dụng mô hình 1 Site Collection độc lập liên kết qua Hub Sites (Home Site + Khối Hub Điều hành + Khối Hub Dự án BIM).
* [x] **[Nền tảng Phát triển SPFx 1.20+ Client-side]**: Sử dụng React 18, Fluent UI v9 tokens và PnPjs v4 làm chuẩn lập trình mở rộng Web Parts và Viva Connections ACEs.
* [x] **[Loại trừ Intranet-in-a-box Thương Mại]**: Quyết định không mua giải pháp đóng gói sẵn (Valo, Powell) để tránh Vendor Lock-in và tối ưu chi phí TCO.

---

## 4. Biên Giới Câu Hỏi & Danh Sách Tickets Mở (Frontier Tickets)

Mỗi ticket đại diện cho một câu hỏi kiến trúc cụ thể cần giải quyết:

| Mã Ticket | Tên Ticket & Hành Động | Loại | Assignee | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **`T01`** | **[`[Đặc tả SPFx Components & Azure Functions Seam]`](#ticket-t01)** | `Research [AFK]` | *Unassigned* | **UNBLOCKED (Sẵn sàng)** |
| **`T02`** | **[`[Stress-Test Cấu Trúc Thông Tin IA & Term Store]`](#ticket-t02)** | `Grilling [HITL]` | *Unassigned* | **UNBLOCKED (Sẵn sàng)** |
| **`T03`** | **[`[Stress-Test Mô Hình Phân Quyền & Purview Security]`](#ticket-t03)** | `Grilling [HITL]` | *Unassigned* | **UNBLOCKED (Sẵn sàng)** |
| **`T04`** | **[`[Dựng Mẫu Thử Giao Diện Viva Connections ACEs]`](#ticket-t04)** | `Prototype [HITL]` | *Unassigned* | **UNBLOCKED (Sẵn sàng)** |

---

### Chi Tiết Các Ticket Tại Biên Giới

#### Ticket T01: `[Research] Đặc tả Kiến trúc SPFx Components & Serverless Azure Functions Seam` [AFK] {#ticket-t01}
* **Mục tiêu:** Xác định danh mục các Web Parts tùy biến, Application Customizers và Viva Dashboard ACE cards cốt lõi; thiết kế contract giao tiếp an toàn qua Azure Functions với Managed Identity.
* **Đầu ra:** Bản đặc tả kỹ thuật module `spfx-components-spec.md`.

#### Ticket T02: `[Grilling] Stress-Test Cấu Trúc Thông Tin (IA), Term Store Taxonomy & Content Types` [HITL] {#ticket-t02}
* **Mục tiêu:** Phỏng vấn Socrates chốt danh mục Hub Sites phân cấp (Corporate Hub vs Project Hub), bộ từ điển Managed Metadata (Phòng ban, Loại văn bản, Dự án, Giai đoạn thiết kế) và các Content Types chuẩn.
* **Đầu ra:** Bảng sơ đồ IA hoàn chỉnh và Decision Log.

#### Ticket T03: `[Grilling] Stress-Test Mô Hình Phân Quyền & Microsoft Purview Security` [HITL] {#ticket-t03}
* **Mục tiêu:** Chốt ranh giới phân quyền 3 lớp (Entra ID Dynamic Groups, Site Roles, Sensitivity Labels DLP) và quy trình cấp phát Site tự động (**PnP Provisioning Engine**).
* **Đầu ra:** Ma trận phân quyền và hồ sơ ADR về bảo mật Intranet.

#### Ticket T04: `[Prototype] Dựng Mẫu Thử Giao Diện Viva Connections Dashboard ACEs Card` [HITL] {#ticket-t04}
* **Mục tiêu:** Dựng một file HTML standalone prototype mô phỏng thẻ Viva Connections ACE Card (Card View tóm tắt tác vụ + Quick View form thao tác nhanh) có floating picker để người dùng duyệt UX/UI.
* **Đầu ra:** Prototype HTML và `NOTES.md`.

---

## 5. Sương Mù Chiến Trận / Chưa Xác Định Rõ (Not Yet Specified)

Các câu hỏi chưa đủ sắc nét để tạo ticket (đang bị chặn bởi các quyết định ở Frontier):

1. *Chiến lược lưu trữ bản vẽ kỹ thuật lớn: SharePoint Online Native Document Libraries vs SharePoint Embedded Container API.* (Phụ thuộc vào kết quả Ticket T01).
2. *Cấu hình chỉ mục ngữ nghĩa Semantic Index & SharePoint Custom Copilot Agents cho từng bộ môn (PCCC, MEP, Kết cấu).* (Phụ thuộc vào cấu trúc thông tin tại Ticket T02).
3. *Quy trình CI/CD tự động đóng gói SPFx bundle và deploy lên App Catalog qua GitHub Actions / Azure DevOps.* (Phụ thuộc vào Ticket T01).

---

## 6. Ngoài Phạm Vi (Out of Scope)

* **Giải pháp Intranet-in-a-box thương mại:** Không tích hợp hay mua bản quyền bên thứ ba.
* **Di chuyển dữ liệu cũ (Legacy Migration):** Không bao gồm việc migrate từ SharePoint On-Premises 2013/2016 cổ điển; hệ thống bắt đầu trực tiếp trên nền Modern SharePoint Online.
