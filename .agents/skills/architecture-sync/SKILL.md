---
name: architecture-sync
description: Đồng bộ hóa toàn bộ tài liệu kiến trúc sau khi refactor codebase — bao
  phủ 4 tầng tài liệu nhạy cảm.
disable-model-invocation: true
bundle: _core
triggers:
- architecture-sync
- đồng bộ hiến pháp
- đồng bộ kiến trúc
- architecture
- sync
- cập nhật tài liệu kiến trúc
- refactor docs
---
# Constitution Sync: Architecture Synchronizer

Đồng bộ hóa toàn bộ tài liệu kiến trúc và hướng dẫn vận hành của hệ thống sau khi refactor cấu trúc thư mục hoặc thay đổi thiết kế module.

> **Phạm vi**: Skill này quản lý **4 tầng tài liệu nhạy cảm kiến trúc** — từ hiến pháp cốt lõi đến tài liệu auto-generated. Mỗi tầng có mức độ ưu tiên kiểm tra khác nhau.

---

## Registry Tài liệu Nhạy cảm Kiến trúc

### Tier 1 — BẮT BUỘC đồng bộ mọi lần refactor

| File | Nội dung nhạy cảm |
|------|--------------------|
| `AGENTS.md` | Hiến pháp rào chắn, quy tắc SDLC |
| `README.md` | Sơ đồ cây ASCII, bảng services, badge thống kê |
| `PLATFORM.md` | Sơ đồ cây chi tiết nhất, bảng 7 packages, phân loại skills/workflows, hướng dẫn tạo mới |
| `CONTEXT.md` | Ubiquitous Language — thuật ngữ chuẩn hóa chứa đường dẫn cụ thể |
| `CONTRIBUTING.md` | Hướng dẫn cài đặt, bảng Agent Workflows, Dev Environment commands |
| `.github/copilot-instructions.md` | Model routing cho Copilot — tương đương GEMINI.md |
| `GEMINI.md` | Model routing cho Gemini (nếu có) |
| `.github/workflows/ci.yml` | Đường dẫn cài 7 packages, script commands |
| `catalog.yaml` | Registry trung tâm — skill_path, workflow_path, triggers |
| `pyproject.toml` | CLI entry points, build targets, workspace members |

### Tier 2 — Kiểm tra khi thay đổi scripts, packages, hoặc workflows

| File | Nội dung nhạy cảm |
|------|--------------------|
| `install.ps1` | Đường dẫn cài đặt package |
| `.env.example` | Schema biến môi trường |
| `.pre-commit-config.yaml` | Hook scripts, đường dẫn cấu hình |
| `PROJECT.md` | Active project code layout, interface contracts |
| Skills chứa CLI: `platform-loader`, `ai-gateway-sdk`, `docs-validator`, `docs_manager`, `setup-pre-commit`, `eval-gate`, `xu-ly-van-phong` | Đường dẫn `scripts/`, `templates/`, import paths |
| Workflows chứa paths: `ccba-init-spoke`, `ccba-issue-to-hub`, `ccba-contribute-to-hub`, `ccba-propose-to-hub`, `ccba-update-spoke`, `ccba-build-skill`, `ccba-release-feature` | Đường dẫn Hub/Spoke, script commands |
| Rules chứa paths: `naming_conventions`, `release_gate` | Cấu trúc `.md/`, đường dẫn scripts |

### Tier 3 — Kiểm tra khi có thay đổi kiến trúc lớn (rename module, xóa package)

- `docs/adr/` — Architecture Decision Records (đặc biệt: `0009`, `0010`, `0018`, `0021`)
- `.agents/proposals/` — Đề xuất tích hợp lịch sử
- `.md/knowledge/` — Research docs, codebase summaries, specs

### Tier 4 — Tự động re-generate (không sửa thủ công)

- `skills_compiled.md` — Compiled dump toàn bộ skills
- `workflows_compiled.md` — Compiled dump toàn bộ workflows
- `session_learnings.md` — Tri thức tích lũy

---

## Quy trình thực hiện

### Bước 1: Khảo sát Codebase (Legwork)

