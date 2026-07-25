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

### 18. Release-Gate Post-Timeout Re-Audit (Đối soát lại sau timeout tại Release)
- **Ngữ cảnh**: Khi PR CI và Copilot review bị timeout lúc chạy lệnh khởi tạo PR (`/ccba-create-pr`), có thể bình luận của Copilot sẽ được đẩy lên sau đó trước khi PR được merge.
- **Giải pháp**: Cưỡng chế chạy lại đối soát comments (`audit_pr_comments.py`) ngay tại bước đầu tiên của quy trình Release (`/ccba-release-feature`) để chặn đứng việc merge mù nếu có ý kiến đóng góp muộn từ reviewer.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

### 19. Structure-Based Knowledge Segregation (Phân tách cấu trúc tri thức)
- **Ngữ cảnh**: Sắp xếp tài liệu trong thư mục `.md/` để tránh việc tất cả các tệp đều lưu ở thư mục gốc `.md/knowledge/`, gây lộn xộn và khó quản lý.
- **Giải pháp**: Phân chia rõ ràng thành các thư mục con chuyên biệt:
  * `.md/data/` cho các tệp dữ liệu động hoặc registry thay đổi liên tục (`legal_registry.yaml`, `sources_registry.yaml`, các kết quả evaluation).
  * `.md/knowledge/configs/` cho các tệp cấu hình.
  * `.md/knowledge/guidelines/` cho các tài liệu hướng dẫn nghiệp vụ.
  * `.md/knowledge/related_papers/` cho các bài báo nghiên cứu, tài liệu tham khảo.
  * `.md/knowledge/reports/` cho các báo cáo phân tích, đánh giá, session retrospective.
  * `.md/knowledge/specs_and_roadmaps/` cho các đặc tả và lộ trình phát triển.
  * `.md/seminars/` cho các tài liệu liên quan đến seminar.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

### 20. Workspace-Relative Link Validation (Kiểm duyệt liên kết tương đối trong không gian làm việc)
- **Ngữ cảnh**: Khi định nghĩa các liên kết (file links) trong tài liệu dự án (như workflows hay skills).
- **Giải pháp**: Luôn sử dụng liên kết tương đối bắt đầu bằng các thư mục con trong dự án (ví dụ: `../skills/...` hoặc `../../.md/...`) thay vì liên kết tuyệt đối dạng `file:///d:/...` để đảm bảo tài liệu hoạt động đúng trên mọi môi trường và vượt qua được sự kiểm duyệt nghiêm ngặt của linter.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

### 21. Dynamic Legal Registry Integration (Tích hợp Registry Pháp lý Động)
- **Ngữ cảnh**: Tránh hardcode các số hiệu, ngày hiệu lực hoặc trạng thái chuyển tiếp luật tĩnh vào hiến pháp `AGENTS.md`.
- **Giải pháp**: Cưỡng chế Agent luôn tra cứu động qua `legal_registry.yaml` để xác định trạng thái thực tế (`status: current`).
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

### 22. Dual-Role Source Classification (Phân tách vai trò nguồn thông tin)
- **Ngữ cảnh**: Quản lý nhiều nguồn thông tin pháp luật có độ chính thống và mức độ hỗ trợ tự động hóa khác nhau.
- **Giải pháp**: Tách biệt vai trò "Xác minh pháp lý tối cao" (các cổng TTĐT Chính phủ/MOC) và "Moteur cào/lược đồ tự động" (Thư viện Pháp luật `thuvienphapluat.vn`).
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

### 23. Local-first Git-ignored Skills (Git-ignore Kỹ năng cục bộ tại Spoke)
- **Ngữ cảnh**: Tránh drift code và Git bloat tại Spoke khi đồng bộ các kỹ năng nặng từ Hub.
- **Giải pháp**: Sao chép thư mục `skills/` về local của Spoke để IDE auto-discovery hoạt động mượt mà và không gặp lỗi phân quyền, nhưng đưa thư mục này vào `.gitignore` mẫu của Spoke để không bao giờ commit lên git. Chỉ commit các file workflow mỏng (wrapper) và `AGENTS.md`.
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

### 24. Functional Spoke Ownership Mapping (Phân cấp sở hữu Spoke Chuyên môn)
- **Ngữ cảnh**: Phân định trách nhiệm chuẩn hóa tri thức và tài nguyên theo cơ cấu phòng ban CCBA.
- **Giải pháp**: Phân loại Spoke thành Spoke Triển khai (Delivery Spoke - ngắn hạn theo dự án) và Spoke Chuyên môn (Functional/R&D Spoke - dài hạn thuộc quyền sở hữu của Trưởng phòng chuyên môn). Định vị Hub là nhân của Nền tảng số IDOP (được quản lý bởi bộ phận Nền tảng số & Công nghệ BIM).
- **Nguồn**: Session `2e9d3d62-5a5e-4574-a0c7-9f9256a1b3e5`, 2026-07-07

### 25. Replaced Document Auto-Supersede (Tự động cập nhật trạng thái văn bản bị thay thế)
- **Ngữ cảnh**: Cập nhật trạng thái hiệu lực tự động cho các văn bản cũ khi cào/đăng ký văn bản thay thế mới.
- **Giải pháp**: Khi cào và cập nhật một văn bản mới (ví dụ NĐ 207/2026), hệ thống phải tự động quét trường `replaced_docs` và đổi trạng thái của văn bản cũ thành `status: superseded` trong `legal_registry.yaml`.
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

### 17. Single-Check Merge Authorization
- **Vấn đề**: Chỉ kiểm tra bình luận của Copilot một lần lúc tạo PR. Nếu Copilot chạy chậm (post-timeout), Agent ở phiên release sẽ merge mà không hề hay biết, dẫn đến lọt các lỗi hoặc contradiction nghiêm trọng.
- **Thay thế bằng**: Cấu hình kiểm tra hai lớp, bắt buộc re-audit comments ngay trước khi bấm nút merge chính thức.

### 18. Flat Knowledge Directory Pollution (Gây ô nhiễm thư mục tri thức phẳng)
- **Vấn đề**: Lưu trữ tất cả các loại tệp (từ tệp cấu hình, báo cáo, tài liệu học thuật đến dữ liệu động thường xuyên cập nhật) trực tiếp tại thư mục gốc của `.md/knowledge/`. Điều này làm tăng độ nhiễu thông tin khi Agent tìm kiếm tri thức và phá vỡ cấu trúc tổ chức dự án.
- **Thay thế bằng**: Áp dụng quy tắc phân tách cấu trúc tri thức (Structure-Based Knowledge Segregation) vào các thư mục con chuyên biệt.

### 19. Hardcoded Absolute Local File Paths in Shared Docs (Hardcode đường dẫn tuyệt đối cục bộ trong tài liệu chia sẻ)
- **Vấn đề**: Sử dụng đường dẫn tuyệt đối dạng `file:///d:/GitHubProjects/...` trong các tài liệu Markdown hoặc Workflow. Các đường dẫn này chỉ chạy được trên máy của một nhà phát triển cụ thể và sẽ báo lỗi khi chạy linter kiểm tra tài liệu trên các máy khác hoặc trên CI.
- **Thay thế bằng**: Luôn sử dụng đường dẫn tương đối (relative paths) từ vị trí của tài liệu đến đích cần liên kết.

### 20. Hardcoded Default Credentials in Markdown (Hardcode thông tin tài khoản mặc định trong Markdown)
- **Vấn đề**: Lưu tài khoản và mật khẩu mặc định dạng văn bản thô (`vuvanchu119` / `ccba@ibst`) trong tệp `SKILL.md` công khai trên repo, gây nguy cơ rò rỉ thông tin xác thực.
- **Thay thế bằng**: Bắt buộc cấu hình biến môi trường (`TVPL_USERNAME`, `TVPL_PASSWORD`) thông qua file cấu hình cục bộ `.env` và đưa tệp này vào `.gitignore`.

