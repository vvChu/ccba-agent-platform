# Session Learnings — OKF Bundle & Legal Crawler Upgrades (2026-07-05)

Tài liệu này tổng hợp các bài học kinh nghiệm, patterns và giải pháp tối ưu được đúc rút từ chuỗi nâng cấp tính năng và sửa lỗi linter pháp lý.

---

## Patterns (Mẫu tốt)

### 1. VIP Session Mutex Lock
- **Ngữ cảnh**: Tránh xung đột phiên đăng nhập VIP (kick-out) khi chạy nhiều tiến trình cào dữ liệu song song hoặc phân tán.
- **Giải pháp**:
  - Sử dụng file lock nguyên tử tại một vị trí cố định (ví dụ: `.md/data/tvpl_vip_session.lock`).
  - Ghi nhận thông tin PID và timestamp của tiến trình sở hữu khóa.
  - Hỗ trợ cơ chế tự giải phóng (Override) nếu khóa chết (deadlock) vượt quá thời gian tối đa cho phép (ví dụ: > 5 phút).
  - Sử dụng block `try...finally` để đảm bảo tệp khóa luôn được giải phóng sạch sẽ khi thoát tiến trình (kể cả khi gặp ngoại lệ).
- **Nguồn**: Session `d9f9dfde-660c-473b-a89e-3988904a7463`, 2026-07-05

### 2. Late-binding Closure Capture (Default Parameter Binding)
- **Ngữ cảnh**: Định nghĩa hàm lồng (nested function) hoặc hàm callback bên trong một vòng lặp sử dụng biến vòng lặp (ví dụ: `filepath` trong vòng lặp duyệt tệp). Tránh cảnh báo Ruff B023.
- **Giải pháp**: Sử dụng default parameter binding để bắt cứng giá trị của biến vòng lặp tại thời điểm khai báo thay vì tham chiếu động lúc thực thi:
  ```python
  for filepath in files:
      def replace_link(match, filepath=filepath):
          # Sử dụng filepath an toàn ở đây
          ...
  ```
- **Nguồn**: Session `d9f9dfde-660c-473b-a89e-3988904a7463`, 2026-07-05

### 3. Raise from None in Non-chained Exceptions
- **Ngữ cảnh**: Khi kiểm tra logic nghiệp vụ độc lập (như kiểm tra timeout) bên trong một block `try...except Exception:` và muốn ném ngoại lệ mới nhưng không muốn hiển thị trace ngược (context chain) của lỗi trước đó không liên quan. Tránh cảnh báo Ruff B904.
- **Giải pháp**: Sử dụng `from None`:
  ```python
  try:
      ...
      if time.time() - start >= timeout:
          raise TimeoutError("Timeout occurred") from None
  except Exception as e:
      ...
  ```
- **Nguồn**: Session `d9f9dfde-660c-473b-a89e-3988904a7463`, 2026-07-05

### 4. Skill Link Portability
- **Ngữ cảnh**: Khi định nghĩa các liên kết tham chiếu bên trong tệp `SKILL.md` (ví dụ: dẫn đến tệp reference hoặc cấu hình).
- **Giải pháp**: Luôn sử dụng liên kết tương đối (relative paths) thay vì liên kết tuyệt đối dạng `file:///d:/...` để tránh bị hỏng link khi các nhà phát triển khác chạy trên máy cá nhân của họ.
- **Nguồn**: Session `18073a94-bdd0-4310-84dd-8f4e3ba9387e`, 2026-07-05

### 5. Parse-Protection (Bảo vệ phân tích thủ công)
- **Ngữ cảnh**: Khi cần tự động cập nhật báo cáo hoặc tệp tri thức bằng AI/scripts nhưng muốn bảo toàn tuyệt đối phần ghi chú thủ công của con người viết trong cùng một tệp.
- **Giải pháp**: Thiết kế tệp tin phân tầng và sử dụng cặp thẻ marker comment ẩn để cách ly hoàn toàn:
  * Đọc tệp tin gốc và dùng regex để trích xuất nội dung giữa `<!-- DEVELOPER-NOTES-START -->` và `<!-- DEVELOPER-NOTES-END -->`.
  * Tạo nội dung tự động mới và bọc trong cặp thẻ `<!-- AUTO-GENERATED-START -->` và `<!-- AUTO-GENERATED-END -->`.
  * Nối hai phần lại và ghi đè lại file.
