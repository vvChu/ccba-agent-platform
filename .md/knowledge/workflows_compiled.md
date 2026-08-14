# Workflow: ccba-academic-writing

---
name: ccba-academic-writing
description: Hướng dẫn lập đề cương, viết bản thảo và tự động kiểm định văn phong bài báo khoa học theo cấu trúc IMRAD.
user-invocable: true
workflow_trigger_level: 1
---

Hãy nạp và thực thi kỹ năng viết bài báo khoa học tại [SKILL.md](../skills/academic_writing/SKILL.md) và chạy kiểm duyệt vi mô thông qua script [microstructure_audit.py](../skills/academic_writing/scripts/microstructure_audit.py) khi có bản thảo hoặc dữ liệu thực tế.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*


---

# Workflow: ccba-ai-qc-pccc-audit

---
description: Hệ thống Thẩm tra lỗi thiết kế đa bộ môn (PCCC, MEP, Kiến trúc) thông qua cơ chế Semantic Map-Reduce.
applies_to:
  - "Quản lý chất lượng"
  - "Thẩm tra thiết kế"
bundle: "_qc"
---

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng tại [SKILL.md](../skills/ccba-ai-qc-pccc-audit/SKILL.md) để bắt đầu quy trình rà soát và kiểm soát chất lượng thiết kế PCCC (Map-Reduce).


---

# Workflow: ccba-ask

---
description: Hướng dẫn định tuyến/tư vấn chọn kỹ năng hoặc workflow phù hợp.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Hướng dẫn Định hướng Kỹ năng (/ccba-ask)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `ask` tại [SKILL.md](../skills/ask/SKILL.md) để bắt đầu tư vấn, định hướng và dẫn đường cho luồng công việc tiếp theo trên Platform.


---

# Workflow: ccba-brainstorm

---
description: Khởi động phiên thảo luận ý tưởng và chuẩn bị tài liệu đầu vào tại input_documents/
command: /ccba-brainstorm [-- <topic_id>]
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
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
1. **Chuyển đổi tài liệu:** Chuyển đổi theo quy trình `/ccba-convert-markdown` — tham khảo skill [markdown-document-processing](../skills/markdown-processing/SKILL.md) cho quy tắc routing theo `project.mode`.
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

# Workflow: ccba-build-skill

---
name: ccba-build-skill
description: Nghiên cứu tài liệu từ nhiều nguồn qua NotebookLM và tự động đóng gói sinh Skill mới đạt chuẩn CCBA.
user-invocable: true
keywords: [build-skill, create-skill, research, notebooklm]
---

# Quy trình thực thi Slash Command `/ccba-build-skill`

Khi người dùng kích hoạt lệnh này dưới dạng:
`/ccba-build-skill <danh-sách-nguồn-hoặc-thư-mục> [--name <tên-skill>]`

Agent tiếp nhận lệnh bắt buộc phải tự động thực thi chuỗi tác vụ sau:

1.  **Quét bảo mật & Nạp nguồn**:
    *   Đọc danh sách nguồn tài liệu được cung cấp (tệp tin cục bộ, URL hoặc video).
    *   Chạy quét bảo mật qua `scripts/maskara.py` đối với các tệp tin cục bộ.
    *   Nạp nguồn vào Google NotebookLM thông qua CLI helper.
2.  **Chưng cất tri thức**:
    *   Chạy lệnh sinh `study-guide` hoặc `report` của CLI helper để kết xuất cẩm nang tri thức tổng hợp Markdown sạch vào `.md/knowledge/`.
    *   Đọc tệp tin cẩm nang này để nắm rõ toàn bộ logic, patterns và API của công cụ cần tạo skill.
3.  **Khởi tạo cấu trúc Skill đạt chuẩn**:
    *   Tạo thư mục skill tại `.agents/skills/<tên_skill_dạng_snake_case>/`.
    *   Tạo file `SKILL.md` chứa YAML Frontmatter chuẩn chỉnh và hướng dẫn chi tiết.
    *   Tạo các tệp tin script hỗ trợ (nếu có) vào thư mục `scripts/` tương ứng.
4.  **Đăng ký Slash Command**:
    *   Tạo một tệp tin workflow mỏng bắt đầu bằng `ccba-` tại `.agents/workflows/` (ví dụ: `ccba-<tên-lệnh>.md`) để đăng ký lệnh Slash Command chính thức của Skill.
5.  **Kiểm định chất lượng (QC Gate)**:
    *   Chạy công cụ `validate_docs.py` để kiểm định chất lượng tài liệu Markdown của Skill vừa tạo trước khi hoàn tất.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*


---

# Workflow: ccba-convert-markdown

---
description: Chuyển đổi tài liệu sang Markdown bằng mdconverter và tự động hậu xử lý (bảng biểu, biểu mẫu, liên kết)
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Workflow: Convert to Markdown (/ccba-convert-markdown)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `markdown-document-processing` tại [SKILL.md](../skills/markdown-processing/SKILL.md) để bắt đầu quy trình chuyển đổi tài liệu Word/PDF sang Markdown và tự động khắc phục các lỗi định dạng (bảng biểu, biểu mẫu, liên kết tương đối).


---

# Workflow: ccba-copywriting

---
description: Soạn thảo văn bản hành chính/thương mại theo mẫu chuẩn đã thống nhất, kế thừa trực tiếp nguồn dữ liệu biểu mẫu (templates) được chuẩn hóa.
applies_to:
  - "Phần mềm"
  - "Tác vụ Admin"
bundle: "_core"
---

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng copywriting tại [SKILL.md](../skills/copywriting/SKILL.md) để bắt đầu luồng soạn thảo văn bản theo mẫu chuẩn.


---

# Workflow: ccba-create-pr

---
description: Push code hiện tại và tạo Pull Request tự động
applies_to:
  - "Phần mềm"
bundle: "_software"
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
   ```bash
   .venv\Scripts\python scripts/run_harness_evals.py
   ```
2. **Quy tắc chặn lỗi tại nguồn:**
   - Nếu `run_harness_evals.py` trả về `PASS 100%`: Mã nguồn đạt chuẩn, tiếp tục Bước 2.
   - Nếu có Gate bị `FAIL` hoặc phát hiện Architecture Drift: Tạm dừng workflow, yêu cầu Agent/người dùng sửa lỗi tại local (hoặc chạy `python scripts/update_arch_stats.py`) và commit lại trước khi đẩy mã nguồn.

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

1. Trình bày đường dẫn PR và trạng thái kiểm thử CI cho người dùng.
2. Nhắc nhở người dùng: "Hãy gọi `/ccba-release-feature` khi CI đã xanh để merge và dọn dẹp."


---

# Workflow: ccba-discard-feature

---
description: Hủy bỏ branch hiện tại, xóa cả local và remote
applies_to:
  - "Phần mềm"
bundle: "_software"
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

# Workflow: ccba-docs

---
description: Khởi động quy trình tự động cập nhật và kiểm định tài liệu kỹ thuật của dự án.
triggers: [/ccba-docs, cập nhật tài liệu, update docs]
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: ccba-docs

Khi người dùng kích hoạt Slash Command này, Agent **bắt buộc** phải nạp và thực thi kỹ năng `docs_manager` tại [SKILL.md](../skills/docs_manager/SKILL.md) để bắt đầu quy trình quản lý tài liệu.


---

# Workflow: ccba-eval-gate

---
description: Chạy kiểm định tự động qua CI Gates và kích hoạt vòng lặp tự sửa lỗi (Self-Healing).
---

# Lệnh /ccba-eval-gate