### 21. Full Python Test Suite Run for Markdown-only Changes (Chạy toàn bộ ca thử nghiệm Python khi chỉ thay đổi Markdown)
- **Vấn đề**: Chạy toàn bộ 457 test cases khi chỉ thay đổi các tệp cấu hình markdown là dư thừa và dễ gây gián đoạn do restart hệ thống.
- **Thay thế bằng**: Chỉ chạy các bộ kiểm định nhanh chuyên biệt (`validate_skills.py` và `validate_docs.py`) để xác thực tính hợp lệ của tài liệu.

---
### 26. LaTeX Math-to-OMML Native Rendering in Word
- **Ngữ cảnh**: Cần in các công thức toán học block (`$$...$$`) và toán học nội dòng (`$...$`) trong Markdown sang tệp Word (.docx) bản địa.
- **Giải pháp**:
  - Thiết lập bộ phân tích tách biệt văn bản thường và công thức toán học.
  - Chuyển đổi các biểu thức LaTeX sang MathML (sử dụng mapping hoặc converter).
  - Sử dụng stylesheet mặc định của Microsoft Office (`C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL` và thư viện `lxml`) để **dịch chuyển MathML sang OMML XML bản địa của Word**.
  - Append trực tiếp XML DOM vào phần tử paragraph trong Word (`p._element.append(omml.getroot())`). Công thức hiển thị sắc nét, đúng chỉ số dưới, ký tự Hy Lạp và hoàn toàn editable trực tiếp trên Word.
- **Nguồn**: Session `5ad8a2ba-ad29-4bcb-ac3e-dab95c43c54d`, 2026-07-08

### 27. Mermaid Flowchart Rendering via Base64 & Online CDN
- **Ngữ cảnh**: Cần hiển thị sơ đồ quy trình Mermaid dạng đồ họa trực quan trong tài liệu Word thay vì chỉ in nhãn giữ chỗ text thô.
- **Giải pháp**:
  - Trích xuất mã sơ đồ Mermaid trong code block.
  - Mã hóa mã thô sơ đồ thành chuỗi **URL-safe Base64** (sử dụng `base64.urlsafe_b64encode`).
  - Gửi yêu cầu HTTP tải hình ảnh kết xuất PNG từ CDN `https://mermaid.ink/img/{base64_string}` về tệp cục bộ tạm thời.
  - Chèn trực tiếp ảnh này vào Word thông qua `document.add_picture()` và thêm chú thích thích hợp dưới ảnh.
- **Nguồn**: Session `5ad8a2ba-ad29-4bcb-ac3e-dab95c43c54d`, 2026-07-08

### 28. Cell-Level Inline Formatting & Fixed Widths for Word Tables
- **Ngữ cảnh**: Phân dịch bảng biểu Markdown sang Word mà các ô vẫn chứa định dạng chữ đậm/nghiêng (`**`, `*`) thô và cột bảng co giãn tự động làm tràn chữ.
- **Giải pháp**:
  - Chạy trình phân tích định dạng học thuật (`parse_academic_text`) bên trong từng ô dữ liệu để xử lý độc lập kiểu chữ và công thức toán học nội dòng.
  - Áp dụng kích thước cột cố định cho bảng (sử dụng `cell.width = Inches(N)`) khớp khít vùng in khả dụng (ví dụ 6.5 inches cho khổ giấy dọc A4) giúp chống tràn chữ, thăng bằng cột.
- **Nguồn**: Session `5ad8a2ba-ad29-4bcb-ac3e-dab95c43c54d`, 2026-07-08

### 29. Cohesive Topic Folder Pattern (Mẫu thư mục đề tài chuyên biệt)
- **Ngữ cảnh**: Sắp xếp tài liệu nghiên cứu, bản thảo và tệp Word xuất bản liên quan đến một đề tài cụ thể.
- **Giải pháp**: Nhóm toàn bộ các tệp liên quan vào một thư mục con chuyên đề nằm dưới `.md/projects/[Ten_De_Tai]/` (ví dụ: `NC_Van_Hoa_Am_Tinh_Tu_Van_XD/`). Giúp gom cụm ngữ cảnh tốt, tăng tính kết hợp (High Cohesion), giảm phụ thuộc (Low Coupling) và dễ dàng đóng gói bàn giao thông qua kênh đồng bộ đám mây (OneDrive/SharePoint).
- **Nguồn**: Session `5ad8a2ba-ad29-4bcb-ac3e-dab95c43c54d`, 2026-07-08

---

## Anti-patterns (Cách tránh)

