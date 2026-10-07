---
request_id: req-discuss-wave10-content-office-diagram-skills-001
verdict: APPROVE_PLAN
conditions:
- id: COND-01
  description: 'Đã khóa. Đúng một mục `## 🏛️ Platform-Aware Architecture Posture`
    trên mỗi file, tiêu đề không chứa số ADR. ccba-excalidraw-diagram đổi tiêu đề
    mục dòng 75 tại chỗ và giữ package-bound trên diagram_layout.v1 (ccba_diagram:apply_smart_layout),
    fence `find-seam --in diagram --out layout --json`, và Determinism Invariant.
    ccba-xu-ly-van-phong nhận package-bound trên ooxml_processor.v1 (ccba_ooxml:DocxDocument);
    card cấm import thay thế docx và openpyxl. Năm skill còn lại nhận seam-exempt,
    vai trò caller khi thân bài đã gọi script hoặc CLI. seam-contracts.yaml giữ 16
    seam_id. packages/ đứng ngoài đợt. Lý do posture lấy từ thân bài trên đĩa.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-02
  description: 'Đã khóa. Frontmatter bảy file đứng nguyên từng khóa đang có. Cả bảy
    giữ tier kernel. Khối gpi giữ nguyên hệ số: excalidraw (4.0, 4.0, 3.0, 3.0) =
    19.5; xu-ly-van-phong (3.0, 3.0, 1.0, 1.0) = 14.0; pptx (3.0, 2.0, 1.0, 1.0) =
    12.0; docs-manager (3.0, 3.0, 1.0, 1.0) = 14.0; academic-writing (4.0, 3.0, 1.0,
    1.0) = 16.5; copywriting (3.0, 3.0, 1.0, 1.0) = 14.0; to-spec (4.0, 2.0, 1.0,
    1.0) = 14.5. Điểm 12.0 đã là Tier 2B vì ngưỡng >= 12.0 và đồng thời nằm trong
    deadband [11.5, 12.5). Cờ is-deterministic, is-orchestrated, existing-tier và
    khóa score tiếp tục vắng. package_path chỉ có trên ccba-xu-ly-van-phong.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-03
  description: 'Đã khóa. Bảng Level 3 đứng nguyên đúng tên và đúng thứ tự trên đĩa.
    academic-writing 3 dòng, copywriting 10 dòng, docs-manager 1 dòng, excalidraw-diagram
    1 dòng, pptx 2 dòng, to-spec 2 dòng, xu-ly-van-phong 4 dòng. references/, resources/,
    standards/, scripts/, templates/, examples/ của bảy thư mục skill đứng ngoài diff
    của cả bốn PR.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-04
  description: 'Đã khóa. Tập số ADR của từng SKILL.md đứng yên. ccba-excalidraw-diagram
    giữ đúng một token ADR-0061, chuyển từ tiêu đề cũ vào câu đầu của cùng mục posture.
    Sáu skill còn lại giữ tập rỗng. Mẫu $(...) đứng ngoài bảy SKILL.md. Đoạn posture
    viết điểm dạng (S, K, A, P) = số. docs/adr/, catalog.yaml, seam-contracts.yaml
    và packages/ đứng ngoài bốn PR.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-05
  description: 'Đã khóa. Bốn PR 10A-10D sửa đúng SKILL.md của cặp hoặc file được giao,
    bốn tập đường dẫn tách biệt, được phép chạy song song. Mỗi SKILL.md khóa bằng
    validate_skills.py --file --enforce-gpi, audit_skills_hygiene.py --file, và verify-patch
    --preset skill --target. Sau khi cả bốn PR có trên đĩa, chạy verify-patch --preset
    ci và lấy exit code 0 của sáu lệnh preset. Sàn này là exit code, không phải một
    hằng số lượng test.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
risk_score: 2
effort: M
summary: Kế hoạch Đợt 10 được phép bắt đầu. ccba-excalidraw-diagram và ccba-xu-ly-van-phong
  giữ package-bound. Năm skill còn lại nhận seam-exempt. GPI, tier kernel và 16 card
  seam đứng yên. Bốn PR không chung tệp nên chạy song song. Lý do posture khóa theo
  thân bài trên đĩa. Token ADR-0061 của excalidraw phải còn trong thân bài sau khi
  tiêu đề bỏ số ADR, để sync_hub_adr_matrix.py --check giữ xanh.
