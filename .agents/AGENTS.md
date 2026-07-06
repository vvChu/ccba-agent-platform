# CCBA Workspace Rules — Layer 1 Constitution

> [!IMPORTANT]
> **Đây là Hiến pháp Tối cao và là nguồn quy tắc duy nhất về hành vi của Agent.**
> Mọi quy định dưới đây phải được tuân thủ nghiêm ngặt trong tất cả các phiên làm việc và trên mọi dự án (Spokes) liên kết với Platform.
> Các tài liệu khác (như README.md hoặc SKILL.md) là Layer 2 hoặc Layer 3 và không được phép ghi đè hay thay đổi các quy tắc cốt lõi này.

---

## 1. CCBA Agent Services Platform (Hub) - Reuse-First Gate

Trước khi viết bất kỳ utility/script mới nào tại Spoke (extract, convert, parse...), Agent **PHẢI** thực hiện đánh giá tái sử dụng.
* **Rào cản bắt buộc:** Trong mọi tài liệu kế hoạch triển khai (`implementation_plan.md`) được tạo ra, Agent **bắt buộc phải điền** một mục riêng mang tên `## Đánh giá khả năng tái sử dụng (Reuse Assessment)`.
* **Nội dung bắt buộc trong kế hoạch:**
  * Trạng thái tra cứu Hub catalog (`platform-loader/catalog.yaml`): Chỉ rõ các tool/workflow trùng lặp hoặc liên quan đã tồn tại.
  * Đánh giá cost-benefit: Lý do chi tiết của việc đề xuất viết mới hoặc kế thừa (nêu rõ các yếu tố về dependencies, network, complexity).
* Nếu thiếu mục đánh giá này, kế hoạch triển khai sẽ bị coi là vi phạm nghiêm trọng quy chế làm việc và không được phép tiến hành thực thi.

---

## 2. CCBA Identity & Voice (Bản sắc & Phong cách giao tiếp)

* **Giọng điệu giao tiếp:** Trả lời bằng **tiếng Việt** (trừ khi người dùng dùng tiếng Anh). Giữ nguyên các thuật ngữ kỹ thuật tiếng Anh (function, class, endpoint, database...). Giao tiếp chuyên nghiệp, súc tích, khách quan.
* **Quy tắc Attribution:** Mọi output tài liệu chính thức đều bắt buộc kèm dòng attribution ở cuối:
  `*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*`
* **Disclaimer bắt buộc:** Khi output liên quan đến pháp luật hoặc văn bản pháp lý (VBPL), LUÔN kèm disclaimer ở cuối tài liệu:
  `*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*`

---

## 3. CCBA Quality Standards (Quy chuẩn chất lượng đầu ra)

* **Độ chính xác (Accuracy):** Trích dẫn VBPL phải chính xác số hiệu, điều/khoản, ngày hiệu lực. Không tự sáng tạo số hiệu VBPL không tồn tại hoặc đưa dự thảo (draft) làm căn cứ chính thức.
* **Tính đầy đủ (Completeness):** Các checklist nghiệm thu, hồ sơ hoàn thành phải đầy đủ theo Phụ lục VBPL hiện hành, không bỏ sót mục.
* **Tính truy vết (Traceability):** Mọi tuyên bố kỹ thuật hoặc pháp lý phải chỉ rõ nguồn (VBPL, TCVN, hoặc tài liệu tham chiếu cụ thể).
* **Kiểm định mã nguồn, cấu hình & tài liệu:** 
  - Mọi file YAML được Agent chỉnh sửa phải pass qua lệnh parse `yaml.safe_load()`.
  - Luôn sử dụng type hints trong Python (parameters + return types), viết docstring (Google style) cho tất cả public functions.
  - Hàm/phương thức không dài quá 50 dòng; ưu tiên composition over inheritance.
  - Mọi tài liệu Markdown kỹ thuật chính quy (như README.md, kiến trúc hệ thống) trước khi hoàn tất phải được kiểm định bằng công cụ `validate_docs.py` để đảm bảo không chứa code references ảo ảnh, link hỏng hoặc thiếu cấu hình trong `.env.example`.

---

## 4. CCBA Naming Conventions & Git Conventions

### Quy ước đặt tên file và thư mục
* **Tài liệu Seminar:** `CCBA_RD_SEMINAR_NNN_RevXX-DD.MM.YY-Title.{ext}`
  *(ví dụ: CCBA_RD_SEMINAR_004_Rev00-30.03.26-VBPL_Update.docx)*
* **Tài liệu VBPL (do CCBA tổng hợp):** `CCBA_RD_VBPL_NNN_RevXX-ShortName.{ext}`
  *(ví dụ: CCBA_RD_VBPL_003_Rev00-ND_06_2021.docx)*
* **Thư mục và file của AI Agent:** 
  - Skills: `lowercase_with_underscores` hoặc `kebab-case` (folders & file names).
  - Workflows: `kebab-case.md`.
  - YAML data: `lowercase_with_underscores.yaml`.
  - Templates: `lowercase_with_underscores.md`.
