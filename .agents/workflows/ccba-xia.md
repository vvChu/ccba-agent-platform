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

Quy trình này dẫn dắt AI Agent thực hiện trích xuất, so sánh, phản biện và chuẩn bị kế hoạch chuyển dịch (port) một tính năng từ repository đích (GitHub hoặc thư mục cục bộ) vào hệ thống CCBA Agent Platform.

Triết lý cốt lõi: hiểu rõ trước khi sao chép | phản biện trước khi triển khai | thích ứng chứ không cấy ghép

## Các pha xử lý

```text
[1. Recon] -> [2. Map] -> [3. Analyze] -> [4. Challenge] -> [5. Plan] -> [6. Deliver]
```

### Pha 1: Recon (Trinh sát)

Mục tiêu: Đóng gói và thu thập tri thức của repository đích.

1. **Xác minh môi trường:** Đảm bảo máy tính có cài đặt Node.js/npm để chạy `npx`.
2. **Đóng gói mã nguồn:** Chạy helper script [repomix_pack.py](file:///d:/GitHubProjects/ccba-agent-platform/scripts/repomix_pack.py) để đóng gói toàn bộ thư mục/repo đích thành một file context phẳng dạng XML đặt tại [.md/scratch/source_pack.txt](file:///d:/GitHubProjects/ccba-agent-platform/.md/scratch/source_pack.txt):
   ```bash
   python scripts/repomix_pack.py --source <path-to-target-repo> --output .md/scratch/source_pack.txt
   ```
   *Lưu ý: Nếu nguồn là repository GitHub online, Agent cần hướng dẫn người dùng clone về một thư mục tạm thời trong workspace rồi trỏ đường dẫn tới đó.*
3. **Đọc hiểu cấu trúc:** Đọc tệp [.md/scratch/source_pack.txt](file:///d:/GitHubProjects/ccba-agent-platform/.md/scratch/source_pack.txt) để hiểu tổng quan kiến trúc, dependencies và các files cốt lõi.

### Pha 2: Map (Ánh xạ cấu trúc)

Mục tiêu: Ánh xạ các thành phần nguồn sang hệ thống cục bộ.

1. **Kiểm kê thành phần:** Phân tích folder/file cấu thành tính năng nguồn (logic, state, API, config, types, tests).
2. **Ma trận Dependency:** Xây dựng ma trận ánh xạ sang Platform hiện có:
   * `EXISTS`: Thành phần/thư viện đã có sẵn ở cục bộ.
   * `NEW`: Thành phần cần viết mới hoàn toàn.
   * `CONFLICT`: Thành phần bị xung đột cần adapt hoặc viết lại (ví dụ Node.js hooks vs Python hooks).

### Pha 3: Analyze (Phân tích)

Mục tiêu: Tìm hiểu lý do tại sao mã nguồn nguồn hoạt động như vậy.

1. **Phân tích luồng thực thi:** Trace luồng dữ liệu từ điểm kích hoạt đến hiệu ứng phụ (side effects).
2. **Ánh xạ cấu hình:** Phân tích các biến môi trường, cờ cấu hình cần thiết để tính năng hoạt động.
3. **Phân tích theo chế độ:**
   * `--compare`: Tập trung vào sự khác biệt kiến trúc và tính khả thi.
   * `--port`: Viết lại một cách tự nhiên (idiomatic) theo stack của dự án (Python, v.v.).

### Pha 4: Challenge (Phản biện thiết kế) - CỔNG KIỂM SOÁT CỨNG

Mục tiêu: Phản biện thiết kế để loại bỏ các giả định sai lầm.

1. **Câu hỏi phản biện:** Đưa ra **ít nhất 5 câu hỏi phản biện cốt lõi**. Mỗi câu hỏi phải có:
   * Giải pháp của nguồn (Source's way).
   * Giải pháp của Platform (Our way).
   * Rủi ro / Đánh giá đánh đổi nếu cấy ghép trực tiếp (Risk / Trade-off).
2. **Ma trận quyết định (Decision Matrix):** Trình bày ma trận so sánh và đề xuất thích ứng.
3. **CỔNG PHÊ DUYỆT:** Dừng lại, in ma trận quyết định và yêu cầu người dùng phê duyệt trước khi lập kế hoạch chi tiết (trừ khi chạy chế độ `--fast`).

### Pha 5: Plan (Lập kế hoạch)

Mục tiêu: Soạn thảo kế hoạch triển khai port mã nguồn.

1. Tạo hoặc cập nhật tệp kế hoạch triển khai [implementation_plan.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/implementation_plan.md) (lưu tại thư mục artifacts hoặc [.md/knowledge/](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/)).
2. Kế hoạch phải chỉ rõ:
   * Các tệp tin cần tạo mới `[NEW]`, chỉnh sửa `[MODIFY]`.
   * Cách thức adapt code (ví dụ chuyển từ Javascript sang Python).
   * Chiến lược khôi phục (Rollback Strategy) nếu gặp lỗi.

### Pha 6: Deliver (Bàn giao)

Mục tiêu: Báo cáo kết quả phân tích và kế hoạch cho người dùng.

*   In ra thông báo bàn giao kế hoạch triển khai kèm theo đường dẫn file [implementation_plan.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/implementation_plan.md).
*   *Lưu ý: Workflow này không tự động viết hay thay thế code dự án, việc thực thi sẽ do kỹ sư hoặc subagent đảm nhận sau khi kế hoạch được duyệt.*
