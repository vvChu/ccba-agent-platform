---
name: ccba-platform
description: Cổng điều phối toàn cục (Global Router) và kiểm tra môi trường cho CCBA Agent Services Platform. Tự động kiểm tra VPN/Gateway, cấu trúc Spoke và điều hướng đúng kỹ năng.
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
  version: v4.0
  publisher: CCBA
---

# CCBA Platform — Global Entry Point & Orchestrator

> Đây là Global Skill khả dụng từ **mọi dự án** trong hệ sinh thái CCBA Agent Services Platform.
> Khi người dùng yêu cầu một trong các tác vụ dưới đây, Agent đọc định nghĩa kỹ năng tương ứng từ Hub rồi thực thi.
> Output và thành phẩm luôn lưu về thư mục dự án (Spoke) hiện tại để đảm bảo tính độc lập dữ liệu.

## Hub Location Phân Giải Động
* Đường dẫn gốc Platform Hub được tự động phân giải qua biến môi trường **`CCBA_HUB_PATH`**.
* Nếu biến môi trường không được đặt, Agent tự động duyệt ngược từ thư mục làm việc hiện tại (CWD) lên 5 cấp để tìm thư mục có chứa `.agents` làm gốc Hub.

---

## 🛡️ Pha 1: Kiểm Định Môi Trường & Điều Hướng Nhanh (Environment Verification)

Trước khi hiển thị Menu hoặc thực thi bất kỳ kỹ năng (skill) nào, Agent **bắt buộc** phải tự động chạy kiểm định môi trường dự án:

1. **Environment Liveness & VPN Check:**
   * Kiểm tra kết nối tới LiteLLM Gateway ở Server Spark: `http://100.83.192.30:8090/v1` (hoặc biến `AI_GATEWAY_URL`).
   * Nếu kết nối lỗi, cảnh báo và hướng dẫn người dùng bật VPN Tailscale để kết nối vào mạng nội bộ CCBA.
   * **Tiêu chí hoàn thành:** Xác nhận kết nối thành công tới LiteLLM Gateway hoặc hiển thị hướng dẫn kết nối Tailscale VPN rõ ràng.

2. **Spoke Integrity & Structure Audit:**
   * Kiểm tra sự tồn tại của thư mục tri thức `.md/` cục bộ tại Spoke. Nếu chưa có:
     - Nếu thư mục đã có mã nguồn hiện hữu $\rightarrow$ Đề xuất chạy ngay `/ccba-spoke-adopter` (Lựa chọn `2`).
     - Nếu là thư mục hoàn toàn mới $\rightarrow$ Đề xuất chạy `/ccba-init-spoke` (Lựa chọn `1`).
   * Kiểm tra tệp tin cấu hình dự án `.env` tại Spoke. Biến `CCBA_HUB_PATH` phải được định nghĩa hoặc tự động kế thừa.
   * **Tiêu chí hoàn thành:** Đảm bảo thư mục `.md/` tồn tại và các thông tin cấu hình cốt lõi của Spoke đã sẵn sàng.

---

## ⚡ Khi được gọi không có argument

Nếu người dùng gọi `/ccba-platform` mà **không kèm nội dung gì thêm**, sau khi kiểm định môi trường hoàn tất, Agent hiển thị menu điều phối trung tâm sau:

---

🏗️ **CCBA Agent Services Platform — Bạn muốn thực hiện tác vụ gì?**

**Quản lý Spoke & Khởi tạo môi trường:**
- `1` · **init spoke** (`/ccba-init-spoke`) — Khởi tạo Spoke dự án MỚI TINH (Greenfield)
- `2` · **adopt spoke** (`/ccba-spoke-adopter`) — Đánh giá hiện trạng & Tiếp nhận CODEBASE HIỆN HỮU an toàn (Brownfield / `adopt-spoke`)
- `3` · **update & sync spoke** (`/ccba-update-spoke`) — Đồng bộ kỹ năng, kiểm tra trạng thái lệch phiên bản (`sync-spoke`, `spoke-status`)
- `4` · **bootstrap spoke** (`bootstrap-spoke`) — Thiết lập liên kết Monorepo packages cho Spoke venv (HUB-ADR-0044)

