# 0066. Skills Taxonomy, Multi-Environment Distribution Matrix, and Slash Command Governance

* **Status:** Accepted
* **Date:** 2026-10-06
* **Deciders:** CCBA Platform Core Team & Peer Agents (Grok, Gemini)
* **Consulted:** ADR 0009 (Pstack Disciplines), ADR 0044 (Spoke Bootstrap & Cleanliness), ADR 0047 (Catalog Manifest SSOT), ADR 0057 (Two-Stage Decision Framework & GPI)

---

## Context & Problem Statement

Sau khi triển khai Khung Quyết Định Hai Giai Đoạn và Chỉ số GPI (ADR 0057), nền tảng đã kiểm soát thành công việc phân tầng giữa Monorepo Deep Seams (Tier 1), Progressive References (Tier 2A), và Standalone Kernel Skills (Tier 2B). Tuy nhiên, trong quá trình tiếp thu các kỹ luật kiểm định Pstack Upstream (ADR 0009) và vận hành hệ sinh thái phân tán Hub-Spoke, một khoảng trống kiến trúc mới xuất hiện:

1. **Sự Cố Lệch Pha Slash Command Tại Spoke (The Slash Command Ergonomics Gap):**
   Khi kỹ năng `/ccba-create-verification-skill` được khởi tạo với `bundle: _governance`, nó chỉ tồn tại vật lý tại Hub. Khi lập trình viên mở một Spoke repository và gõ `/` trên thanh chat của IDE (Antigravity/Cursor), menu popup tự động gợi ý (Autocomplete Dropdown) không hiển thị lệnh này vì IDE chỉ quét các tệp `SKILL.md` vật lý trong workspace cục bộ. Mặc dù cơ chế **Virtual Hub Fallback** cho phép thực thi nếu gõ tay đầy đủ, việc thiếu gợi ý popup làm suy giảm nghiêm trọng tính công thái học và khả năng khám phá công cụ của nhà phát triển.

2. **Nguy Cơ Bẫy Ranh Giới Giữa `_core` và `_software` (Boundary Trap):**
   Thiếu tiêu chí định lượng để phân định giữa một công cụ phát triển dùng chung cho mọi dự án và một kỹ năng kỹ thuật phần mềm chuyên sâu. Nếu định nghĩa cảm tính, các công cụ kiểm định vòng đời dễ bị đẩy vào `_software` (khiến các Spoke phi phần mềm như Pháp điển, Thẩm tra không có), hoặc ngược lại làm phình `_core` với các công cụ framework chuyên biệt gây loãng menu lệnh.

3. **Thiếu Khai Báo Tường Minh Về Phạm Vi Hiện Diện (`scope`):**
   Hệ thống thiếu một thuộc tính metadata chuẩn để phân biệt các lệnh chỉ dành riêng cho Maintainer tại Hub (như `/ccba-adr-lifecycle`) với các lệnh phổ quát cho mọi Spoke, dẫn đến nguy cơ báo động giả (False Positive) khi thiết lập các bộ linter kiểm tra phân phối lệnh.

---

## Decision Outcome

Đội ngũ kiến trúc CCBA quyết định ban hành và thực thi toàn diện:

### 1. Nguyên Tắc Phân Định Vận Hành Nền Tảng (Platform Operations Invariant)
Phân định rạch ròi giữa công cụ điều phối vòng lặp phát triển của Agent và nghiệp vụ chuyên ngành:

- **`bundle: _core` (Platform Lifecycle Operations)**:
  - **Phạm vi**: 100% mọi Spoke bất kể `project_type`.
  - **Tiêu chí**: Chỉ chứa các công cụ điều phối vòng lặp phát triển chuẩn của Agent (SDLC Loop) và giao thức đồng bộ Hub-Spoke:
    - Đồng bộ Spoke (`ccba-update-spoke`, `sync-spoke`).
    - Kiểm tra và sinh bộ test harness (`ccba-create-verification-skill`).
    - Rà soát mã nguồn & Anti-Slop (`ccba-code-review`).
    - Quy trình phát hành tính năng & PR (`ccba-new-feature`, `ccba-create-pr`).
  - **Trải nghiệm**: Tự động đồng bộ vật lý xuống mọi Spoke; luôn hiện diện trong menu autocomplete Slash Command (`/`).

