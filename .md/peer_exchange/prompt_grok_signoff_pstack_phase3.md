---
request_id: "req-20261019-signoff-pstack-phase3-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "verify"
profile: "signoff_diff"
subject: "Stage 3 Post-Code Sign-Off: Pstack Phase 3 (v0.15.20 -> v0.15.27/28 — Zero Skill Bloat)"
timestamp: "2026-10-19T16:45:45+07:00"
source_documents:
  - .agents/skills/ccba-create-verification-skill/SKILL.md
  - .agents/skills/ccba-create-verification-skill/references/maintain_drift_guide.md
  - .agents/skills/ccba-grilling/SKILL.md
  - .agents/skills/ccba-handoff/SKILL.md
  - .agents/skills/ccba-code-review/references/unslop_checklist.md
  - docs/rules/code_quality.md
output_path: ".md/peer_exchange/grok_signoff_pstack_phase3.md"
target_files:
  - .agents/skills/ccba-create-verification-skill/SKILL.md
  - .agents/skills/ccba-create-verification-skill/references/maintain_drift_guide.md
  - .agents/skills/ccba-grilling/SKILL.md
  - .agents/skills/ccba-handoff/SKILL.md
  - .agents/skills/ccba-code-review/references/unslop_checklist.md
  - docs/rules/code_quality.md
---

# 🎯 Yêu Cầu Ký Duyệt Sau Triển Khai (Pass 2 Sign-Off): Pstack Phase 3 (Zero Skill Bloat)

> ⚠️ **Chỉ Dẫn Quan Trọng Cho Grok (`signoff_diff --no-tools`)**: Toàn bộ diff nguyên văn của 6 tệp mục tiêu và kết quả chạy kiểm chuẩn tự động (`verify-patch` mã thoát `0`) đã được đính kèm bên dưới. Hãy đối soát việc thực thi 4 điều kiện (`COND-01` $\to$ `COND-04`) từ phiên Pass 1 (`bfc636a9-66fa-44fe-ae07-1a70c19ff39b`) và trả về khối YAML frontmatter `PeerVerdictBlock` (`verdict: FINAL_ACCEPT | APPROVE`, `risk_score: 1`, `conditions: []`).

---

## 1. Bảng Đối Soát Thực Thi 4 Điều Kiện Chặn Từ Pass 1 (`COND-01` → `COND-04`)

| Mã ĐK | Nội dung yêu cầu từ Grok (Pass 1) | Thực thi cụ thể trong Diff | Trạng thái |
| :--- | :--- | :--- | :---: |
| **`COND-01`** | Quy trình hoàn nguyên tất định cho Scratch Mutation Proof (`git diff --quiet` tiền kiểm $\to$ `git checkout -- <mutated_files>` $\to$ hậu kiểm sạch). | Đã bổ sung tại Bước 5 Mode 1 & Mode 2 của `ccba-create-verification-skill/SKILL.md` và Mục 1.1 của `maintain_drift_guide.md` (sử dụng `git diff --quiet <mutated_files> && git diff --cached --quiet <mutated_files>` tương thích đa nền tảng Windows/POSIX, không dùng bashism `$(...)`). | ✅ Hoàn tất |
| **`COND-02`** | Xác định rõ đột biến là **Semantic Mutation** (tác động logic hợp đồng/giá trị biên, cấm syntax error/`raise` thô) và lưu vết *counterexample failure log*. | Đã quy định tường minh trong `ccba-create-verification-skill/SKILL.md`, `maintain_drift_guide.md` (Mục 1.1) và `unslop_checklist.md` (Mục 6). | ✅ Hoàn tất |
| **`COND-03`** | Gắn kết định nghĩa *Observable Behavior* (khoản 10.4) và tín hiệu giám sát thường trực (khoản 17.5) trực tiếp với các bất biến tiêu chuẩn tại Mục 12 `docs/rules/code_quality.md`. | Đã tích hợp trực tiếp tham chiếu và ràng buộc Mục 12 vào khoản 10.4 (*Two-Edit Behavioral Test Litmus*) và khoản 17.5 (*Post-Forensic Cheap Always-On Signal*) trong `docs/rules/code_quality.md` và `unslop_checklist.md`. | ✅ Hoàn tất |
| **`COND-04`** | Bảo toàn khối `## 🏛️ Platform-Aware Architecture Posture`, dòng `Tiêu chí hoàn thành:` và liên kết tương đối chuẩn `RULE-3.5`. | Đã bảo toàn 100%; vượt qua toàn bộ `validate_skills.py --enforce-gpi`, `audit_skills_hygiene.py`, `compile_catalog.py --check`, `sync_hub_adr_matrix.py --check` và `verify-doc` với mã thoát `0`. | ✅ Hoàn tất |

---