Khi nhận được lệnh này, hãy nạp trực tiếp kỹ năng [SKILL.md](../skills/eval-gate/SKILL.md) và làm theo hướng dẫn thực thi trong đó để tự động kiểm chứng và sửa lỗi mã nguồn.


---

# Workflow: ccba-extract-style

---
description: Trích xuất và phân tích đặc trưng văn phong thầu/hành chính từ tài liệu mẫu của CCBA, tự động dựng biểu mẫu (Template) có placeholders.
applies_to:
  - "Phần mềm"
  - "Tác vụ Admin"
bundle: "_core"
---

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng copywriting tại [SKILL.md](../skills/copywriting/SKILL.md) và chạy phần trích xuất/nghiên cứu văn phong thô để chuẩn hóa thành tệp template.


---

# Workflow: ccba-git-guardrails

---
description: Thiết lập và kích hoạt rào chắn lệnh Git nguy hiểm của Agent.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Rào Chắn An Toàn Git (/ccba-git-guardrails)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `git-guardrails` tại [SKILL.md](../skills/git-guardrails/SKILL.md) để bắt đầu kích hoạt chế độ chặn và xin quyền cho các lệnh Git nguy hiểm.


---

# Workflow: ccba-grill-with-docs

---
description: Phiên phỏng vấn Socrates dồn dập giúp làm sắc nét kế hoạch thiết kế và tự động ghi nhận tệp thuật ngữ (CONTEXT.md) cùng quyết định kiến trúc (ADRs).
applies_to:
  - "Phần mềm"
bundle: "_core"
---

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng tại [SKILL.md](../skills/grilling/SKILL.md) và kết hợp kỹ năng [domain-modeling](../skills/domain-modeling/SKILL.md) để ghi nhận lại các thuật ngữ mới vào tệp `CONTEXT.md` và các quyết định khó đảo ngược thành hồ sơ thiết kế ADR tại `docs/adr/`.


---

# Workflow: ccba-grilling

---
description: Phỏng vấn dồn dập người dùng từng câu một để stress-test kế hoạch hoặc thiết kế.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Phỏng Vấn Dồn Dập (/ccba-grilling)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `grilling` tại [SKILL.md](../skills/grilling/SKILL.md) để bắt đầu grilling loop.


---

# Workflow: ccba-handoff

---
description: Đóng gói phiên làm việc thành tài liệu handoff nhỏ gọn cho Agent tiếp theo.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Handoff Phiên Làm Việc (/ccba-handoff)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `handoff` tại [SKILL.md](../skills/handoff/SKILL.md) để tổng hợp ngữ cảnh phiên làm việc hiện tại.


---

# Workflow: ccba-implement

---
description: Triển khai lập trình khép kín (TDD -> Eval Gate -> Code Review -> Commit -> Walkthrough)
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Triển khai lập trình (/ccba-implement)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `implement` tại [SKILL.md](../skills/implement/SKILL.md) để bắt đầu quy trình lập trình khép kín dựa trên đặc tả kỹ thuật (Spec) hoặc các tickets công việc đã chia nhỏ.


---

# Workflow: ccba-improve-codebase-architecture

---
description: Cải tiến kiến trúc codebase bằng cách quét phát hiện module nông và đề xuất deepening.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Cải Tiến Kiến Trúc Codebase (/ccba-improve-codebase-architecture)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `improve-codebase-architecture` tại [SKILL.md](../skills/improve-codebase-architecture/SKILL.md) để bắt đầu phân tích cấu trúc module.


---

# Workflow: ccba-init-spoke

---
description: Khởi tạo một dự án (Spoke) tuân thủ kiến trúc CCBA Agent Platform
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
  - "Tác vụ Admin"
bundle: "_core"
---

# Khởi tạo CCBA Spoke Workspace

Workflow này tự động hóa việc thiết lập một không gian làm việc (workspace) dự án mới để tuân thủ kiến trúc **CCBA Hub-and-Spoke** và **Global Rules**. Bạn nên chạy command `/ccba-init-spoke` ngay khi mở một thư mục dự án trên IDE.

## Các bước thực hiện:

### 1. Khởi tạo cấu trúc Knowledge Base (Global Rule 1)
Tạo kiến trúc thư mục `.md` chứa dữ liệu tri thức bằng PowerShell tùy theo Mode được chọn (`software`, `delivery`, hoặc `hybrid`):
```powershell
$mode = "[mode tương ứng]" # (Phần mềm -> software, Xây dựng/Tư vấn -> delivery, Platform/R&D -> hybrid)
if ($mode -eq "software") {
    $kbDirs = @(".md\scratch")
} else {
    $kbDirs = @(
        ".md\seminars", 
        ".md\legal_docs", 
        ".md\extracted_docs", 
        ".md\scratch", 
        ".md\data", 
        ".md\knowledge\configs", 
        ".md\knowledge\guidelines", 
        ".md\knowledge\related_papers", 
        ".md\knowledge\reports", 
        ".md\knowledge\specs_and_roadmaps"
    )
}
foreach ($dir in $kbDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
```


### 2. Ghi nhận tên dự án
Lấy tên thư mục Root hiện hành để cấu hình:
```powershell
(Get-Item .).Name
```

### 3. Tạo file Workspace Context
Tạo file `.md\workspace_context.yaml` và ghi nội dung cấu hình. Đề nghị người dùng chọn 1 trong các loại dự án sau để điền vào trường `type`:
- Dự án phần mềm/build tools (type: `Phần mềm`)
- Thẩm tra thiết kế/ Third-party Review (type: `Thẩm tra thiết kế`)
- Thiết kế/ Design (type: `Thiết kế`)
- Kiểm định/Assessment (type: `Kiểm định`)
- Tác vụ Admin/ Hành chính & Quản trị (type: `Tác vụ Admin`)

Dựa vào `type` được chọn, xác định `mode` mặc định (`software` cho Phần mềm, `delivery` cho các loại còn lại. Nếu là Hub hoặc Spoke hỗn hợp thì chọn `hybrid`).
Xác định `qc_mode` tự động:
- Thiết kế $\rightarrow$ `internal`
- Thẩm tra thiết kế $\rightarrow$ `third-party`
- Kiểm định $\rightarrow$ `assessment`
- Phần mềm hoặc Tác vụ Admin $\rightarrow$ `null`

```yaml
# =============================================================================
# WORKSPACE CONTEXT — [Tên thư mục dự án]
# Machine-readable onboarding file for AI Agents.
# =============================================================================

project:
  name: "[Tên thư mục dự án]"
  type: "[Loại dự án được chọn]"
  mode: "[mode tương ứng: software | delivery | hybrid]"
  qc_mode: "[qc_mode tương ứng]"
  description: >
    [Mô tả ngắn gọn mục tiêu và phạm vi dự án]

# =============================================================================
# MUST-READ FILES
# =============================================================================
must_read:
  always:
    - path: .md/GLOSSARY.md
      why: "Ubiquitous Language — thuật ngữ chuẩn"

# =============================================================================
# DO NOT TOUCH
# =============================================================================
do_not_touch:
  - .env

# =============================================================================
# AGENT ACKNOWLEDGMENT PROTOCOL (Global Rule 4 — Override)
# =============================================================================
acknowledgment_required: true
acknowledgment_format: >
  "Tôi đã đọc workspace_context.yaml. Dự án [tên] là [type] (mode: [mode]). Tác vụ hiện tại liên quan đến [lĩnh vực]."
```