- **Nguồn**: Session `18073a94-bdd0-4310-84dd-8f4e3ba9387e`, 2026-07-06

### 6. Two-axis Parallel Review (Đánh giá song song hai trục)
- **Ngữ cảnh**: Cần rà soát một đối tượng phức tạp dưới nhiều góc độ khác nhau (như code review theo Standards và Spec) để tránh ô nhiễm context.
- **Giải pháp**: Spawn hai sub-agents chạy độc lập và song song dưới cùng một context cha. Sub-agent A chỉ rà soát Standards; sub-agent B chỉ rà soát Spec. Sau đó gộp kết quả ở Agent chính.
- **Nguồn**: Session `18073a94-bdd0-4310-84dd-8f4e3ba9387e`, 2026-07-06

### 7. Safe Workspace Sandbox (Sandbox an toàn cho Workspace)
- **Ngữ cảnh**: Thiết kế lớp quản lý tệp tin giải nén tạm thời (đặc biệt khi chạy song song nhiều tiến trình).
- **Giải pháp**: Sử dụng `tempfile.TemporaryDirectory` kết hợp đặt tệp tin repacked trung gian ẩn (ví dụ: `.repacked_filename`) ở ngay bên trong thư mục con này thay vì thư mục cha dùng chung, giúp tự động thu hồi/xóa sạch khi thoát khối `with` mà không sợ va chạm dữ liệu.
- **Nguồn**: Session `18073a94-bdd0-4310-84dd-8f4e3ba9387e`, 2026-07-06

### 8. Path Traversal Guard (Rào chắn Path Traversal)
- **Ngữ cảnh**: Cung cấp API cho phép người dùng hoặc Caller bên ngoài truy cập file trong một thư mục sandbox bằng đường dẫn tương đối (`rel_path`).
- **Giải pháp**: Luôn gọi `.resolve()` và dùng `Path.is_relative_to(sandbox_root)` để chặn đứng mọi hành vi thoát sandbox (ví dụ: `../../etc/passwd`).
- **Nguồn**: Session `18073a94-bdd0-4310-84dd-8f4e3ba9387e`, 2026-07-06

### 9. Hierarchical Section Parser (Bộ phân tích phân tầng tiêu đề)
- **Ngữ cảnh**: Cần linter phát hiện và kiểm duyệt chính xác các bước quy trình nằm sâu dưới tiêu đề phụ `###` mà không bị bỏ sót, đồng thời tự động kế thừa trạng thái loại trừ (Exclusion) hoặc quy trình (Workflow) từ cha xuống con.
- **Giải pháp**: Sử dụng một stack chứa bộ ba `(heading_level, header_text, is_workflow)` để theo dõi độ sâu tiêu đề. Khi gặp tiêu đề mới, pop các tiêu đề cũ có cấp độ lớn hơn hoặc bằng ra khỏi stack để duy trì cấu trúc cây phân cấp chính xác.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-06

### 10. Plan Concurrency Lock (Khóa kế hoạch đồng thời)
- **Ngữ cảnh**: Tránh rủi ro ghi đè mất mát dữ liệu (Lost Update) khi nhiều Agents chạy song song cùng cập nhật tệp trạng thái kế hoạch chung (`plan.md`).
- **Giải pháp**: Thiết kế context manager `FileLock` đơn giản bằng Python thuần tạo tệp khóa tạm thời `.plan.lock` ở chế độ ghi độc quyền (`exist_ok=False`). Nếu khóa đang bị giữ, luồng chạy sau sẽ đợi (delay 100ms) đến khi timeout (5 giây) hoặc thành công.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-06

