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

3. **Phân Loại Ngữ Cảnh Tô Pô & Động Học 5 Bối Cảnh (Context-Aware Dynamic Dispatch):**
   Agent bắt buộc xác định chính xác dự án đang thuộc về 1 trong 5 bối cảnh sau đây để lọc thực đơn điều phối:
   - **Bối cảnh 1: Hub Monorepo Context**
     - Dấu hiệu: `git remote get-url origin` chứa `ccba-agent-platform`.
     - Hành vi điều phối: **ẨN TOÀN BỘ** các lệnh khởi tạo/adopt Spoke (`/ccba-init-spoke`, `/ccba-spoke-adopter`, `bootstrap-spoke`). Chỉ hiển thị các kỹ năng phát triển nền tảng (SDLC `_core`, `_software`, Governance, Verify).
   - **Bối cảnh 2: Greenfield Spoke Context (Thư mục trống / Dự án mới tinh)**
     - Dấu hiệu: Thư mục chưa có mã nguồn hoặc chưa có `.git`, chưa có `.md/`.
     - Hành vi điều phối: **CHỈ HIỂN THỊ DUY NHẤT** `/ccba-init-spoke` để khởi tạo cấu trúc chuẩn ban đầu.
   - **Bối cảnh 3: Brownfield Spoke Context (Codebase hiện hữu chưa cấu hình)**
     - Dấu hiệu: Đã có mã nguồn dự án nhưng hoàn toàn chưa có `.md/workspace_context.yaml`.
     - Hành vi điều phối: **CHỈ HIỂN THỊ** `/ccba-spoke-adopter` để phân tích và tiếp nhận không phá hủy.
   - **Bối cảnh 4: Multi-Device Cloned Spoke Context (Spoke đã đăng ký được clone sang máy mới)**
     - Dấu hiệu: ĐÃ CÓ `.md/workspace_context.yaml` (hoặc `.agents/workspace_context.yaml`) nhưng chưa có môi trường Python ảo (`.venv`) hoặc chưa liên kết editable packages với Hub.
     - Hành vi điều phối: **ẨN HOÀN TOÀN** `/ccba-init-spoke` và `/ccba-spoke-adopter` để tuân thủ hiến pháp *Single-User Multi-Device*. Đặt lệnh bootstrap môi trường lên vị trí ưu tiên hàng đầu:
       - Linux / macOS / WSL:
         ```bash
         python3 "$CCBA_HUB_PATH/scripts/ccba_platform_cli.py" bootstrap-spoke --create-venv
         ```
       - Windows PowerShell:
         ```powershell
         python "$env:CCBA_HUB_PATH/scripts/ccba_platform_cli.py" bootstrap-spoke --create-venv
         ```
   - **Bối cảnh 5: Healthy Ready Spoke Context (Spoke hoàn chỉnh, môi trường sẵn sàng)**
     - Dấu hiệu: Đã có `.md/workspace_context.yaml` VÀ `.venv` đã kích hoạt / liên kết đầy đủ.
     - Hành vi điều phối: Ẩn các lệnh onboarding ban đầu; chỉ hiển thị các kỹ năng nghiệp vụ tương ứng với `archetype` của Spoke (`_qc`, `_consulting`, `_bim`, `_software`) và các lệnh cập nhật (`/ccba-update-spoke`, `verify-patch`).
   * **Tiêu chí hoàn thành:** Phân loại chính xác bối cảnh 1-5 và lọc thực đơn điều hướng tương ứng.

4. **Kiểm Định Cấu Hình Tô Pô Hệ Điều Hành (OS Topology Audit - HUB-ADR-0049 / HUB-ADR-0051):**
   * Tự động nhận diện hệ điều hành môi trường thực thi (Linux, WSL, Windows, macOS).
   * Kiểm tra tính tương thích của đường dẫn Hub (`hub_path` hoặc `project.hub_path`) trong `workspace_context.yaml` hoặc biến môi trường `CCBA_HUB_PATH`:
     - Ưu tiên hàng đầu: Sử dụng biến môi trường hệ thống `CCBA_HUB_PATH` để cô lập máy hoàn toàn.
     - Khi lưu đường dẫn tương đối trong `workspace_context.yaml`: Luôn dùng định dạng POSIX (`../ccba-agent-platform`) để bảo đảm tính khả chuyển.
   * **Tiêu chí hoàn thành:** Đường dẫn Hub tương thích 100% với hệ điều hành thực tế, không gây crash hoặc rò rỉ đường dẫn tuyệt đối của máy trạm.

---

## ⚡ Ma Trận Điều Phối Kỹ Năng Động (Dynamic Context-Aware Dispatch Matrix)

Căn cứ vào kết quả nhận diện 5 bối cảnh ở Pha 1, Agent chủ động lọc và hiển thị danh mục lệnh phù hợp với trạng thái thực tế của dự án:

### 🌟 Bảng Kỹ Năng Phân Nhóm Theo Bối Cảnh

