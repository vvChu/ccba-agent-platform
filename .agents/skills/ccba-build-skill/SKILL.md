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
tier: kernel
command: /ccba-build-skill
metadata:
  version: "1.1.1"
  author: "CCBA Hub"
gpi:
  s: 3.0
  k: 2.0
  a: 2.0
  p: 1.0
triggers:
- ccba-writing-great-skills
- writing-great-skills
- ccba-review-skill
- review-skill
---

# Workflow: Xây Dựng Kỹ Năng & Quy Trình Chuẩn (/ccba-build-skill)

Khi người dùng kích hoạt lệnh này dưới dạng:
`/ccba-build-skill <danh-sách-nguồn-hoặc-thư-mục> [--name <tên-skill>] [--local]`

Agent tiếp nhận lệnh bắt buộc phải tự động thực thi chuỗi tác vụ sau:

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `seam-exempt`. Kỹ năng này là SOP kernel tác tạo kỹ năng AI mới: kiểm tra môi trường Hub vs. Spoke, quét bảo mật qua `scripts/maskara.py` (Seam `maskara_scanner.v1`), nạp nguồn qua Cloud RAG (`notebooklm_rag.v1`) hoặc Local Fallback (`model_routing.v1`), áp dụng Cổng 0 (Determinism), Cổng 1 (Orchestration), định lượng chỉ số GPI qua `ccba-harness evaluate-gpi --json`, sinh `SKILL.md` và `eval_<stem>.json`, biên dịch `compile_catalog.py`, tự phục hồi lỗi theo Allowlist và kiểm định `verify-patch --preset skill`. Kỹ năng đóng vai trò caller điều phối, bản thân là quy trình tác tạo vận hành độc lập với các Seam dữ liệu ứng dụng.
- **Governance Compliance**: Đạt chuẩn Governance ADR-0057 Tier 2B Standalone Kernel Skill với điểm GPI (S: 3.0, K: 2.0, A: 2.0, P: 1.0) = 14.0 >= 12.0. Toàn bộ 3 tệp tài liệu chuyên sâu (`references/skill_authoring_guide.md`, `references/skill_review_checklist.md`, `references/skill_glossary.md`) được bảo tồn nguyên vẹn tại chỉ mục Level 3.

---

## 🌐 0. Tiền Kiểm Tra Môi Trường & Phân Định Hub vs. Spoke
Trước khi thực hiện bất kỳ thao tác nào, Agent bắt buộc phải xác định ngữ cảnh thực thi:
- Đọc `git remote get-url origin`.
  - **Trường hợp 1 (Hub Mode):** URL remote chứa `ccba-agent-platform`. Tiếp tục thực thi tác vụ tại checkout hiện tại.
  - **Trường hợp 2 (Spoke Mode):** Không chứa `ccba-agent-platform`.
    1. Kiểm tra biến môi trường `CCBA_HUB_PATH` (`$CCBA_HUB_PATH` trên Bash hoặc `$env:CCBA_HUB_PATH` trên PowerShell).
    2. **Điều kiện dừng (Stop Conditions):** Nếu `CCBA_HUB_PATH` không được thiết lập, không phải thư mục git của Hub, trùng toplevel với Spoke hiện tại, cây làm việc của Hub đang bẩn (`git -C "<hub_path>" status --porcelain` khác rỗng), Hub không đứng đúng nhánh tích hợp mặc định `main` (`git -C "<hub_path>" branch --show-current` khác `main`), hoặc đã tồn tại nhánh/PR `proposal/<tên-skill>` $\rightarrow$ **DỪNG LẠI NGAY** và thông báo lý do chi tiết. Cấm tự ý suy diễn đường dẫn ổ đĩa. Cấm tự ý chạy `git checkout` chuyển nhánh có sẵn hay `git pull` trên Hub.
    3. Định tuyến toàn bộ việc tạo tệp tin kỹ năng sang `<hub_path>` trên một nhánh làm việc mới `git -C "<hub_path>" checkout -b proposal/<tên-skill>`.
    4. Chỉ chuẩn bị gói đề xuất, chạy kiểm tra chống rò rỉ dữ liệu Spoke bằng `python "<hub_path>/scripts/governance/check_spoke_leakage.py" --root "<hub_path>"`, cấm tự ý đẩy mã lên remote. Sau khi hoàn tất kiểm định, yêu cầu người dùng xác nhận trước khi kích hoạt `/ccba-contribute-to-hub`.
- **Tiêu chí hoàn thành:** Xác định đúng môi trường Hub/Spoke và vị trí làm việc hợp lệ.

---

