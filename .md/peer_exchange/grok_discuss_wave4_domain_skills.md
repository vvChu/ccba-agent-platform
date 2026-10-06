---
request_id: req-discuss-wave4a-bigbim-consulting-001
verdict: REVISE_PLAN
conditions:
- id: COND-01
  description: Bốn skill BIM (classification, governance, rase, risk) nhận đúng một
    posture seam-exempt. Catalog không có card IFC, Uniclass, RASE hay governance.
    ifcopenshell không phải seam nền tảng. Mỗi mục posture ghi lý do riêng của skill
    đó, cấm find-seam bằng từ khóa, cấm thêm script, cấm dán index_sha256. Nhánh embedding
    hoặc chat, khi được chạy, đi ai_embedding.v1 và model_routing.v1. Gỡ URL https://example.com.
    Thiếu file KB ngoài repo thì dừng; cấm viết bảng Uniclass hoặc điều ISO để lấp
    chỗ trống.
  blocking: true
  source_profile: arch_audit
  source_profiles: []
- id: COND-02
  description: Kế hoạch thực thi dùng GPI = 2.5*S + 2*K + 2*A - 1.5*P. classification,
    governance và risk = 22.5. rase = 24.5. vbpl-digest, completion-checklist và seminar-builder
    = 18.0. ccba-design = 16.5. Giữ nguyên khối gpi trong frontmatter. Cả tám skill
    vẫn tier kernel vì mọi điểm đều >= 12.
  blocking: true
  source_profile: arch_audit
  source_profiles: []
- id: COND-03
  description: bigbim-vbpl-digest và ccba-completion-checklist nhận compose-existing.
    Trích dẫn VBPL đi qua python -m ccba_legal query và get-clause. Dán nguyên văn
    predicate hiệu lực Mục 5 đã chốt ở Đợt 3. Gỡ sổ số hiệu trong description và mục
    Legal Basis. Chunk NĐ 175 dưới bigbim_method_path hết vai trò nguồn hiệu lực.
    checklist_master.yaml giữ vai trò khung hạng mục; mỗi lần trích căn cứ phải qua
    predicate. Xuất docx đi ooxml_processor.v1 (ccba_ooxml:DocxDocument). Card chưa
    có thao tác checklist thì xuất Markdown và dừng. Cấm python-docx.
  blocking: true
  source_profile: arch_audit
  source_profiles: []
- id: COND-04
  description: ccba-seminar-builder nhận compose-existing trên ooxml_processor.v1,
    gọi build_presentation_from_markdown và python -m ccba_ooxml build-deck. Sửa đường
    dẫn template sang resources/. Archive nằm ở .md/seminars/. Bỏ bước ghi seminars
    vào legal_registry.yaml. PR này không sửa seam-contracts.yaml.
  blocking: true
  source_profile: arch_audit
  source_profiles: []
- id: COND-05
  description: 'ccba-design là PR riêng, posture compose-existing trên ai_chat.v1
    (ccba_ai:ai) và model_routing.v1 (ccba_ai:choose_model). Gỡ khối Setup GEMINI_API_KEY,
    lệnh pip install google-genai, và mọi chuỗi gemini-* trong SKILL.md cùng references/logo-design.md,
    references/cip-design.md, references/icon-design.md. llm_adapter.py hết fallback
    Google GenAI và CLI cục bộ trên lối chữ; lỗi gateway thì dừng. Lối sinh ảnh trong
    scripts/logo/generate.py, scripts/icon/generate.py và scripts/cip/generate.py
    chưa có card: cách ly có hạn với seam_id=ai_chat.v1, reason, until và issue, hoặc
    tắt lối đó. Cấm sửa packages/. Cấm chú thích allow-raw-model trong Markdown để
    giữ chuỗi model.'
  blocking: true
  source_profile: arch_audit
  source_profiles: []
- id: COND-06
  description: 'Chia 4 PR: 4A1 bốn skill BIM, 4A2 hai skill pháp lý, 4A3 seminar-builder,
    4A4 ccba-design. Bốn PR không chung file nên chạy song song sau khi kế hoạch ghi
    đủ COND-01 đến COND-06. Mỗi PR kết thúc bằng python scripts/validate_skills.py
    --file <SKILL.md> --enforce-gpi và python -m ccba_harness verify-patch. Mã thoát
    khác 0 thì chưa xong. Catalog đã commit thì regenerate bằng lệnh có sẵn của repo;
    cấm sửa tay .md/knowledge/skills_compiled.md.'
  blocking: true
  source_profile: arch_audit
  source_profiles: []
