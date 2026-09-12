---
name: ccba-sync-upstream
description: Kiểm tra cập nhật và thẩm tra tính năng thượng nguồn (ADR-0057 Radar)
  kết hợp kích hoạt 1-Click Port qua /ccba-xia.
metadata:
  version: "1.1.0"
  author: "CCBA Hub"
disable-model-invocation: true
bundle: _core
tier: kernel
user-invocable: true
command: /ccba-sync-upstream
gpi:
  s: 4.0
  k: 3.0
  a: 3.0
  p: 1.0
triggers:
- sync-upstream
- ccba-sync-upstream
- sync upstream
- đồng bộ tri thức
- claudekit
- mattpocock
- check update
---

# Kỹ năng: Radar Thượng Nguồn & Cầu Nối Porting (Upstream Radar & Handshake)

Kỹ năng này vận hành hệ thống Radar tự động giám sát các kho chứa thượng nguồn (được cấu hình linh hoạt tại [`.md/knowledge/upstream_sources.yaml`](../../../.md/knowledge/upstream_sources.yaml)), kiểm tra bản quyền, thẩm tra tính năng mới theo **Thể chế ADR-0057 & RES-2026-ARCH-001 v1.2 (Khung Quyết Định Phân Rã Hai Giai Đoạn)** qua AI Gateway và tự động sinh lệnh **1-Click Porting** với `/ccba-xia`.

---

## 🚀 Các Cờ CLI Hỗ Trợ (Command Line Flags)

Hệ thống cung cấp các cờ dòng lệnh linh hoạt phục vụ cả tự động hóa lẫn trinh sát thủ công:

| Cờ CLI | Ý nghĩa & Hành vi |
| :--- | :--- |
| `--check-only` | Chỉ kiểm tra SHA, tải repo và liệt kê tài nguyên/tệp thay đổi mà không gọi AI Gateway đánh giá |
| `--scan-all` | Quét toàn bộ tài nguyên trong kho nguồn (bỏ qua điều kiện trùng SHA commit) |
| `--repo <name>` | Chỉ định kho nguồn cụ thể cần kiểm tra (ví dụ: `--repo claudekit-marketing`, `claudekit-engineer`, `mattpocock-skills`) |
| `--fast` / `--offline` | Chế độ ngoại tuyến: sử dụng clone cục bộ sẵn có, không gọi mạng `fetch`/`clone`, tận dụng cache đánh giá |
| `--limit <N>` | Giới hạn tối đa $N$ tài nguyên được đánh giá trong mỗi kho (tránh cạn quota API) |

Ví dụ kích hoạt:
```powershell
# Trinh sát nhanh không đánh giá
python scripts/spoke/check_claudekit_updates.py --check-only

# Quét toàn bộ kỹ năng của một repo ở chế độ offline
python scripts/spoke/check_claudekit_updates.py --scan-all --repo claudekit-marketing --fast --limit 10
```

---

## 🛡️ Cơ Chế Vận Hành & Tự Chữa Lành (Self-Healing & Safety)

1. **Khóa Mutex `upstream_sync.lock`:** Tự động tạo tệp khóa tại `.md/scratch/upstream_sync.lock` ngăn chặn xung đột tiến trình nền khi nhiều phiên làm việc cùng khởi động. Khóa áp dụng timeout 300s (KISS) tự động dọn dẹp khóa chết (stale lock).
2. **Tự chữa lành Git `index.lock`:** Tự động phát hiện và xóa tệp `.git/index.lock` tồn đọng sau sự cố crash/mất điện hoặc server restart đột ngột.
3. **Clean Clone Fallback:** Khi kho lưu trữ cục bộ bị hỏng chỉ mục (corrupted repository) khiến `git fetch` hoặc `git reset` thất bại, hệ thống tự động dọn dẹp an toàn với `stat.S_IWRITE` (vượt qua rào cản Read-Only trên Windows) và clone lại từ đầu.
4. **Khử Bẫy Khởi Tạo "Zero-Scan Init Trap":** Khi kho mới clone lần đầu chưa có `local_sha`, hệ thống tự động chuyển sang quét khởi tạo toàn diện thay vì kết thúc sớm.
5. **Bộ Phân Giải Đa Năng (Multi-Resource Resolver):** Tự động phát hiện kỹ năng phân cấp lồng nhau (nested skills như `document-skills/docx`, `document-skills/pptx`), đồng thời phân biệt rạch ròi giữa **Domain Workflows** (Tier 3 Composite Orchestrator) và **Governance Rules** (Tier 2A Progressive Reference).
6. **Khử Trùng Lặp Mờ & Bộ Nhớ Đệm Cache:** Tự động loại trừ prefix (`ck-`, `ccba-`), tra cứu `UPSTREAM_ALIAS_MAP` và lưu kết quả đánh giá tại `.md/scratch/upstream_eval_cache.json` để tối ưu tốc độ phản hồi và tiết kiệm token.

