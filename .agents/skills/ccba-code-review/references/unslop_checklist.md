# Anti-Slop & Zero-Noise Code Checklist (Pstack Upstream Discipline)

Tài liệu này cung cấp checklist chuyên biệt để nhận diện và loại bỏ mã rác, nhiễu ngữ cảnh (LLM slop), và các cấu trúc thừa thãi do AI sinh ra (theo ADR-0009).

---

## 1. Zero-Noise Comments Checklist
- [ ] **Không dịch tên định danh sang văn xuôi**: Không có comment lặp lại tên hàm, lớp hoặc biến (ví dụ: `# get project by id` ngay trên `def get_project_by_id():`).
- [ ] **Không mô tả cơ chế hiển nhiên của ngôn ngữ**: Loại bỏ các comment như `# loop over items`, `# return result`, `# check if list is empty`.
- [ ] **Chỉ giữ lại "WHY"**: Comment chỉ giải thích lý do kiến trúc, giả định ngầm hoặc đánh đổi kỹ thuật.
- [ ] **Trích dẫn pháp lý chuẩn (ADR-0059)**: Các comment trích dẫn điều khoản văn bản quy phạm pháp luật (`# Theo Điều...`, `# Luật Xây dựng`, `# NĐ...`, `# QCVN...`) phải giữ nguyên văn bản chính thức.

---

## 2. Commented-Out Dead Code Checklist
- [ ] **Triệt tiêu dead code**: Không có bất kỳ khối mã nào bị comment out (`# def old_fn(): ...`, `# import legacy_lib`, `# return False`).
- [ ] **Tin tưởng Git History**: Mọi mã cũ cần tham khảo đã được lưu trong lịch sử commit của Git, không lưu rác trong source tree.

---

## 3. Anti Over-Engineering Checklist
- [ ] **Tuân thủ Platform-Aware KISS**: Không tạo abstractions, interface wrappers, hoặc factory classes khi hệ thống chỉ có đúng một cài đặt cụ thể.
- [ ] **Triệt tiêu mã phỏng đoán (No Speculative Generality)**: Không thêm tham số, options, hoặc extension hooks mà user request hoặc issue hiện tại chưa yêu cầu.
- [ ] **Tối đa 50 dòng/hàm**: Mọi hàm/method phải tuân thủ giới hạn $\le 50$ dòng; nếu dài hơn phải tách thành sub-functions.

---

## 4. Token & Context Economy Checklist
- [ ] **Prompt tinh gọn**: Không chứa các lời chào, câu cảm thán, hoặc văn hoa sáo rỗng trong các file kỹ năng/prompts.
- [ ] **Không lặp hiến pháp**: Các prompt của sub-agent không lặp lại toàn bộ hiến pháp nền tảng mà chỉ kế thừa qua references.

---

## 5. Automated Gate Verification
- [ ] Chạy kiểm toán tự động qua 7-Stage Peer Gate:
  ```bash
  python -c "from ccba_harness import check_redundant_comments; print(check_redundant_comments(['<target_file>']))"
  ```
- [ ] Đảm bảo 0 vi phạm về redundant comments hoặc dead code trước khi hoàn tất review.
