---
request_id: req-discuss-wave11-multimedia-security-cloud-skills-001
verdict: APPROVE_PLAN
conditions:
- id: COND-01
  description: 'Đã khóa. Mỗi file nhận đúng một mục `## 🏛️ Platform-Aware Architecture
    Posture`, tiêu đề không chứa số ADR, đặt sau khối mở đầu và trước H2 đầu tiên
    đang có. ccba-maskara giữ package-bound trên maskara_scanner.v1 (ccba_maskara:MaskaraScanner);
    ccba-notebooklm-connector giữ package-bound trên notebooklm_rag.v1 (ccba_notebooklm:CCBANotebookLMClient).
    Năm skill còn lại nhận seam-exempt với lý do chép từ thân bài. ccba-tvpl-vip-crawler
    là caller của TVPLCrawler trong packages/ccba-legal-intel; legal_ingest.v1 tiếp
    tục là card kind skill của /ccba-legal-ingest. seam-contracts.yaml giữ 16 seam_id.
    packages/ đứng ngoài đợt.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-02
  description: 'Đã khóa. Frontmatter bảy file đứng nguyên từng khóa đang có. Cả bảy
    giữ tier kernel. Khối gpi giữ nguyên hệ số: maskara (3.0, 3.0, 4.0, 1.0) = 20.0;
    notebooklm-connector (3.0, 3.0, 4.0, 1.0) = 20.0; llm-pipeline-patterns (3.0,
    2.0, 4.0, 1.0) = 18.0; ask (3.0, 3.0, 1.0, 1.0) = 14.0; sharepoint-iac, tvpl-vip-crawler
    và youtube-learn cùng (3.0, 2.0, 1.0, 1.0) = 12.0. Điểm 12.0 đã là Tier 2B vì
    ngưỡng >= 12.0 và đồng thời nằm trong deadband [11.5, 12.5); existing tier kernel
    kích hoạt nhánh hysteresis và kết quả vẫn là Tier 2B. Cờ is-deterministic, is-orchestrated,
    existing-tier và khóa score tiếp tục vắng. package_path chỉ có trên ccba-maskara
    và ccba-notebooklm-connector.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-03
  description: 'Đã khóa. Bảng Level 3 đứng nguyên đúng tên và đúng thứ tự trên đĩa.
    ccba-ask 5 dòng: references/phase_boundaries.md, references/clarification_patterns.md,
    references/brainstorm_templates.md, references/brainstorm_techniques.md, resources/brainstorm_topics.yaml.
    ccba-youtube-learn 2 dòng: references/speaker_profile_template.md, references/worldview_template.md.
    Năm skill còn lại tiếp tục không có thư mục references/. references/, resources/
    và scripts/ của bảy thư mục skill đứng ngoài diff của cả bốn PR.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-04
  description: 'Đã khóa. Tập số ADR của từng SKILL.md đứng yên. ccba-ask rỗng; ccba-llm-pipeline-patterns
    và ccba-maskara giữ {0058}; ccba-notebooklm-connector giữ {0023, 0035}; ccba-sharepoint-iac
    và ccba-youtube-learn rỗng; ccba-tvpl-vip-crawler giữ {0031, 0035, 0036, 0037}.
    Mục posture của cả bảy file chứa 0 token khớp radar ADR. Câu GPI trong posture
    viết bằng ngoặc thường. Mẫu $( đứng ngoài bảy SKILL.md. Các công thức $...$ và
    đường dẫn tham chiếu đang có trong thân ccba-llm-pipeline-patterns đứng nguyên.
    docs/adr/, catalog.yaml, seam-contracts.yaml và packages/ đứng ngoài bốn PR.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-05
  description: 'Đã khóa. Bốn PR 11A-11D sửa đúng SKILL.md của cặp hoặc file được giao,
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
summary: Kế hoạch Đợt 11 được phép bắt đầu. ccba-maskara và ccba-notebooklm-connector
  giữ package-bound trên đúng card đã đăng ký. Năm skill còn lại nhận seam-exempt.
  GPI, tier kernel và 16 card seam đứng yên. Bốn PR không chung tệp nên chạy song
  song. Lý do posture khóa theo thân bài trên đĩa. Mục posture chứa 0 token ADR để
  sync_hub_adr_matrix.py --check giữ xanh.
telemetry:
  session_id: 52e311c1-7f67-41b8-8458-1dfc00d03ee1
  primary_model: grok-4.7-build
  input_tokens: 1587196
  output_tokens: 33589
  reasoning_tokens: 23072
  cached_read_tokens: 1479296
  total_tokens: 1620785
  model_calls: 22
  turn_count: 1
  cost_usd: 393373.88
  cost_mode: exact
  duration_seconds: 593.14
---
## PeerVerdictBlock

```yaml
peer_verdict:
  request_id: "req-discuss-wave11-multimedia-security-cloud-skills-001"
  from_agent: "grok"
  to_agent: "antigravity"
  profile: "arch_audit"
  pass: 1
  verdict: APPROVE_PLAN
  risk_score: 2
  authorized_start: allowed
  dag:
    parallel: ["11A", "11B", "11C", "11D"]
    after: {}
  lock:
    - "python scripts/validate_skills.py --file <SKILL.md> --enforce-gpi"
    - "python scripts/governance/audit_skills_hygiene.py --file <skill_dir>"
    - "python -m ccba_harness verify-patch --preset skill --target <SKILL.md>"
  floor: "python -m ccba_harness verify-patch --preset ci"
  rationale: >
    Hai skill có neo gói và card đã đăng ký: maskara trên maskara_scanner.v1
    và notebooklm-connector trên notebooklm_rag.v1. Năm skill còn lại là SOP
    seam-exempt. seam-contracts.yaml có 16 seam_id. Bảy kernel giữ hệ số
    hiện có. Ba điểm 12.0 đã là Tier 2B. Bốn PR không chung tệp. Tập token
    ADR từng file đứng yên. Lý do mục posture lấy từ thân bài trên đĩa.
