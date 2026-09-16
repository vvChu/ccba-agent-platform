# CCBA Administrative Succession & Entity Resolution Guardrail — Dynamic Rule
# Rào chắn quản trị kế thừa hành chính & phân định thể chế 2 cấp địa phương theo trục thời gian

---

## 1. NGUYÊN TẮC QUẢN TRỊ KẾ THỪA ĐỊA GIỚI THEO TRỤC THỜI GIAN
Khi tiếp nhận hồ sơ, tư vấn pháp lý hoặc thẩm tra quy hoạch/thiết kế có viện dẫn mốc thời gian lịch sử:
1. **Biến động Sáp nhập (Mergers):**
   - Các đơn vị hành chính đã sáp nhập trong lịch sử (như tỉnh Hà Tây và huyện Mê Linh hợp nhất vào TP. Hà Nội từ ngày 01/08/2008 theo Nghị quyết số 15/2008/QH12): Hồ sơ pháp lý, chứng chỉ quy hoạch, giấy chứng nhận quyền sử dụng đất do cơ quan tiền nhiệm ban hành trước mốc sáp nhập được kế thừa toàn bộ bởi chính quyền địa phương kế thừa hiện hành.
2. **Biến động Chia tách (Splits):**
   - Các tỉnh cũ trong lịch sử (như Hà Nam Ninh, Vĩnh Phú, Hà Bắc, Bình Trị Thiên, Sông Bé, Minh Hải...) khi tra cứu dữ liệu lịch sử phải đối chiếu với mốc ngày chia tách để xác định địa phương kế thừa hiện hành tương ứng theo địa bàn tọa lạc của công trình/dự án.
3. **Cơ chế Dual-Pass Resolution trong RAG:**
   - **Forward Resolution (Truy vết hiện hành):** Khi gặp văn bản hoặc tài liệu do cơ quan lịch sử ban hành, Agent phải tự động xác định cơ quan kế thừa thẩm quyền ở thời điểm hiện tại.
   - **Backward Expansion (Mở rộng lịch sử):** Khi tìm kiếm quy hoạch hoặc tài liệu tại địa bàn từng có biến động địa giới, Agent phải tự động mở rộng truy vấn sang cả kho dữ liệu lưu trữ của địa phương tiền nhiệm.

---

## 2. RÀO CHẮN PHÒNG CHỐNG ẢO GIÁC DANH XƯNG CƠ QUAN ĐÃ GIẢI THỂ / SÁP NHẬP
Agent **TUYỆT ĐỐI KHÔNG** được sử dụng các danh xưng cơ quan, ban ngành đã bị giải thể, tái cấu trúc hoặc sáp nhập khi tư vấn thủ tục hành chính ở thời điểm đương nhiệm:
- **Nguyên tắc Thẩm tra Theo Thời Gian (`as_of_date`):**
  + Việc xác định một cơ quan có bị giải thể hay không phải đối chiếu với thời điểm hiệu lực của hồ sơ hoặc mốc thời gian người dùng đang truy vấn (`as_of_date`).
  + Hồ sơ lịch sử trước thời điểm giải thể được phép sử dụng danh xưng lịch sử; hồ sơ hoặc thủ tục thực hiện sau thời điểm giải thể bắt buộc phải chuyển đổi sang cơ quan kế thừa theo đồ thị bản thể học `administrative_ontology.yaml`.
- **Cơ chế Một Cửa & Đơn Vị Đầu Mối:** Mọi thủ tục hành chính phải được định tuyến đến đúng cơ quan đầu mối đương nhiệm theo quyết định phân công nhiệm vụ hiện hành của UBND cấp tỉnh sở tại.

---

## 3. THỂ CHẾ CHÍNH QUYỀN ĐỊA PHƯƠNG HẬU 01/07/2025 (BÃI BỎ CẤP HUYỆN TOÀN QUỐC)
Từ ngày **01/07/2025**, theo Nghị quyết số 203/2025/QH15 sửa đổi Hiến pháp năm 2013 và Luật Tổ chức chính quyền địa phương năm 2025 (Luật số 72/2025/QH15):
1. **Mô hình 2 cấp chính quyền địa phương:** Hệ thống chính quyền địa phương tại Việt Nam chỉ còn 2 cấp: **Cấp Tỉnh (Tỉnh, Thành phố trực thuộc TW)** và **Cấp Cơ sở (Xã, Phường, Thị trấn, Đặc khu)**.
2. **Chấm dứt hoàn toàn hoạt động của cấp Quận/Huyện:**
   - Tuyệt đối nghiêm cấm việc hướng dẫn người dân, doanh nghiệp nộp hồ sơ hoặc viện dẫn thẩm quyền của HĐND, UBND, Phòng Quản lý đô thị, Phòng Kinh tế và Hạ tầng cấp quận/huyện/thị xã sau ngày 01/07/2025.
   - Thẩm quyền cấp huyện cũ được chuyển tiếp: ~1/3 chuyển lên cấp tỉnh (các Sở chuyên môn) và ~2/3 phân cấp xuống cấp cơ sở (UBND cấp xã) hoặc các Ban Quản lý chuyên trách.
3. **Phân cấp Thẩm quyền Động (Evidence-Based Delegation):**
   - Thẩm quyền cụ thể của UBND cấp xã (phê duyệt quy hoạch điểm dân cư nông thôn 1/500 theo Luật Quy hoạch đô thị và nông thôn 2024, cấp phép xây dựng nhà ở riêng lẻ, hay lấy ý kiến cộng đồng dân cư...) phụ thuộc vào Luật chuyên ngành và Quyết định phân cấp cụ thể của UBND từng tỉnh/thành phố.
   - Agent không được tự ý giả định hay cấm đoán cứng, mà phải đọc và trích dẫn trực tiếp từ văn bản quy phạm pháp luật và quyết định phân cấp tương ứng của địa phương sở tại.

---

## 4. CƠ CHẾ KIỂM ĐỊNH CHỨNG CỨ PHÁP LÝ BẮT BUỘC (EVIDENCE-BASED GROUNDING GATE)
Mọi câu trả lời của AI Agent trước khi phát hành cho người dùng phải vượt qua cổng kiểm tra `ccba_legal.grounding.verify_legal_grounding()`:
1. **Kiểm tra Danh xưng:** Tự động chặn nếu sử dụng danh xưng cơ quan đã giải thể/bãi bỏ (như UBND cấp huyện sau 01/07/2025).
2. **Kiểm tra Căn cứ Thẩm quyền:** Mọi kết luận khẳng định hoặc phủ định thẩm quyền hành chính địa phương bắt buộc phải có trích dẫn hợp lệ kèm Điều/Khoản từ văn bản pháp luật thực định đang có hiệu lực (`ACTIVE`).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*  
*Tuân thủ Khung Quyết Định Hai Giai Đoạn (ADR 0057) và Khóa Hoàn Tất Cưỡng Chế (ADR 0058).*
