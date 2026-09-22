---
name: ccba-ai-qc-pccc-audit
description: Hệ thống Thẩm tra lỗi thiết kế đa bộ môn (PCCC, MEP, Kiến trúc) thông
  qua cơ chế Semantic Map-Reduce.
applies_to:
- Thẩm tra thiết kế
- Thiết kế
bundle: _qc
tier: kernel
user-invocable: true
command: /ccba-ai-qc-pccc-audit
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 2.0
  k: 2.0
  a: 4.0
  p: 1.0
triggers:
- pccc audit
- semantic map-reduce
- thẩm tra PCCC
- thiết bị chữa cháy
- báo cháy
- ccba-pccc-cdt-tuthamdinh
- pccc-cdt-tuthamdinh
- ccba-pccc-thamdinh-congan
- pccc-thamdinh-congan
- ccba-pccc-thamdinh-cqxd
- pccc-thamdinh-cqxd
---

# CCBA AI QC PCCC Audit

Skill này sử dụng cơ chế **Semantic Map-Reduce** để phân tích chéo và gộp kết quả đánh giá kỹ thuật đối với hồ sơ PCCC lớn, giúp khắc phục giới hạn context window của LLM và hiện tượng sinh ảo giác.

---

## 🔍 Điều kiện Áp dụng

### Khi nào sử dụng (When to use)
- Sử dụng khi người dùng yêu cầu thẩm tra thiết kế phòng cháy chữa cháy (PCCC), hệ thống cơ điện (MEP), hoặc kiến trúc thoát nạn của công trình xây dựng.
- Sử dụng để đối chiếu, kiểm tra sự tuân thủ quy chuẩn xây dựng Việt Nam (như QCVN 06, TCVN 3890, TCVN 2622).

### Khi nào KHÔNG sử dụng (When NOT to use)
- Tuyệt đối **KHÔNG** áp dụng kỹ năng này và **KHÔNG** nhắc đến các quy chuẩn PCCC (QCVN 06, TCVN 3890, TCVN 2622) khi người dùng hỏi các câu hỏi thông thường không liên quan đến thẩm tra PCCC (ví dụ: lập trình phần mềm, lắp đặt thiết bị gia dụng đơn giản, viết email công việc, giải toán...).
- Đối với các yêu cầu không thuộc phạm vi thẩm tra PCCC, hãy trả lời trực tiếp và ngắn gọn theo đúng chủ đề người dùng yêu cầu.

---

## Quy trình Map-Reduce

- **Map 1 (Legal & Specs):** Đánh giá thuyết minh PCCC dựa trên quy chuẩn QCVN 06:2022/BXD, TCVN 3890:2023 và phản hồi của PC07.
- **Map 2 (MEP Water):** So sánh chéo thông số thiết bị chữa cháy giữa bản vẽ MEP và thuyết minh.
- **Map 3 (MEP Alarm vs Arch):** So sánh sơ đồ báo cháy và bản vẽ kiến trúc (vị trí đầu báo, đèn sự cố, lối thoát nạn).
- **Reduce:** Tổng hợp các lỗi phát hiện được, loại bỏ trùng lặp và xuất thành báo cáo Markdown hoàn chỉnh theo mẫu PC13 (NĐ 105/2025/NĐ-CP).
- **Ràng buộc đối soát đệ quy (ADR 0010):** Đối với các lỗi nghi vấn vi phạm quy chuẩn (như QCVN 06 hoặc TCVN 3890), Agent **không tự động** kích hoạt research. Hãy đề xuất người dùng chạy `/ccba-research [tên_quy_chuẩn]` để đối soát chéo dưới nền nhằm kiểm soát chi phí API.

---

## Hướng dẫn Vận hành

### 1. Điều kiện tiền quyết
Toàn bộ tài liệu PDF phải được chạy qua `ccba-ai-pdf-preprocessor` để chuyển đổi sang định dạng văn bản `.md`.

### 2. Lệnh chạy script:
Xác định đường dẫn Hub (`hub_path`) và chạy lệnh:
```bash
python "[hub_path]/.agents/skills/ccba-ai-qc-pccc-audit/scripts/audit_engine.py" \
    --tm "đường/dẫn/đến/thuyet_minh.md" \
    --arch "đường/dẫn/đến/kien_truc.md" \
    --mep "đường/dẫn/đến/mep.md" \
    --gopy "đường/dẫn/đến/pc07.md" \
    --model "qwen-local-primary" \
    --out "Bao_Cao_Tham_Dinh_PCCC.md"
```
*(Nếu không có văn bản góp ý của PC07, truyền một chuỗi rỗng `--gopy ""`)*


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/sop_cdt_tu_tham_dinh.md` | Danh mục SOP tự thẩm tra hồ sơ thiết kế PCCC cho Chủ đầu tư |
| `references/sop_tham_dinh_congan.md` | Danh mục SOP thẩm duyệt thiết kế PCCC với Cơ quan Công an PCCC |
| `references/sop_tham_tra_cqxd.md` | Danh mục SOP thẩm tra quy chuẩn xây dựng và an toàn cháy với Sở Xây dựng |

## 5. Quy Chuẩn Kỹ Thuật PCCC QCVN 06:2022/BXD & Bảng Đối Soát Bậc H.1 (Map 1)
* **Bậc chịu lửa & Chiều cao:** Nhà nhóm F1.3 có chiều cao PCCC > 50m bắt buộc phải thiết kế Bậc chịu lửa Bậc I (Bảng H.1).
* **Kiểm soát khói:** Hành lang dài > 15m không có thông gió tự nhiên bắt buộc phải trang bị hệ thống hút khói cơ khí sự cố và van ngăn khói.
* **Thang bộ thoát nạn:** Nhà có chiều cao PCCC > 28m bắt buộc sử dụng buồng thang bộ không nhiễm khói loại N1 hoặc N2/N3 có hệ thống tăng áp.
