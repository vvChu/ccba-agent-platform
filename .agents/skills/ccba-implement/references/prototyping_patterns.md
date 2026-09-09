# ccba-prototype — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Mẫu hình tạo spike / prototype nhanh để kiểm chứng giải pháp kỹ thuật
> **Mô tả gốc:** Xây dựng mẫu thử thô (throwaway prototype) để trả lời câu hỏi thiết kế (Logic hoặc UI) trước khi triển khai chính thức.

---

# 🚀 Kỹ năng: ccba-prototype (Xây Dựng Mẫu Thử Nhanh)

Mẫu thử (prototype) là **mã nguồn thô viết nhanh, chỉ dùng một lần (throwaway code) để trả lời một câu hỏi thiết kế cụ thể**. Mục tiêu của mẫu thử không phải là sản phẩm hoàn thiện, mà là để kiểm chứng ý tưởng nhanh nhất và sau đó xóa bỏ hoặc hấp thụ.

---

## 📋 Tiêu chí hoàn thành (Completion Criteria)
Kỹ năng chỉ được coi là hoàn thành khi đáp ứng các điều kiện sau:
1.  Xác định rõ câu hỏi thiết kế cần trả lời.
2.  Viết mã nguồn thô và chạy thành công trên máy (không viết unit test, không tối ưu cấu trúc).
3.  In hoặc hiển thị rõ ràng các trạng thái thay đổi để người dùng đánh giá.
4.  Lưu trữ báo cáo/kết luận mẫu thử (`NOTES.md`) vào thư mục tri thức dự án:
    `.md/knowledge/issues/[feature_name]/prototypes/`
5.  Xóa bỏ hoàn toàn mã nguồn thô (TUI shell hoặc router/switcher thử nghiệm) sau khi câu hỏi thiết kế đã được giải đáp hoặc hấp thụ.

---

## 🛠️ Quy trình thực hiện

### Bước 1: Xác định câu hỏi thiết kế cần trả lời
Đọc kỹ yêu cầu của người dùng để xác định loại câu hỏi thiết kế:
- **"Logic / State machine này có chạy đúng trong trường hợp X rồi đến Y không?"** $\rightarrow$ Chọn nhánh **Logic Prototype** (Xem tài liệu chi tiết tại [prototype_logic.md](./prototype_logic.md)).
- **"Bố cục giao diện này hiển thị như thế nào, phương án nào tối ưu hơn?"** $\rightarrow$ Chọn nhánh **UI Prototype** (Xem tài liệu chi tiết tại [prototype_ui.md](./prototype_ui.md)).

*Lưu ý:* Phải ghi rõ câu hỏi này dưới dạng 1 đoạn văn ngắn ở đầu file mã nguồn của mẫu thử hoặc trong file `README.md` tạm của mẫu thử.

**Tiêu chí hoàn thành:** Câu hỏi thiết kế được ghi rõ ràng ở đầu mã nguồn hoặc tài liệu tạm của mẫu thử.

### Bước 2: Tuân thủ các nguyên tắc thiết kế mẫu thử thô (Throwaway Rules)
1.  **Throwaway từ ngày đầu tiên:** Đặt tên file/thư mục có chứa chữ `prototype` để người đọc sau biết đây không phải code sản xuất. Không commit code thô này vào nhánh chính mà không có sự đồng ý của người dùng.
2.  **Khởi chạy bằng 1 lệnh duy nhất:** Định nghĩa lệnh chạy trong task runner hiện tại của dự án (ví dụ: `npm run dev:proto`, `python path/to/proto.py`, v.v.) để người dùng dễ dàng kiểm thử.
3.  **Không phụ thuộc database thực tế (No Persistence):** Trạng thái chỉ lưu trên bộ nhớ (in-memory state). Nếu bắt buộc phải dùng DB, hãy dùng file SQLite tạm hoặc file text tạm với nhãn rõ ràng: `PROTOTYPE_WIPE_ME.db`.
4.  **Bỏ qua tối ưu hóa:** Không viết unit tests, không xử lý lỗi ngoại lệ phức tạp, không viết code trừu tượng. Mục tiêu duy nhất là làm cho mẫu thử **chạy được nhanh nhất**.
5.  **Hiển thị trạng thái rõ ràng:** Với mỗi action (trong logic) hoặc mỗi lần chuyển đổi variant (trong UI), phải in hoặc hiển thị toàn bộ trạng thái hiện tại lên màn hình để dễ theo dõi.

**Tiêu chí hoàn thành:** Mẫu thử chạy được nhanh bằng 1 lệnh duy nhất và tuân thủ các nguyên tắc throwaway.

### Bước 3: Thu hoạch và dọn dẹp (Absorb or Delete)
Khi mẫu thử đã trả lời được câu hỏi thiết kế:
- Ghi nhận quyết định thiết kế vào commit message, ADR (Architectural Decision Record) hoặc file `NOTES.md` nằm trong thư mục `.md/knowledge/issues/[feature_name]/prototypes/`.
- **Dọn dẹp sạch sẽ**: 
  - Nếu là Logic: Xóa bỏ TUI shell thô, chỉ copy module logic thuần túy (reducer/pure functions) vào codebase thật và viết code chuẩn chỉ.
  - Nếu là UI: Xóa bỏ switcher tạm và các variant bị loại; chỉ giữ lại variant chiến thắng và refactor nó theo chuẩn chất lượng của dự án.

**Tiêu chí hoàn thành:** Quyết định thiết kế được ghi nhận vào NOTES.md và mã nguồn thô tạm thời được dọn dẹp sạch sẽ.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
