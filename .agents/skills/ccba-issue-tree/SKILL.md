---
name: ccba-issue-tree
description: Phân rã bài toán phức tạp theo cây vấn đề McKinsey MECE (Why, What, How) và quản trị vòng đời kiểm chứng giả thuyết.
bundle: _core
tier: kernel
role: master_skill
user-invocable: true
command: /ccba-issue-tree
disable-model-invocation: true
metadata:
  version: "1.1.0"
  author: "CCBA Hub"
gpi:
  s: 4.0
  k: 2.0
  a: 1.0
  p: 1.0
triggers:
- issue tree
- mece
- cây vấn đề
- why tree
- what tree
- how tree
- root cause analysis
- rca
- phân tích nguyên nhân
- phân rã vấn đề
- giải quyết vấn đề
- hypothesis testing
---

# Kỹ Năng Phân Rã Bài Toán Bằng Cây Vấn Đề (McKinsey MECE Issue Tree)

Kỹ năng master điều phối phân rã các bài toán phức tạp, sự cố kỹ thuật hoặc thách thức chiến lược theo phương pháp luận Cây Vấn Đề (Issue Tree) chuẩn **MECE (Mutually Exclusive, Collectively Exhaustive)** của McKinsey, tích hợp tầng vận hành **Governed Lifecycle** nhằm quản trị vòng đời kiểm chứng giả thuyết và gắn kết với các Ghế trách nhiệm Hiến chương CCBA.

---

## 1. Nguyên Tắc Cốt Lõi & Rào Chắn Bất Biến

1. **Chuẩn Mực MECE Bắt Buộc:**
   - **ME (Mutually Exclusive - Không trùng lặp):** Các nhánh cùng cấp không được chồng lấn phạm vi, không phụ thuộc vòng tròn hoặc tranh chấp ranh giới định nghĩa.
   - **CE (Collectively Exhaustive - Không bỏ sót):** Tổng thể các nhánh phải bao quát 100% không gian khả năng của vấn đề, luôn có nhánh dự phòng kiểm soát các yếu tố ngoại lai (Edge Cases / External Factors).
2. **Quy Tắc Nhất Quán Loại Cây (No Mixed Branches):**
   - Tuyệt đối không pha trộn các loại câu hỏi (Tại sao? Cái gì? Làm thế nào?) trong cùng một tầng phân rã. Mỗi cây chỉ phụng sự một mục đích nhận thức duy nhất.
3. **Tầng Vận Hành Có Quản Trị (Governed Lifecycle):**
   - Cây vấn đề không phải là sơ đồ tĩnh để chiêm ngưỡng. Mỗi nút lá là một đối tượng sống chuyển dịch qua 6 trạng thái vòng đời xác định (`UNVERIFIED`, `IN_INVESTIGATION`, `VERIFIED_FACT`, `FALSIFIED`, `DECISION_READY`, `COMMITTED`).
4. **Verbatim Evidence Grounding (ADR-0059):**
   - Mọi giả thuyết chuyển sang `VERIFIED_FACT` phải có bằng chứng thực nghiệm (log máy tính, số liệu đo đạc) hoặc trích dẫn pháp lý nguyên văn 100% từ văn bản chính thống kèm mã băm SHA-256.
5. **Bất Biến Môi Trường Thực Thi (OS & Shell Awareness Guard):**
   - Khi xuất đoạn mã hoặc lệnh ở các nút lá `[COMMITMENT]` / `[SYNTHESIS]`, Agent bắt buộc phải đọc thông tin hệ điều hành từ `user_information.OS`. Trên môi trường Windows, cấm tuyệt đối sinh cú pháp Unix Bash (như `[ -n ... ]`, `date +%s`). Mọi script tự động hóa phải dùng PowerShell hợp lệ hoặc lệnh Python chuẩn (`python -m ...`).
6. **Nguyên Tắc Stateless Tuân Thủ KISS:**
   - Cây vấn đề vận hành hoàn toàn trong ngữ cảnh hội thoại Markdown (Stateless). Tuyệt đối không tự ý sinh tệp trạng thái phụ (`.yaml`, `.json`) trong workspace để tránh phát sinh tệp rác.