## 🛡️ 1. Quét Bảo Mật & Nạp Nguồn Dual-Mode (Per-Source Ingestion)
- Đọc danh sách nguồn tài liệu được cung cấp (tệp tin cục bộ, URL hoặc video).
- **Quét bảo mật từng nguồn:** Chạy quét bảo mật qua `scripts/maskara.py` (Seam `maskara_scanner.v1`) đối với từng tệp tin cục bộ. Nếu phát hiện rò rỉ bí mật (`findings` khác rỗng) $\rightarrow$ **DỪNG LẠI NGAY** đối với nguồn đó và cảnh báo người dùng.
- **Định tuyến nguồn theo phân loại bảo mật:**
  - **Chế độ A (Cloud RAG qua NotebookLM):** Áp dụng cho tài liệu công khai, URL web, video YouTube. Sử dụng Seam `notebooklm_rag.v1` thông qua `python -m ccba_notebooklm`. Nếu gặp các failure modes của cloud (`auth_expired`, `quota_exceeded`, `source_upload_failed`) $\rightarrow$ tự động hạ cấp xuống Chế độ B.
  - **Chế độ B (Local Knowledge Extraction - Fallback):** Áp dụng khi người dùng truyền cờ `--local`, hoặc nguồn là tài liệu mật của dự án không được đưa lên cloud. Sử dụng pipeline xử lý tài liệu sẵn có (`ccba-markdown-document-processing`) và gọi mô hình qua `model_routing.v1` (`from ccba_ai.routing import choose_model`). Cấm viết parser ad-hoc mới.
  - **Văn bản pháp quy:** Nếu nguồn là văn bản quy phạm pháp luật Việt Nam, chuyển hướng sang `/ccba-legal-ingest` theo ADR-0059.
- **Tiêu chí hoàn thành:** Toàn bộ nguồn được quét sạch bí mật và nạp an toàn theo đúng phân loại bảo mật.

---

## 📚 2. Chưng Cất Tri Thức Vào Scratch Tạm
- Kết xuất cẩm nang tri thức tổng hợp Markdown vào thư mục đệm `.md/scratch/build-skill/<tên-skill>/summary.md`. **CẤM** ghi trực tiếp vào `.md/knowledge/` dài hạn của repo trước khi kỹ năng vượt qua kiểm định.
- Đọc cẩm nang này để nắm rõ toàn bộ logic, patterns, parameters, APIs và ranh giới nghiệp vụ của công cụ cần tạo skill.
- **Tiêu chí hoàn thành:** Tệp tri thức tổng hợp Markdown được lưu trữ đầy đủ trong `.md/scratch/build-skill/<tên-skill>/`.

---

## ⚖️ 3. Tiền Kiểm Tra Cổng Kiến Trúc & Định Lượng GPI Bằng CLI Tất Định (HUB-ADR-0057)
Trước khi khởi tạo bất kỳ tệp tin nào, Agent bắt buộc chạy bộ kiểm định quyết định 2 giai đoạn bằng CLI có cấu trúc:

### Phần 3.1: Thu thập bằng chứng 4 trục định lượng
Agent chuẩn bị 4 dòng bằng chứng quan sát được thực tế từ cẩm nang tri thức:
- **S (Reasoning Steps):** Số bước suy luận nhận thức (1.0 – 5.0).
- **K (Interface / Schema Complexity):** Số tham số và độ phức tạp input/output (1.0 – 5.0).
- **A (Autonomous Model Invocation):** Mức độ tự động triệu hồi (1.0 cho Ritual/User-invoked, 2.0 – 5.0 cho Model-invoked).
- **P (Parent Domain Coupling):** Tên kỹ năng cha và mức độ gắn kết (1.0 – 5.0).

### Phần 3.2: Chạy CLI Kiểm định Tất định & Parse JSON
Chạy lệnh đánh giá với cờ `--json`:
```bash
python -m ccba_harness evaluate-gpi --name <tên-skill> --s <S> --k <K> --a <A> --p <P> --json
```
- Nếu tác vụ giải quyết 100% bằng giải thuật xác định (regex, AST parse, math, file I/O) $\rightarrow$ thêm cờ `--deterministic`.
- Nếu tác vụ điều phối đa tác tử song song, StateGraph hoặc cần HITL $\rightarrow$ thêm cờ `--orchestrated`.
- Kỹ năng mới (greenfield) **CẤM** truyền `--existing-tier` và `--force-tier-flip`.

