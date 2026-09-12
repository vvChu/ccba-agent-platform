---
name: ccba-setup-skills
description: Thiết lập cấu hình dự án (Spoke/Hub) cho các công cụ kỹ thuật — cấu hình
  issue tracker, nhãn phân loại (triage), và bố cục tài liệu tri thức (Domain Docs).
  Chạy một lần trước khi sử dụng các kỹ năng phát triển phần mềm.
disable-model-invocation: true
bundle: _core
tier: kernel
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 3.5
  k: 2.0
  a: 2.0
  p: 1.0
user-invocable: true
command: /ccba-setup-skills
triggers:
- setup skills
- thiết lập cấu hình
- cấu hình tracker
- cấu hình nhãn
- setup-skills
- ccba-setup-skills
- ccba-setup-pre-commit
- setup-pre-commit
- ccba-setup-ts-deep-modules
- setup-ts-deep-modules
---

# Kỹ năng Thiết Lập Cấu Hình Phát Triển (Setup CCBA Skills)

Dựng khung cấu hình cho repository hiện tại để các kỹ năng phát triển phần mềm khác (`ccba-triage`, `ccba-to-tickets`, `ccba-to-spec`, `ccba-tdd`, `ccba-improve-codebase-architecture`, v.v.) hoạt động chính xác:

- **Issue tracker** — Nơi theo dõi công việc (GitHub, GitLab, hoặc Local Markdown lưu offline).
- **Triage labels** — Từ vựng nhãn tương ứng với 5 vai trò trạng thái của triage.
- **Domain docs** — Cấu trúc tài liệu miền tri thức (`CONTEXT.md` và ADRs).
- **Skills Governance** — Thể chế quản trị kỹ năng 3 tầng và Khung Quyết Định Hai Giai Đoạn (ADR-0057 & RES-2026-ARCH-001 v1.2).

Đây là kỹ năng tương tác và tự động hóa. Agent sẽ trinh sát trước, đưa ra gợi ý, xác nhận với người dùng rồi tiến hành ghi cấu hình.

---

## Quy trình thực hiện (Process)

### 1. Trinh sát (Explore)

Quét dự án hiện tại để nhận diện trạng thái ban đầu:
- Chạy lệnh `git remote get-url origin` hoặc `git remote -v` để nhận diện repo có sử dụng GitHub, GitLab hay không.
- Đọc file `.md/workspace_context.yaml` tại thư mục gốc để xem đã có cấu hình `archetype` ([ADR 0041](../../../docs/adr/0041-hub-spoke-ecosystem-taxonomy-and-archetypes.md)), `issue_tracker` hoặc các cấu hình khác chưa.
- Kiểm tra sự tồn tại của file hiến pháp `.agents/AGENTS.md` hoặc `AGENTS.md`.
- Kiểm tra sự tồn tại của `CONTEXT.md` / `CONTEXT-MAP.md` ở thư mục gốc hoặc `.md/knowledge/`.
- Kiểm tra sự tồn tại của thư mục cấu hình đích `.md/knowledge/agents/`.
- **Kiểm tra Kỹ năng Triage (Multi-tier Detection)**: Quét qua 3 cấp: (1) Thư mục `.agents/skills/ccba-triage/` hoặc `.agents/skills/triage/`, (2) Đăng ký trong `catalog.yaml`, (3) Danh sách Kỹ năng khả dụng trong ngữ cảnh. Thiết lập cờ `triage_installed = true` nếu tìm thấy; ngược lại `triage_installed = false`.
- **Kiểm tra Tín hiệu Monorepo (Monorepo Inference)**: Kiểm tra file `pnpm-workspace.yaml`, trường `workspaces` trong `package.json`, hoặc sự tồn tại của `CONTEXT-MAP.md`. Thiết lập cờ `is_monorepo = true` nếu phát hiện; ngược lại `is_monorepo = false`.
- **Kiểm tra Môi trường Monorepo & Liên kết Hub**: Quét kiểm tra xem gói `packages/ccba-harness` đã được cài đặt dưới dạng editable (`pip list` hoặc import) chưa, và xác định liên kết Hub (`git remote get-url origin` hoặc đường dẫn Hub cục bộ) để kích hoạt cơ chế đồng bộ và bảo đảm năng lực kiểm định thể chế.

### 2. Gợi ý cấu hình & Phỏng vấn (Present findings and ask)

