---
request_id: "req-discuss-wave3-core-skills-001"
verdict: REVISE_PLAN
conditions:
  - id: COND-01
    description: "Cấm nhân bản một mục Platform-Aware Reuse Gate vào cả 8 SKILL.md. Mỗi skill nhận đúng một posture: package-bound, skill-bound, compose-existing, hoặc seam-exempt. Biên lai chỉ hợp lệ khi find-seam trả MATCH; KEYWORD_HINT không phải hợp đồng. Không commit index_sha256 tĩnh vào SKILL.md."
    blocking: true
    source_p---
request_id: "req-discuss-wave3-core-skills-001"
verdict: REVISE_PLAN
conditions:
  - id: COND-01
    description: "Cấm nhân bản một mục Platform-Aware Reuse Gate vào cả 8 SKILL.md. Mỗi skill nhận đúng một posture: package-bound, skill-bound, compose-existing, hoặc seam-exempt. Biên lai chỉ hợp lệ khi find-seam trả MATCH; KEYWORD_HINT không phải hợp đồng. Không commit index_sha256 tĩnh vào SKILL.md."
    blocking: true
    source_profile: arch_audit
  - id: COND-02
    description: "PR skill không được thêm seam_id mới và không được sửa packages/. Bốn skill chưa có card (tracker, intel, pccc, mermaid) chỉ compose seam đang có hoặc ghi miễn trừ. API đang bị comment sai trên tracker (generate_diff, consolidate(base_ast)) phải được gỡ; symbol thật là VBHNEngine.merge_documents và LegislativeConsolidator."
    blocking: true
    source_profile: arch_audit
  - id: COND-03
    description: "ADR-0059 áp dụng cho cả tracker và intel, không chỉ ingest và advisor. Gỡ danh sách hiệu lực và ngưỡng số QCVN đang dán trong SKILL.md; phân giải qua legal_registry.yaml và ccba_legal get-clause. Cấm sinh references/ bằng điều khoản viết tay. Đường captcha/CDP và --mock không được là đường thành công. Giả định chỉ được phép cho sự kiện dự án và phải gắn nhãn; cấm giả định điều khoản."
    blocking: true
    source_profile: arch_audit
  - id: COND-04
    description: "Quét raw model theo từng PR skill, cấm regex toàn đợt. Mẫu đã xác nhận là --model qwen-local-primary trong ccba-ai-qc-pccc-audit. Lời gọi công khai là ccba_ai.choose_model hoặc ModelArchetype. Cấm dùng chú thích allow-raw-model trong Markdown để hợp thức hóa chuỗi model."
    blocking: true
    source_profile: arch_audit
  - id: COND-05
    description: "Chia đúng 7 PR theo ma trận, tuần tự ở nhánh QC và Legal. ccba-ai-qc là orchestrator, cấm chép khối gpi của legal-ingest. Trước PR pccc phải chấm lại P (parent coupling) bằng ccba-harness evaluate-gpi; nếu GPI dưới 12 thì hạ xuống reference của ccba-ai-qc."
    blocking: true
    source_profile: arch_audit
  - id: COND-06
    description: "PR 3B1 gỡ mục XML pháp lý và ngưỡng QCVN đang nằm trong ccba-ai-qc, và chỉ nêu import_path của qc_pipeline.v1 là ccba_qc_core:QCAuditPipeline. PR skill không xóa pdf_vector_extractor.py và không đưa import fitz vào ccba_qc_core."
    blocking: true
    source_profile: arch_audit
  - id: COND-07
    description: "PR 3C1 chốt một lệnh nạp văn bản sau khi đối chiếu --help của CLI hiện có. Cấm giữ hai sổ tay pipeline song song (scripts/ccba_platform_cli.py ingest-legal và python -m ccba_legal ingest) và cấm bịa lệnh thứ ba. Sổ tay đầy đủ nằm ở skill mà legal_ingest.v1 đang trỏ."
    blocking: true
    source_profile: arch_audit
risk_score: 3
effort: L
summary: "Bốn chủ đề Đợt 3 đúng hướng, nhưng một mục Seam Binding cho cả 8 skill sẽ đóng dấu hợp đồng giả. Chấp nhận thứ tự Diagram → QC → Legal chỉ khi tách thành 7 PR và bốn posture khớp seam-contracts.yaml."
---