telemetry:
  session_id: 74e0f77a-954c-47e3-b438-cb3c1c1a097c
  primary_model: grok-4.7-build
  input_tokens: 1289033
  output_tokens: 29603
  reasoning_tokens: 19534
  cached_read_tokens: 1145728
  total_tokens: 1318636
  model_calls: 19
  turn_count: 1
  cost_usd: 352611.28
  cost_mode: exact
  duration_seconds: 385.09
---
## PeerVerdictBlock

```yaml
peer_verdict:
  request_id: "req-discuss-wave10-content-office-diagram-skills-001"
  from_agent: "grok"
  to_agent: "antigravity"
  profile: "arch_audit"
  pass: 1
  verdict: APPROVE_PLAN
  risk_score: 2
  authorized_start: allowed
  dag:
    parallel: ["10A", "10B", "10C", "10D"]
    after: {}
  lock:
    - "python scripts/validate_skills.py --file <SKILL.md> --enforce-gpi"
    - "python scripts/governance/audit_skills_hygiene.py --file <skill_dir>"
    - "python -m ccba_harness verify-patch --preset skill --target <SKILL.md>"
  floor: "python -m ccba_harness verify-patch --preset ci"
  rationale: >
    Hai skill có neo gói thật: excalidraw-diagram trên diagram_layout.v1 và
    xu-ly-van-phong trên ooxml_processor.v1. Năm skill còn lại là SOP
    seam-exempt. seam-contracts.yaml có 16 seam_id. Bảy kernel giữ hệ số
    hiện có. pptx đạt GPI 12.0, đúng ngưỡng Tier 2B. Bốn PR không chung tệp.
    Tập token ADR từng file đứng yên.
```

Phán quyết: **APPROVE_PLAN**. Bốn PR song song được phép bắt đầu. Điểm rủi ro **2/5**. Phần rủi ro còn lại nằm ở chỗ chuyển token `ADR-0061` khỏi tiêu đề mà vẫn giữ token trong thân bài, ở chỗ mục posture của `ccba-xu-ly-van-phong` phải nói đúng card `ooxml_processor.v1` trong khi `resources/` vẫn đứng ngoài diff, và ở chỗ năm mục seam-exempt phải chép lý do từ thân bài đang có. Năm điều kiện `blocking: false` ở trên đã khóa các điểm đó.

Tệp: `.md/peer_exchange/grok_discuss_wave10_content_office_diagram_skills.md`

## 1. Đối soát trên đĩa

`seam-contracts.yaml` có đúng 16 `seam_id`: `legal_markdown.v1`, `ooxml_processor.v1`, `pdf_preprocessor.v1`, `legal_ingest.v1`, `legal_advisor.v1`, `ai_chat.v1`, `ai_embedding.v1`, `ai_transcribe.v1`, `model_routing.v1`, `maskara_scanner.v1`, `diagram_layout.v1`, `qc_pipeline.v1`, `harness_verify.v1`, `harness_eval.v1`, `peer_dispatch.v1`, `notebooklm_rag.v1`.

Card `diagram_layout.v1` có `import_path: ccba_diagram:apply_smart_layout`, `in: [diagram, excalidraw_elements]`, `out: [layout]`, `forbidden_substitute_imports: [graphviz]`. Card `ooxml_processor.v1` có `import_path: ccba_ooxml:DocxDocument`, `in: [docx, xlsx, pptx]`, `out: [docx, structured_table, markdown]`, `forbidden_substitute_imports: [openpyxl, docx]`, `implementation_packages: [ccba_ooxml, ccba_legal, mdconverter]`. `match_seam_cards` nhận MATCH khi mọi type được hỏi nằm trong card. Lệnh `find-seam --in diagram --out layout` là truy vấn capability, trạng thái `MATCH`. Đường keyword riêng trả `KEYWORD_HINT`. Fence đang có trong `ccba-excalidraw-diagram` đi đúng đường capability.

