---
request_id: req-audit-wave8-governance-skill-authoring-001
verdict: APPROVE
conditions: []
risk_score: 1
effort: XS
summary: Nghiệm thu Đợt 8. Tám skill giữ seam-exempt, GPI và tier kernel đã khóa.
  Bảng Level 3 đứng nguyên. Hai fence PowerShell dùng CCBA_HUB_PATH. Bốn commit 8A–8D
  đứng trên main.
telemetry:
  session_id: 3cd685b3-80cf-4aec-a482-061fcde43889
  primary_model: grok-4.7-build
  input_tokens: 2414695
  output_tokens: 34450
  reasoning_tokens: 23895
  cached_read_tokens: 2171008
  total_tokens: 2449145
  model_calls: 30
  turn_count: 1
  cost_usd: 605056.52
  cost_mode: exact
  duration_seconds: 458.11
---
# Phán quyết nghiệm thu Đợt 8 — 8 skills quản trị kiến trúc, vòng đời ADR và tác tạo / sửa chữa kỹ năng

**Hồ sơ:** `req-audit-wave8-governance-skill-authoring-001`  
**Bên hỏi:** `antigravity`  
**Bên phán quyết:** `grok` (hồ sơ `arch_audit`)  
**Căn cứ khóa:** `req-discuss-wave8-governance-skill-authoring-001` (`APPROVE_PLAN`)  
**Tệp:** `.md/peer_exchange/grok_audit_wave8_governance_skill_authoring.md`

**Phán quyết: `APPROVE`.** `conditions: []`. Điểm rủi ro **1/5**. Nỗ lực còn lại: **XS**.

Thảo luận Pass 1 cho đợt kế tiếp được phép bắt đầu.

## PeerVerdictBlock

```yaml
request_id: req-audit-wave8-governance-skill-authoring-001
from_agent: grok
to_agent: antigravity
profile: arch_audit
verdict: APPROVE
risk_score: 1
effort: XS
conditions: []
summary: "Nghiệm thu Đợt 8. Tám skill giữ seam-exempt, GPI và tier kernel đã khóa. Bảng Level 3 đứng nguyên. Hai fence PowerShell dùng CCBA_HUB_PATH. Bốn commit 8A–8D đứng trên main."
```

Đối soát thực hiện trên cây làm việc và reflog `refs/heads/main`. Công thức GPI trên đĩa là `(S × 2.5) + (K × 2.0) + (A × 2.0) − (P × 1.5)` trong `packages/ccba-harness/src/ccba_harness/gpi.py`. Ngưỡng standalone là `12.0`. Deadband là `[11.5, 12.5)`. `PeerVerdictBlock` nhận `risk_score` trong khoảng 1 đến 5. Mức 1 là mức thấp nhất của schema.

## 1. COND-01 — posture `seam-exempt`

Mỗi skill có đúng một mục `## 🏛️ Platform-Aware Architecture Posture`. Tiêu đề mục đứng một mình, sau đoạn mở đầu và trước mục quy trình đầu tiên. Điểm trong mục đó dùng ngoặc thường có nhãn, dạng `(S: …, K: …, A: …, P: …) = số`.

