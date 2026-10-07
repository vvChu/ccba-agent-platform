---
request_id: req-discuss-wave9-orchestration-session-skills-001
verdict: APPROVE_PLAN
conditions:
- id: COND-01
  description: Đã khóa. Bảy skill nhận đúng một mục `## 🏛️ Platform-Aware Architecture
    Posture`, không có số ADR trong tiêu đề, đặt sau đoạn mở đầu và trước H2 hiện
    có. ccba-ai-qc giữ một mục duy nhất, thế năng package-bound với qc_pipeline.v1
    (import ccba_qc_core:QCAuditPipeline) và lời gọi pdf_preprocessor.v1 (import ccba_pdf_prep:PDFProcessingPipeline).
    Token ADR-0061 đứng trong mục đó. Không thêm mục posture thứ hai. seam-contracts.yaml
    giữ 16 seam_id. packages/ đứng ngoài đợt. Lý do posture lấy từ thân bài trên đĩa.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-02
  description: 'Đã khóa. Frontmatter tám file đứng nguyên từng khóa: name, tier, bundle,
    command, triggers, description, metadata, gpi, package_path, is-orchestrated,
    disable-model-invocation, applies_to, category, keywords, argument-hint, role.
    Cờ is-deterministic tiếp tục vắng. Bốn orchestrator giữ tier orchestrator và is-orchestrated
    true, khối gpi tiếp tục vắng, validator trả về sau Cổng 1. Bốn kernel giữ điểm:
    wayfinder 14.5, handoff 12.0, session-retrospective 12.0, issue-tree 14.5. Điểm
    12.0 đi nhánh Tier 2B vì ngưỡng >= 12.0 và đồng thời nằm trong deadband [11.5,
    12.5). Khóa existing-tier tiếp tục vắng. tier kernel là existing tier. Điểm 14.5
    nằm phía trên cận 12.5.'
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-03
  description: 'Đã khóa. Bảng Level 3 đứng nguyên đúng tên và đúng thứ tự. ccba-ai-qc
    4 dòng discovery.md, integrated_audit.md, reporter.md, batch_orchestrator.md.
    ccba-session-retrospective 1 dòng references/agent_environment_diagnostics.md.
    ccba-issue-tree 2 dòng references/tree_templates.md, references/governed_lifecycle_guide.md.
    Năm skill chưa có references/: teamwork, autoresearch, knowledge-loop, wayfinder,
    handoff. ccba-teamwork giữ resources/team_sheet_template.md. ccba-ai-qc giữ năm
    tệp scripts/. references/, resources/, scripts/ đứng ngoài diff của cả bốn PR.'
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-04
  description: Đã khóa. Tập số ADR của từng SKILL.md đứng yên. Mục posture của bảy
    skill mới chứa 0 token ADR. ccba-ai-qc giữ ADR-0061. teamwork giữ 0053 và 0058.
    knowledge-loop giữ 0053. session-retrospective giữ 0030, 0053, 0057, 0058, 0060.
    issue-tree giữ 0059. autoresearch, wayfinder, handoff giữ tập rỗng. Mẫu $(...)
    đứng ngoài tám SKILL.md. docs/adr/, catalog.yaml, seam-contracts.yaml, packages/
    đứng ngoài bốn PR.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-05
  description: Đã khóa. Bốn PR song song 9A-9D, bốn cặp thư mục tách biệt, mỗi PR
    chỉ sửa SKILL.md của cặp đó. Mỗi SKILL.md khóa bằng validate_skills.py --file
    --enforce-gpi, audit_skills_hygiene.py --file, và verify-patch --preset skill
    --target. Preset skill đã gọi compile_catalog.py --check và sync_hub_adr_matrix.py
    --check. Sau khi cả bốn PR có trên đĩa, chạy verify-patch --preset ci. Điểm trong
    đoạn posture viết dạng (S, K, A, P) = số.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
risk_score: 2
effort: M
summary: Kế hoạch Đợt 9 được phép bắt đầu. Bảy skill nhận seam-exempt. ccba-ai-qc
  giữ package-bound trên qc_pipeline.v1. GPI, tier và 16 card seam đứng yên. Bốn PR
  song song. Lý do posture và bảng Level 3 khóa theo tệp đang có trên đĩa. Tập token
  ADR từng file đứng yên để preset skill và preset ci giữ sync_hub_adr_matrix.py --check
  xanh.
telemetry:
  session_id: adcfde13-4e97-49fb-9b38-37726f1ff1ad
  primary_model: grok-4.7-build
  input_tokens: 1089200
  output_tokens: 26514
  reasoning_tokens: 17006
  cached_read_tokens: 989312
  total_tokens: 1115714
  model_calls: 17
  turn_count: 1
  cost_usd: 290195.44
  cost_mode: exact
  duration_seconds: 347.08
