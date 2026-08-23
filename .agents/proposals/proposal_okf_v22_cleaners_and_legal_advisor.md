# 🏛️ Đề Xuất Đóng Góp Ngược: OKF v2.2 Scoped Noise Strippers & Legal Advisor Skill

> **Mã đề xuất:** `RFC-2026-08-OKF-V22-ADVISOR`  
> **Dự án nguồn (Spoke):** `ccba-legal-knowledge`  
> **Nhánh đề xuất (Branch):** `proposal/okf-v22-cleaners-and-legal-advisor`  
> **Loại đóng góp:** `package` (`packages/ccba-legal-intel`) + `skill` (`legal-advisor`) + `workflow` (`ccba-legal-advisor`)  
> **Mức độ ưu tiên:** Cao (Critical Core Engine)  

---

## 1. 🎯 Bối Cảnh & Nỗi Đau Thực Tế (Context & Problem)

Trong quá trình chuẩn hóa 26 gói tri thức pháp lý (24 VBPL + 2 QCVN) theo chuẩn **OKF v2.2 Native-First (ADR 0021)** tại Spoke `ccba-legal-knowledge`, chúng tôi phát hiện 2 điểm nghẽn lớn:

1. **Rác Layout Hành Chính & Mã Scraping:** Thân văn bản khi bóc tách từ DOCX/HTML gốc của TVPL VIP thường bị dính chữ ký hành chính (`CHỦ TỊCH QUỐC HỘI`, `THỦ TƯỚNG`, `Nơi nhận:`) hoặc các thẻ JavaScript/iframe quảng cáo của web pháp lý, làm ô nhiễm context của LLM.
2. **Bẫy Câu Hỏi Mơ Hồ Của Kỹ Sư:** 90% câu hỏi ban đầu của kỹ sư khi tra cứu luật đều thiếu tham số (quy mô, cấp công trình, bối cảnh chuyển tiếp). Nếu AI trả lời ngay sẽ sinh ra lý thuyết chung chung hoặc giả định sai lệch gây rủi ro pháp lý.

---

## 2. 💡 Giải Pháp Đề Xuất Đóng Góp Lên Hub (Proposed Solution)

### A. Gói Thư Viện `packages/ccba-legal-intel`:
- Bổ sung `Cleaners.strip_administrative_noise(text: str)`: Cắt bỏ 100% rác Quốc hiệu, Tiêu ngữ, Nơi nhận và chữ ký hành chính.
- Bổ sung `Cleaners.strip_web_artifacts(text: str)`: Loại bỏ các thẻ `<script>`, `<form>`, `<input>`, `<iframe>`, nút chia sẻ mạng xã hội.

### B. Kỹ Năng Mới `.agents/skills/legal-advisor/`:
- Tích hợp **Cơ chế Phỏng vấn Thích ứng (Adaptive Diagnostic Depth)**: Không giới hạn cứng số câu hỏi, linh hoạt co giãn theo độ phức tạp của dự án (Level 1 $\rightarrow$ Level 3).
- Tích hợp **4 Khung Mẫu Tương Tác Động Theo Ngữ Cảnh**:
  - *Mẫu 1:* Thẩm định tham số kỹ thuật cụ thể.
  - *Mẫu 2:* Đối chiếu chuyển tiếp & không hồi tố.
  - *Mẫu 3:* Bảng Ma trận Checklist Thẩm tra Đa cột.
  - *Mẫu 4:* Bóc tách Biểu mẫu & Danh mục hồ sơ hoàn công/cấp phép.
- Định dạng chuẩn: **Phiếu Ý Kiến Pháp Lý CCBA (CCBA Legal Opinion Standard Form)** gồm 4 phần.

### C. Workflow Mới `.agents/workflows/ccba-legal-advisor.md`:
- Kích hoạt tự động (`disable-model-invocation: false`) khi người dùng đặt câu hỏi tư vấn pháp lý.

---

## 3. 🧪 Kế Hoạch Kiểm Thử & Nghiệm Thu (Verification & Test Suite)

- **Bộ kiểm thử tự động:** `packages/ccba-legal-intel/tests/test_okf_v22_cleaners.py`
- **Kết quả chạy kiểm thử:** **2/2 Tests PASSED (100%)**.
- **Tính tương thích:** Không gây breaking change cho các services hiện hữu (`ccba-ai-qc`, `ccba-legal-intel`).
