---
proposal_id: "2026-09-22_deep_seam_legal_ocr_normalizer"
type: "tool"
name: "deep-seam-legal-ocr-normalizer"
status: "open"
priority: "Cao"
related_issue: "#322"
proposed_by_project: "dgx-spark-toolkit"
proposed_by_archetype: "specialized_extension"
proposed_date: "2026-09-22"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Tất cả Spokes"
---

# RFC Proposal: Tích Hợp Deep Seam Multi-Pass Legal OCR Text Normalizer Vào ccba-legal-intel

- **Tác giả đề xuất:** Kỹ sư / Agent đại diện Spoke (`dgx-spark-toolkit`)
- **Ngày lập:** 2026-09-22
- **Trạng thái:** Đang mở (Open) — Liên kết Issue #322
- **Căn cứ pháp lý nền tảng:** ADR-0033, ADR-0045, ADR-0056, ADR-0058, OKF v2.4

---

### 1. Bối cảnh & Động lực Thực tế tại Spoke (Context & Motivation)

1. **Nỗi đau thực tế (Pain Points):**
   - Trong quá trình số hóa và nạp văn bản quy phạm pháp luật Việt Nam (QCVN, TCVN, Nghị định, Thông tư) tại các Spoke, tài liệu trích xuất từ PDF scan hoặc OCR cũ của TVPL VIP thường xuyên gặp các lỗi biến dạng văn bản nghiêm trọng:
     * **Khoảng cách ký tự bị tách rời:** Các âm tiết tiếng Việt bị chèn 1-3 khoảng trắng giữa từng ký tự (`B Ộ  X Â Y  D Ự N G`, `N G H Ị  Đ Ị N H`).
     * **Từ ngữ bị dính liền:** Các từ thường gặp bị OCR ghép chặt (`hồsơ`, `sựcố`, `đầutư`, `thôngtưnày`).
     * **Rác tiêu ngữ và hành chính:** Các khối Quốc hiệu, Tiêu ngữ, Số ký hiệu, Nơi nhận, Ký thay (KT.), và chữ ký số điện tử (`Ký bởi: Cổng Thông tin điện tử Chính phủ...`) chiếm dụng token ngữ cảnh.
     * **Gãy dòng và ngắt đoạn xuyên trang:** Lỗi xuống dòng giữa câu tại mép trang PDF làm đứt gãy cấu trúc cây cú pháp (AST) khi nạp vào `ast_parser.py`.
     * **Bảng biểu biến dạng:** Bảng OCR mất dòng kẻ phân cách hoặc xuất hiện các ký tự rác cô lập (`X`, `*`, `-`).
2. **Quá trình ươm tạo & kiểm chứng tại Spoke:**
   - Đã được xây dựng, tôi luyện và kiểm chứng qua hàng ngàn trang văn bản pháp điển trong pipeline nạp liệu của Spoke `dgx-spark-toolkit`.
   - Đạt độ tin cậy tuyệt đối với 100% Python Standard Library (không phát sinh dependency ngoại lai) và 40 unit tests thực thi trong `0.5s` `[đo thực tế]`.
3. **Phản biện đối kháng kép (Double-Pass Adversarial Review):**
   - Sàng lọc và loại bỏ hoàn toàn mã mồ côi/mã chết (`post_ocr_validator.py` 207 dòng) để tuân thủ nghiêm ngặt ADR-0033 và ADR-0056 (Clean Dead Wood).
   - Định tuyến chuẩn xác vào package `ccba-legal-intel` (tuyệt đối không đưa vào `mdconverter` để bảo toàn rào chắn kiến trúc ADR-0036 $\rightarrow$ ADR-0042).
   - Sử dụng Git Worktree cô lập hoàn toàn để không ảnh hưởng đến working directory của Hub.

---

### 2. Đánh Giá Giá Trị × Rủi Ro × KISS (Evaluation Matrix)

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Rất cao (9.5/10) | Giải quyết triệt để lỗi OCR vỡ chữ tiếng Việt, phục vụ toàn bộ các Spoke pháp điển |
| **Độ Phức tạp (Complexity)** | Thấp (2.5/10) | Kiến trúc Deep Module: 4 submodules chuyên biệt giấu kín logic regex phức tạp |
| **Rủi ro Rò rỉ (Risk)** | 0% (Triệt tiêu) | Không chứa bất kỳ đường dẫn hay logic đặc thù host DGX Spark; pass `check_spoke_leakage.py` |
| **Bảo tồn Tiêu chuẩn** | Tuân thủ 100% | 40/40 unit tests pass; 401/401 full package tests pass; pass `ruff check` và `ruff format` |
| **Tuân thủ KISS** | Xuất sắc (9.5/10) | Public interface gọn gàng: `TextNormalizer.clean_chunk()` và `Cleaners.normalize_legal_text()` |

---

### 3. Thiết Kế Chi Tiết & Thay Đổi Kỹ Thuật

- **Submodule mới:** `packages/ccba-legal-intel/src/ccba_legal/normalizers/`
  * `ocr_fixes.py`: Khử khoảng cách vỡ hạt ký tự (`normalize_ocr_spacing`), sửa lỗi chính tả OCR phổ biến (`fix_common_ocr_typos`), tách từ dính tiếng Việt (`fix_stuck_vietnamese_words`, `fix_vietnamese_syllable_boundaries`).
  * `boilerplate.py`: Khử khối Quốc hiệu - Tiêu ngữ, Nơi nhận, Ký thay, chữ ký số điện tử.
  * `structure.py`: Nối dòng gãy giữa câu (`rejoin_paragraphs`), nối đoạn xuyên trang (`rejoin_cross_page_paragraphs`), chuẩn hóa heading Điều/Khoản/Điểm.
  * `tables.py`: Phát hiện bảng quét biến dạng (`detect_garbled_table`), phục hồi bảng pipe table thiếu hàng phân cách.
  * `text_normalizer.py`: Facade `TextNormalizer` và `NormalizerConfig` điều phối chuỗi xử lý đa tầng.
  * `__init__.py`: Re-export toàn bộ public API của submodule.
- **Nâng cấp Facade hiện hữu:** `packages/ccba-legal-intel/src/ccba_legal/cleaners.py`
  * Cập nhật `Cleaners.remove_ocr_artifacts`: Tích hợp thêm bước xử lý khoảng cách và chính tả OCR trước khi regex lọc dòng chữ in hoa, bảo toàn tương thích ngược 100%.
  * Bổ sung phương thức `Cleaners.normalize_legal_text(text, config, strip_doc_id_prefix)` và alias `normalize_legal_text`.
- **Root Package Exports:** `packages/ccba-legal-intel/src/ccba_legal/__init__.py`
  * Xuất khẩu `TextNormalizer`, `NormalizerConfig`, `get_text_normalizer`, `normalize_chunk_text`, `normalize_legal_text`.
- **Bộ Kiểm Thử:** `packages/ccba-legal-intel/tests/test_text_normalizer.py`
  * 40 unit tests kiểm thử toàn diện toàn bộ các kịch bản chuẩn hóa và tích hợp với `Cleaners`.