1. Quét cây thư mục bằng `list_dir` để ghi nhận cấu trúc thực tế hiện tại.
2. Xác định phạm vi thay đổi: thêm/bớt/rename thư mục, module, package, script nào.
3. Thu thập số liệu thống kê thực tế:
   - Đếm thư mục con trong `.agents/skills/` → số lượng skills thực tế
   - Đếm file `.md` trong `.agents/workflows/` → số lượng workflows thực tế
   - Đếm thư mục con trong `packages/` → số lượng packages thực tế
   - Đếm entries `skill_path` trong `catalog.yaml` → số lượng catalog entries

### Bước 2: Đối soát Số liệu Thống kê (Statistics Drift Detection)

So sánh số liệu thực tế (Bước 1) với các con số hardcoded trong tài liệu. Các con số cần kiểm tra:
- `"N skills"` — xuất hiện trong: `README.md`, `PLATFORM.md`, `CONTEXT.md`, `copilot-instructions.md`
- `"N workflows"` — xuất hiện trong: `README.md`, `PLATFORM.md`
- `"N packages"` — xuất hiện trong: `PLATFORM.md`, `CONTRIBUTING.md`
- `"N models"` — xuất hiện trong: `README.md`, `PLATFORM.md`, `ai-gateway-sdk/SKILL.md`

Nếu phát hiện sai lệch → ghi nhận và cập nhật ở Bước 3.

### Bước 3: Đồng bộ hóa Tài liệu (Tiered Sync)

**Tier 1 (bắt buộc):**
1. **`AGENTS.md`**: Cập nhật quy tắc, schemas nếu có thay đổi quy trình.
2. **`README.md`** + **`PLATFORM.md`**: Cập nhật sơ đồ cây ASCII, bảng services, số liệu thống kê.
3. **`CONTEXT.md`**: Cập nhật thuật ngữ nếu có khái niệm mới hoặc đường dẫn thay đổi.
4. **`CONTRIBUTING.md`**: Cập nhật hướng dẫn cài đặt và bảng workflows.
5. **`copilot-instructions.md`**: Cập nhật bảng packages, import paths, tham chiếu chéo.
6. **`ci.yml`**: Cập nhật đường dẫn packages, script commands.
7. **`catalog.yaml`**: Cập nhật `skill_path` / `workflow_path` nếu rename.
8. **`pyproject.toml`**: Cập nhật entry points, workspace members nếu thêm/bớt package.

**Tier 2 (khi ảnh hưởng):**
- Rà soát các Skills và Workflows trong registry Tier 2 ở trên.
- Tìm kiếm đường dẫn cũ bằng `grep_search` trên `.agents/skills/` và `.agents/workflows/`.

**Tier 3 (khi thay đổi lớn):**
- Chỉ cập nhật ADRs nếu quyết định kiến trúc cũ bị thay thế → tạo ADR mới thay vì sửa ADR cũ.

**Tier 4 (re-generate):**
- Chạy lại script compile nếu có thay đổi nội dung skills/workflows.

### Bước 4: Kiểm định Gác cổng (Linter Gate)

Chạy linter tài liệu tĩnh trên các file có thay đổi:
```bash
python scripts/validate_docs.py . --changed
```
- Nếu phát hiện lỗi, bắt buộc phải sửa đổi hoàn chỉnh trước khi lưu trữ.

### Bước 5: Lưu trữ Knowledge Item (KI)

- Tạo artifact tóm tắt (ví dụ: `walkthrough.md`) ghi nhận các thay đổi kiến trúc chính để chuyển tiếp tri thức sang phiên làm việc sau.

---

## Tiêu chí hoàn thành (Completion Criteria)

- `[ ]` Tất cả file Tier 1 được cập nhật khớp 100% cấu trúc codebase mới.
- `[ ]` Số liệu thống kê (skill count, workflow count, package count) nhất quán trên tất cả các file.
- `[ ]` Các file Tier 2 bị ảnh hưởng đã được rà soát và cập nhật.
- `[ ]` Lệnh kiểm định `validate_docs.py` chạy qua và không phát sinh lỗi.
- `[ ]` Artifact tóm tắt kiến trúc được tạo thành công.