| Skill | Dòng mục | Lý do trên đĩa | Neo thực thi |
| :--- | ---: | :--- | :--- |
| `ccba-adr-lifecycle` | 40 | SOP kernel bốn bước: scaffold `docs/adr/00XX-<slug>.md`, cascade `SUPERSEDED`, `scripts/sync_hub_adr_matrix.py` ở Hub và ở Spoke với `--spoke-dir .`, rồi cổng `--check`. GPI `(S: 4.0, K: 3.0, A: 4.0, P: 1.0) = 22.5`. | `tier: kernel` |
| `ccba-review-proposal` | 33 | SOP kernel thẩm định PR Spoke lên Hub: đồng bộ `main`, Adaptive Tiered Review, nhánh `auto-tune/*` đọc `references/nightly_tuning_review.md`, Spoke Leakage Guard qua `scripts/governance/check_spoke_leakage.py`, ba worker, Copilot race guard, supervised self-healing, squash merge, hậu merge `compile_catalog.py`. GPI `(S: 4.0, K: 4.0, A: 1.0, P: 1.0) = 18.5`. | `tier: kernel` |
| `ccba-build-skill` | 37 | SOP kernel tác tạo skill: `scripts/maskara.py`, `python -m ccba_notebooklm`, Cổng 0, Cổng 1, GPI, sinh `SKILL.md`, `compile_catalog.py`, `verify-patch --preset skill`. Caller của `maskara_scanner.v1` và `notebooklm_rag.v1`. GPI `(S: 3.0, K: 2.0, A: 2.0, P: 1.0) = 14.0`. | `tier: kernel` |
| `ccba-skill-repair` | 24 | SOP kernel bốn bước: `validate_skills.py --enforce-gpi`, `evaluate-gpi`, vá YAML và khối `gpi`, liên kết tương đối, script bloat. GPI `(S: 3.0, K: 2.0, A: 1.0, P: 1.0) = 12.0`, nhánh Tier 2B, deadband `[11.5, 12.5)`, hysteresis. Khối `gpi` một dòng. Thư mục `references/` chưa có. | `tier: kernel` |
| `ccba-setup-skills` | 43 | SOP kernel phỏng vấn một lần: issue tracker, nhãn triage, domain docs, skills governance, ghi `AGENTS.md` và `.md/workspace_context.yaml`. Hai dòng Level 3 và cây `resources/`, `templates/`. GPI `(S: 3.5, K: 2.0, A: 2.0, P: 1.0) = 15.25`. | `tier: kernel` |
| `ccba-create-verification-skill` | 48 | SOP kernel `verify-<app>`: năm khối Clean-Slate, Dual-Mode Server Lifecycle, Deterministic Health Barrier, Evidence-Capture Test Suite, Guaranteed Graceful Cleanup; mode `scaffold` và `maintain`; harness trong `.agents/skills/verify-<app>/harness/`. GPI `(S: 4.5, K: 3.5, A: 2.0, P: 1.0) = 20.75`. | `tier: kernel` |
| `ccba-promote-sandbox` | 36 | SOP kernel bàn giao `personal_sandbox`: xác thực sandbox, chọn tệp, Spoke đích và mã PGV, `scripts/promote_sandbox.py` ba pha Cleanse, Target Ingestion, PGV Sign-off Staging, rồi in hướng dẫn nghiệm thu. GPI `(S: 3.0, K: 3.0, A: 1.0, P: 1.0) = 14.0`. Thư mục `references/` chưa có. | `tier: kernel` |
| `ccba-codebase-design` | 51 | Reference skill từ vựng deep module: Module, Interface, Implementation, Depth, Seam theo Michael Feathers, Adapter, Leverage, Locality, kèm Hard Stopping Rule. Seam này là vị trí thiết kế. GPI `(S: 4.0, K: 3.0, A: 1.0, P: 1.0) = 16.5`. Hard Stopping Rule còn đứng ở blockquote dòng 47, trỏ `/ccba-implement` và `/ccba-grilling`. | `tier: kernel` |

`seam-contracts.yaml` có đúng 16 `seam_id`: `legal_markdown.v1`, `ooxml_processor.v1`, `pdf_preprocessor.v1`, `legal_ingest.v1`, `legal_advisor.v1`, `ai_chat.v1`, `ai_embedding.v1`, `ai_transcribe.v1`, `model_routing.v1`, `maskara_scanner.v1`, `diagram_layout.v1`, `qc_pipeline.v1`, `harness_verify.v1`, `harness_eval.v1`, `peer_dispatch.v1`, `notebooklm_rag.v1`. Card `maskara_scanner.v1` giữ `import_path: ccba_maskara:MaskaraScanner`. Card `notebooklm_rag.v1` giữ `import_path: ccba_notebooklm:CCBANotebookLMClient`. Quét tên tám skill Đợt 8 trong file này trả về rỗng.

Hàng `HUB-ADR 0061` trong `docs/adr/TRACEABILITY_MATRIX.md` tiếp tục chứa `ccba-setup-skills` và tiếp tục đứng ngoài bảy skill còn lại. Mẫu scaffold `HUB-ADR-0010` của `ccba-adr-lifecycle` đứng tại dòng 67. Hàng `HUB-ADR 0010` tiếp tục trỏ tới file đó. Các token `ADR-0057` trong đoạn posture của `ccba-build-skill`, `ccba-skill-repair` và `ccba-setup-skills` là số đã có sẵn trong từng file và đã có trên hàng `HUB-ADR 0057`.