Công thức trong `packages/ccba-harness/src/ccba_harness/gpi.py` là `(S × 2.5) + (K × 2.0) + (A × 2.0) − (P × 1.5)`. `GPI_STANDALONE_THRESHOLD` là 12.0. Deadband là `[11.5, 12.5)`. Nhánh gốc gán Tier 2B khi điểm `>= 12.0`. Bảy số trên đĩa khớp frontmatter:

| Skill | `(S, K, A, P)` | GPI | Tier | Bundle | `package_path` |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `ccba-excalidraw-diagram` | `(4.0, 4.0, 3.0, 3.0)` | 19.5 | `kernel` | `_core` | vắng |
| `ccba-xu-ly-van-phong` | `(3.0, 3.0, 1.0, 1.0)` | 14.0 | `kernel` | `_software` | `packages/ccba-ooxml` |
| `ccba-pptx` | `(3.0, 2.0, 1.0, 1.0)` | 12.0 | `kernel` | `_core` | vắng |
| `ccba-docs-manager` | `(3.0, 3.0, 1.0, 1.0)` | 14.0 | `kernel` | `_software` | vắng |
| `ccba-academic-writing` | `(4.0, 3.0, 1.0, 1.0)` | 16.5 | `kernel` | `_core` | vắng |
| `ccba-copywriting` | `(3.0, 3.0, 1.0, 1.0)` | 14.0 | `kernel` | `_software` | vắng |
| `ccba-to-spec` | `(4.0, 2.0, 1.0, 1.0)` | 14.5 | `kernel` | `_core` | vắng |

Điểm 12.0 của `ccba-pptx` đã là Tier 2B trước hysteresis, và đồng thời nằm trong deadband. Sáu điểm còn lại nằm phía trên cận `GPI_DEADBAND_UPPER` 12.5, nên hysteresis không tham gia. `SkillValidator` lấy `existing_tier` từ `tier: kernel` khi frontmatter không có khóa `existing-tier`. Khóa đó tiếp tục vắng trên cả bảy file. Cờ `is-deterministic` tiếp tục vắng. Thêm cờ đó đẩy skill sang Cổng 0 và validator trả về trước Stage 2.

`compile_catalog.py` kéo `name`, `bundle`, `description`, `triggers`, `command`, `package_path`, `tier`. Entry catalog của `ccba-xu-ly-van-phong` đã có `package_path: packages/ccba-ooxml`. Sáu entry còn lại không có `package_path`. Mục posture nằm trong thân Markdown. Các khóa catalog đứng yên thì `catalog.yaml` đứng yên.

Preset `skill` chạy `validate_skills.py --enforce-gpi`, `compile_catalog.py --check`, và `sync_hub_adr_matrix.py --check`. Preset `ci` là sáu lệnh: `ruff check`, `ruff format --check`, `pytest` trên các đường dẫn telemetry / verify-patch / `tests/governance`, rồi ba lệnh check ở trên. Scanner ma trận trong Hub khớp `\b(?:HUB-ADR|HUB_ADR|ADR)[-\s]*0*([0-9]+)\b`. Hàng `HUB-ADR 0061` đã có `ccba-excalidraw-diagram`. Sáu skill còn lại vắng trên ma trận.

Bốn PR trong kế hoạch không chung đường dẫn. Mũi tên `10A → 10B → 10C → 10D` là lịch, không phải phụ thuộc tệp. DAG được phép chạy song song.

## 2. COND-01 — posture trên đĩa

Sáu skill chưa có mục posture nhận một mục `## 🏛️ Platform-Aware Architecture Posture`. Tiêu đề không kèm số ADR. Mục đặt sau đoạn mở đầu, trước H2 đang có, một lần.

`ccba-excalidraw-diagram` đã có mục tại dòng 75. Đợt này đổi tiêu đề mục đó thành `## 🏛️ Platform-Aware Architecture Posture` và giữ nguyên phần còn lại của mục. Đợt này không chèn mục posture thứ hai.

