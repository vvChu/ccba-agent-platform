# Cẩm nang Chưng cất Phiên làm việc thành Kỹ năng (`--from-workflow`)

> Nguồn gốc: Thích ứng từ `workflow-skill-creator` của Google LLC (Apache-2.0 License). Tài liệu tham chiếu tăng tiến (Tier 2A) cho kỹ năng gốc [ccba-build-skill](../SKILL.md).

> **Lưu ý:** Tài liệu này là cẩm nang tham chiếu tăng tiến thuần túy (all-reference), dùng cho **Chế độ C (`--from-workflow`)** của `/ccba-build-skill`.

---

## 1. Ngữ cảnh Kích hoạt & Phạm vi (Bottom-Up Session Distillation)

Khác với Chế độ A/B (tác tạo kỹ năng theo hướng Top-Down từ kho tài liệu nguồn), **Chế độ C (`--from-workflow`)** phục vụ chưng cất **Bottom-Up** một chuỗi thao tác thực tế đã hoàn thành thành công ngay trong phiên làm việc hiện tại:

- **Khi kích hoạt:** Người dùng truyền cờ `--from-workflow` (ví dụ: `/ccba-build-skill --from-workflow [--name <tên-skill>]`) hoặc yêu cầu đóng gói quy trình vừa chạy trong hội thoại thành kỹ năng tái sử dụng.
- **Không áp dụng khi:** Người dùng cần tạo kỹ năng mới từ đầu khi chưa có quy trình thực chiến đã chạy (dùng Chế độ A/B của `/ccba-build-skill`) hoặc chỉ muốn tiến hóa một `SKILL.md` đã tồn tại cuối phiên (dùng `/ccba-session-retrospective`).
- **Tái sử dụng trước tiên (`ADR-0061`):** Kiểm tra `catalog.yaml` và chạy `ccba-platform find-seam --in <types> --out <types> --json`. Nếu một bước trong phiên đã được bao phủ bởi kỹ năng hoặc Deep Seam sẵn có của Platform, kỹ năng mới bắt buộc dẫn chiếu lại thay vì sao chép hoặc tự triển khai lại.

---

## 2. Quét Bảo mật Lịch sử Phiên & Khử Trạng thái Máy trạm (Privacy & Machine-State Guard)

Lịch sử hội thoại và nhật ký terminal thường chứa khóa API, header xác thực hoặc đường dẫn máy cá nhân. Trước khi chưng cất tri thức ở Bước 2 của [ccba-build-skill](../SKILL.md), Agent thực hiện trình tự bảo vệ dữ liệu sau:

- **Trích xuất vào vùng đệm tạm:** Rút gọn chuỗi bước thực tế, lệnh đã chạy, tham số I/O và kết quả kiểm chứng từ ngữ cảnh phiên vào tệp nháp tạm trong `.md/scratch/build-skill/<tên-skill>/`.
- **Quét bí mật qua `scripts/maskara.py`:** Chạy `python scripts/maskara.py` (Seam `maskara_scanner.v1`) trực tiếp lên tệp nháp trích xuất. Nếu phát hiện rò rỉ thông tin nhạy cảm (`findings` khác rỗng) $\rightarrow$ **DỪNG NGAY**, loại bỏ hoặc ẩn token nhạy cảm và cảnh báo người dùng trước khi tiếp tục.
- **Khử trạng thái máy trạm (`Machine-State Decoupling`):** Thay thế mọi đường dẫn ổ đĩa tuyệt đối cá nhân hoặc định danh phiên tạm thời bằng tham số cấu hình hoặc biến môi trường chuẩn (`CCBA_HUB_PATH`, tham số CLI) trước khi kết xuất sang `.md/scratch/build-skill/<tên-skill>/summary.md`.

---

## 3. Bảng Đối soát Chưng cất Tự điền & Phỏng vấn Hội tụ 1–2 Lượt (`Workflow Distillation Matrix`)

Áp dụng nguyên tắc *tự tra cứu facts từ ngữ cảnh phiên, chỉ hỏi người dùng các decisions* (từ `/ccba-grilling`):

- **Tự điền bảng nháp trước khi hỏi:** Agent tự trích xuất thông tin thực tế đã quan sát trong phiên để điền sẵn **Bảng Đối soát Chưng cất (`Workflow Distillation Matrix`)** theo khung dưới đây:

| Bước | Thao tác thực tế trong phiên | Độ cứng (`Strict` / `Flexible`) | Chính sách lỗi (`ask` / `fallback` / `fail-loud`) | Phân tầng đích (`Tier 1 Seam` / `Tier 2 Step`) | Kỹ năng / Seam tái sử dụng |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `<Lệnh hoặc bước Agent đã chạy>` | `Strict` hoặc `Flexible` | `ask` / `fallback` / `fail-loud` | `Tier 1 Seam` hoặc `Tier 2 Step` | `<tên skill hoặc seam_id>` |