---
## PeerVerdictBlock

```yaml
peer_verdict:
  request_id: "req-discuss-wave9-orchestration-session-skills-001"
  from_agent: "grok"
  to_agent: "antigravity"
  profile: "arch_audit"
  pass: 1
  verdict: APPROVE_PLAN
  risk_score: 2
  authorized_start: allowed
  dag:
    parallel: ["9A", "9B", "9C", "9D"]
    after: {}
  lock:
    - "python scripts/validate_skills.py --file <SKILL.md> --enforce-gpi"
    - "python scripts/governance/audit_skills_hygiene.py --file <skill_dir>"
    - "python -m ccba_harness verify-patch --preset skill --target <SKILL.md>"
  floor: "python -m ccba_harness verify-patch --preset ci"
  rationale: >
    Bảy skill là SOP seam-exempt. ccba-ai-qc đã gắn package-bound với
    qc_pipeline.v1 và là caller của pdf_preprocessor.v1. seam-contracts.yaml
    có 16 seam_id. Bốn orchestrator dừng tại Cổng 1. Bốn kernel giữ hệ số
    hiện có. handoff và session-retrospective đạt GPI 12.0, đúng ngưỡng Tier 2B.
    Bốn PR không chung tệp. Tập token ADR từng file đứng yên.
```

Phán quyết: **APPROVE_PLAN**. Bốn PR song song được phép bắt đầu. Điểm rủi ro **2/5**. Phần rủi ro còn lại nằm ở kỷ luật khi chép lý do posture từ thân bài, khi giữ `package-bound` của `ccba-ai-qc`, và khi giữ nguyên tập token ADR để cổng parity vẫn xanh. Năm điều kiện `blocking: false` ở trên đã khóa các điểm đó.

Tệp: `.md/peer_exchange/grok_discuss_wave9_orchestration_session_skills.md`

## 1. Đối soát trên đĩa

`seam-contracts.yaml` có đúng 16 `seam_id`: `legal_markdown.v1`, `ooxml_processor.v1`, `pdf_preprocessor.v1`, `legal_ingest.v1`, `legal_advisor.v1`, `ai_chat.v1`, `ai_embedding.v1`, `ai_transcribe.v1`, `model_routing.v1`, `maskara_scanner.v1`, `diagram_layout.v1`, `qc_pipeline.v1`, `harness_verify.v1`, `harness_eval.v1`, `peer_dispatch.v1`, `notebooklm_rag.v1`.

Card `qc_pipeline.v1` có `import_path: ccba_qc_core:QCAuditPipeline`, `in: [drawing_set, project_dir]`, `out: [audit_report]`. Card `pdf_preprocessor.v1` có `import_path: ccba_pdf_prep:PDFProcessingPipeline`. Card `harness_verify.v1` có `import_path: ccba_harness:auto_apply_and_verify_patch`. Card `harness_eval.v1` có `import_path: ccba_harness:EvalRunner`. Tên bảy skill seam-exempt vắng trong file này. `ccba-ai-qc` cũng vắng tên trong file hợp đồng; liên kết của nó đi qua `package_path` và lời gọi import.

Công thức trong `packages/ccba-harness/src/ccba_harness/gpi.py` là `(S × 2.5) + (K × 2.0) + (A × 2.0) − (P × 1.5)`. `GPI_STANDALONE_THRESHOLD` là 12.0. Deadband là `[11.5, 12.5)`. Bốn số kernel trên đĩa khớp frontmatter:

| Skill | `(S, K, A, P)` | GPI | Tier trên đĩa | Bundle |
| :--- | :--- | :---: | :--- | :--- |
| `ccba-wayfinder` | `(4.0, 2.0, 1.0, 1.0)` | 14.5 | `kernel` | `_core` |
| `ccba-handoff` | `(3.0, 2.0, 1.0, 1.0)` | 12.0 | `kernel` | `_core` |
| `ccba-session-retrospective` | `(3.0, 2.0, 1.0, 1.0)` | 12.0 | `kernel` | `_core` |
| `ccba-issue-tree` | `(4.0, 2.0, 1.0, 1.0)` | 14.5 | `kernel` | `_core` |

Nhánh phân tầng gốc gán Tier 2B khi điểm `>= 12.0`. Điểm 12.0 của `ccba-handoff` và `ccba-session-retrospective` đã là Tier 2B trước hysteresis. Deadband cũng chứa 12.0. Điểm 14.5 nằm phía trên cận `GPI_DEADBAND_UPPER` 12.5, nên hysteresis không tham gia hai skill đó. `SkillValidator` lấy `existing_tier` từ `tier: kernel` khi frontmatter không có khóa `existing-tier`. Khóa đó tiếp tục vắng trên cả bốn kernel.

