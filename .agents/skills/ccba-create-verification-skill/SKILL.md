---
name: ccba-create-verification-skill
description: Khởi tạo và bảo trì kỹ năng kiểm định tự động verify-<app> cho dự án/spoke (ADR-0009 / Upstream Pstack Disciplines).
user-invocable: true
command: /ccba-create-verification-skill
when_to_use: Dùng khi người dùng muốn thiết lập mới hoặc bảo trì, sửa lỗi sai lệch (drift repair) cho bộ kỹ năng kiểm định tự động (verification harness) của một ứng dụng hoặc spoke.
category: governance
gpi:
  s: 4.5
  k: 3.5
  a: 2.0
  p: 1.0
keywords:
- verification
- harness
- test
- quality
- pstack
- verify
- drift
- maintain
argument-hint: '[--app APP_NAME | --mode {scaffold,maintain} | --type {web,api,cli,worker}]'
metadata:
  author: CCBA
  version: 1.2.0
disable-model-invocation: true
bundle: _core
tier: kernel
triggers:
- ccba-create-verification-skill
- create-verification-skill
- tạo verification skill
- thiết lập harness
- verify harness
- maintain-verification-skill
- bảo trì verification skill
- sửa verification skill
- repair verification skill
- harness drift
---

# Kỹ Năng Khởi Tạo & Bảo Trì Bộ Kiểm Định Ứng Dụng (ccba-create-verification-skill)

Kỹ năng này tự động thiết lập bộ kỹ năng kiểm định tự động chuyên biệt `verify-<app>` cho bất kỳ ứng dụng nào trong hệ sinh thái CCBA (Web, REST API, CLI, Worker, hoặc Spoke repository).

Được kế thừa và nâng cấp từ triết lý `create-verification-skill` của Cursor `pstack`, bộ kiểm định này tuân thủ nghiêm ngặt nguyên tắc **Vệ Sinh Spoke (ADR-0044)**: toàn bộ mã kiểm thử và kịch bản thực thi được cô lập bên trong `.agents/skills/verify-<app>/harness/`, tuyệt đối không làm phình thư mục `scripts/` vượt quá giới hạn 15 kịch bản.

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `seam-exempt`. Kỹ năng này là SOP kernel khởi tạo và bảo trì bộ kiểm định ứng dụng `verify-<app>` qua 5 khối chức năng cốt lõi (Clean-Slate, Dual-Mode Server Lifecycle, Deterministic Health Barrier, Evidence-Capture Test Suite, Guaranteed Graceful Cleanup) với 2 chế độ `scaffold` và `maintain`. Kỹ năng cô lập harness trong `.agents/skills/verify-<app>/harness/` theo chuẩn vệ sinh Spoke, không thuộc các Seam dữ liệu ứng dụng.
- **Governance Compliance**: Đạt chuẩn thể chế Tier 2B Standalone Kernel Skill với điểm GPI (S: 4.5, K: 3.5, A: 2.0, P: 1.0) = 20.75 >= 12.0. Cả 2 tệp tài liệu chuyên sâu (`references/features_map_guide.md`, `references/maintain_drift_guide.md`) được bảo tồn nguyên vẹn tại chỉ mục Level 3.

---

## 5 Khối Chức Năng Cốt Lõi Trong Kỹ Năng Kiểm Định `verify-<app>`

Mỗi kỹ năng `verify-<app>` được tạo ra phải bao gồm đầy đủ 5 khối cấu trúc sau:

```mermaid
flowchart TD
    B1["1. Clean-Slate Pre-flight\n(Kiểm tra xung đột port, diệt tiến trình mồ côi)"] --> B2["2. Dual-Mode Server Lifecycle\n(POSIX setsid / Windows Process Group)"]
    B2 --> B3["3. Deterministic Health Barrier\n(Readiness Probe với polling & timeout)"]
    B3 --> B4["4. Evidence-Capture Test Suite\n(Chạy Pytest/Playwright, chụp log/kết quả)"]
    B4 --> B5["5. Guaranteed Graceful Cleanup\n(Finally block dọn sạch tiến trình con)"]
```

### 1. Clean-Slate Pre-flight (Tiền Kiểm Sạch Sẽ)
- Kiểm tra xem cổng dịch vụ (port) mục tiêu có đang bị chiếm dụng bởi tiến trình khác hay không.
- Nếu có tiến trình chiếm dụng ngoài ý muốn, cảnh báo hoặc thực hiện ngắt kết nối an toàn.

### 2. Dual-Mode Server Lifecycle (Quản Trị Vòng Đời Tiến Trình Đa Nền Tảng)
- Khởi động server trong một nhóm tiến trình riêng biệt (Process Group) để đảm bảo có thể dừng toàn bộ cây tiến trình con một cách triệt để khi kết thúc bài test.
- **Quy chuẩn đa hệ điều hành bắt buộc**:
  ```python
  import os
  import subprocess
  import sys

  is_win = sys.platform == "win32"
  kwargs = {}
  if is_win:
      # Windows: Khởi tạo Process Group mới
      kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
  else:
      # Linux / macOS (POSIX): Sử dụng setsid
      kwargs["preexec_fn"] = os.setsid

  proc = subprocess.Popen(server_cmd, **kwargs)
  ```

