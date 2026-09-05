# Mẫu Biểu: Tờ Trình Ký Tiếp Hợp Đồng Lao Động (Chuẩn NĐ 30)

> **Mô tả**: Mẫu Tờ trình đề xuất Viện trưởng Viện KHCN Xây dựng ký tiếp hợp đồng lao động cho cán bộ Trung tâm CCBA.

---

## 📋 Cấu trúc Dữ liệu JSON Input

```json
{
  "co_quan_chu_quan": "BỘ XÂY DỰNG",
  "co_quan_ban_hanh": "TRUNG TÂM TƯ VẤN VÀ ỨNG DỤNG BIM TRONG XÂY DỰNG",
  "so_ky_hieu": "{{SO_TTR}}/TTr-BIM",
  "dia_danh": "Hà Nội",
  "ngay_thang_nam": "ngày {{NGAY}} tháng {{THANG}} năm {{NAM}}",
  "trich_yeu": "Về việc: đề nghị ký tiếp hợp đồng lao động cho cán bộ",
  "kinh_gui": ["Ông Viện trưởng Viện KHCN Xây dựng", "Ông Trưởng phòng Tổ chức - Hành chính"],
  "thong_bao_tchc": "Thông báo số {{SO_TB}}/TB-TCHC ngày {{NGAY_TB}}",
  "danh_sach_can_bo": [
    {
      "ho_ten": "{{HO_TEN_CAN_BO}}",
      "loai_hd_de_xuat": "Hợp đồng xác định thời hạn 12 tháng"
    }
  ],
  "chuc_vu_nguoi_ky": "GIÁM ĐỐC",
  "ten_nguoi_ky": "{{TEN_GIAM_DOC_BIM}}"
}
```

---

## 📝 Nội dung Khung Mẫu (Template Structure)

```markdown
BỘ XÂY DỰNG                                    CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
TRUNG TÂM TƯ VẤN VÀ ỨNG DỤNG BIM                Độc lập - Tự do - Hạnh phúc
Số: {{SO_TTR}}/TTr-BIM                           Hà Nội, ngày {{NGAY}} tháng {{THANG}} năm {{NAM}}

                                   TỜ TRÌNH
            Về việc: đề nghị ký tiếp hợp đồng lao động cho cán bộ

Kính gửi:
- Ông Viện trưởng Viện KHCN Xây dựng;
- Ông Trưởng phòng Tổ chức - Hành chính.

Căn cứ Thông báo số {{SO_TB}}/TB-TCHC ngày {{NGAY_TB}} của phòng Tổ chức hành chính Viện KHCN Xây dựng về việc Hết thời hạn Hợp đồng lao động;
Căn cứ nhu cầu nhân sự để thực hiện các nhiệm vụ của Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.

Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng kính đề nghị Viện trưởng xem xét ký tiếp hợp đồng lao động với cán bộ có tên sau:

Ông (Bà): {{HO_TEN_CAN_BO}}

Trong thời gian công tác tại Viện KHCN Xây dựng, đơn vị nhận thấy cán bộ đáp ứng tốt yêu cầu công việc được giao. Xét nguyện vọng và mong muốn làm việc lâu dài tại Viện, Trung tâm trình Viện trưởng xem xét ký tiếp Hợp đồng lao động với thời hạn và hình thức như đề xuất ở trên.

Trung tâm kính trình Viện trưởng xem xét, quyết định.
Trân trọng cảm ơn!

Nơi nhận:                                                   GIÁM ĐỐC
- Như trên;                                              (Ký, đóng dấu, ghi rõ họ tên)
- Lưu: VT, BIM.

                                                        {{TEN_GIAM_DOC_BIM}}
```