---

## Quy trình 3 Nhịp (Process)

### Nhịp 1: Trinh sát & Radar Cập nhật (Recon & Diff Radar)
- Chạy script Python để tự động clone/fetch các kho chứa thượng nguồn về `.md/scratch/repos/` ở chế độ kiểm tra:
  ```powershell
  python scripts/spoke/check_claudekit_updates.py --check-only
  ```
- **Kiểm tra Bản quyền (License Audit):** Tự động phân loại giấy phép repo nguồn (PERMISSIVE, COPYLEFT, PROPRIETARY, UNKNOWN).
- **Tiêu chí hoàn thành:** Script chạy thành công với exit code 0. Toàn bộ kho nguồn được cập nhật, in ra danh sách thay đổi và SHA tương ứng.
- **Cơ chế tự chữa lành (Self-Healing):** Nếu gặp lỗi Git index corruption hoặc đứt kết nối mạng, Agent tự động dọn dẹp stale `index.lock` hoặc kích hoạt Clean Clone fallback an toàn.

### Nhịp 2: Thẩm tra Thể chế ADR-0057 & RES-2026-ARCH-001 v1.2 (Constitutional Evaluation)
- Hỏi ý kiến người dùng trước khi quét sâu bằng AI: *"Tôi tìm thấy N file mới. Bạn có muốn kích hoạt AI Gateway thẩm tra theo thể chế ADR-0057 (Khung Quyết Định Phân Rã Hai Giai Đoạn & Radar GPI) để cập nhật báo cáo khuyến nghị không?"*
- Nếu người dùng đồng ý, chạy script thẩm tra:
  ```powershell
  python scripts/spoke/check_claudekit_updates.py
  ```
- **Tiêu chí phân tầng của AI Gateway:**
  * **Zero-Duplicate Check:** Đối chiếu với danh mục kỹ năng hiện có trong `catalog.yaml` bằng thuật toán khử trùng lặp mờ.
  * **Khung Quyết Định Phân Rã Hai Giai Đoạn (ADR-0057):**
    - Cổng 0 (Determinism Gate): Tác vụ xác định 100% -> **Tier 1: Package Function / Deep Seam** trong `packages/*/src/`.
    - Cổng 1 (Orchestration Gate): Tác vụ đa tác tử/checkpoints/HITL -> **Tier 3: Composite Orchestrator** trong `.agents/workflows/`.
    - Giai đoạn 2 (Chỉ số GPI): $GPI < 12.0$ -> **Tier 2A: Progressive Reference** trong `references/*.md`; $GPI \ge 12.0$ -> **Tier 2B: Standalone Kernel Skill** trong `.agents/skills/ccba-<name>/`.
  * **Đánh giá tương thích:** Khả năng chuyển đổi từ TS/Node sang chuẩn Python Monorepo (`ruff`, `mypy`, `pytest`).
- **Tiêu chí hoàn thành:** Báo cáo [port_recommendations.md](../../../.md/knowledge/port_recommendations.md) được cập nhật và bảo vệ nguyên vẹn vùng ghi chú của kỹ sư (`Parse-Protection`).

### Nhịp 3: Chuyển giao Kiểm soát sang `/ccba-xia` (1-Click Port Handshake)
- Đọc nội dung cập nhật tại `port_recommendations.md` và trình bày tóm tắt cho người dùng.
- Hiển thị cú pháp gọi lệnh `/ccba-xia` trỏ trực tiếp đường dẫn cục bộ tương ứng với từng kỹ năng được khuyến nghị, ví dụ:
  ```text
  /ccba-xia .md/scratch/repos/claudekit-marketing document-skills/docx --port
  ```
- Kỹ sư kích hoạt lệnh `/ccba-xia` để khởi chạy quy trình 6 Pha (đặc biệt là Hard Gate Pha 4 chống hallucination).
- **Tiêu chí hoàn thành:** Người dùng nhận được bảng khuyến nghị kèm liên kết lệnh 1-Click Porting rõ ràng.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
