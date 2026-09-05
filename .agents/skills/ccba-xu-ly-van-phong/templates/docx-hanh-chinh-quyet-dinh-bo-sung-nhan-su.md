# Mẫu Biểu: Quyết Định Bổ Sung Nhân Sự Đoàn TVGS (Chuẩn NĐ 30)

> **Mô tả**: Mẫu Quyết định của Viện trưởng Viện KHCN Xây dựng (IBST) về việc thành lập / bổ sung nhân sự Đoàn Tư vấn Giám sát (TVGS).

---

## 📋 Cấu trúc Dữ liệu JSON Input

```json
{
  "co_quan_chu_quan": "BỘ XÂY DỰNG",
  "co_quan_ban_hanh": "VIỆN KHOA HỌC CÔNG NGHỆ XÂY DỰNG",
  "so_ky_hieu": "{{SO_DECISION}}/QĐ-VKH",
  "dia_danh": "Hà Nội",
  "ngay_thang_nam": "ngày {{NGAY}} tháng {{THANG}} năm {{NAM}}",
  "trich_yeu": "Về việc: bổ sung nhân sự Đoàn TVGS thực hiện hợp đồng số {{SO_HOP_DONG}}",
  "ben_a": "{{TEN_BEN_A}}",
  "dia_diem_du_an": "{{DIA_DIEM_DU_AN}}",
  "danh_sach_nhan_su": [
    {
      "stt": 1,
      "ho_ten": "{{HO_TEN_1}}",
      "chuc_danh": "Trưởng đoàn TVGS",
      "chung_chi_hanh_nghe": "{{CC_HANH_NGHE_1}}"
    }
  ],
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
    Về việc: bổ sung nhân sự Đoàn TVGS thực hiện hợp đồng số {{SO_HOP_DONG}}

                    VIỆN TRƯỞNG VIỆN KHOA HỌC CÔNG NGHỆ XÂY DỰNG

Căn cứ Quyết định số 1452/QĐ-BXD ngày 30/12/2022 của Bộ trưởng Bộ Xây dựng về quy định chức năng, nhiệm vụ, quyền hạn của Viện KHCN Xây dựng;
Căn cứ Quy chế thực hiện Nhiệm vụ Khoa học công nghệ và Triển khai dịch vụ kỹ thuật của Viện KHCN Xây dựng;
Căn cứ Hợp đồng số {{SO_HOP_DONG}} ký giữa {{TEN_BEN_A}} và Viện Khoa học Công nghệ Xây dựng (IBST) về việc {{NOI_DUNG_TVGS}} tại {{DIA_DIEM_DU_AN}};
Xét đề nghị của Giám đốc Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng,

                                   QUYẾT ĐỊNH:

Điều 1. Bổ sung nhân sự Đoàn Tư vấn giám sát thực hiện Hợp đồng số {{SO_HOP_DONG}}. Danh sách cán bộ gồm các Ông (Bà) có tên trong Danh sách kèm theo Quyết định này.

Điều 2. Nhiệm vụ của các thành viên được bổ sung quy định tại Danh sách Đoàn tư vấn giám sát kèm theo.

Điều 3. Các ông (bà) Trưởng phòng TCHC, KHKT, TCKT, Giám đốc Trung tâm TV&ƯD BIM trong xây dựng và các cán bộ có tên chịu trách nhiệm thi hành Quyết định này./.

Nơi nhận:                                                   VIỆN TRƯỞNG
- Như Điều 3;                                            (Ký, đóng dấu, ghi rõ họ tên)
- Lưu: VT, TCHC.

                                                          {{TEN_VIEN_TRUONG}}
```
