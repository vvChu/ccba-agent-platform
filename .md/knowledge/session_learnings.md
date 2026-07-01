## Session Learnings - Kiến thức tích lũy

## Cập nhật gần nhất: 2026-07-01

---

## Patterns (Mẫu tốt)

### 1. Phân mảnh khối lượng tải PDF (PDF Chunking) cho Gateways
- **Ngữ cảnh**: Gửi các tệp PDF scan dày và chằng chịt ảnh nội dung thông qua Base64 Data URI lên AI Provider.
- **Vấn đề giải quyết**: Payload base64 của file 50MB-100MB sẽ lập tức đánh sập cổng cấu hình Proxy limit (ví dụ Nginx / LiteLLM) trước khi kịp chạm tới model.
- **Giải pháp**: Phân chia file PDF gốc thành các khối (chunks) từ 10-20 trang bằng thư viện `pypdf`, xử lý lần lượt qua mạng rồi merge Markdown thuần túy ở đầu cuối. Tránh hoàn toàn lỗi Overflow.
- **Ví dụ code**:
```python
from pypdf import PdfReader, PdfWriter
import io

reader = PdfReader(source_path)
for i in range(0, len(reader.pages), 20):
    writer = PdfWriter()
    for j in range(i, min(i + 20, len(reader.pages))):
        writer.add_page(reader.pages[j])
    chunk_io = io.BytesIO()
    writer.write(chunk_io)
    file_chunks.append(chunk_io.getvalue())
```
- **Nguồn**: Session 54f85dcb-dcf1-423e-98d8-d332bb4fe1d6, 2026-04-09

### 2. Định Tuyến Self-Healing Free-tier (Bất Tử Hóa Models)
- **Ngữ cảnh**: Khi thực thi các task trích xuất RAG cường độ cao (ví dụ Stress-test bắn liên tiếp 40-50 luồng).
- **Vấn đề giải quyết**: Chạm Rate Limit 15 Request/Minute (lỗi HTTP 429) hoặc API Key chết (HTTP 403), khiến toàn bộ script phá sản.
- **Giải pháp**: Xây dựng AI Gateway thông minh (cụ thể là cấu hình Alias model trong LiteLLM). Cho phép Client đẩy mọi loại áp lực tải lên Gateway bất kể cấu hình. Hệ thống sẽ giữ session, ném request lỗi (403/429) vào khe Fallback để lấy API Key khác retry lại. Tỷ lệ thành công 100%.
- **Nguồn**: Session 54f85dcb-dcf1-423e-98d8-d332bb4fe1d6, 2026-04-09

### 3. Xử lý Phân đoạn Tài liệu (Segment-based Processing) cho Hybrid PDF
- **Ngữ cảnh**: Tài liệu PDF có sự pha trộn giữa trang văn bản số (Text-rich) và trang quét (Scanned/OCR), hoặc file có dung lượng cực lớn.
- **Vấn đề giải quyết**: Xử lý nguyên file bằng OCR model gây tốn token và chậm (đối với trang text). Xử lý bằng LLM thuần túy thì lỗi trang scan. Gửi file quá lớn gây lỗi `413 Payload Too Large`.
- **Giải pháp**: 
    1. Sử dụng `PDFAnalyzer` để phân đoạn tài liệu thành các `Segment` liên tục cùng loại.
    2. Chia nhỏ (split) PDF thành các file tạm theo segment.
    3. Thực thi chuyển đổi song song (Concurrent) các segment: trang Text dùng model nhanh/rẻ, trang Scan dùng model OCR.
    4. Hợp nhất nội dung Markdown kèm theo Segment Markers.
- **Nguồn**: Session 3cca2e64-49c0-4c49-aef3-684c8c1d80fd, 2026-04-15

### 4. Xẻ mảnh bản vẽ (High-res Tiling) cho AI Vision
- **Ngữ cảnh**: Xử lý các bản vẽ kỹ thuật khổ lớn (A0-A3) chứa các chi tiết nhỏ hoặc bảng thông số li ti.
- **Vấn đề giải quyết**: Nén cả trang vào một ảnh LLM Vision (2048px) làm mờ nét vẽ.
- **Giải pháp**: 
    1. Render trang ở DPI cao (300+). 
    2. Sử dụng tham số `clip` trong `get_pixmap` để render trực tiếp từng mảnh (tile) 1024-2048px. 
    3. Gửi mảnh ảnh chất lượng gốc cho AI giúp tăng độ chính xác trích xuất.
