---
request_id: req-20261019-plan-pstack-phase3-001
verdict: APPROVE_WITH_CONDITIONS
conditions:
- id: COND-01
  description: 'Bổ sung quy trình hoàn nguyên tất định cho Scratch Mutation Proof:
    Bắt buộc xác nhận working tree ở trạng thái sạch trước khi thực hiện đột biến,
    bọc thao tác kiểm thử trong cơ chế phục hồi tự động (git checkout/stash), và kiểm
    tra tính nguyên vẹn của mã nguồn trước khi ghi nhận kết quả.'
  blocking: true
  source_profiles: []
- id: COND-02
  description: Xác định rõ nội dung phép thử đột biến là đột biến ngữ nghĩa (Semantic
    Mutation) tác động trực tiếp vào logic hợp đồng, điều kiện rẽ nhánh và giá trị
    biên; lưu vết phản chứng (counterexample failure log) vào hồ sơ nghiệm thu kỹ
    năng kiểm định.
  blocking: true
  source_profiles: []
- id: COND-03
  description: Định nghĩa khái niệm hành vi quan sát được (Observable Behavior) trong
    Two-Edit Behavioral Test Litmus (khoản 10.4) và tín hiệu giám sát (khoản 17.5)
    gắn kết trực tiếp với các bất biến tiêu chuẩn quy định tại Mục 12 docs/rules/code_quality.md.
  blocking: true
  source_profiles: []
- id: COND-04
  description: 'Bảo toàn toàn bộ cấu trúc Governance bắt buộc: Khối ''## 🏛️ Platform-Aware
    Architecture Posture'', dòng ''Tiêu chí hoàn thành:'' tại từng bước quy trình,
    và liên kết tương đối chuẩn mực RULE-3.5 để vượt qua hoàn toàn python scripts/validate_skills.py
    --enforce-gpi và python scripts/validate_docs.py.'
  blocking: true
  source_profiles: []
risk_score: 2
summary: Kế hoạch Triển khai Pstack Phase 3 đạt chất lượng thiết kế xuất sắc, tiếp
  thu chuẩn xác các cải tiến giá trị từ pstack v0.15.28 theo nguyên tắc Zero Skill
  Bloat. Đề xuất tăng cường 4 Kernel Skills hiện hữu và chuẩn mực code_quality.md
  hoàn toàn tối ưu về kiến trúc hệ thống và quản trị kho kỹ năng. Kế hoạch được phê
  duyệt triển khai kèm theo 4 điều kiện kiểm soát quy trình đột biến mã nguồn và bảo
  đảm tính tương thích chuẩn mực.
telemetry:
  session_id: bfc636a9-66fa-44fe-ae07-1a70c19ff39b
  primary_model: gemini-3.8-flash-high
  input_tokens: 14740
  output_tokens: 3252
  reasoning_tokens: 4415
  cached_read_tokens: 0
  total_tokens: 17992
  model_calls: 1
  turn_count: 1
  cost_usd: 0.0347
  cost_mode: estimated
  duration_seconds: 76.09
  degraded_reasoning: false
---

# BÁO CÁO THẨM ĐỊNH ĐỐI KHÁNG KIẾN TRÚC: KẾ HOẠCH TRIỂN KHAI PSTACK PHASE 3
**Tiêu điểm**: Tiếp thu Tinh hoa Kỹ thuật pstack v0.15.20 → v0.15.28 — Chiến lược Zero Skill Bloat  
**Đơn vị thẩm định**: Hệ thống Thẩm định Độc lập (Direct Audit Engine)

---

## 1. Đánh Giá Kiến Trúc Tổng Thể & Chiến Lược Zero Skill Bloat

