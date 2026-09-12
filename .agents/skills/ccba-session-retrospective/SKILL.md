---
name: ccba-session-retrospective
description: Tự động tổng hợp tri thức cuối phiên làm việc (Retrospective), tiến hóa
  kỹ năng trực tiếp, đồng bộ ADR Matrix, tái biên dịch tài liệu, kích hoạt Governance
  Gate và dọn dẹp workspace.
disable-model-invocation: true
category: workflow
user-invocable: true
command: /ccba-session-retrospective
gpi:
  s: 3.0
  k: 2.0
  a: 1.0
  p: 1.0
keywords:
- retrospective
- session learnings
- skill evolution
- governance gate
- tổng kết phiên
- bài học kinh nghiệm
- kiểm định quản trị
metadata:
  author: CCBA
  version: 1.3.0
bundle: _core
tier: kernel
triggers:
- retrospective
- session learnings
- skill evolution
- governance gate
- tổng kết phiên
- bài học kinh nghiệm
- kiểm định quản trị
- ccba-session-retrospective
---
# Quy trình Tổng kết Phiên làm việc (Session Retrospective)

Kỹ năng này được kích hoạt ở cuối mỗi phiên làm việc để:
- Chắt lọc tri thức thực chiến (Evidence-Backed Learnings) và cập nhật vào Knowledge Base trung tâm.
- **Tiến hóa Kỹ năng Trực tiếp (Skill Evolution Loop):** Sửa đổi, nâng cấp và bump version các tệp `SKILL.md` liên quan ngay khi phát hiện khiếm khuyết trong phiên.
- **Đồng bộ Ma Trận ADR & Tái Biên Dịch Tài Liệu:** Duy trì Living Traceability Matrix và đồng bộ hóa Service Catalog/Web Documentation Portal.
- Kích hoạt **Governance & Architecture Drift Gate** và **ADR-0058 Hard Completion Lock** nhằm bảo đảm tài liệu, môi trường và test suite hoàn toàn đồng bộ trước khi đóng phiên.
- Dọn dẹp tệp tin rác trong workspace và quản lý commit an toàn qua Bypass Protocol.

---

## Quy trình Thực hiện (Process)

### Bước 1: Thu thập & Chắt lọc Tri thức (Evidence-Backed Learnings)
- Đọc [`.md/knowledge/session_learnings.md`](../../../.md/knowledge/session_learnings.md) để nắm context 5 Miền Kiến Trúc (ADR-0057) hiện tại và chống trùng lặp:
  1. **Architecture & Governance** (Miền 1)
  2. **Code Quality & Testing** (Miền 2)
  3. **Legal & Data Standards** (Miền 3)
  4. **Workflows & Review** (Miền 4)
  5. **Windows & Tooling** (Miền 5)
- **Quy chuẩn Tiered Memory Model (ADR-0030, ADR-0057):**
  * Ngân sách trần cứng của `session_learnings.md` là $\le 10.0\text{ KB}$ (10,240 bytes).
  * Chỉ ghi nhận các quy tắc cô đọng dạng `RULE-X.Y` (ngắn gọn, tập trung vào Invariants).
  * Mọi bug narrative chi tiết, nhật ký phân tích dài dòng phải định tuyến lưu vào [`.md/knowledge/archive/session_learnings_history.md`](../../../.md/knowledge/archive/session_learnings_history.md).
- Phân tích toàn bộ diễn biến phiên làm việc hiện tại để nhận diện:
  * **Vấn đề & Điểm nghẽn:** Những giả định sai lầm, hiểu lầm về SDK/Transport, hoặc các vòng lặp phản biện/sửa lỗi kéo dài.
  * **Giải pháp & Deep Seams:** Các mẫu thiết kế thành công giúp đơn giản hóa hệ thống (High Leverage & Locality).
  * **Độ Chuẩn xác Định danh (Naming Precision):** Đặt tên Core Patterns / Anti-Patterns phản ánh đúng bản chất kỹ thuật (ví dụ: *Embedded Domain Logic* thay vì *Undocumented Domain Logic*).
- **Tiêu chí hoàn thành:** Lập danh sách tri thức mới kèm dẫn chứng cụ thể từ codebase (tên class, tên module, mã lỗi) và phân loại chuẩn vào đúng Miền Kiến Trúc, tuân thủ nghiêm ngặt Tiered Memory Model.

