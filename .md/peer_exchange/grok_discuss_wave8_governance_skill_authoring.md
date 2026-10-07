---
request_id: req-discuss-wave8-governance-skill-authoring-001
verdict: APPROVE_PLAN
conditions:
- id: COND-01
  description: Đã khóa. Tám skill, mỗi skill một mục "## 🏛️ Platform-Aware Architecture
    Posture" đặt một lần ngay sau H1. Tiêu đề mục không kèm số ADR. seam-exempt cho
    cả tám. seam-contracts.yaml giữ 16 seam_id. packages/ đứng ngoài đợt. Lý do posture
    lấy từ thân bài trên đĩa, theo bảng mục 2. ccba-build-skill là caller của maskara_scanner.v1
    và notebooklm_rag.v1. Seam trong ccba-codebase-design là từ vựng Michael Feathers.
    Tập token ADR của từng SKILL.md đứng yên, gồm mẫu HUB-ADR-0010 trong scaffold
    của ccba-adr-lifecycle.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-02
  description: 'Đã khóa. Frontmatter tám file đứng nguyên từng byte: name, tier, bundle,
    command, triggers, description, metadata, gpi, cờ disable-model-invocation, applies_to,
    conforms_to, layer, scope. Tám skill giữ tier kernel. Điểm giữ nguyên: adr-lifecycle
    22.5, review-proposal 18.5, build-skill 14.0, skill-repair 12.0, setup-skills
    15.25, create-verification-skill 20.75, promote-sandbox 14.0, codebase-design
    16.5. skill-repair giữ khối gpi một dòng. Điểm 12.0 đi nhánh Tier 2B và nằm trong
    deadband [11.5, 12.5). Cờ is-deterministic và is-orchestrated tiếp tục vắng.'
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-03
  description: Đã khóa. Bảng Level 3 đứng nguyên với đúng tên tệp và đúng thứ tự trên
    đĩa. adr-lifecycle 1 dòng architecture_sync_guide.md. review-proposal 1 dòng nightly_tuning_review.md.
    build-skill 3 dòng skill_authoring_guide.md, skill_review_checklist.md, skill_glossary.md.
    setup-skills 2 dòng pre_commit_setup.md, ts_deep_modules.md. create-verification-skill
    2 dòng features_map_guide.md, maintain_drift_guide.md. codebase-design 4 dòng
    codebase_refactor_guide.md, deepening.md, design_it_twice.md, html_report_template.md.
    skill-repair và promote-sandbox chưa có references/. references/, resources/,
    templates/ đứng ngoài diff. Câu cấm hub_path của setup-skills tại dòng 139-140
    đứng nguyên.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-04
  description: 'Đã khóa. Fence powershell của ccba-adr-lifecycle dùng python "$env:CCBA_HUB_PATH/scripts/sync_hub_adr_matrix.py"
    --spoke-dir . Lệnh Hub tương đối python scripts/sync_hub_adr_matrix.py đứng nguyên.
    ccba-promote-sandbox: ví dụ đích là $env:PROJECTS_ROOT/2026-04-dh-viet-nhat. Fence
    powershell dùng python "$env:CCBA_HUB_PATH/scripts/promote_sandbox.py" --target
    "$env:PROJECTS_ROOT/2026-04-dh-viet-nhat" --files <files> --pgv "<pgv>". Câu mở
    đầu bước 3 phân giải Hub qua $env:CCBA_HUB_PATH. Mẫu $(...) đứng ngoài tám SKILL.md.
    Chú thích ccba:allow-machine-path đứng ngoài markdown.'
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-05
  description: Đã khóa. Bốn PR song song 8A-8D, bốn cặp thư mục tách biệt, mỗi PR
    chỉ sửa SKILL.md của cặp đó. Mỗi SKILL.md khóa bằng validate_skills.py --file
    --enforce-gpi, audit_skills_hygiene.py --file, và verify-patch --preset skill
    --target. Sau khi cả bốn PR có trên đĩa, chạy verify-patch --preset ci. catalog.yaml,
    seam-contracts.yaml, packages/ và docs/adr/ đứng ngoài bốn PR. Điểm trong đoạn
    posture viết dạng (S, K, A, P) = số.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
risk_score: 2
effort: M
summary: Kế hoạch Đợt 8 được phép bắt đầu. Tám skill nhận seam-exempt. GPI, tier và
  16 card seam đứng yên. Bốn PR song song. Lý do posture và bảng Level 3 khóa theo
  tệp đang có trên đĩa. Hai fence PowerShell dùng $env:CCBA_HUB_PATH. Tập token ADR
  của từng SKILL.md đứng yên để preset skill và preset ci giữ sync_hub_adr_matrix.py
  --check xanh.