**Thẩm tra Thiết kế & An toàn Công trình (AI QC):**
- `5` · **ai qc audit** (`/ccba-ai-qc`) — Thẩm tra chất lượng bản vẽ & mô hình đa bộ môn (Discovery, Quad-View, Heat Map)
- `6` · **pccc & mep audit** (`/ccba-ai-qc-pccc-audit`) — Thẩm tra an toàn PCCC, MEP và thoát nạn theo QCVN 06:2022

**Pháp lý Xây dựng & Thu nạp Tri thức (Legal):**
- `7` · **legal advisor** (kỹ năng `ccba-legal-advisor`) — Phỏng vấn thích ứng & xuất Phiếu Ý kiến Pháp lý (Legal Opinion) chuẩn OKF v2.4
- `8` · **legal ingest** (kỹ năng `ccba-legal-ingest` / CLI: `ingest-legal`) — Thu nạp văn bản TVPL tự động vào Spoke tri thức (HUB-ADR-0039)
- `9` · **legal document tracker** (`/ccba-legal-document-tracker`) — Tra cứu hiệu lực, so sánh sửa đổi văn bản quy phạm pháp luật

**Quản trị Thông tin BIGBIM:**
- `10` · **bigbim classification** (kỹ năng `bigbim-classification`) — Bảng thực thể Uniclass 200, ISO 12006-2 & Room Naming
- `11` · **bigbim governance** (kỹ năng `bigbim-governance`) — Hiến pháp Sợi Chỉ Vàng, rào chắn Sợi Chỉ Đỏ & Unique ID

**Quản trị Phần mềm, CI/CD & Tài liệu:**
- `12` · **adr lifecycle** (`/ccba-adr-lifecycle`) — Khởi tạo ADR, cascade status, ma trận truy vết và CI parity (HUB-ADR-0048)
- `13` · **verify patch** (`/ccba-eval-gate`) — Chốt chặn hoàn thành tất định (HUB-ADR-0058 Hard Completion Lock)
- `14` · **doc & cross-ref audit** (`doc-audit`) — Kiểm toán tài liệu 5 trục & ma trận liên kết chéo (`ccba-platform doc-audit`)
- `15` · **convert markdown** (`/ccba-markdown-document-processing`) — Chuyển đổi Word/PDF sang Markdown chuẩn hóa qua ConversionPipeline
- `16` · **session retrospective** (`/ccba-session-retrospective`) — Tổng kết bài học và cập nhật tri thức cuối phiên làm việc

---
*Trả lời bằng số (1-16), gõ trực tiếp Slash Command, hoặc mô tả yêu cầu công việc.*

---

## Trigger → Kỹ Năng (Skill) Mapping

Sau khi người dùng lựa chọn (bằng số hoặc keyword), Agent nạp và thực thi kỹ năng/lệnh tương ứng từ Hub (phân giải qua `[hub_path]`):

| Lựa chọn / Trigger | Lệnh trực tiếp / Tên Kỹ năng | Đường dẫn Kỹ năng / Công cụ tại Hub |
|---|---|---|
| `1` / `init spoke`, `setup dự án mới` | `/ccba-init-spoke` | `[hub_path]/.agents/skills/ccba-init-spoke/SKILL.md` |
| `2` / `adopt spoke`, `tiếp nhận dự án`, `brownfield` | `/ccba-spoke-adopter` | `[hub_path]/.agents/skills/ccba-spoke-adopter/SKILL.md` |
| `3` / `update spoke`, `đồng bộ hub`, `spoke status` | `/ccba-update-spoke` | `[hub_path]/.agents/skills/ccba-update-spoke/SKILL.md` |
| `4` / `bootstrap spoke`, `cài venv`, `monorepo link` | CLI `bootstrap-spoke` | `[hub_path]/scripts/spoke/spoke_bootstrap.py` |
| `5` / `ai qc`, `thẩm tra thiết kế`, `audit bản vẽ` | `/ccba-ai-qc` | `[hub_path]/.agents/skills/ccba-ai-qc/SKILL.md` |
| `6` / `pccc`, `thẩm tra pccc`, `thoát nạn` | `/ccba-ai-qc-pccc-audit` | `[hub_path]/.agents/skills/ccba-ai-qc-pccc-audit/SKILL.md` |
| `7` / `legal advisor`, `ý kiến pháp lý`, `tư vấn luật` | `ccba-legal-advisor` | `[hub_path]/.agents/skills/ccba-legal-advisor/SKILL.md` |
| `8` / `legal ingest`, `thu nạp văn bản`, `cào luật` | `ccba-legal-ingest` (CLI `ingest-legal`) | `[hub_path]/.agents/skills/ccba-legal-ingest/SKILL.md` |
| `9` / `legal tracker`, `tra cứu vbpl`, `so sánh luật` | `/ccba-legal-document-tracker` | `[hub_path]/.agents/skills/ccba-legal-document-tracker/SKILL.md` |
| `10` / `bigbim classification`, `uniclass`, `room naming` | `bigbim-classification` | `[hub_path]/.agents/skills/bigbim-classification/SKILL.md` |
| `11` / `bigbim governance`, `sợi chỉ vàng`, `unique id` | `bigbim-governance` | `[hub_path]/.agents/skills/bigbim-governance/SKILL.md` |
| `12` / `adr lifecycle`, `tạo adr`, `ma trận adr` | `/ccba-adr-lifecycle` | `[hub_path]/.agents/skills/ccba-adr-lifecycle/SKILL.md` |
| `13` / `verify patch`, `chốt chặn hoàn thành`, `verify` | `/ccba-eval-gate` | `[hub_path]/.agents/skills/ccba-eval-gate/SKILL.md` |
| `14` / `doc audit`, `cross ref`, `kiểm toán tài liệu` | CLI `doc-audit` / `validate-cross-ref` | `[hub_path]/scripts/ccba_platform_cli.py` |
| `15` / `convert markdown`, `chuyển đổi tài liệu` | `/ccba-markdown-document-processing` | `[hub_path]/.agents/skills/ccba-markdown-document-processing/SKILL.md` |
| `16` / `session retrospective`, `tổng kết phiên` | `/ccba-session-retrospective` | `[hub_path]/.agents/skills/ccba-session-retrospective/SKILL.md` |