# Phán quyết phản biện Đợt 3 — 8 skills lõi (Legal, QC, Diagram)

**Hồ sơ:** `req-discuss-wave3-core-skills-001`  
**Bên hỏi:** `antigravity`  
**Bên phán quyết:** `grok` (Grok 4.7, hồ sơ `arch_audit`)  
**Căn cứ:** ADR-0057, ADR-0058, ADR-0059, ADR-0061, `seam-contracts.yaml`, frontmatter và thân 8 `SKILL.md`  
**Tệp:** `.md/peer_exchange/grok_discuss_wave3_core_skills.md`

**Phán quyết: `REVISE_PLAN`.** Bốn trọng điểm đúng trục. Thêm cùng một mục `find-seam` và một mẫu Python API vào cả 8 skill sẽ lệch card hiện có và ghi `KEYWORD_HINT` thành biên lai.

Điểm rủi ro **3/5**. Công thức GPI trong đề xuất đúng. `ccba-legal-ingest` (`S=4, K=4, A=4, P=1`) = 24.5. Con số đó không được chép sang 7 skill còn lại.

## Ranh giới Skill và Package

Cổng 0: thuật toán xác định nằm ở package. Skill giữ phán đoán, thứ tự việc, và điều kiện dừng.

| Skill | GPI trong frontmatter | Posture |
| :--- | :--- | :--- |
| `ccba-excalidraw-diagram` | 19.5 (`4, 4, 3, 3`) | **package-bound** `diagram_layout.v1` |
| `ccba-mermaid-diagram` | 18.0 (`3, 4, 2, 1`) | **seam-exempt** |
| `ccba-ai-qc` | Không có `gpi`. `tier: orchestrator` | **package-bound** `qc_pipeline.v1` |
| `ccba-ai-qc-pccc-audit` | 15.5 (`2, 2, 4, 1`) | **compose-existing**, chấm lại `P` |
| `ccba-legal-ingest` | 24.5 | **skill-bound** `legal_ingest.v1` |
| `ccba-legal-advisor` | 22.5 | **skill-bound** `legal_advisor.v1` |
| `ccba-legal-document-tracker` | 22.5 | **compose-existing** |
| `ccba-legal-intel` | 24.5 | **compose-existing**, thu hẹp về ingest |

`diagram_layout.v1` đã trỏ `ccba_diagram:apply_smart_layout`. `get_shape_boundary_point` có trên API công khai. Skill chọn hint layout và gọi seam. Khóa canvas `1000–1150 px` là hằng của engine. Câu “tối ưu tọa độ” trong skill cần có nghĩa: gọi `apply_smart_layout`, rồi đọc kết quả.

Mermaid không có hàm layout CCBA. Miễn trừ seam phải được viết rõ. Giữ hai quy ước escape tách biệt: nhãn Mermaid dùng `#40;` / `#41;`; bảng đặc tả Excalidraw cấm các entity đó và dùng ngoặc tròn thật. Lệch palette Academic Grayscale để PR sau.

Năm script QC và `audit_engine.py` là adapter mỏng tới `ccba_qc_core`. `pdf_vector_extractor.py` tự `import fitz`. Việc đó thuộc `pdf_preprocessor.v1`. PR skill không xóa file này và không đưa `fitz` vào `ccba_qc_core`.

`ccba-ai-qc` vừa import đúng `ccba_qc_core.QCAuditPipeline`, vừa nêu `python -m ccba_ai.cli run-qc`. Một class cùng tên đang sống trong `ccba_ai.pipeline`. PR 3B1 chỉ nêu `ccba_qc_core:QCAuditPipeline`. Thân skill còn dán XML pháp lý và ngưỡng QCVN (F1.3 trên 50 m, hành lang trên 15 m, thang trên 28 m). Orchestrator không mang sổ tay hiệu lực.

PCCC gọi script skill với `--model "qwen-local-primary"`. Engine thật là `ccba_qc_core.pccc`. GPI 15.5 đứng trên 12 vì `P=1`, trong khi việc nằm trong QC. Chấm lại `P`. Nếu GPI dưới 12, hạ thành reference của `ccba-ai-qc`.