### 1.1. Tính Đúng Đắn của Chiến Lược Tích Hợp Cốt Lõi (Zero Skill Bloat)
Quyết định tích hợp các cải tiến từ 32 commits mới nhất của `cursor/plugins/pstack` trực tiếp vào 4 Kernel Skills hiện hữu (`ccba-create-verification-skill`, `ccba-grilling`, `ccba-handoff`, `ccba-code-review`) và Quy tắc Tầng 2 (`docs/rules/code_quality.md`) thể hiện tư duy kiến trúc nền tảng vững chắc:
- **Tuân thủ Cổng Năng lực ADR-0057**: Giữ số lượng kỹ năng ở mức hiện hữu, ngăn ngừa sự phân mảnh năng lực thành các micro-skills có dung lượng thấp (dưới 1KB) vi phạm ngưỡng chỉ số quản trị ($\text{GPI} < 12.0$).
- **Bảo toàn Nhận thức Ngữ cảnh (Context Budget Optimization)**: Tích hợp trực tiếp các chỉ dẫn mài sắc (`sharpen`), diễn đạt lại (`in-your-own-words`), và bàn giao gọn (`ketchup`) vào đúng điểm kích hoạt trong chu trình vận hành giúp Agent nắm bắt đầy đủ ngữ cảnh tại thời điểm thực thi mà không phải tải thêm định nghĩa kỹ năng độc lập.
- **Biên lai Tra cứu Hợp lệ (ADR-0061)**: Biên lai `status: NO_MATCH` kèm chữ ký băm `index_sha256` chứng minh việc nâng cấp trực tiếp tài liệu quy chuẩn nội bộ là đường dẫn giải pháp phù hợp với nguyên tắc Reuse-First.

---

## 2. Thẩm Tra Chi Tiết Ba Câu Hỏi Trọng Tâm

### 2.1. Câu Hỏi 1: Tính Đầy Đủ, Ranh Giới Chống Test Tampering & An Toàn Thực Thi Scratch Mutation Proof

Cơ chế kết hợp giữa `sync_commit`, **Scratch Mutation Proof**, và **Ma trận 4 Trạng thái (`in_sync`, `updated`, `bug`, `blocked`)** thiết lập một hàng rào kỹ thuật mạnh mẽ nhằm loại bỏ hiện tượng *Pass on Stale Description* (bài kiểm định báo thành công trên mã nguồn đã thay đổi cấu trúc).

#### A. Ranh Giới An Toàn Khi Chạy Scratch Mutation Proof
Việc can thiệp trực tiếp vào mã nguồn để tạo đột biến tiềm ẩn nguy cơ để lại mã lỗi trên cây làm việc nếu tiến trình gặp gián đoạn. Cần bổ sung quy trình bảo vệ tất định gồm các bước:
1. **Kiểm tra trạng thái cây làm việc trước khi thực thi**:
   ```bash
   git diff --quiet && git diff --cached --quiet
   ```
   Chỉ cho phép chạy Scratch Mutation Proof khi cây làm việc ở trạng thái hoàn toàn sạch.
2. **Thực thi trong cơ chế phục hồi tự động**:
   Mọi thay đổi đột biến phải được thực hiện thông qua tập lệnh hoặc cấu trúc bảo đảm phục hồi mã nguồn ngay lập tức sau khi hoàn tất lệnh kiểm thử:
   ```bash
   # Áp dụng patch đột biến tạm thời -> Chạy verify -> Hoàn nguyên mã nguồn
   git apply mutation.patch
   python -m ccba_harness verify-app || MUTATION_CAUGHT=1
   git checkout -- <mutated_files>
   ```
3. **Xác nhận tính nguyên vẹn sau thử nghiệm**:
   Kiểm tra lại `git status --porcelain` để bảo đảm toàn bộ cây làm việc đã trở về trạng thái sạch trước khi phát hành kết luận nghiệm thu.

#### B. Phân Định Đột Biến Ngữ Nghĩa (Semantic Mutation)
Để loại trừ trường hợp Agent tạo đột biến hình thức (như chèn lỗi cú pháp thô hoặc lệnh `raise` ở đầu hàm), văn bản hướng dẫn cần quy định rõ:
- Đột biến hợp lệ là **đột biến ngữ nghĩa (Semantic Mutation)**: Thay đổi toán tử so sánh (ví dụ: `>` thành `>=`), đảo ngược cờ boolean, bỏ qua một bước ghi nhật ký trạng thái, hoặc thay đổi nhẹ giá trị tính toán đầu ra.
- Ghi lại bằng chứng nhật ký lỗi phản chứng (Failure Counterexample Log) do chính bộ kiểm định phát hiện vào báo cáo bảo trì.

---

### 2.2. Câu Hỏi 2: Tính Tương Thích Với Mục 12 (`Standards-to-Code Enforcement Invariant`)