risk_score: 3
effort: L
summary: Bốn skill BIM nhận seam-exempt vì catalog không có card IFC/Uniclass. Hai
  skill pháp lý giữ compose-existing với predicate Mục 5 và bỏ sổ hiệu lực viết tay.
  Seminar gắn ooxml_processor.v1. ccba-design tách PR riêng để cắt lối google-genai.
  Kế hoạch 3 PR cần thành 4.
telemetry:
  session_id: 9da556e4-a2af-4930-85c0-40f9d4a6040f
  primary_model: grok-4.7-build
  input_tokens: 259078
  output_tokens: 24307
  reasoning_tokens: 17957
  cached_read_tokens: 197120
  total_tokens: 283385
  model_calls: 7
  turn_count: 1
  cost_usd: 125228.12
  cost_mode: exact
  duration_seconds: 331.08
---
# Phán quyết phản biện Đợt 4A — 8 skills BIGBIM & Consulting

**Hồ sơ:** `req-discuss-wave4a-bigbim-consulting-001`  
**Bên hỏi:** `antigravity`  
**Bên phán quyết:** `grok` (Grok 4.7, hồ sơ `arch_audit`)  
**Căn cứ:** ADR-0057, ADR-0058, ADR-0059, ADR-0061, `seam-contracts.yaml`, predicate Mục 5 đã `APPROVE` tại `req-audit-wave3-core-skills-004`, frontmatter và thân 8 `SKILL.md`  
**Tệp:** `.md/peer_exchange/grok_discuss_wave4_domain_skills.md`

**Phán quyết: `REVISE_PLAN`.** Tách Đợt 4A khỏi Đợt 4B là đúng bán kính. Gán `compose-existing` cho cả tám skill sẽ đóng dấu hợp đồng giả lên bốn skill BIM và để lối `google-genai` của `ccba-design` sống trong script. Điểm rủi ro **3/5**.

## Đối chiếu đã dùng cho phán quyết

| Việc | Kết quả |
| :--- | :--- |
| `seam-contracts.yaml` | Có `ooxml_processor.v1`, `ai_chat.v1`, `ai_embedding.v1`, `model_routing.v1`, `legal_ingest.v1`, `legal_advisor.v1`. Không có card IFC, Uniclass, RASE, governance, hay sinh ảnh. |
| Công thức GPI | `scripts/governance/compile_skills_docs.py` tính `(S * 2.5) + (K * 2.0) + (A * 2.0) - (P * 1.5)`. |
| `ccba-design` | `SKILL.md` có khối Setup `$env:GEMINI_API_KEY` và `pip install google-genai`, cộng chuỗi `gemini-2.5-flash-image`, `gemini-3-pro-image-preview`, `gemini-3.1-pro-preview`. Cùng mẫu nằm ở `references/logo-design.md`, `references/cip-design.md`, `references/icon-design.md`. `scripts/llm_adapter.py` gọi gateway rồi fallback `google-genai`. `scripts/logo/generate.py`, `scripts/icon/generate.py`, `scripts/cip/generate.py` gọi SDK trực tiếp. |
| Seminar | `build_presentation_from_markdown` và CLI `build-deck` có trong `ccba_ooxml` (`__all__` và test). Thân skill đang trỏ `templates/*.md`; trên đĩa file nằm ở `resources/`. |
| Checklist | Mục Legal Basis ghi sẵn số hiệu. Phần phụ thuộc ghi `python-docx`. Card `ooxml_processor.v1` cấm import thay thế `docx`. |
| VBPL digest | Luồng thực thi đọc chunk `175_2024_ND-CP_*` dưới `[bigbim_method_path]`. |

## GPI

Khối `gpi` trong frontmatter khớp bảng đề xuất. Tổng điểm của bốn skill BIM thì lệch, vì trọng số `A` trong đề xuất đang là 1 trong khi harness dùng 2.

