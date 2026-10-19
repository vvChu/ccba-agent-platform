---
request_id: "req-20261019-plan-pstack-phase3-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "review"
profile: "audit_direct"
subject: "Thẩm định Kế hoạch Triển khai Pstack Phase 3 (v0.15.20 -> v0.15.27/28 — Zero Skill Bloat)"
timestamp: "2026-10-19T15:43:30+07:00"
source_documents:
  - .agents/skills/ccba-create-verification-skill/SKILL.md
  - .agents/skills/ccba-create-verification-skill/references/maintain_drift_guide.md
  - .agents/skills/ccba-grilling/SKILL.md
  - .agents/skills/ccba-handoff/SKILL.md
  - .agents/skills/ccba-code-review/references/unslop_checklist.md
  - docs/rules/code_quality.md
output_path: ".md/peer_exchange/grok_review_plan_pstack_phase3.md"
target_files:
  - .agents/skills/ccba-create-verification-skill/SKILL.md
  - .agents/skills/ccba-create-verification-skill/references/maintain_drift_guide.md
  - .agents/skills/ccba-grilling/SKILL.md
  - .agents/skills/ccba-handoff/SKILL.md
  - .agents/skills/ccba-code-review/references/unslop_checklist.md
  - docs/rules/code_quality.md
---

# 🎯 Yêu Cầu Phản Biện Đối Kháng (Pass 1 Plan Review): Kế Hoạch Triển Khai Pstack Phase 3 (v0.15.20 → v0.15.27/28 — Zero Skill Bloat)

> ⚠️ **Chỉ Dẫn Quan Trọng Cho Grok (`audit_direct --no-tools`)**: Toàn bộ nội dung thiết kế kỹ thuật, ngữ cảnh lịch sử Pstack Phase 1 & Phase 2, cùng nội dung nguyên văn các đoạn liên quan trong 6 tệp mục tiêu đã được đính kèm đầy đủ 100% trong prompt này. Hãy tập trung thẩm tra đối kháng (adversarial review) thiết kế bên dưới và trả về báo cáo kèm khối `PeerVerdictBlock` (YAML frontmatter chuẩn với `verdict: APPROVE_PLAN | REVISE_PLAN | REJECT_PLAN`, `risk_score: 1..5`, `conditions: [...]`).

---

## 1. Bối Cảnh Thực Chứng (Empirical Context)

Sau khi hoàn tất Pstack Phase 1 (PR `#486` — Anti-Slop, Zero-Noise Comments & `ccba-create-verification-skill`) và Pstack Phase 2 (ngày `2026-10-06` — Verification Drift Maintenance & Hypothesis-Driven Forensic), kho `cursor/plugins/pstack` đã phát hành thêm **32 commits** từ `v0.15.20` đến `v0.15.27` (`0148b78c`) và `v0.15.28` (`d4575673`).

Qua khảo sát trực tiếp cây mã nguồn `cursor/plugins/pstack` (Double-Pass Adversarial Review theo Rule 8):
- Chúng tôi **bác bỏ** việc tạo thêm các micro-skills rời rạc như `/sharpen` (756 bytes), `/in-your-own-words` (315 bytes), `/ketchup` hay tách riêng `create-formal-verification-skill` / `maintain-formal-verification-skill`, vì sẽ làm phình số lượng skills vượt mức 76 skills hiện tại và vi phạm cổng GPI ($\text{GPI} < 12.0$ theo ADR-0057 / `RULE-1.1`).
- Chúng tôi cũng **loại bỏ** các hạng mục đã có tương đương 100% tại CCBA Hub (`check-pstack-docs.mjs` `#704` $\leftrightarrow$ `DriftAuditor` + `validate_docs.py`; subagent effort matching `#613` $\leftrightarrow$ `PROFILE_SPECS` trong `peer.py` theo ADR-0065).
- Thay vào đó, **Kế hoạch Pstack Phase 3 (PA1)** tiếp thu **4 tinh hoa kỹ thuật mới** từ `pstack` v0.15.27/28 trực tiếp vào 4 Kernel Skills hiện hữu (`ccba-create-verification-skill`, `ccba-grilling`, `ccba-handoff`, `ccba-code-review`) và Layer-2 Rules (`docs/rules/code_quality.md`) với **Zero Skill Bloat**:
  1. **Mutation Proof, `sync_commit` Provenance & 4-Outcome Drift Matrix** (từ `/create-formal-verification-skill` `#709/#721` & `/maintain-formal-verification-skill` `#716`).
  2. **Two-Edit Behavioral Test Litmus & Post-Forensic Cheap Always-On Signal** (từ `principle-test-behavior-not-implementation` `#633` & `principle-fix-root-causes` `#604`).
  3. **Pre-Execution Expert Sharpening & Outside Check Gate** (từ `/sharpen` `#615/#712` & `/in-your-own-words` `#602/#606`).
  4. **Decision-Decidable Catch-up & Compact Visuals Protocol** (từ `/ketchup` `#539/#609/#628/#692/#708`).