* **Quy tắc đăng ký Slash Command cho Kỹ năng (Skills):**
  Khi chuyển dịch (porting) hoặc tạo mới các kỹ năng có thuộc tính `user-invocable: true` từ thượng nguồn (hoặc khi nguồn dùng slash command để kích hoạt), Agent bắt buộc phải đăng ký thành Slash Command chính thức bằng cách tạo một file workflow mỏng tại thư mục `.agents/workflows/`.
  - Tên file workflow và Slash Command phải bắt đầu bằng tiền tố `ccba-` (ví dụ: `ccba-handoff.md` tạo lệnh `/ccba-handoff`).
  - Nội dung file workflow chỉ được chứa mô tả frontmatter tiếng Việt ngắn gọn và một dòng lệnh hướng dẫn Agent nạp trực tiếp file `SKILL.md` tương ứng để thực thi.

### Quy định quản lý và phân loại thư mục tri thức `.md/` (Project Root)
Để duy trì tính ngăn nắp của Knowledge Base dự án, Agent **bắt buộc** phải phân loại các tệp được tạo ra/sửa đổi vào đúng các thư mục con chức năng sau trong `.md/`:
* `.md/knowledge/`: Lưu trữ các tài liệu nghiên cứu, roadmap, spec kỹ thuật và tệp cấu hình tĩnh (ví dụ: `brand_rules.yaml`).
* `.md/seminars/`: Lưu trữ các tệp agenda, thông báo, tóm tắt seminar (các tệp bắt đầu bằng `CCBA_RD_SEMINAR_`).
* `.md/scratch/`: Lưu trữ các scripts test Python dùng một lần, file log tạm và SHA check.
* `.md/data/`: Lưu trữ dữ liệu động của các tools (ví dụ: `team_tasks.json`).
* `.md/extracted_docs/` và `.md/legal_docs/`: Lưu trữ văn bản pháp luật và văn bản trích xuất thô.
Tuyệt đối **không** tạo hoặc để các tệp tin này trực tiếp ở thư mục gốc `.md/` để tránh làm loãng thư mục tri thức chính.

### Quy ước Git (Git Conventions) & Quy trình phát hành (Release Gate)
* **Đặt tên Branch:** `type/short-description` *(ví dụ: feature/add-auth, fix/query-timeout)*.
* **Format Commit Message:** `type(scope): description` (bằng tiếng Anh).
  - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`.
  - Commit theo từng logical unit độc lập, không commit tất cả file cùng lúc.
* **Rào chắn đối soát PR (Release Gate Audit):**
  - Trước khi thực hiện merge bất kỳ Pull Request nào (trừ các PR nâng cấp thư viện tự động dependabot/chore đã pass CI và không có phản biện ngoài), Agent **bắt buộc** phải chạy lệnh `gh pr view <PR> --comments` (hoặc công cụ tương đương) để kiểm tra, đánh giá và giải trình tất cả các bình luận, cảnh báo từ Copilot hoặc các reviewers khác.
  - **Quy tắc dừng chờ Copilot**: Khi kiểm tra trạng thái PR qua `gh pr view <PR>`, nếu thấy người đánh giá `copilot-pull-request-reviewer` ở trạng thái `(Requested)` (chưa hoàn thành review), Agent **bắt buộc phải dừng lại và chờ** (sử dụng công cụ `schedule` để hẹn giờ kiểm tra lại sau mỗi 30s-60s). Thời gian chờ tối đa (timeout) là 3 phút; nếu quá thời gian này mà Copilot vẫn chưa chạy xong, Agent mới được báo cáo người dùng xin ý kiến bypass.
  - Phải tiến hành sửa lỗi hoặc giải trình lý do chính đáng và nhận được sự đồng thuận tường minh của người dùng trước khi merge.
  - Ghi nhận chi tiết kết quả xử lý bình luận của Copilot vào tài liệu bàn giao `walkthrough.md`.

---

## 5. CCBA Legal Compliance Rules (Quy tắc tuân thủ pháp lý)

* **Trạng thái hiệu lực văn bản:**
  - `draft` (Dự thảo): Được phép phân tích nhưng phải ghi rõ chữ "DỰ THẢO". Không dùng làm căn cứ chính thức.
  - `enacted` (Đã thông qua): Được phép phân tích, phải ghi rõ ngày hiệu lực.
  - `current` (Đang hiệu lực): Áp dụng bình thường.
  - `superseded` (Hết hiệu lực): Chỉ dùng tham chiếu lịch sử, phải ghi rõ "HẾT HIỆU LỰC".
* **Nguồn tin cậy:** Ưu tiên tra cứu theo thứ tự: (1) Cổng TTĐT Bộ Xây dựng (`moc.gov.vn`), (2) Cổng TTĐT Chính phủ (`vanban.chinhphu.vn`), (3) Cơ sở dữ liệu quốc gia về VBPL (`vbpl.vn`), (4) Registry cục bộ.
* **Giai đoạn chuyển tiếp (đến 01/07/2026):**
  > [!WARNING]
  > Trong giai đoạn chuyển đổi Luật Xây dựng 2014 → 2025 và Nghị định 06/2021 → Nghị định QLCL 2026, Agent **BẮT BUỘC** ghi rõ:
  > *"Áp dụng theo VBPL hiện hành đến 30/06/2026"* hoặc *"Theo dự thảo NĐ QLCL 2026 (chưa ban hành chính thức)"*.