`legal_ingest.v1` và `legal_advisor.v1` là `kind: skill`, không có `import_path`. Hai skill tracker và intel không có card. `VBHNEngine` có thật, method công khai là `merge_documents`. Comment `generate_diff` và `consolidate(base_ast, …)` trong tracker là API không tồn tại. Ingest và intel đang kể cùng pipeline bằng hai lệnh: `scripts/ccba_platform_cli.py ingest-legal` và `python -m ccba_legal ingest`. Sổ tay đầy đủ ở lại skill mà `legal_ingest.v1` đang trỏ.

## Bảy PR

Thứ tự miền Diagram → QC → Legal là đúng. Một PR mỗi miền thì không nguyên tử.

| PR | Việc |
| :--- | :--- |
| **3A1** | Excalidraw, package-bound. `find-seam --in diagram --out layout --json`, chỉ nhận `MATCH`. |
| **3A2** | Mermaid, seam-exempt. Gỡ câu hứa `references/` khi thư mục không có. |
| **3B1** | `ccba-ai-qc`: một import seam, gỡ XML pháp lý và ngưỡng QCVN, giữ orchestrator, không thêm GPI. |
| **3B2** | PCCC sau 3B1: `evaluate-gpi`, bỏ `--model`, gọi CLI package. |
| **3C1** | Ingest + intel: một lệnh nạp sau `--help`. Rút CDP/captcha và `--mock` khỏi lối thành công. |
| **3C2** | Advisor: giữ bốn heading phiếu. Giả định chỉ cho tham số công trình. Provenance là `pdf_sha256` + đường dẫn tương đối. |
| **3C3** | Tracker: xóa API comment sai. Trỏ `merge_documents` / `LegislativeConsolidator`. Hiệu lực lấy từ registry. |

3A1 và 3A2 có thể song song sau khi mẫu posture được review. 3B và 3C tuần tự. Mỗi PR tự gỡ bản sao danh sách hiệu lực trên đúng file mình sửa.

## Cạm bẫy cần giữ

Biên lai `KEYWORD_HINT` và `index_sha256` dán sẵn trong skill sẽ thành mỏ neo sai. Comment `# ccba:allow-raw-model` trong Markdown không hợp thức hóa `--model`. Kéo `pdf_vector_extractor.py` vào `ccba_qc_core` đụng độc quyền `fitz` của preprocessor. Gộp hai class `QCAuditPipeline` đụng test của `ccba_ai`. Đổi heading phiếu advisor làm `verify-patch --preset doc` thất bại. Bốn skill không có `references/`; lấp chỗ trống bằng điều khoản viết tay vi phạm ADR-0059. `file:///` và profile `~/.gemini/antigravity/chrome_vip` là trạng thái máy. Rút kịch bản captcha là đổi hành vi vận hành, mô tả PR phải nói rõ.

`APPROVE_PLAN` chỉ đến khi kế hoạch thực thi ghi đủ bảy PR, bốn posture, và `COND-01` … `COND-07`.
 dưới 12, SOP trong `references/` chuyển thành reference của `ccba-ai-qc` và skill đứng riêng được giải thể ở PR đó.

### Legal: hai card là skill, hai skill không có card, một pipeline bị viết hai lần

`legal_ingest.v1` và `legal_advisor.v1` có `kind: skill`, `binding.mode: skill`. Chúng không có `import_path`. Mục “Python API chuẩn” gắn vào hai card này sẽ bịa một import. Tra `find-seam` với hai card này phải ra chính skill và slash-command, rồi việc xác định (convert, hash, get-clause) đi qua package đã có: `legal_markdown.v1`, `ooxml_processor.v1`, `pdf_preprocessor.v1`, `python -m ccba_legal`.

`ccba-legal-document-tracker` nói tới `VBHNEngine`. Class này có thật và có trong `__all__` của `ccba_legal`, method công khai là `merge_documents`. Khối comment trong skill còn `generate_diff` và `consolidate(base_ast, [patch1, patch2])`. Hai method đó không có trên class. Agent sẽ bỏ comment và gọi API không tồn tại. Không mở `vbhn.v1` trong PR skill. Card mới, nếu cần, là PR package sau khi AST đối soát `ccba_legal:VBHNEngine`.

`ccba-legal-intel` và `ccba-legal-ingest` đang kể cùng một pipeline OKF, VBHN, 15 cổng, với hai lệnh khác nhau:

- ingest: `python scripts/ccba_platform_cli.py ingest-legal`
- intel: `python -m ccba_legal ingest`