---

## 2. Toàn Văn Bản Kế Hoạch Kỹ Thuật (Implementation Plan)

### Bằng Chứng Tra Cứu Seam (ADR-0061 Reuse-First Audit Receipt)
```json
{
  "status": "NO_MATCH",
  "index_sha256": "acb01ed09bcc44bd0bfebdcd400db5c4cd6f2f9d678c198a4b9acb8b6601bab0",
  "freshness": "unverified",
  "count": 0,
  "cards": []
}
```

### Thành Phần 1: Chuẩn Mực Kiểm Định & Bảo Trì Drift (`ccba-create-verification-skill`)

#### 1.1. Sửa đổi `.agents/skills/ccba-create-verification-skill/SKILL.md`
- Nâng `metadata.version` từ `1.1.0` $\to$ `1.2.0`.
- Tại **Mode 1 — Khởi Tạo Mới (`scaffold`)**:
  - Bước 3 (*Sinh Tệp Định Nghĩa Kỹ Năng `verify-<app>/SKILL.md`*): Bổ sung yêu cầu ghi nhận trường `sync_commit` (commit SHA tại thời điểm xác nhận bộ kiểm định khớp 100% với mã nguồn) và danh sách tệp/hàm được bảo vệ (`covered_paths`) vào `verify-<app>/SKILL.md`.
  - Bước 5 (*Chạy Thử Nghiệm Xác Minh & Mutation Proof*): Trước khi bàn giao, bắt buộc thực hiện 1 phép thử đột biến tạm thời (**Scratch Mutation Proof** — cố tình làm sai lệch logic/invariant trên mã nguồn hoặc trả về giá trị sai) để chứng minh `verify-<app>` thực sự bắt được lỗi (fail đúng kỳ vọng), sau đó hoàn nguyên mã nguồn về trạng thái sạch và xác nhận pass với exit code 0. Một kỹ năng kiểm định chưa từng chứng minh khả năng bắt lỗi chỉ được coi là bản nháp (draft).
- Tại **Mode 2 — Bảo Trì & Sửa Sai Lệch Drift (`maintain`)**:
  - Bước 1 & Bước 5: Tích hợp phân loại **4 Trạng Thái Kết Quả Bảo Trì (`in_sync`, `updated`, `bug`, `blocked`)**; khi kết quả là `updated`, bắt buộc chạy lại **Mutation Proof** trên nhánh mã mới để chứng minh việc cập nhật harness không làm mất khả năng bắt lỗi (tránh bẫy *Pass on Stale/Weakened Description*); chỉ nâng `sync_commit` khi đạt `in_sync` hoặc `updated`, tuyệt đối cấm nâng `sync_commit` khi `blocked` hoặc `bug`.

#### 1.2. Sửa đổi `.agents/skills/ccba-create-verification-skill/references/maintain_drift_guide.md`
- Bổ sung **Mục 1.1: Bốn Trạng Thái Kết Quả Bảo Trì (`in_sync`, `updated`, `bug`, `blocked`) & Chốt Chặn `sync_commit` + Mutation Proof (Pstack v0.15.28)**:
  - Cảnh báo nguy cơ **"Pass trên mô tả lỗi thời (Pass on Stale Description)"**: Khi mã nguồn thay đổi (tách bước, thêm nhánh rẽ, đổi hàm ghi state) mà bộ kiểm định không cập nhật, bài kiểm thử có thể vẫn trả về PASS giả tạo vì chỉ kiểm tra đường dẫn cũ.
  - Định nghĩa 4 trạng thái đầu ra bắt buộc cho mỗi hạng mục kiểm định:
    1. `in_sync`: Không có thay đổi nào từ `sync_commit` đến `HEAD` làm thay đổi hành vi được mô tả; bài kiểm định PASS.
    2. `updated`: Mã nguồn thay đổi chủ đích (có bằng chứng trong commit message, docstring, PR/ADR), harness/property đã được cập nhật từ chính mã nguồn mới, đã vượt qua **Mutation Proof** (thử làm gãy logic mới $\to$ check bắt được lỗi $\to$ hoàn nguyên) và PASS.
    3. `bug`: Bộ kiểm định phản ánh đúng mã nguồn hiện hành nhưng mã nguồn làm gãy tính chất/hợp đồng. CẤM làm yếu bài kiểm định; giữ nguyên harness, ghi nhận chuỗi bước tái lập lỗi (counterexample) và commit gây lỗi.
    4. `blocked`: Không thể chạy hoặc đồng bộ kiểm định (nêu rõ nguyên nhân, **cấm dịch chuyển `sync_commit`**).