### 11. Target Line Override (Cập nhật ghi đè dòng mục tiêu)
- **Ngữ cảnh**: Cần cập nhật tự động các trường giá trị trong YAML Frontmatter nhưng muốn bảo toàn nguyên vẹn 100% chú thích (comments) và trật tự dòng tùy biến do con người viết trước đó.
- **Giải pháp**: Thay vì safe_load và safe_dump lại toàn bộ cấu trúc frontmatter, tiến hành đọc tệp thô và sử dụng regex thay thế chính xác dòng mục tiêu cần sửa (ví dụ: `status: ...`), giữ nguyên các dòng còn lại.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-06

### 12. Dual-source Multi-sampling Video Extraction (Trích xuất video đa nguồn đa mẫu)
- **Ngữ cảnh**: Cần trích xuất bài giảng từ video trực tuyến một cách nhanh chóng, đầy đủ slide hình ảnh cùng phụ đề chất lượng cao.
- **Giải pháp**: 
  - Kết hợp phân đoạn sơ cấp qua storyboard grids thô của YouTube CDN (nhận diện slide qua LLM-as-Judge lọc Talking Heads) giúp tối đa tốc độ tải ảnh.
  - Sử dụng cơ chế dự phòng (fallback) tự động tải audio và chạy Whisper STT qua SDK `ccba-ai` nếu API phụ đề YouTube bị lỗi hoặc thiếu.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

### 13. Dynamic Local AppData Fallback (Định vị AppData Windows động)
- **Ngữ cảnh**: Cần định vị các gói ứng dụng (như Winget, FFmpeg) trên Windows một cách tự động mà không bị bó buộc vào tên tài khoản người dùng cụ thể.
- **Giải pháp**: Sử dụng biến môi trường `%LOCALAPPDATA%` hoặc fallback sang `Path.home() / "AppData" / "Local"` để xây dựng đường dẫn linh hoạt trên mọi máy trạm.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

### 14. Local-First Agent Evaluation of PR Comments (Tự đối soát bình luận PR tại Agent)
- **Ngữ cảnh**: Cần đối soát và phản biện toàn bộ ý kiến của Copilot/Reviewers trước khi merge PR.
- **Giải pháp**: Thay vì gọi API LLM phức tạp từ trong file bash/python script, hãy để script chỉ trích xuất dữ liệu thô (JSON comments), và sử dụng chính trí tuệ native cùng ngữ cảnh đầy đủ của Agent đang chạy để đánh giá, sửa code VALID hoặc giải trình code INVALID.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

### 15. Secure Composable Zip Extraction (Giải nén Zip an toàn & giải phóng file)
- **Ngữ cảnh**: Khi giải nén và nén tệp Office Open XML, cần đảm bảo an toàn sandbox và giải phóng tài nguyên.
- **Giải pháp**: Kết hợp `Path.resolve()` và `is_relative_to` kiểm duyệt an toàn trước Path Traversal, đồng thời bọc zip extraction trong khối `with` context manager và sử dụng `shutil.copyfileobj` để giải phóng handle tập tin ngay lập tức, tránh PermissionError khóa file trên Windows.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

### 16. Dynamic System Dependency Detection & Fallback (Tìm kiếm CLI động & dự phòng)
- **Ngữ cảnh**: Khi thực thi các tiến trình CLI bên ngoài (như Pandoc, LibreOffice) trên máy tính Windows của người dùng.
- **Giải pháp**: Sử dụng `shutil.which` kết hợp mảng fallback các đường dẫn cài đặt mặc định trên Windows (`C:\Program Files\...`) để định vị tự động tệp thực thi. Nếu không tìm thấy, ném lỗi `FileNotFoundError` thân thiện hướng dẫn người dùng cài đặt hoặc chuyển sang cơ chế dự phòng dùng thư viện Python thuần.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

### 17. Forbidden Background Installer Execution (Cấm cài đặt thư viện ngầm)
- **Ngữ cảnh**: Script chạy nghiệp vụ tự động gọi `pip install` hoặc cài đặt gói thư viện bên thứ ba ngầm trong code.
- **Giải pháp**: Thay vì chạy lệnh cài đặt ngầm có thể gây crash hoặc rủi ro bảo mật, ném `ImportError` tiêu chuẩn để thông báo rõ ràng cho kỹ sư cài đặt hoặc để Agent chạy thông qua lệnh terminal được người dùng phê duyệt trực tiếp.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