---

## Cách thực thi & Kiến trúc Điều phối

1. **Nhận diện yêu cầu:** Xác định kỹ năng hoặc tiện ích phù hợp từ bảng điều phối trên theo lựa chọn của người dùng.
   * **Tiêu chí hoàn thành:** Nhận diện chính xác tệp kỹ năng hoặc lệnh CLI tương ứng với yêu cầu.
2. **Tải tài liệu kỹ năng:** Đọc tệp kỹ năng (`SKILL.md`) bằng `view_file` theo đường dẫn tuyệt đối phân giải từ `[hub_path]`.
   * **Tiêu chí hoàn thành:** Đọc thành công toàn bộ nội dung kỹ năng vào ngữ cảnh làm việc của Agent.
3. **Thực thi quy trình:** Tuân thủ chặt chẽ các bước và quy chuẩn trong kỹ năng đã tải.
   * **Tiêu chí hoàn thành:** Thực thi đầy đủ và chính xác tất cả các bước chỉ dẫn với tiêu chí hoàn thành tương ứng.
4. **Phân quyền ghi (Single-Writer Protocol):** Duy nhất Orchestrator có quyền ghi (Single-Writer) vào các tệp tin cấu hình và tài liệu chính; các worker/subagents chỉ hoạt động ở chế độ read-only để đảm bảo tính toàn vẹn dữ liệu.
   * **Tiêu chí hoàn thành:** Toàn bộ thao tác ghi đĩa được kiểm soát tập trung qua Orchestrator.
5. **Độc lập dữ liệu Spoke:** Lưu mọi output, báo cáo và sản phẩm đầu ra trực tiếp vào thư mục Spoke/Project hiện tại, không ghi đè vào Hub.
   * **Tiêu chí hoàn thành:** Xác nhận các tệp tin kết quả được lưu trữ đúng vị trí dự án cục bộ.

## Catalog đầy đủ

[catalog.yaml](../platform-loader/catalog.yaml)

## 4. Quy Chuẩn Đóng Gói Phản Hồi & Thẻ Cấu Trúc XML
* Mọi kết quả tra cứu và phân tích pháp lý bắt buộc phải được đóng gói qua cấu trúc thẻ:
  - `<legal_context>`: Tóm tắt bối cảnh và văn bản quy phạm pháp luật áp dụng (Luật, Nghị định, Thông tư).
  - `<legal_citation>`: Viện dẫn chính xác Điều, Khoản, Điểm kèm trích dẫn nguyên văn.
  - `<compliance_verdict>`: Kết luận tuân thủ pháp luật và khuyến nghị chuyên môn.
* Đảm bảo không phát sinh disclaimer từ chối đối với các yêu cầu hợp lệ trong lĩnh vực xây dựng.
