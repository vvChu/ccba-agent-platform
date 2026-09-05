# CCBA Workflows Registry (ADR-0056 Unified into Skills)

> **Notice**: As per ADR-0056, all 69 legacy workflows have been upgraded to modern Agent Skills in `.agents/skills/ccba-*/SKILL.md`.
> Active slash commands are registered directly in skill YAML frontmatters.

---

# Archived Workflow: ccba-academic-writing

---
name: ccba-academic-writing
description: Hướng dẫn lập đề cương, viết bản thảo và tự động kiểm định văn phong
  bài báo khoa học theo cấu trúc IMRAD.
user-invocable: true
workflow_trigger_level: 1
disable-model-invocation: true
bundle: _core
command: /ccba-academic-writing
triggers:
- academic writing
- viết bài báo
- nghiên cứu khoa học
- IMRAD
- CARS
---
# Workflow: Viết Bài Báo Khoa Học IMRAD (/ccba-academic-writing)

Hãy nạp và thực thi kỹ năng viết bài báo khoa học tại [SKILL.md](../skills/ccba-academic-writing/SKILL.md) và chạy kiểm duyệt vi mô thông qua script [microstructure_audit.py](../skills/ccba-academic-writing/scripts/microstructure_audit.py) khi có bản thảo hoặc dữ liệu thực tế.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*


---

# Archived Workflow: ccba-adopt-spoke

---
description: Đánh giá hiện trạng và tiếp nhận an toàn một codebase hiện hữu (Brownfield)
  vào mạng lưới CCBA Platform.
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
- BIM
- Tác vụ Admin
- Pháp điển
bundle: _core
disable-model-invocation: true
command: /ccba-adopt-spoke
triggers:
- adopt-spoke
- adopt spoke
- tiếp nhận spoke
- onboard spoke
- tiếp nhận dự án có sẵn
---
# Tiếp Nhận Spoke Hiện Hữu (/ccba-adopt-spoke)

Workflow này tự động hóa việc đánh giá hiện trạng, phân tích rủi ro và tiếp nhận thích ứng an toàn (**Non-Destructive Adoption**) một repository/codebase đã có sẵn vào mạng lưới **CCBA Hub-and-Spoke**, bảo tồn 100% dữ liệu nghiệp vụ và Hiến pháp riêng của Spoke.

---

## Các Bước Thực Hiện:

### 1. Đánh Giá Hiện Trạng & Xuất Ma Trận Rủi Ro (Discovery Matrix)
Agent chạy kiểm tra trước (Dry-Run) để lập báo cáo hiện trạng:
```powershell
python [hub_path]\scripts\adopt_spoke.py --spoke . --dry-run
```
Trình bày kết quả ma trận đánh giá cho người dùng:
* Stack công nghệ phát hiện (PowerShell/SharePoint, Python, Node.js, BIM CAD, OKF v2.4 Legal Corpus qua `legal_docs/` & `legal_registry.yaml`...).
* Đề xuất Archetype theo [ADR 0041](../../docs/adr/0041-hub-spoke-ecosystem-taxonomy-and-archetypes.md) (`project_delivery`, `enterprise_governance`, `knowledge_corpus`, `specialized_extension`).
* Tình trạng Git repository và tệp `workspace_context.yaml`.
* Các tệp tin được bảo vệ (AGENTS.md, datamodel, specs).

### 2. Thực Hiện Tiếp Nhận & Hợp Nhất Cấu Hình An Toàn
Sau khi người dùng đồng ý, Agent thực thi tiếp nhận (tự động nhận diện stack):
```powershell
python [hub_path]\scripts\adopt_spoke.py --spoke .
```

*Tùy chọn chỉ định tường minh cấu hình (nếu muốn ghi đè auto-detect):*
```powershell
python [hub_path]\scripts\adopt_spoke.py --spoke . --archetype knowledge_corpus --type "Pháp điển" --mode software
```

Quá trình này sẽ tự động:
1. **Tạo bản sao lưu:** `workspace_context.yaml.bak_<timestamp>`.
2. **Additive Merge:** Bổ sung trường tương thích Hub & Archetype, giữ nguyên 100% các nhóm tài liệu của Spoke.
3. **Cài đặt Guardrails:** Thiết lập Maskara pre-commit hook trong `.git/hooks/` (tự động bỏ qua an toàn nếu là Spoke Dự án/Delivery chỉ đồng bộ qua OneDrive/SharePoint không dùng Git).
4. **Đồng bộ Kỹ năng:** Bơm an toàn bundle Kỹ năng & Workflows phù hợp vào `.agents/skills/`.
5. **Đăng ký Hub Registry:** Đăng ký Spoke vào danh bạ mã hóa của CCBA Platform.

### 3. Báo Cáo Hoàn Tất
In thông báo:
*"🎉 Spoke đã được tiếp nhận thành công vào CCBA Platform! Toàn bộ cấu trúc nghiệp vụ cũ được bảo tồn 100%."*

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-adr-lifecycle

---
description: Workflow quản trị toàn diện vòng đời quyết định kiến trúc ADR
disable-model-invocation: true
bundle: _governance
command: /ccba-adr-lifecycle
triggers:
- ccba-adr-lifecycle
- tao adr
- cap nhat adr
- adr sync
- adr lifecycle
---
# Workflow: Quản Trị Vòng Đời Quyết Định Kiến Trúc (/ccba-adr-lifecycle)

> **Mô tả:** Workflow tự động hóa quản lý vòng đời ADR: Khởi tạo file mới theo chuẩn YAML Frontmatter -> Lan truyền trạng thái thay thế (Cascading Supersedes) -> Tự động tái biên dịch bảng mục lục `README.md` và Ma trận Quan hệ Kỹ năng `TRACEABILITY_MATRIX.md` -> Chạy cổng kiểm định chống lệch pha CI.

---

## 🚀 Các Bước Thực Hiện Của Agent

### 1. Xác Định Hành Động Cần Thực Hiện
Agent lắng nghe yêu cầu của người dùng để chọn 1 trong 3 nhánh xử lý:
- **Nhánh A (Tạo ADR mới):** Người dùng muốn ghi nhận quyết định kiến trúc mới.
- **Nhánh B (Cập nhật / Thay thế ADR cũ):** Người dùng muốn điều chỉnh trạng thái (ACCEPTED -> SUPERSEDED / DEPRECATED).
- **Nhánh C (Đồng bộ & Kiểm định):** Người dùng muốn quét lại ma trận và kiểm tra link.

---

### 2. Thực Thi & Tự Động Hóa (Tương ứng với nhánh)

#### Khi Tạo Mới (Nhánh A):
* Tự động dò số hiệu lớn nhất tiếp theo trong `docs/adr/`.
* Khởi tạo file `docs/adr/00XX-<slug>.md` với template chuẩn.
* Hướng dẫn người dùng hoặc tự động điền các mục: Trạng thái, Bối cảnh, Quyết định, Hệ quả.

#### Khi Cập Nhật Trạng Thái (Nhánh B):
* Mở ADR cũ cần thay thế và cập nhật trạng thái `SUPERSEDED by ADR-00XX`.
* Kiểm tra các tài liệu hoặc skills đang phụ thuộc vào ADR cũ để phát cảnh báo.

#### Khi Đồng Bộ & Kiểm Định (Nhánh C):
* Chạy lệnh biên dịch Living ADR Matrix:
  ```powershell
  python scripts/sync_hub_adr_matrix.py
  ```
* Chạy cổng kiểm định ADR:
  ```powershell
  python -m pytest tests/governance/test_adr.py
  ```

---

### 3. Báo Cáo Nghiệm Thu
* In ra bảng tóm tắt số lượng ADR, số liên kết sống được ghi nhận, và trạng thái $100\%$ Parity.


---

# Archived Workflow: ccba-ai-qc-pccc-audit

---
description: Hệ thống Thẩm tra lỗi thiết kế đa bộ môn (PCCC, MEP, Kiến trúc) thông
  qua cơ chế Semantic Map-Reduce.
applies_to:
- Thẩm tra thiết kế
- Thiết kế
bundle: _qc
disable-model-invocation: true
command: /ccba-ai-qc-pccc-audit
triggers:
- pccc audit command
- chạy kiểm tra PCCC
- run pccc audit
---
# Workflow: Thẩm Tra Thiết Kế PCCC Map-Reduce (/ccba-ai-qc-pccc-audit)

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng tại [SKILL.md](../skills/ccba-ai-qc-pccc-audit/SKILL.md) để bắt đầu quy trình rà soát và kiểm soát chất lượng thiết kế PCCC (Map-Reduce).


---

# Archived Workflow: ccba-ask

---
description: Hướng dẫn định tuyến/tư vấn chọn kỹ năng hoặc workflow phù hợp.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-ask
triggers:
- ask
- tư vấn
- định hướng
- bản đồ kỹ năng
---
# Workflow: Hướng dẫn Định hướng Kỹ năng (/ccba-ask)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `ask` tại [SKILL.md](../skills/ccba-ask/SKILL.md) để bắt đầu tư vấn, định hướng và dẫn đường cho luồng công việc tiếp theo trên Platform.


---

# Archived Workflow: ccba-autoresearch

---
description: Khởi chạy vòng lặp tối ưu hóa kỹ năng AI tự động qua đêm (Git-Ratchet
  Auto-Tuner) lấy cảm hứng từ karpathy/autoresearch.
disable-model-invocation: true
bundle: _core
command: /ccba-autoresearch
triggers:
- autoresearch
- auto-research
- git ratchet
- ratchet
- auto tune
- auto-tune
- tối ưu qua đêm
- tối ưu prompt tự động
---
# Lệnh /ccba-autoresearch

Khi nhận được lệnh này từ người dùng, Agent sẽ tự động nạp và thực thi công cụ tối ưu hóa tự động **Git-Ratchet Auto-Tuner** (`scripts/eval/git_ratchet_tuner.py`).

---

## 🛠️ Hướng dẫn thực thi các bước

### Bước 1: Kiểm tra hoặc Tạo tệp `program.md`
Agent kiểm tra xem thư mục gốc đã có tệp `program.md` chưa:
- Nếu chưa có, copy mẫu từ [`.agents/skills/ccba-eval-gate/program_template.md`](../skills/ccba-eval-gate/program_template.md) vào `program.md` và điều chỉnh `Target File` theo yêu cầu của người dùng.

### Bước 2: Kích hoạt Git-Ratchet Auto-Tuner
Chạy lệnh CLI sau tại thư mục gốc của dự án:
```bash
# Chạy tối ưu hóa theo đặc tả trong program.md (có Git commit tự động)
python scripts/eval/git_ratchet_tuner.py --program program.md

# Chạy thử nghiệm an toàn không commit git (Dry-run mode)
python scripts/eval/git_ratchet_tuner.py --program program.md --dry-run-git

# Chạy tối ưu một kỹ năng trực tiếp qua CLI
python scripts/eval/git_ratchet_tuner.py --target .agents/skills/ccba-copywriting/SKILL.md --max-trials 10 --target-score 90.0
```

### Bước 3: Đánh giá Báo cáo Ratchet
- Đọc bảng tổng kết:
  * Điểm số cải thiện: `Start Score` $\rightarrow$ `Final Score`.
  * Số commits thành công được lưu lại (`kept_commits`).
  * Số lần tự động rollback khi không đạt điểm (`reverted_trials`).
- Báo cáo kết quả rõ ràng và hiển thị `git log` tóm tắt các cải tiến đã đạt được.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-brainstorm

---
description: Khởi động phiên thảo luận ý tưởng và chuẩn bị tài liệu đầu vào tại input_documents/
command: /ccba-brainstorm [-- <topic_id>]
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
disable-model-invocation: true
triggers:
- brainstorm
- ý tưởng
- nạp tài liệu
- thảo luận
- đầu vào
---
# CCBA Brainstorming & Ingestion Workflow

> **Nguồn gốc:** Cấu trúc tương tác luân phiên (Hybrid Rhythm, Deferred Judgment, Party Mode) được học hỏi từ nguyên tắc của `brainstorm-coach` bởi Lưu Trọng Hiếu (License: All Rights Reserved - Adapted patterns only).

Workflow này giúp khởi chạy một phiên thảo luận ý tưởng, tự động quét và phân loại tài liệu đầu vào tại thư mục nháp `input_documents/`, đồng thời kích hoạt các hướng dẫn phân tích đặc thù theo từng chủ đề nghiệp vụ.

## Các bước thực hiện của Agent

### 1. Đọc cấu hình và Xử lý tham số (Config & Routing)
Agent bắt buộc phải đọc và gộp cấu hình các chủ đề từ hai nguồn:
1. **Mặc định từ Hub:** Đọc cấu hình mặc định tại [brainstorm_topics.yaml](resources/brainstorm_topics.yaml).
2. **Cục bộ từ Spoke:** Kiểm tra sự tồn tại của tệp cấu hình cục bộ tại `.md/knowledge/brainstorm_topics.yaml`. Nếu có, đọc và gộp (merge) với cấu hình mặc định (tập tin cục bộ được phép ghi đè các chủ đề trùng `topic_id` hoặc khai báo thêm chủ đề mới).

**Xử lý tham số Bypass:** Agent phân tích câu lệnh kích hoạt để phát hiện tham số truyền sau ký tự `--`:
* **Nếu có tham số trùng khớp `topic_id`:** Bypass — lập tức di chuyển sang **Bước 3** để nạp Kỹ năng và chuyển đổi tài liệu, bỏ qua Bước 2 (Quét) và Menu chọn.
* **Nếu tham số không trùng khớp:** In cảnh báo `⚠️ Chủ đề '[tham-so]' không tồn tại trong cấu hình.` và chuyển sang **Bước 2**.
* **Nếu không có tham số:** Chạy tiếp **Bước 2** thông thường.

*Tiêu chí hoàn thành:* Agent đã nạp cấu hình từ ít nhất một nguồn, in ra cấu trúc các chủ đề khả dụng, và quyết định rẽ nhánh chính xác.

---

### 2. Quét tài liệu và Chọn chủ đề (Scan & Select)
Quét toàn bộ danh sách tệp tin nằm trong thư mục [input_documents/](../../input_documents/):
* In bảng danh sách tệp tin phát hiện được kèm dung lượng (KB/MB).
* Đọc lướt nội dung (skimming) và so khớp từ khóa của các tệp với danh sách `keywords` của các chủ đề trong cấu hình để tự động đề xuất chủ đề phù hợp nhất.
* Hiển thị danh sách tất cả các chủ đề khả dụng cho người dùng lựa chọn. Chờ người dùng xác nhận chủ đề hoặc yêu cầu đổi sang chủ đề khác.

*Tiêu chí hoàn thành:* Người dùng đã phản hồi lựa chọn chủ đề từ danh sách và Agent đã xác nhận chủ đề được kích hoạt.

---

### 3. Chuyển đổi định dạng và Nạp Kỹ năng (Ingestion & Skill Activation)
Sau khi chủ đề được xác nhận, Agent tiến hành:
1. **Chuyển đổi tài liệu:** Chuyển đổi theo quy trình `/ccba-convert-markdown` — tham khảo skill [markdown-document-processing](../skills/ccba-markdown-document-processing/SKILL.md) cho quy tắc routing theo `project.mode`.
   * Đối với các tệp nhẹ `< 5MB` (`.docx`, `.txt`): Tự động chuyển đổi sang Markdown.
   * Đối với các tệp nặng `> 5MB` (PDF bản vẽ, Excel lớn): In cảnh báo, lập bảng tóm tắt metadata và chỉ convert chi tiết khi thảo luận đi sâu vào tệp đó.
2. **Nạp Kỹ năng:** Nạp toàn bộ các kỹ năng nghiệp vụ được chỉ định trong thuộc tính `required_skills` của chủ đề được chọn.

*Tiêu chí hoàn thành:* Toàn bộ các tệp nhẹ đã được chuyển đổi sang Markdown, và các kỹ năng nghiệp vụ tương ứng đã được nạp thành công.

---

### 4. Áp dụng Guidelines và Khởi động Brainstorming
In ra danh sách các chỉ dẫn thảo luận đặc thù (`guidelines`) của chủ đề đã chọn, sau đó bắt đầu phiên trao đổi hai chiều tuân thủ các quy tắc tương tác dưới đây.

*   **Gợi ý kỹ thuật:** Tham khảo [brainstorm_techniques.md](resources/brainstorm_techniques.md) để đề xuất kỹ thuật brainstorm phù hợp với chủ đề (SCAMPER, Reversal, Question Storming, v.v.). Để người dùng chọn hoặc đề xuất 1-2 technique kèm lý do.

**Quy tắc tương tác (Hybrid Rhythm):** Mỗi vòng brainstorm tuân thủ 4 nhịp:
1. **Prompt** — Agent đặt **đúng 1 câu hỏi** mở liên quan đến chủ đề. Luôn hỏi duy nhất 1 câu mỗi lượt để kích thích sự sáng tạo.
2. **User first** — Chờ người dùng trả lời. Bắt buộc giữ **nguyên văn** (verbatim) mọi câu chữ của người dùng với tag `(user)`.
3. **AI Build** — Agent bổ sung 2-4 ý tưởng mới với tag `(AI)`, xây dựng trên ý tưởng người dùng vừa nêu (yes-and), không thay thế.
4. **Return floor** — Kết thúc bằng **đúng 1 câu hỏi tiếp theo** để trả quyền điều khiển về người dùng.

*   **Deferred Judgment:** Trong giai đoạn phát tán ý tưởng, Agent chỉ đóng vai trò ghi nhận và mở rộng ý tưởng; bảo lưu toàn bộ việc đánh giá tính khả thi và xếp hạng cho đến giai đoạn Tổng hợp (mọi ý tưởng được ghi nhận bình đẳng).
*   **Energy Checkpoint:** Sau mỗi 3-4 vòng trao đổi, Agent chủ động hỏi: tiếp tục hướng hiện tại, đổi góc nhìn/kỹ thuật, hay chuyển sang tổng hợp kết quả?
*   **Nghiên cứu bổ sung:** Khi phát sinh nhu cầu nghiên cứu chuyên sâu (tài liệu lớn, API bên thứ ba, so sánh VBPL), kích hoạt `/ccba-research` chạy song song.

*Tiêu chí hoàn thành:* Các chỉ dẫn và quy tắc tương tác đã hiển thị đầy đủ, phiên brainstorming đã bắt đầu với vòng Hybrid Rhythm đầu tiên (Agent đặt câu hỏi mở đầu tiên).

---

### 5. Tổng hợp và Ghi nhận Phiên (Convergence & Session Document)
Khi người dùng yêu cầu tổng hợp (hoặc sau Energy Checkpoint chọn "tổng hợp"), Agent chuyển sang giai đoạn convergence:
1. **Nhóm phân loại:** Gom các ý tưởng đã thu thập thành 3-5 nhóm chủ đề tự nhiên.
2. **Xếp hạng:** Yêu cầu người dùng chọn 3-5 ý tưởng ưu tiên nhất. Agent không tự xếp hạng thay.
3. **Action items:** Chuyển các ý tưởng được chọn thành bước hành động cụ thể.
4. **Session Document:** Tạo artifact Markdown trong thư mục workspace hiện tại ghi nhận toàn bộ phiên với cấu trúc:
   - **Intake:** Chủ đề, ràng buộc, ngày tháng
   - **Ý tưởng phát tán:** Liệt kê mọi ý tưởng với tag `(user)` hoặc `(AI)`, giữ nguyên văn
   - **Nhóm phân loại:** Bảng phân nhóm
   - **Ưu tiên:** Top ý tưởng được chọn
   - **Action items:** Bước tiếp theo

*Tiêu chí hoàn thành:* Artifact Session Document đã được tạo và hiển thị cho người dùng.

---

### 6. Party Mode (Tùy chọn — Multi-role Ideation)
Khi người dùng yêu cầu "nhiều góc nhìn", "phản biện ý tưởng", hoặc "party mode", Agent chuyển sang chế độ brainstorm đa vai:
1. Tạo 2-3 persona ảo phù hợp với chủ đề (ví dụ: khách hàng, đối thủ cạnh tranh, kỹ sư skeptic, nhà đầu tư).
2. Mỗi vòng: Agent phát biểu từ góc nhìn của từng persona, gắn tag rõ ràng (ví dụ: `(Khách hàng)`, `(Skeptic)`).
3. Người dùng vẫn giữ vai trò chính — persona bổ sung góc nhìn, không thay thế.
4. Kết thúc Party Mode khi người dùng yêu cầu hoặc sau Energy Checkpoint.

> **Phân biệt với `/ccba-grilling`:** Party Mode sinh ý tưởng từ nhiều góc nhìn. Grilling stress-test một kế hoạch đã có. Mục đích khác nhau.

*Tiêu chí hoàn thành:* Ít nhất 2 persona đã phát biểu và ý tưởng được ghi nhận vào Session Document, hoặc người dùng yêu cầu dừng/chuyển giai đoạn.

---

## Tiêu chí hoàn thành (Completion Criteria)