Mục 12 của `docs/rules/code_quality.md` yêu cầu mọi logic và bộ kiểm thử phải truy nguyên trực tiếp về điều khoản tiêu chuẩn, quy chuẩn xây dựng hoặc quy định pháp lý.

#### A. Tích hợp Khoản 10.4 (*Two-Edit Behavioral Test Litmus*)
Khoản 10.4 tương thích và củng cố trực tiếp cho Mục 12 khi định nghĩa khái niệm **Hành vi quan sát được (Observable Behavior)**:
- **Hành vi** được hiểu là kết quả tính toán, giới hạn an toàn, bảng dữ liệu tuân thủ, và các hiệu ứng phụ (side-effects) được quy định rõ trong văn bản tiêu chuẩn.
- Phép thử *Break the behavior* đóng vai trò kiểm chứng: Nếu làm sai lệch một chỉ số quy định trong tiêu chuẩn mà bài test vẫn vượt qua, bài test đó chưa đạt yêu cầu của Mục 12.
- Phép thử *Change the internals* bảo vệ tính ổn định của mã nguồn: Tái cấu trúc cấu trúc dữ liệu nội bộ mà vẫn đáp ứng đúng quy chuẩn sẽ không làm gãy bài kiểm thử.

#### B. Tích hợp Khoản 17.5 (*Post-Forensic Cheap Always-On Signal*)
- Khi hoàn tất điều tra nguyên nhân gốc rễ của lỗi vi phạm quy chuẩn/tiêu chuẩn, tín hiệu giám sát thường trực được bổ sung phải mang mã định danh chuẩn hóa (Standard Clause Identifier) trong cấu trúc dữ liệu nhật ký (Structured Log) hoặc kiểm tra bất biến (Invariant Assertion).
- Tín hiệu này đóng vai trò chốt chặn giám sát thời gian thực, cảnh báo ngay lập tức khi xuất hiện dữ liệu vi phạm tiêu chuẩn mà không làm suy giảm hiệu năng hệ thống.

---

### 2.3. Câu Hỏi 3: Tính Tuân Thủ Governance (`validate_skills.py` & `validate_docs.py`)

Kế hoạch điều chỉnh đáp ứng đầy đủ các tiêu chuẩn kiểm định tự động của nền tảng khi áp dụng các nguyên tắc sau:
1. **Bảo tồn khối Platform Posture**: Giữ nguyên vẹn tiêu đề và nội dung cấu trúc `## 🏛️ Platform-Aware Architecture Posture` trong cả 3 tệp `SKILL.md`. Khối này là điều kiện tiên quyết trong bộ phân tích cú pháp của `validate_skills.py`.
2. **Duy trì mốc hoàn thành chuẩn mực**: Mọi bước trong quy trình thực thi bắt buộc giữ cấu trúc `Tiêu chí hoàn thành:` với các điều kiện nghiệm thu định lượng cụ thể.
3. **Quy tắc liên kết tương đối (`RULE-3.5`)**: Sử dụng đường dẫn tương đối chính xác từ thư mục chứa tệp:
   - Trong `SKILL.md`: Trỏ đến `references/maintain_drift_guide.md`.
   - Trong `code_quality.md`: Trỏ đến các tài liệu liên quan trong cùng cây thư mục `docs/rules/`.
4. **Bảo toàn và nâng cao chỉ số GPI**: Việc bổ sung logic mài sắc mục tiêu và cơ chế bàn giao quyết định làm tăng độ sâu nghiệp vụ và giá trị điều phối của kỹ năng, bảo đảm điểm số GPI luôn duy trì ở mức cao vượt trội so với ngưỡng tối thiểu 12.0.

---

## 3. Thẩm Tra Chi Tiết Các Thành Phần Sửa Đổi