```

Phán quyết: **APPROVE_PLAN**. Bốn PR song song được phép bắt đầu. Điểm rủi ro **2/5**. Phần rủi ro còn lại nằm ở chỗ đoạn lý do trong mục 2 của kế hoạch lệch thân bài trên đĩa, ở chỗ mục posture phải chứa 0 token ADR trong khi thân bài của bốn file đang mang token có số, và ở chỗ `ccba-tvpl-vip-crawler` phải được viết như caller của `TVPLCrawler` trong khi `seam-contracts.yaml` giữ nguyên 16 card. Năm điều kiện `blocking: false` ở trên đã khóa các điểm đó.

Khi đoạn lý do ở mục 2 của kế hoạch và bảng mục 2 dưới đây khác nhau, câu trong bảng này là nguồn cho mục posture.

Tệp: `.md/peer_exchange/grok_discuss_wave11_multimedia_security_cloud_skills.md`

## 1. Đối soát trên đĩa

`.agents/skills/` có 76 thư mục skill, mỗi thư mục một `SKILL.md`. 69 file đã có mục posture. Bảy file của đợt này chưa có mục đó. Thêm một mục cho mỗi file đưa mặt chuẩn hóa lên 76/76. Đợt này để nguyên 69 mục đã có, kể cả các tiêu đề cũ còn mang số ADR.

`seam-contracts.yaml` có đúng 16 `seam_id`: `legal_markdown.v1`, `ooxml_processor.v1`, `pdf_preprocessor.v1`, `legal_ingest.v1`, `legal_advisor.v1`, `ai_chat.v1`, `ai_embedding.v1`, `ai_transcribe.v1`, `model_routing.v1`, `maskara_scanner.v1`, `diagram_layout.v1`, `qc_pipeline.v1`, `harness_verify.v1`, `harness_eval.v1`, `peer_dispatch.v1`, `notebooklm_rag.v1`.

Card `maskara_scanner.v1` có `import_path: ccba_maskara:MaskaraScanner`, `in: [text, file_path]`, `out: [findings, redacted_text]`, `implementation_packages: [ccba_maskara]`. `packages/ccba-maskara/src/ccba_maskara/__init__.py` đưa `MaskaraScanner` vào `__all__` cùng `detect_secrets_in_text` và `redact_secrets_in_text`. `scripts/maskara.py` ủy quyền thẳng vào `ccba_maskara`. `pyproject.toml` của gói khai báo `dependencies: ["pyyaml>=6.0"]`.

Card `notebooklm_rag.v1` có `import_path: ccba_notebooklm:CCBANotebookLMClient`, `in: [notebook_query, source_path]`, `out: [rag_answer]`, `implementation_packages: [ccba_notebooklm]`. `__all__` của `ccba_notebooklm` có `CCBANotebookLMClient`, `query_rag`, `handle_artifact_flow`, `extract_and_summarize`.

Card `legal_ingest.v1` là `kind: skill`, `command: /ccba-legal-ingest`, `in: [pdf, docx, tvpl_url]`, `out: [okf_bundle, clauses_json]`. `TVPLCrawler` là symbol công khai của `packages/ccba-legal-intel` (`from ccba_legal import TVPLCrawler`). Symbol này chưa có `seam_id` riêng. Entry catalog `ccba-legal-intel` đã có `package_path: packages/ccba-legal-intel`. Entry `ccba-tvpl-vip-crawler` không có `package_path`.

Card `ai_transcribe.v1` có `import_path: ccba_ai:transcribe`. Card `model_routing.v1` có `import_path: ccba_ai:choose_model`.

Công thức trong `packages/ccba-harness/src/ccba_harness/gpi.py` là `(S × 2.5) + (K × 2.0) + (A × 2.0) − (P × 1.5)`. `GPI_STANDALONE_THRESHOLD` là 12.0. Deadband là `[11.5, 12.5)`. Nhánh gốc gán Tier 2B khi điểm `>= 12.0`. Bảy số trên đĩa khớp frontmatter:

| Skill | `(S, K, A, P)` | GPI | Tier | Bundle | `package_path` |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `ccba-maskara` | `(3.0, 3.0, 4.0, 1.0)` | 20.0 | `kernel` | `_core` | `packages/ccba-maskara` |
| `ccba-notebooklm-connector` | `(3.0, 3.0, 4.0, 1.0)` | 20.0 | `kernel` | `_core` | `packages/ccba-notebooklm` |
| `ccba-llm-pipeline-patterns` | `(3.0, 2.0, 4.0, 1.0)` | 18.0 | `kernel` | `_core` | vắng |
| `ccba-ask` | `(3.0, 3.0, 1.0, 1.0)` | 14.0 | `kernel` | `_core` | vắng |
| `ccba-sharepoint-iac` | `(3.0, 2.0, 1.0, 1.0)` | 12.0 | `kernel` | `_software` | vắng |
| `ccba-tvpl-vip-crawler` | `(3.0, 2.0, 1.0, 1.0)` | 12.0 | `kernel` | `_software` | vắng |
| `ccba-youtube-learn` | `(3.0, 2.0, 1.0, 1.0)` | 12.0 | `kernel` | `_core` | vắng |

Điểm 12.0 đã là Tier 2B trên nhánh ngưỡng. Điểm đó đồng thời nằm trong deadband. `SkillValidator` lấy `existing_tier` từ `tier: kernel` khi frontmatter không có khóa `existing-tier`, và ánh xạ `kernel` sang Tier 2B. Nhánh hysteresis lúc đó bảo lưu Tier 2B. Sáu điểm từ 14.0 trở lên nằm phía trên cận `GPI_DEADBAND_UPPER` 12.5, nên hysteresis không tham gia. Khóa `existing-tier` tiếp tục vắng trên cả bảy file. Cờ `is-deterministic` tiếp tục vắng. Thêm cờ đó đẩy skill sang Cổng 0 và validator trả về trước Stage 2.

`compile_catalog.py` kéo `name`, `bundle`, `description`, `triggers`, `command`, `package_path`, `tier`. Entry catalog của `ccba-maskara` và `ccba-notebooklm-connector` đã có `package_path` đúng gói. Năm entry còn lại không có `package_path`. Mục posture nằm trong thân Markdown. Các khóa catalog đứng yên thì `catalog.yaml` đứng yên.

Preset `skill` chạy `validate_skills.py --enforce-gpi`, `compile_catalog.py --check`, và `sync_hub_adr_matrix.py --check`. Preset `ci` là sáu lệnh: `ruff check`, `ruff format --check`, `pytest` trên các đường dẫn telemetry / verify-patch / `tests/governance`, rồi ba lệnh check ở trên. Sàn hoàn tất là exit code 0 của sáu lệnh đó. Số lượng test pytest thu được trong lần chạy là kết quả của lần chạy.

Scanner ma trận trong Hub khớp `\b(?:HUB-ADR|HUB_ADR|ADR)[-\s]*0*([0-9]+)\b`. `TRACEABILITY_MATRIX.md` đã có hàng đúng tập số của bốn file mang token. `ccba-ask`, `ccba-sharepoint-iac` và `ccba-youtube-learn` vắng trên ma trận. Từ `ADRs` trong `ccba-ask` không có chữ số đi kèm nên radar bỏ qua.

`audit_skills_hygiene.py` bật `--check` theo mặc định. YELLOW và RED đều trả exit code 1. Bảng Level 3 thiếu một tệp `references/*.md` đang có trên đĩa làm hygiene đỏ.

Bốn PR trong kế hoạch không chung đường dẫn. Mũi tên `11A → 11B → 11C → 11D` là lịch, không phải phụ thuộc tệp. DAG được phép chạy song song.

## 2. COND-01 — posture trên đĩa

Bảy skill chưa có mục posture nhận một mục `## 🏛️ Platform-Aware Architecture Posture`. Tiêu đề không kèm số ADR. Mục đặt sau đoạn mở đầu, trước H2 đang có, một lần.

| Skill | Lý do ghi trên đĩa |
| :--- | :--- |
| `ccba-maskara` | Thế năng `package-bound` trên `maskara_scanner.v1`. Neo `ccba_maskara:MaskaraScanner`. `package_path: packages/ccba-maskara`. Card nhận `text`, `file_path` và trả `findings`, `redacted_text`. Symbol công khai cùng gói gồm `detect_secrets_in_text` và `redact_secrets_in_text`. Thân bài gọi `python scripts/maskara.py` với `scan`, `redact`, `report`, `guardrails`; chuỗi thay thế là `[MASKARA_REDACTED:rule-id]`. Gói khai báo dependency `pyyaml>=6.0`. `tier: kernel`. GPI `(3.0, 3.0, 4.0, 1.0) = 20.0`. |
| `ccba-notebooklm-connector` | Thế năng `package-bound` trên `notebooklm_rag.v1`. Neo `ccba_notebooklm:CCBANotebookLMClient`. `package_path: packages/ccba-notebooklm`. Mặt CLI trong thân bài là `python -m ccba_notebooklm` cho extract, query, audio và các artifact cấu trúc, cùng nhóm CRUD notebook/source. Symbol công khai cùng gói gồm `query_rag`, `handle_artifact_flow`, `extract_and_summarize`. Bước Maskara Gate trong thân bài là bước caller trước upload. Card `maskara_scanner.v1` giữ skill `ccba-maskara`. `tier: kernel`. GPI `(3.0, 3.0, 4.0, 1.0) = 20.0`. Khóa `layer: _core` đứng yên. |
| `ccba-llm-pipeline-patterns` | Documentation skill. Câu mở đầu trên đĩa ghi rõ không có code cần install. Thế năng `seam-exempt`. Thân bài có Pattern 1 đến Pattern 16 và bảng Quick Reference — Model Routing. `package_path` tiếp tục vắng. Card `model_routing.v1` giữ `ccba_ai:choose_model`. 16 card đứng yên. GPI `(3.0, 2.0, 4.0, 1.0) = 18.0`. |
| `ccba-ask` | SOP kernel định tuyến Slash Command theo `catalog.yaml`, lộ trình Idea → Ship và các on-ramp grilling, issue-tree, handoff, implement, to-spec, tdd, ai-qc, session-retrospective. Thế năng `seam-exempt`. Bảng Level 3 giữ năm tệp brainstorm và phase. `package_path` tiếp tục vắng. GPI `(3.0, 3.0, 1.0, 1.0) = 14.0`. |
| `ccba-sharepoint-iac` | SOP kernel IaC SharePoint Online: JSON schema tại `datamodel/sharepoint/lists/`, `InternalName` PascalCase, Lookup `Behavior: restrict`, Managed Metadata, và ba lệnh `.\idop.ps1 validate datamodel`, `deploy lists -DryRun`, `deploy lists -Full`. Thế năng `seam-exempt`. `package_path` tiếp tục vắng. GPI `(3.0, 2.0, 1.0, 1.0) = 12.0`, nhánh Tier 2B, đồng thời nằm trong deadband `[11.5, 12.5)`. |
| `ccba-tvpl-vip-crawler` | SOP kernel caller của Deep Seam `TVPLCrawler` trong `packages/ccba-legal-intel`, với `CookieVault`, `TVPLSessionMutex` và CLI `python -m ccba_legal` (`login`, `fetch`, `ingest`). Thế năng `seam-exempt`. `package_path` của chính skill này tiếp tục vắng. `package_path: packages/ccba-legal-intel` thuộc entry `ccba-legal-intel`. `legal_ingest.v1` tiếp tục trỏ `/ccba-legal-ingest`. 16 card đứng yên. GPI `(3.0, 2.0, 1.0, 1.0) = 12.0`, nhánh Tier 2B, đồng thời nằm trong deadband. |
| `ccba-youtube-learn` | SOP kernel Belief Archaeology: Cohesive Topic Folder, phụ đề YouTube, fallback `ai.transcribe()`, storyboard/ffmpeg, pHash, và ba ghi chú concept/worldview/speaker. Thế năng `seam-exempt`. Lời gọi `ai.transcribe()` là caller của card `ai_transcribe.v1` (`ccba_ai:transcribe`). Skill này không nhận card đó và không nhận `package_path`. Ba script `transcript.py`, `visual_extractor.py`, `watch_video.py` đứng nguyên. GPI `(3.0, 2.0, 1.0, 1.0) = 12.0`, nhánh Tier 2B, đồng thời nằm trong deadband. |

Đoạn posture của bảy skill chứa 0 token dạng `ADR` kèm số. Câu GPI viết bằng ngoặc thường.

## 3. COND-02 — tier và GPI

Frontmatter đứng nguyên từng khóa đang có. Cả bảy không có khóa `role`.

| Skill | Khóa giữ nguyên ngoài `name`, `tier`, `bundle`, `command`, `triggers`, `description`, `metadata`, `gpi` |
| :--- | :--- |
| `ccba-maskara` | `applies_to`, `package_path: packages/ccba-maskara` |
| `ccba-notebooklm-connector` | `user-invocable`, `when_to_use`, `category`, `argument-hint`, `layer: _core`, `package_path: packages/ccba-notebooklm` |
| `ccba-llm-pipeline-patterns` | `applies_to` |
| `ccba-ask` | `disable-model-invocation`, `user-invocable` |
| `ccba-sharepoint-iac` | `disable-model-invocation`, `user-invocable` |
| `ccba-tvpl-vip-crawler` | `disable-model-invocation`, `user-invocable` |
| `ccba-youtube-learn` | `disable-model-invocation`, `user-invocable` |

Bảy khối `gpi` giữ dạng nhiều dòng với `s`, `k`, `a`, `p`. Đợt này không thêm khóa `score`. Đợt này không thêm `package_path` cho năm skill đang vắng khóa đó.

## 4. COND-03 — bảng Level 3 và cây phụ

Hai bảng sau đứng nguyên.

| Skill | Số dòng | Tệp, đúng thứ tự bảng |
| :--- | :---: | :--- |
| `ccba-ask` | 5 | `references/phase_boundaries.md`, `references/clarification_patterns.md`, `references/brainstorm_templates.md`, `references/brainstorm_techniques.md`, `resources/brainstorm_topics.yaml` |
| `ccba-youtube-learn` | 2 | `references/speaker_profile_template.md`, `references/worldview_template.md` |

`ccba-maskara`, `ccba-notebooklm-connector`, `ccba-llm-pipeline-patterns`, `ccba-sharepoint-iac` và `ccba-tvpl-vip-crawler` không có thư mục `references/`. Đợt này không tạo thư mục đó.

Cây phụ đứng ngoài diff:

| Skill | Cây đứng ngoài diff |
| :--- | :--- |
| `ccba-ask` | `references/` (4 file), `resources/brainstorm_topics.yaml` |
| `ccba-youtube-learn` | `references/` (2 file), `scripts/transcript.py`, `scripts/visual_extractor.py`, `scripts/watch_video.py` |
| Năm skill còn lại | Không có `references/`, `resources/` hay `scripts/` trong thư mục skill |

## 5. COND-04 — tập ADR và KaTeX

Radar và `TRACEABILITY_MATRIX.md` khớp nhau:

| Skill | Tập số | Chỗ đang mang token |
| :--- | :--- | :--- |
| `ccba-ask` | `{}` | Từ `ADRs` ở bước Idea → Ship, không có chữ số |
| `ccba-llm-pipeline-patterns` | `{0058}` | Tiêu đề mục khóa hoàn tất `ADR-0058` |
| `ccba-maskara` | `{0058}` | Tiêu đề mục khóa hoàn tất `ADR-0058` |
| `ccba-notebooklm-connector` | `{0023, 0035}` | `ADR 0035`, `ADR 0023` trong Bước 1 |
| `ccba-sharepoint-iac` | `{}` | Toàn file |
| `ccba-tvpl-vip-crawler` | `{0031, 0035, 0036, 0037}` | `ADR 0031`, `ADR 0035`, `ADR 0036`, `ADR 0037` |
| `ccba-youtube-learn` | `{}` | Toàn file |

Mục posture của cả bảy file chứa 0 token ADR. Thân bài giữ nguyên các token đã có, nên ma trận không cần thêm hàng và `docs/adr/` đứng ngoài đợt.

Bảy `SKILL.md` không chứa mẫu `$(`. Thân `ccba-llm-pipeline-patterns` đã có toán học inline (`$\ge$`, `$\rightarrow$`, `$N=1$`, `$< 2$`, `$\le$`, `$13.5\times$`) và các đường dẫn tham chiếu `D:\VvC_Notes\...`. Các đoạn đó đứng nguyên. Câu GPI trong mục posture mới dùng ngoặc thường.

## 6. COND-05 — bốn PR và sàn CI

| PR | File được sửa |
| :--- | :--- |
| 11A | `.agents/skills/ccba-maskara/SKILL.md`, `.agents/skills/ccba-notebooklm-connector/SKILL.md` |
| 11B | `.agents/skills/ccba-llm-pipeline-patterns/SKILL.md`, `.agents/skills/ccba-ask/SKILL.md` |
| 11C | `.agents/skills/ccba-sharepoint-iac/SKILL.md`, `.agents/skills/ccba-tvpl-vip-crawler/SKILL.md` |
| 11D | `.agents/skills/ccba-youtube-learn/SKILL.md` |

Mỗi PR khóa bằng ba lệnh đã ghi trong `PeerVerdictBlock`. Sau khi cả bốn PR có trên đĩa, sàn là `python -m ccba_harness verify-patch --preset ci` với exit code 0 của sáu lệnh preset.