*   [x] Config đã nạp và chủ đề đã được xác nhận.
*   [x] Tài liệu đầu vào đã chuyển đổi Markdown (nếu có).
*   [x] Guidelines và quy tắc Hybrid Rhythm đã hiển thị, phiên brainstorming đã bắt đầu.
*   [x] Khi kết thúc phiên: Session Document artifact đã được tạo với đầy đủ ý tưởng tagged `(user)` / `(AI)`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*


---

# Archived Workflow: ccba-build-skill

---
name: ccba-build-skill
description: Nghiên cứu tài liệu từ nhiều nguồn qua NotebookLM và tự động đóng gói
  sinh Skill mới đạt chuẩn CCBA.
user-invocable: true
keywords:
- build-skill
- create-skill
- research
- notebooklm
disable-model-invocation: true
bundle: _core
command: /ccba-build-skill
---
# Workflow: Xây Dựng Kỹ Năng & Quy Trình Chuẩn (/ccba-build-skill)

Khi người dùng kích hoạt lệnh này dưới dạng:
`/ccba-build-skill <danh-sách-nguồn-hoặc-thư-mục> [--name <tên-skill>]`

Agent tiếp nhận lệnh bắt buộc phải tự động thực thi chuỗi tác vụ sau:

---

## 🛡️ 1. Quét Bảo Mật & Nạp Nguồn
- Đọc danh sách nguồn tài liệu được cung cấp (tệp tin cục bộ, URL hoặc video).
- Chạy quét bảo mật qua `scripts/maskara.py` đối với các tệp tin cục bộ để tránh lộ khóa API.
- Nạp nguồn vào Google NotebookLM thông qua CLI helper (`scripts/notebooklm_cli.py`).

---

## 📚 2. Chưng Cất Tri Thức
- Chạy lệnh sinh `study-guide` hoặc `report` của CLI helper để kết xuất cẩm nang tri thức tổng hợp Markdown sạch vào `.md/knowledge/`.
- Đọc tệp cẩm nang này để nắm rõ toàn bộ logic, patterns và API của công cụ cần tạo skill.

---

## 🧩 3. Khởi Tạo Cấu Trúc SKILL.md Đạt Chuẩn (ADR 0001, ADR 0040)
Tạo thư mục tại `.agents/skills/<tên_skill_dạng_kebab_case>/SKILL.md` theo đúng bộ khung chuẩn:

```markdown
---
name: <tên-skill-kebab-case>
description: <Mô tả ngắn gọn súc tích <= 180 ký tự>
bundle: _core # _core | _software | _qc | _consulting | _bim
disable-model-invocation: true # true cho ritual/tool skills, false nếu là master deep skill
---
# <Tên Kỹ Năng In Hoa>

<Mô tả mục đích và vai trò của kỹ năng>

## Quy trình thực hiện (Process)

1. **Bước 1: <Tiêu đề bước>**
   - <Hướng dẫn thao tác 1>
   - <Hướng dẫn thao tác 2>
   **Tiêu chí hoàn thành:** <Kết quả cụ thể cần đạt được ở bước này>

2. **Bước 2: <Tiêu đề bước>**
   - <Hướng dẫn thao tác 1>
   **Tiêu chí hoàn thành:** <Kết quả cụ thể cần đạt được ở bước này>
```

---

## ⚡ 4. Đăng Ký Slash Command Workflow (ADR 0040)
Nếu kỹ năng có thể được kích hoạt trực tiếp từ người dùng bằng slash command, tạo tệp workflow tại `.agents/workflows/ccba-<tên-lệnh>.md` theo khung chuẩn:

```markdown
---
description: <Mô tả chức năng của workflow>
applies_to:
  - "Phần mềm"
bundle: "_core"
disable-model-invocation: true # BẮT BUỘC: 0-token system prompt
---
# Workflow: <Tên Tiếng Việt> (/ccba-<tên-lệnh>)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng tại [SKILL.md](../skills/<tên-skill>/SKILL.md) để bắt đầu quy trình.
```

---

## ✅ 5. Kiểm Định Chất Lượng Tự Động (CI Hard Gates)
Chạy toàn bộ bộ công cụ kiểm định để xác nhận đạt chuẩn 100% trước khi bàn giao:
```bash
python scripts/validate_skills.py
python scripts/validate_docs.py
python scripts/governance/check_spoke_leakage.py
```

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-contribute-to-hub

---
description: Đóng gói mã nguồn, tests, proposal từ Spoke và mở PR lên Hub kèm Vòng lặp Dừng chờ CI & Copilot Review (Self-Healing Gate)
applies_to:
  - Phần mềm
  - Thẩm tra thiết kế
  - Thiết kế
  - Kiểm định
bundle: _core
disable-model-invocation: true
command: /ccba-contribute-to-hub
triggers:
  - contribute
  - contribute to hub
  - đóng góp mã nguồn
  - tạo pr lên hub
  - mở proposal
  - ccba-contribute-to-hub
---
# Workflow: Contribute to Hub (Đóng Góp Mã Nguồn Ngược Lên Hub Chuẩn OKF v2.0)

Quy trình chuẩn hóa để đóng gói mã nguồn, tests, proposal và mở GitHub Pull Request (PR) kèm hoàn tất thẩm định tự động từ Spoke lên Platform Hub (`ccba-agent-platform`). *(Alias: `/ccba-propose-to-hub`)*

---

## 📋 Bước 1: Thu thập Thông tin, Liên Kết Issue & Cổng Kiểm Lọc R&D
Ghi nhận đầy đủ thông tin cốt lõi:
1. **Liên kết Issue & Cổng Tự Động Phân Loại Scope (Smart Scope-Aware Issue Gate):**
   - **Nếu có `--issue [ID]`:** Kế thừa trực tiếp mã Issue để liên kết và đóng tự động (`Closes #[ID]`).
   - **Nếu KHÔNG có `--issue`:** Agent tự động đánh giá quy mô thay đổi:
     * 🟢 **Quy mô Lớn (Major Scope):** Thêm module/deep seam mới trong `packages/`, cập nhật kiến trúc (ADR), hoặc thay đổi $\ge 100$ dòng code / $\ge 3$ files $\rightarrow$ **Agent chủ động gợi ý/tự động tạo 1 GitHub Issue** trên Hub để ghi nhận Changelog, Ký ức dài hạn (Traceability) và gắn vào PR.
     * ⚪ **Quy mô Nhỏ / Nội bộ (Minor Scope):** Vá lỗi nhỏ, sửa typo, cập nhật docstring, refactor nội bộ $< 100$ dòng $\rightarrow$ **Bỏ qua tạo Issue** để tránh làm rác Issue Tracker, mở PR trực tiếp.
2. **Loại đề xuất:** `tool` (Package trong `packages/`), `skill` (`.agents/skills/`), `workflow` (`.agents/workflows/`), hoặc `rules`.
3. **Tên đề xuất:** Dạng kebab-case (ví dụ: `modernize-annex-engine-okf-v23`).
4. **Mô tả & Vấn đề giải quyết:** Nỗi đau thực tế đã giải quyết tại Spoke.
5. **Cổng Kiểm Lọc R&D (Graduation Pre-Flight Gate):**
   - Đảm bảo mã nguồn đã được làm sạch qua `/ccba-graduate-rd` (loại bỏ 100% `print`, đường dẫn hardcoded, rác tạm; có đủ Type Hints & Docstrings Google style).
   - Test suite cục bộ trong `packages/[pkg]/tests/` phải đạt **100% PASS** trước khi tạo Proposal.

---

## 🔍 Bước 2: Kiểm tra Trùng lặp (Duplicate Detection)
Trước khi tạo mới, Agent **bắt buộc** kiểm tra hệ sinh thái Hub:
1. Đọc `.md/workspace_context.yaml` để lấy `hub_path`.
2. Đọc `<hub_path>/.agents/skills/platform-loader/catalog.yaml`, `packages/`, `<hub_path>/.agents/AGENTS.md`, `PLATFORM.md`.
*Nếu phát hiện đã tồn tại thành phần tương tự:* Đề xuất nâng cấp/mở rộng thay vì tạo mới trùng lặp.

---

## 📦 Bước 3: Đóng Gói Mã Nguồn & Tạo Proposal Trên Branch Mới
Thực thi tại thư mục Hub (`hub_path`):
1. **Đồng bộ nhánh & Khóa bảo vệ nhánh (Pre-Commit Branch Assertion):**
   ```bash
   BRANCH_NAME="proposal/${ISSUE_ID:+issue-${ISSUE_ID}-}${PROPOSAL_NAME}"
   git checkout main && git pull origin main && git checkout -b "$BRANCH_NAME"
   [ "$(git branch --show-current)" = "main" ] && { echo "❌ Lỗi: Đang ở main!"; exit 1; }
   ```
2. **Đóng gói Mã nguồn & Tests vào Package tương ứng:**
   - Code: `packages/[pkg]/src/[submodule]/`, Public Deep Seam: `packages/[pkg]/src/__init__.py`, Tests: `packages/[pkg]/tests/`.
   - Format, linting & cập nhật kiến trúc:
     ```bash
     python -m ruff check --fix packages/[pkg]/ && python -m ruff format packages/[pkg]/ && python scripts/update_arch_stats.py
     ```
3. **Ghi nhận tệp Proposal (`.agents/proposals/[YYYY-MM-DD]_[tên-đề-xuất].md` - ADR 0045):**
   ```yaml
   ---
   proposal_id: "[YYYY-MM-DD]_[tên-đề-xuất]"
   type: "tool" # "tool" | "skill" | "workflow" | "rules"
   name: "[tên-đề-xuất]"
   status: "open"
   priority: "Cao"
   related_issue: "#[ISSUE_ID]" # Liên kết Issue nếu có
   proposed_by_project: "[tên-spoke]"
   proposed_by_archetype: "knowledge_corpus"
   proposed_date: "YYYY-MM-DD"
   applies_to: ["Phần mềm", "Thẩm tra thiết kế"]
   ---
   ```
4. **Leakage Guard & Push:**
   ```bash
   python scripts/governance/check_spoke_leakage.py
   git add -A && git commit -m "feat([scope]): add [tên-đề-xuất] and proposal" && git push origin "$BRANCH_NAME"
   ```

---