### 3. Deterministic Health Barrier (Rào Chắn Sẵn Sàng Xác Định)
- Tuyệt đối CẤM dùng `time.sleep(N)` tùy tiện để chờ server khởi động.
- BẮT BUỘC sử dụng vòng lặp kiểm tra HTTP endpoint (ví dụ: gửi request thăm dò readiness probe) với timeout xác định (ví dụ tối đa 15s, thăm dò mỗi 200ms).

### 4. Evidence-Capture Test Suite (Thực Thi Kiểm Thử & Thu Thập Bằng Chứng)
- Chạy toàn bộ các kịch bản kiểm thử (API, UI, hoặc integration tests).
- Lưu giữ kết quả có cấu trúc (JUnit XML, JSON log, hoặc test artifacts) để phục vụ CI/CD và báo cáo nghiệm thu.

### 5. Guaranteed Graceful Cleanup (Dọn Dẹp Đảm Bảo Tuyệt Đối)
- Quá trình dừng server BẮT BUỘC nằm trong khối `finally:` để đảm bảo không để lại tiến trình mồ côi (zombie processes) ngay cả khi bài test thất bại:
  ```python
  try:
      # Chạy test suite...
      pass
  finally:
      if is_win:
          subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], check=False)
      else:
          import signal
          try:
              os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
          except ProcessLookupError:
              pass
  ```

---

## Chế Độ Hoạt Động Kép (Dual-Mode Operation) & Tự Động Nhận Diện

Kỹ năng tự động xác định chế độ vận hành dựa trên hiện trạng hệ thống tệp:
- **Nếu chưa tồn tại `.agents/skills/verify-<app>/harness/`** $\rightarrow$ Kích hoạt **Mode 1: Khởi Tạo Mới (`scaffold`)**.
- **Nếu đã tồn tại `.agents/skills/verify-<app>/harness/`** $\rightarrow$ Kích hoạt **Mode 2: Bảo Trì & Sửa Sai Lệch (`maintain`)**.

---

## Quy Trình Triển Khai Cho AI Agent

### Mode 1 — Khởi Tạo Mới (`scaffold`)
1. **Khảo Sát Ứng Dụng (App Discovery):**
   - Xác định loại ứng dụng: Web (FastAPI, Flask, Next.js), CLI, Worker, hoặc Thư viện.
   - Xác định lệnh khởi động server (nếu có), cổng mặc định, và probe kiểm tra sức khỏe (readiness check hoặc command ping).
   - **Tiêu chí hoàn thành:** Xác định đầy đủ loại ứng dụng, lệnh khởi chạy, cổng lắng nghe, và cơ chế probe sẵn sàng.
2. **Khởi Tạo Cấu Trúc Thư Mục Cục Bộ:**
   - Tạo thư mục `.agents/skills/verify-<app>/`.
   - Tạo thư mục con `.agents/skills/verify-<app>/harness/` chứa các kịch bản thực thi.
   - **Tiêu chí hoàn thành:** Thư mục `.agents/skills/verify-<app>/harness/` được tạo thành công trên hệ thống tệp.
3. **Sinh Tệp Định Nghĩa Kỹ Năng (`verify-<app>/SKILL.md`) & Neo Phiên Bản (`sync_commit`):**
   - Định nghĩa frontmatter chuẩn (`name: verify-<app>`, `category: verification`, v.v.).
   - Ghi nhận rõ trường `sync_commit` (mã commit SHA tại thời điểm xác nhận bộ kiểm định khớp 100% với mã nguồn) và danh mục `covered_paths` (các tệp/hàm cốt lõi được bộ kiểm định bảo vệ).
   - Hướng dẫn các bước chạy kiểm định và đối chiếu trạng thái theo 5 khối cấu trúc.
   - **Tiêu chí hoàn thành:** Tệp `.agents/skills/verify-<app>/SKILL.md` được sinh ra với đầy đủ frontmatter, quy trình 5 khối, trường `sync_commit` và `covered_paths`.
4. **Khởi Tạo Features Map (`features/INDEX.md`):**
   - Lập danh mục các tính năng hiện có của ứng dụng theo chuẩn `features_map_guide.md`.
   - **Tiêu chí hoàn thành:** Tệp `features/INDEX.md` được khởi tạo với bảng ánh xạ các tính năng chính và bài kiểm thử tương ứng.