---

## 2. Quy Trình Tác Nghiệp 4 Pha (Workflow)

### Pha 1: Phân Loại & Lựa Chọn Cây (Triaging)
Xác định câu hỏi trọng tâm của bài toán để chọn đúng loại cây thích hợp:
1. **Diagnostic Why-Tree (Chẩn đoán nguyên nhân):**
   - *Khi nào dùng:* Sự cố chưa rõ nguồn gốc, sai lệch thiết kế, xung đột mô hình BIM, tranh chấp hợp đồng hoặc bug hệ thống phần mềm.
   - *Câu hỏi cốt lõi:* *"Tại sao sự cố này lại xảy ra?"*
   - *Đầu ra nút lá:* Giả thuyết có thể kiểm chứng (`testable hypothesis`).
2. **Solution How-Tree (Chiến lược giải pháp):**
   - *Khi nào dùng:* Nguyên nhân đã được xác nhận hoặc mục tiêu đã chốt, cần tìm phương án can thiệp tối ưu.
   - *Câu hỏi cốt lõi:* *"Làm thế nào để đạt mục tiêu hoặc khắc phục triệt để?"*
   - *Đầu ra nút lá:* Phương án hành động xếp hạng (`ranked option`) kèm ma trận Giá trị / Độ phức tạp / Rủi ro / KISS.
3. **Workplan What-Tree (Kế hoạch hành động):**
   - *Khi nào dùng:* Cần phân rã gói công việc, xác lập phạm vi dự án hoặc danh mục sản phẩm bàn giao deliverable.
   - *Câu hỏi cốt lõi:* *"Cần thực hiện những hạng mục công việc cụ thể nào?"*
   - *Đầu ra nút lá:* Gói việc được gắn 1 trong 4 thẻ MECE: `[ANALYSIS]`, `[DECISION]`, `[COMMITMENT]`, `[SYNTHESIS]`.
4. **Quy Tắc Chuỗi Chuyển Tiếp Cây (Tree Chaining Sequence):**
   - Khi bài toán toàn trình trải dài từ điều tra sự cố đến thực thi: Khởi đầu bằng `Why-Tree` (chẩn đoán xác định gốc rễ) $\rightarrow$ Lấy nguyên nhân đã kiểm chứng (`VERIFIED_FACT`) làm Gốc cho `How-Tree` (tìm đòn bẩy giải pháp) $\rightarrow$ Lấy phương án được chọn (`COMMITTED`) làm Gốc cho `What-Tree` (bóc tách gói việc deliverable). Tuyệt đối không gộp chung cả 3 mục đích vào 1 cây đơn lẻ.
5. **Rào Chắn Phân Tách Đa Bộ Môn (Multi-disciplinary Partitioning):**
   - Khi bài toán có sự chồng lấn giữa kỹ thuật và pháp lý (ví dụ: vừa sụt lún vừa tranh chấp hợp đồng FIDIC), bắt buộc phân tách rạch ròi ở Tầng 1 theo ranh giới bộ môn (Nhánh 1: Kỹ thuật địa chất/kết cấu; Nhánh 2: Pháp lý hợp đồng & quản lý dự án), triệt tiêu hiện tượng lai tạp chéo (no mixed branches).