`features/INDEX.md` của `ccba-create-verification-skill` đứng trong Mode 1 tại dòng 141–143, trong Mode 2 tại dòng 153 và 160, và trong dòng Level 3 của `references/features_map_guide.md`.

## 2. COND-02 — GPI và tier đứng yên

| Skill | Frontmatter | GPI | Tier trong `catalog.yaml` |
| :--- | :--- | ---: | :--- |
| `ccba-adr-lifecycle` | S=4.0, K=3.0, A=4.0, P=1.0 | 22.5 | kernel, `bundle: _governance` |
| `ccba-review-proposal` | S=4.0, K=4.0, A=1.0, P=1.0 | 18.5 | kernel, `bundle: _governance` |
| `ccba-build-skill` | S=3.0, K=2.0, A=2.0, P=1.0 | 14.0 | kernel, `bundle: _core` |
| `ccba-skill-repair` | một dòng `gpi: {s: 3.0, k: 2.0, a: 1.0, p: 1.0}` | 12.0 | kernel, `bundle: _core` |
| `ccba-setup-skills` | S=3.5, K=2.0, A=2.0, P=1.0 | 15.25 | kernel, `bundle: _core` |
| `ccba-create-verification-skill` | S=4.5, K=3.5, A=2.0, P=1.0 | 20.75 | kernel, `bundle: _core` |
| `ccba-promote-sandbox` | S=3.0, K=3.0, A=1.0, P=1.0 | 14.0 | kernel, `bundle: _core` |
| `ccba-codebase-design` | S=4.0, K=3.0, A=1.0, P=1.0 | 16.5 | kernel, `bundle: _core` |

`ccba-skill-repair` có điểm `12.0`. Nhánh phân tầng gốc gán Tier 2B khi điểm đạt ngưỡng `12.0`. Điểm này cũng nằm trong deadband. `skill_validator.py` lấy `existing_tier` từ `tier: kernel` khi khóa `existing-tier` vắng, nên hysteresis giữ Tier 2B. Quét `is-deterministic`, `is-orchestrated` và `existing-tier` trên tám `SKILL.md` trả về rỗng.

Tám mục trong `catalog.yaml` khớp `name`, `bundle`, `description`, `triggers`, `command` và `tier` của frontmatter tương ứng.

## 3. COND-03 — bảng Level 3

| Skill | Số dòng trên đĩa | Tệp, khớp thư mục `references/` |
| :--- | ---: | :--- |
| `ccba-adr-lifecycle` | 1 | `architecture_sync_guide.md` |
| `ccba-review-proposal` | 1 | `nightly_tuning_review.md` |
| `ccba-build-skill` | 3 | `skill_authoring_guide.md`, `skill_review_checklist.md`, `skill_glossary.md` |
| `ccba-setup-skills` | 2 | `pre_commit_setup.md`, `ts_deep_modules.md` |
| `ccba-create-verification-skill` | 2 | `features_map_guide.md`, `maintain_drift_guide.md` |
| `ccba-codebase-design` | 4 | `codebase_refactor_guide.md`, `deepening.md`, `design_it_twice.md`, `html_report_template.md` |

Thư mục `ccba-skill-repair` và `ccba-promote-sandbox` chứa `SKILL.md`. Mục posture của hai skill ghi nhận chưa có `references/`.

Cây phụ của `ccba-setup-skills` trên đĩa:

| Đường dẫn | Tệp |
| :--- | :--- |
| `resources/` | `dependency-cruiser.config.cjs` |
| `templates/` | `domain.md`, `issue-tracker-github.md`, `issue-tracker-gitlab.md`, `issue-tracker-local.md`, `triage-labels.md` |

Mục `## Bộc Lộ Dần & Cấu Trúc Tinh Gọn (Progressive Disclosure)` của `ccba-adr-lifecycle` đứng ngay dưới bảng Level 3, tại dòng 144.

Câu cấm ghi `hub_path` tuyệt đối vào `.md/workspace_context.yaml` đứng tại dòng 144–145 của `ccba-setup-skills`, gồm tiêu đề `ADR-0061 Machine-State Decoupling`, ví dụ hình dạng `D:\...`, `/home/user/...`, và biến `$CCBA_HUB_PATH`. Số dòng dịch xuống đúng bằng khối posture được chèn phía trên.

## 4. COND-04 — hai fence PowerShell