Bốn orchestrator trên đĩa:

| Skill | Tier | `is-orchestrated` | Khối `gpi` | Bundle | `package_path` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ccba-ai-qc` | `orchestrator` | `true` | vắng | `_qc` | `packages/ccba-qc-core` |
| `ccba-teamwork` | `orchestrator` | `true` | vắng | `_core` | vắng |
| `ccba-autoresearch` | `orchestrator` | `true` | vắng | `_core` | vắng |
| `ccba-knowledge-loop` | `orchestrator` | `true` | vắng | `_core` | vắng |

Validator trả về ngay sau Cổng 1 khi `tier` là `orchestrator`, trước khi đọc `gpi`. Cờ `is-deterministic` tiếp tục vắng trên cả tám file. Thêm cờ đó sẽ đẩy skill sang Cổng 0.

`compile_catalog.py` kéo `name`, `bundle`, `description`, `triggers`, `command`, `package_path`, `tier`. Mục posture nằm trong thân Markdown. `catalog.yaml` giữ nguyên khi các khóa đó đứng yên. Entry `ccba-ai-qc` đã có `package_path: packages/ccba-qc-core` và `tier: orchestrator`. Entry `ccba-autoresearch` mô tả Git-Ratchet Auto-Tuner.

Preset `skill` trong `verifier.py` chạy `validate_skills.py --enforce-gpi`, `compile_catalog.py --check`, và `sync_hub_adr_matrix.py --check`. Preset `ci` cũng chạy hai lệnh check đó. Scanner ma trận khớp `HUB-ADR`, `HUB_ADR`, và `ADR` kèm số. Hàng `HUB-ADR 0061` đã có `ccba-ai-qc`. Bảy skill còn lại chưa có trên hàng đó.

## 2. COND-01 — posture trên đĩa

Bảy skill chưa có mục posture nhận một mục `## 🏛️ Platform-Aware Architecture Posture`. Tiêu đề không kèm số ADR. Mục đặt sau đoạn mở đầu, trước H2 đang có, một lần. Mẫu vị trí là mục đã đứng trong `ccba-skill-repair`.

`ccba-ai-qc` đã có mục tại dòng 85, `## 🏛️ Platform-Aware Reuse Gate & Seam Binding (ADR-0061)`, thế năng `package-bound`. Đợt này đổi tiêu đề mục đó thành `## 🏛️ Platform-Aware Architecture Posture` và giữ token `ADR-0061` trong câu đầu của cùng mục. Fence `find-seam`, fence `from ccba_qc_core import QCAuditPipeline`, và câu `pdf_preprocessor.v1` đứng nguyên. Mục này tiếp tục đứng sau Bước 1 và trước bảng Level 3. Đợt này không chèn mục posture thứ hai.