6. **Chế Độ Phân Nhánh Tự Động: Fast-Tree vs. Full-Tree (Adaptive Branching):**
   - **Điều kiện Fast-Tree (Cục bộ):** Tự động áp dụng khi bài toán thuộc phạm vi cục bộ ($\le 2$ files bị ảnh hưởng, script độc lập, bugfix đơn lẻ không rò rỉ deadlock).
   - **Chu trình rút gọn 3 bước:** Chuyển dịch nhanh qua `UNVERIFIED` $\rightarrow$ `VERIFIED` $\rightarrow$ `SOLVED`.
   - **Lược bỏ RACI:** Tự động cắt giảm ma trận RACI 12 ghế và định dạng chi tiết 200 dòng để tiết kiệm 60% output. Chỉ xuất cây phân rã gọn gàng và bảng gói việc MECE với 4 nhãn chuẩn tắc: `[ANALYSIS]`, `[DECISION]`, `[COMMITMENT]`, `[SYNTHESIS]`.
   - **Dòng thông báo xác nhận chuẩn (Confirmation Header):** Luôn in dòng thông báo sau ở ngay đầu phản hồi để người dùng kiểm soát và chủ động điều hướng:
     ```markdown
     > 💡 [Phân loại: Fast-Tree] Bài toán được xếp loại Cục bộ (Fast-Tree). Gõ `/ccba-issue-tree --full` nếu muốn mở rộng toàn diện (Full-Tree với 6 trạng thái & RACI).
     ```
   - **Điều kiện Full-Tree:** Áp dụng khi bài toán liên quan đến $\ge 3$ packages, tranh chấp pháp lý hợp đồng, kiến trúc hệ thống lớn, deadlock/race condition phức tạp, hoặc khi có cờ tường minh `--full`.
- **Tiêu chí hoàn thành:** Xác định duy nhất 1 loại cây phù hợp với câu hỏi bài toán trọng tâm và không gian giả định ban đầu.

### Pha 2: Dựng Cây & Phân Rã Chuyên Biệt (Tree Construction)
Tiến hành phân rã đệ quy từ gốc (vấn đề trung tâm) xuống các tầng chi tiết:
1. **Xác định Vấn đề Gốc (Root Problem Statement):** Định nghĩa bài toán sắc bén, lượng hóa rõ ràng mục tiêu hoặc hiện tượng sự cố.
2. **Phân rã Tầng 1 (Primary Branches):** Chia tách không gian vấn đề thành 2 đến 4 nhánh lớn toàn diện (ví dụ theo chuỗi cung ứng, theo dòng dữ liệu, theo các thành phần kết cấu/hợp đồng).
3. **Phân rã Đệ quy (Sub-branches):** Mở rộng đến độ sâu 3-4 tầng. Đảm bảo:
   - Đối với **Why-Tree**: Đi từ cơ chế logic vật lý hoặc quy trình nghiệp vụ $\rightarrow$ nút lá phải là giả thuyết nhị phân (Đúng/Sai).
   - Đối với **How-Tree**: Đi từ đòn bẩy chiến lược $\rightarrow$ nút lá là hành động can thiệp khả thi.
   - Đối với **What-Tree**: Đi từ phạm vi hệ thống $\rightarrow$ nút lá bắt buộc mang 1 trong 4 nhãn chuẩn tắc:
     * `[ANALYSIS]`: Thu thập dữ liệu, khảo sát thực địa, tính toán kỹ thuật, đối soát VBPL. Không dùng cho phê duyệt hay cam kết nguồn lực.
     * `[DECISION]`: Điểm chốt lựa chọn ngã rẽ kỹ thuật hoặc phê chuẩn phương án của cấp có thẩm quyền.
     * `[COMMITMENT]`: Phân bổ ngân sách, ký biên bản/hợp đồng, giao việc IDOP hoặc cam kết tiến độ.
     * `[SYNTHESIS]`: Sản phẩm bàn giao tích hợp cuối cùng (báo cáo thẩm tra, hồ sơ hoàn công, tài liệu nghiệm thu).
- **Tiêu chí hoàn thành:** Cây đạt độ sâu 3-4 tầng, mỗi nút lá chứa đúng kiểu dữ liệu của loại cây tương ứng.

### Pha 3: Kiểm Định Đối Kháng MECE (Double-Check Gate)
Thực hiện thẩm tra tính chặt chẽ của cây trước khi đưa vào vận hành:
1. **Kiểm tra Mutually Exclusive (ME):**
   - Đặt câu hỏi đối kháng: *"Có khả năng một nguyên nhân/giải pháp thuộc về 2 nhánh cùng cấp không?"*
   - Rà soát sự phụ thuộc vòng tròn giữa các nhánh. Nếu có chồng lấn, tái cấu trúc lại trục phân loại (dimension).