`legal_ingest.v1` trỏ file skill ingest. Sổ tay đầy đủ ở lại đó. Intel giữ phần còn phân biệt được (đồ thị 11 quan hệ, checklist) và trỏ bước thu thập về `/ccba-legal-ingest`. Lệnh nào sống được quyết bằng `--help` của CLI đang có trong PR 3C1.

Cổng 0 trên ingest còn một dạng khác: thân skill đang là đặc tả thứ hai của `DocxCanonicalSanitizer` (rsid, NFC, KaTeX, multi-part table). Đặc tả đó thuộc package và ADR đã dẫn. Đợt 3 không chép thêm pha thuật toán vào skill.

---

## 2. Thứ tự tiểu đợt (Câu hỏi 2)

Thứ tự miền **Diagram → QC → Legal** là đúng gradient rủi ro. Chia **một PR cho mỗi miền** thì không nguyên tử. Legal đụng bốn file cùng các đoạn dán chéo; QC đụng quyết định còn-hay-hạ tier của PCCC.

| PR | File được sửa | Việc trong PR | Việc để ngoài PR |
| :--- | :--- | :--- | :--- |
| **3A1** | `ccba-excalidraw-diagram/SKILL.md` | Posture package-bound. Mẫu `find-seam --in diagram --out layout --json`. Bắt `status: MATCH`. Gọi `apply_smart_layout`. Cấm agent tự ghi tọa độ. | Không đụng `ccba_diagram`. Không gom palette với Mermaid. |
| **3A2** | `ccba-mermaid-diagram/SKILL.md` | Posture seam-exempt, một đoạn lý do. Giữ quy tắc escape riêng. Gỡ câu progressive disclosure đang hứa references không có thư mục. | Không tạo `diagram_mermaid.v1`. Không thêm `references/` bằng ví dụ bịa. |
| **3B1** | `ccba-ai-qc/SKILL.md` | Posture package-bound, một import `ccba_qc_core:QCAuditPipeline`. Gỡ mục XML pháp lý và ngưỡng QCVN. Giữ `tier: orchestrator`, không thêm `gpi` chép từ ingest. | Không sửa `ccba_ai.pipeline`. Không xóa adapter mỏng. Không đụng `pdf_vector_extractor.py`. |
| **3B2** | `ccba-ai-qc-pccc-audit/SKILL.md` và, chỉ khi GPI < 12, references chuyển chỗ | Chạy `evaluate-gpi` với `P` gắn cha là `ccba-ai-qc`. Bỏ `--model`. Gọi CLI package `pccc`, bỏ đường dẫn script trong `.agents/skills`. Ngưỡng số trở lại `get-clause`. | Không mở seam PCCC mới. Không gộp PR này với 3B1. |
| **3C1** | `ccba-legal-ingest/SKILL.md`, `ccba-legal-intel/SKILL.md` | Chốt một lệnh nạp sau `--help`. Sổ tay pipeline nằm ở skill của `legal_ingest.v1`. Intel thành con trỏ cộng phần checklist/đồ thị. Rút kịch bản CDP/captcha và đường `--mock` khỏi lối thành công. Thiếu PDF/DOCX thì dừng, xin file, hoặc gọi crawler chính thức. | Không viết lại 15 cổng. Không sửa `ccba_legal`. |
| **3C2** | `ccba-legal-advisor/SKILL.md` | Giữ bốn heading phiếu hiện tại vì `verify-patch --preset doc` đang khóa chúng. Giả định chỉ cho tham số công trình và phải gắn nhãn. Điều khoản chỉ từ `get-clause` / `query`, kèm `pdf_sha256` và đường dẫn tương đối bundle. Bỏ `file:///` tuyệt đối. | Không đổi tên mục phiếu. Không sinh điều khoản mẫu. |
| **3C3** | `ccba-legal-document-tracker/SKILL.md` | Xóa comment `generate_diff` / `consolidate(base_ast)`. Trỏ `LegislativeConsolidator` và `VBHNEngine.merge_documents`, hoặc CLI `consolidate` đã có. Danh sách hết hiệu lực lấy từ `relations` của registry. | Không khai `vbhn.v1` trong PR này. |

