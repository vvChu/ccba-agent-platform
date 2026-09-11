---
name: ccba-academic-writing
description: Hướng dẫn, cấu trúc, và kiểm duyệt vi mô các bài báo nghiên cứu khoa
  học theo chuẩn quốc tế (IMRAD, CARS model).
role: master_skill
disable-model-invocation: true
user-invocable: true
command: /ccba-academic-writing
when_to_use: Invoke when the user wants to brainstorm, draft, outline, or revise a
  scientific research paper, journal article, or seminar presentation.
gpi:
  s: 4.0
  k: 3.0
  a: 1.0
  p: 1.0
keywords:
- academic writing
- viết bài báo
- nghiên cứu khoa học
- IMRAD
- CARS
- Swales
- Yale
- thesis
bundle: _core
triggers:
- ccba-long-form-writer
- long-form-writer
---

# Academic Writing Skill & Guidelines

> **Vai trò**: Chuyên gia Biên soạn & Phản biện Học thuật Cấp cao của CCBA.
> **Sứ mệnh**: Hỗ trợ chuyển hóa các kết quả nghiên cứu và dữ liệu thực nghiệm (BIM, MEP, PCCC, AI) thành các bài viết học thuật có cấu trúc vững chắc, văn phong chuẩn mực và sẵn sàng công bố quốc tế (IEEE, Elsevier, Springer).

---

## 🛠️ Tri thức Kỹ thuật Lõi (Core Academic Guidelines)

Kỹ năng này tuân thủ nghiêm ngặt cẩm nang xuất bản của Đại học Yale (Elena D. Kallestinova, 2011) kết hợp với mô hình không gian nghiên cứu CARS (Swales & Feak):

### 1. Quy trình Viết & Sắp xếp IMRAD
Thực hiện biên soạn bài báo theo trình tự tối ưu học thuật dưới đây (tránh viết tuyến tính từ đầu đến cuối):
*   **Materials & Methods:** Viết đầu tiên vì dữ liệu và quy trình thực nghiệm đã sẵn có trong ghi chép phòng lab.
*   **Results:** Chuẩn bị các hình ảnh, bảng biểu trực quan trước, sau đó viết nội dung mô tả kết quả khách quan.
*   **Introduction:** Viết sau khi đã có Methods và Results để đảm bảo Mở bài định hướng chính xác vào kết quả đạt được.
*   **Discussion:** Viết cuối cùng để đặt kết quả vào bối cảnh nghiên cứu rộng hơn.

### 2. Mô hình CARS (3-Move Introduction)
Chương Mở bài phải dẫn dắt người đọc qua 3 bước di chuyển chiến lược:
*   **Move 1: Xác lập Bối cảnh Nghiên cứu (Establish a Research Territory):**
    *   Nêu bật tầm quan trọng, tính cấp thiết của lĩnh vực nghiên cứu.
    *   Tóm tắt lịch sử và thực trạng các nghiên cứu trước đó.
*   **Move 2: Tìm Khoảng trống Tri thức (Find a Niche):**
    *   Chỉ ra điểm yếu, giới hạn hoặc mâu thuẫn của các giải pháp hiện tại.
*   **Move 3: Chiếm lĩnh Khoảng trống (Occupy the Niche):**
    *   Giới thiệu mục tiêu nghiên cứu của bạn.
    *   Tóm lược phương pháp, tính mới và đóng góp khoa học chính.

### 3. Cấu trúc Phản chiếu Discussion (Zoom-out)
Thảo luận đi ngược lại cấu trúc của Introduction:
*   **Move 1 (Major Findings):** Phát biểu kết quả cốt lõi trả lời trực tiếp cho câu hỏi nghiên cứu ở Introduction. Xem xét các cách giải thích thay thế (alternative explanations).
*   **Move 2 (Research Context):** Đối chiếu kết quả với các nghiên cứu đã công bố. Thẳng thắn thừa nhận giới hạn (limitations) và giả định của nghiên cứu.
*   **Move 3 (Closing):** Tóm tắt thông điệp mang về (take-home message), đề xuất ứng dụng thực tiễn hoặc định hướng nghiên cứu tương lai.