telemetry:
  session_id: 50995bc7-e562-4622-994c-f10463203485
  primary_model: grok-4.7-build
  input_tokens: 1143546
  output_tokens: 31259
  reasoning_tokens: 22277
  cached_read_tokens: 1052288
  total_tokens: 1174805
  model_calls: 19
  turn_count: 1
  cost_usd: 304712.76
  cost_mode: exact
  duration_seconds: 405.1
---
## PeerVerdictBlock

```yaml
peer_verdict:
  request_id: "req-discuss-wave8-governance-skill-authoring-001"
  from_agent: "grok"
  to_agent: "antigravity"
  profile: "arch_audit"
  pass: 1
  verdict: APPROVE_PLAN
  risk_score: 2
  authorized_start: allowed
  dag:
    parallel: ["8A", "8B", "8C", "8D"]
    after: {}
  lock:
    - "python scripts/validate_skills.py --file <SKILL.md> --enforce-gpi"
    - "python scripts/governance/audit_skills_hygiene.py --file <skill_dir>"
    - "python -m ccba_harness verify-patch --preset skill --target <SKILL.md>"
  floor: "python -m ccba_harness verify-patch --preset ci"
  rationale: >
    Tám skill là SOP kernel. Hai skill bundle _governance, sáu skill bundle _core.
    seam-contracts.yaml có 16 seam_id. Tám GPI đều >= 12.0. ccba-skill-repair đạt 12.0
    và đi nhánh Tier 2B. Bốn PR không chung tệp. Lý do posture lấy từ thân bài trên đĩa.
    Hai fence PowerShell phân giải Hub qua $env:CCBA_HUB_PATH. Tập token ADR từng file
    đứng yên vì preset skill và preset ci đều gọi sync_hub_adr_matrix.py --check.
```

Phán quyết: **APPROVE_PLAN**. Bốn PR song song được phép bắt đầu. Điểm rủi ro **2/5**. Phần rủi ro còn lại nằm ở kỷ luật khi chép lý do posture, khi sửa hai fence PowerShell, và khi giữ nguyên tập token ADR để cổng parity vẫn xanh. Năm điều kiện `blocking: false` ở trên đã khóa các điểm đó.

Tệp: `.md/peer_exchange/grok_discuss_wave8_governance_skill_authoring.md`

## 1. Đối soát trên đĩa

`seam-contracts.yaml` có đúng 16 `seam_id`: `legal_markdown.v1`, `ooxml_processor.v1`, `pdf_preprocessor.v1`, `legal_ingest.v1`, `legal_advisor.v1`, `ai_chat.v1`, `ai_embedding.v1`, `ai_transcribe.v1`, `model_routing.v1`, `maskara_scanner.v1`, `diagram_layout.v1`, `qc_pipeline.v1`, `harness_verify.v1`, `harness_eval.v1`, `peer_dispatch.v1`, `notebooklm_rag.v1`.

Card `maskara_scanner.v1` có `import_path: ccba_maskara:MaskaraScanner`. Card `notebooklm_rag.v1` có `import_path: ccba_notebooklm:CCBANotebookLMClient`. Tên tám skill Đợt 8 vắng trong file này.

Công thức trong `packages/ccba-harness/src/ccba_harness/gpi.py` là `(S × 2.5) + (K × 2.0) + (A × 2.0) − (P × 1.5)`. `GPI_STANDALONE_THRESHOLD` là 12.0. Deadband là `[11.5, 12.5)`. Tám số trên đĩa khớp frontmatter:

| Skill | `(S, K, A, P)` | GPI | Tier trên đĩa | Bundle |
| :--- | :--- | :---: | :--- | :--- |
| `ccba-adr-lifecycle` | `(4.0, 3.0, 4.0, 1.0)` | 22.5 | `kernel` | `_governance` |
| `ccba-review-proposal` | `(4.0, 4.0, 1.0, 1.0)` | 18.5 | `kernel` | `_governance` |
| `ccba-build-skill` | `(3.0, 2.0, 2.0, 1.0)` | 14.0 | `kernel` | `_core` |
| `ccba-skill-repair` | `(3.0, 2.0, 1.0, 1.0)` | 12.0 | `kernel` | `_core` |
| `ccba-setup-skills` | `(3.5, 2.0, 2.0, 1.0)` | 15.25 | `kernel` | `_core` |
| `ccba-create-verification-skill` | `(4.5, 3.5, 2.0, 1.0)` | 20.75 | `kernel` | `_core` |
| `ccba-promote-sandbox` | `(3.0, 3.0, 1.0, 1.0)` | 14.0 | `kernel` | `_core` |
| `ccba-codebase-design` | `(4.0, 3.0, 1.0, 1.0)` | 16.5 | `kernel` | `_core` |