### 4. Quét tìm tài liệu chưa xử lý
Kiểm tra xem dự án có file tài liệu thô (Word/PDF) nào chưa được xử lý hay không:
```powershell
Get-ChildItem -Path . -Recurse -Depth 3 | Where-Object { $_.Extension -match "\.(pdf|docx)$" } | Select-Object Name
```

### 5. Đồng bộ hóa Giao diện Lệnh (Copy theo Bundle)
Xác định đường dẫn Hub (`hub_path`) của Platform (mặc định lấy từ biến môi trường `CCBA_HUB_PATH` hoặc repository chung). Tiến hành sao chép các kỹ năng/workflows tương ứng về Spoke:
```powershell
$bundles = @{
    "Phần mềm"          = @("_core", "_software")
    "Thẩm tra thiết kế" = @("_core", "_qc", "_consulting")
    "Thiết kế"          = @("_core", "_qc", "_consulting")
    "Kiểm định"         = @("_core", "_qc", "_consulting")
    "Tác vụ Admin"      = @("_core", "_consulting")
}
$type = "[type vừa được chọn]"
$hub  = "[hub_path]"
New-Item -ItemType Directory -Force -Path ".agents\skills", ".agents\workflows" | Out-Null
foreach ($bundle in $bundles[$type]) {
    if (Test-Path "$hub\skills\$bundle") {
        Copy-Item -Path "$hub\skills\$bundle\*" -Destination ".agents\skills\" -Recurse -Force
    }
    if (Test-Path "$hub\workflows\$bundle") {
        Copy-Item -Path "$hub\workflows\$bundle\*" -Destination ".agents\workflows\" -Recurse -Force
    }
}
```

### 6. Khởi tạo cấu trúc .gitignore và Mã nguồn Chuẩn
*Lưu ý:* Bước này và bước 6.1 chỉ áp dụng nếu dự án được khởi tạo dưới dạng Spoke Chức năng (Functional/R&D Spoke) có sẵn Git cục bộ. Đối với các Spoke Dự án/Triển khai (Delivery Spoke) đồng bộ thuần túy qua OneDrive/SharePoint và không có repo GitHub riêng, hãy bỏ qua các bước cấu hình Git này.

Tạo tệp `.gitignore` mẫu **bảo mật 2 lớp** cho dự án (loại bỏ whitelist cho `skills` để Kỹ năng không bị commit vào Spoke, đồng thời loại trừ đệ quy các tệp nhị phân lớn để đồng bộ SharePoint):
```text
# System / IDE
.env
.vscode/
.idea/
*.log

# Python / Node.js build
__pycache__/
*.pyc
node_modules/
.venv/
build/
dist/
*.egg-info/

# CCBA Agent Platform - Whitelist selected configs (skills is local only and git-ignored)
.agents/*
!.agents/workflows/
!.agents/proposals/
!.agents/AGENTS.md
.agents/**/*.log
.agents/**/*.json
.agents/**/*.env
.agents/**/__pycache__/
.agents/**/*.pyc

# Processing Workspace (.md/)
# Temp files during processing are ignored, but structure is tracked
.md/**/*.pdf
.md/**/*.docx
.md/**/*.xlsx
.md/**/*.pptx
.md/**/*.txt
# Except keep markdown and raw transcripts in general folders
!.md/**/raw_transcript.txt
.md/extracted_docs/*
!.md/extracted_docs/.gitkeep
# Ignore images of youtube-learn
.md/**/images/*.webp
.md/**/images/*.jpg
.md/**/images/*.png

# Ignore all specific project outputs (OneDrive/SharePoint synced)
.md/projects/*
!.md/projects/.gitkeep
```

### 6.1. Thiết lập Git Pre-commit Hook Bảo mật (Maskara)
Tự động cấu hình pre-commit hook cục bộ tại Spoke để gọi Maskara bảo vệ khóa API và thông tin nhạy cảm:
```powershell
if (Test-Path ".git") {
    $hookDir = ".git\hooks"
    if (-not (Test-Path $hookDir)) {
        New-Item -ItemType Directory -Path $hookDir -Force | Out-Null
    }
    $hookPath = Join-Path $hookDir "pre-commit"
    $hookContent = @"
#!/bin/sh
# CCBA Maskara Pre-commit Security Hook
echo 'Running Maskara staged files scan...'

# Get list of staged files (excluding deleted ones)
staged_files=`$(git diff --cached --name-only --diff-filter=d)

if [ -z "`$staged_files" ]; then
    echo "No files staged for commit. Skipping scan."
    exit 0
fi

has_leak=0
for file in `$staged_files; do
    # Skip binary and static asset files
    if echo "`$file" | grep -qE '\.(png|jpg|jpeg|gif|ico|pdf|zip|tar|gz|exe|dll|so|dylib|woff|woff2|eot|ttf|mp3|mp4|wav|avi)$'; then
        continue
    fi
    
    # Skip ignored dirs
    if echo "`$file" | grep -qE '^(\.md/scratch/|\.venv/|node_modules/)'; then
        continue
    fi
    
    if [ -f "`$file" ]; then
        python "$hub/scripts/maskara.py" scan --root "`$file" > /dev/null 2>&1
        status_code=`$?
        if [ `$status_code -ne 0 ]; then
            echo "❌ Leak detected in staged file: `$file"
            python "$hub/scripts/maskara.py" scan --root "`$file"
            has_leak=1
        fi
    fi
done