### Bước 2: Cập nhật Knowledge Base, Mutation Log & Ma Trận ADR
- Ghi nhận các quy tắc cô đọng `RULE-X.Y` mới vào [`.md/knowledge/session_learnings.md`](../../../.md/knowledge/session_learnings.md) dưới đúng Miền Kiến Trúc tương ứng.
- **Kiểm tra Kích thước Bộ nhớ Làm việc:**
  ```bash
  python scripts/governance/compact_session_learnings.py --stats
  ```
  Nếu kích thước vượt quá hoặc tiệm cận $10.0\text{ KB}$ (10,240 bytes), thực hiện nén và lưu trữ bug narratives chi tiết vào [`.md/knowledge/archive/session_learnings_history.md`](../../../.md/knowledge/archive/session_learnings_history.md).
- Ghi nhận nhật ký dòng thời gian vào [`.md/knowledge/log.md`](../../../.md/knowledge/log.md) theo chuẩn `## [YYYY-MM-DD] [operation] | Title` nếu phiên làm việc có nạp/sửa đổi/ban hành tài liệu mới.
- Cập nhật mục lục danh mục [`.md/knowledge/index.md`](../../../.md/knowledge/index.md) nếu có thêm tệp tài liệu mới.
- **Tự động đồng bộ Living Traceability Matrix cho ADRs:**
  ```bash
  python scripts/sync_hub_adr_matrix.py
  ```
- Giữ nguyên cấu trúc phân loại theo 5 Miền Kiến Trúc, sử dụng đúng bộ từ vựng thiết kế Deep Modules (`/ccba-codebase-design`).
- **Tiêu chí hoàn thành:** Tệp `session_learnings.md` duy trì kích thước $\le 10.0\text{ KB}$, `log.md` và Living Traceability Matrix (`docs/adr/TRACEABILITY_MATRIX.md`, `docs/adr/README.md`) được cập nhật đầy đủ, không tạo orphan notes.

### Bước 3: Tiến hóa Kỹ năng Trực tiếp (Direct Skill Evolution Loop) & Recompilation Gate
- **Nguyên tắc "Học đi đôi với Hành":** Không dừng lại ở việc ghi nhận thụ động vào `session_learnings.md`. Nếu bài học ở Bước 2 chỉ ra một quy trình trong `SKILL.md` (như `ccba-improve-codebase-architecture`, `ccba-code-review`, `ccba-tvpl-vip-crawler`...) còn thiếu rào chắn hoặc gây sai lệch:
  * **Bổ sung bước rà soát cụ thể:** Đưa các câu hỏi tự phản biện (Pre-Proposal Self-Check) hoặc rào chắn kỹ thuật vào quy trình của Skill tương ứng.
  * **Bắt buộc có Tiêu chí hoàn thành (Exit Criteria):** Mọi bước rà soát mới thêm vào Skill phải có tiêu chí đo lường rõ ràng (ví dụ: bảng xác nhận ✅/❌ 4 dòng, tỷ lệ phục hồi, mã thoát CLI).
  * **Bump Version:** Cập nhật version trong frontmatter của tệp `SKILL.md` được sửa đổi (ví dụ: `1.1.0` $\rightarrow$ `1.2.0`).
- **Rào chắn Phạm vi (Scope Creep Guard):** Agent **KHÔNG** tự ý sửa tất cả các SKILL.md phát hiện có khiếm khuyết. Thay vào đó, Agent phải **đề xuất danh sách các Skill cần sửa** kèm lý do cụ thể (1-2 dòng mỗi Skill) rồi **chờ người dùng quyết định** Skill nào sẽ được sửa trong phiên hiện tại.
- **Rào Chắn Tái Biên Dịch Bắt Buộc (Recompilation Gate):**
  Ngay sau khi tạo mới hoặc sửa đổi bất kỳ tệp `SKILL.md` nào, Agent **bắt buộc** phải kích hoạt quy trình tái biên dịch kép để đồng bộ hóa Service Catalog và Web Documentation Portal:
  ```bash
  python scripts/governance/compile_catalog.py
  python scripts/governance/compile_skills_docs.py --write
  ```
- **Tiêu chí hoàn thành:** Danh sách đề xuất được hiển thị cho người dùng; các `SKILL.md` được người dùng phê duyệt đã được cập nhật hoàn chỉnh, bump version, và vượt qua Recompilation Gate (`catalog.yaml` và `docs/skills/` được biên dịch đồng bộ).

### Bước 4: Rào chắn Kiểm định Quản trị & ADR-0058 Hard Completion Lock
Trước khi kết thúc phiên, Agent **bắt buộc** phải thực hiện quy trình kiểm định quản trị đa tầng:

1. **Cập nhật số liệu kiến trúc:**
   ```bash
   python scripts/update_arch_stats.py
   ```