| Skill | Lý do ghi trên đĩa |
| :--- | :--- |
| `ccba-excalidraw-diagram` | Thế năng `package-bound` trên `diagram_layout.v1` của `ccba-diagram`. Fence `find-seam --in diagram --out layout --json` phải trả `status == "MATCH"`, `import_path` là `ccba_diagram:apply_smart_layout`. Tám engine layout và `generate_markdown_spec_table` đứng nguyên. Determinism Invariant giữ lệnh cấm Agent tự ghi toạ độ. `index_sha256` tiếp tục ở plan của phiên. `tier: kernel`. GPI `(4.0, 4.0, 3.0, 3.0) = 19.5`. |
| `ccba-xu-ly-van-phong` | Master kernel, `package_path: packages/ccba-ooxml`, `sub_skills` là `ccba-pptx` và `ccba-markdown-document-processing`. Thế năng `package-bound` trên `ooxml_processor.v1`, neo `ccba_ooxml:DocxDocument`. Card nhận `docx`, `xlsx`, `pptx` và cấm import thay thế `docx`, `openpyxl`. Symbol công khai cùng gói gồm `pack_document`, `unpack_document`, `validate_document`, `DeckBuilder`, `build_presentation_from_markdown`, `WordFormFiller`, `recalc_xlsx`. `resources/form-filling.md` đã import `WordFormFiller`. PDF nằm trong `resources/` và `scripts/` của skill này. Card `pdf_preprocessor.v1` thuộc gói khác và đứng ngoài mục posture. `tier: kernel`. GPI `(3.0, 3.0, 1.0, 1.0) = 14.0`. |
| `ccba-pptx` | Sub-skill, `master_skill: xu-ly-van-phong`, `role: sub_skill`. Thế năng `seam-exempt`. Thân bài gọi `python -m ccba_ooxml unpack`, `validate`, `pack` và luồng `html2pptx` qua `scripts/html2pptx.js`. Skill này là caller của gói master, không sở hữu card riêng và không nhận `package_path`. GPI `(3.0, 2.0, 1.0, 1.0) = 12.0`, nhánh Tier 2B, đồng thời nằm trong deadband `[11.5, 12.5)`. |
| `ccba-docs-manager` | SOP kernel năm pha trên đĩa: `repomix_pack.py`, `scripts/maskara.py redact`, backup vào `.md/scratch/backups/`, `validate_docs.py`, cleanup. Pha 3 gọi `ccba-relative-link-patcher` và tối đa 3–5 subagent nghiên cứu module. Thế năng `seam-exempt`. Lời gọi script maskara là caller của script Hub. Card `maskara_scanner.v1` giữ `ccba_maskara:MaskaraScanner`. 16 card đứng yên. GPI `(3.0, 3.0, 1.0, 1.0) = 14.0`. |
| `ccba-academic-writing` | SOP master: IMRAD, CARS, APA 7th và BibTeX, bốn bước thực thi. `scripts/microstructure_audit.py`, `export_paper_to_docx.py`, `scaffold_manuscript.py` là adapter mỏng sang `mdconverter`. Thế năng `seam-exempt`. Card `legal_markdown.v1` giữ `mdconverter:ConversionPipeline` với chiều `pdf, docx → markdown`. Skill này không nhận card đó và không nhận `package_path`. GPI `(4.0, 3.0, 1.0, 1.0) = 16.5`. `role: master_skill` đứng yên. |
| `ccba-copywriting` | SOP master soạn hồ sơ thầu, quyết định, công văn, hợp đồng từ `ccba-xu-ly-van-phong/templates/`, kèm công thức ở `references/copy-formulas.md` và văn phong ở `references/writing-styles.md`. `sub_skills` là `form-template-cleaner` và `ccba-viet-chuyen-nghiep`. Thế năng `seam-exempt`. GPI `(3.0, 3.0, 1.0, 1.0) = 14.0`. |
| `ccba-to-spec` | SOP kernel tổng hợp hội thoại thành spec, nhãn `ready-for-agent`, đường `.md/knowledge/specs/spec-{feature_slug}.md` khi tracker cục bộ. Invariant cắt ticket: blast radius, một Public Deep Seam mỗi ticket, lệnh nghiệm thu tất định. Câu “seams” trong thân bài là phương pháp đặc tả. Thế năng `seam-exempt`. 16 card đứng yên. GPI `(4.0, 2.0, 1.0, 1.0) = 14.5`. |