2. **Kiểm tra Collectively Exhaustive (CE):**
   - Đặt câu hỏi đối kháng: *"Nếu kịch bản ngoại lai X xảy ra, nó nằm ở đâu trên cây?"*
   - Bắt buộc kiểm tra nhánh kiểm soát "Các yếu tố ngoại lai & Môi trường biên".
3. **Thử nghiệm "Nhánh thứ N+1":**
   - Thử đưa vào một tình huống biên ngẫu nhiên. Nếu tình huống đó không xếp được vào nhánh nào mà không làm vỡ logic cây, cây chưa đạt CE và phải bổ sung nhánh.
- **Tiêu chí hoàn thành:** Đạt 100% MECE checklist, không có xung đột logic giữa các nhánh song song.

### Pha 4: Vận Hành & Quản Trị Vòng Đời Giả Thuyết (Governed Lifecycle & Operating Layer)
Chuyển hóa cây phân rã tĩnh thành hệ thống điều hành động:
1. **Gán Trạng Thái Vòng Đời Cho Từng Nút Lá:**
   - Bắt đầu với `UNVERIFIED` cho toàn bộ các giả thuyết ban đầu.
   - Đưa các nhánh ưu tiên cao vào điều tra (`IN_INVESTIGATION`).
   - Chốt kết quả kiểm chứng bằng chứng cứ xác thực: `VERIFIED_FACT` hoặc `FALSIFIED`.
   - Nâng cấp thành `DECISION_READY` khi đã đủ cơ sở phản biện đối kháng.
   - Chốt cam kết triển khai `COMMITTED` khi cấp thẩm quyền phê duyệt.
2. **Áp Dụng Thang Đo Bằng Chứng (ADR-0059 Grounding):**
   - Mỗi giả thuyết `VERIFIED_FACT` phải ghi nhận cấp độ bằng chứng: `FACT_LOG`, `STATUTE_VERBATIM`, `MEASURED_METRIC`, hoặc `INFERRED_HYPOTHESIS`.
3. **Phân Định Trách Nhiệm Theo Các Ghế Trách Nhiệm CCBA Charter:**
   - Phân công rõ ràng ghế phụ trách điều tra (`Investigator`), ghế kiểm chứng phản biện (`Verifier`), và ghế chốt quyết định (`Approver`).
- **Tiêu chí hoàn thành:** Toàn bộ các nhánh lá đều được gán trạng thái vòng đời, cấp độ bằng chứng và ghế chịu trách nhiệm cụ thể.

---

## 3. Định Dạng Trình Bày Chuẩn

Khi xuất kết quả phân rã cây vấn đề cho người dùng, Agent sử dụng định dạng kép:
1. **Biểu đồ Mermaid:** Trực quan hóa cấu trúc phân nhánh và quan hệ logic.
2. **Bảng Markdown Chi Tiết Nút Lá:** Liệt kê mã định danh nút, loại nút, trạng thái vòng đời, cấp độ bằng chứng, và ghế phụ trách.

```markdown
### [MÃ NÚT] Tên Nhánh / Giả Thuyết
- **Loại nút:** [Hypothesis / Ranked Option / Action Item]
- **Trạng thái:** [UNVERIFIED / IN_INVESTIGATION / VERIFIED_FACT / FALSIFIED / DECISION_READY / COMMITTED]
- **Bằng chứng kiểm chứng:** [Trích dẫn nguyên văn / Log / Đo kiểm / Trống]
- **Ghế phụ trách:** [KY_SU_THUC_THI / CHU_TRI_BO_MON / CO_VAN_PHAP_LY_QA / TRUONG_PHONG_RD_HTQT / GIAM_DOC]
```

---

## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ phân tích cây vấn đề chuyên sâu, Agent sử dụng công cụ `view_file` để nạp các tài liệu mẫu và hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/tree_templates.md` | Bộ mẫu biểu đồ Mermaid và Text Tree chuẩn hóa cho Diagnostic Why-Tree, Solution How-Tree và Workplan What-Tree |
| `references/governed_lifecycle_guide.md` | Hướng dẫn tầng vận hành (Operating Layer), máy trạng thái vòng đời nhánh, thang đo bằng chứng ADR-0059 và ma trận RACI Hiến chương CCBA |

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
