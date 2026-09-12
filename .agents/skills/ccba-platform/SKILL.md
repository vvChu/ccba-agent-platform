---
name: ccba-platform
description: Cổng điều phối toàn cục (Global Router) và kiểm tra môi trường cho CCBA Agent Services Platform. Tự động kiểm tra Hub/Spoke, Gateway/VPN, cấu trúc Spoke và điều hướng đúng kỹ năng.
bundle: _core
tier: orchestrator
is-orchestrated: true
user-invocable: true
disable-model-invocation: true
command: /ccba-platform
triggers:
  - platform
  - ccba
  - ccba-platform
  - hub
  - spoke
  - bootstrap
metadata:
  version: v4.1
  author: "CCBA Hub"
---

# CCBA Platform — Global Entry Point & Orchestrator

> Đây là Global Skill khả dụng từ **mọi dự án** trong hệ sinh thái CCBA Agent Services Platform.
> Khi người dùng yêu cầu một trong các tác vụ dưới đây, Agent nạp định nghĩa kỹ năng tương ứng rồi điều phối thực thi.
> Output và thành phẩm luôn lưu về thư mục dự án (Spoke) hiện tại để đảm bảo tính độc lập dữ liệu.

## Phân Giải Đường Dẫn Hub & Spoke Động
* Đường dẫn gốc Platform Hub được tự động phân giải qua biến môi trường **`CCBA_HUB_PATH`** hoặc cấu hình trong `.md/workspace_context.yaml`.
* Nếu chưa thiết lập, Agent tự động duyệt ngược từ thư mục làm việc hiện tại (CWD) lên các cấp cha để tìm thư mục có chứa `.agents` làm gốc Hub.

---

## 🛡️ Pha 1: Kiểm Định Môi Trường & Nhận Diện Ngữ Cảnh (Topology & Health Audit)

Trước khi hiển thị Ma Trận Điều Phối hoặc thực thi bất kỳ kỹ năng nào, Agent **bắt buộc** phải tự động chạy kiểm định môi trường dự án:

1. **Nhận diện Ngữ cảnh Hub vs. Spoke (Constitution Core Invariant):**
   * Kiểm tra nguồn gốc kho mã nguồn:
     ```bash
     git remote get-url origin
     ```
   * **Nếu URL chứa `ccba-agent-platform`** $\rightarrow$ **Hub Monorepo Context**: Bỏ qua kiểm tra cấu trúc Spoke, sẵn sàng cho các tác vụ phát triển nền tảng hoặc kiểm thử hệ sinh thái.
   * **Nếu URL khác** $\rightarrow$ **Spoke Context**: Chuyển sang kiểm tra tính toàn vẹn của Spoke (Bước 3).
   * **Tiêu chí hoàn thành:** Xác định chính xác vai trò ngữ cảnh đang vận hành (Hub hay Spoke).

2. **Kiểm Tra Kết Nối AI Gateway (RULE-4.5):**
   * Kiểm tra kết nối tới LiteLLM Gateway ở Server Spark: `http://100.83.192.30:8090/v1` (hoặc biến `AI_GATEWAY_URL`) kèm token Bearer: `Authorization: Bearer sk-spark-secure-key-2026`.
   * Nếu kết nối lỗi, cảnh báo và hướng dẫn người dùng kích hoạt Tailscale VPN (`100.83.192.30`) để kết nối vào mạng nội bộ CCBA.
   * **Tiêu chí hoàn thành:** Xác nhận kết nối thành công tới LiteLLM Gateway hoặc hiển thị hướng dẫn kết nối Tailscale VPN rõ ràng.