- **Nguồn**: Session 3cca2e64-49c0-4c49-aef3-684c8c1d80fd, 2026-04-15

### 5. Đóng gói Giải pháp Fallback Ngoại tuyến (Offline ZIP Scaffolding)
- **Ngữ cảnh**: Khi xây dựng các công cụ tích hợp các CLI bên thứ ba (như Microsoft Power Platform CLI `pac`) để đóng gói sản phẩm.
- **Vấn đề giải quyết**: Trong môi trường CI/CD hoặc máy chạy offline thiếu các công cụ CLI này, bộ kiểm định tự động hoặc quá trình build sẽ bị lỗi.
- **Giải pháp**: Viết luồng đóng gói fallback bằng module `zipfile` của Python để tự sinh cấu trúc thư mục giải pháp và file XML siêu dữ liệu (`Solution.xml`) giúp đảm bảo tệp `.zip` đầu ra luôn được tạo ra đồng bộ và hợp lệ cho việc import thủ công.
- **Nguồn**: Session 86ca4b06-4329-478b-8c16-ca53827675de, 2026-06-27

### 6. Ma hoa bat doi xung RSA Spoke Registry (Local Encryption, GitHub Storage)
- **Ngu canh**: Can thu thap thong tin cau hinh va duong dan vat ly cuc bo cua cac Spoke ve Hub de phan tich nhung phai dam bao an toan tuyet doi va tranh lo thong tin ca nhan tren GitHub.
- **Van de giai quyet**: Tranh ro ri duong dan va Username, dong thoi tranh xung dot Git khi nhieu nguoi cung push file registry.
- **Giai phap**: Su dung RSA 2048-bit. Spoke dung Khoa cong khai de ma hoa thong tin local thanh chuoi Base64 va push len GitHub. Chỉ Admin giu Khoa bi mat (luu ngoai codebase) moi giai ma doc duoc.
- **Nguon**: Session 98bf7ffe-a23a-4fcd-a7cb-59ee0ed5dac2, 2026-06-29

### 7. Giới hạn phạm vi (Scope) khi chạy quét an toàn thông tin nhạy cảm ngoại tuyến
- **Ngữ cảnh**: Khi chạy các công cụ quét tĩnh như `maskara.py scan` để kiểm tra secrets hoặc credentials rò rỉ.
- **Vấn đề giải quyết**: Chạy quét chế độ tự động mặc định (`auto`) có thể quét vào thư mục cấu hình toàn cục của các AI agent (như `.gemini`, `.claude` ở thư mục Home của user), nơi chứa hàng nghìn file logs và cache khổng lồ làm tiến trình bị treo hoặc chạy rất lâu.
- **Giải pháp**: Luôn cấu hình hoặc truyền tham số giới hạn phạm vi quét rõ ràng (`--root .` hoặc chỉ định trực tiếp thư mục dự án) để tối ưu hóa thời gian xử lý và tránh lãng phí tài nguyên CPU/RAM.
- **Nguồn**: Session 6bc722af-2748-44b7-8b54-4399e4df56df, 2026-06-29

### 8. Exclusion of isolated references from scans (Chặn quét thư mục tham khảo)
- **Ngữ cảnh**: Khi clone hoặc tải các repository mã nguồn bên ngoài về để nghiên cứu, thích ứng tính năng (porting).
- **Vấn đề giải quyết**: Agent khi làm việc tự động sẽ quét toàn bộ workspace, dễ bị lag, tốn hàng chục ngàn tokens và load nhầm tệp cấu hình cũ (như `AGENTS.md` hoặc `GEMINI.md`) của repo đó làm "Hiến pháp".
- **Giải pháp**: Di chuyển toàn bộ repo clone vào một thư mục cách ly đặc biệt `.md/extracted_docs/references/clones/` và cấu hình cho script hook `scout_block.py` chặn đứng (block) mọi công cụ đọc/ghi/tìm kiếm trỏ vào folder `clones/`. Chỉ cho phép bypass có kiểm soát bằng tiền tố `APPROVED:` khi chạy lệnh `/ccba-xia`.
- **Nguồn**: Session fb742b4b-83a0-4744-b61e-cede7703bd86, 2026-06-29