| Skill | `S, K, A, P` | GPI đúng | Trong đề xuất |
| :--- | :--- | ---: | ---: |
| `bigbim-classification` | 4, 3, 4, 1 | **22.5** | 18.5 |
| `bigbim-governance` | 4, 3, 4, 1 | **22.5** | 18.5 |
| `bigbim-rase` | 4, 4, 4, 1 | **24.5** | 20.5 |
| `bigbim-risk` | 4, 3, 4, 1 | **22.5** | 18.5 |
| `bigbim-vbpl-digest` | 3, 2, 4, 1 | **18.0** | 18.0 |
| `ccba-completion-checklist` | 3, 2, 4, 1 | **18.0** | 18.0 |
| `ccba-seminar-builder` | 3, 2, 4, 1 | **18.0** | 18.0 |
| `ccba-design` | 4, 3, 1, 1 | **16.5** | 16.5 |

`docs/skills/bigbim-rase.md` đã ghi 24.50. Đợt 4A giữ nguyên bốn hệ số. Cả tám điểm đều trên ngưỡng 12, nên tier `kernel` đứng yên. Chạy `evaluate-gpi` chỉ khi một PR đổi hệ số.

## 1. Posture nhóm BIGBIM

Bốn skill `bigbim-classification`, `bigbim-governance`, `bigbim-rase`, `bigbim-risk` nhận **`seam-exempt`**.

Lý do đề xuất đưa ra cho `compose-existing` — hợp thành từ ifcopenshell và “không có Seam riêng trong packages” — là đúng hồ sơ của miễn trừ seam. `compose-existing` chỉ đứng khi mục posture liệt kê card có `status: MATCH`. Từ khóa `ifc` / `uniclass` sẽ ra `KEYWORD_HINT`. Đợt 3 đã cấm coi hint đó là hợp đồng.

Mỗi skill một đoạn lý do riêng:

| Skill | Lý do miễn trừ | Câu đi kèm trong cùng mục |
| :--- | :--- | :--- |
| `bigbim-classification` | Quy tắc Uniclass / ISO 19650 / IFC Alignment là SOP. Không có card phân loại. | Câu “trích xuất bằng ifcopenshell” và nhánh BERT dừng tại ranh giới này. PR skill cấm thêm script. Embedding, khi chạy, đi `ai_embedding.v1` (`ccba_ai:embed`). Chat đi `model_routing.v1`. |
| `bigbim-governance` | Rào chắn Sợi Chỉ Vàng / Đỏ và Unique ID là phán đoán trên hồ sơ. | Gỡ các URL `https://example.com/bigbim-governance/...`. |
| `bigbim-rase` | Ma trận RASE và ánh xạ Pset/Qto là SOP schema. | Câu hỏi điều khoản luật đi sang `bigbim-vbpl-digest`. Skill này hết vai trò kho chunk ISO. |
| `bigbim-risk` | Phát hiện xung đột thông tin ở V2 là SOP phối hợp. | Ngưỡng 900 mm và 150 mm là hằng phương pháp BIGBIM. Cấm thêm ngưỡng QCVN mới vào `SKILL.md`. |

Bốn skill này mỗi skill chỉ có `SKILL.md`. Link KB ngoài repo giữ dạng token chưa giải. Token trống hoặc file vắng thì dừng và hỏi người dùng. Cấm sinh `references/` bằng bảng mã hoặc điều khoản viết tay.

`seam-exempt` ở đây miễn card nghiệp vụ BIM. Nó vẫn để lối model đi hai card AI đã có, và chỉ khi nhánh đó thực sự chạy.

## 2. `ccba-design`

Việc cần làm là một PR sửa cả ba lớp: `SKILL.md`, ba file reference đang cài `google-genai`, và script đang gọi SDK. Gỡ riêng khối ví dụ trong `SKILL.md` để lại lối vận hành.

Posture của cả skill là **`compose-existing`**, bám hai card chữ:

- `ai_chat.v1` → `ccba_ai:ai`
- `model_routing.v1` → `ccba_ai:choose_model`

`package-bound` cho toàn skill thì rộng hơn bề mặt thật. Skill còn HTML, CSV, BM25 và sinh ảnh. Catalog không có card ảnh.