3A1 và 3A2 không chung file nên có thể làm song song sau khi mẫu posture của 3A1 đã được review. 3B2 đứng sau 3B1. 3C1 → 3C2 → 3C3 tuần tự vì cùng cụm câu “rào chắn điểm liệt”. Mỗi PR skill tự gỡ bản sao của danh sách đó trên file mình sửa. Không mở PR thứ tám chỉ để sửa cùng một đoạn trên năm file.

Mỗi PR skill kết thúc bằng `python scripts/validate_skills.py --file <SKILL.md> --enforce-gpi` và `python -m ccba_harness verify-patch` với preset doc tương ứng. Mã thoát khác 0 thì chưa được báo xong (ADR-0058). PR này là phán quyết kế hoạch, chưa chạy hai lệnh đó trên tám file.

---

## 3. Cạm bẫy có xác suất gãy cao (Câu hỏi 3)

1. **Biên lai giả.** `find-seam` với từ khóa tự do trả `KEYWORD_HINT` và mã thoát khác MATCH. Hiến pháp cấm coi đó là hợp đồng. Bốn skill không card sẽ rơi vào nhánh này nếu bị ép cùng một mục tra cứu. Hash `index_sha256` đổi mỗi lần compile catalog. Hash dán sẵn trong skill sẽ thành mỏ neo cũ ngay PR kế tiếp. Skill chỉ hướng dẫn ghi receipt vào plan của phiên: `seam_id`, `status`, `index_sha256`.

2. **Scanner model không đọc Markdown theo kiểu comment Python.** `# ccba:allow-raw-model` trong `SKILL.md` không làm chuỗi `"qwen-local-primary"` hợp lệ. Mẫu đã thấy nằm ở lệnh `--model` của PCCC. Quét regex cả đợt sẽ đụng ví dụ phản mẫu, tên trong ADR, và telemetry. Chỉ sửa lệnh thật sự gọi model, trong đúng PR của skill đó.

3. **`fitz` trong skill script.** `pdf_vector_extractor.py` import `fitz` dưới `.agents/skills/`. Linter phụ thuộc hiện quét package. Kéo file này vào `ccba_qc_core` sẽ đụng `forbidden_substitute_imports` của `pdf_preprocessor.v1`. Xóa file trong PR văn bản sẽ gãy caller chưa được kê. PR 3B1 không đụng file .py này.

4. **Hai `QCAuditPipeline`.** Sửa prose không gãy test. “Dọn giúp” class trong `ccba_ai.pipeline` trong cùng PR skill sẽ đụng `packages/ccba-ai/tests/test_qc_pipeline.py`. Để issue package riêng.

5. **GPI và validator.** `ccba-ai-qc` không có khối `gpi` vì nó là orchestrator. Thêm khối chép `24.5` có thể qua ngưỡng số và vẫn sai Cổng 1. Hạ tier PCCC khi GPI mới < 12 làm `validate_skills.py --enforce-gpi` thất bại nếu frontmatter vẫn khai `tier: kernel`. Đổi tier và đổi điểm trong cùng commit với kết quả `evaluate-gpi`.

6. **Sinh references cho đủ bảng.** `ccba-mermaid-diagram`, `ccba-legal-ingest`, `ccba-legal-advisor`, `ccba-legal-intel` không có thư mục `references/`. Link thật của excalidraw, QC, PCCC, tracker đang trỏ file có trên đĩa. Chỗ gãy là đoạn progressive disclosure mẫu đã dán vào Mermaid dù không có file. ADR-0059 cấm bịa điều khoản để lấp chỗ trống. PR chỉ sửa link 404 hoặc xóa câu hứa. Không tạo bài viết pháp lý mới.

7. **Danh sách hiệu lực và ngưỡng số là dữ liệu, đang là văn xuôi.** Cùng một danh sách nghị định thay thế nằm trong ingest, advisor và tracker. Cùng ngưỡng QCVN nằm trong `ccba-ai-qc` và PCCC. Sửa một đầu sẽ lệch các đầu còn lại trong lúc 3B/3C đang mở. Vì vậy 3C tuần tự, và mỗi PR gỡ bản sao trên đúng file mình sở hữu. SSOT hiệu lực là `legal_registry.yaml`. SSOT điều khoản là bundle OKF đã có `pdf_sha256`.