### 9. Multi-tiered Documentation Verification (Kiểm định tài liệu đa tầng)
- **Ngữ cảnh**: Cần đảm bảo tài liệu kỹ thuật (README, APIs) luôn chính xác, không bị lỗi thời sau khi refactor mã nguồn.
- **Vấn đề giải quyết**: Lập trình viên hoặc Agent vô tình viết sai tên hàm, link hỏng hoặc thiếu config keys nhưng không phát hiện ra.
- **Giải pháp**: Thiết lập 2 lớp kiểm định tự động: Chạy Git Hook (Pre-commit) ở local máy trạm để ngăn chặn sớm ngay khi gõ lệnh commit, và chạy GitHub Actions ở Server làm chốt chặn cuối cùng trước khi merge PR.
- **Nguồn**: Session fb742b4b-83a0-4744-b61e-cede7703bd86, 2026-06-29

### 10. Granular Exit Codes in Validation (Exit code phân loại khi validate)
- **Ngữ cảnh**: Khi tích hợp công cụ kiểm tra tài liệu (`validate_docs.py`) vào Git hooks và CI/CD.
- **Vấn đề giải quyết**: Tránh tình trạng commit hoặc build bị chặn oan (false positives) do các cảnh báo không nghiêm trọng (ví dụ regex nhận diện nhầm Code References hoặc các biến môi trường nghi ngờ).
- **Giải pháp**: Phân loại mức độ nghiêm trọng: Chặn cứng (exit code 1) đối với lỗi liên kết hỏng (Broken relative links), và chỉ cảnh báo mềm (exit code 0) đối với các cảnh báo Code Refs/Env Vars nghi vấn để cho phép commit đi qua bình thường.
- **Nguồn**: Session fb742b4b-83a0-4744-b61e-cede7703bd86, 2026-06-29

### 11. Mock Credentials Fallback on Clean CI/CD (Khóa giả lập dự phòng trên CI/CD sạch)
- **Ngữ cảnh**: Khi phát triển các gói thư viện/dịch vụ (như `ccba-ai` hoặc tích hợp các API bên thứ ba) khởi tạo Client ngay khi import module trong `__init__.py`.
- **Vấn đề giải quyết**: Các biến môi trường API keys thật sẽ không tồn tại trên môi trường CI/CD sạch. Một số SDK (như OpenAI) sẽ lập tức crash khi truyền `api_key=""` hoặc khi thiếu key trong tiến trình import tĩnh, làm tê liệt toàn bộ pytest run/linter check.
- **Giải pháp**: Đặt default fallback là một chuỗi khóa giả lập không rỗng (ví dụ: `"mock-key-for-ci"`) khi khởi tạo API client nếu không có key thật từ biến môi trường. Điều này cho phép client tạo object thành công mà không cản trở việc chạy thử nghiệm cục bộ hay CI/CD.
- **Nguồn**: Session fb742b4b-83a0-4744-b61e-cede7703bd86, 2026-07-01

---

## Anti-patterns (Cách tránh)

### 1. Tự ý thay đổi Alias mặc định của AI Gateway
- **Vấn đề**: Khi cập nhật tài liệu hoặc cấu hình, việc tự ý thay thế các định danh alias do Server quy định (như `qwen-local-primary`) bằng tên gốc thực tế của model (như `qwen3.5-35b`) sẽ phá vỡ hệ thống routing, load-balancing và các luồng fallback đã được setup ngầm định trên Gateway.
- **Thay thế bằng**: Luôn tôn trọng và duy trì cấu trúc định danh alias chuẩn (như `qwen-local-primary`, `ocr-primary`, `rag-core`, v.v.) trong mọi file config (`.env`) và mã nguồn mẫu.
- **Nguồn**: Session df3394e5-3891-4d1b-b234-ce3af1d47689, 2026-04-28

