---
name: ccba-create-verification-skill
description: Khởi tạo kỹ năng kiểm định tự động verify-<app> cho dự án/spoke (ADR-0009 / Upstream Pstack Disciplines).
user-invocable: true
command: /ccba-create-verification-skill
when_to_use: Dùng khi người dùng muốn thiết lập hoặc cấu hình bộ kỹ năng kiểm định tự động (deterministic verification harness) cho một ứng dụng hoặc spoke mới.
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
argument-hint: '[--app APP_NAME | --type {web,api,cli,worker}]'
metadata:
  author: CCBA
  version: 1.0.0
disable-model-invocation: true
bundle: _governance
tier: kernel
triggers:
- ccba-create-verification-skill
- create-verification-skill
- tạo verification skill
- thiết lập harness
- verify harness
---

# Kỹ Năng Khởi Tạo Bộ Kiểm Định Ứng Dụng (ccba-create-verification-skill)

Kỹ năng này tự động thiết lập bộ kỹ năng kiểm định tự động chuyên biệt `verify-<app>` cho bất kỳ ứng dụng nào trong hệ sinh thái CCBA (Web, REST API, CLI, Worker, hoặc Spoke repository).

Được kế thừa và nâng cấp từ triết lý `create-verification-skill` của Cursor `pstack`, bộ kiểm định này tuân thủ nghiêm ngặt nguyên tắc **Vệ Sinh Spoke (ADR-0044)**: toàn bộ mã kiểm thử và kịch bản thực thi được cô lập bên trong `.agents/skills/verify-<app>/harness/`, tuyệt đối không làm phình thư mục `scripts/` vượt quá giới hạn 15 kịch bản.

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

## Quy Trình Triển Khai Cho AI Agent

Khi người dùng yêu cầu `/ccba-create-verification-skill`:

1. **Khảo Sát Ứng Dụng (App Discovery):**
   - Xác định loại ứng dụng: Web (FastAPI, Flask, Next.js), CLI, Worker, hoặc Thư viện.
   - Xác định lệnh khởi động server (nếu có), cổng mặc định, và probe kiểm tra sức khỏe (readiness check hoặc command ping).
   - **Tiêu chí hoàn thành:** Xác định đầy đủ loại ứng dụng, lệnh khởi chạy, cổng lắng nghe, và cơ chế probe sẵn sàng.
2. **Khởi Tạo Cấu Trúc Thư Mục Cục Bộ:**
   - Tạo thư mục `.agents/skills/verify-<app>/`.
   - Tạo thư mục con `.agents/skills/verify-<app>/harness/` chứa các kịch bản thực thi.
   - **Tiêu chí hoàn thành:** Thư mục `.agents/skills/verify-<app>/harness/` được tạo thành công trên hệ thống tệp.
3. **Sinh Tệp Định Nghĩa Kỹ Năng (`verify-<app>/SKILL.md`):**
   - Định nghĩa frontmatter chuẩn (`name: verify-<app>`, `category: verification`, v.v.).
   - Hướng dẫn các bước chạy kiểm định và đối chiếu trạng thái.
   - **Tiêu chí hoàn thành:** Tệp `.agents/skills/verify-<app>/SKILL.md` được sinh ra với đầy đủ frontmatter và quy trình 5 khối.
4. **Khởi Tạo Features Map (`features/INDEX.md`):**
   - Lập danh mục các tính năng hiện có của ứng dụng theo chuẩn `features_map_guide.md`.
   - **Tiêu chí hoàn thành:** Tệp `features/INDEX.md` được khởi tạo với bảng ánh xạ các tính năng chính và bài kiểm thử tương ứng.
5. **Chạy Thử Nghiệm Xác Minh (Dry-Run Verification):**
   - Thực thi thử kịch bản harness để xác nhận hệ thống có thể khởi động, chạy probe, và dọn dẹp sạch sẽ với exit code 0.
   - **Tiêu chí hoàn thành:** Kịch bản harness thực thi dry-run thành công và thoát với mã exit code 0.

---

## Progressive Disclosure & Reference Index (Level 3)

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/features_map_guide.md` | Hướng dẫn thiết lập và duy trì Features Map (`features/INDEX.md`) cho ứng dụng |

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này tuân thủ Hiến pháp Nền tảng CCBA (ADR-0009 & ADR-0044).*