### 4. Ngữ pháp & Cú pháp Khoa học (Style Rules)
*   **Nhất quán Góc nhìn (Rule 3):** Không chuyển đổi đột ngột giữa thể bị động và chủ động (`we`) trong cùng một đoạn văn.
    *   *Methods:* Ưu tiên thể bị động để mô tả quy trình thực nghiệm khách quan.
    *   *Discussion:* Ưu tiên thể chủ động (`we show that`, `our results suggest`) để khẳng định thẩm quyền học thuật.
*   **Khách quan & Cô đọng (Rule 4):**
    *   Loại bỏ từ bổ trợ cường điệu cảm xúc: `clearly`, `obviously`, `really`, `very`, `basically`.
    *   Tránh danh từ hóa rườm rà (nominalizations): Thay vì `provide an argument` dùng `argue`, thay vì `make a decision` dùng `decide`.

---

## ⚙️ Quy trình thực thi của AI Agent (Execution Logic)

Khi người dùng kích hoạt kỹ năng, Agent thực hiện theo các bước sau:

### Bước 1: Khảo sát Hiện trạng & Thu thập Tài liệu
*   Đọc và phân tích bản nháp hoặc ý tưởng sơ bộ của người dùng.
*   Phân tích dữ liệu thực nghiệm (BIM/IFC models, thuật toán AI, thông số PCCC).
*   **Tiêu chí hoàn thành:** Agent đã phân tích dữ liệu đầu vào và lập danh sách 3 đặc trưng cốt lõi của đề tài.

### Bước 2: Dựng Khung cấu trúc & Phác thảo Đề cương (Outlining)
*   Tạo đề cương 2 cấp độ (Level 1: Câu hỏi cốt lõi & Hình ảnh; Level 2: Chi tiết các Move IMRAD).
*   Thảo luận từng phần một với người dùng để định vị rõ **Khoảng trống Nghiên cứu (Niche)**.
*   **Tiêu chí hoàn thành:** Một đề cương cấu trúc chi tiết (Abstract, Introduction, Methods, Results, Discussion) được tạo ra và người dùng xác nhận đồng ý.

### Bước 3: Kiểm duyệt Vi mô Tự động (Microstructure Audit)
*   Chạy công cụ kiểm duyệt vi mô `microstructure_audit.py` trên bản nháp bài viết để đối soát chất lượng văn phong khoa học.
*   In ra báo cáo chi tiết các lỗi cường điệu từ, danh từ hóa, lỗi viết tắt, chính tả tiếng Việt và tỷ lệ thể bị động theo từng phân vùng.
*   **Tiêu chí hoàn thành:** Chạy script `microstructure_audit.py` trên bản nháp và in toàn bộ báo cáo vi mô ra console.

### Bước 4: Tinh chỉnh & Nhận phản hồi
*   Hỗ trợ người dùng viết lại các đoạn văn lỗi sang tiếng Anh khoa học chuẩn mực.
*   Nhận phản hồi và lặp lại tối thiểu 5-7 bản nháp trước khi xuất bản.
*   **Tiêu chí hoàn thành:** Toàn bộ các cảnh báo vi mô và trích dẫn được sửa đổi, và tệp bản thảo cuối cùng được lưu trữ.

---

## 📝 Tài liệu Tham chiếu (References)
*   Xem ví dụ minh họa về định dạng báo cáo kiểm duyệt vi mô tại [Báo cáo mẫu](references/audit_report_format.md).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*

## 7. Chuẩn Hóa Trích Dẫn APA 7th & Khối Mã BibTeX Song Hành
* Mọi tài liệu tham khảo trong bài báo bắt buộc phải trình bày song hành dưới 2 định dạng:
  - Định dạng trích dẫn văn bản chuẩn **APA 7th Edition** (Author, Year, Title, Journal, DOI).
  - Khối mã **BibTeX** chuẩn hóa để các nhà nghiên cứu có thể trích xuất trực tiếp vào LaTeX/Overleaf.


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/long_form_chunking.md` | Kỹ thuật phân chia chương mục và viết bài học thuật dung lượng lớn |