## 🚀 Bước 4: Mở GitHub Pull Request (PR Flow Tự Đóng Issue)
- **Tự động qua GitHub CLI (Tự động gắn mã Closes #[ISSUE_ID]):**
  ```bash
  PR_BODY="Automated proposal submission from Spoke [tên-spoke].${ISSUE_ID:+ Closes #${ISSUE_ID}}"
  gh pr create --title "feat([scope]): add [tên-đề-xuất]" --body "$PR_BODY" --base main --head "$BRANCH_NAME"
  ```
- **Thủ công:** Truy cập `[PR-creation-URL]/pull/new/[BRANCH_NAME]`.

---

## 🔄 Bước 5: Vòng Lặp Dừng Chờ & Tự Làm Xanh CI (Self-Healing Loop)

> [!IMPORTANT]
> **Tuyệt đối không kết thúc quy trình ngay sau khi mở PR.** Agent phải đồng hành cho đến khi $100\%$ CI Tích Xanh.

1. **Dừng chờ động (Grace Period):** Dùng `schedule` hẹn giờ kiểm tra: PR nhỏ (<100 dòng) `45s`, PR vừa (100-500 dòng) `60s-90s`, PR lớn (>500 dòng) `90s-180s`.
2. **Kiểm tra song song 2 cổng (Dual-Gate):**
   - CI Status: `gh pr checks <PR_NUMBER>`
   - Copilot Review: `gh pr view <PR_NUMBER> --json reviews,comments --jq '.reviews[] | select(.author.login=="copilot-pull-request-reviewer")'`
3. **Tự khắc phục (Self-Healing Action):**
   - Nếu CI Fail: Đọc log qua `gh run view <RUN_ID> --log-failed` $\rightarrow$ Sửa lỗi $\rightarrow$ Commit & push bản vá.
   - Nếu Copilot góp ý: Refactor code đối soát với chuẩn CCBA $\rightarrow$ Commit & push.
   - Tiêu chí: Lặp lại đến khi `gh pr checks <PR_NUMBER>` pass 100%.

---

## ✅ Bước 6: Báo Cáo Hoàn Tất & Sẵn Sàng Merge
Tổng hợp báo cáo: Link PR, kết quả CI, tóm tắt góp ý đã sửa, và thông báo Maintainer kích hoạt `/ccba-review-proposal [PR_NUMBER]`.

---

## 🔄 Bước 7: Vòng Khép Kín Hậu Hợp Nhất (Closed-Loop Spoke Sync Gate)
Sau khi PR được Squash Merge vào Hub `main`, thực thi chu trình 4 bước đóng vòng tại Spoke:
1. **Xác nhận Hợp nhất:** `gh pr view <PR_NUMBER> --json state,mergedAt --jq '.state'` (phải là `MERGED`).
2. **Đồng bộ Downstream:** Chạy `/ccba-update-spoke` hoặc `python [hub_path]\scripts\sync_spoke.py --spoke . --apply`.
3. **Tái cài đặt Editable Package:** `pip install -e "[hub_path]\packages\[package-name]"` (nếu là `tool`).
4. **Hồi quy & Dọn dẹp:** Chạy kiểm thử Spoke (`python scripts\validate_legal_spoke.py`), xóa branch `git branch -D proposal/[tên-đề-xuất]`, và ghi log vào `.md/knowledge/session_learnings.md`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-convert-markdown

---
description: Chuyển đổi tài liệu sang Markdown qua Deep Seam ConversionPipeline (tự
  động xử lý bảng biểu, biểu mẫu, liên kết)
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
disable-model-invocation: true
command: /ccba-convert-markdown
triggers:
- convert
- mdconverter
- chuyển đổi tài liệu
- pdf to markdown
---
# Workflow: Convert to Markdown (/ccba-convert-markdown)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `markdown-document-processing` tại [SKILL.md](../skills/ccba-markdown-document-processing/SKILL.md) để chuyển đổi tài liệu Word/PDF sang Markdown thông qua Deep Seam `ConversionPipeline` (tự động phục hồi bảng vỡ, làm sạch biểu mẫu và chuẩn hóa liên kết phụ lục trong 1 bước).


---

# Archived Workflow: ccba-copywriting

---
description: Soạn thảo văn bản hành chính/thương mại theo mẫu chuẩn đã thống nhất,
  kế thừa trực tiếp nguồn dữ liệu biểu mẫu (templates) được chuẩn hóa.
applies_to:
- Phần mềm
- Tác vụ Admin
bundle: _core
disable-model-invocation: true
command: /ccba-copywriting
triggers:
- copywriting
- viết thầu
- soạn thầu
- hồ sơ thầu
- viết thuyết phục
- marketing admin
---
# Workflow: Soạn Thảo Văn Bản Chuẩn (/ccba-copywriting)

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng copywriting tại [SKILL.md](../skills/ccba-copywriting/SKILL.md) để bắt đầu luồng soạn thảo văn bản theo mẫu chuẩn.


---

# Archived Workflow: ccba-create-pr

---
description: Push code hiện tại và tạo Pull Request tự động
applies_to:
- Phần mềm
bundle: _software
disable-model-invocation: true
command: /ccba-create-pr
triggers:
- create PR
- pull request
- tạo PR
---
# Workflow: Create Pull Request

Quy trình tự động hóa đẩy mã nguồn và khởi tạo Pull Request siêu tốc.

## Bước 0: Main Branch Guard (Tự động phát hiện & sửa sai)

1. Lấy tên branch hiện hành:
   ```bash
   git branch --show-current
   ```
2. **Nếu đang ở `main`**: Kiểm tra xem có commits chưa push không:
   ```bash
   git log origin/main..main --oneline
   ```
3. **Nếu có commits chưa push trên `main`** → Tự động tạo feature branch retroactively:
   a. Phân tích commit messages để suy ra loại công việc (`feat`, `fix`, `docs`, `refactor`, `chore`) và mô tả ngắn gọn.
   b. Đề xuất tên branch (ví dụ: `feat/architecture-sync-enforcement`) và xin xác nhận người dùng.
   c. Sau khi được đồng ý, thực hiện:
      ```bash
      # Tạo feature branch tại vị trí hiện tại (giữ nguyên commits)
      git branch [ten_branch]
      # Reset main về origin (xóa commits khỏi main)
      git reset --hard origin/main
      # Chuyển sang feature branch
      git checkout [ten_branch]
      ```
   d. Thông báo: *"Đã tự động tạo branch `[ten_branch]` từ N commits trên main. Main đã được reset về origin."*
4. **Nếu không có commits chưa push trên `main`** → Báo lỗi: *"Không có thay đổi nào trên main để tạo PR. Hãy tạo feature branch và commit trước."* Dừng workflow.
5. **Nếu đã ở feature branch** → Bỏ qua bước này, tiếp tục Bước 1.

## Bước 1: Kiểm định Chất lượng Local CI Eval Gates (Shift-Left Gate)

1. Kích hoạt toàn bộ hệ thống kiểm thử tự động và kiểm định tài liệu tại local TRƯỚC KHI đẩy code:
   * **Tại Hub Platform:**
     ```bash
     python scripts/eval/run_harness_evals.py
     ```
   * **Tại Spoke (Pháp điển / Knowledge Corpus):**
     ```bash
     python scripts/validate_legal_spoke.py
     ```
2. **Quy tắc chặn lỗi tại nguồn:**
   - Nếu kiểm thử trả về `PASS 100%`: Mã nguồn đạt chuẩn, tiếp tục Bước 2.
   - Nếu có Gate bị `FAIL` hoặc phát hiện Architecture Drift: Tạm dừng workflow, yêu cầu Agent/người dùng sửa lỗi tại local và commit lại trước khi đẩy mã nguồn.

## Bước 2: Kiểm tra trạng thái và Push code lên remote

1. Kiểm tra trạng thái làm việc (working tree):
   ```bash
   git status --porcelain
   ```
   *Lưu ý:* Đảm bảo không còn thay đổi chưa commit.
2. Lấy tên branch hiện hành:
   ```bash
   git branch --show-current
   ```
3. Đẩy branch lên origin và thiết lập upstream:
   ```bash
   git push -u origin [current_branch]
   ```

## Bước 3: Khởi tạo Pull Request

1. Kiểm tra xem GitHub CLI (`gh`) có hoạt động không:
   ```bash
   gh auth status
   ```
2. Nếu `gh` đã đăng nhập:
   - Tự động lấy danh sách 5 commit gần nhất để làm nội dung mô tả:
     ```bash
     git log -n 5 --pretty=format:"- %s"
     ```
   - Tự động tạo PR bằng dòng lệnh (thay thế tiêu đề dựa trên tên branch và body bằng mô tả commit):
     ```bash
     gh pr create --title "[Feature/Fix Title]" --body "[Commit List Description]" --base main --head [current_branch]
     ```
3. Nếu `gh` chưa đăng nhập:
   - Sử dụng `browser_subagent` mở link tạo PR động:
     - URL: Lấy từ `git remote get-url origin` chuyển thành dạng URL Pull Request.
     - Tiêu đề: Lấy từ tên branch (bỏ prefix `feature/`, `fix/`, viết hoa chữ cái đầu).
     - Nội dung: Tóm tắt từ 5 commit gần nhất (`git log -n 5 --pretty=format:"- %s"`).

## Bước 4: Thông báo kết quả

1. Trình bày đường dẫn PR, trạng thái kiểm thử CI và tiến trình yêu cầu review (Review Requests) cho người dùng.
2. Nhắc nhở người dùng: "PR đã được khởi tạo. GitHub Actions CI và GitHub Copilot Review đang chạy ngầm. Hãy gọi `/ccba-release-feature` khi CI đã xanh và Copilot đã hoàn tất lượt review để đối soát và merge."


---

# Archived Workflow: ccba-discard-feature

---
description: Hủy bỏ branch hiện tại, xóa cả local và remote
applies_to:
- Phần mềm
bundle: _software
disable-model-invocation: true
command: /ccba-discard-feature
triggers:
- discard
- hủy branch
- xóa branch
---
# Workflow: Discard Feature (Hủy bỏ Branch)

Quy trình xóa bỏ an toàn một branch thử nghiệm không sử dụng nữa.

## Bước 1: Xác nhận an toàn

1. Lấy tên branch hiện hành:
   ```bash
   git branch --show-current
   ```
2. Cảnh báo rõ ràng cho người dùng trước khi xóa vĩnh viễn và yêu cầu xác nhận (`yes/no`). Nếu từ chối, dừng thực hiện ngay lập tức.

## Bước 2: Quay về Main và Dọn dẹp

1. Chuyển ngữ cảnh về branch `main`:
   ```bash
   git checkout main
   ```
2. Xóa branch trên remote (nếu có):
   ```bash
   git push origin --delete [discard_branch]
   ```
   *(Nếu xảy ra lỗi do remote branch không tồn tại, bỏ qua và tiếp tục)*
3. Xóa branch cục bộ:
   ```bash
   git branch -D [discard_branch]
   ```

## Bước 3: Thông báo hoàn tất

1. Báo cáo trạng thái hoàn tất:
   - 🗑️ Đã hủy bỏ branch thành công.
   - 🔙 Đã quay về branch `main` an toàn.


---

# Archived Workflow: ccba-docs

---
description: Khởi động quy trình tự động cập nhật và kiểm định tài liệu kỹ thuật của
  dự án.
triggers:
- /ccba-docs
- cập nhật tài liệu
- update docs
- docs
- validate docs
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-docs
---
# Workflow: ccba-docs

Khi người dùng kích hoạt Slash Command này, Agent **bắt buộc** phải nạp và thực thi kỹ năng `docs_manager` tại [SKILL.md](../skills/ccba-docs-manager/SKILL.md) để bắt đầu quy trình quản lý tài liệu.


---

# Archived Workflow: ccba-eval-gate

---
description: Chạy kiểm định tự động qua CI Gates và kích hoạt vòng lặp tự sửa lỗi
  (Self-Healing).
disable-model-invocation: true
bundle: _core
command: /ccba-eval-gate
triggers:
- eval gate
- kiểm chứng
- self-healing
- run gate
---
# Lệnh /ccba-eval-gate

Khi nhận được lệnh này, hãy nạp trực tiếp kỹ năng [SKILL.md](../skills/ccba-eval-gate/SKILL.md) và làm theo hướng dẫn thực thi trong đó để tự động kiểm chứng và sửa lỗi mã nguồn.


---

# Archived Workflow: ccba-extract-style

---
description: Trích xuất và phân tích đặc trưng văn phong thầu/hành chính từ tài liệu
  mẫu của CCBA, tự động dựng biểu mẫu (Template) có placeholders.
applies_to:
- Phần mềm
- Tác vụ Admin
bundle: _core
disable-model-invocation: true
command: /ccba-extract-style
triggers:
- extract style
- trích xuất văn phong
- văn phong mẫu
- style thầu
- phong cách viết
---
# Workflow: Trích Xuất & Chuẩn Hóa Biểu Mẫu (/ccba-extract-style)

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng copywriting tại [SKILL.md](../skills/ccba-copywriting/SKILL.md) và chạy phần trích xuất/nghiên cứu văn phong thô để chuẩn hóa thành tệp template.


---

# Archived Workflow: ccba-git-guardrails

---
description: Thiết lập và kích hoạt rào chắn lệnh Git nguy hiểm của Agent.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-git-guardrails
triggers:
- git-guardrails
- git guardrails
- git
- guardrails
---
# Workflow: Rào Chắn An Toàn Git (/ccba-git-guardrails)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `git-guardrails` tại [SKILL.md](../skills/ccba-git-guardrails/SKILL.md) để bắt đầu kích hoạt chế độ chặn và xin quyền cho các lệnh Git nguy hiểm.


---

# Archived Workflow: ccba-graduate-rd

---
description: Quy trình cưỡng chế chuyển hóa mã nguồn R&D thành Deep Seam Production, tích hợp /boost, /teamwork và mở PR tự động.
applies_to:
- Phần mềm
- Kiểm định
- Thẩm tra thiết kế
bundle: _core
disable-model-invocation: true
command: /ccba-graduate-rd
triggers:
- graduate
- tốt nghiệp
- hợp nhất vào hub
- consolidate
- deep seam
- chuyển scratch vào production
- ccba-graduate-rd
---
# Workflow: Tốt Nghiệp R&D → Deep Seam Production & Auto-PR (/ccba-graduate-rd)

Quy trình tự động hóa toàn trình 7 bước (Full-Cycle Autonomous Pipeline) chuyển hóa mã nguồn thử nghiệm (scratch script, prototype) thành module Production chuẩn mực trong Hub (`packages/ccba-*/src/`), tự động đóng gói Proposal, tạo Pull Request và tự làm xanh CI (Self-Healing Dual-Gate).

> [!CAUTION]
> **3 Bất Biến Tuyệt Đối (Core Invariants):**
> 1. **Không để script vá tồn tại qua phiên:** Mọi scratch script nằm trong `brain/*/scratch/` hoặc `.md/scratch/`, cấm commit vào `scripts/` Spoke.
> 2. **Upstream Promotion bắt buộc:** Khi scratch script chứng minh hiệu quả → Bắt buộc refactor vào Hub `packages/` trong cùng phiên.
> 3. **1-Pass Clean Run & 100% CI Green:** Xóa script vá, chạy lại lệnh gốc và nghiệm thu toàn bộ CI Gates đạt 100% Tích Xanh.

---

## 📋 Bước 1: Kiểm Kê & Phân Loại R&D Artifacts
Quét và phân loại toàn bộ files trong `brain/*/scratch/`, `.md/scratch/` và `scripts/`:
* **Thuật toán cốt lõi** (regex, parser, classifier, KaTeX): → Bước 2 nhúng Deep Seam.
* **Glue code** (CLI wrapper, `print`, `tempfile`): → Loại bỏ, không nhúng vào lõi.
* **Dữ liệu mẫu / fixture**: → Bước 3 chuyển thành test fixture.
* **Báo cáo / ghi chú**: → Lưu vào `.md/archive/` theo chuẩn ADR 0033.

---

## 🔧 Bước 2: Bóc Tách & Nhúng Lõi Deep Seam (Giao thức /boost)
Áp dụng cơ chế **Deep Reasoning** (`DeepCoder`) và **5 Cổng Phản Biện** (`improve-codebase-architecture`):
1. **Cổng 1 (Glue vs Domain):** Tỷ lệ $\ge 70\%$ Glue Code $
ightarrow$ KHÔNG nhúng vào lõi Seam.
2. **Cổng 2 (Hard Caller Gate):** Đếm số callers thực tế và xác minh implementation.
3. **Cổng 3 (SDK Signatures):** Kiểm tra signature tương thích kiến trúc hiện có.
4. **Cổng 4 (Unique Naming):** Đảm bảo symbol name không xung đột toàn cục.
5. **Cổng 5 (Measurable Friction):** Bằng chứng lỗi runtime hoặc benchmark thực tế.
*Refactor chuẩn mực:* Loại bỏ hardcoded paths, thêm type hints và Google docstrings đầy đủ.

---

## 🧪 Bước 3: Xây Dựng Test Suite (Double-Pass Adversarial Review)
1. Tạo test fixtures trong `packages/ccba-*/tests/` từ dữ liệu thực tế của phiên R&D.
2. Viết unit tests độc lập và chạy kiểm thử tự phản biện (Self-Adversarial):
   ```powershell
   python -m pytest packages/ccba-*/tests/ -v
   ```
   *Tiêu chuẩn:* **100% tests passed, 0 failures**.

---

## 🔁 Bước 4: Kiểm Chứng 1-Pass Clean Run & Spoke CI
1. Xóa các scratch scripts cục bộ.
2. Chạy lại lệnh gốc từ đầu vào ban đầu (ví dụ: `python -m ccba_legal convert "ten_doc.docx" "legal_docs/..."`).
3. Chạy Master CI Gate của Spoke:
   ```powershell
   python scripts/validate_legal_spoke.py
   ```
   *Tiêu chuẩn:* `0 Errors, 0 Critical Warnings, 100% Pass`.

---

## 📦 Bước 5: Đóng Gói Proposal & Khởi Tạo Branch
Thực thi tại thư mục Hub (`hub_path`):
1. **Khởi tạo branch đề xuất (ADR 0045):**
   ```bash
   BRANCH_NAME="proposal/${ISSUE_ID:+issue-${ISSUE_ID}-}${PROPOSAL_NAME}"
   git checkout main && git pull origin main && git checkout -b "$BRANCH_NAME"
   ```
2. **Định dạng & Cập nhật Thống kê Kiến trúc:**
   ```bash
   python -m ruff check --fix . && python -m ruff format . && python scripts/update_arch_stats.py
   ```
3. **Soạn thảo Proposal File (`.agents/proposals/YYYY-MM-DD_[proposal-name].md`):** Ghi nhận đầy đủ Context, Implementation và Verification.
4. **Leakage Guard & Push:** Chạy `python scripts/governance/check_spoke_leakage.py` và `git push origin "$BRANCH_NAME"`.

---

## 🚀 Bước 6: Mở GitHub Pull Request & Vòng Lặp Self-Healing CI Dual-Gate
1. **Mở Pull Request qua GitHub CLI:**
   ```bash
   gh pr create --title "feat([scope]): [tên-đề-xuất]" --body "$PR_BODY" --base main --head "$BRANCH_NAME"
   ```
2. **Vòng lặp Dừng chờ & Tự làm xanh CI (Teamwork Autonomous CI Guard):**
   - Lắng nghe trạng thái qua `gh pr checks <PR_NUMBER>`.
   - Nếu CI Fail: Đọc log qua `gh run view <RUN_ID> --log-failed` $
ightarrow$ Tự động phân tích và sinh bản vá $
ightarrow$ Commit & push bản vá.
   - Lặp lại đến khi **100% CI Checks Tích Xanh** (`validate`, `scan`, `test matrix`, `lint`).

---

## 🔄 Bước 7: Báo Cáo & Closed-Loop Spoke Sync
1. Báo cáo URL Pull Request, trạng thái CI Tích Xanh và tóm tắt tính năng cho Maintainer.
2. Sẵn sàng cho lệnh `/ccba-review-proposal [PR_NUMBER]` hoặc đồng bộ downstream khi PR được merge.


---

# Archived Workflow: ccba-grill-with-docs

---
description: Phiên phỏng vấn Socrates dồn dập giúp làm sắc nét kế hoạch thiết kế và
  tự động ghi nhận tệp thuật ngữ (CONTEXT.md) cùng quyết định kiến trúc (ADRs).
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-grill-with-docs
triggers:
- grill
- grilling
- phỏng vấn
- socrates
- context.md
- adrs
---
# Workflow: Phỏng Vấn Socrates Đối Chiếu Quy Chuẩn (/ccba-grill-with-docs)

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng tại [SKILL.md](../skills/ccba-grilling/SKILL.md) và kết hợp kỹ năng [domain-modeling](../skills/ccba-domain-modeling/SKILL.md) để ghi nhận lại các thuật ngữ mới vào tệp `CONTEXT.md` và các quyết định khó đảo ngược thành hồ sơ thiết kế ADR tại `docs/adr/`.


---

# Archived Workflow: ccba-grilling

---
description: Phỏng vấn dồn dập người dùng từng câu một để stress-test kế hoạch hoặc
  thiết kế.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-grilling
triggers:
- grill
- grilling
- phỏng vấn
- stress test
---
# Workflow: Phỏng Vấn Dồn Dập (/ccba-grilling)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `grilling` tại [SKILL.md](../skills/ccba-grilling/SKILL.md) để bắt đầu grilling loop.


---

# Archived Workflow: ccba-handoff

---
description: Đóng gói phiên làm việc thành tài liệu handoff nhỏ gọn cho Agent tiếp
  theo.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-handoff
triggers:
- handoff
- đóng gói phiên
- transfer context
- bàn giao
---
# Workflow: Handoff Phiên Làm Việc (/ccba-handoff)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `handoff` tại [SKILL.md](../skills/ccba-handoff/SKILL.md) để tổng hợp ngữ cảnh phiên làm việc hiện tại.


---

# Archived Workflow: ccba-implement

---
description: Triển khai lập trình khép kín (TDD -> Eval Gate -> Code Review -> Commit
  -> Walkthrough)
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-implement
triggers:
- implement
- triển khai code
- lập trình tính năng
---
# Workflow: Triển khai lập trình (/ccba-implement)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `implement` tại [SKILL.md](../skills/ccba-implement/SKILL.md) để bắt đầu quy trình lập trình khép kín dựa trên đặc tả kỹ thuật (Spec) hoặc các tickets công việc đã chia nhỏ.


---

# Archived Workflow: ccba-improve-codebase-architecture

---
description: Cải tiến kiến trúc codebase bằng cách quét phát hiện module nông và đề
  xuất deepening.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-improve-codebase-architecture
triggers:
- improve architecture
- codebase architecture
- module nông
- refactor
---
# Workflow: Cải Tiến Kiến Trúc Codebase (/ccba-improve-codebase-architecture)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `improve-codebase-architecture` tại [SKILL.md](../skills/ccba-improve-codebase-architecture/SKILL.md) để bắt đầu phân tích cấu trúc module.


---

# Archived Workflow: ccba-init-spoke

---
description: Khởi tạo một dự án (Spoke) tuân thủ kiến trúc CCBA Agent Platform
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
- BIM
- Tác vụ Admin
- Pháp điển
bundle: _core
disable-model-invocation: true
command: /ccba-init-spoke
triggers:
- init spoke
- setup project
- khởi tạo dự án
---
# Workflow: Khởi Tạo CCBA Spoke Workspace (/ccba-init-spoke)
Workflow này tự động hóa việc thiết lập không gian làm việc dự án mới theo chuẩn **CCBA Hub-and-Spoke** (ADR 0041, ADR 0044) và **Global Rules**.

---

## 🛡️ Bước 0: Rào Chắn An Toàn Dự Án Hiện Hữu (Brownfield Safety Guard)
> [!CAUTION]
> Nếu thư mục hiện tại **đã có sẵn mã nguồn hoặc cấu hình cũ** (có `workspace_context.yaml`, `.md/`, `.agents/`):
> - **TUYỆT ĐỐI KHÔNG** chạy tiếp `/ccba-init-spoke` để tránh ghi đè dữ liệu!
> - Hãy chuyển sang lệnh: **`/ccba-adopt-spoke`** để tự động tiếp nhận an toàn và bảo tồn 100% dữ liệu cũ.

---

## 📋 Bước 1: Khảo Sát & Tạo Cấu Hình `workspace_context.yaml`

1. **Lấy tên dự án:** Lấy tên thư mục hiện tại làm `project.name`.
2. **Xác định Archetype ([ADR 0041](../../docs/adr/0041-hub-spoke-ecosystem-taxonomy-and-archetypes.md)):**
   - `project_delivery` (Dự án tư vấn, thiết kế, thẩm tra công trình thực tế)
   - `enterprise_governance` (Hệ điều hành quản trị nội bộ / IDOP-CCBA-WAY)
   - `knowledge_corpus` (Kho tri thức pháp điển quốc gia OKF v2.0 / ccba-legal-knowledge)
   - `specialized_extension` (Khung mở rộng chuyên biệt):
     * `sub_type: personal_sandbox` (Không gian nghiên cứu, thử nghiệm & làm việc cá nhân theo Quy chế CCBA 2026)
     * `sub_type: research_lab` (Viện R&D, bài báo khoa học)
     * `sub_type: tooling_plugin` (Phát triển Add-in CAD/BIM)
     * `sub_type: client_portal` (Cổng Khách hàng Extranet)
3. **Xác định Loại dự án (`type` & `mode`):**
   - `Phần mềm` $\rightarrow$ mode: `software`, qc_mode: `null`
   - `Thẩm tra thiết kế` $\rightarrow$ mode: `delivery`, qc_mode: `third-party`
   - `Thiết kế` $\rightarrow$ mode: `delivery`, qc_mode: `internal`
   - `Kiểm định` $\rightarrow$ mode: `delivery`, qc_mode: `assessment`
   - `BIM` $\rightarrow$ mode: `delivery`, qc_mode: `internal`
   - `Tác vụ Admin` $\rightarrow$ mode: `admin`, qc_mode: `null`
   - `Pháp điển` $\rightarrow$ mode: `software`, qc_mode: `legal`
4. **Khởi tạo tệp `.md/workspace_context.yaml`:**

#### Mẫu A: Spoke Dự Án Kỹ Thuật (`project_delivery`)
```yaml
project:
  name: "2026-04-dh-viet-nhat"
  archetype: "project_delivery"
  type: "Thẩm tra thiết kế"
  mode: "delivery"
  qc_mode: "third-party"
  hub_path: "D:/GitHubProjects/ccba-agent-platform"
  description: "Dự án Thẩm tra Thiết kế PCCC & MEP Công trình ĐH Việt Nhật"
must_read:
  always: [{path: .md/GLOSSARY.md, why: "Thuật ngữ chuẩn hóa dự án"}]
do_not_touch: [.env]
acknowledgment_required: true
acknowledgment_format: "Tôi đã đọc workspace_context.yaml. Đây là Spoke Dự Án '[project_name]'. Sẵn sàng làm việc!"
```

#### Mẫu B: Spoke Cá Nhân (`specialized_extension` / `personal_sandbox` — Quy chế 2026)
```yaml
project:
  name: "chuvu-sandbox"
  archetype: "specialized_extension"
  sub_type: "personal_sandbox"
  hub_path: "D:/GitHubProjects/ccba-agent-platform"
  description: "Không gian nghiên cứu & làm việc cá nhân theo Quy chế CCBA 2026"
organizational_identity:
  owner_name: "Chu Vũ"
  owner_email: "chuvu@ibst-bim.vn"
  department: "PHONG_RD_HTQT"
  seat_role: "IDOP_LEAD"
qc_governance:
  authorized_qc_level: "LEVEL_1_TECHNICAL_CHECK"
  can_sign_off_technical: true
guardrails:
  sandbox_mode: true
  prevent_direct_production_publish: true
  upstream_proposal_target: "main"
must_read:
  always: [{path: d:/idop-ccba-way/.md/governance_constitution/03_ccba_charter_2026.md, why: "Quy chế 2026"}]
do_not_touch: [.env, "*.pfx", "*.key"]
```

#### Mẫu C: Spoke Kho Tri Thức Pháp Điển (`knowledge_corpus` / `Pháp điển`)
```yaml
project:
  name: "ccba-legal-knowledge"
  archetype: "knowledge_corpus"
  type: "Pháp điển"
  mode: "software"
  qc_mode: "legal"
  hub_path: "D:/GitHubProjects/ccba-agent-platform"
  description: "Kho Tri thức Pháp điển & Quy chuẩn Xây dựng Quốc gia (OKF v2.4 Universal Agent-Centric)"
hub_packages: [ccba-legal-intel, ccba-notebooklm]
must_read:
  always: [{path: .md/GLOSSARY.md, why: "Thuật ngữ pháp lý chuẩn hóa"}]
do_not_touch: [.env]
acknowledgment_required: true
acknowledgment_format: "Tôi đã đọc workspace_context.yaml. Đây là Spoke Kho Tri Thức '[project_name]'. Sẵn sàng làm việc!"
```

> [!NOTE]
> **Quy chuẩn Spoke Tri thức (ADR 0036, ADR 0044 & Issue #215):**
> 1. **Cấu trúc OKF v2.4 Universal (ADR 0036):** Bắt buộc có ngăn kéo `sources/` (chứa PDF/DOCX gốc) và 4 ngăn chuyên biệt (`tables/`, `figures/`, `annexes/`, `templates/`). Tuyệt đối cấm để thư mục `templates/` rỗng.
> 2. **Gate 0 Ingestion Provenance (ADR 0016):** Tự động đối soát cấu trúc và Text Parity giữa DOCX và PDF Công báo qua `ccba_legal.provenance`.
> 3. **Script Budget & Cleanliness (ADR 0044):** Duy trì $\le 15$ core scripts trong `scripts/`. Tái sử dụng `ccba_legal` và `ccba_ai` từ Hub qua `spoke_bootstrap.py`. Chặn wrapper thừa qua `check_spoke_cleanliness.py`.

---

## 🔄 Bước 2: Đồng Bộ Kỹ Năng & Đăng Ký Spoke (Single-Engine Sync)

Agent chạy Deep Seam `SpokeSynchronizer`:
```powershell
python "[hub_path]\scripts\sync_spoke.py" --spoke .
```
*Tự động: tạo `.md/`, chọn bundle từ `catalog.yaml`, bơm skills/workflows, đồng bộ `AGENTS.md`, đăng ký RSA 2048-bit vào Hub Registry.*

---

## 📦 Bước 3: Thiết Lập Python Packages & Spoke Leakage Guard (ADR 0044, ADR 0045)

Đối với dự án có Python (`is_python_project = True`), khởi tạo môi trường liên kết:
```powershell
python "[hub_path]\scripts\spoke\spoke_bootstrap.py" --spoke .
```
*Tự động: sinh `requirements-hub.txt` kết nối editable packages (`ccba-ai`, `ccba-harness`...), cấu hình `.gitignore` cách ly.*

---

## 🔒 Bước 4: Cài Đặt Bảo Mật Maskara & Hoàn Tất

1. **Cài đặt Git Hook:** Tự động tạo pre-commit hook trong `.git/hooks/` gọi Maskara quét chặn lộ API keys.
2. **Xác nhận Onboarding (Global Rule 4):**
   > *"Tôi đã khởi tạo thành công Spoke `[tên_dự_án]` (Archetype: `[archetype]`, Type: `[type]`). Sẵn sàng làm việc!"*

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-issue-to-hub

---
description: Soạn thảo và gửi đề xuất ý tưởng/tính năng/báo lỗi (RFC Proposal) từ
  Spoke lên Hub dưới dạng GitHub Issue
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
disable-model-invocation: true
command: /ccba-issue-to-hub
triggers:
- issue to hub
- đề xuất ý tưởng
- rfc
- tạo issue
- feature request
- ccba-issue-to-hub
---
# Workflow: Đề Xuất Ý Tưởng & Tính Năng Lên Hub (/ccba-issue-to-hub)

Quy trình tự động hóa bóc tách ngữ cảnh thảo luận tại dự án Spoke, biên soạn bản đề xuất cải tiến (**RFC Proposal**) chuẩn chỉnh và tạo GitHub Issue trực tiếp lên repository trung tâm CCBA Hub (`ccba-agent-platform`).

---

## 🎯 Mục Đích & Vai Trò
- **Giai đoạn Ý tưởng (Idea & RFC Phase):** Khi phát hiện bài toán mới, nhu cầu cải tiến công cụ, chuẩn hóa quy trình hoặc phát hiện lỗi ở cấp nền tảng nhưng chưa cần đóng gói mã nguồn ngay.
- **Tính đối xứng:** Là bước đi trước của `/ccba-contribute-to-hub` (đóng gói code & mở PR) trong chu trình đóng góp ngược (Upstream Contribution Loop).

---

## 📋 Các Bước Thực Hiện:

### Bước 1: Trích xuất Ngữ cảnh & Đánh giá Nhu cầu
Agent thu thập thông tin từ ngữ cảnh hội thoại hiện tại hoặc tài liệu tại Spoke:
1. **Loại đề xuất:** `feat` (tính năng/kỹ năng mới), `fix` (sửa lỗi nền tảng), `refactor` (tối ưu kiến trúc/deep seams), `docs` (chuẩn hóa tài liệu/hiến pháp).
2. **Tiêu đề ngắn gọn:** Dưới 10 từ theo định dạng `type(scope): mô tả ngắn`.
3. **Nỗi đau thực tế (Pain Point):** Vấn đề cụ thể gặp phải tại dự án Spoke hiện tại.
4. **Giải pháp kỹ thuật dự kiến:** Ý tưởng module, skill, workflow, rules, hoặc API contract cần bổ sung trên Hub.

---

### Bước 2: Kiểm tra Trùng lặp trên Hub
Trước khi tạo Issue mới, Agent chủ động kiểm tra xem vấn đề đã được ghi nhận hoặc giải quyết trên Hub hay chưa:
1. **Kiểm tra Issues hiện có:**
   ```bash
   gh issue list --repo vvChu/ccba-agent-platform --limit 30
   ```
2. **Kiểm tra Catalog Hub:**
   Đọc tệp `catalog.yaml` (qua đường dẫn `hub_path` trong `.md/workspace_context.yaml` nếu có) để xác nhận kỹ năng/công cụ tương tự chưa tồn tại.

*Nếu phát hiện đã có Issue tương tự:* Gợi ý người dùng bổ sung thảo luận vào Issue cũ thay vì tạo mới.

---

### Bước 3: Soạn Thảo Bản Đề Xuất (RFC Proposal Body)
Soạn thảo nội dung Issue theo cấu trúc chuẩn CCBA RFC:

```markdown
### 1. Bối cảnh & Vấn đề (Context & Problem):
- Mô tả thực trạng và lý do phát sinh nhu cầu từ dự án Spoke.
- Tác động tiêu cực nếu không xử lý (Token OpEx, lỗi dữ liệu, thiếu tính năng).

### 2. Đề xuất giải pháp (RFC Proposal):
- Kiến trúc / Kỹ năng / Package / Workflow dự kiến triển khai trên Hub.
- Phân tích tính tương thích và khả năng tái sử dụng cho các Spokes khác.

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [ ] Tiêu chí 1 (Code / Package / Seam)
- [ ] Tiêu chí 2 (Workflow / Skills Catalog)
- [ ] Tiêu chí 3 (Tài liệu Hiến pháp & Tests)

---
*Được đề xuất tự động từ Spoke `[tên-spoke]` qua workflow `/ccba-issue-to-hub`.*
```

Agent trình bày bản thảo cho người dùng xem và xác nhận trước khi gửi.

---

### Bước 4: Mở GitHub Issue Trực Tiếp Trên Hub Repo
Thực thi tạo Issue thông qua GitHub CLI:

```bash
gh issue create --repo vvChu/ccba-agent-platform --title "[Tiêu đề]" --body "[Nội dung RFC]"
```

*Trường hợp không có kết nối `gh` CLI hoặc thiếu token:*
Cung cấp toàn bộ nội dung markdown đã định dạng kèm đường dẫn tạo issue thủ công:
👉 `https://github.com/vvChu/ccba-agent-platform/issues/new`

---

### Bước 5: Báo Cáo & Hướng Dẫn Vòng Đời Tiếp Theo
Sau khi tạo thành công, Agent gửi phản hồi tổng kết:
1. **Mã số & Link Issue:** Ví dụ `#209 - https://github.com/vvChu/ccba-agent-platform/issues/209`.
2. **Hướng dẫn chu trình khép kín tiếp theo:**
   - Khi có prototype/script nháp tại Spoke $\to$ Tốt nghiệp mã nguồn: `/ccba-graduate-rd --issue #[ISSUE_ID]`
   - Khi mở PR chính thức lên Hub $\to$ Đóng gói & mở PR: `/ccba-contribute-to-hub --issue #[ISSUE_ID]` (Tự động gắn mã `Closes #[ISSUE_ID]`).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-knowledge-loop

---
name: ccba-knowledge-loop
description: Quy trình Vòng lặp Tri thức & Định hướng toàn trình (Recon → Brainstorm
  → Wayfinder → Exec)
disable-model-invocation: true
bundle: _core
command: /ccba-knowledge-loop
triggers:
- knowledge-loop
- vòng lặp tri thức
- trinh sát thảo luận hoạch định
---
# Quy trình Vòng lặp Tri thức & Định hướng (/ccba-knowledge-loop)

Quy trình này hướng dẫn Agent cách kết hợp đồng bộ 4 kỹ năng cốt lõi của CCBA Agent Services Platform: [YouTube-Learn](../skills/ccba-youtube-learn/SKILL.md) (Trinh sát tri thức video), [Research](../skills/ccba-research/SKILL.md) (Nghiên cứu ngầm), [Brainstorm](ccba-brainstorm.md) (Hội chẩn giải pháp) và [Wayfinder](../skills/ccba-wayfinder/SKILL.md) (Lập lộ trình) để giải quyết một bài toán kỹ thuật/nghiệp vụ lớn và mơ hồ (Foggy Problem) mà không gây block phiên làm việc hoặc làm tràn ngữ cảnh (token bloating).

---

## 📋 Tiêu chí hoàn thành (Completion Criteria)

Quy trình chỉ được coi là thực thi thành công khi đáp ứng:
1. [x] Đã trinh sát và ingest tri thức nền tảng (Video/VBPL/Code) vào Knowledge Base của dự án.
2. [x] Đã tổ chức brainstorm để thống nhất giải pháp thô và tạo Session Document chứa các Action Items.
3. [x] Đã lập Bản đồ định hướng (`map.md`) thông qua Wayfinder với Điểm đích (Destination) và các Frontier Tickets.
4. [x] Các ticket Research được giao cho subagent chạy ngầm tự động và cập nhật kết quả ngược lại bản đồ tuần tự.

---

## 🛠️ Hướng dẫn thực thi các Phase

### Phase 1: Trinh sát & Thu thập Tri thức Sơ cấp (Reconnaissance)
Khi đối mặt với yêu cầu mới hoặc vùng tri thức chưa được định hình rõ ràng:
1. **Bóc tách video/bài giảng:** Agent chạy [/ccba-youtube-learn](../skills/ccba-youtube-learn/SKILL.md) trên các video hướng dẫn của chuyên gia, webinar công nghệ hoặc seminar tập huấn liên quan để thu thập tri thức thực hành và các slide tĩnh.
   * *Đầu ra:* `notes_concept_[video_id].md` và thế giới quan `notes_worldview_[video_id].md`.
2. **Nghiên cứu ngầm tài liệu sơ cấp:** Agent chính kích hoạt [/ccba-research](../skills/ccba-research/SKILL.md) để spawn subagent chạy ngầm quét các văn bản pháp lý (VBPL), API docs của bên thứ ba, hoặc cấu trúc code hiện có.
   * *Đầu ra:* File báo cáo `.md/knowledge/research_and_studies/research_[chủ_đề]_[timestamp].md`.
3. **Đọc và nạp ngữ cảnh:** Agent chính nạp các tài liệu được sinh ra ở trên vào thư mục tri thức nháp của dự án để chuẩn bị làm ngữ cảnh cho Phase tiếp theo.

Tiêu chí hoàn thành: Toàn bộ tài liệu bóc tách từ video (`notes_concept_[video_id].md`) và báo cáo nghiên cứu ngầm (`research_[chủ_đề]_[timestamp].md`) hiện diện đầy đủ trong thư mục dự án và được nạp vào ngữ cảnh của Agent chính.

---

### Phase 2: Hội chẩn & Sáng tạo Phương án (Brainstorming)
Sau khi có dữ liệu trinh sát, Agent cùng User thống nhất phương án triển khai thô:
1. **Nạp tri thức:** Kích hoạt [/ccba-brainstorm](ccba-brainstorm.md). Đảm bảo các ghi chú và báo cáo nghiên cứu ở Phase 1 nằm trong thư mục `input_documents/` để làm nền tảng tri thức.
2. **Hybrid Rhythm:** Thực hiện thảo luận hai chiều tuân thủ nghiêm ngặt 4 nhịp:
   * **Prompt:** Agent đặt đúng 1 câu hỏi mở.
   * **User first:** Chờ user trả lời, giữ nguyên văn với tag `(user)`.
   * **AI Build:** AI bổ sung 2-4 ý tưởng mới với tag `(AI)` xây dựng trên ý tưởng của user (Yes-and).
   * **Return floor:** Trả quyền điều khiển kèm đúng 1 câu hỏi mở tiếp theo.
3. **Party Mode (Phản biện đa vai):** Kích hoạt Party Mode. Sử dụng thông tin từ tệp `notes_worldview.md` của diễn giả ở Phase 1 để tạo Persona ảo phản biện sắc nét các điểm yếu của phương án (ví dụ: *Persona "Kỹ sư Skeptic"* phản biện về tính khả thi, *Persona "Cảnh sát PCCC"* phản biện về tính pháp lý).
4. **Hội tụ:** Gom nhóm ý tưởng, nhờ user xếp hạng và ghi nhận Session Document chứa các **Action Items**.

Tiêu chí hoàn thành: Người dùng đã xếp hạng các ý tưởng ưu tiên và Agent đã tạo thành công tệp Session Document ghi nhận Action Items trong thư mục dự án.

---

### Phase 3: Hoạch định & Thiết lập Bản đồ (Wayfinder Mapping)
Tổ chức các Action Items rời rạc thành một lộ trình có cấu trúc:
1. **Thiết lập bản đồ:** Kích hoạt [/ccba-wayfinder](../skills/ccba-wayfinder/SKILL.md) để khởi tạo bản đồ định hướng tại `.md/knowledge/issues/<feature>/map.md`.
2. **Cấu trúc bản đồ:**
   * **Điểm đích (Destination):** Xác định rõ tiêu chí nghiệm thu hoàn thành của bài toán.
   * **Frontier Tickets:** Các ticket mở, sẵn sàng thực thi ngay và độc lập với các ticket khác. Phân loại rõ: *Research [AFK]*, *Prototype [HITL]*, *Grilling [HITL]*, *Task [HITL/AFK]*.
   * **Sương mù chiến trận / Chưa xác định rõ (Not yet specified):** Chỉ ghi nhận các vùng thông tin và quyết định đã rõ ràng; các phần chưa thể nhìn thấy sẽ được giữ lại trong mục này dưới dạng ghi chú phác thảo cho đến khi đủ thông tin unblock.
3. **Tham chiếu theo tên:** Mọi ticket đều phải có tên gọi và link Markdown cụ thể (Ví dụ: `[Đóng gói Mutex Lock](../skills/ccba-wayfinder/SKILL.md)`).

Tiêu chí hoàn thành: Bản đồ định hướng `map.md` được khởi tạo với mục Điểm đích (Destination) rõ ràng và ít nhất một Frontier ticket được tạo lập.

---

### Phase 4: Vận hành Thực thi Song song & Đóng gói Quyết định
Giải quyết các Frontier Tickets và mở rộng bản đồ:
1. **Phân phối AFK:** Với các ticket thuộc loại **Research [AFK]**, Agent chính kích hoạt [/ccba-research](../skills/ccba-research/SKILL.md) để spawn subagent chạy ngầm xử lý, đồng thời tiếp tục nhận các yêu cầu khác từ người dùng trong khi subagent đang chạy.
2. **Tự động cập nhật:** Khi subagent nghiên cứu hoàn thành và xuất báo cáo (xác nhận file báo cáo thực sự tồn tại), Agent chính hấp thụ kết quả, đóng (close) ticket tương ứng, cập nhật vào mục **Quyết định đã chốt (Decisions so far)** trên bản đồ.
3. **Mở rộng biên giới:** Dựa trên kết quả vừa chốt, chuyển đổi các vùng mờ trong mục *Not yet specified* thành các ticket Frontier mới.
4. **Giải quyết vùng mờ đột xuất:** Nếu biên giới bản đồ gặp sương mù quá dày không thể tự quyết, Agent đề xuất chạy một phiên [/ccba-brainstorm](ccba-brainstorm.md) mini với User để thống nhất hướng đi tiếp theo.

Tiêu chí hoàn thành: Mọi ticket trên bản đồ được chuyển sang trạng thái đóng (closed), không còn Frontier ticket nào chưa giải quyết và lộ trình đạt tới Điểm đích hoàn toàn.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*


---

# Archived Workflow: ccba-legal-advisor

---
description: "Tư vấn & Giải đáp Pháp lý Xây dựng: Tự động phân tích câu hỏi mơ hồ, phỏng vấn làm rõ thích ứng, truy xuất tri thức OKF v2.2 và xuất Phiếu Ý kiến Pháp lý (Legal Opinion) chuẩn mực. Kích hoạt khi người dùng hỏi các câu hỏi về cấp phép xây dựng, PCCC, nghiệm thu, đấu thầu, hoặc xin tư vấn pháp lý công trình."
bundle: _consulting
command: /ccba-legal-advisor
triggers:
  - legal-advisor
  - tư vấn pháp lý
  - giải đáp pháp lý
  - ý kiến pháp lý
  - legal opinion
disable-model-invocation: true
---

# Workflow: Tư Vấn & Giải Đáp Pháp Lý Xây Dựng (/ccba-legal-advisor)

Khi người dùng kích hoạt lệnh này hoặc đặt các câu hỏi liên quan đến tư vấn quy chuẩn, cấp phép, nghiệm thu hay thẩm tra pháp lý công trình, Agent hãy nạp và thực thi kỹ năng `legal-advisor` tại [SKILL.md](../skills/ccba-legal-advisor/SKILL.md) để:
1. Tiếp nhận câu hỏi và phân loại độ phức tạp (Fast-track hoặc Phỏng vấn thích ứng).
2. Lồng ghép linh hoạt 4 Khung Mẫu Tương Tác Động (Diagnostic, Time-Travel, Matrix Checklist, Atomic Template).
3. Truy xuất chính xác cây điều khoản AST và bảng số liệu 2D từ kho tri thức OKF v2.2.
4. Trình bày câu trả lời theo đúng Form Phiếu Giải Đáp Pháp Lý CCBA 4 phần.


---

# Archived Workflow: ccba-legal-ingest

---
description: Workflow tự động hóa toàn trình nạp văn bản pháp lý OKF v2.4 Universal Agent-Centric
disable-model-invocation: true
bundle: _consulting
command: /ccba-legal-ingest
triggers:
- ccba-legal-ingest
- nap van ban
- thu thap van ban
- harvest legal doc
- ingest law
conforms_to:
- "ADR-0016"
- "ADR-0021"
- "ADR-0029"
- "ADR-0030"
- "ADR-0031"
- "ADR-0034"
- "ADR-0035"
- "ADR-0036"
- "ADR-0037"
---
# Workflow: Nạp Văn Bản Pháp Lý Toàn Trình (/ccba-legal-ingest)

> **Mô tả:** Workflow tự động hóa tuần tự quy trình nạp văn bản pháp lý mới từ Thư Viện Pháp Luật (TVPL VIP Pro) vào Kho Tri Thức Chuẩn **OKF v2.4 Universal Agent-Centric (ADR 0034 – ADR 0037)**, bao gồm: Thu thập 3 tầng (Google Drive Vault) -> Trích xuất nguyên văn DOCX AST 100% -> Hợp nhất VBHN -> Nghiệm thu Master CI 11 Gates Spoke.

---

## 🚀 Các Bước Thực Hiện Của Agent

```
[Bước 0: Thu thập & Xác thực] ──► [Bước 1: OKF v2.4 Convert] ──► [Bước 2: VBHN Consolidation] ──► [Bước 3: 1-Command Master CI]
 (ingest --upload-drive)          (Zero-LLM Verbatim AST)         (Nếu có văn bản sửa đổi)          (validate_legal_spoke.py)
```

---

### Bước 0: Thu Thập & Xác Thực Nguồn Gốc (Giao thức "Một Cửa `tab=7`" - ADR 0035, ADR 0036)

* **Kịch bản 1 — Nạp tự động 1 lệnh toàn trình (Happy Path):**
  ```powershell
  python -m ccba_legal ingest "<URL_HOAC_SO_HIEU>" --category <01_vbpl|02_qcvn|03_tcvn> --upload-drive
  ```
  *(Tự động tải DOCX Gold Source + PDF Công báo số hóa vào `sources/`, chuyển đổi sang OKF v2.4 Bundle, đồng bộ lên Google Drive Vault `CCBA_Legal_Vault` và sinh Native Google Docs cho NotebookLM)*.

* **Kịch bản 2 — Tiếp nhận thủ công / Fallback khi cào bị lỗi:**
  Nếu việc cào tự động gặp trở ngại (Cloudflare/Captcha), Agent giải quyết cục bộ bằng script CDP/thủ công để đưa đúng 2 tệp `.docx` và `.pdf` vào `legal_docs/<category>/<doc_slug>/sources/`. **Sau khi có file, BẮT BUỘC thực thi Bước 1 bằng lệnh `convert` — TUYỆT ĐỐI CẤM tự viết file Markdown bằng LLM.**

* **Kịch bản 3 — Làm mới / Thay thế file scan mờ bằng bản nét (Force Refresh):**
  Chạy lệnh tải đè bản đẹp vào `sources/` rồi chuyển sang Bước 1:
  ```powershell
  python -m ccba_legal fetch "<tvpl_url>" -o "legal_docs/<category>/<doc_slug>/sources"
  ```

---

### Bước 1: Chuyển Đổi Sang OKF v2.4 Bundle (Zero-LLM Deterministic AST - ADR 0037)

* Thực thi lệnh chuyển đổi trích xuất nguyên văn $100\%$ từ DOCX gốc:
  ```powershell
  python -m ccba_legal convert --docx-path "legal_docs/<category>/<doc_slug>/sources/<doc_slug>.docx" --target-bundle-dir "legal_docs/<category>/<doc_slug>"
  ```
* **Quy chuẩn bất biến (Core Invariants):**
  - Thân văn bản Markdown trích xuất xác định $1:1$ từ DOCX (cấm LLM rewrite).
  - Phân tách rạch ròi 4 ngăn kéo: `tables/`, `figures/`, `annexes/`, `templates/`.
  - Toàn bộ file gốc DOCX + PDF nằm trong `sources/`.
  - Tự động sinh cây điều khoản AST `clauses.json` và bộ câu hỏi `qa_benchmark.json`.

---

### Bước 2: Hợp Nhất Văn Bản Sửa Đổi (VBHN Engine — nếu có)

* Nếu văn bản có sửa đổi/bổ sung, thực thi lệnh hợp nhất AST:
  ```powershell
  python -m ccba_legal consolidate `
    --manifest "legal_docs/<category>/<doc_slug>/patch_manifest.yaml" `
    --base "legal_docs/<category>/<doc_slug>/sources/<doc_slug>_goc.md" `
    --output "legal_docs/<category>/<doc_slug>"
  ```
* Bắt buộc sinh ma trận so sánh đồng vị `bang_so_sanh_thay_doi.md` tại gốc bundle (ADR 0036).

---

### Bước 3: Đăng Ký Sổ Bộ & Nghiệm Thu Master CI Gate (1-Command Automation)

1. Cập nhật `bundle_path`, `pdf_path`, `pdf_sha256`, `pdf_status: verified` và khối `source_assets` vào `legal_registry.yaml`.
2. Chạy bộ kiểm định 11 Cổng Master Spoke CI Validator:
   ```powershell
   python scripts/validate_legal_spoke.py
   ```
3. **Tiêu chuẩn nghiệm thu:** `0 Errors, 0 Warnings, 100% Visual Parity, 100% Verbatim Match (Gate 11 >= 98.0%), 100% PDF SHA-256 Match`.


---

# Archived Workflow: ccba-legal-intel

---
description: Workflow tư vấn và rà soát pháp luật xây dựng Việt Nam với RAG và Grounding
  Gate
disable-model-invocation: true
bundle: _consulting
command: /ccba-legal-intel
triggers:
- ccba-legal-intel
- crawl law
- diff law
- legal checklist
- thuvienphapluat
- tvpl
---
# Workflow: Tư Vấn & Rà Soát Pháp Luật Xây Dựng (/ccba-legal-intel)

> **Mô tả:** Workflow tự động cào, tra cứu RAG, đối chiếu và tư vấn giải đáp thắc mắc pháp lý xây dựng Việt Nam với cơ chế kiểm định trích dẫn nguồn bắt buộc (Grounding Gate).

## Các bước thực hiện của Agent

### 1. Tiếp nhận Câu hỏi & Nạp Sổ bộ (`legal_registry.yaml`)
- Nạp module `scripts/legal_rag_indexer.py` và đọc cơ sở dữ liệu pháp lý tại `.agents/skills/ccba-legal-document-tracker/resources/legal_registry.yaml`.
- Phân tích câu hỏi của người dùng để xác định các từ khóa trọng tâm (Luật Xây dựng, Nghị định QLCL, Giấy phép xây dựng, PCCC, Hợp đồng...).

---

### 2. Tra cứu RAG & Trích xuất Văn bản
- Chạy hàm `search_legal_registry(query, registry_path)` để tìm 3-5 văn bản pháp lý phù hợp nhất.
- Kiểm tra trạng thái vòng đời văn bản (Văn bản còn hiệu lực `current`, Hết hiệu lực `superseded`, hay Dự thảo `draft`).
- Trích xuất chính xác Điều, Khoản, Điểm điều luật liên quan.

---

### 3. Kiểm định Grounding Gate (`scripts/legal_grounding_gate.py`)
- Kiểm tra câu trả lời tư vấn với hàm `verify_legal_grounding(response_text, retrieved_docs)`.
- **Rào chắn:** Nếu câu trả lời thiếu trích dẫn nguồn dạng `[Short Name - Doc Number]` hoặc suy diễn không có căn cứ, Agent bắt buộc phải bổ sung trích dẫn hoặc gắn cảnh báo ungrounded.

---

### 4. Định dạng Đầu ra & Đính kèm Disclaimer
- Đặt trích dẫn nguồn chi tiết tại từng ý kiến tư vấn.
- Đính kèm tự động disclaimer chuẩn CCBA:

```markdown
---
⚠️ **Disclaimer:** Nội dung tư vấn trên được tự động trích xuất và kiểm định bằng AI Agent dựa trên Sổ bộ Pháp lý CCBA (`legal_registry.yaml`). Đây là thông tin tham khảo kỹ thuật, KHÔNG phải văn bản tư vấn pháp lý chính thức. Luôn cần chuyên gia pháp lý hoặc Luật sư xác nhận trước khi áp dụng vào dự án thực tế.
```

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-loop-me

---
description: Thiết kế chu trình lặp (Loops) trong công việc và biên soạn thành đặc
  tả workflow mới.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-loop-me
triggers:
- loop-me
- loop me
- thiết kế chu trình
---
# Workflow: Thiết kế chu trình công việc (/ccba-loop-me)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `loop-me` tại [SKILL.md](../skills/ccba-loop-me/SKILL.md) để bắt đầu chuỗi phỏng vấn Socrates làm rõ và sinh workflow mới.


---

# Archived Workflow: ccba-new-feature

---
description: Tạo feature branch mới với quy trình lập kế hoạch và phân tách session sạch (Factory Model)
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-new-feature
triggers:
- new feature
- feature mới
- tạo branch
---
# Workflow: Tạo Feature Branch Mới & Phân Tách Session (Factory Model)

Quy trình tự động hóa dọn dẹp các branch cũ, khởi tạo branch tính năng mới và cưỡng chế áp dụng mô hình Nhà máy (**The Factory Model**) tách biệt giữa **Planning** và **Coding** để tối ưu hóa chi phí Token (OpEx) và ngăn ngừa lỗi mã nguồn.

## Các bước thực hiện:

### Bước 1: Chuẩn bị môi trường & Pre-Flight Check
1. **Kiểm tra trạng thái Working Tree:**
   ```bash
   git status --short
   ```
   *Nếu có uncommitted changes dở dang, yêu cầu `git commit` hoặc `git stash` trước khi chuyển nhánh.*
2. **Quay về branch `main` và kéo code mới nhất:**
   ```bash
   git checkout main && git pull origin main
   ```

### Bước 2: Dọn dẹp các branch cũ đã merge
Dọn dẹp các branch cục bộ đã được tích hợp vào `main` (hỗ trợ cả merge thông thường và dọn dẹp prune):
- **Windows PowerShell:**
  ```powershell
  git fetch -p
  git branch --merged main | Where-Object { $_ -notmatch 'main' -and $_ -notmatch '^\*' } | ForEach-Object { git branch -d $_.Trim() }
  ```
- **Bash (Linux / macOS / Git Bash):**
  ```bash
  git fetch -p
  git branch --merged main | grep -vE '^\*|main$' | xargs -r git branch -d
  ```

### Bước 3: Thu thập thông tin & Bóc tách Issue tự động (Hỗ trợ Offline Fallback)
- **Trường hợp 1 (Có mã Issue, ví dụ `/ccba-new-feature #228`):**
  1. Agent ưu tiên gọi GitHub CLI để trích xuất thông tin:
     ```bash
     gh issue view <issue_id> --json title,body,labels
     ```
  2. **Offline / Local Fallback:** Nếu mất mạng hoặc `gh` chưa đăng nhập, Agent tự động đọc tệp cục bộ `.md/knowledge/issues/issue-<issue_id>.md`.
  3. **Nhận diện tự động:**
     - Tự động nhận diện loại công việc từ tiêu đề hoặc labels: `feat(...)` $\rightarrow$ `feat`, `fix(...)` $\rightarrow$ `fix`, `docs(...)` $\rightarrow$ `docs`, `refactor(...)` $\rightarrow$ `refactor`.
     - Tự động trích xuất nội dung **Agent Brief** (nếu đã qua `/ccba-triage`) để chuyển thẳng sang Bước 6.
     - Tự động đề xuất tên branch ở Bước 4 mà **không cần hỏi lại người dùng**.
- **Trường hợp 2 (Không cung cấp mã Issue):**
  Hỏi người dùng lần lượt các thông tin:
  1. Loại công việc cần thực hiện: `feat` (tính năng mới), `fix` (sửa lỗi), `docs` (tài liệu), `refactor` (cải tiến cấu trúc), hoặc `experiment` (thử nghiệm).
  2. Mô tả ngắn gọn tính năng (3-5 từ).

### Bước 4: Đề xuất tên branch chuẩn định danh
Dựa trên thông tin thu thập được, đề xuất tên branch theo định dạng chuẩn CCBA có gắn mã Issue:
- `feat/issue-<id>-<ten-ngan-gon>` (hoặc `feat/<ten-tinh-nang>` nếu không có issue)
- `fix/issue-<id>-<ten-loi>` (hoặc `fix/<ten-loi>` nếu không có issue)
- `docs/issue-<id>-<ten-tai-lieu>`
- `refactor/issue-<id>-<ten-module>`
- `experiment/<ten-thu-nghiem>`

*Quy tắc đặt tên branch:* Viết thường hoàn toàn (lowercase), sử dụng dấu gạch ngang `-` thay cho khoảng trắng, ngắn gọn, có thể truy vết ngược về Issue.

### Bước 5: Khởi tạo branch mới
Sau khi chốt tên branch, tạo và chuyển sang branch mới:
```bash
git checkout -b [ten_branch_da_chot]
```

### Bước 6: Lập kế hoạch thiết kế (Planning Phase — Triage Fast-Path & Socrates Grill)
Agent **bắt buộc** phải chuyển sang **Planning Mode**, tuyệt đối không được viết code ở bước này:
1. **Triage Fast-Path (Smart Skipping):**
   - Nếu Issue đã có sẵn **Agent Brief** chuẩn từ `/ccba-triage`: Agent tự động nạp yêu cầu, bỏ qua các câu hỏi phỏng vấn cơ bản và chỉ chất vấn 1-2 câu kiến trúc cốt lõi nếu thực sự cần thiết.
   - Nếu chưa có Agent Brief: Kích hoạt `/ccba-grilling` để phỏng vấn người dùng và stress-test các giả định.
2. **Soạn thảo Kế hoạch Triển khai (`implementation_plan.md`):**
   - Bắt buộc có mục `## Đánh giá khả năng tái sử dụng (Reuse Assessment)` tra cứu `catalog.yaml` (ADR 0047).
   - Xác định rõ các Deep Seams (khớp nối) và Scoped Verification Plan.
3. **Phê duyệt:** Đợi người dùng nhấn **Proceed** phê duyệt bản kế hoạch.

### Bước 7: Bàn giao cô lập ngữ cảnh (Factory Model Hand-off & Smart Routing)
Sau khi bản kế hoạch được duyệt, để ngăn ngừa phình to ngữ cảnh hội thoại (Context Rot) và giảm OpEx:
- **Định tuyến thực thi (Execution Routing):** Đọc khuyến nghị từ Agent Brief:
  - 🟢 **Standard** (`/ccba-implement`): Mở session chat mới sạch sẽ và gọi `/ccba-implement`.
  - 🟣 **Deep Reasoning** (`/boost`): Kích hoạt điều tra chuyên sâu cho logic thuật toán phức tạp.
  - 🔵 **Multi-Agent Orchestration** (`/ccba-teamwork` hoặc `invoke_subagent`): Phân rã Seams và chạy đa tác nhân song song.

### Bước 8: Lập trình, Kiểm chứng & Tự sửa lỗi (Coding & Verification Phase)
Coding Agent thực hiện nhiệm vụ:
1. Khởi tạo danh mục theo dõi `task.md`.
2. Viết mã nguồn tương thích, áp dụng type hints và docstring chuẩn Google/CCBA.
3. **Thực thi Cổng Kiểm định Tự động (Automation-First Quality Gates):**
   - `python scripts/safe_pytest.py -f tests/test_xxx.py` (chạy scoped test an toàn).
   - `ruff check packages/ scripts/ tests/` (linter & format).
   - `mypy packages/ scripts/` (static type checker).
   - `python scripts/spoke/check_hub_import_depth.py` & `check_spoke_cleanliness.py` (ADR 0044).
   - `python scripts/eval/run_harness_evals.py` (hoặc `/ccba-eval-gate`).
4. Nếu phát hiện linter hoặc type check báo lỗi, tự động kích hoạt **Self-Healing Loop** tối đa 3 lần.
5. Khi tất cả các Gates đều vượt qua thành công (PASS), bàn giao kết quả qua tệp `walkthrough.md` cho người dùng nghiệm thu trước khi tạo PR (`/ccba-create-pr`).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-notebooklm

---
description: Kết nối tự động với NotebookLM để import YouTube/tài liệu, trích xuất
  tóm tắt, RAG query hoặc tạo Audio Overview.
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
disable-model-invocation: true
command: /ccba-notebooklm
triggers:
- notebooklm
- rag query
- audio overview
- podcast
---
# Workflow: NotebookLM Connector (/ccba-notebooklm)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `notebooklm-connector` tại [SKILL.md](../skills/ccba-notebooklm-connector/SKILL.md) để bắt đầu chu trình kết nối, xác thực và xử lý tri thức với Google NotebookLM Cloud.


---

# Archived Workflow: ccba-prepare-seminar

---
description: Chuẩn bị nội dung cho buổi seminar/thảo luận nội bộ CCBA
applies_to:
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _consulting
disable-model-invocation: true
command: /ccba-prepare-seminar
triggers:
- chuẩn bị seminar
- buổi thảo luận
- prepare seminar
---
# Workflow: Prepare Seminar (/ccba-prepare-seminar)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `seminar-builder` tại [SKILL.md](../skills/ccba-seminar-builder/SKILL.md) để bắt đầu quy trình chuẩn bị nội dung, chương trình nghị sự và recap cho buổi seminar.


---

# Archived Workflow: ccba-promote-sandbox

---
description: Thăng cấp và bàn giao sản phẩm từ Spoke Cá Nhân sang Spoke Dự Án hoặc
  Hub (ADR 0046)
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
- Tác vụ Admin
bundle: _core
disable-model-invocation: true
command: /ccba-promote-sandbox
triggers:
- promote sandbox
- bàn giao sandbox
- thăng cấp sản phẩm
- nghiệm thu pgv
- pgv handover
---
# Workflow: Thăng Cấp & Bàn Giao Sản Phẩm Từ Sandbox (/ccba-promote-sandbox)

Workflow này hướng dẫn kỹ sư thực hiện quy trình thăng cấp bàn giao 3 bước để chuyển giao sản phẩm nghiên cứu, bản tính hoặc báo cáo từ **Spoke Cá Nhân (`personal_sandbox`)** sang **Spoke Dự Án chính thức (`project_delivery`)** hoặc đề xuất lên Hub theo **ADR 0046** và **Quy chế CCBA 2026**.

---

## 🛡️ Bước 1: Khảo Sát & Xác Thực Môi Trường Nguồn

1. Agent đọc tệp `.md/workspace_context.yaml` tại thư mục hiện tại.
2. **Kiểm tra điều kiện tiên quyết:**
   - Workspace phải được cấu hình là Spoke Cá Nhân (`sub_type: personal_sandbox` hoặc `guardrails.sandbox_mode: true`).
   - Nếu không phải sandbox, Agent thông báo:
     > *"Thư mục hiện tại không phải là Spoke Cá Nhân. Quy trình này chỉ áp dụng cho môi trường sandbox."*

---

## 📋 Bước 2: Xác Định Sản Phẩm & Dự Án Đích

Agent hỗ trợ kỹ sư xác định các tham số bàn giao:

1. **Danh sách tệp bàn giao (`--files`):**
   - Quét các tệp hoàn thiện trong `output/`, `specs/`, `scripts/` (ví dụ: `output/pccc_audit_report.md`).
2. **Đường dẫn Spoke Dự Án đích (`--target`):**
   - Đường dẫn thư mục của Spoke Dự Án thụ hưởng (ví dụ: `D:/GitHubProjects/2026-04-dh-viet-nhat`).
   - *Nếu là công cụ/script dùng chung:* Hướng dẫn kỹ sư sử dụng lệnh `/ccba-propose-to-hub` thay thế.
3. **Mã Phiếu Giao Việc (`--pgv`):**
   - Mã PGV được phân công trên IDOP (ví dụ: `PGV-2026-08-014`).

---

## ⚙️ Bước 3: Thực Thi Thăng Cấp 3 Bước (Single-Command Promotion)

Agent xác định đường dẫn Hub (`hub_path`) và thực thi lệnh thăng cấp:

```powershell
python "[hub_path]\scripts\promote_sandbox.py" --target "[duong_dan_spoke_dich]" --files [danh_sach_tep] --pgv "[ma_pgv]"
```

*Động cơ `SandboxPromoter` sẽ tự động thực hiện tuần tự:*
1. **Pha 1 (Cleanse & Validate):** Rà soát và gỡ bỏ hoàn toàn thủy ấn `[CCBA SANDBOX DRAFT]` để chuẩn hóa thành phẩm.
2. **Pha 2 (Target Ingestion):** Sao chép tệp sạch sang Spoke Dự Án đích, tự động tạo thư mục cha và tính mã băm SHA-256 bất biến.
3. **Pha 3 (PGV Sign-off Staging):** Tạo biên nhận `.md/idop_staged/pgv_handover_[pgv]_[timestamp].json` lưu trữ thông tin kỹ sư (`owner_name`, `seat_role`) và commit SHA để phục vụ nghiệm thu trên SharePoint IDOP.

---

## 🎯 Bước 4: Hướng Dẫn Nghiệm Thu & Giải Ngân Tầng 3 (Điều 17 Quy Chế 2026)

Agent in báo cáo xác nhận thành công:
> ✅ **Đã bàn giao thành công `[so_tep]` tệp sang Spoke `[ten_du_an_dich]`.**
> 📋 **Biên nhận nghiệm thu IDOP:** `[duong_dan_receipt]`
> 
> 💡 **Bước tiếp theo:** Vui lòng thông báo cho Chủ nhiệm Hợp đồng (`CHU_TRI_HOP_DONG_PM`) hoặc Trưởng phòng chuyên môn để thực hiện kiểm tra Cấp 2 và phê duyệt nghiệm thu Phiếu Giao Việc `[ma_pgv]` trên hệ thống IDOP.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*\n

---

# Archived Workflow: ccba-propose-to-hub

---
name: propose-to-hub
description: '[Alias tương thích ngược của /ccba-contribute-to-hub] Đóng gói mã nguồn, tests, proposal từ Spoke và mở PR lên Hub'
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
disable-model-invocation: true
command: /ccba-propose-to-hub
triggers:
- đề xuất
- tích hợp Hub
- contribution
- propose
- skill mới
---
# Workflow: Propose to Hub (Alias -> /ccba-contribute-to-hub)

> [!NOTE]
> **Định tuyến chuẩn hóa:** Workflow này là Alias tương thích ngược (Backward Compatibility) của [`/ccba-contribute-to-hub`](ccba-contribute-to-hub.md).
> - Để đề xuất **Ý tưởng / RFC / Báo lỗi**, sử dụng: [`/ccba-issue-to-hub`](ccba-issue-to-hub.md).
> - Để đóng gói **Mã nguồn / Tests / Mở PR**, sử dụng: [`/ccba-contribute-to-hub`](ccba-contribute-to-hub.md).

---

## Quy Trình Thực Thi:
Vui lòng tham khảo chi tiết toàn bộ các bước tại [`.agents/workflows/ccba-contribute-to-hub.md`](ccba-contribute-to-hub.md):
1. **Bước 1:** Thu thập thông tin & Mã nguồn đóng gói.
2. **Bước 2:** Kiểm tra trùng lặp trên Hub (`catalog.yaml`, `packages/`).
3. **Bước 3:** Đóng gói mã nguồn & Tạo file proposal chuẩn ADR-0045 trên branch mới.
4. **Bước 4:** Mở GitHub Pull Request (`gh pr create`).
5. **Bước 5:** Vòng lặp dừng chờ bất đồng bộ & Tự làm xanh CI (Self-Healing Loop).
6. **Bước 6:** Báo cáo hoàn tất & Sẵn sàng cho Maintainer thẩm định (`/ccba-review-proposal`).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-prototype

---
name: ccba-prototype
command: /ccba-prototype
description: Khởi động quy trình xây dựng mẫu thử code thô (Logic hoặc UI) để giải
  quyết vấn đề thiết kế mờ mịt.
disable-model-invocation: true
bundle: _core
triggers:
- prototype
- mẫu thử
- test thô
- ccba-prototype
---
# Workflow: Dựng Mẫu Thử Nhanh (/ccba-prototype)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `ccba-prototype` tại [SKILL.md](../skills/ccba-prototype/SKILL.md) để bắt đầu quy trình dựng mẫu thử nhanh và dọn dẹp.


---

# Archived Workflow: ccba-release-feature

---
description: Merge PR, cleanup branch, auto-close local issues và cập nhật walkthrough
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-release-feature
triggers:
- release
- merge PR
- phát hành
---
# Workflow: Release Feature

Quy trình tự động hóa tích hợp mã nguồn (merge), kiểm tra Copilot Review, tự động đóng issue và dọn dẹp môi trường.

## Bước 0: Thực thi Kiểm thử Toàn diện Slow Integration Tests (Pre-release Gate)

*Quy tắc bắt buộc:* Trước khi thực hiện merge PR, Agent **bắt buộc phải chạy kiểm thử toàn bộ tập test `slow` và `stress`** để đảm bảo các bài test cào mạng/tích hợp không bị hỏng ngầm (test decay):

1. **Kiểm tra môi trường hiện tại (Hub vs Spoke):**
   - **Tại Hub Platform (`ccba-agent-platform`):**
     ```bash
     python scripts/eval/run_isolated_tests.py --all --stress
     ```
   - **Tại Spoke (Pháp điển / Knowledge Corpus / Specialized Spokes):**
     ```bash
     # Nếu spoke có script kiểm định chuyên sâu:
     python scripts/validate_legal_spoke.py
     # hoặc chạy toàn bộ test cô lập cục bộ:
     python scripts/eval/run_isolated_tests.py --all
     ```
2. Nếu có bài test nào thất bại, Agent **phải dừng quy trình release ngay lập tức** để tiến hành sửa lỗi trước khi tiếp tục.

---

## Bước 1: Đối soát bình luận và Merge PR trên GitHub

1. **Lấy thông tin PR và Branch hiện hành (Platform-Agnostic):**
   ```bash
   git branch --show-current
   gh pr view --json number,title,state,headRefName
   ```

2. **Kiểm tra xác thực GitHub CLI (`gh`):**
   ```bash
   gh auth status
   ```

3. **Kiểm tra trạng thái GitHub Actions CI:**
   ```bash
   gh pr checks
   ```
   - *Rào chắn Zero-Polling CI:* 
     - Nếu các checks đang ở trạng thái `pending`, Agent có thể khởi chạy `gh pr checks --watch` rồi **lập tức dừng gọi công cụ (End Turn)** để hệ thống đánh thức qua cơ chế *Reactive Wakeup* khi CI xanh.
     - **Tuyệt đối nghiêm cấm** chạy vòng lặp gọi `manage_task status` liên tiếp nhiều lần để thăm dò task `--watch`.

4. **Chốt chặn Review Requests của Copilot (Chống Race Condition Merge Sớm):**
   - Trước khi đọc comments, Agent **bắt buộc phải kiểm tra xem Copilot đã nộp bài review xong hay chưa**:
     ```bash
     gh pr view --json reviewRequests,reviews --jq '{pending: [.reviewRequests[]?.login], reviewed: [.reviews[]?.user.login]}'
     ```
   - *Quy tắc bắt buộc:*
     - Nếu danh sách `pending` chứa `copilot-pull-request-reviewer` (hoặc bot review) HOẶC Copilot chưa xuất hiện trong `reviewed` (nếu PR vừa tạo chưa quá 2 phút): Có nghĩa là Copilot **vẫn đang phân tích và chưa Submit Review**. Agent **tuyệt đối không được merge ngay**, mà phải dừng lượt hoặc chờ Copilot hoàn tất nộp bài.
     - Chỉ khi Copilot đã hoàn tất lượt review và nộp bài vào `reviews` (hoặc không có review pending), Agent mới chuyển sang bước 5.

5. **Thực hiện đối soát bình luận của Copilot trên PR:**
   ```bash
   gh pr view --json comments,reviews --jq '.comments[] | {id: .id, path: .path, line: .line, body: .body}'
   ```
   - Hoặc kiểm tra chi tiết các inline review comments:
     ```bash
     gh api repos/:owner/:repo/pulls/$(gh pr view --json number --jq .number)/comments --jq '.[] | {id: .id, path: .path, line: .line, body: .body}'
     ```
   - Nếu phát hiện bất kỳ bình luận nào của Copilot, Agent phải tạm dừng quy trình merge, đánh giá và thực hiện chỉnh sửa mã nguồn cục bộ, commit & push cập nhật, và cập nhật `walkthrough.md` trước khi tiếp tục.
   - Nếu phát hiện các góp ý hợp lý (VALID) chưa sửa, hoặc các góp ý không hợp lý chưa được giải trình trong `walkthrough.md`, Agent phải giải trình hoặc sửa lỗi cục bộ và push cập nhật trước khi merge.

6. **Tiến hành Merge khi 100% điều kiện đạt chuẩn:**
   - Nếu `gh` đã đăng nhập, CI pass (100% xanh) và Copilot review đã xử lý xong: Thực hiện merge và xóa remote branch tự động (sử dụng Squash and Merge để giữ lịch sử nhánh main tinh gọn):
     ```bash
     gh pr merge --squash --delete-branch
     ```
   - *Tùy chọn Auto-Merge:* Nếu CI vẫn đang chạy nốt những giây cuối, có thể kích hoạt cờ tự động merge:
     ```bash
     gh pr merge --squash --delete-branch --auto
     ```
   - Nếu `gh` chưa đăng nhập: Sử dụng `browser_subagent` truy cập trang PR, chờ CI và Review hoàn tất rồi chọn **Squash and merge** -> **Confirm squash and merge** -> **Delete branch**.

---

## Bước 2: Cập nhật Lịch sử Thay đổi (Walkthrough)

1. Lấy danh sách các commit của feature branch hiện tại (so sánh với `origin/main`) **trước khi** chuyển nhánh:
   ```bash
   git log origin/main..HEAD --oneline
   ```
2. Cập nhật nội dung tóm tắt thay đổi và kết quả nghiệm thu vào tệp tin `walkthrough.md`.

---

## Bước 3: Sync Local Codebase, Auto-Close Local Issue & Dọn dẹp

1. Kiểm tra trạng thái làm việc (working tree) để đảm bảo không có file nào bị dơ (uncommitted changes):
   ```bash
   git status --porcelain
   ```
   *Lưu ý:* Nếu có thay đổi chưa commit, hãy commit hoặc stash trước khi chuyển nhánh.

2. Quay về branch `main` và kéo code mới nhất:
   ```bash
   git checkout main && git pull origin main
   ```

3. Xóa branch feature cục bộ an toàn:
   ```bash
   git branch -D [feature_branch_name]
   ```

4. **Tự động đóng Issue Cục bộ (Offline Knowledge Base Mirror):**
   - Nếu PR giải quyết một issue cụ thể (ví dụ `#228`), kiểm tra tệp tin tương ứng tại `.md/knowledge/issues/issue-XXX.md`.
   - Cập nhật trường trạng thái trong metadata: `status: closed` (hoặc `state: closed`) kèm ghi chú liên kết PR đã merge.

---

## Bước 4: Thông báo hoàn tất

1. Báo cáo trạng thái hoàn tất rõ ràng:
   - ✅ Feature đã được tích hợp thành công vào `main`.
   - 🗑️ Branch cục bộ và remote đã được dọn dẹp sạch sẽ.
   - 📌 Issue liên quan đã được đóng (trên GitHub và CSDL cục bộ).
   - 📝 Lịch sử thay đổi `walkthrough.md` đã được lưu trữ hoàn tất.


---

# Archived Workflow: ccba-research

---
name: ccba-research
command: /ccba-research
description: Khởi động subagent nghiên cứu chạy ngầm để tra cứu tài liệu, APIs, source
  code hoặc VBPL song song dưới nền với rào chắn Search Budget Cap (5 tool calls)
  và Mẫu báo cáo 5 phần chuẩn hóa.
disable-model-invocation: true
bundle: _core
triggers:
- research
- nghiên cứu
- tìm hiểu
- ccba-research
---
# Workflow: Nghiên Cứu Chạy Ngầm Đa Luồng (/ccba-research)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `ccba-research` tại [SKILL.md](../skills/ccba-research/SKILL.md) để bắt đầu quy trình spawn subagent chạy ngầm, áp dụng Search Budget Cap (Max 5 tool calls), Cross-Reference Validation và xuất Báo cáo Kỹ thuật 5 phần chuẩn hóa.


---

# Archived Workflow: ccba-resolving-merge-conflicts

---
description: Giải quyết xung đột Git merge/rebase hiện tại một cách an toàn.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-resolving-merge-conflicts
triggers:
- resolving-merge-conflicts
- merge conflicts
- xung đột merge
- rebase
---
# Workflow: Giải Quyết Xung Đột Git (/ccba-resolving-merge-conflicts)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `resolving-merge-conflicts` tại [SKILL.md](../skills/ccba-resolving-merge-conflicts/SKILL.md) để bắt đầu giải quyết xung đột Git cục bộ.


---

# Archived Workflow: ccba-review-proposal

---
description: Thẩm định toàn trình các PR đề xuất từ Spoke lên Hub kèm Adaptive Tiered Review (Fast/Boost), Spoke Leakage Guard, Copilot Guard và Đồng bộ Catalog Hậu Merge (ADR 0045, ADR 0047)
bundle: _core
command: /ccba-review-proposal
triggers:
  - review proposal
  - thẩm định pr
  - duyệt đề xuất
  - review-proposal
  - review proposal boost
  - deep review proposal
applies_to:
- Tác vụ Admin
- Phần mềm
disable-model-invocation: true
---
# Workflow: Review Proposal (Thẩm Định Đề Xuất Spoke Lên Hub — ADR 0045 & ADR 0047)

Quy trình chuẩn hóa toàn trình dành cho Hub Maintainer để thẩm định, làm sạch, tự sửa lỗi có kiểm soát và hợp nhất an toàn các đề xuất (Pull Requests) từ các dự án Spoke vào Hub Monorepo với cơ chế **Phân Cấp Thích Ứng (Adaptive Tiered Review)**.

---

## 📋 Bước 1: Tiếp Nhận, Phân Tuyến & Khởi Tạo (Pre-flight Sync & Tier Selection)

1. **Đồng bộ Base Branch (Pre-flight Sync Gate):**
   - Đảm bảo nhánh `main` local sạch và được đồng bộ với upstream trước khi thẩm định:
     ```bash
     git checkout main && git pull origin main
     ```
2. **Xác định PR mục tiêu & Tùy chọn Chế độ Review:**
   - Cú pháp chuẩn: `/ccba-review-proposal <PR_NUMBER> [--boost | --deep]`
   - Nếu không chỉ định PR: Tự động quét danh sách các PR đang mở:
     ```bash
     gh pr list --state open
     ```
3. **Phân Tuyến Thích Ứng (Adaptive Review Tier):**
   - **Tier 1 — Fast Deterministic Review (Mặc định):** Áp dụng cho PR scoped thông thường ($< 400$ LOC, đóng gói trong 1 package). Chạy bộ 3 Deterministic Workers tự động ($< 15$ giây).
   - **Tier 2 — Boost / Multi-Agent Deep Review:** Tự động kích hoạt khi có cờ `--boost` / `--deep` HOẶC PR thay đổi gói core `_core`, sửa đổi $> 400$ LOC. Ủy quyền cho subagents `DeepInvestigator` và `DeepCoder` thực hiện Double-Pass Adversarial Review và kiểm tra Threat Model.
4. **Khảo sát tệp Proposal:**
   - Kiểm tra tệp ghi nhận tại `.agents/proposals/[YYYY-MM-DD]_[name].md`.
   - Đọc YAML frontmatter (`proposal_id`, `type`, `proposed_by_project`, `priority`).
   - Đọc tóm tắt kiến trúc và mục tiêu nghiệp vụ mà Spoke đã giải quyết.

---

## 🛡️ Bước 2: Kích Hoạt 3 Worker Thẩm Định Song Song (Parallel Review Gate)

Điều phối 3 luồng kiểm tra song song (tự động chạy script hoặc phân bổ Subagents tương ứng theo Tier):

1. **Worker 1 — Spoke Leakage & Privacy Guard (ADR 0045):**
   - Chạy rào chắn rò rỉ và quét Maskara credentials:
     ```bash
     python scripts/governance/check_spoke_leakage.py
     ```
   - *Chốt chặn (Zero Tolerance):* Không chứa `.md/teach/`, `.tmp/`, cache, đường dẫn tuyệt đối Windows `D:\...`. Tệp proposal bắt buộc có đủ 4 trường metadata (`proposal_id`, `type`, `status`, `name`).

2. **Worker 2 — Deep Seams & Scoped Tests Verification:**
   - Kiểm tra ranh giới Module Sâu: Mã nguồn nghiệp vụ nằm gọn trong `packages/[pkg]/src/`, entry points công khai khai báo trong `__all__` tại `__init__.py`.
   - Chạy kiểm thử tự động và linter:
     ```bash
     uv run pytest packages/[package-name]/tests
     uv run ruff check packages/[package-name]
     ```
   - *Tiêu chí:* $100\%$ Passed, 0 errors, 0 warnings.

3. **Worker 3 — Proposal Lifecycle & Catalog Governance (ADR 0047):**
   - Soát chiếu metadata frontmatter của skill/workflow mới đề xuất.
   - Kiểm tra tính tương thích của `catalog.yaml` và Traceability Matrix.

---

## 🤖 Bước 3: Bóc Tách Nhận Xét Copilot & CI Checks Status (Race-Condition Guard)

1. **Kiểm tra trạng thái GitHub Actions CI:**
   ```bash
   gh pr checks <PR_NUMBER>
   ```
2. **Chốt chặn Review Requests của Copilot (Chống Race Condition Merge Sớm):**
   - Đảm bảo Copilot đã hoàn tất nộp bài review trước khi đọc comment:
     ```bash
     gh pr view <PR_NUMBER> --json reviewRequests,reviews --jq '{pending: [.reviewRequests[]?.login], reviewed: [.reviews[]?.user.login]}'
     ```
   - Nếu `pending` còn chứa `copilot-pull-request-reviewer`, Agent tạm dừng chờ Copilot hoàn tất.
3. **Bóc tách nhận xét kỹ thuật từ GitHub Copilot:**
   ```bash
   gh api repos/:owner/:repo/pulls/<PR_NUMBER>/comments --jq ".[] | {path: .path, line: .line, body: .body}"
   ```
4. **Phân loại nhận xét:**
   - *Lỗi kỹ thuật rõ ràng / Đường dẫn vi phạm:* Chuyển sang Bước 4 để tự động khắc phục (Self-Healing).
   - *Góp ý thiết kế / Tài liệu:* Báo cáo Maintainer xem xét.

---

## 🛠️ Bước 4: Tự Sửa Lỗi Có Giám Sát (Supervised Self-Healing) & Hợp Nhất

1. **Khắc phục lỗi tự động trên Branch:**
   - Áp dụng các bản vá sửa regex, docstring conflict, link tuyệt đối hoặc format mã nguồn.
   - Chạy lại `pytest` và `ruff check` để xác minh xanh $100\%$.
   - Push bản vá lên nhánh PR: `git push origin <branch_name>`.
2. **Trình bày Diff cho Maintainer Phê Duyệt:**
   - Tóm tắt các điểm đã sửa và trình bày cho Maintainer bấm xác nhận.
3. **Hợp nhất vào nhánh `main` (Squash Merge):**
   ```bash
   gh pr merge <PR_NUMBER> --squash --delete-branch
   git checkout main && git pull origin main
   ```

---

## 🏛️ Bước 5: Quản Trị Vòng Đời Hậu Merge (Post-Merge Governance)

1. **Cập nhật Proposal Header:**
   - Mở tệp `.agents/proposals/[YYYY-MM-DD]_[name].md`, đổi `status: "open"` $\rightarrow$ `status: "merged"`, ghi nhận `merged_commit` hash và `merged_date`.
2. **Đăng ký Hệ Sinh Thái (ADR 0047):**
   - Tự động tái biên dịch Catalog SSoT:
     ```bash
     python scripts/governance/compile_catalog.py
     ```
3. **Gợi ý Spoke Sync (Closed-Loop Sync):**
   - Thông báo cho Spoke đề xuất kích hoạt **Bước 7 của `/ccba-contribute-to-hub`** (hoặc `/ccba-update-spoke`) để nạp tính năng mới và hoàn tất đóng vòng.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-review-skill

---
description: Đánh giá chất lượng và tối ưu hóa tệp tin SKILL.md theo tiêu chuẩn viết
  skill của CCBA.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-review-skill
triggers:
- review-skill
- audit-skill
- review_skill
- kiểm định skill
---
# Workflow: Đánh giá Chất lượng Skill (/ccba-review-skill)

Khi người dùng kích hoạt lệnh này dưới dạng `/ccba-review-skill <đường-dẫn-file>`, Agent hãy nạp và thực thi kỹ năng `review_skill` tại [SKILL.md](../skills/ccba-review-skill/SKILL.md) để bắt đầu quy trình rà soát, cắt tỉa và tối ưu hóa chất lượng tệp tin kỹ năng.


---

# Archived Workflow: ccba-run-qc-pipeline

---
description: Tự động chạy toàn trình chuỗi kiểm soát chất lượng (QC) đa bộ môn qua
  Deep Seam QCAuditPipeline
applies_to:
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _qc
disable-model-invocation: true
command: /ccba-run-qc-pipeline
triggers:
- qc pipeline
- run QC
- audit tự động
- kiểm tra hồ sơ
---
# Workflow: Run QC Pipeline (/ccba-run-qc-pipeline)

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng tại [SKILL.md](../skills/ccba-ai-qc/SKILL.md) để bắt đầu quy trình chạy toàn trình chuỗi kiểm soát chất lượng bản vẽ thiết kế qua Deep Seam `QCAuditPipeline` (tự động phát hiện bản vẽ Discovery $\rightarrow$ quét đối soát Quad-View đa bộ môn $\rightarrow$ xuất báo cáo kỹ thuật Heat Map).


---

# Archived Workflow: ccba-server-deploy

---
description: Tự động triển khai và cấu hình nền tảng CCBA Agent Platform trên Server
  Spark
applies_to:
- Tác vụ Admin
- Phần mềm
bundle: _core
disable-model-invocation: true
---
# Workflow: Tự Động Triển Khai Nền Tảng Trên Server Spark (/ccba-server-deploy)

Khi người dùng kích hoạt lệnh này, Agent hãy đọc và thực thi chỉ dẫn triển khai tự động theo tài liệu [server_spark_agent_instructions.md](../../docs/playbooks/server_spark_agent_instructions.md).

---

## Các bước thực hiện:
1. **Khảo sát môi trường:** Kiểm tra Python 3.10+, Git, Tailscale VPN và LiteLLM Gateway (`:8090`).
2. **Khởi tạo thư mục:** Clone `ccba-agent-platform` và `ccba-legal-knowledge` nằm ngang hàng tại `~/ccba/`.
3. **Cài đặt packages:** Thiết lập Virtualenv và cài đặt editable packages (`ccba-ai`, `ccba-harness`, `ccba-legal-intel`).
4. **Cấu hình Cron:** Đăng ký lịch chạy `run_nightly_tuner.sh` lúc `0 0 * * *` (nửa đêm hàng ngày).
5. **Kiểm thử khép kín:** Chạy dry-run `nightly_tuner_daemon.py` và báo cáo kết quả cho người dùng.


---

# Archived Workflow: ccba-session-retrospective

---
description: Session Knowledge Retrospective Workflow — Tự động tổng hợp tri thức
  cuối phiên làm việc và dọn dẹp workspace.
applies_to:
- Tác vụ Admin
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-session-retrospective
triggers:
- retrospective
- cuối phiên
- tổng kết
- session learnings
---
# Workflow: Tổng Hợp Tri Thức Cuối Phiên (/ccba-session-retrospective)

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng tại [SKILL.md](../skills/ccba-session-retrospective/SKILL.md) để bắt đầu quy trình tổng hợp tri thức cuối phiên và dọn dẹp tệp tin tạm.


---

# Archived Workflow: ccba-setup-pre-commit

---
description: Thiết lập cấu hình pre-commit cho Python trong repository hiện tại.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-setup-pre-commit
triggers:
- setup-pre-commit
- setup precommit
- hooks python
---
# Workflow: Thiết lập Pre-commit (/ccba-setup-pre-commit)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `setup-pre-commit` tại [SKILL.md](../skills/ccba-setup-pre-commit/SKILL.md) để bắt đầu quy trình thiết lập pre-commit hooks cho Python.


---

# Archived Workflow: ccba-setup-skills

---
description: Thiết lập cấu hình dự án (Spoke/Hub) cho các công cụ phát triển phần
  mềm (cấu hình issue tracker, nhãn triage, domain docs)
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
- BIM
- Tác vụ Admin
- Pháp điển
bundle: _core
disable-model-invocation: true
command: /ccba-setup-skills
triggers:
- setup skills
- thiết lập cấu hình
- cấu hình tracker
- cấu hình nhãn
- setup-skills
- ccba-setup-skills
---
# Workflow: Thiết lập Cấu Hình Phát Triển (/ccba-setup-skills)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `ccba-setup-skills` tại [SKILL.md](../skills/ccba-setup-skills/SKILL.md) để bắt đầu quy trình trinh sát, phỏng vấn và ghi nhận cấu hình phát triển cho dự án.


---

# Archived Workflow: ccba-setup-ts-deep-modules

---
description: Thiết lập cấu hình Deep Modules cho TypeScript bằng dependency-cruiser.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-setup-ts-deep-modules
triggers:
- setup-ts-deep-modules
- setup deep modules
- dependency cruiser ts
---
# Workflow: Thiết lập TS Deep Modules (/ccba-setup-ts-deep-modules)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `setup-ts-deep-modules` tại [SKILL.md](../skills/ccba-setup-ts-deep-modules/SKILL.md) để bắt đầu quy trình cấu hình ranh giới import cho TypeScript.


---

# Archived Workflow: ccba-skills-eval

---
description: Khởi chạy hệ thống kiểm thử tự động (Evaluations) cho các kỹ năng AI
  trong CCBA Platform.
disable-model-invocation: true
bundle: _core
command: /ccba-skills-eval
triggers:
- skills-eval
- eval-skills
- kiểm thử kỹ năng
- chạy evals
---
# Lệnh /ccba-skills-eval

Khi nhận được lệnh này từ người dùng, Agent sẽ tự động nạp và thực thi công cụ kiểm định chất lượng (Evaluations) cho các kỹ năng AI.

---

## 🛠️ Hướng dẫn thực thi các bước

### Bước 1: Xác định phạm vi kiểm thử
Agent phân tích yêu cầu của người dùng để xác định tham số:
- **Kiểm thử một kỹ năng cụ thể:** Nếu người dùng yêu cầu kiểm tra một kỹ năng (ví dụ: `/ccba-skills-eval copywriting`), xác lập tham số `--skill copywriting`.
- **Kiểm thử toàn bộ:** Nếu người dùng chỉ gõ lệnh chung `/ccba-skills-eval`, mặc định chạy cho tất cả kỹ năng bằng cách bỏ trống `--skill` hoặc đặt `--skill all`.
- **Số lần chạy thử:** Mặc định chạy 3 lần thử (`--trials 3`) để đo độ tin cậy. Nếu người dùng cần chạy nhanh để kiểm tra lỗi cú pháp, có thể đặt `--trials 1`.

### Bước 2: Kích hoạt Core Eval Runner & Harness Engine
Chạy lệnh CLI sau tại thư mục gốc của dự án:
```bash
# Kiểm thử một kỹ năng cụ thể qua ccba_harness Multi-Scorer Engine
python .agents/skills/ccba-eval-gate/scripts/eval_runner.py --skill [tên-skill] --trials 3

# Tự động tối ưu hóa SKILL.md (Skill Auto-Tuner via SkillOpt loop)
python .agents/skills/ccba-eval-gate/scripts/eval_runner.py --skill [tên-skill] --auto-tune --max-iterations 3

# Khai phá lỗi từ transcript log thực chiến và tự động sinh test cases
python scripts/eval/log_eval_miner.py --skill [tên-skill] --auto-inject

# Kiểm thử toàn bộ các kỹ năng AI
python .agents/skills/ccba-eval-gate/scripts/eval_runner.py --trials 3
```

### Bước 3: Đánh giá Đa chiều theo Barem Rubrics & Rào chắn Điểm Liệt
- **Bộ Tiêu chí Định lượng & Rubrics:** Đối chiếu kết quả với Quy chuẩn tại [`.md/knowledge/guidelines/domain_success_criteria_rubrics.md`](../../.md/knowledge/guidelines/domain_success_criteria_rubrics.md):
  * **Code-Based Assertions (< 1ms):** ExactMatch, RegexMatch, JsonSchemaMatch, LengthBounds.
  * **Model-Based Rubrics (Likert 1–5):** Anthropic Prompt Structure (`<rubric>`, `<answer>`, `<thinking>`, `<score>`).
  * **Rào chắn Điểm Liệt (Hard Floor):** Nếu vi phạm tiêu chí cốt lõi (False Negative PCCC, sai hiệu lực văn bản luật, bịa trích dẫn), bài thi bị đánh rớt ngay lập tức (Score = 0.0%) bất kể các tiêu chí phụ.
- **Chế độ Auto-Tuner (`--auto-tune`):** 
  Core Eval Runner sẽ tự động điều phối chu trình 4 bước (**Rollout -> Reflect -> Edit -> Validate**). LLM Optimizer sẽ đề xuất chỉnh sửa văn bản `SKILL.md` và kiểm chứng qua Cổng **Validation Gate** để loại bỏ hiện tượng **Prompt Drift** trước khi cập nhật.
- **Nếu tất cả các test cases đạt PASS (exit code = 0):** Báo cáo kết quả thành công cho người dùng.
- **Nếu có test case bị FAILED (exit code = 1):**
  1. Đọc chi tiết lỗi so khớp (Regex mismatch hoặc LLM Judge feedback) được in trong output log.
  2. Xác định xem lỗi do mô hình suy giảm hiệu năng (regression), lỗi placeholders, hay lỗi over-triggering.
  3. Thực hiện sửa đổi và bổ sung chỉ thị trực tiếp vào tệp `SKILL.md` của kỹ năng bị lỗi đó để khắc phục (tương tự như cách sửa lỗi over-triggering bằng When to Use / When NOT to Use).
  4. Chạy lại kiểm thử (tối đa lặp lại 3 lần). Nếu sau 3 lần vẫn lỗi, hãy báo cáo cụ thể cho người dùng để nhận chỉ thị.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-sync-upstream

---
description: Kiểm tra cập nhật và đồng bộ tri thức từ ClaudeKit và MattPocock
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-sync-upstream
triggers:
- sync upstream
- đồng bộ tri thức
- claudekit
- mattpocock
- check update
---
# Workflow: Đồng Bộ Tri Thức Thượng Nguồn (/ccba-sync-upstream)

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng sync-upstream tại [SKILL.md](../skills/ccba-sync-upstream/SKILL.md) để bắt đầu luồng kiểm tra cập nhật và đồng bộ tri thức từ thượng nguồn.


---

# Archived Workflow: ccba-tdd

---
description: Viết code theo quy trình Test-Driven Development (Red-Green-Refactor).
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-tdd
triggers:
- tdd
- test-driven
- red-green-refactor
- unit test
---
# Workflow: Test-Driven Development (/ccba-tdd)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `tdd` tại [SKILL.md](../skills/ccba-tdd/SKILL.md) để bắt đầu chu kỳ Red-Green-Refactor cục bộ.


---

# Archived Workflow: ccba-teach

---
description: Khởi động không gian học tập và giảng dạy tương tác tại thư mục chuyên
  biệt .md/teach/
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-teach
triggers:
- teach
- đào tạo
- học tập
- .md/teach/
---
# Workflow: Giảng Dạy & Không Gian Học Tập Tương Tác (/ccba-teach)

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng tại [SKILL.md](../skills/ccba-teach/SKILL.md) để bắt đầu phiên giảng dạy tương tác (setup mục tiêu hoặc biên soạn bài giảng kế tiếp).


---

# Archived Workflow: ccba-teamwork

---
name: ccba-teamwork
command: /ccba-teamwork
description: Khởi động quy trình điều phối đa tác nhân dài hạn (Teamwork Multi-Agent Framework) theo mô hình 3 vai trò, lập Team Sheet và điều phối các đợt thực thi song song.
disable-model-invocation: true
bundle: _core
triggers:
- teamwork
- ccba-teamwork
- điều phối nhóm
- multi-agent
- team sheet
---
# Workflow: Điều Phối Đa Tác Nhân Dài Hạn (/ccba-teamwork)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `ccba-teamwork` tại [SKILL.md](../skills/ccba-teamwork/SKILL.md) để bắt đầu:

1. **Giai đoạn 1 (Structured Interview):** Phỏng vấn xác định mục tiêu dự án, non-goals, phân rã seams và ánh xạ trách nhiệm giải trình (11 Ghế CCBA Charter 2026).
2. **Giai đoạn 2 (Team Sheet Generation):** Sinh tệp `.agents/teams/[project]_team_sheet.md` theo template chuẩn và thực hiện File-path Pre-Check.
3. **Giai đoạn 3 (Parallel Milestone Execution):** Dispatch Workers (read-only, max 3/batch, timeout 10 phút), tổng hợp kết quả scratch và ghi file chính thức.
4. **Giai đoạn 4 (Success Auditor Gate):** Kiểm định scoped test suite, quét Maskara, kiểm toán Post-Merge Diff Audit và biên dịch Catalog SSOT.


---

# Archived Workflow: ccba-to-questionnaire

---
description: Hệ thống Khảo sát & Thu thập Quyết định Đa kênh Tương tác (Dual-Track Questionnaire Engine v2.0)
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
- Tác vụ Admin
bundle: _core
disable-model-invocation: true
command: /ccba-to-questionnaire
triggers:
- to-questionnaire
- questionnaire
- bảng hỏi
- async questionnaire
- dual-track questionnaire
- phiếu lấy ý kiến
---
# Workflow: Hệ Thống Bảng Hỏi Đa Kênh Tương Tác (/ccba-to-questionnaire)

Quy trình tự động hóa khảo sát và thu thập quyết định kỹ thuật bất đồng bộ từ các bên liên quan (Chủ đầu tư, Tư vấn thiết kế, Ban QLDA, Kỹ sư MEP/PCCC) hoặc soạn thảo đề xuất nền tảng Hub (Platform Track) thông qua **Dual-Track Questionnaire Engine v2.0**.

---

## 📋 Các Chế Độ & Cú Pháp Sử Dụng

### 1. Khởi tạo Bảng hỏi Mới (Mặc định)
```bash
/ccba-to-questionnaire
```
Agent nạp kỹ năng `to-questionnaire` tại [SKILL.md](../skills/ccba-to-questionnaire/SKILL.md), tiến hành:
1. Xác định phân luồng: **Platform Track** (Spoke ➔ Hub RFC) hay **Delivery Track** (Dự án ➔ Đối tác).
2. Phỏng vấn ngắn gọn làm rõ đối tượng gửi và thông tin cần thu về.
3. Soạn thảo file Markdown chuẩn v2.0 tại `.md/knowledge/questionnaires/to-questionnaire-<slug>.md` với khung trắc nghiệm 3 tầng giả định A/B/C/D kèm trade-off tóm tắt.

### 2. Phân Luồng Chuyên Biệt
- **Platform Track (Đề xuất nền tảng Hub):**
  ```bash
  /ccba-to-questionnaire --track platform
  ```
  Tự động đóng gói nội dung thành RFC Proposal và chuyển tiếp sang workflow [`/ccba-issue-to-hub`](ccba-issue-to-hub.md) để mở GitHub Issue.
- **Delivery Track (Bài toán dự án công trường):**
  ```bash
  /ccba-to-questionnaire --track delivery
  ```
  Tập trung vào thông số thiết kế, quy chuẩn QCVN và tự động kích hoạt bộ xuất bản đa kênh.

### 3. Xuất Bản Đa Kênh (Omni-Format Export)
```bash
python scripts/questionnaire_engine.py <file.md> --format all
# Hoặc xuất riêng lẻ: --format docx / --format html / --format chat / --format email
```
- **Word `.docx`**: Biểu mẫu Phiếu lấy ý kiến CCBA có format trang trọng, bảng chọn checkbox Unicode và khung phê duyệt 3 bên.
- **Web Landing Page**: Form HTML độc lập 100% offline, lưu LocalStorage, thanh phản hồi nhanh và mã QR.
- **Micro Chat**: Đoạn tóm tắt <15 dòng cho Zalo/Teams.
- **Email Table**: Bảng so sánh HTML chuẩn inline styling.

### 4. Chu Trình Nạp Hai Chiều & Bàn Giao (`--reply`)
Khi nhận được phản hồi từ đối tác, nạp kết quả để cập nhật Markdown AST và chuyển sang trạng thái `RESOLVED`:
```bash
python scripts/questionnaire_engine.py <file.md> --reply "1A, 2B, 3C" --resolved-by "Đại diện Chủ đầu tư"
```
Sau khi nạp thành công:
- Tự động kích hoạt [`/ccba-to-spec`](../skills/ccba-to-spec/SKILL.md) để chuyển hóa quyết định thành PRD / Đặc tả kỹ thuật.
- Hoặc kích hoạt [`/ccba-to-tickets`](../skills/ccba-to-tickets/SKILL.md) để phân rã nhiệm vụ phát triển.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-to-spec

---
description: Soạn thảo tài liệu Spec từ ngữ cảnh hiện tại.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-to-spec
triggers:
- spec
- to-spec
- soạn spec
- tạo spec
---
# Workflow: Soạn thảo Spec (/ccba-to-spec)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `to-spec` tại [SKILL.md](../skills/ccba-to-spec/SKILL.md) để bắt đầu quy trình soạn thảo tài liệu Đặc tả Kỹ thuật (Spec) dựa trên ngữ cảnh hội thoại hiện tại.


---

# Archived Workflow: ccba-to-tickets

---
description: Phân rã kế hoạch hoặc spec (Đặc tả) hiện tại thành các ticket phát triển
  độc lập dạng lát cắt dọc (vertical slices)
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
disable-model-invocation: true
command: /ccba-to-tickets
triggers:
- to-tickets
- tickets
- bẻ ticket
- tạo ticket
---
# Workflow: Phân rã công việc thành Tickets (/ccba-to-tickets)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `to-tickets` tại [SKILL.md](../skills/ccba-to-tickets/SKILL.md) để phân rã yêu cầu thành các ticket phát triển độc lập và liên kết chặn.


---

# Archived Workflow: ccba-triage

---
description: Điều phối và sàng lọc Issues/PRs qua các trạng thái và viết brief.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-triage
triggers:
- triage
- sàng lọc
- phân loại
- incident
- bug triage
---
# Workflow: Điều phối và Sàng lọc Sự cố (/ccba-triage)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `triage` tại [SKILL.md](../skills/ccba-triage/SKILL.md) để bắt đầu quy trình điều phối trạng thái, xác thực lỗi, rà soát trùng lặp và soạn thảo Agent Brief.


---

# Archived Workflow: ccba-tvpl-vip-crawler

---
description: Quy trình thực thi cào dữ liệu văn bản pháp luật VIP từ Thư viện Pháp
  luật (TVPL) qua Deep Seam TVPLCrawler
disable-model-invocation: true
bundle: _consulting
command: /ccba-tvpl-vip-crawler
triggers:
- tvpl-vip-crawler
- tvpl vip crawler
- cào thư viện pháp luật
- tvpl vip
- vip crawler
---
# Quy trình thực thi Slash Command `/ccba-tvpl-vip-crawler`

Khi người dùng kích hoạt lệnh Slash Command này dưới dạng:
`/ccba-tvpl-vip-crawler <đường-dẫn-url-hoặc-tên-văn-bản-tvpl>`

Agent tiếp nhận lệnh bắt buộc phải thực thi theo các bước sau:

1. **Kiểm tra Cấu hình & Nạp Kỹ năng**:
   - Đọc hướng dẫn tại [SKILL.md](../skills/ccba-tvpl-vip-crawler/SKILL.md).
   - Xác nhận tài khoản VIP `TVPL_USERNAME` và `TVPL_PASSWORD` sẵn sàng tại `.env`.

2. **Kích hoạt Deep Seam TVPLCrawler Trực tiếp (Giao thức Một Cửa `tab=7`)**:
   - Thực thi lệnh cào và nạp văn bản tự động qua CLI:
     ```bash
     python -m ccba_legal ingest "<đường-dẫn-url-hoặc-tên-văn-bản-tvpl>" --category <01_vbpl|02_qcvn|03_tcvn> --upload-drive
     ```

3. **Cấu trúc hóa OKF Bundle & Kiểm tra Kết quả**:
   - Kiểm tra kết quả đóng gói tại `legal_docs/<category>/<slug>/`.
   - Báo cáo kết quả đóng gói thành công bao gồm các tệp `metadata.yaml`, `index.md`, `clauses.json`, `qa_benchmark.json`, và 4 ngăn kéo chuyên biệt.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Archived Workflow: ccba-update-legal-registry

---
name: ccba-update-legal-registry
description: Tự động đồng bộ các thay đổi pháp lý từ legal_registry.yaml lên Google
  NotebookLM (hỗ trợ lưu trữ qua Google Drive chung).
disable-model-invocation: true
keywords:
- legal
- sync
- update
- notebooklm
- drive
bundle: _consulting
command: /ccba-update-legal-registry
triggers:
- legal
- sync
- update
- notebooklm
- drive
- cập nhật VBPL
- legal update
- update registry
- văn bản mới
---
# Lệnh Slash Command `/ccba-update-legal-registry`

Đồng bộ hóa tự động tri thức pháp luật xây dựng (VBPL) từ máy cục bộ lên Google NotebookLM Cloud RAG.

## Các Bước thực thi của Agent

Khi lệnh này được kích hoạt, Agent thực hiện theo quy trình sau:

### Bước 1: Tra cứu Notebook ID (Context Lookup)
1. Đọc tệp cấu hình cục bộ tại `.md/workspace_context.yaml` để tìm giá trị `notebook_id`.
2. Nếu không tìm thấy hoặc tệp không tồn tại, kiểm tra biến môi trường hệ thống `NOTEBOOKLM_ID`. Chỉ hỏi người dùng làm phương án dự phòng cuối cùng nếu cả hai nguồn đều trống.

### Bước 2: Kiểm tra môi trường & Cấp quyền
1. Xác nhận sự tồn tại của biến cookie `NOTEBOOKLM_SESSION_COOKIE` hoặc tệp cấu hình `NOTEBOOKLM_COOKIES_JSON` trong môi trường hệ thống.
2. Nếu người dùng chỉ định đồng bộ qua Google Drive (`--use-drive`), kiểm tra xác thực Google Drive qua Application Default Credentials (ADC):
   ```bash
   gcloud auth application-default login --scopes="https://www.googleapis.com/auth/drive"
   ```

### Bước 3: Chạy Script Đồng bộ
Thực thi lệnh Python đồng bộ với Notebook ID đã xác định:
```bash
python scripts/sync_notebooklm_knowledge.py --notebook-id <notebook_id> [--upload-drive]
```

## Tiêu chí Hoàn thành (Completion Criteria)
- **Kiểm chứng thành công**: Script chạy trả về mã thoát `Exit Code 0` (hoặc thông báo `Sync completed successfully` trên console output).
- **Attribution & Disclaimer**: Kết quả đầu ra hiển thị bảng thống kê số lượng nguồn được nạp mới/xóa bỏ, đồng thời bắt buộc đính kèm dòng bản quyền CCBA và Disclaimer pháp lý ở cuối tệp/tin nhắn phản hồi.
- **Xử lý lỗi**: Nếu gặp lỗi xác thực cookie (401/403) hoặc lỗi kết nối, in rõ thông báo lỗi chi tiết và hướng dẫn người dùng cập nhật lại Token môi trường thay vì im lặng kết thúc.


---

# Archived Workflow: ccba-update-spoke

---
description: Đồng bộ hóa các kỹ năng, quy trình và cập nhật phiên bản giữa Hub và các Spoke (đơn lẻ hoặc hàng loạt)
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
- BIM
- Tác vụ Admin
- Pháp điển
bundle: _core
disable-model-invocation: true
command: /ccba-update-spoke
triggers:
- update spoke
- đồng bộ hub
- lấy lệnh mới
- cập nhật dự án
- sync all
- sync all spokes
- đồng bộ toàn bộ spoke
- spoke status
- kiểm tra spoke
---
# Cập Nhật & Đồng Bộ Hóa CCBA Spoke Workspace (/ccba-update-spoke)

Workflow này đồng bộ hóa các bản cập nhật mới nhất (kịch bản lệnh, kỹ năng, hiến pháp `AGENTS.md`, rào chắn test) từ **CCBA Agent Platform (Hub)** sang các dự án **Spoke**, hỗ trợ đồng bộ đơn lẻ, tải On-Demand và đồng bộ hàng loạt.
Quy trình áp dụng cơ chế **Safe-by-Default** 2 pha (Two-Phase Execution), bảo vệ Git working tree và tự động tạo snapshot sao lưu để có thể hoàn tác tức thì.

---

## 🛡️ Nguyên Tắc Safe-by-Default (Mặc định An toàn):
1. **Pha 1 (Xem trước Preview):** Lệnh mặc định luôn chạy mô phỏng trước, phân loại và in bảng kiểm tra 4 trạng thái tệp:
   - `🟢 NEW`: Kỹ năng/quy trình mới từ Hub chưa có tại Spoke.
   - `🔄 UPDATED`: Kỹ năng/quy trình đã có sự thay đổi từ Hub.
   - `⚪ UNCHANGED`: Tệp hoàn toàn trùng khớp, không cần cập nhật.
   - `🛡️ PRESERVED`: Kỹ năng/quy trình tùy biến nội bộ của Spoke, được bảo toàn 100%.
2. **Pha 2 (Xác nhận Thực thi):** Người dùng xác nhận `[y/N]` để áp dụng, hoặc truyền cờ `--apply` / `-y`.
3. **Git Working Tree Guard:** Tự động kiểm tra `git status`. Nếu thư mục `.agents/` có uncommitted changes, hệ thống cảnh báo và yêu cầu commit/stash trước khi sync (hoặc dùng `--force`).
4. **Snapshot Backup & Rollback:** Tự động sao lưu thư mục `.agents/` vào `.md/backups/agents_backup_<timestamp>/` trước khi sửa đổi, cho phép hoàn tác qua cờ `--rollback`.

---

## 🎯 Khi Nào Dùng:
1. **Tại Hub:** Kiểm tra độ trễ phiên bản hoặc đồng bộ 1 chạm cho tất cả các Spoke kết nối (`--all`).
2. **Tại Spoke:** Cập nhật toàn bộ Skills/Workflows của dự án hiện tại theo đúng nghiệp vụ (`project_type`).
3. **Tại Spoke (On-Demand):** Tải nhanh kỹ năng còn thiếu trên Hub (Lazy Loading).
4. **Khi Cần Hoàn Tác:** Khôi phục trạng thái `.agents/` trước lần đồng bộ gần nhất (`--rollback`).
5. **Đóng Vòng Hậu Hợp Nhất:** Khi PR đóng góp từ Spoke vừa được merge vào Hub (Bước 7 của `/ccba-contribute-to-hub`).

---

## 🛠️ Các Chế Độ Thực Hiện:

### 📊 Chế độ 1: Kiểm Tra Trạng Thái Sức Khỏe & Độ Lệch Phiên Bản (Tại Hub)
```powershell
python scripts\ccba_platform_cli.py spoke-status
```

### 🌐 Chế độ 2: Đồng Bộ Hàng Loạt Toàn Bộ Spoke Đang Đăng Ký (Từ Hub)
```powershell
# 1. Xem trước mô phỏng (Pha 1) | 2. Đồng bộ chính thức (Pha 2, bỏ qua sandbox):
python scripts\sync_spoke.py --all --dry-run
python scripts\sync_spoke.py --all --apply
# 3. Đồng bộ bao gồm cả Spoke Cá Nhân (ADR 0046):
python scripts\sync_spoke.py --all --apply --include-sandboxes
```

### 📁 Chế độ 3: Đồng Bộ Toàn Bộ Cho Spoke Hiện Tại (Tại Spoke)
```powershell
# Safe-by-Default (Hiện Preview -> Hỏi xác nhận [y/N]):
python [hub_path]\scripts\sync_spoke.py --spoke .
# Áp dụng ngay (Non-interactive / CI) hoặc Bỏ qua cảnh báo uncommitted:
python [hub_path]\scripts\sync_spoke.py --spoke . --apply
python [hub_path]\scripts\sync_spoke.py --spoke . --apply --force
```

### ⚡ Chế độ 4: Tải Bổ Sung Kỹ Năng / Workflow Cụ Thể (On-Demand)
```powershell
python [hub_path]\scripts\sync_spoke.py --spoke . --sync-item [tên-kỹ-năng] --apply
```

### ⏪ Chế độ 5: Hoàn Tác & Quản Lý Snapshot Sao Lưu (Rollback & Undo)
```powershell
python [hub_path]\scripts\sync_spoke.py --spoke . --list-backups
python [hub_path]\scripts\sync_spoke.py --spoke . --rollback
```

### ⚖️ Chế độ 6: Đồng Bộ Tri Thức Pháp Lý Chuẩn OKF v2.4 (Two-Tier Legal Sync — ADR 0050)
1. **🟢 Tự động đồng bộ cho Spoke liên quan (Pháp điển, Thẩm tra, Kiểm định, PCCC):** Quét và sao chép gói OKF v2.4 từ Tier 1 (Offline) hoặc Tier 2 (Cloud Drive Vault), thực hiện Non-Destructive Additive Registry Merge. Lệnh độc lập: `python -m ccba_legal sync --pull-latest`.
2. **💡 Zero-Bloat cho Spoke còn lại (Phần mềm, BIM, Admin):** Mặc định bỏ qua để giữ repo tinh gọn. Khi cần tra cứu tải lẻ: `python -m ccba_legal sync --doc <doc_id>` hoặc truy vấn RAG qua `ccba-ai` trên LiteLLM Spark.

---

## 📋 Báo Cáo Kết Quả & Dọn Dẹp:
1. **Báo cáo đồng bộ:** Báo cáo chi tiết: `🟢 NEW`, `🔄 UPDATED`, `⚪ UNCHANGED`, `🛡️ PRESERVED`.
2. **Tổng kết tri thức pháp lý (ADR 0050):** Hiển thị số lượng gói OKF v2.4 đã đồng bộ.
3. **Đồng bộ Pre-commit Hooks & Cleanliness Gate (ADR 0044 §7):**
   ```powershell
   Copy-Item "$hub\scripts\spoke\check_hub_import_depth.py" -Destination ".\scripts\check_hub_import_depth.py" -Force
   Copy-Item "$hub\scripts\spoke\check_spoke_cleanliness.py" -Destination ".\scripts\check_spoke_cleanliness.py" -Force
   ```
4. **Kiểm tra Script Budget & Cleanliness:** Chạy `python .\scripts\check_spoke_cleanliness.py`.
5. **Kiểm định Hồi quy & Packages (Hậu Đóng Góp):** Chạy `pip install -e "[hub_path]\packages\[pkg]"` và chạy test cục bộ (`python scripts\validate_legal_spoke.py`).
6. **Kiểm tra sức khỏe tổng thể:** Chạy `python scripts\ccba_platform_cli.py spoke-status` xác nhận trạng thái xanh.


---

# Archived Workflow: ccba-viet-chuyen-nghiep

---
description: Viết tiếng Việt chuyên nghiệp — nhà xuất bản AI
applies_to:
- Phần mềm
bundle: _software
disable-model-invocation: true
command: /ccba-viet-chuyen-nghiep
triggers:
- viet-chuyen-nghiep
- viết tiếng việt
- chuyên nghiệp
- nhà xuất bản
---
# Workflow: Viết tiếng Việt chuyên nghiệp (/ccba-viet-chuyen-nghiep)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `viet-chuyen-nghiep` tại [SKILL.md](../skills/ccba-viet-chuyen-nghiep/SKILL.md) để bắt đầu quy trình biên soạn và tối ưu văn bản tiếng Việt chuyên nghiệp.


---

# Archived Workflow: ccba-wait-what

---
description: Dừng lại và giải thích lại tin nhắn trước bằng ngôn ngữ tiếng Việt đơn
  giản.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-wait-what
triggers:
- wait-what
- wait what
- giải thích lại
- chưa hiểu
---
# Workflow: Giải Thích Lại Bằng Ngôn Ngữ Đơn Giản (/ccba-wait-what)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `wait-what` tại [SKILL.md](../skills/ccba-wait-what/SKILL.md) để dừng lại và diễn đạt lại nội dung vừa rồi bằng ngôn ngữ đơn giản, bổ sung ngữ cảnh cần thiết.


---

# Archived Workflow: ccba-wayfinder

---
description: Vạch bản đồ giải quyết các bài toán mù mờ (foggy problems).
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-wayfinder
triggers:
- wayfinder
- bài toán mơ hồ
- foggy
---
# Workflow: Wayfinder Vạch Đường (/ccba-wayfinder)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `wayfinder` tại [SKILL.md](../skills/ccba-wayfinder/SKILL.md) để bắt đầu phân tích vấn đề và thiết lập bản đồ.


---

# Archived Workflow: ccba-wizard

---
description: Tạo bash script wizard hướng dẫn quy trình cài đặt/thiết lập thủ công.
applies_to:
- Phần mềm
bundle: _core
disable-model-invocation: true
command: /ccba-wizard
triggers:
- wizard
- setup wizard
- tạo script
---
# Workflow: Tạo Script Setup Wizard (/ccba-wizard)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `wizard` tại [SKILL.md](../skills/ccba-wizard/SKILL.md) để bắt đầu scope và sinh script setup wizard.


---

# Archived Workflow: ccba-xia

---
description: Trích xuất, so sánh, port hoặc thích ứng một tính năng từ một repository
  GitHub hoặc đường dẫn thư mục cục bộ vào dự án hiện tại
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
disable-model-invocation: true
command: /ccba-xia
triggers:
- xia
- port from
- copy from repo
- clone feature
- adapt from
---
# Workflow: Port tính năng (xỉa code) từ repository ngoài (/ccba-xia)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `ccba-xia` tại [SKILL.md](../skills/ccba-xia/SKILL.md) để bắt đầu quy trình trích xuất và chuyển dịch mã nguồn.


---

# Archived Workflow: ccba-xu-ly-van-phong

---
description: Tạo, sửa, chuyển đổi file văn phòng (Word, Excel, PowerPoint, PDF)
applies_to:
- Phần mềm
bundle: _software
disable-model-invocation: true
command: /ccba-xu-ly-van-phong
triggers:
- xu-ly-van-phong
- xử lý văn phòng
- word
- excel
- powerpoint
- pdf
---
# Workflow: Xử lý Văn phòng (/ccba-xu-ly-van-phong)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `xu-ly-van-phong` tại [SKILL.md](../skills/ccba-xu-ly-van-phong/SKILL.md) để bắt đầu quy trình tạo, sửa, chuyển đổi định dạng và format văn bản văn phòng chuyên nghiệp.


---

# Archived Workflow: ccba-youtube-learn

---
description: Khảo cổ học Niềm tin (Belief Archaeology) từ video YouTube/bài giảng
  học thuật.
disable-model-invocation: true
bundle: _core
command: /ccba-youtube-learn
triggers:
- youtube-learn
- youtube
- bóc tách
- belief archaeology
---
# Lệnh /ccba-youtube-learn

Khi nhận được lệnh này, hãy nạp trực tiếp kỹ năng [SKILL.md](../skills/ccba-youtube-learn/SKILL.md) và làm theo hướng dẫn thực thi trong đó để thực hiện bóc tách phụ đề, hình ảnh slide học thuật và khảo cổ thế giới quan diễn giả.


---

# Archived Workflow: workflow_pccc_cdt_tuthamdinh

---
name: workflow_pccc_cdt_tuthamdinh
description: Quy trình Hỗ trợ Chủ đầu tư Tự thẩm định toàn bộ thiết kế PCCC (theo
  Luật 55/2024 & NĐ 105/2025)
applies_to:
- Thẩm tra thiết kế
- Thiết kế
bundle: _qc
disable-model-invocation: true
command: /workflow_pccc_cdt_tuthamdinh
triggers:
- tự thẩm định
- cdt tự thẩm định
- luật 55/2024
- NĐ 105/2025
---
# Quy trình Tư vấn Hỗ trợ Chủ đầu tư Tự thẩm định toàn bộ thiết kế PCCC

Căn cứ điểm đ khoản 1 Điều 17 Luật PCCC số 55/2024/QH15 và khoản 1 Điều 8 Nghị định số 105/2025/NĐ-CP, đối với các công trình không thuộc thẩm quyền thẩm định của Cơ quan chuyên môn về xây dựng và Cơ quan Công an, **Chủ đầu tư / Chủ sở hữu công trình có trách nhiệm tự tổ chức thẩm định thiết kế về PCCC**.

Quy trình này hướng dẫn cách sử dụng CCBA AI Agent để hỗ trợ Chủ đầu tư thực hiện nhiệm vụ rà soát toàn diện và xuất Mẫu PC13 theo đúng quy định pháp luật.

## 1. Nội dung Tự thẩm định (Full Audit)

Chủ đầu tư phải tự chịu trách nhiệm trước pháp luật về việc thẩm định đầy đủ 07 nội dung (từ điểm a đến điểm g khoản 1 Điều 16 Luật 55/2024/QH15):
*   **Phần Kiến trúc & Thụ động:**
    *   [a] Khoảng cách phỏng cháy, chữa cháy.
    *   [b] Đường bộ, bãi đỗ xe, khoảng trống phục vụ PCCC.
    *   [c] Giải pháp thoát nạn.
    *   [d] Bậc chịu lửa, giải pháp ngăn cháy, chống cháy lan.
    *   [đ] Giải pháp chống khói.
*   **Phần Chủ động & Hệ thống điện:**
    *   [e] Hệ thống điện phục vụ phòng cháy và chữa cháy.
    *   [g] Phương tiện, hệ thống phòng cháy và chữa cháy.

## 2. Trình tự thực hiện bằng CCBA Semantic Audit Engine

Thay vì phải rà soát thủ công một lượng lớn bản vẽ Kiến trúc, Điện, Nước và Thuyết minh, Chủ đầu tư/Tư vấn QLDA áp dụng phương pháp Map-Reduce của CCBA:

**Bước 1: Chuẩn bị Hồ sơ (Data Ingestion)**
Tập hợp toàn bộ Thuyết minh tính toán, Bản vẽ Kiến trúc PCCC và Bản vẽ MEP PCCC vào một thư mục chung.

**Bước 2: Phân tách Gói Dữ Liệu (Map)**
*   Gói 1 (Legal & Specs): Thuyết minh tổng hợp + Quy chuẩn áp dụng.
*   Gói 2 (MEP Water): Mặt bằng bơm, bể nước, vách tường, Sprinkler + Thuyết minh.
*   Gói 3 (MEP Alarm vs Arch): Mặt bằng Kiến trúc + Báo cháy + Điện PCCC.

**Bước 3: Chạy Engine Đánh Giá (Reduce)**
*   Sử dụng Local LLM (qwen-local-primary) chạy tuần tự qua các Gói dữ liệu để so sánh chéo, phát hiện xung đột và lỗi sai thông số.
*   Cross-check tự động với cơ sở dữ liệu TCVN 3890:2023, TCVN 5738:2021, TCVN 7336:2021 và QCVN 06:2022/BXD.

**Bước 4: Trích xuất Báo cáo Thẩm định (PC13)**
*   Hệ thống tổng hợp các Findings (Lỗi) và xuất ra Báo cáo Đánh giá Chất lượng Hồ sơ.
*   Sử dụng kết quả này làm cơ sở để phát hành **Văn bản kết quả thẩm định thiết kế về phòng cháy, chữa cháy** (Mẫu số PC13 ban hành kèm theo Nghị định số 105/2025/NĐ-CP). Chủ đầu tư ký và lưu hồ sơ theo quy định.


---

# Archived Workflow: workflow_pccc_thamdinh_congan

---
name: workflow_pccc_thamdinh_congan
description: Quy trình Thẩm định thiết kế PCCC phần Hệ thống Cơ điện (MEP) nộp Cơ
  quan Công an (PC07)
applies_to:
- Thẩm tra thiết kế
- Thiết kế
bundle: _qc
disable-model-invocation: true
command: /workflow_pccc_thamdinh_congan
triggers:
- thẩm định công an
- mep pccc
- pc07
---
# Quy trình Thẩm định thiết kế PCCC phần Hệ thống MEP (Cơ quan Công an)

Căn cứ theo điểm c khoản 1 Điều 17 Luật PCCC số 55/2024/QH15 và Nghị định số 105/2025/NĐ-CP, Cơ quan Công an (Cục/Phòng Cảnh sát PCCC - PC07) thực hiện thẩm định chuyên biệt đối với phần Hệ thống chủ động và Hệ thống điện PCCC.

## 1. Thẩm quyền và Nội dung thẩm định (Phần Cơ điện - Chủ động)

Nội dung do Cơ quan Công an thẩm định tập trung vào điểm e, g khoản 1 Điều 16 Luật 55/2024/QH15:
*   **[e] Hệ thống điện PCCC:** Hệ thống cáp cấp nguồn cho bơm chữa cháy, quạt hút khói/tăng áp, thang máy chữa cháy, chiếu sáng sự cố, tiếp địa.
*   **[g] Phương tiện & Hệ thống báo/chữa cháy:**
    *   Hệ thống báo cháy tự động (khói, nhiệt, chuông, còi, tủ trung tâm).
    *   Hệ thống chữa cháy (vách tường, Sprinkler tự động, màng ngăn Drencher, khí/bọt).
    *   Phương tiện chữa cháy xách tay (bình chữa cháy).

## 2. Danh mục Hồ sơ trình Thẩm định

Để nộp Cơ quan Công an thẩm định (Mẫu PC11 theo NĐ 105/2025), hồ sơ thiết kế MEP cần bao gồm:
1.  **Hệ thống Báo cháy:**
    *   Sơ đồ nguyên lý toàn hệ thống.
    *   Mặt bằng bố trí đầu báo, nút nhấn, còi đèn, dây cáp từng tầng.
    *   Chi tiết lắp đặt thiết bị.
2.  **Hệ thống Chữa cháy:**
    *   Sơ đồ không gian (Isometric) / Sơ đồ nguyên lý cấp nước chữa cháy.
    *   Mặt bằng bố trí đầu phun Sprinkler, họng nước vách tường, bình chữa cháy.
    *   Chi tiết trạm bơm chữa cháy (bố trí bơm, tủ điện, ống hút/đẩy, dung tích bể ngầm).
3.  **Hệ thống Điện PCCC:**
    *   Sơ đồ nguyên lý cấp nguồn riêng biệt cho tải PCCC.
    *   Chi tiết cáp chống cháy (FR), tuyến cáp đi an toàn.
4.  **Thuyết minh tính toán:**
    *   Thuyết minh tính toán thủy lực mạng lưới cấp nước PCCC.
    *   Tính toán dung lượng ắc quy dự phòng cho tủ trung tâm báo cháy.

## 3. Trình tự thực hiện (Dành cho Agent/Kỹ sư)

Sử dụng CCBA Agent Platform để audit lỗi thiết kế MEP trước khi nộp PC07:

1.  **Thu thập dữ liệu MEP:** Chuyển đổi Thuyết minh MEP PCCC và Bản vẽ MEP PCCC sang Markdown/Vector.
2.  **Kích hoạt AI Audit:** Gọi module Semantic Map-Reduce Audit cho:
    *   "Package 2: MEP Water vs Specs" (Đồng bộ số liệu bơm, bể nước).
    *   "Package 3: MEP Alarm vs Arch" (Đồng bộ vị trí báo cháy, vùng phủ, trần giả).
3.  **Kiểm soát rủi ro điển hình (Common Pitfalls):**
    *   Kiểm tra sự lệch pha giữa Thuyết minh (vd: tính toán 45m3) và Bản vẽ (vd: bể 54m3).
    *   Đảm bảo việc trích dẫn đúng quy chuẩn cấp điện (QCVN 12:2014/BXD).
4.  **Hoàn thiện:** Sửa lỗi thiết kế và in Hồ sơ xin Thẩm duyệt thiết kế PCCC nộp Cơ quan Công an.


---

# Archived Workflow: workflow_pccc_thamdinh_cqxd

---
name: workflow_pccc_thamdinh_cqxd
description: Quy trình Thẩm định/Thẩm tra PCCC phần Kiến trúc & Kiểm soát khói nộp
  Cơ quan chuyên môn về xây dựng (theo Luật 55/2024 & NĐ 105/2025)
applies_to:
- Thẩm tra thiết kế
- Thiết kế
bundle: _qc
disable-model-invocation: true
command: /workflow_pccc_thamdinh_cqxd
triggers:
- thẩm định cơ quan xây dựng
- kiến trúc pccc
- kiểm soát khói
---
# Quy trình Thẩm định/Thẩm tra PCCC phần Kiến trúc & Kiểm soát khói (CQCMVXD)

Quy trình này áp dụng cơ chế lồng ghép thẩm định thiết kế xây dựng và thẩm định thiết kế PCCC theo quy định tại Điều 16, Điều 17 Luật PCCC số 55/2024/QH15 và Nghị định số 105/2025/NĐ-CP. Việc thẩm định do Cơ quan chuyên môn về xây dựng (CQCMVXD) chủ trì, có thể có sự tham gia của Tổ chức Tư vấn Thẩm tra độc lập (như CCBA).

## 1. Thẩm quyền và Nội dung thẩm định (Phần Kiến trúc - Thụ động)

Căn cứ vào điểm a, b, c, d, đ khoản 1 Điều 16 Luật 55/2024/QH15, nội dung thẩm định bao gồm:
*   **[a] Khoảng cách an toàn PCCC:** Khoảng cách giữa các công trình, hạng mục công trình, đường ranh giới khu đất.
*   **[b] Giao thông & Bãi đỗ xe:** Đường bộ, bãi đỗ xe cứu hỏa, vị trí và lối tiếp cận phục vụ chữa cháy.
*   **[c] Lối thoát nạn:** Hành lang, đường thoát nạn, thang bộ, thang máy chữa cháy, lối ra khẩn cấp, gian lánh nạn.
*   **[d] Bậc chịu lửa & Ngăn cháy lan:** Giới hạn chịu lửa cấu kiện, giải pháp phân chia khoang cháy, bố trí mặt bằng công năng, chèn bịt chống cháy (Firestopping).
*   **[đ] Kiểm soát khói:** Phương án thoát khói (tự nhiên/cơ học), cấp khí bảo vệ (tăng áp) buồng thang bộ, giếng thang máy.

## 2. Danh mục Hồ sơ trình Thẩm định

Để đáp ứng quy định kiểm tra, Hồ sơ Thiết kế cần chuẩn bị:
1.  **Tổng mặt bằng công trình:** Thể hiện rõ khoảng cách, đường giao thông, bãi đỗ xe PCCC.
2.  **Mặt bằng Kiến trúc PCCC các tầng:** Thể hiện lối thoát nạn, phân chia khoang cháy, cửa chống cháy.
3.  **Chi tiết cấu tạo:** Thang thoát nạn, thang máy PCCC, vách/trần chịu lửa, chèn bịt kỹ thuật.
4.  **Bản vẽ Hệ thống thông gió:** Mặt bằng/sơ đồ nguyên lý tăng áp buồng thang, hút khói hành lang/tầng hầm.
5.  **Thuyết minh tính toán:**
    *   Bảng thống kê giới hạn chịu lửa cấu kiện (REI/EI).
    *   Bảng tính toán thoát nạn (chiều rộng cửa, chiều dài quãng đường).
    *   Thuyết minh tính toán hệ thống kiểm soát khói.

## 3. Trình tự thực hiện (Dành cho Agent/Kỹ sư)

Sử dụng CCBA Agent Platform để chạy kiểm tra (Audit) trước khi nộp hồ sơ:

1.  **Thu thập dữ liệu:** Trích xuất toàn bộ Thuyết minh PCCC và Bản vẽ Kiến trúc/Thông gió HVAC sang định dạng Markdown.
2.  **Kích hoạt AI Audit:** Gọi lệnh chạy module Semantic Map-Reduce Audit cho "Package 1: Legal & Architecture".
3.  **Cross-check Pháp lý:**
    *   Đối chiếu số liệu với QCVN 06:2022/BXD.
    *   Kiểm tra tính nhất quán giữa Bản vẽ mặt bằng và Thuyết minh.
4.  **Xuất báo cáo:** Chuyển kết quả Audit thành Phụ lục Báo cáo Thẩm tra Thiết kế, đóng dấu tư vấn và đệ trình lên Cơ quan chuyên môn về xây dựng cùng hồ sơ TKXD triển khai sau TKCS.


---