| Nhóm Bối Cảnh | Lệnh / Slash Command | Vai Trò & Mô Tả Tác Vụ | Phương Thức Kích Hoạt |
| :--- | :--- | :--- | :--- |
| **Bối cảnh 2 (Greenfield)** | `/ccba-init-spoke` | Khởi tạo Spoke dự án MỚI TINH chuẩn cấu trúc `.md/` | Slash command hoặc `[hub_path]/.agents/skills/ccba-init-spoke/SKILL.md` |
| **Bối cảnh 3 (Brownfield)** | `/ccba-spoke-adopter` | Đánh giá hiện trạng & Tiếp nhận CODEBASE HIỆN HỮU không phá hủy | Slash command hoặc `scripts/adopt_spoke.py` |
| **Bối cảnh 4 (Multi-Device)** | `bootstrap-spoke` | Khởi tạo `.venv` và liên kết editable packages cho Spoke đã clone | `python3 "$CCBA_HUB_PATH/scripts/ccba_platform_cli.py" bootstrap-spoke --create-venv` |
| **Bối cảnh 5 & Hub Monorepo** | `/ccba-update-spoke` | Đồng bộ kỹ năng, kiểm tra trạng thái lệch phiên bản (Drift Audit) | Slash command hoặc `scripts/sync_spoke.py` |
| **Bối cảnh 5 & Hub Monorepo** | `/ccba-new-feature` | Khởi tạo feature branch mới & lập kế hoạch Factory Model | Slash command hoặc `[hub_path]/.agents/skills/ccba-new-feature/SKILL.md` |
| **Bối cảnh 5 & Hub Monorepo** | `/ccba-implement` | Hiện thực hóa tính năng theo TDD Red-Green-Refactor & Scoped Tests | Slash command hoặc `[hub_path]/.agents/skills/ccba-implement/SKILL.md` |
| **Bối cảnh 5 & Hub Monorepo** | `/ccba-code-review` | Rà soát chất lượng code song song 2 trục (Standards & Spec) | Slash command hoặc `[hub_path]/.agents/skills/ccba-code-review/SKILL.md` |
| **Bối cảnh 5 & Hub Monorepo** | `/ccba-contribute-to-hub` | Đóng gói mã nguồn, tests, proposal và mở PR đóng góp lên Hub | Slash command hoặc `[hub_path]/.agents/skills/ccba-contribute-to-hub/SKILL.md` |
| **Bối cảnh 5 & Hub Monorepo** | `/ccba-release-feature` | Chạy slow integration tests, squash merge PR & đóng issue tự động | Slash command hoặc `[hub_path]/.agents/skills/ccba-release-feature/SKILL.md` |
| **Nghiệp Vụ Thẩm Tra (`_qc`)** | `/ccba-ai-qc` | Thẩm tra chất lượng thiết kế đa bộ môn (Discovery, Quad-View, Heat Map) | `[hub_path]/.agents/skills/ccba-ai-qc/SKILL.md` |
| **Nghiệp Vụ Thẩm Tra (`_qc`)** | `/ccba-ai-qc-pccc-audit` | Thẩm tra an toàn PCCC, MEP và thoát nạn theo QCVN 06:2022 | `[hub_path]/.agents/skills/ccba-ai-qc-pccc-audit/SKILL.md` |
| **Nghiệp Vụ Pháp Lý (`_consulting`)** | `/ccba-legal-advisor` | Phỏng vấn thích ứng & xuất Phiếu Ý kiến Pháp lý chuẩn OKF v2.4 | `[hub_path]/.agents/skills/ccba-legal-advisor/SKILL.md` |
| **Nghiệp Vụ Pháp Lý (`_consulting`)** | `/ccba-legal-ingest` | Thu nạp văn bản TVPL tự động vào Spoke tri thức chuẩn hoá | `[hub_path]/.agents/skills/ccba-legal-ingest/SKILL.md` |
| **Nghiệp Vụ Pháp Lý (`_consulting`)** | `/ccba-legal-document-tracker` | Tra cứu hiệu lực, so sánh sửa đổi văn bản quy phạm pháp luật | `[hub_path]/.agents/skills/ccba-legal-document-tracker/SKILL.md` |
| **Quản Trị BIGBIM (`_bim`)** | `/bigbim-classification` | Bảng thực thể Uniclass 200, ISO 12006-2 & Room Naming | `[hub_path]/.agents/skills/bigbim-classification/SKILL.md` |
| **Quản Trị BIGBIM (`_bim`)** | `/bigbim-governance` | Hiến pháp Sợi Chỉ Vàng, rào chắn Sợi Chỉ Đỏ & Unique ID | `[hub_path]/.agents/skills/bigbim-governance/SKILL.md` |
| **Thể Chế & Quản Trị (`_core`)** | `/ccba-adr-lifecycle` | Khởi tạo ADR, cascade status, ma trận truy vết sống | `[hub_path]/.agents/skills/ccba-adr-lifecycle/SKILL.md` |
| **Thể Chế & Quản Trị (`_core`)** | `/ccba-docs-manager` | Quản trị tài liệu, kiểm toán 5 trục (`doc-audit` / `validate-cross-ref`) | `[hub_path]/.agents/skills/ccba-docs-manager/SKILL.md` |
| **Thể Chế & Quản Trị (`_core`)** | `/ccba-markdown-document-processing` | Chuyển đổi Word/PDF sang Markdown chuẩn hóa qua ConversionPipeline | `[hub_path]/.agents/skills/ccba-markdown-document-processing/SKILL.md` |
| **Thể Chế & Quản Trị (`_core`)** | `/ccba-session-retrospective` | Tổng kết bài học và cập nhật tri thức cuối phiên làm việc | `[hub_path]/.agents/skills/ccba-session-retrospective/SKILL.md` |
| **Chốt Chặn Kiểm Định (`_core`)** | `verify-patch` | Chốt chặn hoàn thành tất định (HUB-ADR-0058 Hard Completion Lock) | CLI: `.venv/bin/python -m ccba_harness verify-patch` |

---

## 🔄 Quy Trình Phân Phối & Kiến Trúc Điều Phối (Execution Protocol)

1. **Nhận Diện & Điều Hướng (Dispatch Resolution):**
   * Ánh xạ yêu cầu của người dùng (bối cảnh dự án, từ khóa kích hoạt, hoặc tên lệnh) tới kỹ năng tương ứng trong Ma Trận Điều Phối Động.
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
