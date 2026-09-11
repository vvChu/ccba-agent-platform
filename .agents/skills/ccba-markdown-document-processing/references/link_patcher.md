# Link Patcher Reference

Tài liệu này quy định quy tắc chuẩn hóa các liên kết tương đối giữa tệp văn bản chính và các tệp phụ lục.

---

## 1. Quy tắc Đặt Tiền Tố (SOP Rules)

1. **Tiền tố chuẩn:** Các liên kết phụ lục tại tệp nghị định chính phải bắt đầu bằng `./appendices/` thay vì `appendices/` hoặc đường dẫn tuyệt đối `file:///`.
   * *Đúng:*
     ```markdown
     [Phụ lục I](<./appendices/nghi_dinh_217-phu_luc_01.md>)
     ```
   * *Sai:*
     ```markdown
     [Phụ lục I](<appendices/nghi_dinh_217-phu_luc_01.md>)
     ```

2. **Đồng bộ Index:** Khi có phụ lục mới được thêm vào hoặc đổi tên, phải đồng bộ ngay sang tệp mục lục chính `index.md` và phân nhóm theo đúng Nghị định cha.

---

## 2. Lệnh CLI Tự Động

```bash
python -m mdconverter.cli patch-links --file [đường_dẫn_tệp_markdown]
```