Nhánh phân tầng gốc gán Tier 2B khi điểm `>= 12.0`. Điểm 12.0 của `ccba-skill-repair` đã là Tier 2B trước hysteresis. Deadband cũng chứa 12.0. `SkillValidator` lấy `existing_tier` từ `tier: kernel` khi frontmatter không có khóa `existing-tier`. Khóa đó tiếp tục vắng. Hệ số nửa bước 3.5 và 4.5 là float hợp lệ. Khối `gpi` của `ccba-skill-repair` giữ dạng một dòng `gpi: {s: 3.0, k: 2.0, a: 1.0, p: 1.0}`. Bảy skill còn lại giữ khối `gpi` nhiều dòng.

Cổng 0 đọc cờ `is-deterministic`. Cổng 1 đọc cờ `is-orchestrated`. Tám file đang vắng cả hai cờ. Thân bài có subagent hoặc HITL vẫn giữ `tier: kernel`. `compile_catalog.py` kéo `name`, `bundle`, `description`, `triggers`, `command`, `tier`. Mục posture nằm trong thân Markdown. `catalog.yaml` giữ nguyên khi các khóa đó đứng yên.

Preset `skill` trong `verifier.py` chạy `validate_skills.py --enforce-gpi`, `compile_catalog.py --check`, và `sync_hub_adr_matrix.py --check`. Preset `ci` cũng chạy `sync_hub_adr_matrix.py --check`. Scanner ma trận khớp `HUB-ADR`, `HUB_ADR`, và `ADR` kèm số. Hàng `HUB-ADR 0061` hiện có `ccba-setup-skills` và chưa có bảy skill còn lại. `ccba-setup-skills` đã chứa token `ADR-0061` tại dòng 139. Bảy file kia chưa chứa token đó.

Vì `docs/adr/` đứng ngoài bốn PR, đoạn posture và tiêu đề mục giữ nguyên tập token ADR đang có trong từng file. Tiêu đề chung là `## 🏛️ Platform-Aware Architecture Posture`. Mẫu scaffold `HUB-ADR-0010` trong `ccba-adr-lifecycle` đứng nguyên vì hàng 0010 đang trỏ tới file đó.

## 2. COND-01 — tám lý do `seam-exempt`

Mỗi `SKILL.md` nhận một mục `## 🏛️ Platform-Aware Architecture Posture`, đặt ngay sau H1, một lần. Lý do ghi trên đĩa là lý do của chính skill đó. Điểm viết bằng ngoặc thường.