`scripts/llm_adapter.py` đã thử gateway trước, rồi nhận `GEMINI_API_KEY`, rồi nhảy sang CLI `gemini` / `copilot`. Lối chữ sau PR này dừng khi gateway lỗi. `get_target_model()` hết quyền đưa chuỗi `gemini-*` hoặc `CCBA_MODEL` thô vào `ai.chat`.

Lối ảnh trong `logo/generate.py`, `icon/generate.py` và `cip/generate.py` (kể cả nhánh sửa ảnh bằng PIL) chưa có seam. PR skill cấm sửa `packages/` để bịa card ảnh. Hai lối hợp lệ:

1. Cách ly có hạn ngay tại call site: `# ccba:quarantine seam_id=ai_chat.v1 reason=image-gen-absent-from-catalog until=YYYY-MM-DD issue=...`
2. Tắt sinh ảnh và nói rõ trong mô tả PR rằng gateway hiện chưa có card ảnh.

Cách ly không hạn, hoặc để fallback SDK làm lối thành công, trái ADR-0061. Chú thích `# ccba:allow-raw-model` trong Markdown không hợp thức hóa chuỗi model. Câu “When scripts fail, try to fix them directly” rời khỏi `SKILL.md` trong cùng PR. Placeholder `[hub_path]` trong lệnh đổi thành biến `CCBA_HUB_PATH`.

## 3. SSOT hiệu lực cho hai skill pháp lý

Áp dụng nguyên văn predicate Mục 5 đã duyệt ở Đợt 3 là đủ cho **cổng trích dẫn**, và mới đủ khi nó thay sổ số hiệu chứ không ngồi cạnh sổ đó.

Câu dán vào cả hai skill:

> Bảo đảm trạng thái hiệu lực chuẩn hóa `ACTIVE` (bao gồm `current` / `active` qua `normalize_doc_status`) và các trường bị thay `superseded_by`, `replaced_by`, `replaced_by_docs` trống, đồng thời mã văn bản vắng mặt trong danh sách thay thế của mọi văn bản kế nhiệm. Văn bản kế nhiệm giữ `supersedes`, `replaces`, `replaced_docs`, `relations.*` vẫn thuộc tập được trích dẫn.

Đi kèm cổng đó:

- `bigbim-vbpl-digest`: luồng thực thi đọc `python -m ccba_legal query` và `get-clause`. Nguồn điều khoản là bundle OKF có `pdf_sha256`. Description hết khóa cứng “NĐ 175/2024”. Trigger `NĐ 175` được giữ như alias lịch sử. Bảng chunk `175_2024_ND-CP_*` hết vai trò SSOT. ISO 19650 chỉ được trích khi đã có bundle nguồn và hash; thiếu file thì dừng và xin nguồn. Cấm đổi mô tả từ 175 sang một số hiệu kế nhiệm viết tay, kể cả số đang xuất hiện trong khảo sát.
- `ccba-completion-checklist`: mục Legal Basis (các số hiệu đang ghi cho mốc 01/07/2026 và khối chuyển tiếp) rời vai trò căn cứ. Bước cập nhật đang nói `superseded` / `current` và “không đổi thì dùng YAML tĩnh” đổi sang predicate trên. `resources/checklist_master.yaml` vẫn là khung hạng mục hồ sơ. PR này không viết lại YAML và không chép phụ lục nghị định vào skill. Xuất Word đi `ooxml_processor.v1`. `python-docx` nằm trong `forbidden_substitute_imports` của card đó. Card chưa có hàm dựng checklist thì xuất Markdown, chạy `verify-patch --preset doc`, và dừng.

## 4. Bốn PR

Nhóm 4A1 và 4A2 trong đề xuất giữ nguyên. Nhóm truyền thông và thiết kế tách làm hai, vì seminar là một `SKILL.md` còn design đổi hành vi script và đường khóa API.

