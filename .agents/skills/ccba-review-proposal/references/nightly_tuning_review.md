# 🌙 Hướng Dẫn Thẩm Định PR Nightly Auto-Tune & Chốt Chặn Goodhart's Law

> Trở về: [SKILL.md](../SKILL.md)

Tài liệu này cung cấp quy chuẩn và quy trình chi tiết cho Maintainer và Review Agent khi thẩm định các Pull Request tự động do hệ thống **Nightly Auto-Tuner Daemon** tạo ra (nhánh có tiền tố `auto-tune/*` hoặc tiêu đề chứa `auto-tune`).

---

## 1. Đọc Bảng Đối Soát Tiến Hóa Kỹ Năng (Evolution Matrix)

Mọi PR Nightly Auto-Tune hợp lệ đều đi kèm một bảng **Evolution Matrix** tổng hợp kết quả đánh giá qua đêm. Agent thẩm định cần thu thập và phân tích dữ liệu này qua một trong hai phương thức:

### 1.1. Đọc từ Nội dung PR (PR Body)
Sử dụng GitHub CLI để trích xuất trực tiếp phần mô tả PR:
```bash
gh pr view <PR_NUMBER> --json body --jq .body
```

### 1.2. Đọc từ Báo Cáo Lưu Trữ Cục Bộ
Nếu cần đối soát chi tiết hơn về token và từng vòng lặp:
- Truy cập thư mục `.md/knowledge/reports/`.
- Mở tệp báo cáo tương ứng theo timestamp của PR:
  `nightly_tuner_report_YYYYMMDD_HHMMSS.md`

### 1.3. Các Chỉ Số Cần Đối Soát
| Chỉ Số | Ý Nghĩa Kỹ Thuật | Ngưỡng An Toàn |
| :--- | :--- | :--- |
| `Điểm Ban Đầu (Baseline)` | Điểm kiểm chuẩn của kỹ năng trước khi tối ưu | Phải khớp với baseline gần nhất trong hệ thống |
| `Điểm Sau Tối Ưu (Final)` | Điểm cao nhất kỹ năng đạt được qua các vòng lặp | Phải $\ge$ Điểm Ban Đầu (Zero-Regression) |
| `Chênh Lệch (Delta)` | Tỷ lệ phần trăm điểm tăng thêm | $> 0.0\%$ (trừ trường hợp kiểm tra khói 100% Perfect) |
| `Số Commits (Commits Kept)` | Số lượng đột biến cải tiến được ghi nhận | $1 - 10$ commits tùy theo số vòng lặp |
| `Tokens Tiêu Thụ` | Tổng prompt và completion tokens sử dụng | Nằm trong trần token budget cho phép |
| `Rào Chắn An Toàn` | Xác nhận Hard Floor & Zero-Regression | Bắt buộc 100% check pass |

---

## 2. Đối Soát Ngữ Nghĩa & Chống Hiện Tượng Nhồi Từ Khóa Ảo (Goodhart Gaming Gate)