## 2. Bằng Chứng Kiểm Định Tự Động (`[đo thực tế]`)

- `.venv/bin/python -m ccba_harness verify-patch --preset skill --target .agents/skills/ccba-create-verification-skill/SKILL.md` $\to$ **PASS (3/3 commands, 891.0 ms)**
- `.venv/bin/python -m ccba_harness verify-patch --preset skill --target .agents/skills/ccba-grilling/SKILL.md` $\to$ **PASS (3/3 commands, 916.0 ms)**
- `.venv/bin/python -m ccba_harness verify-patch --preset skill --target .agents/skills/ccba-handoff/SKILL.md` $\to$ **PASS (3/3 commands, 906.4 ms)**
- `.venv/bin/python -m ccba_harness verify-patch --preset skill --target .agents/skills/ccba-code-review/SKILL.md` $\to$ **PASS (3/3 commands, 930.9 ms)**
- `.venv/bin/python -m ccba_harness verify-patch --preset doc --target docs/rules/code_quality.md` $\to$ **PASS (393.5 ms)**
- `.venv/bin/python -m ccba_harness verify-patch --preset doc --target .agents/skills/ccba-create-verification-skill/references/maintain_drift_guide.md` $\to$ **PASS (394.2 ms)**
- `.venv/bin/python -m ccba_harness verify-patch --preset doc --target .agents/skills/ccba-code-review/references/unslop_checklist.md` $\to$ **PASS (426.3 ms)**

---

## 3. Toàn Văn `git diff` Thực Tế Trên 6 Tệp Mục Tiêu

