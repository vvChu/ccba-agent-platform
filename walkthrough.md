# CCBA Architectural Walkthrough — Candidates 1, 2 & 3 Implementations

Tài liệu này tóm tắt kết quả thực hiện cải tiến kiến trúc Candidate 1, Candidate 2 và Candidate 3 trên dự án CCBA Platform, kèm theo kết quả đối soát các đóng góp của Copilot.

---

## Candidate 1: Làm sâu `CCBANotebookLMClient` và Đóng gói Artifact Flow

### Các thay đổi đã thực hiện

#### 1. Phẳng hóa `CCBANotebookLMClient`
*   **Địa điểm sửa đổi**: [_client.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-notebooklm/src/ccba_notebooklm/_client.py)
*   **Chi tiết**:
    *   Sửa đổi phương thức `__aenter__` trả về trực tiếp đối tượng `self` (`CCBANotebookLMClient`) thay vì client thô của thư viện bên thứ ba.
    *   Bổ sung thuộc tính `raw_client` để giữ tính tương thích ngược khi cần.
    *   Triển khai trực tiếp 15+ API phẳng để gom các dịch vụ con bên dưới (`sources`, `notebooks`, `sharing`, `settings`, `chat`...):
        *   `list_notebooks`, `create_notebook`, `delete_notebook`
        *   `list_sources`, `delete_source`, `add_file_source`, `add_url_source`
        *   `set_notebook_public`, `get_share_url`
        *   `get_account_tier`, `get_account_limits`
        *   `ask_chat`
    *   Triển khai `generate_artifact` và `download_artifact` thực hiện định tuyến động dựa vào loại Task, ẩn đi việc gọi các phương thức deep-nested như `client.artifacts.generate_quiz`.

#### 2. Đơn giản hóa Pipeline Artifact Flow và CLI
*   **Địa điểm sửa đổi**:
    *   [_artifacts.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-notebooklm/src/ccba_notebooklm/_artifacts.py)
    *   [_gc.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-notebooklm/src/ccba_notebooklm/_gc.py)
    *   [__main__.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-notebooklm/src/ccba_notebooklm/__main__.py)
*   **Chi tiết**:
    *   Loại bỏ hoàn toàn hai tham số callback lambda (`generate_fn`, `download_fn`) khỏi chữ ký hàm `handle_artifact_flow`.
    *   Chuyển sang cơ chế truyền các tham số tùy chọn qua `**kwargs` và gọi trực tiếp `client.generate_artifact` và `client.download_artifact`.
    *   Cập nhật CLI trong `__main__.py` để gọi `handle_artifact_flow` một cách trực quan, sạch sẽ, không lạm dụng biểu thức lambda phức tạp.
    *   Cập nhật bộ dọn dẹp `_gc.py` để sử dụng các API phẳng của client.

#### 3. Cập nhật và Bổ sung Unit Tests
*   **Địa điểm sửa đổi**:
    *   [test_mock_client.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-notebooklm/tests/test_mock_client.py)
    *   [_mock_client.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-notebooklm/src/ccba_notebooklm/_mock_client.py)
*   **Chi tiết**:
    *   Bổ sung `MockChatService` vào Mock adapter (`_mock_client.py`) để hỗ trợ mô phỏng kiểm thử câu lệnh RAG (`ask_chat`).
    *   Cập nhật `test_mock_artifact_flow` để tương thích với chữ ký mới không callback của `handle_artifact_flow`.
    *   Viết thêm test case toàn diện `test_flat_client_methods` để kiểm định toàn bộ hành vi phẳng của client.

---

## Candidate 2: Tách biệt Logic Xử lý VBPL (Amendment Processing) khỏi LegalRegistryManager

### Các thay đổi đã thực hiện

#### 1. Tạo mới lớp điều phối `LegalProcessor`
*   **Địa điểm tạo mới**: [coordinator.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel/ccba_legal/coordinator.py)
*   **Chi tiết**:
    *   Định nghĩa lớp `LegalProcessor` để chịu trách nhiệm nghiệp vụ phân tích tài liệu sửa đổi/bổ sung VBPL.
    *   Giao tiếp và điều phối sạch sẽ giữa `LegalRegistryManager` (quản lý lưu trữ), `LegalAnalysisEngine` (phân tích) và `inject_warning_block` (tiêm cảnh báo vào tệp đích).
    *   Giải quyết triệt độ vấn đề import vòng tròn (circular dependency) trước đây bằng cách đưa mối quan hệ phụ thuộc chéo về một chiều (packager và registry không còn import trực tiếp lẫn nhau nữa, mà packager chỉ dùng `LegalProcessor`).

#### 2. Rút gọn `LegalRegistryManager`
*   **Địa điểm sửa đổi**: [registry.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel/ccba_legal/registry.py)
*   **Chi tiết**:
    *   Xóa bỏ hoàn toàn phương thức `process_amendments_from_document` khỏi `LegalRegistryManager`.
    *   Loại bỏ các inline imports liên quan đến `parser.py` và `packager.py`.
    *   Trả lại vai trò Repository thuần túy cho `LegalRegistryManager` chỉ để CRUD và định vị tệp dữ liệu.