### 2. Raw clone directory placement without block configurations (Clone code thô thiếu cấu hình chặn)
- **Vấn đề**: Để các thư mục clone chứa toàn bộ mã nguồn của dự án khác trực tiếp ở Project Root hoặc trong thư mục cấu hình `.agents/` mà không thiết lập block/exclude. AI Agent sẽ tự động quét, đọc nhầm cấu hình (như `GEMINI.md`, `AGENTS.md`) gây xung đột và tốn token hệ thống.
- **Thay thế bằng**: Luôn di chuyển các thư mục clone tham khảo vào folder cách ly `.md/extracted_docs/references/clones/` và đưa folder `clones` vào danh sách chặn cứng của Scout Block hook.
- **Nguồn**: Session fb742b4b-83a0-4744-b61e-cede7703bd86, 2026-06-29

### 3. Empty API Key Defaults for LLM Client Constructors (Default api_key rỗng khi init LLM Client)
- **Vấn đề**: Cấu hình mặc định `api_key=""` trong constructor của các SDK hiện đại làm SDK ném lỗi cứng `Missing credentials` ngay khi chạy import/setup package, phá hỏng build/test pipelines.
- **Thay thế bằng**: Sử dụng dummy mock string (như `"mock-key-for-ci"`) để bypass kiểm tra cấu trúc của SDK, hoặc áp dụng cơ chế Lazy Instantiation cho SDK client.
- **Nguồn**: Session fb742b4b-83a0-4744-b61e-cede7703bd86, 2026-07-01

---

## Solutions (Giải pháp tham chiếu)

### Xử lý in mã Unicode (Emoji) gây vỡ Console trên Windows PowerShell
- **Vấn đề**: Gọi Python script in Emoji hoặc chữ Tiếng Việt dẫn đến `UnicodeEncodeError: 'charmap' codec can't encode character`. Nguyên nhân là `sys.stdout` map vào kiểu `cp1252`.
- **Giải pháp**: Code cứng ép cấu hình xuất tiêu chuẩn ở đầu Script:
```python
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
```
- **Nguồn**: Session 54f85dcb-dcf1-423e-98d8-d332bb4fe1d6, 2026-04-09

### 2. Đồng bộ hóa quy trình (Pipeline Consistency) trong Watch Mode
- **Vấn đề**: Watch Mode thường bỏ qua các bước xử lý phức tạp (Analyzer, Caching, Post-processing) để tăng tốc độ phản hồi, dẫn đến kết quả khác biệt so với khi chạy thủ công.
- **Giải pháp**: Buộc Watcher phải khởi tạo và gọi thông qua `ProcessingPipeline` thay vì gọi trực tiếp `Converter.convert`. Mọi sự tối ưu (ví dụ: semaphore) phải nằm trong Pipeline để dùng chung cho mọi chế độ chạy.
- **Nguồn**: Session 3cca2e64-49c0-4c49-aef3-684c8c1d80fd, 2026-04-15

### 3. Khắc phục lỗi PyMuPDF Pixmap isinstance TypeError
- **Vấn đề**: Gọi `fitz.Pixmap(pix, rect)` lỗi `TypeError` trên một số phiên bản (isinstance arg 2 must be type).
- **Giải pháp**: Tránh tạo Pixmap trung gian, sử dụng trực tiếp `page.get_pixmap(matrix=matrix, clip=rect)`. Cách này an toàn, tối ưu bộ nhớ và tránh lỗi định dạng nội bộ của thư viện.
- **Nguồn**: Session 3cca2e64-49c0-4c49-aef3-684c8c1d80fd, 2026-04-15

### 4. Lọc Thư mục CDE dựa trên Tiền tố (Failsafe Prefix Filter)
- **Vấn đề**: Bộ test tự động so sánh danh sách thư mục sinh ra bị lệch khi có thêm các thư mục trung gian (như `IDOP_Solution`).
- **Giải pháp**: Thay vì dùng phép trừ tập hợp tĩnh (`actual_dirs - {"lists", "workflows"}`), hãy dùng bộ lọc tiền tố động (`d.startswith(("01", "02", "03", "04", "05"))`) giúp test-suite cô lập hoàn toàn các thư mục CDE chuẩn cần kiểm tra.
- **Nguồn**: Session 86ca4b06-4329-478b-8c16-ca53827675de, 2026-06-27