```diff
diff --git a/.agents/skills/ccba-code-review/references/unslop_checklist.md b/.agents/skills/ccba-code-review/references/unslop_checklist.md
index 4f46fa46..cf71e064 100644
--- a/.agents/skills/ccba-code-review/references/unslop_checklist.md
+++ b/.agents/skills/ccba-code-review/references/unslop_checklist.md
@@ -40,10 +40,14 @@ Tài liệu này cung cấp checklist chuyên biệt để nhận diện và lo
 
 ---
 
-## 6. Hypothesis-Driven Forensic Checklist (Figure-It-Out Discipline)
+## 6. Hypothesis-Driven Forensic & Behavioral Verification Checklist (Pstack Phase 2 & 3)
 - [ ] **Xác lập Completion Predicate & Non-Goals**: Nhiệm vụ phức tạp/mơ hồ có định nghĩa rõ tiêu chí hoàn thành đo lường được và danh sách non-goals không?
 - [ ] **Phân tách vùng mù 4 nhóm**: Đã tự giải quyết Factual Questions bằng công cụ khảo sát codebase trước khi hỏi người dùng?
 - [ ] **Giới hạn thử nghiệm (COND-02)**: Các nhánh giả thuyết thực nghiệm (Empirical Forks) có tuân thủ giới hạn tối đa 3 lần thử-sai không?
 - [ ] **Khắc sâu bài test thường trực (COND-04)**: Minimal Reproducer đã được chuẩn hóa thành test case chính thức trong `tests/` hoặc `harness/` thay vì bị xóa bỏ không?
 - [ ] **Bằng chứng runtime thực tế**: Mọi khẳng định hoàn thành đều có bằng chứng lệnh thực thi (exit code 0), không dựa trên giả định phỏng đoán.
+- [ ] **Two-Edit Behavioral Test Litmus (Pstack v0.15.25 & COND-03)**: Bài test mới có đảm bảo FAIL khi phá vỡ hành vi quan sát được (*Break the behavior* theo hợp đồng/Mục 12 `code_quality.md`) và vẫn PASS khi chỉ tái cấu trúc nội bộ (*Change the internals*) không?
+- [ ] **Cheap Always-On Signal (Pstack v0.15.22 & COND-03)**: Nếu PR sửa một lỗi phải đào sâu mới tìm ra dữ kiện quyết định, đã bổ sung invariant assertion hoặc structured log nhẹ (kèm mã định danh quy chuẩn/điều khoản nếu có) để lần sau phát hiện ngay ở cái nhìn đầu tiên chưa?
+- [ ] **Semantic Mutation Proof & `sync_commit` (Pstack v0.15.28 & COND-01/02)**: Khi khởi tạo hoặc bảo trì `verify-<app>`, đã kiểm chứng bằng đột biến ngữ nghĩa an toàn (kiểm tra `git diff` sạch trước/sau, thu thập counterexample failure log) và cập nhật `sync_commit` chuẩn xác chưa?
+
 
diff --git a/.agents/skills/ccba-create-verification-skill/SKILL.md b/.agents/skills/ccba-create-verification-skill/SKILL.md
index 48428625..6f3881a5 100644
--- a/.agents/skills/ccba-create-verification-skill/SKILL.md
+++ b/.agents/skills/ccba-create-verification-skill/SKILL.md
@@ -22,7 +22,7 @@ keywords:
 argument-hint: '[--app APP_NAME | --mode {scaffold,maintain} | --type {web,api,cli,worker}]'
 metadata:
   author: CCBA
-  version: 1.1.0
+  version: 1.2.0
 disable-model-invocation: true
 bundle: _core
 tier: kernel
@@ -134,21 +134,24 @@ Kỹ năng tự động xác định chế độ vận hành dựa trên hiện
    - Tạo thư mục `.agents/skills/verify-<app>/`.
    - Tạo thư mục con `.agents/skills/verify-<app>/harness/` chứa các kịch bản thực thi.
    - **Tiêu chí hoàn thành:** Thư mục `.agents/skills/verify-<app>/harness/` được tạo thành công trên hệ thống tệp.
-3. **Sinh Tệp Định Nghĩa Kỹ Năng (`verify-<app>/SKILL.md`):**
+3. **Sinh Tệp Định Nghĩa Kỹ Năng (`verify-<app>/SKILL.md`) & Neo Phiên Bản (`sync_commit`):**
    - Định nghĩa frontmatter chuẩn (`name: verify-<app>`, `category: verification`, v.v.).
+   - Ghi nhận rõ trường `sync_commit` (mã commit SHA tại thời điểm xác nhận bộ kiểm định khớp 100% với mã nguồn) và danh mục `covered_paths` (các tệp/hàm cốt lõi được bộ kiểm định bảo vệ).
    - Hướng dẫn các bước chạy kiểm định và đối chiếu trạng thái theo 5 khối cấu trúc.
-   - **Tiêu chí hoàn thành:** Tệp `.agents/skills/verify-<app>/SKILL.md` được sinh ra với đầy đủ frontmatter và quy trình 5 khối.
+   - **Tiêu chí hoàn thành:** Tệp `.agents/skills/verify-<app>/SKILL.md` được sinh ra với đầy đủ frontmatter, quy trình 5 khối, trường `sync_commit` và `covered_paths`.
 4. **Khởi Tạo Features Map (`features/INDEX.md`):**
    - Lập danh mục các tính năng hiện có của ứng dụng theo chuẩn `features_map_guide.md`.
    - **Tiêu chí hoàn thành:** Tệp `features/INDEX.md` được khởi tạo với bảng ánh xạ các tính năng chính và bài kiểm thử tương ứng.
-5. **Chạy Thử Nghiệm Xác Minh (Dry-Run Verification):**
-   - Thực thi thử kịch bản harness để xác nhận hệ thống có thể khởi động, chạy probe, và dọn dẹp sạch sẽ với exit code 0.
-   - **Tiêu chí hoàn thành:** Kịch bản harness thực thi dry-run thành công và thoát với mã exit code 0.
+5. **Chạy Thử Nghiệm Xác Minh & Phép Thử Đột Biến Ngữ Nghĩa (Semantic Mutation Proof — COND-01, COND-02):**
+   - Xác nhận cây làm việc sạch tuyệt đối (`git diff --quiet && git diff --cached --quiet`) trước khi thử nghiệm.
+   - Thực hiện 1 phép thử **Đột Biến Ngữ Nghĩa (Semantic Mutation)** tạm thời trên mã nguồn (ví dụ: đảo toán tử so sánh biên `>` $\to$ `>=`, đảo ngược cờ boolean, hoặc bỏ qua bước cập nhật trạng thái; tuyệt đối cấm chèn lỗi cú pháp thô hay lệnh `raise` ở đầu hàm), chạy `verify-<app>` để chứng minh bộ kiểm định bắt được lỗi và lưu lại nhật ký lỗi phản chứng (*counterexample failure log*).
+   - Hoàn nguyên tự động (`git checkout -- <mutated_files>`), kiểm tra `git status --porcelain` rỗng, và chạy lại kịch bản harness xác nhận thoát sạch với exit code 0.
+   - **Tiêu chí hoàn thành:** Bộ kiểm định bắt được lỗi đột biến ngữ nghĩa (có counterexample log), mã nguồn được hoàn nguyên 100% sạch sẽ và lần chạy chính thức thoát với mã exit code 0.
 
 ### Mode 2 — Bảo Trì & Sửa Sai Lệch Drift (`maintain`)
-1. **Kiểm Tra Nguồn Gốc Thay Đổi (Pre-Remediation Provenance Check - COND-01):**
-   - Đối chiếu commit history hoặc tài liệu API: nếu thay đổi là chủ đích thiết kế (đổi route, port, schema) $\rightarrow$ sửa `harness/`; nếu là lỗi hồi quy ngoài ý muốn (regression) $\rightarrow$ **CẤM SỬA `harness/`**, giữ nguyên bài test và yêu cầu sửa mã nguồn ứng dụng.
-   - **Tiêu chí hoàn thành:** Phân loại chính xác nguyên nhân lỗi thuộc diện Lệch Hợp Đồng (Contract Drift) hay Lỗi Hồi Quy (Regression).
+1. **Kiểm Tra Nguồn Gốc Thay Đổi & Lịch Sử Từ `sync_commit` (Pre-Remediation Provenance Check - COND-01):**
+   - Đối chiếu `git diff <sync_commit>..HEAD` trên các tệp thuộc `covered_paths`: nếu thay đổi là chủ đích thiết kế (đổi route, port, schema có bằng chứng trong PR/commit/ADR) $\rightarrow$ sửa `harness/` (trạng thái `updated`); nếu là lỗi hồi quy ngoài ý muốn (regression) $\rightarrow$ **CẤM SỬA `harness/`**, gán trạng thái `bug`, giữ nguyên bài test và yêu cầu sửa mã nguồn ứng dụng.
+   - **Tiêu chí hoàn thành:** Phân loại chính xác nguyên nhân lỗi thuộc 1 trong 4 trạng thái chuẩn (`in_sync`, `updated`, `bug`, `blocked`) theo `references/maintain_drift_guide.md`.
 2. **Đối Chiếu Bề Mặt Tính Năng (Surface Diff):**
    - So sánh các route/command hiện hành với tài liệu `features/INDEX.md` để khoanh vùng điểm lệch.
    - **Tiêu chí hoàn thành:** Xác định danh sách các điểm trôi lệch giữa code và tài liệu.
@@ -158,9 +161,10 @@ Kỹ năng tự động xác định chế độ vận hành dựa trên hiện
 4. **Khắc Phục Tận Gốc Trong Thư Mục `harness/`:**
    - Cập nhật lệnh CLI, port, timeout, probe URL hoặc schema assertions bên trong `.agents/skills/verify-<app>/harness/`. Tuyệt đối không tạo file rác tại thư mục gốc `scripts/` (ADR-0044).
    - **Tiêu chí hoàn thành:** Kịch bản trong `harness/` và `features/INDEX.md` được cập nhật đồng bộ.
-5. **Xác Minh Thoát Sạch Tuyệt Đối (Clean Exit Verification):**
-   - Chạy lại bài kiểm định, bảo đảm đạt exit code 0 và tiêu diệt sạch toàn bộ cây tiến trình con.
-   - **Tiêu chí hoàn thành:** Toàn bộ harness chạy thành công với exit code 0, không còn tiến trình zombie.
+5. **Kiểm Chứng Đột Biến Ngữ Nghĩa, Cập Nhật `sync_commit` & Xác Minh Thoát Sạch (COND-01, COND-02):**
+   - Khi cập nhật harness (`updated`), bắt buộc thực hiện phép thử **Semantic Mutation Proof** (xác nhận `git diff` sạch $\to$ tiêm đột biến ngữ nghĩa trên nhánh mã mới để chứng minh harness mới không bị mất khả năng bắt lỗi $\to$ `git checkout -- <mutated_files>` và xác nhận `git status --porcelain` rỗng).
+   - Chỉ tiến hành nâng `sync_commit` lên commit hiện tại khi đạt kết quả `in_sync` hoặc `updated` và bài kiểm định thoát với exit code 0. Tuyệt đối CẤM nâng `sync_commit` khi kết quả là `bug` hoặc `blocked`.
+   - **Tiêu chí hoàn thành:** Harness vượt qua Semantic Mutation Proof, thoát sạch với exit code 0, không còn tiến trình zombie và `sync_commit` được cập nhật chuẩn xác.
 
 ---
 
@@ -169,7 +173,7 @@ Kỹ năng tự động xác định chế độ vận hành dựa trên hiện
 | Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
 | :--- | :--- |
 | `references/features_map_guide.md` | Hướng dẫn thiết lập và duy trì Features Map (`features/INDEX.md`) cho ứng dụng |
-| `references/maintain_drift_guide.md` | Hướng dẫn phát hiện & khắc phục 4 dạng drift kiểm định, chống test tampering và bảo vệ Spoke cleanliness |
+| `references/maintain_drift_guide.md` | Hướng dẫn phát hiện & khắc phục 4 dạng drift kiểm định, ma trận 4 trạng thái (`in_sync`, `updated`, `bug`, `blocked`), Semantic Mutation Proof và bảo vệ Spoke cleanliness |
 
 ---
 
diff --git a/.agents/skills/ccba-create-verification-skill/references/maintain_drift_guide.md b/.agents/skills/ccba-create-verification-skill/references/maintain_drift_guide.md
index 8c9df1d7..65d02943 100644
--- a/.agents/skills/ccba-create-verification-skill/references/maintain_drift_guide.md
+++ b/.agents/skills/ccba-create-verification-skill/references/maintain_drift_guide.md
@@ -26,6 +26,28 @@ flowchart TD
    - Ứng dụng bị crash, trả về mã 500, đứt gãy kết nối cơ sở dữ liệu, hoặc logic nghiệp vụ trả về kết quả sai do commit mã mới.
    - **Hành động:** **CẤM SỬA `harness/`**. Giữ nguyên bài test, phân tích nguyên nhân gốc (Root Cause) và yêu cầu sửa mã nguồn ứng dụng để phục hồi tính tương thích.
 
+### 1.1. Bốn Trạng Thái Kết Quả Bảo Trì (`in_sync`, `updated`, `bug`, `blocked`) & Chốt Chặn `sync_commit` + Semantic Mutation Proof (Pstack v0.15.28)
+
+Khi mã nguồn thay đổi mà bộ kiểm định không cập nhật, bài kiểm thử có thể tiếp tục trả về PASS giả tạo vì chỉ kiểm tra mô tả cũ đã lỗi thời (**Pass on Stale Description**). Để triệt tiêu rủi ro này, mỗi lượt chạy bảo trì bắt buộc phân loại kết quả vào đúng 1 trong 4 trạng thái chuẩn:
+
+1. **`in_sync`**: Không có thay đổi nào từ `sync_commit` đến `HEAD` làm thay đổi hành vi/hợp đồng mà bộ kiểm định mô tả, và bài kiểm định PASS. Được phép nâng `sync_commit` lên commit hiện tại.
+2. **`updated`**: Mã nguồn thay đổi có chủ đích (có bằng chứng trong commit message, docstring, PR hoặc ADR), kịch bản trong `harness/` đã được cập nhật từ chính mã nguồn mới, vượt qua **Semantic Mutation Proof** và PASS. Được phép nâng `sync_commit`.
+3. **`bug`**: Bộ kiểm định phản ánh đúng hợp đồng hiện hành nhưng mã nguồn vi phạm tính chất cam kết. Tuyệt đối CẤM làm yếu bài kiểm định hoặc nâng `sync_commit`; báo cáo chuỗi bước tái lập lỗi (*counterexample*) và commit gây lỗi.
+4. **`blocked`**: Không thể thực thi hoặc đồng bộ bộ kiểm định do rào cản môi trường/hạ tầng. Nêu rõ nguyên nhân và **tuyệt đối CẤM dịch chuyển `sync_commit`**.
+
+#### Quy Trình Hoàn Nguyên Tất Định Cho Semantic Mutation Proof (`COND-01` & `COND-02`)
+Để chứng minh bộ kiểm định mới hoặc vừa cập nhật (`updated`) thực sự có khả năng bắt lỗi mà không làm ô nhiễm cây mã nguồn:
+1. **Tiền kiểm trạng thái sạch (`COND-01`)**: Chỉ thực hiện đột biến khi working tree hoàn toàn sạch:
+   ```bash
+   git diff --quiet && git diff --cached --quiet
+   ```
+2. **Đột biến ngữ nghĩa & Thu thập phản chứng (`COND-02`)**: Thực hiện một **đột biến ngữ nghĩa (Semantic Mutation)** tác động trực tiếp vào logic hợp đồng, điều kiện rẽ nhánh hoặc giá trị biên trên mã nguồn thực (ví dụ: đổi toán tử `>` thành `>=`, đảo ngược cờ boolean, hoặc bỏ qua một bước ghi trạng thái; **tuyệt đối cấm** chèn lỗi cú pháp `SyntaxError` hoặc đặt lệnh `raise` thô ở đầu hàm). Chạy `verify-<app>` và lưu lại nhật ký lỗi phản chứng (*counterexample failure log*) để chứng minh bộ kiểm định bắt trúng lỗi.
+3. **Hoàn nguyên tự động & Hậu kiểm nguyên vẹn (`COND-01`)**: Ngay sau khi thu thập phản chứng, phục hồi mã nguồn và xác nhận trạng thái sạch trước khi nghiệm thu:
+   ```bash
+   git checkout -- <mutated_files>
+   git diff --quiet <mutated_files> && git diff --cached --quiet <mutated_files>
+   ```
+
 ---
 
 ## 2. Bốn Dạng Drift Phổ Biến & Quy Trình Khắc Phục
@@ -66,4 +88,4 @@ Khi bảo trì và sửa lỗi cho kỹ năng `verify-<app>` tại Spoke reposit
 
 ---
 
-*Tài liệu tham chiếu thuộc bộ chuẩn mực Pstack Phase 2 — CCBA Agent Services Platform.*
+*Tài liệu tham chiếu thuộc bộ chuẩn mực Pstack Phase 2 & Phase 3 — CCBA Agent Services Platform.*
diff --git a/.agents/skills/ccba-grilling/SKILL.md b/.agents/skills/ccba-grilling/SKILL.md
index 78466cdb..42164c14 100644
--- a/.agents/skills/ccba-grilling/SKILL.md
+++ b/.agents/skills/ccba-grilling/SKILL.md
@@ -23,7 +23,7 @@ disable-model-invocation: true
 bundle: _software
 tier: kernel
 metadata:
-  version: "1.0.0"
+  version: "1.1.0"
   author: "CCBA Hub"
 triggers:
 - grill
@@ -52,12 +52,20 @@ Kỹ năng này bắt buộc Agent phải chạy một vòng lặp phỏng vấn
 - **Seam Capability Posture**: `seam-exempt`. Kỹ năng này là SOP Kernel chuyên trách điều phối vòng lặp phỏng vấn Socrates dồn dập (Grilling Loop) qua 3 nhánh tác nghiệp: Nhánh A (Standard Stress-Test phỏng vấn thiết kế), Nhánh B (Rule Compliance Stress-Test đối soát quy chuẩn) và Nhánh C (Visual Prototype Grilling hội tụ UI). Danh mục Seam chuẩn hóa của Platform không quản lý logic tương tác phỏng vấn người dùng, do đó kỹ năng được miễn trừ trực tiếp (seam-exempt) để vận hành độc lập.
 - **Governance Compliance**: Đạt chuẩn Governance ADR-0057 Tier 2B Standalone Kernel Skill với điểm GPI (S: 4.0, K: 2.0, A: 1.0, P: 1.0) = 14.5 >= 12.0. Tệp tài liệu chuyên sâu duy nhất `references/workflow_looping.md` được bảo tồn nguyên vẹn tại chỉ mục Level 3.
 
+## Bước 0: Tiền Khởi Động — Diễn Đạt Lại Mục Tiêu & Mài Sắc Bài Toán (`in-your-own-words` & `sharpen` — Pstack v0.15.27)
+
+Trước khi bắt đầu đặt câu hỏi ở bất kỳ nhánh Grilling nào (A, B, hoặc C), Agent **BẮT BUỘC** thực hiện bước định hình ngắn gọn:
+1. **Diễn đạt lại mục tiêu (`in-your-own-words`):** Phát biểu lại trong 2–3 câu bằng ngôn ngữ của chính Agent về mục tiêu thực sự và bài toán cốt lõi mà người dùng đang muốn giải quyết.
+2. **Mài sắc theo chuẩn chuyên gia (`sharpen`):** Tự xác định cách một chuyên gia đầu ngành sẽ tiếp cận tác vụ này: sử dụng nguồn dữ liệu gốc nào (*raw sources*), phương pháp thực chất nào (*real methods*), và duy trì ít nhất **1 cơ chế kiểm chứng độc lập bên ngoài (*outside check*)** để chứng minh kết quả đúng.
+3. **Cân bằng mức độ đặc tả:** Chủ động đề xuất tháo bỏ các ràng buộc quá chi tiết nhưng không phục vụ mục tiêu (*over-specification*) song song với việc bổ sung các ràng buộc còn thiếu (*under-specification*), giữ nguyên các lựa chọn thuộc thẩm quyền của người dùng.
+   - **Tiêu chí hoàn thành:** Tóm tắt rõ 2–3 câu mục tiêu thực chất, xác định được 1 cơ chế kiểm chứng độc lập bên ngoài (*outside check*) và ranh giới đặc tả trước khi mở câu hỏi Frontier đầu tiên.
+
 ## Các Chế độ chạy (Branches)
 
 ### Nhánh A: Standard Stress-Test (Phỏng vấn Thiết kế)
 Sử dụng khi người dùng muốn rà quét điểm mù logic thiết kế, cấu trúc file, sự đánh đổi kỹ thuật.
 *   **Quy trình:**
-    1. Đọc kỹ kế hoạch/thiết kế hiện tại.
+    1. Đọc kỹ kế hoạch/thiết kế hiện tại và thực hiện **Bước 0 (Tiền Khởi Động)**.
     2. Đưa ra các câu hỏi stress-test xoay quanh: sự đánh đổi (trade-offs), độ phức tạp (complexity), khả năng mở rộng (scalability), và các giả định chưa được kiểm chứng.
     3. Đặt từng câu hỏi một (one-by-one), chờ người dùng trả lời xong mới chuyển sang câu tiếp theo. **Tuyệt đối không in ra danh sách nhiều câu hỏi cùng lúc.**
     4. Đối với mỗi câu hỏi, Agent phải đưa ra phương án đề xuất của mình trước (recommended answer) làm cơ sở tham chiếu.
diff --git a/.agents/skills/ccba-handoff/SKILL.md b/.agents/skills/ccba-handoff/SKILL.md
index 56b99c72..162947a7 100644
--- a/.agents/skills/ccba-handoff/SKILL.md
+++ b/.agents/skills/ccba-handoff/SKILL.md
@@ -8,7 +8,7 @@ tier: kernel
 disable-model-invocation: true
 metadata:
   author: CCBA
-  version: 2.0.0
+  version: 2.1.0
 user-invocable: true
 command: /ccba-handoff
 gpi:
@@ -38,7 +38,7 @@ Mục tiêu tối thượng là giúp **Agent ở phiên làm việc tiếp theo
 ## 📋 Tiêu Chí Hoàn Thành (Completion Criteria)
 - [x] Tạo thành công tệp bàn giao tại: `.md/scratch/handoffs/handoff-<YYYY-MM-DD-HHMMSS>.md`.
 - [x] Thư mục `.md/scratch/` đã được cấu hình trong `.gitignore` (không đẩy dữ liệu nháp lên remote).
-- [x] Tài liệu tuân thủ đầy đủ **Cấu trúc 5 Phần Tiêu chuẩn CCBA**.
+- [x] Tài liệu tuân thủ đầy đủ **Cấu trúc 5 Phần Tiêu chuẩn CCBA** và chuẩn **Decision-Decidable Catch-up (Pstack v0.15.27)**.
 - [x] Đã che giấu (redact) 100% API keys, tokens, mật khẩu qua chuẩn Maskara.
 
 ---
@@ -57,8 +57,13 @@ Tài liệu bàn giao bắt buộc phải tuân theo cấu trúc sau:
 
 ---
 
-## 1. Outstanding User Requests (Nhiệm vụ còn dang dở & Yêu cầu người dùng)
-- **Danh sách yêu cầu mở:** Liệt kê theo thứ tự ưu tiên (P1, P2, P3).
+## 1. Outstanding User Requests & Decision-Decidable Calls (Nhiệm vụ mở & Quyết định chờ duyệt)
+- **Danh sách quyết định đang chờ người dùng (`riskiest first`):** Liệt kê đầy đủ 100% các mục cần người dùng phê duyệt/lựa chọn (tuyệt đối không cắt bớt vì giới hạn từ), sắp xếp từ rủi ro cao nhất xuống thấp nhất. Mỗi mục (~30 từ) gồm đủ 5 thành tố:
+  1. **Call Required:** Quyết định cần người dùng chốt (merge, approve, chọn phương án).
+  2. **Recommended Pick:** Phương án Agent khuyến nghị thực hiện đầu tiên.
+  3. **User-Visible Impact:** Thay đổi thực tế đối với người dùng/hệ thống.
+  4. **Evidence:** Bằng chứng thực nghiệm hoặc kết quả kiểm thử hậu thuẫn.
+  5. **Risk:** Mức độ rủi ro cụ thể (ghi rõ cả khi rủi ro thấp).
 - **Phân loại giai đoạn:** PLANNING / IMPLEMENTATION / VERIFICATION / REVIEW.
 - **Ngữ cảnh bổ sung:** Trích dẫn nguyên văn câu lệnh hoặc định hướng của người dùng.
 
@@ -90,7 +95,9 @@ Tài liệu bàn giao bắt buộc phải tuân theo cấu trúc sau:
 
 ---
 
-## 🔒 Quy Tắc An Toàn & Bảo Mật
+## 🔒 Quy Tắc An Toàn, Trình Bày & Bảo Mật
 1. **Không trùng lặp tài liệu tĩnh:** Không sao chép lại toàn bộ nội dung của các file spec, ADR hay kế hoạch lớn; thay vào đó hãy sử dụng liên kết Markdown dẫn tới file đó.
 2. **Khử lộ lọt dữ liệu:** Tuyệt đối không lưu API Key, bí mật hay thông tin nhạy cảm vào file handoff.
 3. **Cá nhân hóa theo tham số:** Nếu người dùng truyền thêm tham số (argument) khi gọi lệnh (ví dụ: `/ccba-handoff chuẩn bị seminar PCCC`), hãy tập trung phần `Immediate Next Steps` vào đúng chủ đề đó.
+4. **Quy tắc sơ đồ trực quan tinh gọn (Compact Visuals — `/ketchup` Discipline Pstack v0.15.27):** Khi minh họa kiến trúc, luồng thay đổi hoặc chuỗi phụ thuộc PR bằng sơ đồ Mermaid, giới hạn tối đa $\le 6$ khối (nodes) và $\le 8$ từ trong mỗi khối bằng ngôn ngữ tự nhiên ngắn gọn, không vẽ sơ đồ cho danh sách trạng thái đơn thuần và không lặp lại thông tin đã viết trong văn bản.
+   - **Tiêu chí hoàn thành:** Tài liệu bàn giao liệt kê đầy đủ 100% các quyết định chờ người dùng theo 5 thành tố chuẩn (`riskiest first`), sơ đồ Mermaid (nếu có) tuân thủ giới hạn $\le 6$ khối / $\le 8$ từ mỗi khối, và vượt qua kiểm chuẩn bảo mật Maskara.
diff --git a/docs/rules/code_quality.md b/docs/rules/code_quality.md
index 40c969aa..5dff7b0c 100644
--- a/docs/rules/code_quality.md
+++ b/docs/rules/code_quality.md
@@ -143,6 +143,11 @@ Khi viết unit tests cho các cơ chế kiểm định phòng vệ (Guardrails,
      - Trường hợp có thẻ ngoại lệ hợp lệ $\rightarrow$ Phải tha bổng thành công (`assert len(violations) == 0`).
 3. **Bao phủ toàn diện các ký tự phân cách (Separator Coverage):**
    - Bộ test cho parser/regex ranh giới bắt buộc phải kiểm thử độc lập cả 3 họ phân cách: phân cấp số thập phân (`.1`), hậu tố gạch nối (`-bis`, `-sub`), và gạch chéo (`/2`).
+4. **Phép thử hai biến đổi hành vi (Two-Edit Behavioral Test Litmus — Pstack v0.15.25 & COND-03):**
+   - **Hành vi quan sát được (Observable Behavior)** được định nghĩa gắn kết trực tiếp với các bất biến tiêu chuẩn tại Mục 12: bao gồm giá trị trả về, giới hạn quy chuẩn/tiêu chuẩn, lỗi chuẩn hóa mà caller phân nhánh xử lý, trạng thái đọc lại được qua giao diện công khai, và hiệu ứng phụ (side-effects) lên hệ thống ngoài.
+   - Mọi bài unit/integration test phải vượt qua đồng thời 2 phép biến đổi giả định:
+     - **Phá vỡ hành vi (Break the behavior):** Giả sử làm sai lệch kết quả trả về, vi phạm ngưỡng tiêu chuẩn (Mục 12), bỏ qua một side-effect hoặc gọi trùng lặp $\rightarrow$ nếu bài test vẫn PASS, bài test đó vô giá trị (thường do assertion quá lỏng như `is not None`, hoặc tự tính expected value bằng chính hàm đang test). Bắt buộc viết lại hoặc xóa bỏ.
+     - **Thay đổi cấu trúc nội bộ (Change the internals):** Giữ nguyên 100% hành vi quan sát được và tính tuân thủ quy chuẩn nhưng đổi tên hàm helper nội bộ hoặc thứ tự gọi private $\rightarrow$ nếu bài test FAIL, bài test đang bị ghim cứng vào implementation thay vì contract.
 
 ---
 
@@ -240,5 +245,8 @@ Quy chuẩn xử lý bài toán kỹ thuật phức tạp, di chuyển kiến tr
    - **Bắt buộc lưu vết thường trực (Reproducer Codification):** Mọi Minimal Reproducer sau khi chứng minh và sửa lỗi thành công BẮT BUỘC phải được chuẩn hóa thành test case chính thức trong `tests/` hoặc bài kiểm tra trong `harness/`, tuyệt đối không xóa bỏ dưới dạng script rác tạm thời.
 4. **Runtime Evidence over Proxy Assumptions (Bằng Chứng Thực Tế Thay Vì Giả Định Ảo):**
    - Tuyệt đối CẤM kết luận "code nhìn có vẻ đúng" hoặc "lý thuyết đã khớp". Mọi nghiệm thu bắt buộc phải kèm theo bằng chứng runtime thực tế (kết quả chạy lệnh, stdout/stderr, mã thoát 0 từ `ccba-harness verify-patch`).
+5. **Post-Forensic Cheap Always-On Signal (Tín Hiệu Giám Sát Thường Trực Sau Điều Tra Sâu — Pstack v0.15.22 & COND-03):**
+   - Khi một ca chẩn đoán lỗi đòi hỏi phải đào sâu qua nhiều tầng dữ liệu mới tìm ra dữ kiện quyết định (*deciding fact*), sau khi khắc phục nguyên nhân gốc, Agent bắt buộc phải bổ sung hoặc đề xuất một **tín hiệu giám sát rẻ, luôn bật (cheap always-on signal)** — như một trường dữ liệu trong structured log, một kiểm tra bất biến (invariant assertion) nhẹ mang mã định danh điều khoản/quy chuẩn liên quan (theo Mục 12), hoặc một chỉ báo trong readiness probe — để nếu lỗi tương tự tái diễn, nguyên nhân sẽ lộ diện ngay ở cái nhìn đầu tiên mà không làm suy giảm hiệu năng hệ thống.
+
 
 
```
