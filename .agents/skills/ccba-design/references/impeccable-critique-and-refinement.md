# Impeccable Critique & Iterative UI Refinement Playbook

> **Nguồn tham chiếu (Upstream Attribution):** Chuyển thể và bản địa hóa từ `pbakaus/impeccable` (`.agent/skills/impeccable`, commit `c1e0e549`, Apache License 2.0) tích hợp với bộ kiểm định tĩnh `../scripts/ui/search.py --audit-file` của CCBA Platform. Tuyệt đối không sử dụng launcher nhị phân `npx impeccable`. <!-- ccba:allow-doc-drift -->

Tài liệu này cung cấp quy trình thẩm định thiết kế hai luồng cô lập (Two-Track Isolated Critique), phân loại 4 chế độ bề mặt (Surface Modes) và 6 lượt tinh chỉnh giao diện chuyên sâu cho `/ccba-design`.

---

## 1. Ranh Giới Cốt Lõi: Tinh Chỉnh (Refinement) vs. Tái Thiết Kế (Redesign)

- **Refinement preserves; redesign replaces:**
  - **Refinement (Tinh chỉnh):** Bảo toàn thế giới thị giác hiện hữu (tokens, bảng màu, font chữ đã chốt), hành vi chức năng, nội dung thực tế (factual copy) và mọi phần nằm ngoài phạm vi yêu cầu. Hỏi ý kiến người dùng trước khi sửa đổi tuyên bố nghiệp vụ hoặc số liệu.
  - **Redesign (Tái thiết kế):** Giữ nguyên sự thật sản phẩm, dữ liệu và ràng buộc kỹ thuật, nhưng coi giao diện cũ là đối chứng cần thay thế hoàn toàn bằng một hệ ngôn ngữ thiết kế mới (cập nhật `MASTER.md` / `DESIGN.md`). **Nghiêm cấm nửa vời:** không bao giờ đánh bóng nửa chừng trên một bố cục đã quyết định loại bỏ.
- **The brief wins:** Tôn trọng tuyệt đối thẩm mỹ, chất liệu, bảng màu và kiểu chữ đã được chốt trong brief thiết kế dự án, ngay cả khi khác với thị hiếu mặc định.

---

## 2. Bốn Chế Độ Bề Mặt Theo Mục Đích Người Dùng (Four Surface Modes)

Chọn chế độ theo **bề mặt cụ thể đang thiết kế**, không chọn theo danh mục sản phẩm tổng thể (ví dụ: trang giới thiệu của công cụ kỹ thuật vẫn thuộc `Persuade`; trang tài liệu hướng dẫn luôn thuộc `Read`):

| Chế Độ (Mode) | Tiêu Chí Thành Công Của Người Dùng | Bề Mặt Điển Hình | Khẩu Độ Tham Vọng & Kỷ Luật Thị Giác |
| :--- | :--- | :--- | :--- |
| **Persuade** | Người xem ra quyết định và hành động | Landing pages, trang chiến dịch, bảng giá | Cá tính thị giác rõ nét, điểm nhấn dứt khoát, hình ảnh thực tế bám sát thế giới thương hiệu. |
| **Operate** | Người dùng hoàn thành tác vụ chính xác, lặp lại | App UI, cổng điều hành, QC dashboards, cài đặt | Ưu tiên khả năng quét mắt (scanability), tính nhất quán, kỳ vọng chuẩn nền tảng và mật độ dữ liệu hợp lý hơn là phô diễn hiệu ứng. |
| **Read** | Người đọc tiếp thu và tra cứu tri thức | Tài liệu kỹ thuật, VBPL, bài viết, changelogs | Cấu trúc phân cấp rõ ràng, nhịp điệu đọc bền bỉ (`45–75ch`), không gây mỏi mắt khi đọc dài. |
| **Experience** | Người xem đắm chìm trực tiếp vào tác phẩm | Portfolios, phòng trưng bày 3D/BIM, showcases | Nhường toàn bộ khung nhìn đầu tiên (first viewport) cho tác phẩm; khung giao diện lùi về phía sau. |

---

## 3. Quy Trình Phản Biện Hai Luồng Cô Lập (Two-Track Isolated Critique)

Để ngăn kết quả quét cơ học làm mỏ neo thiên lệch (anchoring bias) lên phán đoán thẩm mỹ tổng thể, mọi phiên critique giao diện web phải tách bạch hai luồng đánh giá trước khi tổng hợp:

### Luồng A — Đánh Giá Đạo Diễn Thiết Kế (Holistic Design Review — Chạy Trước)
Thực hiện bằng subagent đọc độc lập (hoặc hoàn tất ghi chép toàn bộ Luồng A trước khi chạy detector, kèm nhãn minh bạch `DEGRADED: single-context` ở đầu báo cáo nếu môi trường không mở subagent):
1. **Design Specificity Verdict:** Giao diện này mang bản sắc riêng của sản phẩm/ngành nghề, hay chỉ là khuôn mẫu đại trà có thể hoán đổi cho bất kỳ sản phẩm nào?
2. **Cognitive Load Check:** Rà soát gánh nặng nhận thức; đánh dấu mọi điểm quyết định hiển thị đồng thời `> 4` lựa chọn ngang hàng mà thiếu gom nhóm hoặc progressive disclosure.
3. **Emotional Journey:** Kiểm tra quy tắc Đỉnh – Kết (Peak-End rule), các thung lũng cảm xúc và tín hiệu trấn an ở các thao tác rủi ro cao (xóa dữ liệu, chốt phê duyệt, thanh toán).
4. **Chấm Điểm 10 Heuristics Của Nielsen (Thang `0–4`):**
   - Chấm trung thực từng tiêu chí từ `0` (vi phạm nghiêm trọng) đến `4` (xuất sắc; đa số giao diện thực tế đạt `20–32/40`).
   - **Quy tắc chuẩn hóa mẫu số (`Mode Applicability`):** Trên bề mặt `Persuade` và `Experience`, tiêu chí #7 (*Flexibility and Efficiency*) và #10 (*Help and Documentation*) có thể đánh dấu `n/a` kèm lý do 1 dòng; khi đó bắt buộc chuẩn hóa lại tổng điểm tối đa theo số tiêu chí thực chấm (`4 x số tiêu chí áp dụng`, ví dụ `24/32`), tuyệt đối không in `/40` trên tập con khuyết.
5. **Persona Red Flags:** Chọn 2–3 chân dung người dùng sát thực tế (ví dụ: *Kỹ sư thẩm tra dùng phím tắt*, *Người dùng lần đầu*, *Quản lý duyệt nhanh trên di động*) và chỉ đích danh phần tử giao diện làm gãy luồng thao tác của họ.

### Luồng B — Bằng Chứng Máy Dò Tất Định & Trình Duyệt (Detector + Browser Evidence)
- Quét mã nguồn giao diện qua công cụ nội bộ của Hub:
  ```bash
  python $CCBA_HUB_PATH/.agents/skills/ccba-design/scripts/ui/search.py --audit-file <path/to/ui-file>
  ```
- Kết hợp kiểm tra cây trợ năng (accessibility tree), độ tương phản thực tế và ảnh chụp các kích thước khung nhìn (`1440px`, `1024px`, `768px`, `375px`) qua `/ccba-web-testing` (Playwright hoặc Chrome DevTools MCP).
- **Tổng hợp báo cáo:** Đối chiếu điểm đồng thuận giữa Luồng A và Luồng B, các lỗi kỹ thuật mà mắt thường bỏ sót, các cảnh báo dương tính giả (false positives), và xếp hạng 3–5 vấn đề ưu tiên theo mức độ nghiêm trọng `P0`–`P3`.

---

## 4. Sáu Lượt Tinh Chỉnh Chuyên Sâu (Six Refinement Passes)

### 4.1. `Polish` — Hoàn Thiện Toàn Tuyến Trước Khi Bàn Giao
Phân loại nguyên nhân sai lệch (drift) vào đúng 4 nhóm trước khi sửa ở cấp độ hẹp nhất phù hợp:
- **`missing token`:** Hệ thống thiếu giá trị tái sử dụng $\rightarrow$ bổ sung semantic token.
- **`one-off implementation`:** Đã có shared component chuẩn $\rightarrow$ thay thế phần tự viết lẻ.
- **`conceptual mismatch`:** Luồng thông tin lệch chuẩn so với các phân hệ lân cận $\rightarrow$ đồng bộ lại kiến trúc thông tin.
- **`local defect`:** Lỗi cục bộ hoặc thiếu trạng thái $\rightarrow$ sửa trực tiếp tại chỗ.

**Thứ tự ưu tiên khắc phục 5 bước:** (1) Tác vụ bị chặn, mất dữ liệu, sai lệch trạng thái hoặc kẹt bàn phím $\rightarrow$ (2) Thiếu các trạng thái `loading`, `empty`, `error`, `success`, `disabled`, `permission` $\rightarrow$ (3) Lệch phân cấp, responsive và design tokens $\rightarrow$ (4) Lệch căn chỉnh quang học (optical alignment), icon stroke và chuyển động $\rightarrow$ (5) Dọn mã thừa và tài nguyên rác.