2. **Bộ 4 lệnh kiểm tra cốt lõi:**
   - Kiểm tra tính hợp lệ & chỉ số GPI của Skills:
     ```bash
     python scripts/validate_skills.py --enforce-gpi
     ```
   - Kiểm tra sức khỏe LLM-Wiki Knowledge Hub:
     ```bash
     python scripts/governance/wiki_health_linter.py
     ```
   - Kiểm tra ngân sách bộ nhớ `session_learnings.md` ($\le 10.0\text{ KB}$):
     ```bash
     python scripts/governance/compact_session_learnings.py --check
     ```
   - Kiểm tra tài liệu, biến môi trường & Architecture Drift:
     ```bash
     python scripts/validate_docs.py --changed
     ```
     *Nếu phát hiện cảnh báo Structural Drift hoặc thiếu biến môi trường, Agent phải cập nhật ngay `README.md`, `PLATFORM.md`, và `.env.example` trước khi tiếp tục.*
3. **Bộ test quản trị scoped nhanh (< 20s):**
   ```bash
   python -m pytest packages/ccba-harness/tests/test_telemetry.py packages/ccba-harness/tests/test_verify_patch.py tests/governance/ -q
   ```
4. **Khóa cứng hoàn tất tất định (ADR-0058 Hard Completion Lock):**
   ```bash
   python -m ccba_harness verify-patch --preset skill
   ```
- **Tiêu chí hoàn thành:** Cả 4 lệnh kiểm tra cốt lõi, scoped test suite và khóa cứng `verify-patch --preset skill` đều trả về Exit code 0 (100% PASS). Agent nghiêm cấm báo cáo hoàn thành hoặc yêu cầu người dùng nghiệm thu nếu có bất kỳ kiểm định nào thất bại. Lưu ý: `validate_docs.py` có thể trả về Exit code 0 kèm cảnh báo `[WARN]` — đây là chấp nhận được; chỉ khi Exit code 1 (`[ERROR]`) mới chặn hoàn tất.

### Bước 5: Dọn dẹp Tự động & Commit Bypass (Workspace & Git Clean)
- **Dọn dẹp tự động qua công cụ nền tảng:**
  Chạy lệnh dọn dẹp để tự động rà soát và xóa các tệp nháp, log tạm, cache và artifacts không cần thiết:
  ```bash
  python scripts/session_cleanup.py --execute
  ```
- **Phân phối tài liệu thô (nếu có):** Di chuyển các file tài liệu đã xử lý từ `input_documents/` sang `.md/extracted_docs/` hoặc vị trí lưu trữ phù hợp theo quy định của dự án.
- **Vượt cổng `simplify_gate` an toàn (Commit Bypass Protocol — RULE-2.10):**
  * Rào chắn `simplify_gate` (`scripts/hooks/simplify.py`) tự động chặn các commit có quy mô lớn (> 400 LOC, > 8 files) hoặc chứa động từ nhạy cảm.
  * Khi phiên làm việc sinh diff lớn do tái biên dịch tài liệu web portal tự động (`docs/skills/`, `catalog.yaml`), sử dụng tiền tố `# APPROVED: <lý do>` trong câu lệnh commit hoặc chú thích (ví dụ: `git commit -m "docs(skills): update portal # APPROVED: recompilation gate"`). Điều này kích hoạt `context.is_approved = True` cho phép commit an toàn.
- **Commit toàn bộ thay đổi:** Tạo commit với message chuẩn `docs(knowledge): session retrospective ...`.
- **Tiêu chí hoàn thành:** Workspace sạch sẽ (`git status` clean, không còn file rác untracked), và commit thành công tuân thủ rào chắn `simplify_gate`.

### Bước 6: Xuất Báo cáo Tóm tắt (Session Retrospective Summary)
Xuất báo cáo tổng kết ra màn hình chat theo định dạng:
- **Mục tiêu & Kết quả:** Tóm tắt 2-4 dòng kết quả đã hoàn thành.
- **Tri thức & Kỹ năng Tiến hóa:** Bảng liệt kê các Patterns/Anti-patterns/RULEs mới (thuộc 5 Miền Kiến Trúc) và các `SKILL.md` đã được nâng cấp.
- **Trạng thái Kiểm định Quản trị & ADR-0058:** Kết quả chạy bộ 4 Governance Gate và `ccba-harness verify-patch`.
- **Mã Commit & Bypass:** Hash commit cuối cùng của phiên (kèm ghi chú `# APPROVED:` nếu áp dụng).
- **Tiêu chí hoàn thành:** Báo cáo tổng kết hiển thị đầy đủ 4 mục trên trong cửa sổ chat, kèm liên kết Markdown dẫn đến các tệp tri thức vừa cập nhật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
