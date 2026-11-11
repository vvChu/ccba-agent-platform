# SEO Kỹ Thuật, Dữ Liệu Có Cấu Trúc & Khả Năng Khám Phá Cho Tác Nhân AI

> **Nguồn tham chiếu (Upstream Attribution):** Chuyển thể và bản địa hóa từ `addyosmani/web-quality-skills` (`skills/seo`, commit `afa8da94`, MIT License) tích hợp với quy trình cổng thông tin web của CCBA Platform.

Tài liệu này hướng dẫn quy trình tối ưu hóa công cụ tìm kiếm (SEO) dựa trên bằng chứng thực nghiệm, kết hợp kiểm tra trang đã kết xuất (rendered DOM), cấu hình HTTP/crawlability, dữ liệu có cấu trúc JSON-LD và kiểm soát riêng biệt từng tác nhân thu thập dữ liệu AI (AI Crawlers).

---

## 1. Quy Trình Kiểm Định Dựa Trên Bằng Chứng (Evidence-Led SEO Workflow)

1. **Đo lường trang thực tế đã kết xuất:** Khi trang web có thể chạy trực tiếp, sử dụng `lighthouse_audit` (qua Chrome DevTools MCP trong `/ccba-web-testing`) hoặc Lighthouse CLI để định vị chính xác lỗi metadata, ngữ nghĩa HTML và khả năng tương tác tác nhân trên DOM sau khi chạy JavaScript.
2. **Kiểm tra các tín hiệu ngoài tầm nhìn của Lighthouse:** Đối soát trực tiếp HTTP response headers, chuỗi chuyển hướng (redirect chains), tệp `/robots.txt`, độ phủ của `sitemap.xml`, tính nhất quán của thẻ canonical giữa các mẫu trang (templates) và tính hợp lệ của JSON-LD.
3. **Phân tách rạch ròi sự thật kỹ thuật và suy đoán xếp hạng:**
   - Tách biệt hoàn toàn lỗi kỹ thuật thu thập/lập chỉ mục (crawl/index blockers) với chất lượng nội dung và độ uy tín tên miền.
   - **Cấm bịa đặt trọng số thuật toán:** Điểm Lighthouse SEO phản ánh việc tuân thủ các điều kiện kỹ thuật cơ bản, **không phải** là dự báo thứ hạng tìm kiếm. Không bao giờ gán phần trăm tăng hạng giả định; sau khi sửa mã nguồn, báo cáo rõ rằng kết quả lập chỉ mục thực tế cần chờ hệ thống tìm kiếm xác nhận lại.

---

## 2. SEO Kỹ Thuật & Kiểm Soát Thu Thập Dữ Liệu (Crawlability & Indexing)

### 2.1. Quy Chuẩn `/robots.txt`, Meta Robots & Canonical URLs
- **`/robots.txt`:** Chặn các phân vùng quản trị hoặc API nội bộ (`Disallow: /admin/`, `Disallow: /api/`, `Disallow: /private/`), đính kèm đường dẫn tuyệt đối tới `Sitemap: https://example.com/sitemap.xml`. **Tuyệt đối không chặn** các thư mục tài nguyên tĩnh (`/static/`, CSS, JS) cần thiết để công cụ tìm kiếm kết xuất bố cục trang.
- **Meta Robots & `X-Robots-Tag`:** Kiểm soát rõ trạng thái `index, follow` mặc định; rà soát kỹ tránh sót `noindex` từ môi trường staging sang production. Có thể tinh chỉnh độ dài đoạn trích qua `max-snippet:150, max-image-preview:large`.
- **Canonical URLs:** Khuyến nghị gắn thẻ tự tham chiếu (`self-referencing canonical`) bằng URL tuyệt đối chuẩn hóa trên mọi trang có thể lập chỉ mục để triệt tiêu trùng lặp nội dung do tham số truy vấn (`?utm_...`, bộ lọc sắp xếp).