3. **Kiểm Tra Tính Toàn Vẹn Cấu Trúc Spoke (Spoke Integrity Audit):**
   * *(Chỉ áp dụng trong Spoke Context)* Kiểm tra sự tồn tại của thư mục tri thức `.\.md\` và tệp tin SSoT `.\.md\workspace_context.yaml`:
     - Nếu chưa có thư mục `.md/`:
       - Dự án có mã nguồn hiện hữu $\rightarrow$ Đề xuất chạy ngay `/ccba-spoke-adopter`.
       - Thư mục hoàn toàn mới $\rightarrow$ Đề xuất chạy `/ccba-init-spoke`.
     - Nếu đã có `.md/` nhưng thiếu `workspace_context.yaml` $\rightarrow$ Đề xuất cập nhật cấu hình Spoke khai báo `archetype` và `hub_packages`.
   * **Tiêu chí hoàn thành:** Đảm bảo thư mục `.md/` tồn tại và tệp SSoT `workspace_context.yaml` sẵn sàng.

---

## ⚡ Ma Trận Điều Phối Kỹ Năng Toàn Cục (Global Dispatch Matrix)

Khi người dùng gọi `/ccba-platform` hoặc đưa ra yêu cầu tác vụ, Agent căn cứ vào ma trận dưới đây để đối soát và kích hoạt kỹ năng tương ứng (hỗ trợ nhập số thứ tự, gõ Slash Command hoặc mô tả nghiệp vụ):

| # | Nhóm Miền Nghiệp Vụ (Domain Bundle) | Kỹ Năng / Lệnh Kích Hoạt | Vai Trò & Mô Tả Tác Vụ | Đường Dẫn Định Nghĩa |
| :---: | :--- | :--- | :--- | :--- |
| `1` | **Quản Lý Spoke (`_core`)** | `/ccba-init-spoke` | Khởi tạo Spoke dự án MỚI TINH (Greenfield) chuẩn cấu trúc `.md/` | `[hub_path]/.agents/skills/ccba-init-spoke/SKILL.md` |
| `2` | **Quản Lý Spoke (`_core`)** | `/ccba-spoke-adopter` | Đánh giá hiện trạng & Tiếp nhận CODEBASE HIỆN HỮU (Brownfield) | `[hub_path]/.agents/skills/ccba-spoke-adopter/SKILL.md` |
| `3` | **Quản Lý Spoke (`_core`)** | `/ccba-update-spoke` | Đồng bộ kỹ năng, kiểm tra trạng thái lệch phiên bản (Sync & Drift Audit) | `[hub_path]/.agents/skills/ccba-update-spoke/SKILL.md` |
| `4` | **Quản Lý Spoke (`_core`)** | `bootstrap-spoke` | Thiết lập liên kết Monorepo packages cho Spoke venv (HUB-ADR-0044) | CLI: `python scripts/ccba_platform_cli.py bootstrap-spoke` |
| `5` | **Phát Triển SDLC (`_core`/`_software`)** | `/ccba-new-feature` | Khởi tạo feature branch mới & lập kế hoạch Factory Model (RULE-4.1) | `[hub_path]/.agents/skills/ccba-new-feature/SKILL.md` |
| `6` | **Phát Triển SDLC (`_software`)** | `/ccba-implement` | Hiện thực hóa tính năng theo TDD Red-Green-Refactor & Scoped Testing | `[hub_path]/.agents/skills/ccba-implement/SKILL.md` |
| `7` | **Phát Triển SDLC (`_software`)** | `/ccba-code-review` | Rà soát chất lượng code song song 2 trục (Standards & Spec) | `[hub_path]/.agents/skills/ccba-code-review/SKILL.md` |
| `8` | **Phát Triển SDLC (`_core`)** | `/ccba-contribute-to-hub` | Đóng gói mã nguồn, tests, proposal và mở PR đóng góp lên Hub | `[hub_path]/.agents/skills/ccba-contribute-to-hub/SKILL.md` |
| `9` | **Phát Triển SDLC (`_core`)** | `/ccba-release-feature` | Chạy slow integration tests, squash merge PR & đóng issue tự động | `[hub_path]/.agents/skills/ccba-release-feature/SKILL.md` |
| `10` | **Thẩm Tra Thiết Kế (`_qc`)** | `/ccba-ai-qc` | Thẩm tra chất lượng thiết kế đa bộ môn (Discovery, Quad-View, Heat Map) | `[hub_path]/.agents/skills/ccba-ai-qc/SKILL.md` |
| `11` | **Thẩm Tra Thiết Kế (`_qc`)** | `/ccba-ai-qc-pccc-audit` | Thẩm tra an toàn PCCC, MEP và thoát nạn theo QCVN 06:2022 | `[hub_path]/.agents/skills/ccba-ai-qc-pccc-audit/SKILL.md` |
| `12` | **Pháp Lý Xây Dựng (`_consulting`)** | `/ccba-legal-advisor` | Phỏng vấn thích ứng & xuất Phiếu Ý kiến Pháp lý chuẩn OKF v2.4 (RULE-4.2) | `[hub_path]/.agents/skills/ccba-legal-advisor/SKILL.md` |
| `13` | **Pháp Lý Xây Dựng (`_consulting`)** | `/ccba-legal-ingest` | Thu nạp văn bản TVPL tự động vào Spoke tri thức (RULE-4.2) | `[hub_path]/.agents/skills/ccba-legal-ingest/SKILL.md` |
| `14` | **Pháp Lý Xây Dựng (`_consulting`)** | `/ccba-legal-document-tracker` | Tra cứu hiệu lực, so sánh sửa đổi văn bản quy phạm pháp luật | `[hub_path]/.agents/skills/ccba-legal-document-tracker/SKILL.md` |
| `15` | **Quản Trị BIGBIM (`_bim`)** | `/bigbim-classification` | Bảng thực thể Uniclass 200, ISO 12006-2 & Room Naming (RULE-4.2) | `[hub_path]/.agents/skills/bigbim-classification/SKILL.md` |
| `16` | **Quản Trị BIGBIM (`_bim`)** | `/bigbim-governance` | Hiến pháp Sợi Chỉ Vàng, rào chắn Sợi Chỉ Đỏ & Unique ID (RULE-4.2) | `[hub_path]/.agents/skills/bigbim-governance/SKILL.md` |
| `17` | **Thể Chế & Quản Trị (`_core`)** | `/ccba-adr-lifecycle` | Khởi tạo ADR, cascade status, ma trận truy vết sống (HUB-ADR-0037) | `[hub_path]/.agents/skills/ccba-adr-lifecycle/SKILL.md` |
| `18` | **Thể Chế & Quản Trị (`_core`)** | `/ccba-docs-manager` | Quản trị tài liệu, kiểm toán 5 trục (`doc-audit` / `validate-cross-ref`) | `[hub_path]/.agents/skills/ccba-docs-manager/SKILL.md` |
| `19` | **Thể Chế & Quản Trị (`_core`)** | `/ccba-markdown-document-processing` | Chuyển đổi Word/PDF sang Markdown chuẩn hóa qua ConversionPipeline | `[hub_path]/.agents/skills/ccba-markdown-document-processing/SKILL.md` |
| `20` | **Thể Chế & Quản Trị (`_core`)** | `/ccba-session-retrospective` | Tổng kết bài học và cập nhật tri thức cuối phiên làm việc | `[hub_path]/.agents/skills/ccba-session-retrospective/SKILL.md` |
| `21` | **Chốt Chặn Kiểm Định (`_core`)** | `ccba-harness verify-patch` | Chốt chặn hoàn thành tất định (HUB-ADR-0058 Hard Completion Lock) | CLI: `python -m ccba_harness verify-patch` |

---

## 🔄 Quy Trình Phân Phối & Kiến Trúc Điều Phối (Execution Protocol)

1. **Nhận Diện & Điều Hướng (Dispatch Resolution):**
   * Ánh xạ yêu cầu của người dùng (số thứ tự `1–21`, từ khóa kích hoạt, hoặc tên lệnh) tới kỹ năng tương ứng trong Ma Trận Điều Phối.
   * **Tiêu chí hoàn thành:** Xác định chính xác tên kỹ năng hoặc lệnh CLI cần khởi chạy.

2. **Nạp Kỹ Năng Ưu Tiên Spoke-First (Virtual Hub Fallback Invariant):**
   * Agent **bắt buộc** kiểm tra tệp tin kỹ năng cục bộ tại Spoke trước: `.\.agents\skills\<tên-kỹ-năng>\SKILL.md`.
   * Nếu Spoke chưa cài đặt kỹ năng này $\rightarrow$ Tự động nạp qua cơ chế **Virtual Hub Fallback** từ `[hub_path]/.agents/skills/<tên-kỹ-năng>/SKILL.md` bằng công cụ `view_file`.
   * **Tiêu chí hoàn thành:** Nạp đầy đủ chỉ dẫn vận hành của kỹ năng mục tiêu vào ngữ cảnh làm việc.

3. **Phân Quyền Ghi Đĩa (Single-Writer Protocol — HUB-ADR-0053):**
   * Duy nhất Lead Orchestrator có quyền ghi (Single-Writer) vào codebase và tài liệu chính thức.
   * Mọi worker/subagents chỉ được phép hoạt động ở chế độ chỉ đọc (read-only) hoặc xuất kết quả nháp vào thư mục sandbox scratch (`.system_generated/scratch/` hoặc `<appDataDir>\brain\<conversation-id>/scratch/`).
   * Áp dụng giao thức **Transient-to-Permanent Mirroring (HUB-ADR-0058)** để đồng bộ các artifacts đã kiểm định sang thư mục lưu trữ tri thức `.\.md\`.
   * **Tiêu chí hoàn thành:** Toàn bộ thao tác ghi codebase được kiểm soát tập trung, không phát sinh xung đột đa tiến trình.

4. **Khóa Cứng Hoàn Tất Tất Định (HUB-ADR-0058 Hard Completion Lock):**
   * Sau khi thực thi xong quy trình kỹ năng, Agent bắt buộc chạy kiểm định tự động:
     ```bash
     python -m ccba_harness verify-patch
     ```
   * Tuyệt đối không tuyên bố hoàn tất tác vụ hoặc yêu cầu người dùng nghiệm thu nếu lệnh kiểm định trả về mã lỗi $\ne 0$.
   * **Tiêu chí hoàn thành:** Lệnh verify-patch đạt trạng thái `ALL PASSED` (Exit Code 0).

---

## 📚 Tra Cứu Catalog Đầy Đủ
* Tra cứu danh mục chi tiết toàn bộ kỹ năng và công cụ của nền tảng tại: [`catalog.yaml`](../platform-loader/catalog.yaml)
* Hoặc liệt kê nhanh qua dòng lệnh: `python scripts/governance/compile_catalog.py --list`