| Skill | Lý do ghi trên đĩa |
| :--- | :--- |
| `ccba-ai-qc` | Master orchestrator, thế năng `package-bound` theo ADR-0061, gắn `qc_pipeline.v1` của `ccba-qc-core`. `find-seam --in drawing_set project_dir --out audit_report` phải trả `MATCH`, `import_path` là `ccba_qc_core:QCAuditPipeline`. Ba pha chạy qua `QCAuditPipeline.run_audit_sync`. Tiền xử lý PDF đi qua `pdf_preprocessor.v1` (`ccba_pdf_prep:PDFProcessingPipeline`). `tier: orchestrator`. |
| `ccba-teamwork` | SOP orchestrator bốn giai đoạn, ba vai trò, Worker Cap 3. Chữ seam trong thân bài là Exclusive Seam Ownership theo phân vùng tệp. Single-Writer hợp nhất bằng `scripts/governance/apply_worker_patch.py`. `verify-patch --preset code` là caller của `harness_verify.v1`. Bước auditor gọi `scripts/governance/check_spoke_leakage.py`. 16 card đứng yên. `tier: orchestrator`. |
| `ccba-autoresearch` | SOP orchestrator Git-Ratchet Auto-Tuner qua `scripts/eval/git_ratchet_tuner.py`: `--program program.md`, `--dry-run-git`, và `--target` với `--max-trials` cùng `--target-score`. Mẫu `program.md` lấy từ `ccba-eval-gate/references/program_template.md`. Card `harness_eval.v1` giữ `ccba_harness:EvalRunner`. 16 card đứng yên. `tier: orchestrator`. |
| `ccba-knowledge-loop` | SOP orchestrator bốn pha trên đĩa: `/ccba-youtube-learn`, `/ccba-research`, `/ccba-ask` brainstorm, `/ccba-wayfinder`. Single-Writer đã có trong thân bài. Bản đồ tại `.md/knowledge/issues/<feature>/map.md`. Subagent nghiên cứu ghi scratch. 16 card đứng yên. `tier: orchestrator`. |
| `ccba-wayfinder` | SOP kernel Wayfinding Map: Destination, Notes, Decisions so far, Not yet specified, Out of scope. Bốn loại ticket Research, Prototype, Grilling, Task. Fog vs Ticket Test. GPI `(4.0, 2.0, 1.0, 1.0) = 14.5`. `tier: kernel`. |
| `ccba-handoff` | SOP kernel tài liệu 5 phần tại `.md/scratch/handoffs/handoff-<timestamp>.md`. Bước redact đi qua chuẩn Maskara. GPI `(3.0, 2.0, 1.0, 1.0) = 12.0`, nhánh Tier 2B, đồng thời nằm trong deadband `[11.5, 12.5)`. `tier: kernel`. |
| `ccba-session-retrospective` | SOP kernel sáu bước trên đĩa: learnings vào `session_learnings.md`, skill evolution có cổng chờ người dùng, đồng bộ ma trận kèm `compile_catalog.py` và `compile_skills_docs.py`, governance gate, `session_cleanup.py`, báo cáo tóm tắt. GPI `(3.0, 2.0, 1.0, 1.0) = 12.0`, nhánh Tier 2B, đồng thời nằm trong deadband. `tier: kernel`. |
| `ccba-issue-tree` | SOP kernel ba cây MECE trên đĩa: Why-Tree, How-Tree, What-Tree, chuỗi chuyển tiếp, Governed Lifecycle sáu trạng thái, Fast-Tree và Full-Tree. GPI `(4.0, 2.0, 1.0, 1.0) = 14.5`. `role: master_skill` đứng yên. `tier: kernel`. |

Đoạn posture của bảy skill mới chứa 0 token dạng `ADR` kèm số. Câu GPI viết bằng ngoặc thường.

`ccba-teamwork` và `ccba-knowledge-loop` giữ các cụm Single-Writer đang có (`single-writer`, `read-only`, `scratch`, `team_sheet`, `spawn subagent`). Validator chỉ kiểm Single-Writer khi thân bài chứa một trong các cụm điều phối worker. Đoạn posture của `ccba-autoresearch` mô tả Git-Ratchet và đứng ngoài các cụm đó.

Năm tệp `scripts/` của `ccba-ai-qc` (`discovery_engine.py`, `legacy_quadview_engine.py`, `orchestrator.py`, `reporter_engine.py`, `semantic_audit_engine.py`) đứng nguyên trên đĩa. Đợt này không xóa chúng và không sửa `packages/ccba-qc-core`.

## 3. COND-02 — tier và GPI

Frontmatter đứng nguyên từng khóa đang có. `ccba-ai-qc` giữ `applies_to`, `category`, `keywords`, `package_path`. `ccba-teamwork` giữ `disable-model-invocation: true`. `ccba-autoresearch` giữ dòng trống giữa `name` và `description`. `ccba-handoff` giữ `argument-hint`. `ccba-issue-tree` giữ `role: master_skill`. `ccba-session-retrospective` giữ `category: workflow` và `keywords`.

Bốn khối `gpi` kernel giữ dạng nhiều dòng với `s`, `k`, `a`, `p`. Đợt này không thêm khóa `score`. Đợt này không thêm khối `gpi` vào bốn orchestrator.

## 4. COND-03 — bảng Level 3 và cây phụ

Hygiene trả exit code 1 cho cả YELLOW lẫn RED khi một reference markdown thiếu mặt trong bảng. Ba bảng sau đứng nguyên. Năm skill chưa có `references/` ghi câu đó trong mục posture. Đợt này không tạo thư mục `references/` mới.

| Skill | Số dòng trên đĩa | Tệp, đúng thứ tự bảng |
| :--- | :---: | :--- |
| `ccba-ai-qc` | 4 | `discovery.md`, `integrated_audit.md`, `reporter.md`, `batch_orchestrator.md` |
| `ccba-session-retrospective` | 1 | `references/agent_environment_diagnostics.md` |
| `ccba-issue-tree` | 2 | `references/tree_templates.md`, `references/governed_lifecycle_guide.md` |

`ccba-ai-qc` còn sơ đồ mermaid và ba liên kết pha trỏ cùng bốn tệp. Thứ tự đó đứng nguyên.