| Skill | Lý do ghi trên đĩa |
| :--- | :--- |
| `ccba-adr-lifecycle` | SOP kernel bốn bước: scaffold `docs/adr/00XX-<slug>.md`, cascade `SUPERSEDED`, `scripts/sync_hub_adr_matrix.py` ở Hub và ở Spoke với `--spoke-dir .`, rồi cổng `--check`. GPI `(4.0, 3.0, 4.0, 1.0) = 22.5`. |
| `ccba-review-proposal` | SOP kernel thẩm định PR Spoke lên Hub: đồng bộ `main`, Adaptive Tiered Review, nhánh `auto-tune/*` đọc `references/nightly_tuning_review.md`, Spoke Leakage Guard qua `scripts/governance/check_spoke_leakage.py`, ba worker, Copilot race guard, supervised self-healing, squash merge, hậu merge `compile_catalog.py`. GPI `(4.0, 4.0, 1.0, 1.0) = 18.5`. |
| `ccba-build-skill` | SOP kernel tác tạo skill: quét `scripts/maskara.py`, nạp nguồn bằng `python -m ccba_notebooklm`, Cổng 0, Cổng 1, GPI, sinh `SKILL.md`, `compile_catalog.py`, `verify-patch --preset skill`. Caller của `maskara_scanner.v1` và `notebooklm_rag.v1`. GPI `(3.0, 2.0, 2.0, 1.0) = 14.0`. |
| `ccba-skill-repair` | SOP kernel bốn bước: `validate_skills.py --enforce-gpi`, `evaluate-gpi`, vá YAML và khối `gpi`, liên kết tương đối, script bloat, exit 0. GPI `(3.0, 2.0, 1.0, 1.0) = 12.0`, nhánh Tier 2B, đồng thời nằm trong deadband `[11.5, 12.5)`. Khối `gpi` giữ một dòng. Thư mục `references/` chưa có. |
| `ccba-setup-skills` | SOP kernel phỏng vấn một lần: issue tracker, nhãn triage, domain docs, skills governance, ghi `AGENTS.md` và `.md/workspace_context.yaml`. Câu tại dòng 139–140 đứng nguyên. Hai dòng Level 3 giữ `pre_commit_setup.md` và `ts_deep_modules.md`. GPI `(3.5, 2.0, 2.0, 1.0) = 15.25`. |
| `ccba-create-verification-skill` | SOP kernel khởi tạo và bảo trì `verify-<app>`: năm khối Clean-Slate, Dual-Mode Server Lifecycle, Health Barrier, Evidence-Capture, Graceful Cleanup; mode `scaffold` và `maintain`; harness trong `.agents/skills/verify-<app>/harness/`; `features/INDEX.md`. GPI `(4.5, 3.5, 2.0, 1.0) = 20.75`. |
| `ccba-promote-sandbox` | SOP kernel bàn giao `personal_sandbox`: xác thực sandbox, chọn tệp, Spoke đích và mã PGV, gọi `scripts/promote_sandbox.py` ba pha Cleanse, Target Ingestion, PGV Sign-off Staging, rồi in hướng dẫn nghiệm thu. GPI `(3.0, 3.0, 1.0, 1.0) = 14.0`. Thư mục `references/` chưa có. |
| `ccba-codebase-design` | Reference skill từ vựng deep module: Module, Interface, Implementation, Depth, Seam theo Michael Feathers, Adapter, Leverage, Locality. Hard Stopping Rule chuyển sang `/ccba-implement` hoặc `/ccba-grilling` khi chưa có module mục tiêu. Seam này là vị trí thiết kế. 16 card đứng yên. GPI `(4.0, 3.0, 1.0, 1.0) = 16.5`. |

Đợt này giữ hai lời gọi hiện có của `ccba-build-skill` (`scripts/maskara.py`, `python -m ccba_notebooklm`) cạnh hai card sẵn có. Đợt này giữ `packages/` và 16 card.

## 3. COND-03 — bảng Level 3 và cây phụ

Hygiene trả exit code 1 cho cả YELLOW lẫn RED khi một reference markdown thiếu mặt trong bảng. Sáu bảng sau đứng nguyên. `ccba-skill-repair` và `ccba-promote-sandbox` chưa có thư mục `references/`. Đợt này không tạo thư mục đó.

| Skill | Số dòng trên đĩa | Tệp, đúng thứ tự bảng |
| :--- | :---: | :--- |
| `ccba-adr-lifecycle` | 1 | `architecture_sync_guide.md` |
| `ccba-review-proposal` | 1 | `nightly_tuning_review.md` |
| `ccba-build-skill` | 3 | `skill_authoring_guide.md`, `skill_review_checklist.md`, `skill_glossary.md` |
| `ccba-setup-skills` | 2 | `pre_commit_setup.md`, `ts_deep_modules.md` |
| `ccba-create-verification-skill` | 2 | `features_map_guide.md`, `maintain_drift_guide.md` |
| `ccba-codebase-design` | 4 | `codebase_refactor_guide.md`, `deepening.md`, `design_it_twice.md`, `html_report_template.md` |

`ccba-adr-lifecycle` còn mục `## Bộc Lộ Dần & Cấu Trúc Tinh Gọn (Progressive Disclosure)` ngay dưới bảng. Thứ tự đó đứng nguyên.

`ccba-setup-skills` còn cây phụ đứng ngoài diff:

| Đường dẫn | Tệp |
| :--- | :--- |
| `resources/` | `dependency-cruiser.config.cjs` |
| `templates/` | `domain.md`, `issue-tracker-github.md`, `issue-tracker-gitlab.md`, `issue-tracker-local.md`, `triage-labels.md` |

Câu cấm ghi `hub_path` tuyệt đối vào `.md/workspace_context.yaml` tại dòng 139–140 của `ccba-setup-skills` đứng nguyên, gồm ví dụ hình dạng `D:\...`, `/home/user/...`, và biến `$CCBA_HUB_PATH`.

## 4. COND-04 — hai fence PowerShell

