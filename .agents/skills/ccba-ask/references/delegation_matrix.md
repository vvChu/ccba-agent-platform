# Ma Trận Định Tuyến Ủy Quyền 3 Cấp (3-Tier Delegation Matrix)

> **Tài liệu tham chiếu bắt buộc của `/ccba-ask`.** Trước mọi lời gọi `invoke_subagent`, `run_workflow`, hoặc [`/ccba-teamwork`](../../ccba-teamwork/SKILL.md), Agent bắt buộc nạp tệp này và tuân thủ nguyên vẹn các khóa an toàn dưới đây.

---

## Phân Cấp Điều Phối Tăng Dần

1. **Cấp 1 — `invoke_subagent` (Đơn lẻ / Kiểm chứng cục bộ):**
   - Dùng cho **1–2 tác vụ đọc hoặc kiểm thử cô lập** theo `ADR-0035`.
   - **Khóa an toàn:** `depth limit = 1` (tuyệt đối không khởi tạo subagent lồng nhau); giữ mặc định `Model="inherit"` trừ khi người dùng chủ động yêu cầu model khác.

2. **Cấp 2 — `run_workflow` (Khảo sát Chỉ Đọc Theo Lô — Progressive Enhancement):**
   - Chỉ kích hoạt tùy chọn khi cần rà soát diện rộng **$> 3$ mục độc lập** trên môi trường có công cụ `run_workflow`.
   - **Khóa an toàn bắt buộc:**
     - Mọi lời gọi `agent(...)` phải truyền tường minh `type_name="research"` ngay tại constructor (**cấm** để mặc định `type_name="self"`) và `workspace="inherit"` (**cấm** `workspace="branch"`).
     - Chỉ sử dụng đúng **3 công cụ đọc (`view_file`, `grep_search`, `read_resource`)** — **cấm** cấp `run_command`, **cấm** ghi/sửa file, **cấm** gọi Git.
     - Giữ `depth limit = 1` (chạy test cô lập chỉ thuộc `Success Auditor` hoặc bước xác minh kiểm thử độc lập).
     - Chia lô `parallel` tối đa **3 tác nhân/lô** bọc tuần tự trong `pipeline`.
     - **Mọi nhánh `parallel` bắt buộc gọi `finish` khi hoàn tất** (1 nhánh lỗi hoặc thiếu `finish` sẽ hủy toàn bộ lô).
     - Cho phép gán `model="flash"` hoặc `"flash_lite"` cho bước quét bề mặt.
   - **Fallback đa nền tảng:** Trên các nền tảng không có `run_workflow` (Claude Code, Cursor, CLI), lùi về `invoke_subagent` (tối đa `2` song song) hoặc Python CLI thuần.

3. **Cấp 3 — [`/ccba-teamwork`](../../ccba-teamwork/SKILL.md) (Thực thi Sửa Mã Nguồn Đa Seam):**
   - Mọi tác vụ sinh thay đổi mã nguồn đa gói/đa bộ môn phải điều phối qua [`/ccba-teamwork`](../../ccba-teamwork/SKILL.md) (`invoke_subagent` + **Single-Writer Engine `apply_worker_patch.py`**).
   - Giữ nguyên `Model="inherit"` cho các Workers sinh patch.

---

## Bảng Quyết Định Nhanh

| Quy mô & Bản chất tác vụ | Cấp điều phối | Quyền ghi mã nguồn | Mô hình mặc định |
| :--- | :--- | :---: | :--- |
| 1–2 mục đọc hoặc kiểm thử cô lập | Cấp 1 (`invoke_subagent`) | Không | `inherit` |
| $> 3$ mục khảo sát chỉ đọc song song | Cấp 2 (`run_workflow`, `type_name="research"`) | Cấm tuyệt đối | `flash` / `flash_lite` |
| Sửa mã nguồn đa seam / đa tệp song song | Cấp 3 ([`/ccba-teamwork`](../../ccba-teamwork/SKILL.md)) | Qua Single-Writer `apply_worker_patch.py` | `inherit` |

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