#### 3. Cập nhật caller và Unit Tests
*   **Địa điểm sửa đổi**:
    *   [packager.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel/ccba_legal/packager.py)
    *   [test_granular_amendments.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel/tests/test_granular_amendments.py)
*   **Chi tiết**:
    *   Cập nhật `packager.py` để sử dụng `LegalProcessor` phối hợp luồng nghiệp vụ thay vì gọi registry manager thô.
    *   Cập nhật import và test case trong `test_granular_amendments.py` để khởi tạo và kiểm thử thông qua lớp điều phối `LegalProcessor`.

---

## Candidate 3: Gom nhóm và Chuẩn hóa File-based Locks trong môi trường Đa tiến trình

### Các thay đổi đã thực hiện

#### 1. Tạo mới lớp khóa an toàn `FileMutexLock`
*   **Địa điểm tạo mới**: [_mutex.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/_mutex.py)
*   **Chi tiết**:
    *   Định nghĩa lớp `FileMutexLock` kế thừa từ cơ chế khóa nguyên tử nguyên bản, nhưng tích hợp kiểm tra sống PID thông qua `os.kill(lock_pid, 0)` để giải phóng deadlock nếu tiến trình nắm giữ lock bị kết thúc bất thường.
    *   Hỗ trợ thời gian hết hạn tối đa (`expire_seconds`) và cấu hình giãn cách thử lại (`retry_interval`).
    *   Re-export trực tiếp tại [__init__.py](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/__init__.py).

#### 2. Đồng bộ hóa trong `ccba-ai`
*   **Cập nhật dependencies**: Thêm `ccba-harness` vào dependencies của [pyproject.toml](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-ai/pyproject.toml).
*   **plan.py**: Thay thế hoàn toàn lớp `FileLock` tự chế bằng `FileMutexLock` từ `ccba-harness` để bảo vệ an toàn cho quá trình đồng bộ trạng thái phase của plan.
*   **team.py**: Bổ sung khóa `FileMutexLock` bảo vệ cho shared database `team_tasks.json` để tránh race condition khi nhiều agents thực hiện `add_task`, `claim_task`, hoặc `complete_task` đồng thời.

#### 3. Kế thừa trong `ccba-legal-intel`
*   **crawler.py**: Định nghĩa lại `TVPLSessionMutex` kế thừa từ `FileMutexLock` của `ccba-harness` để giữ tính tương thích ngược, đồng thời loại bỏ trùng lặp mã nguồn locking thô.

---

## Báo cáo đối soát phản diện của Copilot (Copilot Review Comments Resolution)

Chúng tôi đã thực hiện chạy công cụ kiểm định bình luận của Copilot trên PR #95 và xử lý 8/8 góp ý (tất cả đều được đánh giá là **HỢP LÝ / VALID**):

- **Comment 3542083145**: `download_artifact() currently treats an explicitly provided empty string output_format (e.g., passed through from handle_artifact_flow default "") as a valid value, overriding the intended per-artifact defaults (json/pdf). This can result in calling the underlying download_* RPC with output_format="", which is likely invalid.`
- **Comment 3542083164**: `Same as quiz/slides: passing output_format="" via kwargs will override the default and call download_flashcards(..., output_format=""). Treat empty output_format as missing to preserve defaults.`
- **Comment 3542083186**: `test_flat_client_methods() intends to verify that the async context manager returns the same client instance, but it currently doesn’t capture the __aenter__ return value (and the isinstance check is trivially true while also constructing a second client via get_client()).`
- **Comment 3542083213**: `The save() docstring still refers to FileLock, but the implementation now uses FileMutexLock.`
- **Comment 3542083231**: `Import grouping/order will fail ruff isort (I) checks: ccba_harness (first-party) should be separated from stdlib imports by a blank line.`
- **Comment 3542083258**: `Import order likely fails ruff isort (I) checks: ccba_ai.* should be ordered before ccba_harness.* within the same section.`
- **Comment 3542083278**: `Import order likely fails ruff isort (I) checks (module names should be sorted within the section).`
- **Comment 3542083307**: `This import block likely fails ruff isort (I) checks: missing blank line between third-party (yaml) and first-party (ccba_legal.*), and module imports should be sorted.`

*Tất cả 8/8 bản sửa lỗi đã được commit lên nhánh `refactor/architecture-deepening` và đẩy lên GitHub.*

---

## Kết quả kiểm thử & Tích hợp liên tục (CI status)

Tất cả các kiểm định tích hợp liên tục (CI) của GitHub Actions trên PR #95 đều đã **Vượt qua thành công (Passed)**:
*   `Lint Markdown`: **pass**
*   `validate`: **pass**
*   `Test - Python 3.10`: **pass**
*   `Test - Python 3.11`: **pass**
*   `Test - Python 3.12`: **pass**

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