---

### Thành Phần 2: Quy Chuẩn Chất Lượng Mã Nguồn & Rà Soát Code (`code_quality.md` & `unslop_checklist.md`)

#### 2.1. Sửa đổi `docs/rules/code_quality.md`
- Tại **Mục 10 (Behavioral & E2E Test Rigor)**, hiện đang có 3 khoản (`1. Cấm kiểm thử chỉ dựa trên trạng thái nội bộ`, `2. Kiểm chứng độc lập nhánh phủ định (Dual Assertion)`, `3. Bao phủ toàn diện các ký tự phân cách (Separator Coverage)`). Bổ sung khoản **4. Phép Thử Hai Biến Đổi Hành Vi (Two-Edit Behavioral Test Litmus — Pstack v0.15.25)**:
  - Đánh giá mọi bài test qua 2 phép biến đổi giả định đối nghịch:
    - *Break the behavior (Phá vỡ hành vi quan sát được)*: Làm cho hàm trả về sai giá trị, bỏ qua side-effect hoặc thực thi trùng lặp. Nếu bài test vẫn PASS $\to$ bài test vô giá trị (thường do assert quá lỏng như `is not None`, hoặc tự tính expected value bằng chính hàm đang test). Bắt buộc viết lại hoặc xóa bỏ.
    - *Change the internals (Thay đổi cấu trúc nội bộ)*: Giữ nguyên 100% kết quả và side-effect mà caller quan sát được nhưng tái cấu trúc hàm helper nội bộ hoặc thứ tự gọi private. Nếu bài test FAIL $\to$ bài test đang bị ghim cứng vào implementation thay vì contract.
- Tại **Mục 17 (Hypothesis-Driven Forensic & Ambiguity Resolution)**, hiện đang có 4 khoản (`1. Completion Predicate & Non-Goals`, `2. 4-Part Uncertainty Partitioning`, `3. Falsifiable Hypotheses & Minimal Reproducer Codification`, `4. Runtime Evidence over Proxy Assumptions`). Bổ sung khoản **5. Tín Hiệu Giám Sát Thường Trực Sau Điều Tra Sâu (Post-Forensic Cheap Always-On Signal — Pstack v0.15.22)**:
  - Khi một ca chẩn đoán lỗi đòi hỏi phải đào sâu qua nhiều tầng dữ liệu mới tìm ra dữ kiện quyết định (*deciding fact*), Agent bắt buộc phải bổ sung hoặc đề xuất một **tín hiệu giám sát rẻ, luôn bật (cheap always-on signal)** — như một trường structured log, một invariant assertion nhẹ, hoặc một chỉ báo trong readiness probe — để nếu lỗi tương tự tái diễn, nguyên nhân sẽ lộ diện ngay ở cái nhìn đầu tiên.

#### 2.2. Sửa đổi `.agents/skills/ccba-code-review/references/unslop_checklist.md`
- Tại **Mục 6 (Hypothesis-Driven Forensic Checklist)**, bổ sung 3 tiêu chí kiểm tra:
  - [ ] **Two-Edit Behavioral Test Litmus (Pstack v0.15.25)**: Bài test mới có đảm bảo FAIL khi phá vỡ hành vi quan sát được (*Break the behavior*) và vẫn PASS khi chỉ tái cấu trúc nội bộ (*Change the internals*) không?
  - [ ] **Cheap Always-On Signal (Pstack v0.15.22)**: Nếu PR sửa một lỗi phải đào sâu mới tìm ra dữ kiện quyết định, đã bổ sung assertion/structured log nhẹ để lần sau phát hiện ngay ở cái nhìn đầu tiên chưa?
  - [ ] **Mutation Proof & `sync_commit` (Pstack v0.15.28)**: Khi khởi tạo hoặc bảo trì `verify-<app>`, đã kiểm chứng khả năng bắt lỗi bằng phép thử đột biến tạm thời (Scratch Mutation Proof) và ghi nhận `sync_commit` chuẩn xác chưa?

---

### Thành Phần 3: Tinh Chỉnh Khung Định Hình Trước Thực Thi & Bàn Giao Quyết Định (`ccba-grilling` & `ccba-handoff`)