- **`bundle: _software` (Application Engineering Domain)**:
  - **Phạm vi**: Đồng bộ có chọn lọc khi Spoke có `project_type: software` trong `workspace_context.yaml`.
  - **Tiêu chí**: Chứa các kỹ năng lập trình nghiệp vụ ứng dụng chuyên sâu:
    - Quản trị mô hình AI & vLLM runtime (`ccba-vllm-manager`, `ccba-ai-gateway-sdk`).
    - Kiến trúc streaming, circuit breaker, batch pipelines.
    - Frameworks frontend / backend chuyên biệt.

- **`bundle: _governance` (Platform Governance Only)**:
  - **Phạm vi**: Chỉ cư trú vật lý tại Hub (`ccba-agent-platform`).
  - **Tiêu chí**: Chỉ phục vụ công tác quản trị kiến trúc, vòng đời ADR (`ccba-adr-lifecycle`) hoặc duyệt proposal đóng góp (`ccba-review-proposal`). Không copy xuống Spoke; Spoke triệu hồi qua Virtual Hub Fallback khi cần.

---

### 2. Chuẩn Hóa Thuộc Tính Khai Báo `scope` Trong Metadata YAML
Bổ sung trường `scope` chính tắc vào frontmatter của mọi tệp `SKILL.md`:

```yaml
---
name: ccba-skill-name
scope: hub | spoke | universal   # Bắt buộc khai báo
bundle: _core | _governance | ...
---
```

- **`scope: universal`**: Kỹ năng dùng được ở cả Hub và mọi Spoke (bắt buộc phải thuộc `_core` hoặc các bundle domain).
- **`scope: spoke`**: Kỹ năng chỉ có ý nghĩa vận hành tại Spoke (ví dụ: các kỹ năng kiểm định `verify-<app>`).
- **`scope: hub`**: Kỹ năng chỉ dành riêng cho Maintainer tại Hub (cho phép đi kèm `bundle: _governance` mà không bị linter cảnh báo).

---

### 3. Cây Quyết Định Gán Bundle & Bộ Chốt Chặn Linter Tự Động (Automated Linters)

1. **Linter Rule — Slash Command Distribution Guardrail (`validate_skills.py`)**:
   Khi một kỹ năng có `user-invocable: true` VÀ có khai báo `command: /...`:
   - Nếu kỹ năng thuộc `bundle: _governance` nhưng thiếu `scope: hub`:
     $\implies$ **Chặn CI (Exit Code 1)** với thông báo: *"Kỹ năng có command tương tác nhưng đặt bundle: _governance và thiếu scope: hub, dẫn đến việc lập trình viên tại Spoke không nhận được gợi ý Slash Command. Bắt buộc chuyển sang bundle: _core hoặc khai báo scope: hub nếu chỉ dùng tại Hub."*
   - Hỗ trợ comment chú thích ngoại lệ chuyển tiếp: `# ccba:allow-hub-only-command`.

2. **Deterministic GPI Recalculation Check (COND-01)**:
   Bộ kiểm tra `validate_skills.py` tự động tính toán lại điểm GPI từ các tham số `{s, k, a, p}` khai báo trong frontmatter:
   $$\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$$
   Nếu điểm tổng kết trong frontmatter sai lệch so với công thức toán học $\implies$ **Báo lỗi CI**.

3. **Virtual Hub Fallback Navigation Banner (COND-02)**:
   Khi Agent tại Spoke triệu hồi một kỹ năng từ Hub qua cơ chế Virtual Hub Fallback, runtime phát thông báo điều hướng minh bạch cho người dùng:
   `[Virtual Hub] Sourcing skill 'ccba-<name>' from Hub (<hub_path>)...`

---

## Consequences

### Positive
- **100% Autocomplete Parity**: Toàn bộ các lệnh phát triển cốt lõi (`_core`) tự động xuất hiện trên menu gợi ý Slash Command (`/`) của mọi Spoke.
- **Zero Ambiguity**: Ranh giới giữa `_core` và `_software` được định nghĩa bằng tiêu chuẩn Platform Operations Invariant thay vì suy đoán cảm tính.
- **Fail-Closed Governance**: Linter tự động ngăn chặn việc gán nhầm bundle ngay trong pull request.

### Negative
- **Frontmatter Addition**: Cần bổ sung trường `scope: hub | spoke | universal` cho các kỹ năng cốt lõi.
- **Spoke Storage Overhead**: Thêm một số tệp `SKILL.md` của `_core` được copy vật lý xuống Spoke, tuy nhiên dung lượng mỗi skill $\le 10\text{ KB}$, hoàn toàn nằm trong ngân sách Zero-Bloat.