### 4.2. `Typeset` — Kỷ Luật Chữ & Nhịp Điệu Đọc
- **Khổ dòng chuẩn (Reading Measure):** Giữ văn bản xuôi trong khoảng **`45–75ch`**; sàn cỡ chữ thân bài web thông thường là **`1rem` (`16px`)**. Độ cao dòng (`line-height`) tỷ lệ nghịch với độ rộng cột (cột rộng cần thoáng dòng hơn).
- **Ngắt dòng hiện đại (Progressive Line Wrapping):** Đặt `text-wrap: balance` cho tiêu đề và khối trích dẫn ngắn căn giữa; đặt `text-wrap: pretty` cho đoạn văn xuôi thân bài để tránh từ mồ côi cuối đoạn. Chỉ chọn một trong hai cách đánh dấu ranh giới đoạn (khoảng cách đoạn *hoặc* thụt đầu dòng, không dùng kép).
- **Bù trừ thị giác trên nền tối (Dark-Surface Perceptual Compensation):** Chữ sáng trên nền tối luôn tạo cảm giác chói và dày nét hơn chữ tối trên nền sáng; bắt buộc tinh chỉnh trên cả 3 trục cảm nhận: tăng nhẹ `line-height`, nới nhẹ giãn chữ (`letter-spacing`), và điều chỉnh độ đậm (`font-weight`) phù hợp với họ font tiếng Việt.
- Sử dụng `font-variant-numeric: tabular-nums` cho mọi cột số liệu, bộ đếm và bảng đối chiếu kỹ thuật.

### 4.3. `Bolder` vs. `Quieter` — Hiệu Chỉnh Biên Độ Biểu Đạt
- **`Bolder`:** Dành cho bề mặt `Persuade` hoặc `Experience` bị nhạt nhòa, an toàn quá mức — tăng tỷ lệ tương phản cấp độ chữ, tạo điểm neo thị giác chủ đạo và bố cục bất đối xứng có chủ đích.
- **`Quieter`:** Dành cho bề mặt `Operate` hoặc `Read` bị quá tải màu sắc, viền kép, đổ bóng dày và chuyển động gây nhiễu — tiết chế về bảng màu trung tính, dùng khoảng trắng và đường phân cách mảnh (`hairline`) để dữ liệu tự lên tiếng.

### 4.4. `Distill` — Chưng Cất Về Bản Chất
Loại bỏ các tầng bọc (wrappers), thẻ lồng thẻ (card-in-card), nhãn giải thích thừa và bước thao tác trung gian không mang lại thông tin quyết định mới.

### 4.5. `Harden` — Gia Cố Độ Bền Giao Diện Thực Chiến
Thiết kế chỉ đẹp với dữ liệu mẫu hoàn hảo thì chưa sẵn sàng vận hành thực tế. Bắt buộc kiểm thử và gia cố 4 chiều:
1. **Dữ liệu cực đoan (Extreme Inputs):** Chuỗi rỗng, ký tự đơn, tên dự án/pháp lý dài bất thường, con số hàng tỷ, danh sách `1,000+` phần tử.
2. **Chống tràn bố cục Flex/Grid:** Luôn khai báo `min-width: 0` (và `min-height: 0` trên Grid) cho các phần tử con chứa văn bản biến thiên, kết hợp `overflow-wrap: break-word` hoặc cắt dòng có kiểm soát (`-webkit-line-clamp`).
3. **Đa ngôn ngữ & Giãn nở văn bản (i18n Expansion):** Dự phòng **`30–40%` ngân sách không gian** cho bản dịch dài hơn tiếng Anh (như tiếng Việt có dấu hoặc tiếng Đức); tuyệt đối không gán chiều rộng cố định (`w-24`) lên nút bấm chứa chữ. Dùng CSS Logical Properties (`margin-inline-start`, `padding-inline`, `border-inline-end`), bảo toàn ký tự `U+200C` (ZWNJ) và định dạng số theo locale (`Intl.NumberFormat`).
4. **Sàn chữ ô nhập liệu di động (`16px` Mobile Input Floor):** Giữ `font-size >= 16px` trên mọi thẻ `<input>`, `<select>`, `<textarea>` di động để ngăn iOS Safari tự động phóng to cưỡng bức làm vỡ khung biểu mẫu; đảm bảo phóng đại trình duyệt `200%` không làm mất nội dung.

### 4.6. `Clarify` — Minh Bạch Hóa Ngôn Từ Giao Diện (UX Microcopy)
Thay thế các nhãn mơ hồ hoặc thông báo lỗi mang tính mã máy bằng ngôn ngữ hành động cụ thể: nêu rõ chuyện gì vừa xảy ra, nguyên nhân và thao tác khôi phục ngay tại chỗ.
