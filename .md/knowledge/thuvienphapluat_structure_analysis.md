# Phân tích Cấu trúc Website Thuvienphapluat.vn & Chiến lược Cào Dữ liệu Tối ưu

Tài liệu này nghiên cứu chi tiết cấu trúc DOM, metadata, hệ thống liên kết quan hệ văn bản của website Thư viện Pháp luật (TVPL) và đề xuất chiến lược cào dữ liệu (scraping) tối ưu, ổn định phục vụ cho hệ thống tri thức CCBA Platform.

---

## 1. Cấu trúc URL của Thư viện Pháp luật

Website `thuvienphapluat.vn` tổ chức các văn bản pháp luật theo cấu trúc đường dẫn tương đối nhất quán, thường có dạng:

1. **Trang nội dung văn bản chính (HTML Text)**:
   - Định dạng: `https://thuvienphapluat.vn/van-ban/[Linh-vuc]/[Ten-Viet-Tat-Van-Ban]-[Id-Van-Ban].aspx`
   - Ví dụ: `https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/Nghi-dinh-06-2021-ND-CP-quan-ly-chat-luong-thi-cong-xay-dung-bao-tri-cong-trinh-xay-dung-462940.aspx`
   - Tại đây, mã số định danh duy nhất của văn bản trên hệ thống TVPL là phần số cuối trước đuôi `.aspx` (ví dụ: `462940`).

2. **Trang Lược đồ (Metadata & Relations)**:
   - Trang lược đồ chứa toàn bộ thông tin thuộc tính (số hiệu, ngày hiệu lực...) và danh sách văn bản liên quan.
   - Định dạng: `https://thuvienphapluat.vn/van-ban/[Linh-vuc]/[Ten-Viet-Tat-Van-Ban]-[Id-Van-Ban].aspx?Tab=LuocDo` hoặc tự động nhảy qua link lược đồ nội bộ.

---

## 2. Cấu trúc DOM Trang Nội dung Văn bản (Primary Page)

### 2.1. Tiêu đề Văn bản
*   **Selector**: `document.title` (chứa tiêu đề đầy đủ do TVPL biên tập).
*   **DOM Element**: Các thẻ tiêu đề trên trang thường nằm trong cụm class `.title-doc` hoặc `h1`.

### 2.2. Nội dung Văn bản (Body Text)
Nội dung văn bản chính được tổ chức trong các thẻ div đặc trưng để phục vụ xem trực tuyến. Các selector chính để trích xuất text sạch bao gồm:
*   `#divContentDoc` (Container chính chứa toàn bộ điều khoản pháp luật dạng HTML sạch).
*   `.content1` hoặc `.contentDoc` (Các selector dự phòng khi giao diện trang thay đổi).
*   `document.body` (Fallback cuối cùng).

### 2.3. Trích xuất Liên kết trong Nội dung
*   Các liên kết dẫn chiếu trực tiếp từ điều khoản này sang văn bản khác được nhúng bằng thẻ `<a>` với thuộc tính `href` chứa cụm `/van-ban/`.
*   Cần trích lọc và làm sạch bằng cách loại bỏ phần tham số query (`?`) và hash (`#`) để thu được URL chuẩn dạng: `https://thuvienphapluat.vn/van-ban/...`

---

## 3. Cấu trúc DOM Trang Lược đồ (Metadata & Relations)

Trang Lược đồ là "mỏ vàng" để xây dựng Graph Database cho hệ thống văn bản pháp luật xây dựng. Dữ liệu tại đây chia làm hai phần chính:

### 3.1. Bảng Thông tin Thuộc tính (Metadata Table)
*   **Selector**: Bảng `<table>` chứa các chuỗi chữ `"Số hiệu"` và `"Ngày ban hành"`.
*   **Cách parse**:
    *   Duyệt qua các thẻ `<tr>` của bảng đích.
    *   Cột thứ nhất (`td[0]`) là Key thuộc tính (sau khi loại bỏ dấu hai chấm `:` và khoảng trắng).
    *   Cột thứ hai (`td[1]`) là Value thuộc tính.
*   **Các trường Metadata quan trọng**:
    *   `Số hiệu` (Document number): Số đăng ký chính thức của văn bản (e.g. `06/2021/NĐ-CP`).
    *   `Loại văn bản` (Document type): Luật, Nghị định, Thông tư, Quyết định...
    *   `Nơi ban hành` (Issuing body): Chính phủ, Bộ Xây dựng, Quốc hội...
    *   `Người ký` (Signer): Thủ tướng, Bộ trưởng...
    *   `Ngày ban hành` (Issued date): Định dạng ngày Việt Nam `DD/MM/YYYY`, cần chuyển về chuẩn ISO `YYYY-MM-DD`.
    *   `Ngày hiệu lực` (Effective date): Định dạng ngày Việt Nam `DD/MM/YYYY`, cần chuyển về chuẩn ISO `YYYY-MM-DD`.
    *   `Ngày đăng` (Published date): Ngày đăng công báo.
    *   `Tình trạng` (Status): Tình trạng hiệu lực (Còn hiệu lực, Hết hiệu lực một phần, Hết hiệu lực...).