#### 3.1. Sửa đổi `.agents/skills/ccba-grilling/SKILL.md`
- Nâng `metadata.version` từ `"1.0.0"` $\to$ `"1.1.0"`.
- Bổ sung mục **Tiền Khởi Động: Diễn Đạt Lại Mục Tiêu & Mài Sắc Bài Toán (`in-your-own-words` & `sharpen` Discipline — Pstack v0.15.27)** trước khi bắt đầu các nhánh Grilling:
  1. **Diễn đạt lại mục tiêu (`in-your-own-words`)**: Tóm tắt trong 2–3 câu bằng ngôn ngữ của chính Agent về mục tiêu thực sự và bài toán cốt lõi người dùng đang muốn giải quyết.
  2. **Mài sắc theo chuẩn chuyên gia (`sharpen`)**: Xác định cách một chuyên gia đầu ngành sẽ giải quyết bài toán này: dựa trên nguồn dữ liệu gốc nào (*raw sources*), phương pháp thực chất nào (*real methods*), và **1 cơ chế kiểm chứng độc lập bên ngoài (*outside check*)** để xác nhận kết quả đúng.
  3. **Cân bằng mức độ đặc tả**: Chủ động đề xuất tháo bỏ các ràng buộc quá chi tiết nhưng không phục vụ mục tiêu (*over-specification*) song song với việc bổ sung các ràng buộc còn thiếu (*under-specification*), giữ nguyên các quyết định thuộc thẩm quyền của người dùng.

#### 3.2. Sửa đổi `.agents/skills/ccba-handoff/SKILL.md`
- Nâng `metadata.version` từ `2.0.0` $\to$ `2.1.0`.
- Tại **Mục 1. Outstanding User Requests** và phần hướng dẫn trình bày, bổ sung quy chuẩn **Decision-Decidable Catch-up & Compact Visuals (`/ketchup` Discipline — Pstack v0.15.27)**:
  - **Không cắt bớt các quyết định đang chờ người dùng**: Liệt kê đầy đủ 100% các mục cần người dùng ra quyết định/phê duyệt (tuyệt đối không rút gọn thành con số tổng để tiết kiệm chữ), sắp xếp theo thứ tự **rủi ro cao nhất lên đầu (riskiest first)**.
  - **Đủ thông tin để ra quyết định ngay trong 1 lượt đọc**: Mỗi mục chờ quyết định trình bày gọn (~30 từ/mục) gồm đủ 5 yếu tố: *(1) Quyết định cần chốt*, *(2) Phương án Agent khuyến nghị (`Recommended Pick`)*, *(3) Thay đổi/tác động thực tế*, *(4) Bằng chứng*, và *(5) Mức độ rủi ro* (nêu rõ cả khi rủi ro thấp).
  - **Quy tắc sơ đồ trực quan tinh gọn (Compact Visuals)**: Khi sử dụng sơ đồ Mermaid để mô tả kiến trúc hoặc chuỗi PR, giới hạn tối đa $\le 6$ khối (nodes) và $\le 8$ từ trong mỗi khối bằng ngôn ngữ tự nhiên ngắn gọn, không lặp lại thông tin đã nêu trong văn bản.

---

## 3. Câu Hỏi Trọng Tâm Nhờ Grok Thẩm Tra

1. **Tính đầy đủ & Ranh giới chống Test Tampering**: Cơ chế `sync_commit` + **Scratch Mutation Proof** + 4 trạng thái (`in_sync`, `updated`, `bug`, `blocked`) trong `ccba-create-verification-skill` đã đủ chặt chẽ để ngăn chặn tình trạng Agent vô tình làm yếu bài kiểm định hoặc bỏ sót nhánh code mới chưa? Có trường hợp biên nào khi chạy Scratch Mutation Proof (ví dụ: working tree đang dirty hoặc bài test sập giữa chừng chưa kịp revert) cần đặt rào chắn an toàn không?
2. **Tính tương thích với Mục 12 (`Standards-to-Code Enforcement Invariant`) của `docs/rules/code_quality.md`**: Việc bổ sung khoản 10.4 (*Two-Edit Behavioral Test Litmus*) và khoản 17.5 (*Post-Forensic Cheap Always-On Signal*) là các nguyên tắc thiết kế/review định hướng hành vi (đồng bộ vào `unslop_checklist.md`). Cần lưu ý gì trong cách diễn đạt để không xung đột với Mục 12?
3. **Tính tuân thủ Governance (`validate_skills.py --enforce-gpi` & `validate_docs.py`)**: Các bản cập nhật trong `ccba-create-verification-skill`, `ccba-grilling`, `ccba-handoff` và `unslop_checklist.md` có giữ nguyên cấu trúc `## 🏛️ Platform-Aware Architecture Posture`, tiêu chí hoàn thành (`Tiêu chí hoàn thành:`) ở các bước quy trình, và quy tắc relative links (`RULE-3.5`) không?