### Phần 3.3: Định tuyến Đầu ra Dựa trên JSON
Agent bắt buộc đọc trường `tier` (chuỗi `ArchitectureTier.value` đầy đủ; lưu ý các mã ngắn `tier-1..tier-3` chỉ là tham số CLI của `--existing-tier`) và cờ top-level `allow_standalone_skill` trong JSON trả về (không chỉ dựa vào Exit Code 0):
- **Cổng 0 (`tier: "Tier 1: Package Function / Deep Seam"`):** **DỪNG LẠI NGAY**, triển khai tại Tầng 1 (`packages/*/src/`). Nghiêm cấm tạo Skill phẳng độc lập.
- **Cổng 1 (`tier: "Tier 3: Composite Orchestrator"`):** **DỪNG LẠI NGAY**, triển khai tại Tầng 3 (`.agents/workflows/` hoặc Orchestrator khai báo `tier: orchestrator`).
- **Tier 2A (`tier: "Tier 2A: Progressive Reference"` hoặc `allow_standalone_skill: false`):** Tạo tệp tham chiếu tăng tiến tại `.agents/skills/<parent-skill>/references/<tên-skill>.md` (kèm cờ `--parent <parent>`). Dừng quy trình tạo thư mục skill riêng.
- **Tier 2B (`tier: "Tier 2B: Standalone Kernel Skill"` và `allow_standalone_skill: true`):** Đủ điều kiện tạo thư mục kỹ năng riêng tại `.agents/skills/ccba-<tên-skill>/SKILL.md`. Sao chép chính xác 4 số $S, K, A, P$ từ kết quả JSON vào frontmatter (cấm giữ mẫu mặc định).

- **Tiêu chí hoàn thành:** Nhận được JSON định tuyến kiến trúc hợp lệ và xác định chính xác tầng đích lưu trữ.

---

## 🧩 4. Khởi Tạo Cấu Trúc SKILL.md Đạt Chuẩn & Full-Stack Scaffolding (HUB-ADR-0001, HUB-ADR-0040, HUB-ADR-0057, HUB-ADR-0058)
Nếu $GPI \ge 12.0$ (`Tier 2B: Standalone Kernel Skill` và `allow_standalone_skill: true`):

### 4.1. Khởi tạo tệp `SKILL.md`
Tạo thư mục tại `.agents/skills/ccba-<tên-skill-kebab-case>/SKILL.md` theo khung chuẩn:

```markdown
---
name: ccba-<tên-skill-kebab-case>
description: <Mô tả ngắn gọn súc tích <= 180 ký tự>
metadata:
  version: "1.0.0"
  author: "CCBA Hub" # Bắt buộc có metadata.version & metadata.author để đạt GREEN trên audit_skills_hygiene.py
user-invocable: true # Bắt buộc true nếu là slash command / ritual do người dùng gọi
disable-model-invocation: true # true cho ritual/tool skills (0-token prompt, a: 1.0), false nếu là master deep skill
command: /ccba-<tên-skill-kebab-case> # Bắt buộc có dòng command khớp với /{name} theo HUB-ADR-0056
category: productivity # productivity | coding | testing | reasoning | documentation | governance
bundle: _core # _core | _software | _qc | _consulting | _bim
tier: kernel # Bắt buộc cho Standalone Kernel Skill để bảo lưu Hysteresis ADR-0057 về sau
triggers:
- <trigger_1>
- <trigger_2>
gpi: {s: <S>, k: <K>, a: <A>, p: <P>} # Sao chép chính xác 4 số từ kết quả JSON của evaluate-gpi
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

### 4.2. Phân tầng Level 3 Progressive Disclosure
Nếu tài liệu hướng dẫn vượt quá ngân sách ngữ cảnh (ADR-0030), tự động tách nội dung chi tiết sang thư mục `.agents/skills/ccba-<tên-skill>/references/` và thiết lập bảng chỉ mục tại Level 3 của `SKILL.md`.

### 4.3. Full-Stack Scaffolding: Khởi tạo Ca Kiểm Thử Mẫu (Eval Dataset)
Bắt buộc khởi tạo tệp ca kiểm thử mẫu tại:
`.agents/skills/ccba-eval-gate/test_cases/eval_<stem>.json`
- **Quy ước tên:** `<stem>` là tên skill đã bỏ tiền tố `ccba-` hoặc `bigbim-` và đổi dấu gạch ngang `-` thành gạch dưới `_` (khớp hoàn toàn với hàm `resolve_domain_dataset()` của `ccba-harness`). Ví dụ: `ccba-legal-intel` $\rightarrow$ `eval_legal_intel.json`.
- **Rào chắn chống ghi đè:** Nếu tệp đã tồn tại, **DỪNG LẠI** và cảnh báo, không ghi đè dataset đang dùng.
- **Cấu trúc nội dung:** Mảng JSON tối thiểu 2 phần tử (schema chuẩn như `eval_skill_repair.json`):
  1. **Ca Happy-Path:** Đầu vào chuẩn, rubric đòi hỏi các token vận hành thật (`evaluate-gpi --json`, `allow_standalone_skill`, Maskara).
  2. **Ca Red-Team:** Đầu vào biên/nguy hiểm (tác vụ regex tất định đòi tạo skill, tài liệu mật đòi upload, hoặc Spoke thiếu `CCBA_HUB_PATH`), rubric đòi hỏi Agent phải dừng lại từ chối thực hiện.

- **Tiêu chí hoàn thành:** Tệp `SKILL.md` và tệp `eval_<stem>.json` được khởi tạo chuẩn xác và đồng bộ.

---

## ⚡ 5. Kích Hoạt Slash Command Native & Biên Dịch Catalog (HUB-ADR-0047, HUB-ADR-0056)
- **Bắt buộc có `user-invocable: true`** và **`command: /ccba-<tên-lệnh>`** để IDE Antigravity hiển thị trên menu khi gõ `/`.
- Khai báo `disable-model-invocation: true` nếu là lệnh điều phối/quy trình thủ tục (0-token system prompt).
- Chạy lệnh biên dịch catalog để tự động cập nhật hệ thống:
```bash
python scripts/governance/compile_catalog.py
```
- **Tiêu chí hoàn thành:** Catalog `catalog.yaml` được biên dịch thành công và đồng bộ 100% với frontmatter.

---

## ✅ 6. Kiểm Định Chất Lượng Tự Động & Vòng Lặp Tự Phục Hồi (ADR-0058 Hard Completion Lock)
Đồng bộ đủ 3 bề mặt quản trị trên Hub rồi chạy cổng kiểm định máy tính một chạm để xác nhận đạt chuẩn 100% trước khi bàn giao:
```bash
python scripts/governance/compile_catalog.py
python scripts/governance/compile_skills_docs.py --write
python scripts/sync_hub_adr_matrix.py
python scripts/governance/compile_skills_docs.py --check
python -m ccba_harness verify-patch --preset skill --target .agents/skills/ccba-<tên-skill>
```
*Cổng preset `skill` tự động chạy: (1) `validate_skills.py --enforce-gpi`, (2) `compile_catalog.py --check`, và (3) `sync_hub_adr_matrix.py --check`.*

### Vòng Lặp Tự Phục Hồi (Self-Healing Loop có Allowlist)
Nếu lệnh `verify-patch` trả về mã lỗi khác 0 (`exit code != 0`), Agent được phép tự động khắc phục với các ràng buộc nghiêm ngặt:
1. **Trần số vòng lặp:** Tối đa **2 lần thử lại** (bộ đếm được duy trì tường minh).
2. **Allowlist được phép sửa:**
   - Sửa lỗi cú pháp YAML frontmatter (thụt lề 2 spaces, đóng ngoặc kép).
   - Sửa các liên kết tương đối bị đứt gãy (`broken relative links`).
   - Chuẩn hóa tiêu chí hoàn thành (`Completion Criterion`) ở các bước.
   - Chạy lại lệnh biên dịch catalog `compile_catalog.py`.
3. **Danh mục CẤM TUYỆT ĐỐI trong vòng sửa chữa:**
   - **CẤM** sửa đổi các hệ số $S, K, A, P$ trong khối `gpi:`.
   - **CẤM** đảo ngược kết luận Cổng 0 hoặc Cổng 1.
   - **CẤM** gọi lại đệ quy `/ccba-build-skill`.
4. **Cơ chế ngắt sớm:** Nếu sau 1 lần sửa mà hash SHA-256 của tệp `SKILL.md` không đổi $\rightarrow$ **DỪNG NGAY** vòng lặp.
5. **Dừng và Báo cáo:** Nếu sau 2 lần tự vá mà `verify-patch` vẫn thất bại, in toàn bộ `stderr`, mã thoát lỗi và dừng quy trình theo quy tắc Khóa Cứng (ADR-0058). Cấm tuyên bố hoàn thành.
6. **Dọn dẹp buffer:** Sau khi kiểm định xanh (Exit Code 0), dọn dẹp thư mục tạm `.md/scratch/build-skill/<tên-skill>/`.
7. **Đóng góp Upstream (ở Spoke):** Yêu cầu người dùng xác nhận trước khi kích hoạt `/ccba-contribute-to-hub` để tạo PR đóng góp ngược về Hub.

- **Tiêu chí hoàn thành:** Lệnh `python -m ccba_harness verify-patch --preset skill --target .agents/skills/ccba-<tên-skill>` trả về **Exit Code 0** (Overall Status: PASS).

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/skill_authoring_guide.md` | Cẩm nang hướng dẫn kỹ sư biên soạn tệp chỉ dẫn SKILL.md chuẩn mực |
| `references/skill_review_checklist.md` | Bảng kiểm định chất lượng và tuân thủ thể chế ADR-0057 cho kỹ năng |
| `references/skill_glossary.md` | Bảng thuật ngữ và quy ước định danh kỹ năng chuẩn mực CCBA |
