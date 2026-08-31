---
id: 215
title: "feat(hub-spoke): Standardize Hub-Spoke Interactions, Spoke Cleanliness Gate & sync_spoke Enum Aliasing"
state: "needs-triage"
labels:

assignee: "none"
created_at: "2026-08-23T10:16:59Z"
updated_at: "2026-08-23T11:30:35Z"
---

# 📖 Mô tả (Description)
## RFC: Standardize Hub-Spoke Interactions, Cleanliness Gate & sync_spoke Enum Aliasing

### 1. Bối cảnh & Vấn đề (Context & Problem):
Từ thực tế vận hành và đúc rút sau quá trình dọn dẹp, chuẩn hóa tại Spoke `ccba-legal-knowledge`:
1. **Lệch kiểu dự án (Project Type Enum Mismatch):** Khi Spoke điền `type: "Kho Tri thức Pháp lý & Quy chuẩn"` trong `.md/workspace_context.yaml`, lệnh `sync_spoke.py` bị văng lỗi do không khớp chính xác enum `"Pháp điển"` trong `catalog.yaml`.
2. **Tích tụ Script tạm thời (Ephemeral Script Accumulation):** Các Spoke dễ tích tụ hàng chục script one-off (`fix_*`, `audit_*`, `build_*`) và script prototype trùng lặp với Hub packages nếu thiếu rào chắn kiểm soát thư mục `scripts/`.
3. **Thiếu Blueprint Archetype cho Knowledge Spokes:** `ccba-init-spoke` hiện tập trung vào archetypes software/consulting/qc, thiếu template khởi tạo chuẩn cho `knowledge_corpus` (`Pháp điển`) dẫn đến cấu trúc không đồng nhất từ đầu.
4. **2 Nhánh Proposal Đang Chờ Duyệt trên Hub:** Nhánh `proposal/tvpl-crawler-security-and-rate-limiting` (commit `970a0bc`) và `proposal/okf-v22-cleaners-and-legal-advisor` đã hoàn tất unit tests 100% nhưng chưa được merge vào Hub `main`.

---

### 2. Đề xuất giải pháp (RFC Proposal):

#### A. Nâng cấp `sync_spoke.py` với Alias & Fuzzy Matching:
- Bổ sung bảng bí danh (Synonyms Mapping) trong `scripts/spoke/sync.py` để tự động ánh xạ các tên gọi phổ biến về enum chuẩn:
  - `"Kho Tri thức Pháp lý"`, `"Pháp lý & Quy chuẩn"` -> `"Pháp điển"`.
- Bổ sung gợi ý thông minh (*Did you mean?*) khi Spoke cấu hình sai enum thay vì throw unhandled error.

#### B. Đóng gói Pre-commit Hook `check_spoke_cleanliness.py` cho Spokes (ADR 0044 §7):
- Hub phân phối script `scripts/spoke/check_spoke_cleanliness.py` qua `/ccba-update-spoke` để tự động:
  - Giới hạn <= 15 core files trong thư mục `scripts/`.
  - Cảnh báo và yêu cầu chuyển script fix/audit một lần vào `.md/archive/legacy_scripts/` hoặc `.md/scratch/`.
  - Kiểm tra rào chắn không duplicate mã nguồn đã có trong `packages/` của Hub.

#### C. Thêm Blueprint Archetype `knowledge_corpus` vào `/ccba-init-spoke`:
- Chuẩn hóa template tạo Spoke tri thức mới với sẵn cấu trúc 15 core files & thin wrappers kế thừa `packages/ccba-legal-intel` và `packages/ccba-ai`.

#### D. Duyệt và Merge 2 Nhánh Proposals trên Hub:
- Merge `proposal/tvpl-crawler-security-and-rate-limiting` (Hardening credentials + TVPL Rate Limiter + Jitter) vào Hub `main`.
- Merge `proposal/okf-v22-cleaners-and-legal-advisor` vào Hub `main`.

---

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [ ] `sync_spoke.py` hỗ trợ alias mapping và gợi ý enum thân thiện khi chạy `--dry-run` / `--apply`.
- [ ] Script `check_spoke_cleanliness.py` được phân phối tự động tới các Spoke Python qua `/ccba-update-spoke`.
- [ ] `/ccba-init-spoke` hỗ trợ archetype `knowledge_corpus` (`Pháp điển`).
- [ ] Hoàn thành review và merge nhánh `proposal/tvpl-crawler-security-and-rate-limiting` vào Hub `main`.

---
*Được đề xuất tự động từ Spoke `ccba-legal-knowledge` qua workflow `/ccba-issue-to-hub`.*


---

# 💬 Thảo luận (Discussion Log)
*(Chưa có thảo luận)*