### 22. Raw LaTeX Math and Underscore Stripping in Word
- **Vấn đề**: In trực tiếp công thức LaTeX ra tệp Word mà không qua bộ biên dịch. Trình phân dịch Markdown thông thường sẽ hiểu lầm ký tự gạch dưới `_` trong công thức là thẻ in nghiêng và xóa bỏ nó, đồng thời hiển thị raw backslash `\` làm hỏng hiển thị toán học.
- **Thay thế bằng**: Sử dụng XML OMML và stylesheet chuyển đổi `MML2OMML.XSL` để chèn công thức toán học bản địa của Word.

### 23. Raw Text/Code Mermaid Placeholders in Final Word Documents
- **Vấn đề**: Để nguyên mã nguồn sơ đồ thô (`graph TD...`) hoặc các nhãn giữ chỗ text thô dạng "[Sơ đồ Mermaid...]" trong tài liệu Word báo cáo chính thức.
- **Thay thế bằng**: Tải ảnh PNG kết xuất từ CDN trực tuyến của Mermaid và chèn trực tiếp ảnh đồ họa vào tài liệu.

### 24. Flat Table Cell Rendering
- **Vấn đề**: Chỉ gọi hàm `add_run()` thô cho giá trị của ô bảng Word mà không chạy bộ phân dịch định dạng văn bản học thuật, làm lộ các dấu `**` hoặc `*` thô trong bảng.
- **Thay thế bằng**: Chạy phân dịch đệ quy `parse_academic_text` cho nội dung từng ô dữ liệu để làm sạch định dạng.

### 25. Flat Knowledge Directory Pollution for Research Projects
- **Vấn đề**: Lưu trữ tất cả tệp nháp, tệp Word xuất bản và báo cáo rà soát trực tiếp ở gốc thư mục `.md/knowledge/` hoặc `.md/knowledge/research_and_studies/` gây lộn xộn thư mục tri thức chính.
- **Thay thế bằng**: Gom cụm vào thư mục con chuyên biệt của đề tài dưới phân vùng `.md/projects/[Ten_De_Tai]/` (Cohesive Topic Folder).

### 30. "Git Core - Cloud Artifacts" Directory Partitioning (Phân hoạch thư mục Nhân Git - Vệ tinh Cloud)
- **Ngữ cảnh**: Đồng bộ hóa tri thức và dữ liệu giữa Hub và Spoke mà không làm phình to dung lượng Git Repo.
- **Giải pháp**: Phân chia rõ rệt: Git chỉ theo dõi mã nguồn, cấu hình nhẹ và bản thảo Markdown (`.md`). Còn các thư mục sản phẩm lớn chứa Word, PDF, ảnh thô dưới phân vùng `.md/projects/` sẽ bị Git-ignore đệ quy và chỉ đồng bộ qua SharePoint/OneDrive.
- **Nguồn**: Session `5ad8a2ba-ad29-4bcb-ac3e-dab95c43c54d`, 2026-07-08

### 31. Maskara Local Git pre-commit Hook Setup in Spoke (Thiết lập Git Hook Maskara cục bộ tại Spoke)
- **Ngữ cảnh**: Chặn đứng rò rỉ API Keys và mật khẩu thô lên repository cục bộ của Spoke mà không bắt buộc cài đặt các thư viện Python cồng kềnh.
- **Giải pháp**: Viết động script pre-commit cục bộ vào `.git/hooks/pre-commit` của Spoke trong tiến trình khởi tạo `/ccba-init-spoke` để gọi `python "$hub\scripts\maskara.py"` rà quét và chặn commit nếu phát hiện khóa API thô.
- **Nguồn**: Session `5ad8a2ba-ad29-4bcb-ac3e-dab95c43c54d`, 2026-07-08

### 32. Orchestrator-Only Cloud Write Sync Lock (Khóa ghi đám mây độc quyền cho Agent chính)
- **Ngữ cảnh**: Tránh lỗi xung đột ghi tệp đồng thời trên OneDrive (tạo ra các tệp trùng lặp dạng `*-Copy.md`) khi chạy teamwork với nhiều Subagents hoạt động song song.
- **Giải pháp**: Cưỡng chế các Subagents chỉ ghi tệp trong các sandbox local cô lập, và chỉ cho phép duy nhất Agent chính (Orchestrator) sau khi tổng hợp và kiểm định chất lượng được quyền ghi đè sản phẩm hoàn thiện vào thư mục đồng bộ Cloud `.md/projects/`.
- **Nguồn**: Session `5ad8a2ba-ad29-4bcb-ac3e-dab95c43c54d`, 2026-07-08

---

## Anti-patterns (Cách tránh)

### 26. Concurrent Cloud Sync Folder Writing by Subagents (Subagents ghi tệp đồng thời lên thư mục Cloud)
- **Vấn đề**: Các subagents chạy song song cùng ghi đè trực tiếp lên thư mục OneDrive, gây ra tình trạng khóa tệp hoặc sinh bản sao xung đột làm loãng không gian làm việc.
- **Thay thế bằng**: Chỉ để Agent chính tổng hợp và ghi đè một lần duy nhất tệp đã hoàn thiện.

### 27. Committing Large Project Deliverables to Git (Commit tệp sản phẩm lớn lên Git)
- **Vấn đề**: Commit trực tiếp các tệp nhị phân `.docx`, `.pdf` hoặc thư mục ảnh slide `.webp` lên Git của Hub hoặc Spoke, gây phình to vĩnh viễn kích thước lịch sử Git.
- **Thay thế bằng**: Cấu hình Git-ignore đệ quy và đồng bộ chúng hoàn toàn qua SharePoint/OneDrive.

### 33. Gated API RAG & Prototyping Boundaries (Ranh giới RAG & Prototype có điều kiện)
- **Ngữ cảnh**: Tích hợp các kỹ năng nặng về mặt tài nguyên (như `ccba-research` và `ccba-prototype`) với các kỹ năng nghiệp vụ thực tế mà không gây phình to chi phí API Gateway hay làm chậm thời gian phản hồi.
- **Giải pháp**: 
  - Áp dụng cơ chế bán tự động (HITL - Human-In-The-Loop) cho đối soát quy chuẩn sâu: Agent chính chỉ gợi ý lệnh chạy thay vì tự ý spawn.
  - Sử dụng static templates làm mặc định cho các nghiệp vụ ổn định, chỉ kích hoạt RAG qua subagent khi Registry phát hiện văn bản thay thế mới.
  - Chỉ bắt buộc dựng mẫu thử thô (prototype) đối với các refactor ảnh hưởng trực tiếp đến Core Platform (Hub) để bảo vệ tính ổn định của nhân hệ thống, đối với Spoke apps thì bỏ qua để tối ưu tiến độ.
- **Nguồn**: Session `d79bdc3f-c199-40c2-b1b7-eefc1865b66b`, 2026-07-09

### 34. Parallel Sub-agent Processing for Batch Matrix (Xử lý subagent song song cho ma trận quét loạt)
- **Ngữ cảnh**: Quét audit hồ sơ bản vẽ đa bộ môn lớn trên Coordination Matrix mà Agent chính bị nghẽn (block) do xử lý tuần tự từng tầng.
- **Giải pháp**: Cấu hình Async Batcher để spawn song song các subagents `ccba-research` độc lập dưới nền chạy quét cho từng tầng/Zone, thu gom kết quả JSON/Markdown về Agent chính để tổng hợp báo cáo.
- **Nguồn**: Session `d79bdc3f-c199-40c2-b1b7-eefc1865b66b`, 2026-07-09

---

## Anti-patterns (Cách tránh)

### 28. Monolithic Agent Core Processing on Large Batches (Agent chính tự xử lý tuần tự trên các lô dữ liệu lớn)
- **Vấn đề**: Để Agent chính tự lặp và gọi LLM lần lượt cho hàng chục dòng bản vẽ hoặc tài liệu lớn trong ma trận phối hợp, gây kéo dài thời gian chờ và dễ bị lỗi timeout/đứt gãy giữa chừng.
- **Thay thế bằng**: Spawn song song các subagents độc lập xử lý phân mảnh (Map) rồi gộp kết quả ở Agent chính (Reduce).

### 29. Automatic High-cost Prototyping on Minor Refactors (Dựng prototype tự động cho các thay đổi nhỏ)
- **Vấn đề**: Bắt buộc Agent phải dựng `/ccba-prototype` cho mọi đề xuất refactor code nhỏ trên các Spoke ứng dụng độc lập, làm kéo dài thời gian phát triển và lãng phí tài nguyên.
- **Thay thế bằng**: Chỉ bắt buộc dựng prototype cho các thay đổi ở mức độ Core Platform (Hub) có tác động lan rộng.

### 35. Dynamic Notebook ID Override via Environment Variables
- **Ngữ cảnh**: Tránh việc cấu hình tĩnh (hardcode) các Notebook IDs đại diện cho tri thức của Hub (`nb-mock-3`) hoặc Spoke trong tệp `catalog.yaml`, giúp hệ thống linh hoạt hơn khi chuyển đổi staging/production.
- **Giải pháp**: Ưu tiên đọc biến môi trường hệ thống có tiền tố `NOTEBOOKLM_<BUNDLE_NAME_UPPER>_ID` (ví dụ: `NOTEBOOKLM_CORE_ID`, `NOTEBOOKLM_QC_ID`). Nếu không được thiết lập, hệ thống mới tự động fallback về cấu hình mặc định trong `catalog.yaml`.
- **Nguồn**: Session `53854b3e-b698-4bfe-9ccd-8b7cde145e0a`, 2026-07-11

### 36. Local Git Reset Hard Synchronisation for Diverged Branches
- **Ngữ cảnh**: Khi nhánh tính năng cục bộ chứa lịch sử cũ lệch pha với remote branch đã được force-push đè bằng code sạch (fresh branch), việc chạy `git pull` sẽ gây xung đột (conflict) toàn bộ file.
- **Giải pháp**: Thay vì tiến hành merge conflict thủ công hàng trăm file, chạy `git merge --abort` để hủy merge lỗi, sau đó thực hiện reset cứng nhánh cục bộ về nhánh fresh tương ứng (`git reset --hard feat/...-fresh`) để đồng bộ hoàn toàn với remote sạch.
- **Nguồn**: Session `53854b3e-b698-4bfe-9ccd-8b7cde145e0a`, 2026-07-11

### 37. GitHub Actions Billing Limit Bypass Gate
- **Ngữ cảnh**: Khi chạy GitHub Checks trên PR bị báo thất bại ngay lập tức sau 3 giây do tài khoản GitHub cạn kiệt ngân sách chạy Actions (Billing / Spending Limit).
- **Giải pháp**: Chạy và xác thực toàn bộ test suite (`pytest`), kiểm định tài liệu (`validate_docs.py`), linter (`ruff`) cục bộ để bảo đảm chất lượng code đạt $100\%$ an toàn, sau đó bỏ qua cảnh báo CI và thực hiện merge PR trực tiếp thông qua GitHub CLI/admin.
- **Nguồn**: Session `53854b3e-b698-4bfe-9ccd-8b7cde145e0a`, 2026-07-11

---

## Anti-patterns (Cách tránh)

### 30. Direct Main Branch Local Commits
- **Vấn đề**: Thực hiện commit trực tiếp các thay đổi lên nhánh `main` cục bộ trước khi push. Việc này vi phạm rào chắn Git (Git Guardrails) và sẽ bị chặn khi push lên remote do chính sách bảo vệ nhánh main protection của GitHub.
- **Thay thế bằng**: Chạy `git reset HEAD~1` để hoàn tác commit nhưng giữ nguyên code sửa đổi, sau đó tạo và checkout sang nhánh tính năng mới (`git checkout -b feat/...`) rồi mới commit và push.

### 31. Broken Document Validation for Missing Env Examples
- **Vấn đề**: Bổ sung tài liệu ADR có nhắc tới các biến môi trường mới mà quên không cập nhật các mẫu biến này vào tệp cấu hình mẫu `.env.example`, gây ra cảnh báo `Env Var Warning` hàng loạt từ linter `validate_docs.py`.
- **Thay thế bằng**: Luôn khai báo mẫu các biến cấu hình mới vào cuối tệp `.env.example` song song với việc viết tài liệu thiết kế.

### 32. Static Video Analysis Storage (Lưu trữ tĩnh kết quả phân tích video)
- **Vấn đề**: Lưu kết quả phân tích video tại thư mục tĩnh dùng chung (như `.md/youtube-learn/`), dẫn đến việc dữ liệu bị ghi đè khi chạy nhiều video và phá vỡ cấu trúc gom nhóm thư mục Đề tài Chuyên biệt.
- **Thay thế bằng**: Sử dụng ID video hoặc băm hash để tạo thư mục ảnh slide động (`images_[video_id]/`) và tệp kết quả động (`notes_concept_[video_id].md`), đồng thời cung cấp tham số đề tài để gom nhóm vào `.md/projects/[Ten_De_Tai]/`.

### 33. Outdated Command and File References (Tham chiếu tệp và lệnh lỗi thời)
- **Vấn đề**: Giữ lại các tham chiếu của tài liệu cũ `PRD` và các lệnh đã xóa như `/ccba-to-prd` hoặc `/ccba-to-issues` trong tài liệu đặc tả, hướng dẫn (`ask`, `code-review`, `ccba-setup-skills`, `AGENTS.md`) dễ gây nhầm lẫn và lỗi thực thi cho Agent.
- **Thay thế bằng**: Rà quét và đồng bộ hóa toàn diện thuật ngữ từ `PRD` sang `Spec` và cập nhật các lệnh thành `/ccba-to-spec` và `/ccba-to-tickets` trong tất cả các tệp cấu hình và đặc tả.

### 34. Bypassing GitHub CI Block via CLI Admin Privilege (Ghi đè merge admin qua GitHub CLI)
- **Vấn đề**: Tài khoản GitHub bị lỗi thanh toán khiến toàn bộ Actions CI bị treo/fail ngay khi chạy, làm chặn việc merge PR theo quy trình tự động.
- **Thay thế bằng**: Xác thực hoàn toàn chất lượng code bằng các công cụ validation cục bộ (`validate_skills.py`, `validate_docs.py`), sau đó sử dụng cờ `--admin` của GitHub CLI (`gh pr merge --admin`) để merge PR trực tiếp bằng quyền Administrator.

### 35. VS Code Multi-repo Auto-discovery Ignored Repositories (Quy tắc bỏ qua Git Repo phụ trong VS Code)
- **Ngữ cảnh**: VS Code tự động phát hiện các Git repo tạm thời của subagents nằm sâu trong thư mục AppData và hiển thị trong Source Control.
- **Giải pháp**:
  - Khai báo đường dẫn tuyệt đối chính xác của thư mục worktree con trong tùy chọn `"git.ignoredRepositories"` của `.vscode/settings.json`.
  - Cấu hình `"git.autoRepositoryDetection": "subFolders"` để hạn chế VS Code tự động quét các Git repo nằm ngoài thư mục dự án hiện tại.
  - Sử dụng tùy chọn UI "Close Repository" trên VS Code để làm sạch cache giao diện hiển thị.

### 36. Git Ignore Database files (Chặn theo dõi tệp mật bằng .gitignore)
- **Ngữ cảnh**: Các file kiểm thử nhạy cảm như `*.db` và `secret_credential.*` sinh ra từ các phiên thử nghiệm của subagent có thể vô tình bị staging.
- **Giải pháp**: Bổ sung cấu hình chặn toàn cục `secret_credential.*` và `*.db` (cùng loại trừ `!Thumbs.db` của OS) vào tệp `.gitignore` dự án chính.

### 37. Subagent Worktree Hard Cleanup (Dọn dẹp triệt để thư mục làm việc của subagent)
- **Ngữ cảnh**: Thư mục làm việc tạm thời của subagent chứa các thay đổi thử nghiệm hoặc tệp rác bị drift gây báo động đỏ trên IDE của kỹ sư.
- **Giải pháp**: Sử dụng Agent chính truy cập trực tiếp qua CLI vào worktree của subagent đó và thực thi `git reset --hard HEAD && git clean -fd` để đưa trạng thái về sạch hoàn toàn.

### 47. Isolated CLI AI Agent Skill Evaluations (Kiểm thử cô lập kỹ năng AI Agent qua CLI)
- **Ngữ cảnh**: Cần kiểm thử sự tương tác giữa mô hình LLM và một Skill AI (system instructions của skill) một cách cô lập, tránh việc mô hình "ăn gian" bằng cách đọc lịch sử hội thoại cũ hoặc dữ liệu cache từ sandbox.
- **Giải pháp**: Thiết lập script Python CLI (`eval_runner.py`) để nạp trực tiếp file `SKILL.md` tương ứng làm system instruction cô lập, đọc test cases cấu hình JSON (gồm cả Happy path và Negative path để chống over-triggering), thực hiện gọi LLM độc lập, và đối sánh kết quả bằng Regex Asserts hoặc LLM-as-a-Judge chấm điểm bằng Rubric. Hỗ trợ tham số `--trials` để chạy nhiều lần nhằm đo lường độ tin cậy do tính phi định tính (non-deterministic) của mô hình.
- **Nguồn**: Session `0952c8e6-7f38-42e8-a5d7-4ed0d34d034f`, 2026-07-20

### 48. Boundary-Driven Prompt Steering for Over-triggering (Định nghĩa ranh giới kích hoạt để chống over-triggering)
- **Ngữ cảnh**: AI Agent được trang bị một skill chuyên biệt (ví dụ: PCCC audit) có xu hướng kích hoạt nhầm hoặc áp đặt logic của skill đó vào các yêu cầu thông thường (như lắp ổ điện gia dụng), gây ra lỗi Over-triggering.
- **Giải pháp**: Bổ sung mục rõ ràng **Khi nào sử dụng (When to use)** và **Khi nào KHÔNG sử dụng (When NOT to use)** (Negative cases) trực tiếp vào tệp `SKILL.md` để mô hình nắm rõ ranh giới áp dụng và trả lời trực tiếp các câu hỏi ngoài phạm vi mà không áp đặt quy trình của skill.
- **Nguồn**: Session `0952c8e6-7f38-42e8-a5d7-4ed0d34d034f`, 2026-07-20

### 38. Local CI Simulation for Billing Issues
- **Ngữ cảnh**: Khi GitHub Actions CI bị tạm dừng hoặc lỗi lập hóa đơn (Billing / Spending Limit) khiến không thể kiểm tra chất lượng code tự động từ PR.
- **Giải pháp**: Xây dựng kịch bản chạy thử nghiệm cục bộ mô phỏng các Gates của CI (`run_harness_evals.py --all`, `validate_docs.py`, và `ruff`) để xác nhận mã nguồn đạt 100% chất lượng trước khi thực hiện merge PR thủ công.
- **Nguồn**: Session `948e08e9-1c85-4029-86a4-70c8b70681d3`, 2026-07-16

### 39. Multi-PR Zombie Branch Triage
- **Ngữ cảnh**: Triage số lượng lớn các PR mở bị tồn đọng lâu ngày trong dự án và có lịch sử rẽ nhánh rất xa.
- **Giải pháp**: Sử dụng lệnh `git log main..branch` để lọc ra các commit độc nhất. Nếu số lượng commit độc nhất bằng 0, nghĩa là các thay đổi đã được nhập vào `main` qua các PR hoặc commit khác từ trước. Cần đóng thẳng các PR này dưới dạng `Already Merged` để dọn dẹp hệ thống thay vì cố merge gây conflict.
- **Nguồn**: Session `948e08e9-1c85-4029-86a4-70c8b70681d3`, 2026-07-16

---

## Anti-patterns (Cách tránh)

### 35. Running Async Pytest without pytest-asyncio
- **Vấn đề**: Chạy các unit tests được đánh dấu `@pytest.mark.asyncio` hoặc chứa hàm `async def` trong khi môi trường ảo `.venv` chưa được cài đặt thư viện `pytest-asyncio`. Điều này dẫn đến các cảnh báo `Unknown pytest.mark.asyncio` và gây lỗi kiểm thử hàng loạt với thông báo không rõ ràng như `"async def functions are not natively supported"`.
- **Thay thế bằng**: Luôn khai báo `pytest-asyncio` trong phần dev dependencies (`pyproject.toml`) và đảm bảo nó được cài đặt đầy đủ trong `.venv` trước khi thực thi `pytest`.

### 36. Dangling Git Worktrees Blocking Branch Deletion
- **Vấn đề**: Để lại các thư mục worktree tạm thời được tạo ra bởi các subagent, dẫn đến việc Git chặn hoàn toàn lệnh xóa nhánh cục bộ (`git branch -D`).
- **Thay thế bằng**: Luôn thực hiện dọn dẹp và gỡ bỏ worktree bằng lệnh `git worktree remove --force <path>` trước khi xóa các nhánh.

---

## Patterns (Mẫu tốt) — Dual-Mode & Security Upgrades (2026-07-19)

### 40. Global AppData Credentials Migration (Di trú credentials toàn cục an toàn)
- **Ngữ cảnh**: Cần lưu trữ và sử dụng OAuth credentials an toàn mà không sợ rò rỉ lên Git, đồng thời hỗ trợ Single Sign-On (SSO) để các Spokes cùng chia sẻ một token.
- **Giải pháp**: 
  - Di dời file credentials ra ngoài workspace dự án, lưu trữ tại thư mục Home của hệ điều hành (ví dụ: `~/.ccba/credentials/`).
  - Viết logic tự động kiểm tra và di chuyển (auto-migration) các file credentials cũ tại thư mục nháp tạm `.md/scratch/` sang thư mục Home ngay trong lần chạy đầu tiên để bảo toàn trạng thái đăng nhập cũ.
- **Nguồn**: Session `3e0991fe-f84e-4404-8fc6-e21c68cb9050`, 2026-07-19

### 41. Staged-Only Git Pre-commit Security Hook (Hook pre-commit chỉ quét staged files)
- **Ngữ cảnh**: Cần chạy quét leak bảo mật (Maskara) khi commit để phát hiện sớm các API keys nhưng tránh bị nghẽn build do quét toàn bộ repository hoặc rà trúng các tệp không track như `.env`.
- **Giải pháp**: Cấu hình hook pre-commit sử dụng `git diff --cached --name-only --diff-filter=d` để chỉ lấy danh sách các tệp đã stage. Lọc bỏ các tệp nhị phân/hình ảnh và thư mục tạm `.md/scratch/`, sau đó chỉ thực hiện lệnh quét Maskara trên các tệp này.
- **Nguồn**: Session `3e0991fe-f84e-4404-8fc6-e21c68cb9050`, 2026-07-19

### 42. Selective CI Security Exit Codes (Exit code CI chọn lọc theo mức độ nghiêm trọng)
- **Ngữ cảnh**: Khi chạy Maskara leak scan trên CI/CD, các mock key dạng ví dụ trong tài liệu (`SECRET_KEY=secret123`) có thể bị khớp pattern và làm đỏ build CI một cách không cần thiết, trong khi chúng chỉ có độ nghiêm trọng thấp/trung bình.
- **Giải pháp**: Cấu hình Maskara chỉ trả về exit code lỗi (`exit 1`) đối với các findings có độ nghiêm trọng `critical` hoặc `high` (API keys thực sự). Các findings `medium` (mock code/placeholders) vẫn được báo cáo đầy đủ thông tin để kỹ sư rà soát nhưng không làm treo/fail build CI.
- **Nguồn**: Session `3e0991fe-f84e-4404-8fc6-e21c68cb9050`, 2026-07-19

### 43. GitHub CLI-based API Sync Fallback (Đồng bộ dự phòng qua GitHub CLI)
- **Ngữ cảnh**: Khi các công cụ MCP hoặc thư viện tích hợp API của GitHub gặp sự cố xác thực (lỗi token / Bad credentials) trong sandbox bảo mật của Agent, làm gián đoạn việc lấy danh sách sự cố hoặc tạo PR.
- **Giải pháp**: Tận dụng trực tiếp công cụ CLI `gh` đã được xác thực an sau trên môi trường máy của kỹ sư. Chạy các lệnh CLI (như `gh issue list`, `gh pr create`) qua `subprocess` của Python để thực thi các tác vụ API một cách tin cậy và không phụ thuộc vào token API cục bộ của Agent.
- **Nguồn**: Session `f19748c3-84c2-4940-ac7f-7c3488932757`, 2026-07-19

### 44. Worktree Divergent Branch Merging via API (Merge nhánh bị khóa worktree qua GitHub API)
- **Ngữ cảnh**: Gặp lỗi `fatal: 'main' is already used by worktree` khi chạy merge nhánh bằng dòng lệnh thông thường (`gh pr merge`) vì nhánh `main` đang được check out và làm việc tại một worktree Git cục bộ khác.
- **Giải pháp**: Gửi yêu cầu merge trực tiếp lên máy chủ GitHub thông qua Web API (`gh api -X PUT repos/.../pulls/<pr_id>/merge`) mà không cần check out hay đồng bộ nhánh main cục bộ, giúp tránh hoàn toàn xung đột khóa file worktree trên Windows.
- **Nguồn**: Session `f19748c3-84c2-4940-ac7f-7c3488932757`, 2026-07-19

### 45. HTML Marker Injection for Auto-Stats (Tự động cập nhật số liệu qua thẻ HTML)
- **Ngữ cảnh**: Các tài liệu kiến trúc (như README, PLATFORM) thường chứa các số liệu tĩnh (ví dụ: "có 53 skills", "có 10 workflows") rất dễ bị lỗi thời (drift) khi dự án phát triển.
- **Giải pháp**: Nhúng các thẻ HTML ẩn (ví dụ: `<!-- KEY_START: SKILL_COUNT -->...<!-- KEY_END -->`) vào tài liệu Markdown. Viết script chạy trong SDLC pipeline để tự động đếm và tiêm (inject) các số liệu mới nhất vào giữa các thẻ này.
- **Nguồn**: Session `3e0991fe-f84e-4404-8fc6-e21c68cb9050`, 2026-07-19

### 46. Architecture Drift Detection via Git Diff (Phát hiện trôi dạt kiến trúc bằng Git Diff)
- **Ngữ cảnh**: Ngăn chặn lập trình viên thêm/xóa thư mục hoặc file cấu trúc lõi (như skills, workflows, packages) mà quên không cập nhật các tài liệu mô tả kiến trúc tương ứng.
- **Giải pháp**: Tích hợp lệnh `git diff --name-only origin/main...HEAD` (hoặc `HEAD` trên môi trường local) vào CI validation script. Nếu phát hiện thay đổi trong các thư mục lõi nhưng các file tài liệu nền tảng (`README.md`, `PLATFORM.md`) không thay đổi tương ứng, script sẽ trả về Exit Code 1 và chặn build CI.
- **Nguồn**: Session `3e0991fe-f84e-4404-8fc6-e21c68cb9050`, 2026-07-19

---

## Anti-patterns (Cách tránh) — Dual-Mode & Security Upgrades (2026-07-19)

### 37. Full-Workspace Pre-commit Scan (Quét toàn bộ workspace tại commit)
- **Vấn đề**: Để pre-commit hook chạy quét toàn bộ thư mục gốc dự án (`--root .`). Điều này làm tốc độ commit cực kỳ chậm khi dự án phình to, và luôn bị chặn do các file cấu hình local không track như `.env` hoặc mock keys trong các file clone nháp tạm.
- **Thay thế bằng**: Chỉ trích xuất danh sách staged files và chạy quét Maskara độc lập trên từng file.

### 38. Monolithic CI Exit Code on Mock Keys (Exit code CI cứng nhắc chặn mock keys)
- **Vấn đề**: Cấu hình lệnh quét bảo mật trả về exit code lỗi và chặn build cho bất kỳ cảnh báo nào (kể cả mock keys hay ví dụ code ở mức `medium`), gây cản trở và treo pipeline CI/CD vô ích.
- **Thay thế bằng**: Chỉ kích hoạt fail build CI đối với các phát hiện độ nghiêm trọng cao `critical` và `high` (các key thực tế có cấu trúc regex đặc thù).

### 39. Ambiguous Variable Name E741 in Comprehensions (Tên biến mơ hồ E741 trong vòng lặp)
- **Vấn đề**: Sử dụng tên biến một chữ cái như `l` hoặc `I` trong list comprehensions (như `[l["name"] for l in labels]`). Linter Ruff sẽ báo lỗi E741 do các ký tự này dễ bị nhầm lẫn về mặt thị giác với số 1 hoặc chữ I hoa trên màn hình code.
- **Thay thế bằng**: Sử dụng các tên biến rõ nghĩa hơn như `lbl`, `item`, hoặc `label_item`.

### 40. Manual Metric Updates in Docs (Cập nhật số liệu thủ công trong tài liệu)
- **Vấn đề**: Bắt buộc nhà phát triển phải tự đếm và sửa bằng tay các con số tổng kết (số lượng package, số lượng file nhạy cảm) trong README hoặc PLATFORM.md mỗi khi tạo PR, gây tốn thời gian và dễ sai sót.
- **Thay thế bằng**: Thay thế bằng việc nhúng HTML markers và tự động cập nhật qua CI pipeline (`update_arch_stats.py`).

---

## Session Learnings — Document Processing Skills & AI Evals Refinement (2026-07-21)
- **ID Phiên làm việc**: `3df38a11-df52-46c4-883c-f9cdcc0eefec`

### Patterns (Mẫu tốt)

#### 49. Flat Directory Skill Governance via Frontmatter & Virtual Tagging
- **Ngữ cảnh**: Cần phân cấp cấu trúc Master Skill vs Sub-Skill cho nhóm kỹ năng xử lý văn bản (`xu-ly-van-phong`, `markdown-document-processing`, `copywriting`, `academic_writing`) mà không làm thay đổi vị trí thư mục vật lý phẳng (`.agents/skills/<name>/`) gây đứt gãy liên kết ở các dự án Spoke và CI gates.
- **Giải pháp**:
  * Giữ nguyên cấu trúc thư mục phẳng vật lý của tất cả skills.
  * Phân cấp logic trong YAML Frontmatter bằng thuộc tính `role: master_skill` (khai báo `sub_skills: [...]`) và `role: sub_skill` (khai báo `master_skill: <name>`).
  * Thực hiện gán nhãn ảo trong `catalog.yaml` bằng `tags: [document, writing]` để nhóm các skill cùng bộ môn.
  * Thêm quy tắc định tuyến vào `platform-loader/SKILL.md` buộc Agent luôn nạp Master Skill trước khi thực thi các Sub-skills vi mô.
- **Nguồn**: Session `3df38a11-df52-46c4-883c-f9cdcc0eefec`, 2026-07-21

#### 50. Multi-Alias Skill Resolution in AI Eval Runner
- **Ngữ cảnh**: Tên của Skill công khai (public alias) như `markdown-document-processing` có thể khác với tên thư mục thực tế trên hệ thống file như `markdown-processing`. Khi chạy `/ccba-skills-eval` dẫn tới lỗi không tìm thấy `SKILL.md`.
- **Giải pháp**: Bổ sung hàm `get_skill_path(skill_name)` trong `eval_runner.py`. Nếu đường dẫn trực tiếp `.agents/skills/<name>/SKILL.md` không tồn tại, tự động tra cứu danh mục `catalog.yaml` theo key `skill_path` để giải quyết chính xác vị trí tệp `SKILL.md`.
- **Nguồn**: Session `3df38a11-df52-46c4-883c-f9cdcc0eefec`, 2026-07-21

#### 51. Negative Constraint Prompt Guard for Placeholder Hallucination
- **Ngữ cảnh**: Trong quá trình kiểm thử AI Evals cho `markdown-document-processing`, mô hình sinh chuỗi placeholder `...` làm đứt đoạn nội dung đoạn văn, vi phạm tiêu chí phân đoạn hoàn chỉnh.
- **Giải pháp**: Bổ sung mục `## 🛑 Điều cấm & Quy tắc rào chắn` trực tiếp vào `markdown-processing/SKILL.md` cấm tuyệt đối sử dụng các ký tự giữ chỗ `...`, nâng tỷ lệ Pass của AI Evals từ 66.7% lên **100% PASS**.
- **Nguồn**: Session `3df38a11-df52-46c4-883c-f9cdcc0eefec`, 2026-07-21