### 3.2. Mối quan hệ liên kết giữa các Văn bản (Relations)
TVPL hiển thị mối quan hệ dưới dạng các khối tiêu đề (header) đi kèm danh sách liên kết. Các tiêu đề tiếng Việt tương ứng với các mối quan hệ được ánh xạ trong CCBA Platform như sau:

| Tiêu đề trên TVPL | Mã mối quan hệ | Hướng liên kết | Ý nghĩa |
| :--- | :--- | :--- | :--- |
| **Văn bản bị sửa đổi bổ sung** | `amends_docs` | Outgoing | Văn bản hiện tại bổ sung/sửa đổi cho các văn bản này |
| **Văn bản bị thay thế** | `replaced_docs` | Outgoing | Văn bản hiện tại thay thế cho các văn bản cũ này |
| **Văn bản được dẫn chiếu** | `referenced_docs` | Outgoing | Các văn bản được trích dẫn nội dung bên trong |
| **Văn bản được căn cứ** | `basis_docs` | Outgoing | Căn cứ pháp lý để ban hành văn bản hiện tại |
| **Văn bản được hướng dẫn** | `guided_docs` | Outgoing | Các văn bản cấp trên được văn bản này hướng dẫn |
| **Văn bản được hợp nhất** | `consolidated_docs` | Outgoing | Các văn bản thành phần tạo nên văn bản hợp nhất này |
| **Văn bản hướng dẫn** | `guiding_docs` | Incoming | Các Nghị định, Thông tư chi tiết hóa văn bản này |
| **Văn bản hợp nhất** | `consolidations` | Incoming | Bản Văn bản Hợp nhất (VBHN) chính thức chứa văn bản này |
| **Văn bản sửa đổi bổ sung** | `amended_by_docs` | Incoming | Các văn bản mới sửa đổi/bổ sung một phần văn bản này |
| **Văn bản thay thế** | `replaced_by_docs` | Incoming | Văn bản mới thay thế hoàn toàn văn bản này |
| **Văn bản liên quan cùng nội dung** | `related_docs` | Bi-directional | Các văn bản có nội dung tương đương hoặc liên quan chặt chẽ |

*   **Thuật toán trích xuất liên kết quan hệ**:
    1.  Tìm thẻ tiêu đề (`div`, `td`, `th`, `strong`, `b`) khớp với một trong các chuỗi tiếng Việt ở bảng trên.
    2.  Dùng `.closest()` hoặc duyệt cây DOM lên trên để tìm container chứa (`div`, `td`, `tr`, `table`).
    3.  Lấy tất cả các thẻ `<a>` bên trong container đó mà href chứa cụm `/van-ban/` và tiêu đề khác tiêu đề nhóm để ra danh sách văn bản đích.

---

## 4. Cơ chế Tải xuống Văn bản gốc (Docx/PDF) và Quản lý Session

Để sở hữu bản offline phục vụ phân tích sâu bằng RAG/LLM hoặc phân rã phụ lục, hệ thống cần tự động tải file `.docx` hoặc `.pdf`.

### 4.1. Định vị Nút tải xuống
*   **Selector**: Tìm thẻ `<a>` có chứa text `"Văn bản tiếng Việt (docx)"`, `"Văn bản tiếng Việt"` hoặc `"Tải bản PDF"`.
*   **Action**: Phát lệnh `.click()` thông qua giao diện hoặc mô phỏng CDP.

### 4.2. Giao thức Bypass Login & Cloudflare
TVPL áp dụng hệ thống tường lửa Cloudflare khá chặt chẽ kèm cơ chế giới hạn lượt tải nếu không đăng nhập tài khoản. Chiến lược vượt rào cản:
1.  **Sử dụng Chrome CDP (Chrome DevTools Protocol) ở cổng debug 9222**:
    *   Chạy Chrome với profile người dùng thực (`--user-data-dir`). Việc này giúp lưu cache cookie, Cloudflare Turnstile tokens, giảm thiểu tần suất bị thách đố (CAPTCHA).
    *   Tự động phát hiện màn hình thách đố của Cloudflare thông qua kiểm tra tiêu đề tài liệu (`document.title`) chứa chữ `"Cloudflare"`, `"Just a moment"` hoặc có các selector thách đố như `.cf-turnstile`, `#challenge-stage`. Khi phát hiện, hệ thống sẽ tạm dừng và báo động để người dùng click tay giải CAPTCHA trước khi tự động chạy tiếp.
2.  **Tự động Đăng nhập (Auto-login)**:
    *   Khi nhấn nút tải, nếu xuất hiện popup đăng nhập `#TB_window`, script sẽ tự động tìm kiếm các ô input dạng text và password bên trong popup.
    *   Tự động điền tài khoản hệ thống của CCBA (`vuvanchu119` / `ccba@ibst`) và kích hoạt sự kiện `.click()` vào nút Đăng nhập.
    *   **Xử lý cảnh báo đăng nhập đa thiết bị**: TVPL thường hiện cảnh báo nếu tài khoản đang đăng nhập ở máy khác. Script tự động dò tìm nút chứa văn bản `"Đồng ý"` trong popup cảnh báo để xác nhận đá phiên cũ ra và tiếp tục tải.
