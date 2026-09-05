# Mẫu Biểu: Quyết Định Giao Việc Hợp Đồng Kinh Tế (Chuẩn NĐ 30)

> **Mô tả**: Mẫu Quyết định giao việc thực hiện Hợp đồng Kinh tế nội bộ giữa Viện IBST và Đơn vị thực hiện (Trung tâm CCBA).

---

## 📋 Cấu trúc Dữ liệu JSON Input

```json
{
  "co_quan_chu_quan": "BỘ XÂY DỰNG",
  "co_quan_ban_hanh": "VIỆN KHOA HỌC CÔNG NGHỆ XÂY DỰNG",
  "so_ky_hieu": "{{SO_DECISION}}/QĐ-VKH",
  "dia_danh": "Hà Nội",
  "ngay_thang_nam": "ngày {{NGAY}} tháng {{THANG}} năm {{NAM}}",
  "ten_hop_dong": "{{TEN_HOP_DONG}}",
  "so_hop_dong": "{{SO_HOP_DONG}}",
  "gia_tri_hop_dong": "{{GIA_TRI_HOP_DONG}}",
  "don_vi_thuc_hien": "Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng",
  "ty_le_trich_nop": "{{TY_LE_TRICH_NOP}}",
  "chuc_vu_nguoi_ky": "VIỆN TRƯỞNG",
  "ten_nguoi_ky": "{{TEN_VIEN_TRUONG}}"
}
```

---

## 📝 Nội dung Khung Mẫu (Template Structure)

```markdown
BỘ XÂY DỰNG                                    CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
VIỆN KHOA HỌC CÔNG NGHỆ XÂY DỰNG                Độc lập - Tự do - Hạnh phúc
Số: {{SO_DECISION}}/QĐ-VKH                       Hà Nội, ngày {{NGAY}} tháng {{THANG}} năm {{NAM}}

                                   QUYẾT ĐỊNH
                 Về việc giao việc thực hiện hợp đồng kinh tế

                    VIỆN TRƯỞNG VIỆN KHOA HỌC CÔNG NGHỆ XÂY DỰNG

Căn cứ Quyết định số 1452/QĐ-BXD ngày 30/12/2022 của Bộ Xây dựng về quy định chức năng, nhiệm vụ của Viện KHCN Xây dựng;
Căn cứ Quy chế thực hiện nhiệm vụ dịch vụ kỹ thuật ban hành kèm theo Quyết định số 2235/QĐ-VKH;
Căn cứ Hợp đồng kinh tế số {{SO_HOP_DONG}} ký ngày {{NGAY_HOP_DONG}} về việc {{TEN_HOP_DONG}};
Xét đề nghị của Trưởng phòng KHKT và Giám đốc {{DON_VI_THUC_HIEN}},

                                   QUYẾT ĐỊNH:

Điều 1. Giao {{DON_VI_THUC_HIEN}} chủ trì thực hiện Hợp đồng kinh tế số {{SO_HOP_DONG}} với giá trị hợp đồng là {{GIA_TRI_HOP_DONG}} đồng.

Điều 2. Đơn vị thực hiện có trách nhiệm tuân thủ đúng tiến độ, chất lượng theo thỏa thuận hợp đồng và thực hiện trích nộp nghĩa vụ quản lý Viện là {{TY_LE_TRICH_NOP}}%.

Điều 3. Các ông (bà) Trưởng phòng TCHC, KHKT, TCKT và Giám đốc {{DON_VI_THUC_HIEN}} chịu trách nhiệm thi hành Quyết định này./.

Nơi nhận:                                                   VIỆN TRƯỞNG
- Như Điều 3;                                            (Ký, đóng dấu, ghi rõ họ tên)
- Lưu: VT, KHKT.

                                                          {{TEN_VIEN_TRUONG}}
```