---

#### 52. Post-Session Workspace Hygiene via Subagent Review
- **Ngữ cảnh**: Phiên làm việc trước kết thúc với workspace bẩn: file mới chưa commit (`safe_runner.py`), 11 file modified chưa staged, `coverage.xml` (generated artifact) lẫn trong tracked files, wayfinder map chưa cập nhật trạng thái.
- **Giải pháp**:
  * Dùng research subagent chạy `git diff` từng file song song, phân loại từng thay đổi thành: intentional/correct vs leftover/debug artifact.
  * Nhóm thành logical commit units theo scope (core feature → tests → docs → tooling), mỗi commit có message chuẩn `type(scope): description`.
  * Loại bỏ generated artifacts (`coverage.xml`) bằng `git checkout --` + thêm vào `.gitignore` + `git rm --cached`.
- **Nguồn**: Session `4f56855a-16fb-48db-9eee-75fab8d7f0ae`, 2026-07-22

#### 53. Safe Runner Detached Process Pattern for Daemon-Resilient Execution
- **Ngữ cảnh**: Antigravity Daemon restart giữa chừng → tất cả `run_command` đang chạy bị cancel ("User cancelled agent execution"), đặc biệt nghiêm trọng với pytest suite dài.
- **Giải pháp**:
  * Script `scripts/safe_runner.py` (151 LOC) nhận `--command` và chạy subprocess cô lập (`subprocess.Popen` với `CREATE_NEW_PROCESS_GROUP` trên Windows).
  * Ghi stdout/stderr vào `.md/scratch/exec_log.txt`, trạng thái vào `.md/scratch/exec_status.json`.
  * Mode `--status` kiểm tra PID còn sống (OpenProcess trên Windows, `os.kill(pid, 0)` trên Unix) và hiển thị tail 20 dòng log.
  * Kết quả: 23/23 tests PASSED qua safe_runner mà không bị cancel.