---

## Anti-patterns (Cách tránh)

### 1. Late-binding Reference in Loop Closures
- **Vấn đề**: Sử dụng trực tiếp biến vòng lặp bên trong một hàm callback/closure lồng mà không capture. Trình linter sẽ báo lỗi Ruff B023, đồng thời gây lỗi logic nghiêm trọng khi các luồng chạy sau đều tham chiếu đến phần tử cuối cùng của vòng lặp thay vì phần tử tương ứng của chúng.
- **Thay thế bằng**: Sử dụng tham số mặc định để bind cứng giá trị (`def callback(arg, loop_var=loop_var):`).

### 2. Copy-paste Frontmatter Fields Manual Maintenance
- **Vấn đề**: Việc phân tách tệp lớn (split document) mà không chuyển tiếp các siêu dữ liệu quản trị quan trọng (`resource`, `status`, `timestamp`) khiến các tệp con bị linter báo lỗi thiếu trường bắt buộc, hoặc gây mất thông tin truy vết.
- **Thay thế bằng**: Nâng cấp trình đóng gói tự động sao chép các trường Frontmatter siêu dữ liệu cần thiết từ tệp gốc sang toàn bộ tệp con và tệp phụ lục đính kèm.

### 3. Monolithic Workflow File
- **Vấn đề**: Đặt toàn bộ nội dung hướng dẫn chi tiết các bước và tiêu chí hoàn thành trực tiếp bên trong thư mục `.agents/workflows/`. Điều này làm tăng kích thước tệp tĩnh và tăng context load của mô hình một cách vô ích.
- **Thay thế bằng**: Tách thành một tệp workflow mỏng (wrapper) chỉ chứa mô tả ngắn gọn và lệnh nạp động tệp `SKILL.md` tương ứng nằm dưới thư mục `.agents/skills/`.

### 4. Redundant Agent Skills
- **Vấn đề**: Tạo thêm một kỹ năng (Skill) thực thi độc lập cho Agent (ví dụ: `tvpl_vip_mutex_downloader`) khi logic đó đã được xử lý hoàn chỉnh và tự động trong code Python chạy ngầm. Việc này làm tăng Context Load mà không đem lại giá trị thực thi trực tiếp nào cho Agent.
- **Thay thế bằng**: Tái sử dụng qua code hoặc chuyển đổi thành tài liệu kiến trúc (ADR) lưu trong thư mục tri thức.

### 5. Automatic High-cost LLM API Invocation
- **Vấn đề**: Tự động gọi phân tích sâu của LLM trên các tệp mới/cập nhật ngay khi phát hiện thay đổi SHA mà không hỏi ý kiến người dùng. Điều này gây lãng phí token và tài nguyên lớn.
- **Thay thế bằng**: Bổ sung cờ kiểm tra nhanh (ví dụ: `--check-only`) để Agent liệt kê các tệp thay đổi và hỏi ý kiến kỹ sư trước khi thực thi AI Gateway phân tích sâu.

### 6. Shared Directory Repack Path
- **Vấn đề**: Lưu tệp tin repacked tạm thời ở thư mục cha dùng chung, dẫn đến rủi ro va chạm (collision) và race condition khi có nhiều tiến trình chạy song song xử lý cùng một file gốc.
- **Thay thế bằng**: Lưu tệp tạm repacked ẩn trực tiếp trong thư mục con workspace tạm độc nhất.

### 7. Unvalidated Relative Paths
- **Vấn đề**: Tin tưởng hoàn toàn vào đường dẫn tương đối do Caller truyền vào, gây ra rò rỉ dữ liệu hoặc lỗi ghi đè file hệ thống qua lỗ hổng Path Traversal.
- **Thay thế bằng**: Kiểm duyệt an toàn bằng `Path.is_relative_to`.

### 8. Flat Linter Section Bypasses
- **Vấn đề**: Việc thiết kế linter kiểm tra quy trình phẳng dễ bị lách qua bằng cách đẩy các bước nghiệp vụ xuống tiêu đề phụ `###`. Việc này gây mất kiểm soát và tích lũy nợ kỹ thuật (thiếu tiêu chí hoàn thành ở các bước con quan trọng).
- **Thay thế bằng**: Sử dụng stack phân cấp để bắt buộc kiểm duyệt ở các mức độ sâu chính xác của workflow.