Tóm tắt kết quả trinh sát và đưa ra cấu hình đề xuất cho người dùng (luôn áp dụng **Recommended-First UX** — đưa câu trả lời đề xuất tốt nhất lên Lựa chọn 1 để người dùng xác nhận bằng Phím Enter hoặc `1`):

- **Nếu đã có cấu hình trong `workspace_context.yaml`**: Hiển thị cấu hình hiện tại và đề xuất dùng tiếp cấu hình này (bỏ qua phỏng vấn từng bước).
- **Nếu chưa có cấu hình**: Thực hiện phỏng vấn tương tác:

  **Câu A — Issue tracker**:
  > *Lựa chọn 1 (Recommended)*: Đề xuất mặc định thông minh dựa trên `archetype` ([ADR 0041](../../../docs/adr/0041-hub-spoke-ecosystem-taxonomy-and-archetypes.md)), `sub_type` ([ADR 0046](../../../docs/adr/0046-personal-sandbox-lifecycle-and-charter-2026-alignment.md)) và `git remote`:
  > - Nếu `archetype == "project_delivery"` hoặc dự án không có remote Git: **Local markdown** (Lưu dưới `.md/knowledge/issues/`).
  > - Nếu `archetype == "enterprise_governance"`: **Local markdown** (Lưu dưới `.md/knowledge/issues/` kết hợp IDOP Governance).
  > - Nếu `archetype == "knowledge_corpus"`: **GitHub Issues** (nếu có remote Git) hoặc **Local markdown** (nếu offline).
  > - Nếu `archetype == "specialized_extension"`:
  >   * Spoke Cá Nhân (`sub_type: personal_sandbox` - ADR 0046): Mặc định **Local markdown** (`.md/knowledge/issues/` hoặc liên kết `idop_tasks.active_pgv_list`), tránh tạo issue công khai cho nghiên cứu cá nhân.
  >   * Spoke Tiện ích / R&D (`tooling_plugin`, `research_lab`) có remote GitHub: **GitHub Issues** (yêu cầu `gh` CLI).
  > - Nếu `archetype == "platform_hub"` và có remote GitHub: **GitHub Issues** (yêu cầu `gh` CLI).
  > - Nếu remote chứa `gitlab.com`: **GitLab Issues** (yêu cầu `glab` CLI).
  - **Local markdown** — Lưu issue thành các file md dưới `.md/knowledge/issues/` (phù hợp dự án tư vấn hiện trường, sandbox cá nhân, chạy offline hoặc solo).
  - **GitHub** — Sử dụng GitHub Issues (yêu cầu `gh` CLI).
  - **GitLab** — Sử dụng GitLab Issues (yêu cầu `glab` CLI).
  - **Khác** — Nhận mô tả quy trình dạng văn bản tự do từ người dùng.
  
  Nếu chọn GitHub/GitLab, hỏi thêm:
  - *Xem PR như yêu cầu tính năng?* (yes / no - Mặc định: **no**).

  **Câu B — Nhãn Triage (Smart Skipping)**:
  > ⚡ **Smart Skipping Rule**: Nếu bước Trinh sát xác định `triage_installed = false`, **BỎ QUA TOÀN BỘ CÂU B NÀY** và thông báo ngầm: *"Đã tự động bỏ qua cấu hình Nhãn Triage do dự án không sử dụng kỹ năng Triage."*

  Nếu `triage_installed = true`, thực hiện phỏng vấn cấu hình ánh xạ cho 5 vai trò nhãn triage:
  - Lựa chọn 1 (Recommended): **Giữ nguyên 5 nhãn mặc định** (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`).
  - Lựa chọn 2: Nhận ghi đè nhãn từ người dùng.

  **Câu C — Cấu trúc tài liệu miền (Monorepo Inference)**:
  > ⚡ **Monorepo Inference Rule**: Nếu bước Trinh sát xác định `is_monorepo = false`, **TỰ ĐỘNG CHỐT Single-context** (`CONTEXT.md` duy nhất tại root) mà không bắt người dùng phỏng vấn thủ công.

  Chỉ khi `is_monorepo = true`, mới hỏi phỏng vấn chọn cấu trúc:
  - **Single-context** (Recommended) — 1 file `CONTEXT.md` và `docs/adr/` ở root.
  - **Multi-context** — Có file `CONTEXT-MAP.md` dẫn tới nhiều folder con chứa `CONTEXT.md` riêng.

  **Câu D — Thể chế Quản trị Kỹ năng (Skills Governance)**:
  > *Lựa chọn 1 (Recommended)*: **Kiến trúc 3 tầng chuẩn hóa ADR-0057** (`skills_governance: {architecture: "3-tier", enforce_gpi: true}`). Tự động kích hoạt kiểm định Cổng 0 (Determinism), Cổng 1 (Orchestration) và chặn Standalone Skills nếu $GPI < 12.0$.
  > - Lựa chọn 2: Tùy chỉnh chế độ quản trị (chỉ áp dụng cho Spoke cá nhân hoặc sandbox nghiên cứu).

### 3. Xác nhận (Confirm)

Hiển thị cho người dùng xem bản nháp của:
- Khối cấu hình `## Agent skills` sẽ được ghi vào file `.agents/AGENTS.md` (hoặc `AGENTS.md` ở root). (Bao gồm tiểu mục `### Triage labels` chỉ khi `triage_installed = true`, và tiểu mục `### Skills Governance`).
- Nội dung chi tiết của các file sẽ được tạo ra tại `.md/knowledge/agents/`:
  - `issue_tracker.md`
  - `triage_labels.md` (chỉ khi `triage_installed = true`)
  - `domain.md`

### 4. Ghi cấu hình (Write)

**Bước A: Cập nhật Hiến pháp**:
- Xác định file ghi hiến pháp: Ưu tiên `.agents/AGENTS.md`, sau đó đến `AGENTS.md` ở root.
- Cập nhật (hoặc thêm mới) block `## Agent skills` vào file đó:
  ```markdown
  ## Agent skills

  ### Issue tracker

  [Tóm tắt ngắn gọn tracker và trạng thái PR]. Xem `.md/knowledge/agents/issue_tracker.md`.

  ### Triage labels (chỉ có khi triage_installed = true)

  [Tóm tắt ngắn gọn nhãn triage]. Xem `.md/knowledge/agents/triage_labels.md`.

  ### Domain docs

  [Tóm tắt ngắn gọn bố cục]. Xem `.md/knowledge/agents/domain.md`.

  ### Skills Governance

  Tuân thủ Khung Quyết Định Hai Giai Đoạn (ADR-0057 & RES-2026-ARCH-001 v1.2) với kiến trúc 3 tầng (Tier 1: Package Function, Tier 2A: Progressive Reference, Tier 2B: Standalone Kernel Skill, Tier 3: Composite Orchestrator). Mọi kỹ năng độc lập bắt buộc đạt $GPI \ge 12.0$ và vượt qua `python scripts/validate_skills.py --file <path> --enforce-gpi`.
  ```

**Bước B: Cập nhật `workspace_context.yaml`**:
- Ghi nhận hoặc cập nhật trường `project.issue_tracker` trong file `.md/workspace_context.yaml` (ví dụ: `github`, `gitlab` hoặc `local_markdown`).
- Bổ sung chiều thiết lập "Skills Governance" và tự động ghi cấu hình `skills_governance: {architecture: "3-tier", enforce_gpi: true}` vào `.md/workspace_context.yaml`.

**Bước C: Tạo các file chỉ dẫn chi tiết**:
Tạo thư mục `.md/knowledge/agents/` (nếu chưa có) và ghi các file cấu hình chi tiết:
- Hướng dẫn Issue Tracker: Lấy từ `issue-tracker-github.md`, `issue-tracker-gitlab.md`, hoặc `issue-tracker-local.md`.
- Hướng dẫn nhãn Triage: Lấy từ `triage-labels.md` (chỉ tạo khi `triage_installed = true`).
- Hướng dẫn Domain: Lấy từ `domain.md`.

### 5. Hoàn tất (Done)

Thông báo cho người dùng việc thiết lập đã hoàn thành. Nhắc nhở người dùng rằng họ có thể chỉnh sửa trực tiếp các file trong `.md/knowledge/agents/` sau này để thay đổi cấu hình, không cần chạy lại lệnh setup trừ khi muốn thay đổi hoàn toàn Issue Tracker.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/pre_commit_setup.md` | Hướng dẫn cấu hình pre-commit linter hooks và bảo vệ mã nguồn |
| `references/ts_deep_modules.md` | Hướng dẫn thiết lập dependency-cruiser và kiểm soát ranh giới module sâu TypeScript |