- **Nguồn**: Session `4f56855a-16fb-48db-9eee-75fab8d7f0ae`, 2026-07-22

---

### Anti-patterns (Cách tránh)

#### 41. Physical Nested Skill Directory Refactoring
- **Vấn đề**: Di chuyển các tệp sub-skill vào các thư mục con phân cấp (ví dụ: `.agents/skills/xu-ly-van-phong/docx/SKILL.md`). Điều này gây hỏng toàn bộ đường dẫn tương đối trong `catalog.yaml`, đứt gãy linter `validate_docs.py`, và gây crash các dự án Spoke khi đồng bộ.
- **Thay thế bằng**: Duy trì thư mục vật lý phẳng 100% tại `.agents/skills/` và sử dụng YAML Frontmatter `role: master_skill / sub_skill` và virtual tagging trong `catalog.yaml` để quản trị phân cấp.

#### 42. Agent Loop-Fix Without Global State Check
- **Vấn đề**: Agent phiên trước cố sửa lỗi `safe_runner.py` bằng cách lặp edit → run → fail → edit liên tục (5+ vòng lặp) mà không dừng lại kiểm tra toàn cảnh (biến nào undefined, flow nào sai). Kết quả: tốn context window, gây frustration cho người dùng, và để lại workspace bẩn.
- **Thay thế bằng**: Khi gặp lỗi lần thứ 2 liên tiếp trên cùng file, DỪNG lại, đọc toàn bộ file từ đầu, xác định root cause trước khi sửa tiếp. Không sửa mù dựa trên error message đơn lẻ.