Regex RED của hygiene, `\$\([^)\r\n]+\)`, soi cả fence `powershell`. Mẫu `$(...)` đứng ngoài tám `SKILL.md`. Quét hiện tại của tám file cho mẫu đó là rỗng. Biến PowerShell `$env:CCBA_HUB_PATH` nằm ngoài mẫu đó.

| Vị trí | Việc trong PR |
| :--- | :--- |
| `ccba-adr-lifecycle` dòng 108, fence powershell | `python "$env:CCBA_HUB_PATH/scripts/sync_hub_adr_matrix.py" --spoke-dir .` |
| `ccba-adr-lifecycle` lệnh Hub | Giữ `python scripts/sync_hub_adr_matrix.py` và `python scripts/sync_hub_adr_matrix.py --check` |
| `ccba-promote-sandbox` dòng 57 | Ví dụ đích `$env:PROJECTS_ROOT/2026-04-dh-viet-nhat` |
| `ccba-promote-sandbox` dòng 68 | Câu phân giải Hub qua `$env:CCBA_HUB_PATH` |
| `ccba-promote-sandbox` dòng 71, fence powershell | `python "$env:CCBA_HUB_PATH/scripts/promote_sandbox.py" --target "$env:PROJECTS_ROOT/2026-04-dh-viet-nhat" --files <files> --pgv "<pgv>"` |

Ba cờ `--target`, `--files`, `--pgv` đứng trong cùng fence. Slug ví dụ `2026-04-dh-viet-nhat` đứng trong ví dụ. Chú thích `ccba:allow-machine-path` đứng ngoài markdown.

## 5. Bốn PR và khóa hoàn tất

| PR | Tệp | Việc |
| :--- | :--- | :--- |
| **8A** | `ccba-adr-lifecycle/SKILL.md`, `ccba-review-proposal/SKILL.md` | Mục `seam-exempt`. GPI 22.5 và 18.5. COND-04 trên `ccba-adr-lifecycle`. Giữ 1 dòng Level 3 cho mỗi skill. |
| **8B** | `ccba-build-skill/SKILL.md`, `ccba-skill-repair/SKILL.md` | Mục `seam-exempt`. Giữ GPI 14.0 và 12.0. Giữ khối `gpi` một dòng của `ccba-skill-repair`. Giữ 3 dòng Level 3 của `ccba-build-skill`. |
| **8C** | `ccba-setup-skills/SKILL.md`, `ccba-create-verification-skill/SKILL.md` | Mục `seam-exempt`. Giữ GPI 15.25 và 20.75. Giữ 2 dòng Level 3 cho mỗi skill. Giữ `resources/` và `templates/` của `ccba-setup-skills`. |
| **8D** | `ccba-promote-sandbox/SKILL.md`, `ccba-codebase-design/SKILL.md` | Mục `seam-exempt`. Giữ GPI 14.0 và 16.5. COND-04 trên `ccba-promote-sandbox`. Giữ 4 dòng Level 3 của `ccba-codebase-design`. |

8A, 8B, 8C, 8D chạy bộ ba lệnh trên từng `SKILL.md` trong cặp của mình. Với `ccba-skill-repair`, điểm 12.0 đi nhánh Tier 2B.

Đứng ngoài bốn PR: `packages/`, `seam-contracts.yaml`, `catalog.yaml`, `docs/adr/`, `scripts/` ở gốc repo, toàn bộ `references/`, `resources/`, `templates/` của tám skill.

Phần để lại cho một đợt sau, và vì vậy điểm rủi ro là 2:

- `ccba-build-skill` tiếp tục gọi `scripts/maskara.py` cạnh card `maskara_scanner.v1`, và `python -m ccba_notebooklm` cạnh card `notebooklm_rag.v1`.
- `ccba-codebase-design` tiếp tục là reference skill với Hard Stopping Rule và từ vựng Seam của Michael Feathers.
- `ccba-review-proposal` tiếp tục mô tả ba worker, subagent Boost, và HITL của Maintainer trong thân bài, với `tier: kernel`.
- Công thức `$$` đang có trong `ccba-build-skill` và `ccba-skill-repair` đứng nguyên. Các dòng `$< 400$` và `$100\%$` trong `ccba-review-proposal` đứng nguyên.
- Dòng chữ ký cuối `ccba-promote-sandbox` đứng nguyên.

Sau khi cả bốn PR xanh trên đĩa, đệ trình nghiệm thu Đợt 8 kèm `python -m ccba_harness verify-patch --preset ci`.