---
id: 231
title: "feat(adr): tiered traceability matrix preserving spoke local domain decisions"
state: "ready-for-agent"
labels:
  - "enhancement"
  - "ready-for-agent"
assignee: "none"
created_at: "2026-09-02T06:27:52Z"
updated_at: "2026-09-02T06:40:00Z"
---

# 📖 Mô tả (Description)
### 1. Bối cảnh & Vấn đề (Context & Problem):
- CCBA Hub hiện quản lý 54 ADRs cốt lõi của nền tảng (`docs/adr/`).
- Một số Spoke chuyên biệt (như Spoke Tri thức Pháp lý `ccba-legal-knowledge`) sở hữu các quyết định kiến trúc nghiệp vụ đặc thù (ví dụ ADR 0021-0039 riêng cho pháp điển hóa, trích xuất KaTeX và AST clauses).
- Khi chạy script đồng bộ hóa `sync_hub_adr_matrix.py`, tệp `docs/adr/TRACEABILITY_MATRIX.md` tại Spoke bị ghi đè hoàn toàn theo Hub, làm mất đi các mục ADR nội bộ quan trọng của Spoke hoặc gây xung đột merge.

---

### 2. Đề xuất giải pháp (RFC Proposal):
Nâng cấp cơ chế biên dịch ma trận truy vết trong `scripts/sync_hub_adr_matrix.py`:
- **Phân tầng Ma trận (Two-Tier Architecture Matrix):**
  - **Tier 1 — Platform Constitution (Hub ADRs):** Danh mục 54+ ADRs dùng chung của nền tảng (bảo đảm đồng bộ 100% từ Hub).
  - **Tier 2 — Spoke Local Decisions (Domain ADRs):** Tự động quét thư mục `docs/adr/` cục bộ của Spoke, trích xuất các ADR riêng biệt và sáp nhập vào phần `## Domain-Specific Architecture Decisions` mà không ghi đè.
- **Bảo toàn số hiệu & Trạng thái ADR:** Hỗ trợ mapping và kiểm tra trạng thái (Approved/Superseded) cho cả 2 tầng ADR.

---

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [ ] `sync_hub_adr_matrix.py` tự động nhận diện và bảo toàn 100% các ADR cục bộ tại Spoke.
- [ ] Không làm mất các bảng đối soát và quy chuẩn đặc thù của Spoke trong `TRACEABILITY_MATRIX.md`.
- [ ] Tích hợp vào CI Gate `validate_legal_spoke.py` (Gate 10) và các Spoke validators khác.

---
*Được đề xuất tự động từ Spoke `ccba-legal-knowledge` qua workflow `/ccba-issue-to-hub`.*

---

# 💬 Thảo luận (Discussion Log)
> **@Antigravity AI Agent (Triage)** (2026-09-02T06:40:00Z):
> Đã hoàn tất quy trình sàng lọc và thẩm định kỹ thuật (Triage).
> Xác nhận nhu cầu phân tầng bảo toàn ADR tại Spoke theo mô hình Two-Tier Matrix (Hub Platform ADRs + Spoke Domain ADRs) để tránh việc sync làm mất các quyết định kiến trúc nghiệp vụ riêng của từng dự án/Spoke.
> Đã gán nhãn `enhancement` và chuyển trạng thái sang `ready-for-agent`. Đính kèm Agent Brief chi tiết bên dưới.

---

## Agent Brief

**Phân loại:** enhancement
**Tóm tắt yêu cầu:** Nâng cấp `scripts/sync_hub_adr_matrix.py` và quy trình ADR Matrix theo cơ chế Two-Tier Preservation để bảo toàn các ADR cục bộ của Spoke.

### Hành vi hiện tại (Current behavior)
- `scripts/sync_hub_adr_matrix.py` chỉ quét đơn lẻ thư mục `docs/adr/` hiện tại và ghi đè danh mục mà không phân biệt Hub Platform ADRs và Spoke Domain ADRs.
- Khi Spoke có các ADR nghiệp vụ riêng (ví dụ ADR pháp điển, ADR schema đặc thù), việc biên dịch lại làm mất hoặc xáo trộn ma trận truy vết.

### Hành vi mong muốn (Desired behavior)
- `sync_hub_adr_matrix.py` hỗ trợ cơ chế Two-Tier:
  - Tầng 1: Hub Platform ADRs (đồng bộ chuẩn hóa từ Hub).
  - Tầng 2: Spoke Domain ADRs (quét và sáp nhập vào phần Domain-Specific Architecture Decisions).
- Tự động nhận diện cờ `--spoke` hoặc chạy trực tiếp tại Spoke mà không xóa đè các quyết định cục bộ.
- Sinh `TRACEABILITY_MATRIX.md` đầy đủ liên kết và trạng thái.

### Các Interface & Kiểu dữ liệu chính (Key interfaces)
- `scripts/sync_hub_adr_matrix.py`:
  - `parse_adr_file(adr_path: Path) -> dict[str, Any]`
  - `compile_two_tier_adr_matrix(hub_adrs: list, spoke_adrs: list, target_file: Path)`

### Tiêu chuẩn nghiệm thu (Acceptance criteria)
- [ ] Biên dịch `TRACEABILITY_MATRIX.md` tại Spoke bảo toàn 100% ADRs của Hub và ADRs của Spoke.
- [ ] Không có broken link giữa các tệp ADR trong bảng chỉ mục.
- [ ] Bổ sung unit test kiểm tra Two-Tier ADR merging.

### Phạm vi loại trừ (Out of scope)
- Không can thiệp vào định dạng Markdown chuẩn của các file ADR hiện hữu.

### Đề xuất chế độ thực thi (Recommended Execution Strategy)
- **Mức độ phức tạp**: Gọn nhẹ / Cục bộ trong `scripts/`
- **Khuyến nghị thực thi**:
  - `[x]` 🟢 **Standard** (`/ccba-implement`): Triển khai tuần tự, scoped tests.
  - `[ ]` 🟣 **Deep Reasoning** (`/boost`): Điều tra chuyên sâu root-cause / phản biện đa vòng.
  - `[ ]` 🔵 **Multi-Agent Orchestration** (`/ccba-teamwork` hoặc `/teamwork-preview`): Phân rã Seams và chạy đa tác nhân song song.