### 3.1. Thành Phần 1: Kiểm Định & Bảo Trì Drift (`ccba-create-verification-skill`)
- **Metadata Version**: Nâng lên `1.2.0` thể hiện đúng mức độ bổ sung tính năng tương thích ngược.
- **Trường `sync_commit` & `covered_paths`**: Thiết lập mốc bám dính phiên bản rõ ràng giữa bộ kiểm định và mã nguồn.
- **Ma trận 4 trạng thái**: Phân định ranh giới xử lý rành mạch:
  - `in_sync`: Mã nguồn khớp hoàn toàn với mô tả kiểm định.
  - `updated`: Cập nhật bộ kiểm định theo thay đổi chủ đích của mã nguồn và xác nhận bằng Scratch Mutation Proof.
  - `bug`: Giữ nguyên bài kiểm thử, ghi nhận counterexample, chặn việc nâng `sync_commit`.
  - `blocked`: Giữ nguyên `sync_commit`, ghi nhận rào cản môi trường.

### 3.2. Thành Phần 2: Quy Chuẩn Chất Lượng & Rà Soát Code
- **Mục 10.4 (`code_quality.md`)**: Cung cấp bộ lọc kép loại bỏ triệt để các bài kiểm thử giả tạo (tự so sánh với chính giá trị hàm trả về hoặc assert lỏng lẻo).
- **Mục 17.5 (`code_quality.md`)**: Chuyển hóa tri thức thu được sau quá trình điều tra sự cố thành giá trị bảo vệ lâu dài cho hệ thống.
- **Bổ sung Checklist (`unslop_checklist.md`)**: Đồng bộ hóa trực tiếp 3 mục kiểm tra thực tế giúp khâu Review PR có công cụ đối soát cụ thể.

### 3.3. Thành Phần 3: Định Hình Trước Thực Thi & Bàn Giao Quyết Định
- **`ccba-grilling`**:
  - Tích hợp bước diễn đạt lại mục tiêu (`in-your-own-words`) và xác lập cơ chế kiểm chứng độc lập bên ngoài (`outside check`) giúp làm rõ yêu cầu ngay từ đầu.
  - Cân bằng đặc tả giúp kế hoạch tập trung vào bản chất bài toán.
- **`ccba-handoff`**:
  - Nguyên tắc xếp các quyết định rủi ro cao nhất lên đầu (`riskiest first`) hỗ trợ người dùng phân bổ sự tập trung chính xác.
  - Định dạng cô đọng ~30 từ với 5 thành tố cung cấp đầy đủ dữ kiện để phê duyệt nhanh chóng.
  - Tiêu chuẩn sơ đồ Mermaid ($\le 6$ khối, $\le 8$ từ/khối) bảo đảm thông tin trực quan, dễ tiếp nhận trên mọi thiết bị hiển thị.

---

## 4. Bảng Ma Trận Rủi Ro Kỹ Thuật & Biện Pháp Kiểm Soát

| Thành phần | Rủi ro tiềm ẩn | Biện pháp kiểm soát bắt buộc |
| :--- | :--- | :--- |
| **Scratch Mutation** | Mã đột biến rò rỉ vào commit chính thức khi kiểm thử gặp sự cố | Áp dụng cơ chế kiểm tra `git status` trước và sau khi thử nghiệm, sử dụng script hoàn nguyên tự động |
| **Đánh giá Drift** | Nhầm lẫn giữa lỗi mã nguồn (`bug`) và thay đổi có chủ đích (`updated`) | Bắt buộc đối chiếu commit log/PR liên quan; chỉ ghi nhận `updated` khi có bằng chứng thay đổi chủ đích |
| **Two-Edit Litmus** | Lạm dụng việc sửa đổi bài test khi tái cấu trúc nội bộ | Cố định hợp đồng giao diện công khai; cấm sửa đổi assertion khi các giá trị quan sát được giữ nguyên |
| **Bàn giao Ketchup** | Tóm tắt quá ngắn làm mất thông tin rủi ro quan trọng | Tuân thủ đủ 5 thành tố bắt buộc cho từng mục quyết định |

---

## 5. Kết Luận & Hướng Dẫn Thực Thi

Kế hoạch Kỹ thuật Triển khai Pstack Phase 3 đáp ứng toàn diện các tiêu chí khắt khe về kiến trúc nền tảng, tính thực tiễn và tính kỷ luật của CCBA Platform. Kế hoạch sẵn sàng để chuyển sang giai đoạn tạo nhánh thực thi (Implementation Branch) và lập trình chi tiết ngay khi tích hợp đầy đủ 4 điều kiện chốt chặn an toàn nêu tại phần đầu báo cáo.