### 2.2. XML Sitemap, Cấu Trúc URL & Bảo Mật HTTPS
- **XML Sitemap:** Giới hạn tối đa **`50,000` URLs hoặc `50MB`** (chưa nén) cho mỗi tệp sitemap; dùng `sitemap_index.xml` cho cổng thông tin quy mô lớn. Chỉ đưa vào các URL chuẩn (canonical), trả mã HTTP `200` và cho phép lập chỉ mục; cập nhật `lastmod` trung thực khi nội dung thực sự thay đổi.
- **Cấu trúc URL:** Dùng chữ thường (lowercase), nối từ bằng dấu gạch ngang (`-`) thay vì gạch dưới (`_`), ngắn gọn (`< 75` ký tự), phản ánh phân cấp ngữ nghĩa rõ ràng và luôn chạy trên HTTPS kèm các header bảo mật (`Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`).

---

## 3. Tối Ưu Hóa Trên Trang (On-Page SEO) & Đa Ngôn Ngữ

- **Thẻ `<title>`:** Duy nhất cho từng trang, đặt chủ đề cốt lõi lên đầu. Mốc `50–60` ký tự chỉ là ngưỡng gợi ý sơ bộ (việc cắt chữ thực tế phụ thuộc chiều rộng pixel trên thiết bị). Phân biệt rõ hiện tượng cắt ngắn hiển thị (truncation) với việc máy tìm kiếm tự viết lại tiêu đề (title-link rewriting) khi `<title>` lệch với tiêu đề hiển thị `<h1>` hoặc văn bản neo (anchor text).
- **Meta Description:** Tóm tắt đặc thù từng trang (gợi ý khoảng `150–160` ký tự), khớp trung thực với nội dung trang và có lời mời hành động rõ ràng.
- **Cấu trúc Heading (`<h1>`–`<h6>`):** Tiêu đề chính `<h1>` mô tả rõ chủ đề trang, phân cấp tuần tự hợp lý không nhảy bậc (không đánh trượt một trang HTML5 hợp lệ chỉ vì có nhiều hơn một thẻ `<h1>` nếu phân cấp vùng ngữ nghĩa rõ ràng).
- **Hình ảnh & Liên kết nội bộ:** Tên tệp ảnh có nghĩa, thuộc tính `alt` mô tả đúng nội dung ảnh (ảnh trang trí thuần túy dùng `alt=""`), khai báo tường minh `width`/`height` chống nhảy bố cục (CLS), nén định dạng WebP/AVIF và `loading="lazy"` cho ảnh dưới màn hình đầu tiên. Liên kết nội bộ dùng anchor text giàu ngữ cảnh thay vì `"xem tại đây"` hay `"đọc thêm"`.
- **Thiết bị di động & Quốc tế hóa:** Khai báo `<meta name="viewport" content="width=device-width, initial-scale=1">`, vùng chạm tối thiểu `48x48px`, cỡ chữ thân bài `>= 16px`; dùng thẻ `<html lang="vi">` và tập liên kết đối ứng `hreflang` (kèm `x-default`) cho cổng thông tin đa ngôn ngữ.

---

## 4. Dữ Liệu Có Cấu Trúc (JSON-LD Structured Data)

- **Nguyên tắc trung thực hiển thị:** Mọi thực thể khai báo trong `<script type="application/ld+json">` (`Organization`, `Article`, `Product`, `FAQPage`, `BreadcrumbList`) **bắt buộc phản ánh nội dung hiển thị thực tế cho người đọc trên trang**. Nghiêm cấm nhồi nhét schema không có thật trên giao diện chỉ để săn tìm rich results.
- Sử dụng kiểu schema cụ thể nhất phù hợp, giữ nguyên định danh `@id` và URL tuyệt đối ổn định qua các lần kết xuất. Cú pháp JSON-LD hợp lệ chỉ là điều kiện cần để xét duyệt, không đảm bảo máy tìm kiếm sẽ luôn hiển thị rich snippet.

---

