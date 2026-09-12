# Viết Chuyên Nghiệp — Router Index (Level 3 Deep Reference)

> **Mục đích:** Bảng điều hướng chỉ mục cho 27 submodules chuyên sâu thuộc hệ thống `viet_chuyen_nghiep`.
> **Kiến trúc Progressive Disclosure:** Agent chỉ tải submodule cụ thể khi gặp từ khóa kích hoạt tương ứng để tiết kiệm ngân sách ngữ cảnh (Context Budget).
> **Tài liệu quy tắc tổng hợp:** Xem [viet_chuyen_nghiep_rules.md](../viet_chuyen_nghiep_rules.md) | Về [SKILL.md](../../SKILL.md)

---

## 1. Pipeline: Research & Thu thập Dữ liệu (`research/`)

| Submodule | Mô Tả & Nhiệm Vụ | Từ Khóa Kích Hoạt |
| :--- | :--- | :--- |
| [`research/research.md`](research/research.md) | Thu thập 5W1H, 3-tier research, content brief | `nghiên cứu`, `research`, `thu thập tư liệu` |
| [`research/analysis.md`](research/analysis.md) | Rút insights từ dữ liệu thô, chấm điểm ICE, khai thác tài liệu chuyên khảo | `phân tích data`, `dữ liệu`, `rút insight` |

---

## 2. Pipeline: Soạn Thảo & Cấu Trúc Nội Dung (`write/`)

| Submodule | Mô Tả & Nhiệm Vụ | Từ Khóa Kích Hoạt |
| :--- | :--- | :--- |
| [`write/story-core.md`](write/story-core.md) | Xây dựng câu chuyện từ insight, chuỗi lập luận logic, show/tell, chuyển ngữ thuật ngữ | `storytelling`, `viết blog`, `câu chuyện` |
| [`write/hook-close.md`](write/hook-close.md) | Kỹ thuật mở bài (4 hook mở) và kết bài (3 kỹ thuật đúc kết) | `mở bài`, `kết bài`, `hook`, `call to action` |
| [`write/rhythm.md`](write/rhythm.md) | Phân bố mật độ đoạn văn, kiểm soát nhịp cảm xúc, biến thiên 70-20-10 | `nhịp điệu`, `rhythm`, `tiết tấu văn phong` |
| [`write/book-chapter.md`](write/book-chapter.md) | Viết chương sách chuyên khảo >5.000 từ, Cold Pedagogy, mô hình Recap-Build-Bridge | `viết sách`, `viết chương`, `chuyên khảo` |
| [`write/technical.md`](write/technical.md) | Soạn tài liệu kỹ thuật, whitepaper, bài báo khoa học, câu chủ đề rõ ràng | `viết kỹ thuật`, `whitepaper`, `academic` |
| [`write/formula-box.md`](write/formula-box.md) | Định dạng hộp công thức và khung tư duy trực quan | `công thức`, `formula-box`, `hộp ghi nhớ` |
| [`write/metaphor.md`](write/metaphor.md) | Xây dựng ẩn dụ mở rộng, đa tầng, liên chương và tổng hợp mô hình | `ẩn dụ`, `metaphor`, `hình tượng hóa` |
| [`write/reframe.md`](write/reframe.md) | Tái định khung nhận thức, đặt tên khái niệm mới, phân tích nghịch lý | `đổi góc nhìn`, `reframe`, `nghịch lý` |
| [`write/debunk.md`](write/debunk.md) | Quy trình phản bác 5 bước, phản biện lịch thiệp, trích dẫn đối chứng | `phản bác`, `debunk`, `phản biện` |
| [`write/emphasis.md`](write/emphasis.md) | Kỹ thuật nhấn mạnh bằng chữ hoa chiến lược, ngắt dòng điểm nhấn | `nhấn mạnh`, `emphasis`, `điểm nhấn` |

---

## 3. Pipeline: Kiểm Tra & Soát Lỗi (`check/`)

| Submodule | Tầng Kiểm Tra | Mô Tả & Nhiệm Vụ |
| :--- | :--- | :--- |
| [`check/consistency.md`](check/consistency.md) | Logic | Đảm bảo tính nhất quán của văn phong, ngữ điệu và hệ thuật ngữ |
| [`check/fact-check.md`](check/fact-check.md) | Nội dung | Kiểm chứng tính xác thực của số liệu, nguồn trích dẫn và tuyên bố |
| [`check/cross-doc.md`](check/cross-doc.md) | Nội dung | Kiểm tra tính nhất quán liên chương, đồng bộ thuật ngữ và case study |
| [`check/ai-detection.md`](check/ai-detection.md) | Chất lượng | Loại bỏ văn phong máy móc, giảm từ nối sáo rỗng và câu rào đón |
| [`check/prose-format.md`](check/prose-format.md) | Hình thức | Chuyển đổi gạch đầu dòng sang văn xuôi mượt mà, chuẩn hóa liên kết câu |
| [`check/english-mixing.md`](check/english-mixing.md) | Hình thức | Chuẩn hóa quy tắc chèn tiếng Anh: ưu tiên tiếng Việt chuẩn trước |
| [`check/capitalization.md`](check/capitalization.md) | Ký tự | Chuẩn hóa quy tắc viết hoa tiêu đề H1/H2/H3 và danh từ riêng |
| [`check/punctuation.md`](check/punctuation.md) | Ký tự | Chuẩn hóa dấu câu tiếng Việt: xử lý em-dash, colon, Oxford comma, khoảng trắng |

---

## 4. Pipeline: Xuất Bản (`publish/`)

| Submodule | Mô Tả & Nhiệm Vụ | Môi Trường Áp Dụng |
| :--- | :--- | :--- |
| [`publish/facebook.md`](publish/facebook.md) | Tối ưu hóa bài viết Facebook cá nhân (plain text) hoặc Fanpage (markdown) | Mạng xã hội, truyền thông |
| [`publish/book.md`](publish/book.md) | Chuẩn hóa thứ bậc tiêu đề, phần tóm tắt in nghiêng và bố cục in ấn | Sách, cẩm nang xuất bản |

---

## 5. Tra Cứu Kỹ Thuật & Phát Triển Nâng Cao (`development/`)

| Submodule | Mô Tả & Nhiệm Vụ |
| :--- | :--- |
| [`pattern-catalog.md`](pattern-catalog.md) | Danh mục 54 mẫu hình viết chia theo 8 nhóm chức năng phục vụ tra cứu nhanh |
| [`development/style-audit.md`](development/style-audit.md) | Phân tích bài viết mẫu để giải mã DNA phong cách tác giả |
| [`development/upgrade.md`](development/upgrade.md) | Quy trình rút tỉa mẫu hình từ output thực tế để hoàn thiện kho kỹ năng |
| [`development/research-framework.md`](development/research-framework.md) | Khung phương pháp luận nghiên cứu sâu có hệ thống |
| [`development/research-results.md`](development/research-results.md) | Tổng hợp các phát hiện nghiên cứu đã được nghiệm thu |