Đoạn posture của sáu skill mới chứa 0 token dạng `ADR` kèm số. Câu GPI viết bằng ngoặc thường.

Mục posture của `ccba-docs-manager` đứng ngoài các cụm `spawn subagent`, `worker subagent`, `dispatch worker`. Validator chỉ kiểm Single-Writer trên `tier: orchestrator`. Bảy skill giữ `tier: kernel`.

`resources/`, `standards/`, `scripts/`, `templates/`, `examples/` của `ccba-xu-ly-van-phong` đứng nguyên. Đợt này không viết lại `resources/docx.md` hay `resources/xlsx.md`. Mục posture mới nói card và danh sách import bị cấm. Thân bài bốn tầng đứng nguyên.

## 3. COND-02 — tier và GPI

Frontmatter đứng nguyên từng khóa đang có.

| Skill | Khóa giữ nguyên ngoài `name`, `tier`, `bundle`, `command`, `triggers`, `description`, `metadata`, `gpi` |
| :--- | :--- |
| `ccba-excalidraw-diagram` | `disable-model-invocation`, `applies_to`, `user-invocable` |
| `ccba-xu-ly-van-phong` | `role: master_skill`, `package_path: packages/ccba-ooxml`, `sub_skills` |
| `ccba-pptx` | `role: sub_skill`, `master_skill: xu-ly-van-phong`, `when_to_use`, `category`, `keywords`, `license` |
| `ccba-docs-manager` | `applies_to`, `disable-model-invocation`, `user-invocable` |
| `ccba-academic-writing` | `role: master_skill`, `when_to_use`, `keywords`, `disable-model-invocation`, `user-invocable` |
| `ccba-copywriting` | `role: master_skill`, `sub_skills`, `argument-hint`, `license`, `disable-model-invocation`, `user-invocable` |
| `ccba-to-spec` | `disable-model-invocation`, `user-invocable` |

Bảy khối `gpi` giữ dạng nhiều dòng với `s`, `k`, `a`, `p`. Đợt này không thêm khóa `score`. Đợt này không thêm `package_path` cho sáu skill đang vắng khóa đó. Entry catalog của `ccba-excalidraw-diagram` tiếp tục không có `package_path`. Liên kết `package-bound` của skill đó nằm trong thân bài.

## 4. COND-03 — bảng Level 3 và cây phụ

Hygiene trả exit code 1 cho cả YELLOW lẫn RED khi một reference markdown thiếu mặt trong bảng hoặc trong router `INDEX.md` đã được bảng trỏ tới. Bảy bảng sau đứng nguyên.

| Skill | Số dòng | Tệp, đúng thứ tự bảng |
| :--- | :---: | :--- |
| `ccba-academic-writing` | 3 | `references/long_form_chunking.md`, `references/academic_phrasebank.md`, `references/audit_report_format.md` |
| `ccba-copywriting` | 10 | `copy-formulas.md`, `writing-styles.md`, `headline-templates.md`, `email-copy.md`, `landing-page-copy.md`, `cta-patterns.md`, `power-words.md`, `social-media-copy.md`, `viet_chuyen_nghiep_rules.md`, `viet_chuyen_nghiep/INDEX.md` |
| `ccba-docs-manager` | 1 | `references/markdown_hallucination_check.md` |
| `ccba-excalidraw-diagram` | 1 | liên kết Markdown [`references/visual_concepts.md`](references/visual_concepts.md) |
| `ccba-pptx` | 2 | `references/html2pptx.md`, `references/ooxml.md` |
| `ccba-to-spec` | 2 | `references/spec_decomposition.md`, `references/interactive_questionnaire.md` |
| `ccba-xu-ly-van-phong` | 4 | `references/office_standards_overview.md`, `references/docx_engine_guide.md`, `references/docx-js.md`, `references/ooxml.md` |