3.  **Bắt sự kiện tải file qua thư mục Downloads**:
    *   Do CDP gặp khó khăn trong việc bắt trực tiếp luồng stream tải xuống của trình duyệt ở một số trang, giải pháp tối ưu là chạy tiến trình giám sát thư mục tải xuống mặc định (`Downloads`).
    *   Khi phát hiện tệp tin mới được tạo có đuôi tạm thời (`.crdownload`, `.tmp`), đợi tệp hoàn thành hoàn chỉnh thành `.docx`/`.pdf`.
    *   Ngay sau khi tải xong, chuyển tệp tin (move) vào đúng cấu trúc thư mục dự án cục bộ dưới tên slug đã chuẩn hóa để quản lý.

---

## 5. Chiến lược Cào Dữ liệu Hiệu quả nhất cho CCBA

Để xây dựng cơ sở dữ liệu tri thức pháp luật chất lượng cao, tối ưu hóa băng thông, tài nguyên và tránh bị khóa tài khoản, chiến lược cào dữ liệu được đề xuất như sau:

### Chiến lược 1: Cơ chế cào chênh lệch tối ưu (Delta-Only Scoping)
*   **Nguyên tắc**: Không tải lại các tài liệu gốc đã được thẩm duyệt và lưu trữ cục bộ.
*   **Thực thi**:
    *   Trước khi cào, đối chiếu URL/Số hiệu với `legal_registry.yaml`. Nếu văn bản gốc đã tồn tại dưới dạng `.md`, bỏ qua cào trang chính.
    *   Chỉ cào quét trang Lược đồ để tìm các văn bản hướng dẫn hoặc văn bản sửa đổi bổ sung mới ban hành (Delta guiding docs), sau đó tiến hành tải các văn bản con đó về đặt vào thư mục `guiding_docs/`.

### Chiến lược 2: Xây dựng cấu trúc lưu trữ OKF (Open Knowledge Foundation) Bundle chuẩn hóa
Mỗi văn bản pháp luật chính sau khi cào sẽ được đóng gói thành một thư mục riêng biệt tại `.md/legal_docs/<bundle_slug>/` với cấu trúc chuẩn:
```text
.md/legal_docs/<bundle_slug>/
├── <bundle_slug>.md              # Nội dung văn bản luật chính dạng Markdown sạch
├── index.md                      # Tệp chỉ mục liệt kê toàn bộ thành phần
├── compliance_checklist.md       # Checklist tuân thủ và RACI Matrix do LLM phân tích
├── relationship_chart.md         # Biểu đồ quan hệ Mermaid
├── guiding_docs/                 # Thư mục chứa các văn bản hướng dẫn liên quan
│   ├── <guiding_slug_1>.md
│   └── <guiding_slug_2>.md
└── appendices/                   # Các biểu mẫu phụ lục được phân rã thành tệp riêng
    ├── phu_luc_01.md
    └── phu_luc_02.md
```

### Chiến lược 3: Phân rã phụ lục (Appendix Splitting) và Sửa liên kết tương đối
*   Các văn bản pháp luật xây dựng (như Nghị định 06/2021) chứa các phụ lục biểu mẫu nghiệm thu cực kỳ dài. Nếu để chung một file sẽ làm tràn cửa sổ ngữ cảnh (context window) của LLM và gây khó khăn khi tái sử dụng biểu mẫu.
*   **Giải pháp**: Tách các phụ lục thành các file độc lập trong thư mục `appendices/`.
*   Dùng script tự động (`split_appendices.py`) kết hợp công cụ vá liên kết tương đối (`relative-link-patcher`) để sửa lại toàn bộ liên kết nội bộ trong văn bản gốc trỏ chuẩn xác đến `appendices/phu_luc_xx.md`, bảo toàn cấu trúc liên kết nguyên bản.

### Chiến lược 4: Đăng ký hai lớp (Two-Layer Registry)
Sau khi cào thành công, dữ liệu metadata trích xuất từ trang Lược đồ phải được tự động ghi nhận vào 2 file cấu hình trung tâm tại `.md/knowledge/`:
1.  **`legal_registry.yaml`**: Lưu trữ ID văn bản, tiêu đề, trạng thái hiệu lực, ngày ban hành/hiệu lực, danh sách tệp markdown cục bộ, và các mối quan hệ liên kết để các agent sau dễ dàng truy xuất phục vụ đối soát thiết kế.
2.  **`sources_registry.yaml`**: Lưu trữ đường dẫn tệp tài liệu gốc (.docx / .pdf) và ID lưu trữ Google Drive để đồng bộ hóa tài nguyên chung của viện.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