---

## Session Learnings — System Stability & Auto-Guardrails (2026-07-22)
- **ID Phiên làm việc**: `9d5aaadb-caba-4a73-a23a-d8ce3d75941a`

### Patterns (Mẫu tốt)

#### 54. Singleton Process Lock for High-Resource Test Runners
- **Ngữ cảnh**: Khi chạy các lệnh kiểm thử CI Gates (`run_harness_evals.py`) hoặc background tasks, việc gọi trùng lặp nhiều lần khiến nhiều tiến trình Python ngốn 100% CPU/RAM làm IDE Extension Host bị ngắt kết nối (`User cancelled agent execution`) và Agent bị restart.
- **Giải pháp**: Tích hợp hàm `ensure_single_instance()` sử dụng `psutil` (hoặc `wmic`/`taskkill` fallback trên Windows) ở ngay đầu hàm `main()` của runner script để tự động phát hiện PID trùng lặp và triệt hạ (`terminate`) tiến trình cũ trước khi khởi chạy đợt kiểm thử mới.
- **Nguồn**: Session `9d5aaadb-caba-4a73-a23a-d8ce3d75941a`, 2026-07-22

#### 55. Pre-Eval Workspace Health & Resource Guardrail
- **Ngữ cảnh**: Khởi chạy tác vụ kiểm thử hoặc build ngầm khi dung lượng đĩa khả dụng quá thấp hoặc môi trường ảo thiếu phụ thuộc, dẫn đến crash giữa chừng.
- **Giải pháp**: Tích hợp kiểm tra sức khỏe `check_pre_eval_health()` (dùng `shutil.disk_usage`) trước khi khởi chạy các gates để cảnh báo khi dung lượng đĩa < 2GB và khuyến nghị dọn dẹp không gian workspace qua `session_cleanup.py`.
- **Nguồn**: Session `9d5aaadb-caba-4a73-a23a-d8ce3d75941a`, 2026-07-22