### 9. Lost Update on Multi-Daemon Plan Updates
- **Vấn đề**: Đọc và ghi đè trực tiếp file kế hoạch chung mà không có cơ chế khóa đồng bộ, dẫn đến việc mất mát trạng thái khi nhiều Agents chạy song song ghi đè chéo nhau.
- **Thay thế bằng**: Sử dụng cơ chế khóa tệp tạm `.plan.lock` khi ghi dữ liệu.

### 10. Blank Slate YAML Safe-Dump
- **Vấn đề**: Sử dụng safe_dump để cập nhật status trong YAML Frontmatter, làm sạch và xóa bỏ hoàn toàn các comments, ghi chú thủ công có giá trị của kỹ sư.
- **Thay thế bằng**: Áp dụng Target Line Override để chỉ sửa đổi tối thiểu dòng trạng thái.

### 11. Out-of-order Git Log Walkthrough Audit
- **Vấn đề**: Đối soát lịch sử thay đổi (`git log origin/main..HEAD`) sau khi đã checkout sang nhánh `main` và kéo code mới, dẫn đến việc hai nhánh trùng nhau và danh sách commit trả về rỗng (mất thông tin bàn giao).
- **Thay thế bằng**: Lấy tên branch hiện tại và chạy truy vấn so sánh commit *trước khi* thực hiện lệnh checkout sang `main`.

### 12. Soft Branch Deletion after Squash Merge
- **Vấn đề**: Sử dụng lệnh xóa mềm `git branch -d` đối với các nhánh tính năng đã được Squash Merge trên GitHub, gây lỗi chặn lệnh do git local không tìm thấy commit trùng khớp hash.
- **Thay thế bằng**: Sử dụng lệnh xóa lực lượng `git branch -D` để dọn dẹp sạch nhánh local sau khi PR đã merge thành công.

### 13. Unclosed PIL Image Handles in Cache
- **Vấn đề**: Lưu trữ hình ảnh grid trực tiếp vào bộ nhớ đệm mà không đóng file handle, dẫn đến khóa tài nguyên tập tin trên Windows và chặn đứng việc xóa dọn dẹp thư mục tạm thời.
- **Thay thế bằng**: Sử dụng khối `with PILImage.open() as img:` kết hợp lưu `.copy()` của ảnh và tự động đóng handle lập tức.

### 14. Unverified Third-party API Recommendations
- **Vấn đề**: Tin tưởng và sử dụng trực tiếp các đề xuất của Copilot/Reviewers về các phương thức thư viện mới (như `list_transcripts`) mà không kiểm tra độ tương thích với phiên bản thư viện hiện tại trong dự án, gây lỗi crash runtime.
- **Thay thế bằng**: Chạy kiểm tra nhanh danh sách phương thức thực tế (qua `dir(Module)`) trong môi trường Python trước khi áp dụng code đề xuất.

### 15. Silent Pip Installer in Python Runtime
- **Vấn đề**: Tự động tải và cài đặt thư viện ngoài bằng `subprocess.check_call([sys.executable, "-m", "pip", "install", ...])` từ trong code Python mà không có sự đồng thuận của kỹ sư, gây lỗi treo tiến trình hoặc vi phạm chính sách bảo mật hệ thống.
- **Thay thế bằng**: Báo lỗi `ImportError` thân thiện và cung cấp lệnh cài đặt rõ ràng ngoài shell.

### 16. Full-Workspace Linter Target
- **Vấn đề**: Chạy linter quét toàn bộ workspace (`validate_skills.py .`) bao gồm cả thư mục ảo `.venv` và thư mục rác tạm thời, dẫn đến hàng trăm cảnh báo/lỗi không liên quan gây ô nhiễm báo cáo.
- **Thay thế bằng**: Chỉ chạy linter nhắm mục tiêu chính xác thư mục chứa skills chính thức (`validate_skills.py` không tham số) hoặc tệp tin đã thay đổi.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
