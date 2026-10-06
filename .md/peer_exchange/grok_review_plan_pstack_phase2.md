---
request_id: req-plan-pstack-phase2-001
verdict: APPROVE_PLAN
conditions: []
summary: ''
telemetry:
  session_id: 28a75ecf-4a0c-49a2-9276-0cdbb1a47dfc
  primary_model: gemini-3.8-flash-high
  input_tokens: 13711
  output_tokens: 2530
  reasoning_tokens: 5070
  cached_read_tokens: 0
  total_tokens: 16241
  model_calls: 1
  turn_count: 1
  cost_usd: 0.0298
  cost_mode: estimated
  duration_seconds: 27.01
---
```

# Báo Cáo Thẩm Định Đối Kháng: Kế Hoạch Triển Khai Pstack Phase 2 & Đồng Bộ Tri Thức

## 1. Phán Quyết & Đánh Giá Tổng Quan

Kế hoạch kỹ thuật được phê duyệt theo hình thức **APPROVE_PLAN** kèm 5 điều kiện ràng buộc bắt buộc (COND-01 đến COND-05).

Bản kế hoạch giải quyết trọn vẹn mục tiêu thu nạp các chuẩn mực tinh hoa từ Cursor `pstack` (v0.15.0+) và tối ưu hóa hạ tầng tri thức CCBA. Thiết kế thể hiện tính kỷ luật cao thông qua các quyết định cụ thể:

1. **Giải pháp Dual-Mode cho `ccba-create-verification-skill`**:
   - Quyết định tích hợp chế độ kép (`scaffold` và `maintain`) vào cùng một skill hiện hữu đáp ứng trọn vẹn triết lý KISS và ADR-0061. 
   - Hai chế độ này chia sẻ chung miền tri thức nền tảng (vòng đời tiến trình server, cổng kiểm tra sức khỏe HTTP/TCP, bẫy lỗi Process Group, mã thoát dọn dẹp tài nguyên). Việc hợp nhất giúp triệt tiêu mã lặp, bảo toàn số lượng kỹ năng của nền tảng ở mức 76 skills và loại bỏ rủi ro phân mảnh tài liệu vận hành.

2. **Khung Phân Tách Vùng Mù 4 Nhóm trong Mục 17 (`docs/rules/code_quality.md`)**:
   - Bốn phân nhóm (*Factual questions*, *Empirical forks*, *Product preferences*, *Irreversible decisions*) định hình phương pháp luận điều tra lỗi khoa học, xóa bỏ thói quen phỏng đoán cảm tính.
   - Tiêu chí này biến triết lý thực nghiệm thành quy chuẩn thực thi có thể đo lường và thẩm tra tự động qua checklist rà soát mã nguồn.

---

## 2. Thẩm Định Đối Kháng & 5 Điều Kiện Ràng Buộc (Binding Conditions)

Để bảo đảm tính toàn vẹn của hệ thống khi triển khai thực tế, Antigravity cần tích hợp 5 điều kiện kỹ thuật dưới đây vào mã nguồn và tài liệu:

### COND-01: Phân Định Rõ Rệt Lỗi Hồi Quy Ứng Dụng Với Sai Lệch Hợp Đồng (Regression vs. Contract Drift Discriminator)
- **Nguy cơ phát hiện**: Khi ứng dụng gãy harness, Agent ở Mode 2 (`maintain`) có thể vội vã sửa mã kiểm thử trong `harness/` để bài test trả về màu xanh (exit code 0), vô tình che giấu một lỗi hồi quy nghiêm trọng của ứng dụng (Test Tampering / False Green).
- **Yêu cầu bắt buộc**: 
  - Trong `maintain_drift_guide.md` và quy trình Mode 2, bổ sung bước kiểm tra nguồn gốc thay đổi (*Pre-Remediation Provenance Check*).
  - Agent đối chiếu lịch sử commit hoặc tài liệu API của ứng dụng:
    - Khi thay đổi trên ứng dụng là chủ đích thiết kế (đổi route `/api/health`, đổi port, đổi định dạng schema) $\rightarrow$ Cập nhật `harness/`.
    - Khi thay đổi trên ứng dụng là lỗi hồi quy ngoài ý muốn $\rightarrow$ Giữ nguyên `harness/`, báo cáo lỗi ứng dụng và yêu cầu sửa mã nguồn chính.

### COND-02: Bộ Ngắt Mạch Số Lần Thử Nghiệm Thực Nghiệm (Bounded Trial Circuit Breaker cho Empirical Forks)
- **Nguy cơ phát hiện**: Khi đối mặt với nhánh giả thuyết (*Empirical Forks*), Agent tự hành có thể sa vào vòng lặp vô tận (thử nghiệm hàng chục biến thể mã nguồn khác nhau), gây lãng phí tài nguyên và làm treo tiến trình.
- **Yêu cầu bắt buộc**: 
  - Quy định rõ trong Mục 17.2: Mọi nhánh thực nghiệm bị giới hạn tối đa 3 lần thử nghiệm độc lập (*Max 3 Empirical Iterations*).
  - Khi vượt quá 3 lần thử nghiệm mà chưa có kết quả đo lường thuyết phục, Agent dừng việc thử-sai, tổng hợp dữ liệu đo đạc và nâng cấp vấn đề thành một cuộc thảo luận kiến trúc (ADR) hoặc xin ý kiến chỉ đạo.

### COND-03: Cơ Chế Ứng Xử Tự Động Cho Product Preferences Khi Chạy Headless
- **Nguy cơ phát hiện**: Khi hệ thống chạy trong môi trường tự động (CI/CD, Background Worker, Batch Run), Agent không có người dùng trực tiếp để hỏi về sở thích sản phẩm (*Product Preferences*), dẫn đến tắc nghẽn luồng xử lý.
- **Yêu cầu bắt buộc**: 
  - Quy định trong Mục 17.2 nguyên tắc hành động khi thiếu kênh tương tác trực tiếp: Agent tự động chọn phương án bảo thủ nhất (*least-privilege*), duy trì tính tương thích ngược cao nhất, đồng thời ghi nhận rõ quyết định này kèm lý do vào phần mô tả PR.

### COND-04: Chuyển Hóa Kịch Bản Tái Lập Lỗi Nhỏ Nhất Thành Kiểm Thử Thường Trực (Reproducer Codification)
- **Nguy cơ phát hiện**: Agent viết kịch bản tái lập lỗi nhỏ nhất (*Minimal Reproducer*) dạng ad-hoc ở thư mục tạm, sau khi sửa xong lỗi thì xóa bỏ, làm mất đi bài test bảo vệ chống tái phát lỗi.
- **Yêu cầu bắt buộc**: 
  - Quy định trong Mục 17.3: Mọi Minimal Reproducer sau khi chứng minh được lỗi thành công bắt buộc phải được chuyển thành test case chính thức trong thư mục `tests/` hoặc bài kiểm tra trong `harness/` trước khi hoàn tất công việc.

### COND-05: Kiểm Soát Tuyệt Đối Dung Lượng `session_learnings.md` $\le 10,240$ Bytes
- **Nguy cơ phát hiện**: Kích thước hiện tại của tệp là ~9.0 KB. Việc bổ sung `RULE-1.17` và `RULE-2.19` có nguy cơ đẩy dung lượng vượt trần 10.0 KB (10,240 bytes).
- **Yêu cầu bắt buộc**: 
  - Soạn thảo hai quy tắc mới với độ cô đọng cao nhất.
  - Đưa lệnh kiểm tra kích thước byte vào bộ lệnh xác minh tự động trước khi đóng tác vụ:
    ```python
    import os
    size = os.path.getsize('.md/knowledge/session_learnings.md')
    assert size <= 10240, f"File size {size} exceeds 10240 bytes ceiling"
    ```

---

## 3. Thẩm Định Chi Tiết Từng Hạng Mục Thiết Kế

| Hạng mục | Đánh giá hiện trạng | Điểm cải tiến và gia cố theo chuẩn CCBA |
| :--- | :--- | :--- |
| **Thành phần A: Kỹ năng kiểm định & cẩm nang drift** | Thiết kế Dual-Mode khoa học, chia tách rõ ràng 2 luồng `scaffold` và `maintain`. | Khai báo cơ chế tự động nhận diện chế độ: nếu phát hiện đã tồn tại thư mục `harness/` thì tự động kích hoạt Mode 2 (`maintain`). Bổ sung quy định hủy tiến trình nền trên Windows dùng `taskkill /F /T /PID` và POSIX dùng `os.killpg(os.getpgid(p.pid), signal.SIGTERM)`. |
| **Thành phần B: Quy chuẩn thẩm định giả thuyết (Mục 17)** | Mô hình 4 vùng mù kế thừa đúng chuẩn `figure-it-out`, xác lập tiêu chí hoàn thành đo lường được (*Completion Predicate*). | Bổ sung giới hạn số lần thử nghiệm (COND-02), cơ chế hành động khi thiếu tương tác (COND-03), và lưu vết bài test hồi quy lâu dài (COND-04). |
| **Thành phần C: Đồng bộ vòng đời tri thức** | Lưu trữ Section 33 vào lịch sử và cập nhật nhật ký phát hành đúng quy trình. | Áp dụng kỹ thuật biểu đạt cô đọng cho `RULE-1.17` và `RULE-2.19` nhằm giữ an toàn ngân sách bộ nhớ dưới 10,240 bytes (COND-05). |

---

## 4. Kế Hoạch Xác Minh Tự Động Đầy Đủ (Verification Matrix)

Tiến trình triển khai chỉ được xem là hoàn tất khi toàn bộ các bước kiểm tra dưới đây kết thúc với mã thoát 0:

1. **Kiểm tra cú pháp và định dạng mã nguồn**:
   ```bash
   ruff check packages/ scripts/governance/ tests/governance/
   ruff format --check packages/ scripts/governance/ tests/governance/
   ```

2. **Kiểm định tính toàn vẹn của danh mục kỹ năng (Skills Governance)**:
   ```bash
   python scripts/validate_skills.py --enforce-gpi
   ```
   *(Bảo đảm 76 skills đạt chuẩn GPI và không có lỗi liên kết cẩm nang tham chiếu).*

3. **Kiểm tra tính nhất quán của Seam Catalog và Ma trận ADR**:
   ```bash
   python scripts/governance/compile_catalog.py --check
   python scripts/sync_hub_adr_matrix.py --check
   ```

4. **Kiểm tra rào chắn trần dung lượng tri thức (Hard Ceiling Check)**:
   ```bash
   python -c "import os; size = os.path.getsize('.md/knowledge/session_learnings.md'); print(f'Size: {size} bytes'); assert size <= 10240, 'Exceeded 10KB limit'"
   ```

5. **Xác minh toàn diện toàn hệ thống qua CI Preset**:
   ```bash
   python -m ccba_harness verify-patch --preset ci
   ```

---

## 5. Kết Luận

Kế hoạch kỹ thuật Pstack Phase 2 đạt độ chín chắn cao về mặt kiến trúc và bảo toàn kỷ luật nền tảng. Antigravity có thể triển khai nhánh mới ngay sau khi tiếp thu đầy đủ 5 điều kiện ràng buộc nêu trên.