if [ `$has_leak -ne 0 ]; then
    echo 'Error: Raw API keys or credentials detected. Commit blocked!'
    exit 1
fi

echo "✅ Security check passed."
exit 0
"@
    [System.IO.File]::WriteAllText($hookPath, $hookContent)
}
```

Nếu `mode` là **"software"** hoặc **"hybrid"**, đề xuất người dùng chọn ngôn ngữ lập trình mục tiêu (Python/Node.js) và dựng cấu trúc thư mục chuẩn:
- Tạo các thư mục `src`, `tests`, `scripts`, `docs`, `docs/references`, `docs/adr`
- Khởi tạo `pyproject.toml` (cho Python) hoặc `package.json` (cho Node.js)
- Với dự án Python: Đồng bộ bộ rào chắn test `conftest.py` và wrapper script `scripts/safe_pytest.py` từ Hub:
  ```powershell
  if (Test-Path "$hub\conftest.py") {
      Copy-Item -Path "$hub\conftest.py" -Destination ".\conftest.py" -Force
  }
  if (Test-Path "$hub\scripts\safe_pytest.py") {
      New-Item -ItemType Directory -Path ".\scripts" -Force | Out-Null
      Copy-Item -Path "$hub\scripts\safe_pytest.py" -Destination ".\scripts\safe_pytest.py" -Force
  }
  ```

### 7. Khởi tạo cấu trúc Tri thức Mẫu (Dành cho các dự án nghiệp vụ)
Nếu `mode` là **"delivery"** hoặc **"hybrid"**, sao chép các tệp tin templates từ Hub về Spoke để kỹ sư bắt đầu ghi nhận tri thức:
```powershell
$hubTemplates = "[hub_path]\.agents\workflows\resources\templates"
if (Test-Path $hubTemplates) {
    Copy-Item -Path "$hubTemplates\ccba_rd_seminar_template.md" -Destination ".md\seminars\CCBA_RD_SEMINAR_001_Rev00-Template.md" -Force
    Copy-Item -Path "$hubTemplates\contract_template.md" -Destination ".md\data\contracts\contract_template.md" -Force
    Copy-Item -Path "$hubTemplates\weekly_report_template.md" -Destination ".md\knowledge\reports\weekly_report_template.md" -Force
}
```

### 8. Báo cáo hoàn tất
- In thông báo thiết lập Spoke Workspace thành công.
- Hướng dẫn người dùng các bước kế tiếp:
  - Chạy `/ccba-setup-skills` để thiết lập cấu hình công cụ phát triển (Issue Tracker, Domain Docs).
  - Sử dụng `/ccba-update-spoke` để nâng cấp các skills/workflows mới từ Hub.
  - Sử dụng `/ccba-convert-markdown` nếu cần chuyển đổi tài liệu Word/PDF sang Markdown.


---

# Workflow: ccba-knowledge-loop

---
name: ccba-knowledge-loop
description: Quy trình Vòng lặp Tri thức & Định hướng toàn trình (Recon → Brainstorm → Wayfinder → Exec)
---

# Quy trình Vòng lặp Tri thức & Định hướng (/ccba-knowledge-loop)

Quy trình này hướng dẫn Agent cách kết hợp đồng bộ 4 kỹ năng cốt lõi của CCBA Agent Services Platform: [YouTube-Learn](../skills/youtube-learn/SKILL.md) (Trinh sát tri thức video), [Research](../skills/ccba-research/SKILL.md) (Nghiên cứu ngầm), [Brainstorm](ccba-brainstorm.md) (Hội chẩn giải pháp) và [Wayfinder](../skills/wayfinder/SKILL.md) (Lập lộ trình) để giải quyết một bài toán kỹ thuật/nghiệp vụ lớn và mơ hồ (Foggy Problem) mà không gây block phiên làm việc hoặc làm tràn ngữ cảnh (token bloating).

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
1. **Bóc tách video/bài giảng:** Agent chạy [/ccba-youtube-learn](../skills/youtube-learn/SKILL.md) trên các video hướng dẫn của chuyên gia, webinar công nghệ hoặc seminar tập huấn liên quan để thu thập tri thức thực hành và các slide tĩnh.
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
1. **Thiết lập bản đồ:** Kích hoạt [/ccba-wayfinder](../skills/wayfinder/SKILL.md) để khởi tạo bản đồ định hướng tại `.md/knowledge/issues/<feature>/map.md`.
2. **Cấu trúc bản đồ:**
   * **Điểm đích (Destination):** Xác định rõ tiêu chí nghiệm thu hoàn thành của bài toán.
   * **Frontier Tickets:** Các ticket mở, sẵn sàng thực thi ngay và độc lập với các ticket khác. Phân loại rõ: *Research [AFK]*, *Prototype [HITL]*, *Grilling [HITL]*, *Task [HITL/AFK]*.
   * **Sương mù chiến trận / Chưa xác định rõ (Not yet specified):** Chỉ ghi nhận các vùng thông tin và quyết định đã rõ ràng; các phần chưa thể nhìn thấy sẽ được giữ lại trong mục này dưới dạng ghi chú phác thảo cho đến khi đủ thông tin unblock.
3. **Tham chiếu theo tên:** Mọi ticket đều phải có tên gọi và link Markdown cụ thể (Ví dụ: `[Đóng gói Mutex Lock](../skills/wayfinder/SKILL.md)`).

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

# Workflow: ccba-legal-intel

---
description: Workflow tư vấn và rà soát pháp luật xây dựng Việt Nam với RAG và Grounding Gate
---

# Workflow: Tư Vấn & Rà Soát Pháp Luật Xây Dựng (/ccba-legal-intel)

> **Mô tả:** Workflow tự động cào, tra cứu RAG, đối chiếu và tư vấn giải đáp thắc mắc pháp lý xây dựng Việt Nam với cơ chế kiểm định trích dẫn nguồn bắt buộc (Grounding Gate).

## Các bước thực hiện của Agent

### 1. Tiếp nhận Câu hỏi & Nạp Sổ bộ (`legal_registry.yaml`)
- Nạp module `scripts/legal_rag_indexer.py` và đọc cơ sở dữ liệu pháp lý tại `.agents/skills/legal-document-tracker/resources/legal_registry.yaml`.
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

# Workflow: ccba-loop-me

---
description: Thiết kế chu trình lặp (Loops) trong công việc và biên soạn thành đặc tả workflow mới.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Thiết kế chu trình công việc (/ccba-loop-me)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `loop-me` tại [SKILL.md](../skills/loop-me/SKILL.md) để bắt đầu chuỗi phỏng vấn Socrates làm rõ và sinh workflow mới.


---

# Workflow: ccba-new-feature

---
description: Tạo feature branch mới với quy trình lập kế hoạch và phân tách session sạch (Factory Model)
applies_to:
  - "Phần mềm"
bundle: "_software"
---

# Workflow: Tạo Feature Branch Mới & Phân Tách Session (Factory Model)

Quy trình tự động hóa dọn dẹp các branch cũ, khởi tạo branch tính năng mới và cưỡng chế áp dụng mô hình Nhà máy (**The Factory Model**) tách biệt giữa **Planning** và **Coding** để tối ưu hóa chi phí Token (OpEx) và ngăn ngừa lỗi mã nguồn.

## Các bước thực hiện:

### Bước 1: Chuẩn bị môi trường
Quay về branch `main` và kéo code mới nhất từ remote:
```bash
git checkout main && git pull origin main
```

### Bước 2: Dọn dẹp các branch cũ đã merge
Dọn dẹp các branch cục bộ đã được tích hợp vào `main` để giải phóng bộ nhớ. Lệnh này tương thích đa nền tảng (bao gồm Windows PowerShell và Linux):
```powershell
git fetch -p
git branch --merged main | Where-Object { $_ -notmatch 'main' } | ForEach-Object { git branch -d $_.Trim() }
```

### Bước 3: Thu thập thông tin tính năng mới
Hỏi người dùng lần lượt các thông tin:
1. Loại công việc cần thực hiện: `feature` (tính năng mới), `fix` (sửa lỗi), `docs` (tài liệu), `refactor` (cải tiến cấu trúc), hoặc `experiment` (thử nghiệm).
2. Mô tả ngắn gọn tính năng (3-5 từ).

### Bước 4: Đề xuất tên branch
Dựa trên câu trả lời, đề xuất tên branch theo định dạng chuẩn CCBA:
- `feature/ten-tinh-nang`
- `fix/ten-loi`
- `docs/ten-tai-lieu`
- `refactor/ten-module`
- `experiment/ten-thu-nghiem`

*Quy tắc đặt tên branch:* Viết thường hoàn toàn (lowercase), sử dụng dấu gạch ngang `-` thay cho khoảng trắng, ngắn gọn và tường minh.
Yêu cầu người dùng xác nhận tên branch đề xuất (`yes/no`).

### Bước 5: Khởi tạo branch mới
Sau khi người dùng đồng ý, tạo và chuyển sang branch mới:
```bash
git checkout -b [ten_branch_da_chot]
```

### Bước 6: Lập kế hoạch thiết kế (Planning Phase - Socrates Grill)
Agent **bắt buộc** phải chuyển sang **Planning Mode**, tuyệt đối không được viết code ở bước này:
1. Kích hoạt kỹ năng `/ccba-grilling` để phỏng vấn người dùng, stress-test các giả định kiến trúc và xác định seam (khớp nối) tích hợp.
2. Tạo tệp `implementation_plan.md` đạt chuẩn (phải có mục `## Đánh giá khả năng tái sử dụng (Reuse Assessment)`).
3. Đợi người dùng nhấn **Proceed** phê duyệt bản kế hoạch.

### Bước 7: Bàn giao cô lập ngữ cảnh (Factory Model Hand-off)
Sau khi bản kế hoạch được duyệt, để ngăn ngừa phình to ngữ cảnh hội thoại (Context Rot) và giảm OpEx:
*   **Phương án 1 (Khuyên dùng - Tiết kiệm Token tối đa):** Agent hướng dẫn người dùng tạo một session chat mới hoàn toàn sạch sẽ. Người dùng dán nội dung file `implementation_plan.md` vào lượt chat đầu tiên và ra lệnh cho Coding Agent thực thi.
*   **Phương án 2 (Tự động hóa ngầm):** Agent chính khởi chạy một **Coding Subagent** ngầm thông qua công cụ `invoke_subagent` trên workspace nhánh để thực thi kế hoạch mà không làm ảnh hưởng đến chat log chính.

### Bước 8: Lập trình, Kiểm chứng & Tự sửa lỗi (Coding & Verification Phase)
Coding Agent thực hiện nhiệm vụ:
1. Khởi tạo danh mục theo dõi `task.md`.
2. Viết mã nguồn tương thích, áp dụng type hints và docstring theo chuẩn CCBA.
3. Chạy `/ccba-eval-gate` (hoặc `python scripts/run_harness_evals.py`) để xác thực.
4. Nếu phát hiện linter hoặc type check báo lỗi, tự động kích hoạt **Self-Healing Loop** tối đa 3 lần.
5. Khi tất cả các Gates đều `PASS`, bàn giao kết quả qua tệp `walkthrough.md` cho người dùng nghiệm thu trước khi merge PR.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Workflow: ccba-notebooklm

---
description: Kết nối tự động với NotebookLM để import YouTube/tài liệu, trích xuất tóm tắt, RAG query hoặc tạo Audio Overview.
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Workflow: NotebookLM Connector (/ccba-notebooklm)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `notebooklm-connector` tại [SKILL.md](../skills/notebooklm-connector/SKILL.md) để bắt đầu chu trình kết nối, xác thực và xử lý tri thức với Google NotebookLM Cloud.


---

# Workflow: ccba-prepare-seminar

---
description: Chuẩn bị nội dung cho buổi seminar/thảo luận nội bộ CCBA
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_consulting"
---

# Workflow: Prepare Seminar (/ccba-prepare-seminar)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `seminar-builder` tại [SKILL.md](../skills/seminar-builder/SKILL.md) để bắt đầu quy trình chuẩn bị nội dung, chương trình nghị sự và recap cho buổi seminar.


---

# Workflow: ccba-propose-to-hub

---
description: Đề xuất tích hợp skill/workflow/tool hoặc rules/directory mới từ Spoke lên Hub
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
---

# Workflow: Propose to Hub (Đóng Góp Ngược Lên Hub)

Quy trình chuẩn hóa đề xuất đóng góp ngược các cải tiến từ dự án Spoke lên Platform Hub chung.

## Bước 1: Thu thập thông tin đề xuất
Hỏi người dùng tuần tự từng câu hỏi sau để ghi nhận đề xuất:
1. **Loại đề xuất:** `skill` / `workflow` / `tool` / `rules`.
2. **Tên đề xuất:** Dạng kebab-case (ví dụ: `auto-pdf-namer`).
3. **Mô tả:** Giải thích ngắn gọn mục đích (1-2 câu).
4. **Vấn đề giải quyết:** Chi tiết khó khăn thực tế cần giải quyết.
5. **Dự án áp dụng:** Các bộ môn áp dụng cụ thể.
6. **Mức độ ưu tiên:** "Cao" / "Trung bình" / "Thấp".

## Bước 2: Kiểm tra trùng lặp (Duplicate Detection)
Trước khi tạo mới, Agent bắt buộc phải kiểm tra hệ thống để tránh trùng lặp:
1. Đọc tệp cấu hình `.md/workspace_context.yaml` để lấy đường dẫn Hub (`hub_path`).
2. Đọc tệp catalog của Hub tại `<hub_path>/.agents/skills/platform-loader/catalog.yaml` để tìm kiếm tên hoặc mô tả tương tự.
3. Đọc tệp hiến pháp `<hub_path>/.agents/AGENTS.md`.
*Nếu phát hiện đã tồn tại thành phần tương tự:* Báo cáo cho người dùng và đề xuất cập nhật/nâng cấp thành phần cũ thay vì tạo mới.

## Bước 3: Tạo và Commit Đề xuất trên Branch mới
Thực thi các lệnh Git tại thư mục Hub (`hub_path`):
1. **Kiểm tra trạng thái workspace:**
   Chạy `git status`. Nếu có thay đổi chưa commit, yêu cầu người dùng commit hoặc stash các thay đổi đó trước khi tiếp tục.
2. **Đồng bộ main:**
   ```bash
   git checkout main && git pull origin main
   ```
3. **Tạo branch và ghi nhận proposal:**
   - Tạo branch mới: `git checkout -b proposal/[tên-đề-xuất]`
   - Tạo tệp proposal tại: `<hub_path>/.agents/proposals/[YYYY-MM-DD]_[tên-đề-xuất].md`
   
   *Cấu trúc tệp proposal:*
   ```markdown
   ---
   proposal_id: "[YYYY-MM-DD]_[tên-đề-xuất]"
   type: "[loại-đề-xuất]"
   name: "[tên-đề-xuất]"
   status: "open"
   priority: "[mức-độ-ưu-tiên]"
   proposed_by_project: "[tên-dự-án-spoke]"
   proposed_date: "[YYYY-MM-DD]"
   applies_to:
     - "[bộ-môn-áp-dụng]"
   ---
   
   ## Mô tả
   ...
   ## Vấn đề giải quyết
   ...
   ## Giải pháp / Cấu trúc đề xuất
   ...
   ```
4. **Commit & Push:**
   Thực hiện commit và push lên remote branch (do thư mục `.agents/proposals/` đã được whitelist trong `.gitignore`, bạn có thể dùng lệnh add thông thường):
   ```bash
   git add .agents/proposals/ && git commit -m "docs(proposal): add proposal for [tên-đề-xuất]" && git push origin proposal/[tên-đề-xuất]
   ```

## Bước 4: Tạo Pull Request (PR Flow)
Kiểm tra quyền qua GitHub CLI bằng cách chạy `gh auth status` hoặc kiểm tra biến môi trường:
- **Nếu có quyền:** Chạy lệnh tạo PR:
  ```bash
  gh pr create --title "docs(proposal): add proposal for [tên-đề-xuất]" --body "Automated proposal submission." --base main --head proposal/[tên-đề-xuất]
  ```
- **Nếu không có quyền:** Cung cấp link tạo PR thủ công dựa trên remote URL lấy được từ `git remote get-url origin`:
  👉 `[PR-creation-URL]/pull/new/proposal/[tên-đề-xuất]`

## Bước 5: Báo cáo hoàn tất
Báo cáo ngắn gọn cho người dùng bao gồm: đường dẫn tệp đề xuất, tên branch, URL của Pull Request (hoặc link tạo thủ công) và bước tiếp theo.


---

# Workflow: ccba-prototype

---
name: ccba-prototype
command: /ccba-prototype
description: Khởi động quy trình xây dựng mẫu thử code thô (Logic hoặc UI) để giải quyết vấn đề thiết kế mờ mịt.
---

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `ccba-prototype` tại [SKILL.md](../skills/ccba-prototype/SKILL.md) để bắt đầu quy trình dựng mẫu thử nhanh và dọn dẹp.


---

# Workflow: ccba-release-feature

---
description: Merge PR, cleanup branch và cập nhật walkthrough
applies_to:
  - "Phần mềm"
bundle: "_software"
---

# Workflow: Release Feature

Quy trình tự động hóa tích hợp mã nguồn (merge) và dọn dẹp môi trường.

## Bước 0: Thực thi Kiểm thử Toàn diện Slow Integration Tests (Pre-release Gate)

*Quy tắc bắt buộc:* Trước khi thực hiện merge PR, Agent **bắt buộc phải chạy kiểm thử toàn bộ tập test `slow` và `stress` trên toàn bộ packages** (thông qua cơ chế Dynamic Discovery) để đảm bảo các bài test cào mạng/tích hợp không bị hỏng ngầm (test decay):
```bash
python scripts/eval/run_isolated_tests.py --all --stress
```
- Nếu có bài test nào thất bại, Agent **phải dừng quy trình release ngay lập tức** để tiến hành sửa lỗi trước khi tiếp tục.


## Bước 1: Đối soát bình luận và Merge PR trên GitHub

1. Lấy và ghi nhớ tên branch hiện hành (Feature Branch Name) trước khi thực hiện dọn dẹp:
   ```bash
   git branch --show-current
   ```
2. Kiểm tra xem GitHub CLI (`gh`) có hoạt động không:
   ```bash
   gh auth status
   ```
3. Thực hiện đối soát tự động toàn bộ bình luận của Copilot:
   ```bash
   uv run python scripts/audit_pr_comments.py
   ```
   *Quy tắc bắt buộc:* 
   - Kể cả khi quy trình `/ccba-create-pr` đã bị quá thời gian chờ (timeout) đối với Copilot, khi thực hiện `/ccba-release-feature` Agent **bắt buộc phải chạy lại đối soát comments** trước khi merge.
   - Nếu phát hiện bất kỳ bình luận mới nào của Copilot (vừa được tạo sau thời điểm timeout), Agent phải tạm dừng quy trình merge, đánh giá và thực hiện chỉnh sửa mã nguồn cục bộ, commit & push cập nhật, và cập nhật `walkthrough.md` trước khi tiếp tục.
   - Nếu phát hiện các góp ý hợp lý (VALID) chưa sửa, hoặc các góp ý không hợp lý chưa được giải trình trong `walkthrough.md`, script sẽ báo lỗi chặn merge để Agent tiến hành sửa lỗi cục bộ và push cập nhật trước.
4. Nếu `gh` đã đăng nhập và đối soát thành công:
   - Kiểm tra trạng thái CI của PR hiện hành:
     ```bash
     gh pr checks
     ```
   - Nếu CI pass: Thực hiện merge và xóa remote branch tự động (sử dụng Squash and Merge để giữ lịch sử nhánh main tinh gọn):
     ```bash
     gh pr merge --squash --delete-branch
     ```
5. Nếu `gh` chưa đăng nhập:
   - Sử dụng `browser_subagent` truy cập trang PR của branch hiện tại.
   - Chờ CI pass, chọn **Squash and merge** -> **Confirm squash and merge** -> **Delete branch**.
   - Báo lỗi cụ thể cho người dùng nếu CI thất bại hoặc có xung đột (conflict).

## Bước 2: Cập nhật Lịch sử Thay đổi (Walkthrough)

1. Lấy danh sách các commit của feature branch hiện tại (so sánh với main/origin/main) **trước khi** chuyển nhánh:
   ```bash
   git log origin/main..[feature_branch_name] --oneline
   ```
2. Cập nhật nội dung tóm tắt thay đổi vào tệp tin `walkthrough.md`.

## Bước 3: Sync Local Codebase & Dọn dẹp

1. Kiểm tra trạng thái làm việc (working tree) để đảm bảo không có file nào bị dơ (uncommitted changes):
   ```bash
   git status --porcelain
   ```
   *Lưu ý:* Nếu có thay đổi chưa commit (ví dụ tệp tạm hoặc hotfix), hãy commit hoặc stash trước khi chuyển nhánh.
2. Quay về branch `main` và kéo code mới nhất:
   ```bash
   git checkout main && git pull origin main
   ```
3. Xóa branch feature cục bộ. Vì GitHub thường sử dụng cơ chế Squash Merge hoặc Rebase Merge (khiến mã hash commit khác biệt), lệnh `git branch -d` có thể báo lỗi chưa merge. Hãy sử dụng lực lượng xóa để dọn dẹp sạch sẽ:
   ```bash
   git branch -D [feature_branch_name]
   ```

## Bước 4: Thông báo hoàn tất

1. Báo cáo trạng thái hoàn tất:
   - ✅ Feature đã được tích hợp thành công.
   - 🗑️ Branch cục bộ đã được dọn dẹp (force-deleted).
   - 📝 Lịch sử thay đổi `walkthrough.md` đã cập nhật.


---

# Workflow: ccba-research

---
name: ccba-research
command: /ccba-research
description: Khởi động subagent nghiên cứu chạy ngầm để tra cứu tài liệu, APIs, source code hoặc VBPL song song dưới nền với rào chắn Search Budget Cap (5 tool calls) và Mẫu báo cáo 5 phần chuẩn hóa.
---

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `ccba-research` tại [SKILL.md](../skills/ccba-research/SKILL.md) để bắt đầu quy trình spawn subagent chạy ngầm, áp dụng Search Budget Cap (Max 5 tool calls), Cross-Reference Validation và xuất Báo cáo Kỹ thuật 5 phần chuẩn hóa.


---

# Workflow: ccba-resolving-merge-conflicts

---
description: Giải quyết xung đột Git merge/rebase hiện tại một cách an toàn.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Giải Quyết Xung Đột Git (/ccba-resolving-merge-conflicts)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `resolving-merge-conflicts` tại [SKILL.md](../skills/resolving-merge-conflicts/SKILL.md) để bắt đầu giải quyết xung đột Git cục bộ.


---

# Workflow: ccba-review-skill

---
description: Đánh giá chất lượng và tối ưu hóa tệp tin SKILL.md theo tiêu chuẩn viết skill của CCBA.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Đánh giá Chất lượng Skill (/ccba-review-skill)

Khi người dùng kích hoạt lệnh này dưới dạng `/ccba-review-skill <đường-dẫn-file>`, Agent hãy nạp và thực thi kỹ năng `review_skill` tại [SKILL.md](../skills/review_skill/SKILL.md) để bắt đầu quy trình rà soát, cắt tỉa và tối ưu hóa chất lượng tệp tin kỹ năng.


---

# Workflow: ccba-run-qc-pipeline

---
description: Tự động chạy toàn trình chuỗi kiểm soát chất lượng (QC) đa bộ môn (Discovery -> Orchestrator).
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
bundle: "_qc"
---

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng tại [SKILL.md](../skills/ccba-ai-qc-pipeline-orch/SKILL.md) để bắt đầu quy trình chạy toàn trình chuỗi kiểm soát chất lượng (QC Pipeline).


---

# Workflow: ccba-session-retrospective

---
description: Session Knowledge Retrospective Workflow — Tự động tổng hợp tri thức cuối phiên làm việc và dọn dẹp workspace.
applies_to:
  - "Tác vụ Admin"
  - "Phần mềm"
bundle: "_core"
---

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng tại [SKILL.md](../skills/session_retrospective/SKILL.md) để bắt đầu quy trình tổng hợp tri thức cuối phiên và dọn dẹp tệp tin tạm.


---

# Workflow: ccba-setup-pre-commit

---
description: Thiết lập cấu hình pre-commit cho Python trong repository hiện tại.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Thiết lập Pre-commit (/ccba-setup-pre-commit)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `setup-pre-commit` tại [SKILL.md](../skills/setup-pre-commit/SKILL.md) để bắt đầu quy trình thiết lập pre-commit hooks cho Python.


---

# Workflow: ccba-setup-skills

---
description: Thiết lập cấu hình dự án (Spoke/Hub) cho các công cụ phát triển phần mềm (cấu hình issue tracker, nhãn triage, domain docs)
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Thiết lập Cấu Hình Phát Triển (/ccba-setup-skills)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `ccba-setup-skills` tại [SKILL.md](../skills/ccba-setup-skills/SKILL.md) để bắt đầu quy trình trinh sát, phỏng vấn và ghi nhận cấu hình phát triển cho dự án.


---

# Workflow: ccba-setup-ts-deep-modules

---
description: Thiết lập cấu hình Deep Modules cho TypeScript bằng dependency-cruiser.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Thiết lập TS Deep Modules (/ccba-setup-ts-deep-modules)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `setup-ts-deep-modules` tại [SKILL.md](../skills/setup-ts-deep-modules/SKILL.md) để bắt đầu quy trình cấu hình ranh giới import cho TypeScript.


---

# Workflow: ccba-skills-eval

---
description: Khởi chạy hệ thống kiểm thử tự động (Evaluations) cho các kỹ năng AI trong CCBA Platform.
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

### Bước 2: Kích hoạt Core Eval Runner
Chạy lệnh CLI sau tại thư mục gốc của dự án:
```bash
# Kiểm thử một kỹ năng cụ thể
python .agents/skills/eval-gate/scripts/eval_runner.py --skill [tên-skill] --trials 3

# Tự động tối ưu hóa SKILL.md (Skill Auto-Tuner via SkillOpt loop)
python .agents/skills/eval-gate/scripts/eval_runner.py --skill [tên-skill] --auto-tune --max-iterations 3

# Kiểm thử toàn bộ các kỹ năng AI
python .agents/skills/eval-gate/scripts/eval_runner.py --trials 3
```

### Bước 3: Đánh giá, Khắc phục lỗi & Auto-Tuning (SkillOpt Loop)
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

# Workflow: ccba-sync-upstream

---
description: Kiểm tra cập nhật và đồng bộ tri thức từ ClaudeKit và MattPocock
applies_to:
  - "Phần mềm"
bundle: "_core"
---

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng sync-upstream tại [SKILL.md](../skills/sync-upstream/SKILL.md) để bắt đầu luồng kiểm tra cập nhật và đồng bộ tri thức từ thượng nguồn.


---

# Workflow: ccba-tdd

---
description: Viết code theo quy trình Test-Driven Development (Red-Green-Refactor).
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Test-Driven Development (/ccba-tdd)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `tdd` tại [SKILL.md](../skills/tdd/SKILL.md) để bắt đầu chu kỳ Red-Green-Refactor cục bộ.


---

# Workflow: ccba-teach

---
description: Khởi động không gian học tập và giảng dạy tương tác tại thư mục chuyên biệt .md/teach/
applies_to:
  - "Phần mềm"
bundle: "_core"
---

Khi người dùng gọi lệnh này, hãy nạp và thực thi kỹ năng tại [SKILL.md](../skills/teach/SKILL.md) để bắt đầu phiên giảng dạy tương tác (setup mục tiêu hoặc biên soạn bài giảng kế tiếp).


---

# Workflow: ccba-to-questionnaire

---
description: Chuyển đổi một quyết định chưa có đủ thông tin thành Bảng hỏi (Questionnaire) bất đồng bộ.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Tạo Bảng Hỏi Bất Đồng Bộ (/ccba-to-questionnaire)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `to-questionnaire` tại [SKILL.md](../skills/to-questionnaire/SKILL.md) để bắt đầu quy trình phỏng vấn 2 bước và soạn thảo Bảng hỏi Markdown.


---

# Workflow: ccba-to-spec

---
description: Soạn thảo tài liệu Spec từ ngữ cảnh hiện tại.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Soạn thảo Spec (/ccba-to-spec)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `to-spec` tại [SKILL.md](../skills/to-spec/SKILL.md) để bắt đầu quy trình soạn thảo tài liệu Đặc tả Kỹ thuật (Spec) dựa trên ngữ cảnh hội thoại hiện tại.


---

# Workflow: ccba-to-tickets

---
description: Phân rã kế hoạch hoặc spec (Đặc tả) hiện tại thành các ticket phát triển độc lập dạng lát cắt dọc (vertical slices)
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Workflow: Phân rã công việc thành Tickets (/ccba-to-tickets)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `to-tickets` tại [SKILL.md](../skills/to-tickets/SKILL.md) để phân rã yêu cầu thành các ticket phát triển độc lập và liên kết chặn.


---

# Workflow: ccba-triage

---
description: Điều phối và sàng lọc Issues/PRs qua các trạng thái và viết brief.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Điều phối và Sàng lọc Sự cố (/ccba-triage)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `triage` tại [SKILL.md](../skills/triage/SKILL.md) để bắt đầu quy trình điều phối trạng thái, xác thực lỗi, rà soát trùng lặp và soạn thảo Agent Brief.


---

# Workflow: ccba-tvpl-vip-crawler

---
description: Quy trình thực thi cào dữ liệu văn bản pháp luật VIP từ Thư viện Pháp luật (TVPL)
---

# Quy trình thực thi Slash Command `/ccba-tvpl-vip-crawler`

Khi người dùng kích hoạt lệnh Slash Command này dưới dạng:
`/ccba-tvpl-vip-crawler <đường-dẫn-url-hoặc-tên-văn-bản-tvpl>`

Agent tiếp nhận lệnh bắt buộc phải thực thi theo các bước sau:

1. **Kiểm tra Cấu hình & Nạp Kỹ năng**:
   - Đọc hướng dẫn tại [SKILL.md](../skills/tvpl-vip-crawler/SKILL.md).
   - Xác nhận tài khoản VIP `TVPL_USERNAME` và `TVPL_PASSWORD` sẵn sàng tại `.env`.

2. **Kích hoạt Script Cào VIP Trực tiếp**:
   - Thực thi lệnh cào tự động:
     ```bash
     python scripts/tvpl_vip_crawler.py "<đường-dẫn-url-hoặc-tên-văn-bản-tvpl>"
     ```

3. **Cấu trúc hóa OKF Bundle & Đồng bộ Google Drive**:
   - Kiểm tra kết quả đóng gói tại `.md/legal_docs/<slug>/`.
   - Báo cáo kết quả đóng gói thành công bao gồm các tệp `metadata.yaml`, `concept.md`, `index.md`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


---

# Workflow: ccba-update-legal-registry

---
name: ccba-update-legal-registry
description: Tự động đồng bộ các thay đổi pháp lý từ legal_registry.yaml lên Google NotebookLM (hỗ trợ lưu trữ qua Google Drive chung).
disable-model-invocation: true
keywords: [legal, sync, update, notebooklm, drive]
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
python scripts/legal_sync.py --notebook-id <notebook_id> [--use-drive] [--drive-folder <folder_id>] [--download-pdf]
```

## Tiêu chí Hoàn thành (Completion Criteria)
- **Kiểm chứng thành công**: Script chạy trả về mã thoát `Exit Code 0` (hoặc thông báo `Sync completed successfully` trên console output).
- **Attribution & Disclaimer**: Kết quả đầu ra hiển thị bảng thống kê số lượng nguồn được nạp mới/xóa bỏ, đồng thời bắt buộc đính kèm dòng bản quyền CCBA và Disclaimer pháp lý ở cuối tệp/tin nhắn phản hồi.
- **Xử lý lỗi**: Nếu gặp lỗi xác thực cookie (401/403) hoặc lỗi kết nối, in rõ thông báo lỗi chi tiết và hướng dẫn người dùng cập nhật lại Token môi trường thay vì im lặng kết thúc.


---

# Workflow: ccba-update-spoke

---
description: Cập nhật thủ công các lệnh và kỹ năng mới từ Hub về dự án Spoke hiện tại
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Cập nhật CCBA Spoke Workspace

Workflow này cho phép dự án (Spoke) hiện tại đồng bộ hóa và tải về các bản cập nhật mới nhất (kịch bản lệnh, kỹ năng) từ trung tâm CCBA Agent Platform (Hub) thông qua python sync script.

## Khi nào dùng:
- Khi khởi tạo hoặc cần cập nhật lại toàn bộ Skills và Workflows của Spoke theo nghiệp vụ.
- Khi Agent phát hiện yêu cầu của User cần đến kỹ năng trên Hub nhưng chưa được tải về Spoke (On-Demand / Lazy Loading).

## Các bước thực hiện:

### 1. Định vị Hub Path
Agent đọc tệp cấu hình `.md/workspace_context.yaml` hoặc biến môi trường `CCBA_HUB_PATH` để lấy đường dẫn Hub (`hub_path`). Mặc định sử dụng repository chung.

### 2. Đồng bộ toàn bộ theo nghiệp vụ
Chạy lệnh đồng bộ tự động dựa trên `project_type` khai báo trong `workspace_context.yaml`:
```powershell
python [hub_path]\scripts\sync_spoke.py --spoke .
```

### 3. Đồng bộ bổ sung một Kỹ năng/Workflow cụ thể (On-Demand)
Khi Agent nhận thấy cần bổ sung một skill cụ thể (ví dụ: `excalidraw-diagram`) để xử lý yêu cầu của User:
1. Agent xin sự cho phép từ người dùng: *"Tôi cần tải bổ sung kỹ năng [excalidraw-diagram] từ Hub để vẽ sơ đồ, bạn có đồng ý không?"*
2. Sau khi người dùng đồng ý, chạy lệnh:
   ```powershell
   python [hub_path]\scripts\sync_spoke.py --spoke . --sync-item excalidraw-diagram
   ```
3. Sau khi đồng bộ bổ sung, Antigravity sẽ tự động nhận diện skill mới nạp (Auto-Discovery) mà không cần khởi động lại. Agent tiếp tục thực thi yêu cầu của User.

## Báo cáo kết quả:
- In ra thông báo: *"Đã đồng bộ thành công các thành phần cập nhật từ Hub về Spoke."*


---

# Workflow: ccba-viet-chuyen-nghiep

---
description: Viết tiếng Việt chuyên nghiệp — nhà xuất bản AI
applies_to:
  - "Phần mềm"
bundle: "_software"
---

# Workflow: Viết tiếng Việt chuyên nghiệp (/ccba-viet-chuyen-nghiep)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `viet-chuyen-nghiep` tại [SKILL.md](../skills/viet-chuyen-nghiep/SKILL.md) để bắt đầu quy trình biên soạn và tối ưu văn bản tiếng Việt chuyên nghiệp.


---

# Workflow: ccba-wait-what

---
description: Dừng lại và giải thích lại tin nhắn trước bằng ngôn ngữ tiếng Việt đơn giản.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Giải Thích Lại Bằng Ngôn Ngữ Đơn Giản (/ccba-wait-what)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `wait-what` tại [SKILL.md](../skills/wait-what/SKILL.md) để dừng lại và diễn đạt lại nội dung vừa rồi bằng ngôn ngữ đơn giản, bổ sung ngữ cảnh cần thiết.


---

# Workflow: ccba-wayfinder

---
description: Vạch bản đồ giải quyết các bài toán mù mờ (foggy problems).
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Wayfinder Vạch Đường (/ccba-wayfinder)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `wayfinder` tại [SKILL.md](../skills/wayfinder/SKILL.md) để bắt đầu phân tích vấn đề và thiết lập bản đồ.


---

# Workflow: ccba-wizard

---
description: Tạo bash script wizard hướng dẫn quy trình cài đặt/thiết lập thủ công.
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# Workflow: Tạo Script Setup Wizard (/ccba-wizard)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `wizard` tại [SKILL.md](../skills/wizard/SKILL.md) để bắt đầu scope và sinh script setup wizard.


---

# Workflow: ccba-xia

---
description: Trích xuất, so sánh, port hoặc thích ứng một tính năng từ một repository GitHub hoặc đường dẫn thư mục cục bộ vào dự án hiện tại
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Workflow: Port tính năng (xỉa code) từ repository ngoài (/ccba-xia)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `ccba-xia` tại [SKILL.md](../skills/xia/SKILL.md) để bắt đầu quy trình trích xuất và chuyển dịch mã nguồn.


---

# Workflow: ccba-xu-ly-van-phong

---
description: Tạo, sửa, chuyển đổi file văn phòng (Word, Excel, PowerPoint, PDF)
applies_to:
  - "Phần mềm"
bundle: "_software"
---

# Workflow: Xử lý Văn phòng (/ccba-xu-ly-van-phong)

Khi người dùng kích hoạt lệnh này, Agent hãy nạp và thực thi kỹ năng `xu-ly-van-phong` tại [SKILL.md](../skills/xu-ly-van-phong/SKILL.md) để bắt đầu quy trình tạo, sửa, chuyển đổi định dạng và format văn bản văn phòng chuyên nghiệp.


---

# Workflow: ccba-youtube-learn

---
description: Khảo cổ học Niềm tin (Belief Archaeology) từ video YouTube/bài giảng học thuật.
---

# Lệnh /ccba-youtube-learn

Khi nhận được lệnh này, hãy nạp trực tiếp kỹ năng [SKILL.md](../skills/youtube-learn/SKILL.md) và làm theo hướng dẫn thực thi trong đó để thực hiện bóc tách phụ đề, hình ảnh slide học thuật và khảo cổ thế giới quan diễn giả.


---

# Workflow: workflow_pccc_cdt_tuthamdinh

---
name: workflow_pccc_cdt_tuthamdinh
description: Quy trình Hỗ trợ Chủ đầu tư Tự thẩm định toàn bộ thiết kế PCCC (theo Luật 55/2024 & NĐ 105/2025)
applies_to:
  - "Quản lý chất lượng"
  - "Thẩm tra thiết kế"
  - "PCCC"
bundle: "_qc"
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

# Workflow: workflow_pccc_thamdinh_congan

---
name: workflow_pccc_thamdinh_congan
description: Quy trình Thẩm định thiết kế PCCC phần Hệ thống Cơ điện (MEP) nộp Cơ quan Công an (PC07)
applies_to:
  - "Quản lý chất lượng"
  - "Thẩm tra thiết kế"
  - "PCCC"
bundle: "_qc"
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

# Workflow: workflow_pccc_thamdinh_cqxd

---
name: workflow_pccc_thamdinh_cqxd
description: Quy trình Thẩm định/Thẩm tra PCCC phần Kiến trúc & Kiểm soát khói nộp Cơ quan chuyên môn về xây dựng (theo Luật 55/2024 & NĐ 105/2025)
applies_to:
  - "Quản lý chất lượng"
  - "Thẩm tra thiết kế"
  - "PCCC"
bundle: "_qc"
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