| PR | File | Việc trong PR | Để ngoài PR |
| :--- | :--- | :--- | :--- |
| **4A1** | Bốn `SKILL.md` BIM | Posture `seam-exempt`, lý do riêng từng skill. Gỡ `example.com`. Câu dừng khi KB ngoài thiếu. RASE trỏ câu hỏi luật sang vbpl-digest. | Không tạo card IFC. Không thêm script ifcopenshell. Không sinh bài KB. Không đổi hệ số GPI. |
| **4A2** | `bigbim-vbpl-digest/SKILL.md`, `ccba-completion-checklist/SKILL.md` | Posture `compose-existing`. Predicate Mục 5. Gỡ sổ hiệu lực và luồng chunk-là-SSOT. Docx theo `ccba_ooxml:DocxDocument` hoặc dừng ở Markdown. | Không sửa `legal_registry.yaml`. Không viết lại `checklist_master.yaml`. Không sửa `ccba_legal`. |
| **4A3** | `ccba-seminar-builder/SKILL.md` | Posture `compose-existing` trên `ooxml_processor.v1`. Giữ `build_presentation_from_markdown` và `build-deck`. Đổi `templates/` thành `resources/`. Archive tại `.md/seminars/`. | Không gắn seam pháp lý. Không ghi `seminars:` vào `legal_registry.yaml`. Không sửa `seam-contracts.yaml`. |
| **4A4** | Cây `ccba-design` (`SKILL.md`, ba reference, `llm_adapter.py`, ba `generate.py`) | Posture `compose-existing` trên `ai_chat.v1` và `model_routing.v1`. Cắt Setup key, fallback chữ, và chuỗi model thô. Ảnh: quarantine có hạn hoặc tắt. | Không sửa `packages/ccba-ai`. Không gộp với 4A3. Không quét regex `gemini` toàn repo. |

Bốn PR không chung file. Sau khi kế hoạch ghi đủ sáu điều kiện, chúng chạy song song. Mỗi PR tự xong bằng:

```bash
python scripts/validate_skills.py --file <SKILL.md> --enforce-gpi
python -m ccba_harness verify-patch
```

Mã thoát khác 0 thì chưa được báo xong (ADR-0058). Phán quyết này chưa chạy hai lệnh đó.

## Cạm bẫy cần giữ

1. **Biên lai giả.** `find-seam` bằng từ khóa BIM trả `KEYWORD_HINT`. Hash `index_sha256` dán trong skill sẽ thành mỏ neo ngay lần compile catalog sau. Receipt chỉ nằm trong plan của phiên.
2. **Một đoạn posture nhân bốn.** Bốn lý do miễn trừ khác nhau. Đoạn chung “hợp thành từ ifcopenshell” kéo governance và risk vào một thư viện chúng không gọi.
3. **Card OOXML và symbol deck.** `import_path` của card là `ccba_ooxml:DocxDocument`. `build_presentation_from_markdown` vẫn là symbol công khai, có test. Skill được gọi symbol đó. Việc `capability.out` của card chưa liệt kê `pptx` thuộc PR package sau, ngoài Đợt 4A.
4. **Sổ hiệu lực thứ hai.** Description, trigger-là-luồng-thực-thi, mục Legal Basis, và chunk `bigbim_method_path` là bốn bản sao hiệu lực. Predicate Mục 5 chỉ còn một cửa trên hai skill pháp lý.
5. **`legal_registry.yaml`.** Seminar đang bảo agent ghi trường `seminars:` vào sổ pháp lý. 4A3 gỡ chỉ thị đó. 4A2 không đụng file sổ.
6. **Quét model cả đợt.** Chuỗi `gemini-*` đã xác nhận nằm trong cây `ccba-design`. PR 4A4 sửa đúng các file đó. Comment Markdown không phải exemption.
7. **Catalog.** `.md/knowledge/skills_compiled.md` phản chiếu thân skill, kể cả lệnh `build-deck`. CI so catalog đã commit thì regenerate bằng lệnh có sẵn trong cùng commit.
8. **Spoke.** Sửa `SKILL.md` trên Hub sẽ lan ra Spoke. Bốn PR tách hồi quy verbatim pháp lý khỏi hồi quy sinh ảnh.

## Điều kiện để chuyển phán quyết

`APPROVE_PLAN` đến khi kế hoạch thực thi ghi đủ bốn PR, bốn posture (`seam-exempt` cho bốn skill BIM, `compose-existing` cho bốn skill còn lại), và `COND-01` … `COND-06`. Thiếu một điều kiện chặn thì giữ `REVISE_PLAN`.