## 5. Khả Năng Duyệt Của Tác Nhân (Agentic Browsing) & Ma Trận AI Crawlers

Bắt buộc phân biệt rõ **3 khái niệm độc lập** khi thiết kế và kiểm toán cổng thông tin hiện đại:
1. **Lighthouse Agentic Browsing:** Đo lường các tín hiệu kỹ thuật giúp trợ lý tự động hiểu và thao tác trên trang đã kết xuất (cây trợ năng ngữ nghĩa, nhãn biểu mẫu, đăng ký WebMCP nếu ứng dụng thực sự có tác vụ cần phơi bày, và tệp `/llms.txt` tùy chọn).
2. **Lập chỉ mục & Xếp hạng tìm kiếm truyền thống:** Vận hành bởi hệ thống chỉ mục của từng công cụ tìm kiếm, không thể suy diễn từ điểm Agentic Browsing.
3. **Thu thập & Trích dẫn bởi sản phẩm AI:** Phụ thuộc chính sách riêng của từng nhà cung cấp dịch vụ.

### 5.1. Kiểm Soát Từng User-Agent Cụ Thể (Product-Specific Crawler Controls)

Không áp dụng quy tắc chặn hoặc mở mù quáng cho mọi bot AI; đánh giá tách biệt **bot khám phá tìm kiếm/truy xuất theo yêu cầu người dùng** với **bot thu thập dữ liệu huấn luyện mô hình**:

| User-Agent Kiểm Soát | Mục Đích Vận Hành Theo Tài Liệu Chính Thức | Hệ Quả Khi Chặn Trong `/robots.txt` |
| :--- | :--- | :--- |
| `OAI-SearchBot` | Khám phá nội dung cho tính năng tìm kiếm trực tuyến của OpenAI | Ngăn nội dung trang xuất hiện trong tóm tắt và đoạn trích tìm kiếm (liên kết/tiêu đề vẫn có thể lộ diện qua nguồn thứ ba). |
| `PerplexityBot` | Lập chỉ mục phục vụ kết quả tìm kiếm Perplexity | Ngăn lập chỉ mục nội dung bị chặn trong câu trả lời tìm kiếm Perplexity. |
| Crawler tìm kiếm & truy xuất của Anthropic | Lập chỉ mục tìm kiếm và tải trang trực tiếp theo yêu cầu người dùng | Giảm khả năng xuất hiện trong kết quả tìm kiếm hoặc ngăn tải nội dung khi người dùng gửi URL trực tiếp. |
| `Google-Extended` | Kiểm soát việc dùng dữ liệu đã thu thập cho huấn luyện mô hình và một số tác vụ tiếp đất (grounding) của Google | **Không ảnh hưởng** đến việc lập chỉ mục hay thứ hạng trên Google Search truyền thống. |
| `GPTBot` / `ClaudeBot` | Thu thập kho ngữ liệu phục vụ huấn luyện mô hình nền tảng | Chặn thu thập dữ liệu huấn luyện mà vẫn có thể giữ mở kênh tìm kiếm nếu cấu hình tách biệt với các bot tìm kiếm ở trên. |

### 5.2. Kỷ Luật Sử Dụng `/llms.txt` & `/llms-full.txt`
- `/llms.txt` là một đề xuất thử nghiệm hỗ trợ các công cụ tương thích đọc nhanh bản đồ tài liệu đã biên tập (như CCBA Hub đang xuất bản tự động qua `compile_skills_docs.py`), **không phải** là chuẩn bắt buộc liên nhà cung cấp và **không phải** là yếu tố xếp hạng tìm kiếm.
- Luôn ưu tiên nền tảng cốt lõi trước tiên: khả năng thu thập dữ liệu sạch, HTML ngữ nghĩa chuẩn, thẻ tiêu đề/mô tả chính xác và nội dung thực chất; không bao giờ nhân bản nguyên xi `sitemap.xml` vào `/llms.txt` chỉ để lấy điểm kiểm toán hình thức.