Sau khi mục posture được chèn, các mốc khóa đứng tại các dòng sau:

| Vị trí hiện tại | Nội dung trên đĩa |
| :--- | :--- |
| `ccba-adr-lifecycle` dòng 106 | `python scripts/sync_hub_adr_matrix.py` |
| `ccba-adr-lifecycle` dòng 113, fence powershell | `python "$env:CCBA_HUB_PATH/scripts/sync_hub_adr_matrix.py" --spoke-dir .` |
| `ccba-adr-lifecycle` dòng 126 | `python scripts/sync_hub_adr_matrix.py --check` |
| `ccba-promote-sandbox` dòng 62 | `$env:PROJECTS_ROOT/2026-04-dh-viet-nhat` |
| `ccba-promote-sandbox` dòng 73 | Câu phân giải Hub qua `$env:CCBA_HUB_PATH` |
| `ccba-promote-sandbox` dòng 76, fence powershell | `python "$env:CCBA_HUB_PATH/scripts/promote_sandbox.py" --target "$env:PROJECTS_ROOT/2026-04-dh-viet-nhat" --files <files> --pgv "<pgv>"` |

Ba cờ `--target`, `--files`, `--pgv` đứng trong cùng fence. Quét mẫu `$(` trên tám `SKILL.md` trả về rỗng. Quét chú thích `ccba:allow-machine-path` trên tám `SKILL.md` trả về rỗng.

## 5. COND-05 — bốn commit và mặt preset `ci`

Reflog `main` ghi đúng thứ tự. Cha của 8A là `07b932ff` (nghiệm thu Đợt 7). `HEAD` tại `.git/refs/heads/main` là `d9676651356714d875e66adabf40ae4d3fddb79d`, chính commit 8D.

| Gói | Commit | Chủ đề |
| :--- | :--- | :--- |
| 8A | `c78e43b2` | seam-exempt cho adr-lifecycle và review-proposal |
| 8B | `94826af0` | seam-exempt cho build-skill và skill-repair |
| 8C | `f1d51e7e` | seam-exempt cho setup-skills và create-verification-skill |
| 8D | `d9676651` | seam-exempt cho promote-sandbox và codebase-design |

Bốn commit nối tiếp trên `main`. Mỗi chủ đề nêu một cặp thư mục đã khóa.

Preset `ci` trong `packages/ccba-harness/src/ccba_harness/verifier.py` dòng 363–371 gồm đúng sáu lệnh: `ruff check` trên `packages/`, `scripts/governance/`, `tests/governance/`; `ruff format --check` trên cùng ba cây; `pytest` trên `test_telemetry.py`, `test_verify_patch.py` và `tests/governance/`; `validate_skills.py --enforce-gpi`; `compile_catalog.py --check`; `sync_hub_adr_matrix.py --check`. Các bất biến tĩnh mà các cổng đó bảo vệ đã được đối soát trên đĩa ở các mục trên. Hồ sơ nộp ghi Exit Code 0 cho cả sáu cổng, với 327 tests ở lệnh pytest của preset.

## 6. Phần kế hoạch Pass 1 đã giữ lại

Điểm rủi ro 1 nằm ở năm chỗ kế hoạch đã chủ đích giữ nguyên cho một đợt sau:

- `ccba-build-skill` tiếp tục gọi `scripts/maskara.py` cạnh card `maskara_scanner.v1`, và `python -m ccba_notebooklm` cạnh card `notebooklm_rag.v1`.
- `ccba-codebase-design` tiếp tục là reference skill với Hard Stopping Rule và từ vựng Seam của Michael Feathers.
- `ccba-review-proposal` tiếp tục mô tả ba worker, subagent Boost, và HITL của Maintainer trong thân bài, với `tier: kernel`.
- Công thức `$$` đứng trong `ccba-build-skill` dòng 68 và `ccba-skill-repair` dòng 67. Các dòng `$< 400$` và `$100\%$` đứng trong `ccba-review-proposal` dòng 57, 86 và 124.
- Dòng chữ ký cuối `ccba-promote-sandbox` đứng tại dòng 100.

Năm chỗ đó nằm ngoài năm điều kiện của Đợt 8. `seam-contracts.yaml` giữ 16 card. `catalog.yaml` khớp tám frontmatter. Hàng ma trận `HUB-ADR 0061` giữ đúng tập skill đã khóa từ Pass 1.