Hàng `references/viet_chuyen_nghiep/INDEX.md` là router cho các submodule dưới `references/viet_chuyen_nghiep/`. Giữ hàng đó giữ độ phủ hygiene.

Cây phụ đứng ngoài diff:

| Skill | Cây |
| :--- | :--- |
| `ccba-academic-writing` | `references/`, `scripts/` (`microstructure_audit.py`, `export_paper_to_docx.py`, `scaffold_manuscript.py`), `examples/` |
| `ccba-copywriting` | `references/`, `scripts/extract-writing-styles.py`, `templates/` |
| `ccba-docs-manager` | `references/` |
| `ccba-excalidraw-diagram` | `references/` |
| `ccba-pptx` | `references/`, `scripts/` (`html2pptx.js`, `inventory.py`, `rearrange.py`, `replace.py`, `thumbnail.py`) |
| `ccba-to-spec` | `references/` |
| `ccba-xu-ly-van-phong` | `references/`, `resources/`, `standards/`, `scripts/`, `templates/`, `examples/` |

Mục “Bộc Lộ Dần” thứ hai trong `ccba-excalidraw-diagram` và `ccba-xu-ly-van-phong` đứng nguyên. Bảng examples trong thân `ccba-xu-ly-van-phong` đứng nguyên.

## 5. COND-04 — tập token ADR

`sync_hub_adr_matrix.py --check` so `docs/adr/TRACEABILITY_MATRIX.md` với radar quét mọi `SKILL.md`. `docs/adr/` đứng ngoài bốn PR, nên tập số của từng file phải giữ đúng như hiện tại.

| Skill | Số ADR đang có trên đĩa | Việc đợt này làm |
| :--- | :--- | :--- |
| `ccba-excalidraw-diagram` | 0061, hiện nằm trong tiêu đề dòng 75 | Tiêu đề mới không chứa số. Câu đầu của cùng mục nhận token `ADR-0061`. Tập vẫn là `{0061}`. |
| `ccba-xu-ly-van-phong` | rỗng | Mục posture chứa 0 token ADR. |
| `ccba-pptx` | rỗng | Mục posture chứa 0 token ADR. |
| `ccba-docs-manager` | rỗng | Mục posture chứa 0 token ADR. |
| `ccba-academic-writing` | rỗng | Mục posture chứa 0 token ADR. |
| `ccba-copywriting` | rỗng | Mục posture chứa 0 token ADR. |
| `ccba-to-spec` | rỗng | Câu “ADRs” ở bước Explore không kèm số, radar bỏ qua. Mục posture chứa 0 token ADR. |

Khối công thái học của `ccba-excalidraw-diagram` và dòng blast-radius của `ccba-to-spec` giữ nguyên công thức toán đang có. Mục posture mới viết điểm bằng ngoặc thường. Mẫu `$(...)` đứng ngoài bảy file.

## 6. COND-05 — bốn PR và sàn CI

| PR | File được sửa | Nội dung |
| :--- | :--- | :--- |
| **10A** | `ccba-excalidraw-diagram/SKILL.md`, `ccba-xu-ly-van-phong/SKILL.md` | Đổi tiêu đề posture excalidraw, chuyển token `ADR-0061` vào câu đầu. Thêm một mục posture package-bound cho văn phòng. |
| **10B** | `ccba-pptx/SKILL.md`, `ccba-docs-manager/SKILL.md` | Một mục seam-exempt mỗi file. |
| **10C** | `ccba-academic-writing/SKILL.md`, `ccba-copywriting/SKILL.md` | Một mục seam-exempt mỗi file. |
| **10D** | `ccba-to-spec/SKILL.md` | Một mục seam-exempt. |

Mỗi PR chỉ sửa `SKILL.md` của các skill được giao. Khóa từng file:

1. `python scripts/validate_skills.py --file <SKILL.md> --enforce-gpi`
2. `python scripts/governance/audit_skills_hygiene.py --file <skill_dir>`
3. `python -m ccba_harness verify-patch --preset skill --target <SKILL.md>`

Sau khi cả bốn PR có trên đĩa, sàn là `python -m ccba_harness verify-patch --preset ci`. Sàn đạt khi sáu lệnh của preset trả exit code 0.