5. **Chạy Thử Nghiệm Xác Minh & Phép Thử Đột Biến Ngữ Nghĩa (Semantic Mutation Proof — COND-01, COND-02):**
   - Xác nhận cây làm việc sạch tuyệt đối (`git diff --quiet && git diff --cached --quiet`) trước khi thử nghiệm.
   - Thực hiện 1 phép thử **Đột Biến Ngữ Nghĩa (Semantic Mutation)** tạm thời trên mã nguồn (ví dụ: đảo toán tử so sánh biên `>` $\to$ `>=`, đảo ngược cờ boolean, hoặc bỏ qua bước cập nhật trạng thái; tuyệt đối cấm chèn lỗi cú pháp thô hay lệnh `raise` ở đầu hàm), chạy `verify-<app>` để chứng minh bộ kiểm định bắt được lỗi và lưu lại nhật ký lỗi phản chứng (*counterexample failure log*).
   - Hoàn nguyên tự động (`git checkout -- <mutated_files>`), kiểm tra `git status --porcelain` rỗng, và chạy lại kịch bản harness xác nhận thoát sạch với exit code 0.
   - **Tiêu chí hoàn thành:** Bộ kiểm định bắt được lỗi đột biến ngữ nghĩa (có counterexample log), mã nguồn được hoàn nguyên 100% sạch sẽ và lần chạy chính thức thoát với mã exit code 0.

### Mode 2 — Bảo Trì & Sửa Sai Lệch Drift (`maintain`)
1. **Kiểm Tra Nguồn Gốc Thay Đổi & Lịch Sử Từ `sync_commit` (Pre-Remediation Provenance Check - COND-01):**
   - Đối chiếu `git diff <sync_commit>..HEAD` trên các tệp thuộc `covered_paths`: nếu thay đổi là chủ đích thiết kế (đổi route, port, schema có bằng chứng trong PR/commit/ADR) $\rightarrow$ sửa `harness/` (trạng thái `updated`); nếu là lỗi hồi quy ngoài ý muốn (regression) $\rightarrow$ **CẤM SỬA `harness/`**, gán trạng thái `bug`, giữ nguyên bài test và yêu cầu sửa mã nguồn ứng dụng.
   - **Tiêu chí hoàn thành:** Phân loại chính xác nguyên nhân lỗi thuộc 1 trong 4 trạng thái chuẩn (`in_sync`, `updated`, `bug`, `blocked`) theo `references/maintain_drift_guide.md`.
2. **Đối Chiếu Bề Mặt Tính Năng (Surface Diff):**
   - So sánh các route/command hiện hành với tài liệu `features/INDEX.md` để khoanh vùng điểm lệch.
   - **Tiêu chí hoàn thành:** Xác định danh sách các điểm trôi lệch giữa code và tài liệu.
3. **Thực Thi Quan Sát Thực Tế (Observed Live Pass):**
   - Chạy 1 pass harness đại diện để ghi nhận log lỗi thực tế thay vì suy đoán cảm tính.
   - **Tiêu chí hoàn thành:** Thu thập toàn văn stack trace và log lỗi thực tế từ lần chạy kiểm định.
4. **Khắc Phục Tận Gốc Trong Thư Mục `harness/`:**
   - Cập nhật lệnh CLI, port, timeout, probe URL hoặc schema assertions bên trong `.agents/skills/verify-<app>/harness/`. Tuyệt đối không tạo file rác tại thư mục gốc `scripts/` (ADR-0044).
   - **Tiêu chí hoàn thành:** Kịch bản trong `harness/` và `features/INDEX.md` được cập nhật đồng bộ.
5. **Kiểm Chứng Đột Biến Ngữ Nghĩa, Cập Nhật `sync_commit` & Xác Minh Thoát Sạch (COND-01, COND-02):**
   - Khi cập nhật harness (`updated`), bắt buộc thực hiện phép thử **Semantic Mutation Proof** (xác nhận `git diff` sạch $\to$ tiêm đột biến ngữ nghĩa trên nhánh mã mới để chứng minh harness mới không bị mất khả năng bắt lỗi $\to$ `git checkout -- <mutated_files>` và xác nhận `git status --porcelain` rỗng).
   - Chỉ tiến hành nâng `sync_commit` lên commit hiện tại khi đạt kết quả `in_sync` hoặc `updated` và bài kiểm định thoát với exit code 0. Tuyệt đối CẤM nâng `sync_commit` khi kết quả là `bug` hoặc `blocked`.
   - **Tiêu chí hoàn thành:** Harness vượt qua Semantic Mutation Proof, thoát sạch với exit code 0, không còn tiến trình zombie và `sync_commit` được cập nhật chuẩn xác.

---

## Progressive Disclosure & Reference Index (Level 3)

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/features_map_guide.md` | Hướng dẫn thiết lập và duy trì Features Map (`features/INDEX.md`) cho ứng dụng |
| `references/maintain_drift_guide.md` | Hướng dẫn phát hiện & khắc phục 4 dạng drift kiểm định, ma trận 4 trạng thái (`in_sync`, `updated`, `bug`, `blocked`), Semantic Mutation Proof và bảo vệ Spoke cleanliness |

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này tuân thủ Hiến pháp Nền tảng CCBA (ADR-0009 & ADR-0044).*