#### 56. Bounded Async Task & Anti-Duplicate Runner Policy
- **Ngữ cảnh**: Agent tự động kích hoạt nhiều tác vụ ngầm trùng lặp cho cùng một script test runner trong cùng một phiên làm việc.
- **Giải pháp**: Bổ sung rào chắn **Anti-Duplicate Background Runner** và **Bounded Async Task** vào Hiến pháp `AGENTS.md`, cưỡng chế Agent luôn chờ kết quả hoặc gỡ bỏ tiến trình cũ trước khi khởi tạo tác vụ ngầm mới.
- **Nguồn**: Session `9d5aaadb-caba-4a73-a23a-d8ce3d75941a`, 2026-07-22

---

### Anti-patterns (Cách tránh)

#### 43. Unlocked Duplicate Background Test Runners
- **Vấn đề**: Kích hoạt đồng thời nhiều background tasks chạy `run_harness_evals.py --all` mà không có cơ chế Auto-Lock hoặc cancellation tiến trình trước. Điều này khiến CPU/RAM bị đẩy lên 100%, gây đứt kết nối IPC và restart IDE Extension Host.
- **Thay thế bằng**: Sử dụng Auto-Lock Singleton `ensure_single_instance()` + Mặc định Scoped Evaluation (chạy theo git diff).


---

## Session Learnings — Safe Execution Sandbox & Technical Debt Cleanup (2026-07-23)
- **ID Phiên làm việc**: `ef5005bc-3ed1-4118-80c9-7053d12c4522`

### Patterns (Mẫu tốt)

#### 57. Safe Execution Sandbox Wrapper (`run_safe_eval_wrapper.py`) with Structured Diagnostics
- **Ngữ cảnh**: Các lệnh terminal kiểm thử (pytest, ruff, mypy) chạy đồng bộ bị ngắt ngang bởi AbortSignal của IDE Host khi quá 30-45s, gây ra thông báo giả lập "User cancelled agent execution".
- **Giải pháp**: Bọc thực thi bằng script `run_safe_eval_wrapper.py` tích hợp `subprocess.Popen`, Timeout Watchdog (90s), Auto-Lock Singleton `ensure_single_instance()`, cô lập file log tại `.md/scratch/eval_runs/run_<timestamp>.log` và tự động trích xuất báo cáo cấu trúc `diagnostics.json` với `status: PASS | FAILED | TIMEOUT`, `error_type`, `failed_gate`, `culprit_file` và `summary_traceback`.
- **Nguồn**: Session `ef5005bc-3ed1-4118-80c9-7053d12c4522`, 2026-07-23

#### 58. PEP 561 `py.typed` Marker Injection for Monorepo Mypy Resolution
- **Ngữ cảnh**: Khi Mypy chạy trên monorepo chứa nhiều packages (`packages/mdconverter`, `packages/ccba-ai`), Mypy bỏ qua việc phân tích các module nội bộ (`Skipping analyzing ... missing py.typed marker`) và báo 75+ lỗi giả lập "Class cannot subclass BaseConverter (has type Any)".
- **Giải pháp**: Thêm tệp marker rỗng `py.typed` vào thư mục gói chính (`packages/<pkg>/src/<pkg>/py.typed`) và cấu hình `mypy_path = ["packages/<pkg>/src"]` trong `pyproject.toml` để Mypy nhận diện 100% type annotations của các gói nội bộ.
- **Nguồn**: Session `ef5005bc-3ed1-4118-80c9-7053d12c4522`, 2026-07-23

#### 59. Blacklist Directory Filtering in Recursive Markdown Linters
- **Ngữ cảnh**: Hàm `lint_directory()` duyệt đệ quy `rglob("*.md")` trên toàn thư mục gốc dự án, đọc toàn bộ nội dung của hàng nghìn file Markdown tạm (`.md/scratch/`, `.md/extracted_docs/`, `.venv/`), dẫn đến Pytest Timeout 10s.
- **Giải pháp**: Bổ sung bộ lọc danh sách đen `EXCLUDED_DIRS = {".venv", ".git", ".md", "node_modules", "build", "dist", "__pycache__"}` trong hàm `lint_directory()`, bỏ qua việc quét file thuộc các thư mục tạm.
- **Nguồn**: Session `ef5005bc-3ed1-4118-80c9-7053d12c4522`, 2026-07-23