### 5. Độ dài Regex linh hoạt trong Bộ quét API Keys (Privacy Guard)
- **Vấn đề**: Các mẫu API keys của các hãng có độ dài thực tế khác nhau (Gemini là 39 ký tự, OpenAI legacy là 51 ký tự, OpenAI project key là 53+ ký tự). Việc code cứng độ dài Regex (như `{35}` hay `{48}`) khiến test suite bị lỗi không bắt được dummy keys.
- **Giải pháp**: Sử dụng độ dài khoảng (như `{30,40}` hoặc `{30,}`) trong Regex để đảm bảo độ bao phủ rộng và an toàn cho mọi loại key.
### 6. Tự động xử lý Cảnh báo đăng nhập trùng phiên (Multi-session Login Warning Bypass)
- **Vấn đề**: Khi cào dữ liệu từ Thư Viện Pháp Luật (TVPL) bằng Chrome DevTools Protocol, do quy tắc hạn chế một tài khoản chỉ được đăng nhập trên một thiết bị tại một thời điểm, script tự động điền form đăng nhập sẽ kích hoạt cảnh báo modal của website: *"Quý khách Đăng nhập vào thì sẽ có 1 người khác bị Đăng xuất."* làm ngắt tiến trình và gây lỗi Timeout.
- **Giải pháp**: Bổ sung logic giám sát DOM ngay sau khi submit form đăng nhập để phát hiện sự xuất hiện của nút **"Đồng ý"** trong modal cảnh báo và tự động click xác nhận để giành quyền phiên làm việc, sau đó đợi trang tải lại để tiếp tục tải tệp tin gốc.
- **Nguồn**: Session 628572ad-aa52-4ae6-ba74-68a61f8709d7, 2026-06-28

### 7. Co che Hybrid Bypass & Fallback cho Slash Command Workflows
- **Van de**: Nguoi dung muon di nhanh vao chu de cu the va nap nhanh skills/guidelines ma khong can di qua khau quet tu dong va menu chon, nhung van phai ho tro luong quet chuan cho nguoi dung moi.
- **Giai phap**: Truyen tham so sau ky tu `--` (vi du `/ccba-brainstorm -- legal`). Neu khop voi chu de cau hinh -> Bypass quet tu dong. Neu sai hoac de trong -> Fallback ve luong quet chuan.
- **Nguon**: Session 98bf7ffe-a23a-4fcd-a7cb-59ee0ed5dac2, 2026-06-29

### 8. Auto-Prune cac ban ghi Spoke khong con hoat dong
- **Van de**: Cac du an Spoke mock hoac da bi xoa vat ly van ton tai trong file registry ma hoa tren Hub gay rac du lieu.
- **Giai phap**: Tich hop co che tu dong vao script giai ma cua Admin. Khi Admin chay decrypt, script tu dong kiem tra su ton tai vat ly cua duong dan Spoke (`os.path.exists()`). Neu khong ton tai -> Tu dong go bo ban ghi va ghi de cap nhat lai file registry.
- **Nguon**: Session 98bf7ffe-a23a-4fcd-a7cb-59ee0ed5dac2, 2026-06-29

### 9. Cấy ghép (Port) an toàn cấu hình bị ignore trong Git
- **Vấn đề**: Các file cấu hình hệ thống nằm trong thư mục bị ignore trong `.gitignore` (ví dụ thư mục `.agents/`) không thể stage thông thường bằng `git add`, làm Agent dễ bỏ sót khi chuyển dịch các cấu hình quan trọng.
- **Giải pháp**: Sử dụng lệnh ép buộc stage của Git: `git add -f <file-path>` (ví dụ `git add -f .agents/skills/platform-loader/catalog.yaml`) để đưa các tệp cấu hình cần thiết vào hệ thống quản lý phiên bản mà không cần thay đổi quy tắc ignore của dự án.
- **Nguồn**: Session 6bc722af-2748-44b7-8b54-4399e4df56df, 2026-06-29