8. **`file:///` và đường máy.** Advisor đang yêu cầu link `file:///` tới `metadata.yaml`. Link này gãy khi sang máy khác và đụng bất biến multi-device. Provenance đúng là slug bundle + `pdf_sha256` + đường dẫn tương đối trong repo tri thức. `~/.gemini/antigravity/chrome_vip` trong intel là trạng thái máy. Đưa vào biến môi trường ở chính PR 3C1, không mở chiến dịch quét path toàn repo.

9. **PowerShell trong fence.** Nhiều ví dụ `consolidate` dùng backtick nối dòng. CI và máy reviewer Linux không chạy fence đó. Khi một PR đụng đúng fence đó, đổi sang nối dòng bash. Không reformat hàng loạt fence không liên quan.

10. **Khóa heading của advisor.** Lệnh hoàn tất trong skill gọi `verify-patch --preset doc` với bốn heading “Tóm Tắt Bối Cảnh”, “Kết Luận Pháp Lý”, “Căn Cứ Pháp Lý”, “Khuyến Nghị Kỹ Thuật”. Đổi tên mục cho “chuẩn hóa” sẽ làm chính tiêu chí hoàn tất của skill thất bại.

11. **Catalog biên dịch.** `.md/knowledge/skills_compiled.md` phản ánh thân skill. Nếu CI so catalog đã commit, PR phải regenerate bằng lệnh có sẵn của repo trong cùng commit. Cấm sửa tay catalog.

12. **Rút kịch bản captcha là đổi hành vi vận hành.** Ingest đang cho agent xử lý captcha bằng script CDP cục bộ, và có nhánh chiếm phiên TVPL. Intel yêu cầu login CDP vào profile máy. Thay bằng “dừng và xin file hoặc gọi crawler” là chủ đích của ADR-0059. Mô tả PR phải nói rõ đường tắt này được rút, để người vận hành không coi đó là hồi quy im lặng.

13. **Spoke sync.** Sửa `SKILL.md` trên Hub sẽ lan ra Spoke. PR một mối quan tâm giúp review diff trước khi sync. Gộp tám file thành một commit làm mất khả năng tách hồi quy verbatim khỏi hồi quy diagram.

---

## 4. Bốn trọng điểm sau khi phản biện

**Trọng điểm 1 — Seam.** Giữ nguyên tắc reuse-first. Đổi hình dạng chỉ dẫn theo posture. Mẫu package-bound (viết một lần ở 3A1, dùng lại cho 3B1) gồm: lệnh `ccba-platform find-seam --in <in> --out <out> --json`, điều kiện `status == MATCH`, `import_path` lấy từ JSON, cấm viết script thay thế khi card đã có. Mẫu skill-bound chỉ ghi `seam_id`, `command`, và các package seam mà skill được phép gọi tiếp. Mẫu compose liệt kê card có sẵn. Mẫu exempt ghi lý do và cấm `find-seam`.

**Trọng điểm 2 — Verbatim.** Rào chắn thiếu file gốc là đúng và phải thêm vào tracker cùng intel. Câu “dừng lại” trong ingest chỉ có hiệu lực khi kịch bản CDP và `--mock` không còn là lối hoàn tất. Ngưỡng số trong QC/PCCC là điều khoản viết lại, đưa về `get-clause`.

**Trọng điểm 3 — Model.** Một điểm đã xác nhận: `--model "qwen-local-primary"`. Sửa tại 3B2 bằng `choose_model` / `ModelArchetype` (đã re-export tại `ccba_ai`, khớp `model_routing.v1`). Không phát động chiến dịch thay chuỗi trên toàn bộ references.

**Trọng điểm 4 — GPI và link.** Công thức và ví dụ ingest là đúng. Bảng GPI thực tế nằm ở mục 1. `ccba-ai-qc` đứng ngoài GPI vì Cổng 1. PCCC phải chấm lại `P` trước khi được coi là kernel. Link Level 3 của excalidraw, QC, PCCC, tracker đang có file. Việc của đợt này là bỏ câu hứa rỗng, không phải viết thêm cẩm nang.

---

## 5. Điều kiện để chuyển phán quyết

`APPROVE_PLAN` chỉ đến sau khi kế hoạch thực thi ghi lại đủ bảy PR, bốn posture, và bảy điều kiện `COND-01` … `COND-07`. Thiếu một điều kiện chặn thì giữ `REVISE_PLAN`.