Theo **Định luật Goodhart (Goodhart's Law)**: *"Khi một thước đo trở thành mục tiêu, nó sẽ không còn là một thước đo tốt."* Trong quá trình tự động tối ưu hóa prompt qua nhiều vòng lặp, mô hình LLM có xu hướng tìm cách "lách" bộ chấm điểm (Scorer) bằng cách chèn từ khóa bề nổi thay vì nâng cao năng lực giải quyết vấn đề thực chất.

### 2.1. Các Dấu Hiệu Nhận Diện Goodhart Gaming
1. **Comment Rác & Chú Thích Giả Lập:**
   - Xuất hiện comment vô nghĩa dạng HTML comment rác Ratchet Optimization (như `<!--` kèm `Ratchet Optimization Refinement: ... -->`) nhằm lách bộ chấm điểm mà không tạo ra thay đổi hiển thị thực tế.
   - *Quy chuẩn ADR-0058:* Nghiêm cấm hoàn toàn chuỗi này trong toàn bộ catalog kỹ năng.
2. **Nhồi Nhét Từ Khóa (Keyword Stuffing):**
   - Chèn hàng loạt tên văn bản quy phạm pháp luật (VBPL), số hiệu tiêu chuẩn hoặc thuật ngữ chuyên môn vào một khối văn bản rời rạc, không gắn liền với logic hướng dẫn hoặc luồng xử lý của Agent.
   - Ví dụ tiêu cực: Thêm danh sách liệt kê `QCVN 06:2022`, `Nghị định 105/2025` vào cuối file mà không chỉ rõ Agent phải áp dụng điều khoản nào trong trường hợp cụ thể.
3. **Thay Đổi Thuần Khoảng Trắng / Định Dạng:**
   - Commit chỉ thay đổi thụt đầu dòng, ngắt dòng hoặc ký tự khoảng trắng mà không sửa đổi ngữ nghĩa (đã có Shift-Left Pre-PR Gate chặn đứng, nhưng cần rà soát lại nếu lọt qua).
4. **Xóa Bỏ / Biến Dạng Cấu Trúc Đã Chuẩn Hóa:**
   - Làm mất frontmatter YAML, làm hỏng bảng Level 3 Progressive Disclosure, hoặc xóa các ràng buộc bảo mật / governance quan trọng của hệ thống.

### 2.2. Lệnh Soát Chiếu Thay Đổi Ngữ Nghĩa (Semantic Diff Inspection)
Agent thực hiện kiểm tra diff thực chất loại trừ khoảng trắng:
```bash
git diff -w origin/main...HEAD .agents/skills/
```
Rà soát từng khối thay đổi:
- Khối văn bản mới có cung cấp logic nghiệp vụ mạch lạc không?
- Các căn cứ pháp lý hoặc quy chuẩn kỹ thuật có được viện dẫn chính xác, có ngữ cảnh thực tế không?
- Có hiện tượng lặp từ khóa bất thường nhằm tăng điểm regex không?

---

## 3. Quy Trình Đình Chỉ Có Giám Sát (Supervised Halt Protocol)

Khi phát hiện PR `auto-tune` có dấu hiệu Goodhart gaming, tăng điểm ảo, hoặc vi phạm cấu trúc tài liệu, Agent **TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ Ý MERGE**. Agent kích hoạt quy trình Supervised Halt Protocol và cung cấp cho Maintainer **3 tùy chọn xử lý dứt khoát**:

### 🔴 Tùy Chọn 1: Đóng PR Toàn Phần (Reject & Close PR)
- **Khi nào áp dụng:** Toàn bộ các cải tiến trong PR đều là nhồi từ khóa ảo, không mang lại giá trị vận hành thực tế, hoặc gây rối loạn tài liệu hướng dẫn.
- **Thao tác thực hiện:**
  ```bash
  gh pr close <PR_NUMBER> --comment "❌ Đóng PR: Phát hiện hiện tượng nhồi từ khóa ảo (Goodhart gaming) theo quy chuẩn ADR-0058."
  ```
- **Hệ quả:** Nhánh tự động sẽ được dọn dẹp bởi chu kỳ cleanup tự động của Daemon.

### 🟡 Tùy Chọn 2: Tỉa Bớt Commit & Giữ Lại Phần Hợp Lệ (Selective Commit Cherry-pick)
- **Khi nào áp dụng:** PR bao gồm nhiều kỹ năng hoặc nhiều commit, trong đó có những cải tiến thực chất đạt chuẩn (semantic enhancement) và có những commit bị Goodhart gaming.
- **Thao tác thực hiện:**
  1. Tạo nhánh làm việc mới từ `main`:
     ```bash
     git checkout -b review/clean-<PR_NUMBER> main
     ```
  2. Cherry-pick các commit sạch:
     ```bash
     git cherry-pick <VALID_COMMIT_HASH>
     ```
  3. Chạy kiểm chuẩn toàn diện:
     ```bash
     python scripts/governance/audit_skills_hygiene.py --check
     python -m ccba_harness verify-patch --preset skill
     ```
  4. Hợp nhất nhánh sạch vào `main` và đóng PR gốc kèm ghi chú giải thích.

### 🔵 Tùy Chọn 3: Cập Nhật & Siết Chặt Bộ Đề Thi / Scorer (Scorer Hardening)
- **Khi nào áp dụng:** Kỹ năng vượt qua bài thi quá dễ dàng do Scorer quá lỏng lẻo (chỉ kiểm tra regex đơn giản mà thiếu ngữ cảnh kiểm chứng).
- **Thao tác thực hiện:**
  1. Đóng PR hiện tại.
  2. Nâng cấp bộ đề thi trong `.agents/skills/ccba-eval-gate/test_cases/eval_<domain>.json` bổ sung các trường hợp Red-Team và bẫy logic (Anti-traps).
  3. Cập nhật Scorer chuyên biệt trong `packages/ccba-harness/src/ccba_harness/evals/scorers/` để kiểm tra logic ngữ nghĩa thay vì chuỗi đơn thuần.
  4. Xác nhận lại bằng lệnh:
     ```bash
     python -m ccba_harness verify-patch --preset eval
     ```
  5. Đợi chu kỳ Nightly Tuner tiếp theo để hệ thống tự tối ưu lại trên bộ đề thi mới đã được gia cố.

---

## 4. Bảng Kiểm Tra Thẩm Định Nhanh Cho Maintainer (Checklist)

Trước khi bấm Merge bất kỳ PR `auto-tune` nào, Maintainer xác nhận đủ 5 tiêu chí:

- [ ] **1. Evolution Matrix Hợp Lệ:** Điểm số có tăng trưởng thực chất ($\Delta > 0$), không có kỹ năng nào bị sụt giảm điểm (Zero-Regression).
- [ ] **2. Không Có Chuỗi Rác:** Không chứa comment rác HTML Ratchet Optimization hoặc các ghi chú lừa bộ quét.
- [ ] **3. Logic Nghiệp Vụ Chuẩn Mực:** Thay đổi trong prompt làm rõ ràng quy trình, bổ sung quy chuẩn có ngữ cảnh chứ không phải nhồi từ khóa rời rạc.
- [ ] **4. 100% Skills Hygiene Pass:** Chạy `python scripts/governance/audit_skills_hygiene.py --check` đạt 73/73 GREEN, 0 YELLOW, 0 RED.
- [ ] **5. Hard Completion Lock Pass:** Chạy `python -m ccba_harness verify-patch --preset code` và `--preset eval` thoát mã 0.