- **Phỏng vấn hội tụ tối đa 1–2 lượt (2–3 câu/lượt, kèm phương án đề xuất trước):** Trình bày bảng nháp để người dùng hiệu chỉnh và khóa đủ **8 tiêu chí hội tụ** trước khi chuyển sang Bước 2 (Chưng cất vào scratch) và Bước 3 (`evaluate-gpi --json`):
  1. **Mục tiêu & Phạm vi bước:** Xác nhận bước nào giữ lại, bước nào là thao tác sửa lỗi nhất thời cần loại bỏ, tần suất tái sử dụng (định kỳ hay theo sự kiện).
  2. **Đầu vào & Đầu ra kỳ vọng (I/O Contract):** Định dạng dữ liệu đầu vào và sản phẩm đầu ra cuối cùng.
  3. **Độ cứng từng bước (`Strict` vs `Flexible`):** Phân định bước nào bắt buộc dùng đúng công cụ/nguồn dữ liệu/thứ tự cố định (`Strict`), bước nào Agent được phép linh hoạt chọn phương án hợp lý (`Flexible`).
  4. **Chính sách xử lý lỗi từng bước:** Khi bước chính thất bại (API sập, rỗng kết quả, sai định dạng), Agent cần: (a) hỏi người dùng (`ask`), (b) tự động thử nhánh thay thế (`fallback`), hay (c) dừng ngay kèm thông báo lỗi rõ ràng (`fail-loud`), và có phơi bày edge cases cho người dùng hay không.
  5. **Kỹ năng & Deep Seams tái sử dụng:** Chốt danh sách kỹ năng/Seam hiện hữu trong `catalog.yaml` cần khai báo phụ thuộc thay vì viết lại.
  6. **Phân tách Cổng 0 (Code vs. Instruction-Only):** Xác nhận mọi bước có gọi API, xử lý dữ liệu, I/O tệp hoặc tính toán tất định đều được đưa xuống Tầng 1 theo Mục 4 bên dưới.
  7. **Ca kiểm thử mẫu từ phiên thực chiến (`eval_<stem>.json`):** Chốt 1 cặp truy vấn đầu vào + kết quả kỳ vọng thực tế vừa quan sát trong phiên để làm giàu ca Happy-Path (và bổ sung ca Red-Team tương ứng) tại `.agents/skills/ccba-eval-gate/test_cases/eval_<stem>.json`.
  8. **Định danh & Tầng lưu trữ dự kiến:** Chốt tên gợi ý `ccba-<tên-skill>` (hoặc `<parent-skill>` nếu điểm GPI rơi vào Tier 2A) và xác nhận vị trí đích trên Hub (kể cả khi đang khởi phát từ Spoke).

---

## 4. Cổng 0, File-First Output & Hợp đồng Tham số Tường minh (`ADR-0057`, `ADR-0061`)

Không đóng gói script xử lý dữ liệu dài hoặc client API cồng kềnh vào thư mục kỹ năng. Mọi bước mang tính lập trình phát hiện trong phiên phải tuân thủ 4 chuẩn kỹ thuật sau:

- **Định tuyến Tầng 1 (`Tier 1: Package Function / Deep Seam`) & Chống Script Bloat:**
  - Toàn bộ logic gọi API, parse dữ liệu, tính toán hoặc xử lý tệp tất định phải triển khai trong `packages/*/src/` và bảo vệ bằng unit test; tuyệt đối không giữ script vượt quá `100 LOC` trong `.agents/skills/<tên-skill>/scripts/`.
  - Nếu cần điểm vào CLI nội bộ trong kỹ năng, chỉ tạo Thin Adapter ($\le 30$ LOC) gọi vào Deep Seam.
  - Với API ngoài chưa có Seam, tái sử dụng mẫu rate limiting đa tiến trình chuẩn của Platform tại [ccba-api-circuit-breaker](../../ccba-api-circuit-breaker/SKILL.md); không sử dụng biến đếm trạng thái trong bộ nhớ như `last_request_time = 0.0` (vốn bị reset ở mỗi lần gọi subprocess CLI mới).
- **File-First Output (`--output`):**
  - Mọi lệnh con (subcommand) hoặc Thin Adapter xuất dữ liệu cấu trúc phải nhận tham số `--output` để ghi JSON (`indent=2`) ra tệp và chỉ in thông báo trạng thái ngắn ra `stdout`, bảo vệ cửa sổ ngữ cảnh khỏi bị tràn bởi payload lớn.
- **Chống cắt ngầm kết quả (`--limit` bắt buộc):**
  - Các lệnh tìm kiếm hoặc liệt kê danh sách phải khai báo tham số `--limit` với `required=True` (không gán giá trị mặc định ngầm), buộc Agent chỉ định rõ ngưỡng lấy dữ liệu thay vì lầm tưởng đã lấy đủ toàn bộ bản ghi.
- **Diagnostic thân lỗi HTTP `4xx`:**
  - Khi gặp lỗi HTTP không thể retry (`400`, `403`, `404`), đọc và đính kèm tối đa `1000` ký tự đầu của response body vào thông báo lỗi thay vì chỉ in mã trạng thái, giúp Agent tự hiệu chỉnh tham số gọi lại chính xác.