`ccba-teamwork` còn cây phụ đứng ngoài diff:

| Đường dẫn | Tệp |
| :--- | :--- |
| `resources/` | `team_sheet_template.md` |

Câu posture của `ccba-teamwork` ghi nhận skill chưa có `references/` và đã có `resources/team_sheet_template.md`.

## 5. COND-04 — tập token ADR

`sync_hub_adr_matrix.py --check` so nguyên văn `docs/adr/TRACEABILITY_MATRIX.md` với radar quét mọi `SKILL.md`. Thêm một số ADR vào file đang vắng số đó làm lệch hàng tương ứng. `docs/adr/` đứng ngoài bốn PR, nên tập số của từng file phải giữ đúng như hiện tại.

| Skill | Số ADR đang có trên đĩa | Hàng ma trận đã trỏ tới file |
| :--- | :--- | :--- |
| `ccba-ai-qc` | 0061 | HUB-ADR 0061 |
| `ccba-teamwork` | 0053, 0058 | HUB-ADR 0053, HUB-ADR 0058 |
| `ccba-autoresearch` | rỗng | chưa có hàng nào |
| `ccba-knowledge-loop` | 0053 | HUB-ADR 0053 |
| `ccba-wayfinder` | rỗng | chưa có hàng nào |
| `ccba-handoff` | rỗng | chưa có hàng nào |
| `ccba-session-retrospective` | 0030, 0053, 0057, 0058, 0060 | các hàng tương ứng |
| `ccba-issue-tree` | 0059 | HUB-ADR 0059 |

Các câu thân bài đang chứa các số trên đứng nguyên, gồm cách viết `ADR 0053` và `ADR-0053` trong `ccba-teamwork`. Mẫu `$(...)` đứng ngoài tám `SKILL.md`. Quét hiện tại cho mẫu đó là rỗng. Ký hiệu toán `$\ne$`, `$\le$`, `$\rightarrow$` đứng ngoài regex RED của hygiene.

## 6. Bốn PR và khóa hoàn tất

| PR | Tệp | Việc |
| :--- | :--- | :--- |
| **9A** | `ccba-ai-qc/SKILL.md`, `ccba-teamwork/SKILL.md` | `ccba-ai-qc` giữ `package-bound` và token 0061. `ccba-teamwork` nhận `seam-exempt`. Giữ 4 dòng Level 3. Giữ `resources/team_sheet_template.md` và năm tệp `scripts/` của `ccba-ai-qc`. Giữ orchestrator. |
| **9B** | `ccba-autoresearch/SKILL.md`, `ccba-knowledge-loop/SKILL.md` | `seam-exempt`. Lý do Auto-Tuner và bốn pha. Giữ orchestrator. Tập ADR của `ccba-autoresearch` giữ rỗng. `ccba-knowledge-loop` giữ số 0053. |
| **9C** | `ccba-wayfinder/SKILL.md`, `ccba-handoff/SKILL.md` | `seam-exempt`. Giữ GPI 14.5 và 12.0. Hai mục posture chứa 0 token ADR. Ghi nhận chưa có `references/`. |
| **9D** | `ccba-session-retrospective/SKILL.md`, `ccba-issue-tree/SKILL.md` | `seam-exempt`. Giữ GPI 12.0 và 14.5. Giữ 1 dòng và 2 dòng Level 3. Giữ tập ADR hiện có của từng file. Giữ `role: master_skill`. |

9A, 9B, 9C, 9D chạy bộ ba lệnh trên từng `SKILL.md` trong cặp của mình. `validate_skills.py --enforce-gpi` với orchestrator trả về tại Cổng 1. Với `ccba-handoff` và `ccba-session-retrospective`, điểm 12.0 đi nhánh Tier 2B.

Đứng ngoài bốn PR: `packages/`, `seam-contracts.yaml`, `catalog.yaml`, `docs/adr/`, `scripts/`, toàn bộ `references/` và `resources/` của tám skill, và các skill được liên kết (`ccba-eval-gate`, `ccba-youtube-learn`, `ccba-research`, `ccba-ask`, `ccba-wayfinder` khi sửa `ccba-knowledge-loop`).

Phần để lại cho một đợt sau, và vì vậy điểm rủi ro là 2: năm script trong `ccba-ai-qc/scripts/` tiếp tục đứng cạnh seam `qc_pipeline.v1`. Đợt 9 chỉ chuẩn hóa posture trong `SKILL.md`.

Sau khi cả bốn PR xanh trên đĩa, đệ trình nghiệm thu Đợt 9 kèm `python -m ccba_harness verify-patch --preset ci`.