#### 60. Fast Mock Network Exceptions in Async API Error Unit Tests
- **Ngữ cảnh**: Sử dụng hostname giả lập chưa đăng ký DNS (như `http://invalid:9999`) trong unit test khiến `httpx`/`asyncio` trên Windows ngâm kết nối 30 giây để chờ DNS resolution timeout, làm Pytest dính timeout.
- **Giải pháp**: Sử dụng `patch.object(GatewayProvider, 'generate', side_effect=httpx.ConnectError(...))` hoặc địa chỉ localhost từ chối kết nối tức thì `http://127.0.0.1:1` trong unit test để kiểm tra bẫy lỗi API mà không gây độ trễ mạng.
- **Nguồn**: Session `ef5005bc-3ed1-4118-80c9-7053d12c4522`, 2026-07-23

---

## Session Learnings — 5-Layer Defense Model & Dependabot CI Guardrails (2026-07-24)
- **ID Phiên làm việc**: `de07cc2b-5990-47a3-afa4-e1c7ff2626b6`

### Patterns (Mẫu tốt)

#### 61. 5-Layer Defense Model for AI Skills Evals & Legal Guardrails
- **Ngữ cảnh**: Các bài test kiểm thử AI Skill bị nhiễu do prompt câu hỏi đơn giản (như sort, fibonacci), bị false negative do câu trả lời từ chối lịch sự (disclaimer) của LLM, và linter pháp lý sử dụng luật xây dựng đã hết hiệu lực.
- **Giải pháp**: 
  - **Tầng 1 (Domain-Adjacent Standard)**: Thay các prompt lập trình chung bằng các tình huống giáp ranh thuộc bộ môn khác để thử thách độ chính xác ranh giới của skill.
  - **Tầng 2 (Disclaimer-Aware Assertions)**: Khóa các định danh thành phẩm chính (`checklist_master.yaml`, `Phụ lục VIb`) trong negative regex thay vì tên skill chung để không bị đánh lừa bởi câu disclaimer lịch sự của LLM.
  - **Tầng 3 (Automated Noise Linter)**: Tích hợp bộ quét mẫu noise prompt (`quicksort`, `fibonacci`, `bubble sort`...) trong `eval_runner.py --dry-run` để tự động phát hiện và chặn các câu hỏi test thiếu thực tế.
  - **Tầng 4 (Superseded Legal Doc Linter)**: Tăng cường `validate_docs.py` phát hiện số hiệu luật cũ (Luật Xây dựng 2014) và cưỡng chế số hiệu luật mới chuẩn xác (**Luật Xây dựng 2025 số 135/2025/QH15** & **NĐ 105/2025/NĐ-CP**).
  - **Tầng 5 (Production Log Mining with Maskara Privacy Redaction)**: Bóc tách dữ liệu tương tác thực từ `transcript.jsonl`, redact thông tin nhạy cảm qua `maskara-privacy`, và tự động xuất thành test cases kiểm thử liên tục.
- **Nguồn**: Session `de07cc2b-5990-47a3-afa4-e1c7ff2626b6`, 2026-07-24

#### 62. Dependabot Semver-Major Ignore Guardrail
- **Ngữ cảnh**: Dependabot tự động khởi tạo PRs hàng tuần nâng cấp các GitHub Actions (`checkout`, `setup-python`) lên phiên bản major (`v7`) gây hỏng toàn bộ pipeline CI.
- **Giải pháp**: Khai báo cấu hình `ignore` quy tắc `update-types: ["version-update:semver-major"]` dưới `package-ecosystem: "github-actions"` trong `.github/dependabot.yml` để duy trì các bản patch/minor security updates nhưng chặn các bản major gây gãy pipeline.
- **Nguồn**: Session `de07cc2b-5990-47a3-afa4-e1c7ff2626b6`, 2026-07-24

#### 63. Scoped Test Execution Interceptor in Pytest (`conftest.py`)
- **Ngữ cảnh**: Chạy lệnh `pytest` unscoped trên toàn bộ workspace gây bùng nổ context window và làm ngắt phiên làm việc của Agent.
- **Giải pháp**: Sử dụng hook `pytest_cmdline_main` trong `conftest.py` để chặn đứng các lệnh `pytest` unscoped, trừ khi có tham số `--allow-unscoped` hoặc biến môi trường `CI=true` / `GITHUB_ACTIONS=true` từ GitHub Actions runner.
- **Nguồn**: Session `de07cc2b-5990-47a3-afa4-e1c7ff2626b6`, 2026-07-24

---

### Anti-patterns (Cách tránh)

#### 44. Unfiltered Major Version Actions Upgrades by Dependabot
- **Vấn đề**: Để Dependabot tự do nâng cấp major version của các GitHub Actions mà không có cấu hình `ignore`, khiến các PRs nâng cấp v6/v7 liên tục được tạo ra làm hỏng CI.
- **Thay thế bằng**: Khai báo rào chắn `ignore semver-major` trong `dependabot.yml` cho `github-actions`.

---

## Session Learnings — Legal Intel Deep Module, VBHN Merger & Execution Stability (2026-07-25)
- **ID Phiên làm việc**: `0c0a9304-cfbb-4fa3-9c81-3e11441ace97`

### Patterns (Mẫu tốt)

#### 64. Article-Scoped Chunking & Double-Pass Alignment Verification
- **Ngữ cảnh**: Sinh `delta_patch.yaml` sửa đổi văn bản pháp luật lớn bằng LLM (`ccba-ai`).
- **Giải pháp**: Phân đoạn Markdown theo từng Điều (`Điều X`), gửi prompt qua `ai.chat()`, và thực hiện dry-run verification (`apply_patch_dry_run()`) để đối soát neo chuỗi (`old_text_anchor`) trước khi nạp vào AST Merger. Tránh trôi neo chuỗi hoặc nhầm lẫn giữa các khoản.
- **Nguồn**: Session `0c0a9304-cfbb-4fa3-9c81-3e11441ace97`, 2026-07-25

#### 65. Visual Diff Markdown Exporter (`~~` Strikethrough & Footnote Citations)
- **Ngữ cảnh**: Trình bày tệp hợp nhất VBHN (`VBHN_{slug}.md`) trực quan cho kỹ sư/chủ đầu tư đọc.
- **Giải pháp**: Render các đoạn bị bãi bỏ bằng gạch ngang `~~text~~`, các đoạn sửa đổi bằng `+ text`, và tự động chèn chú thích chân trang (footnotes `[^1]`) trích dẫn văn bản sửa đổi.
- **Nguồn**: Session `0c0a9304-cfbb-4fa3-9c81-3e11441ace97`, 2026-07-25

#### 66. Telegram VIP Alert & CAPTCHA Barrier Detector
- **Ngữ cảnh**: Cào dữ liệu TVPL gặp rào chắn Đăng nhập, hết hạn tài khoản VIP hoặc thử thách CAPTCHA.
- **Giải pháp**: Quét từ khóa HTML nhạy cảm ("đăng nhập", "captcha", "hết hạn") và kích hoạt Telegram Webhook alert bắn thẳng về Telegram group của quản trị viên kèm URL văn bản để can thiệp kịp thời.
- **Nguồn**: Session `0c0a9304-cfbb-4fa3-9c81-3e11441ace97`, 2026-07-25

---

### Anti-patterns (Cách tránh)

#### 45. Synchronous Unscoped Test Suite Execution (Lỗi "User Cancelled Agent Execution")
- **Vấn đề**: Kích hoạt `pytest` toàn bộ 88+ test cases trong lượt tương tác trực tiếp đồng bộ (synchronous turn) làm luồng chính bị timeout (>15-30s) hoặc dính lock đĩa (`_mutex.py`), dẫn đến hệ thống kích hoạt Circuit Breaker hủy tiến trình và bắn thông báo `"User cancelled agent execution"`.
- **Thay thế bằng**: Áp dụng rào chắn Scoped Testing (chỉ chạy pytest trên file test cụ thể trong TDD lượt trực tiếp — ví dụ 11 tests chỉ mất 5.45s), sử dụng cờ `-m "not slow"` để loại bỏ bài test chậm, và chuyển các bài test full suite sang Bounded Async Tasks.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*