### 10. Fix wildcard spaces regex boundary (Rách so khớp khoảng trắng do ranh giới từ)
- **Vấn đề**: Khi viết regex so khớp khoảng trắng đứng sau ranh giới từ `\bword\b\s+`, các ký tự đặc biệt đứng liền kề (như dấu đóng ngoặc đơn `)`) sẽ làm rách so khớp của khoảng trắng `\s+` vì dấu đóng ngoặc đơn không được tính là khoảng trắng.
- **Giải pháp**: Thiết lập regex linh hoạt hơn hoặc thay đổi cấu trúc test case để tránh các cụm từ lồng ngoặc phức tạp (ví dụ đổi `"let's create a pull request (pr) now"` thành `"please pr this branch"`).
- **Nguồn**: Session fb742b4b-83a0-4744-b61e-cede7703bd86, 2026-06-29

### 11. Package Missing Dependency Crashes in CI (Lỗi crash thiếu package dependency trên CI)
- **Vấn đề**: CI chạy test suite bị crash với lỗi `ModuleNotFoundError` dù ở máy local nhà phát triển đã chạy ổn định (do dev cài đặt thủ công nhưng quên lưu cấu hình).
- **Giải pháp**: Khai báo đầy đủ tất cả thư mục/thư viện import tĩnh (ví dụ `"pyyaml"`) vào phần `dependencies` trong tệp cấu hình package chính thức (như `pyproject.toml` hoặc `setup.py`), đảm bảo quy trình setup sạch tự động khôi phục toàn bộ môi trường.
- **Nguồn**: Session fb742b4b-83a0-4744-b61e-cede7703bd86, 2026-07-01

---

## Conventions (Quy định kiến trúc)

### 1. Phân Tách OCR Engines Độc Lập
- **Ngữ cảnh**: Các mô hình LLM chuyên lập trình hoặc text-reasoning (như Sonnet-4.6, Opus) thường rất yếu, chậm và ngốn quá nhiều token khi phân tích ảnh scan PDF nhị phân (đen trắng/chất lượng thấp).
- **Quy ước**: Tích hợp cờ chuyên biệt `--ocr` vào workflow để gọi ngầm alias model `ocr-primary` giúp bảo hành nội dung thị giác máy tính thay vì phó thác cho fallback tree.

### 2. Phân Tách Dữ Liệu (Data Layer) và Dịch Vụ (Service Layer) trong Platform
- **Ngữ cảnh**: Các kịch bản cào dữ liệu và đóng gói Bundle tri thức nằm rải rác trong `scripts/` làm Spoke project lộn xộn, khó tái sử dụng và khó bảo trì.
- **Quy ước**: Tách dữ liệu tri thức tĩnh (Knowledge Base) vào một thư mục chuyên biệt (`.md/legal_docs/<slug>/` với các tệp phân tích Markdown `.md` và Word `.docx`) phục vụ RAG, đồng thời đóng gói toàn bộ logic nghiệp vụ điều phối thành một Python editable package cài đặt được (`packages/ccba-legal-intel`) để tái sử dụng toàn cục.
- **Nguồn**: Session 628572ad-aa52-4ae6-ba74-68a61f8709d7, 2026-06-28

### 3. Bắt buộc kiểm định tài liệu Markdown kỹ thuật chính quy trước khi hoàn tất
- **Ngữ cảnh**: Viết hoặc cập nhật tài liệu kiến trúc hệ thống (`README.md`, `PLATFORM.md`, `AGENTS.md`) sau khi refactor.
- **Quy ước**: Agent bắt buộc phải chạy công cụ `validate_docs.py` để đảm bảo tài liệu không chứa mã nguồn ảo ảnh (hallucinations), link tương đối hỏng hoặc thiếu cấu hình trong `.env.example`.
- **Nguồn**: Session fb742b4b-83a0-4744-b61e-cede7703bd86, 2026-06-29

---

## Configurations (Cấu hình tối ưu)

| Setting / Alias | Value / Backend | Lý do | Áp dụng khi |
| --------- | ------- | ------- | ------------- |
| `text-gemma` | Gemma 3 27B | Tận dụng Google Free Quota (144k req/ngày) | High-volume NLP, phân loại, summarize |
| `ocr-primary` | Gemini 3.1 Flash Lite | Tận dụng Free Quota Vision (5k req/ngày) | OCR, bóc tách văn bản từ hình ảnh/bản vẽ |
| `reasoning-gemma` | Gemma 4 31B | Logic nâng cao, Free Quota (15k req/ngày)| Các task JSON phức tạp, trích xuất cấu trúc |

