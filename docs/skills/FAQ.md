# CCBA Agent Platform — Hỏi Đáp Thường Gặp (FAQ)

Tài liệu này tập hợp các câu hỏi và giải đáp cốt lõi về kiến trúc, cách vận hành kỹ năng (skills), cơ chế đồng bộ Hub-Spoke và kỷ luật kỹ thuật trên **CCBA Agent Services Platform**.

---

## 1. Kiến trúc Nền tảng & Ranh giới Hub vs Spoke

### Q1: Hub và Spoke khác nhau như thế nào?
- **Hub (`ccba-agent-platform`)**: Là kho lưu trữ trung tâm (Upstream SSOT), nơi phát triển, thẩm tra chất lượng, đóng gói và quản trị toàn bộ các kỹ năng, quy trình (workflows), gói thư viện chia sẻ và các bản ghi quyết định kiến trúc (ADR).
- **Spoke**: Là các dự án thực tế độc lập (dự án tư vấn thiết kế, thẩm tra công trình, phần mềm vệ tinh). Spoke nhận kỹ năng và quy chuẩn từ Hub thông qua cơ chế đồng bộ một chiều (`sync_spoke.py`) và đóng góp ngược lại Hub thông qua Upstream Contribution Loop (`ccba-contribute-to-hub`).

### Q2: Làm sao để Agent biết mình đang đứng ở Hub hay Spoke?
Theo **Layer 1 Constitution**, môi trường được nhận diện tự động qua lệnh:
```bash
git remote get-url origin
```
Nếu URL chứa chuỗi `ccba-agent-platform`, Agent đang ở **Hub**. Ngược lại, Agent đang ở **Spoke**.

### Q3: Cơ chế "Virtual Hub Fallback" là gì?
Tại Spoke, nếu một kỹ năng được người dùng hoặc workflow tham chiếu nhưng chưa được cài đặt vật lý vào thư mục cục bộ `.\.agents\skills\`, Agent **bắt buộc** phải đọc trực tiếp định nghĩa kỹ năng từ Hub:
```text
[hub_path]/.agents/skills/<skill_name>/SKILL.md
```
Điều này cho phép Spoke luôn tiếp cận được năng lực mới nhất từ Hub mà không cần phải sao chép toàn bộ 68 kỹ năng về máy cục bộ.

---

## 2. Triệu Hồi & Vận Hành Kỹ Năng

### Q4: Có mấy cách để kích hoạt một kỹ năng?
Hệ thống hỗ trợ 3 phương thức kích hoạt:
1. **Slash Command trong IDE Chat (`/ccba-...` hoặc `/bigbim-...`)**: Dành cho kỹ sư con người gõ trực tiếp trong Cursor, Claude Code, Windsurf hoặc Copilot.
2. **Model-Invoked qua Triggers / Keywords**: Agent tự động nhận diện từ khóa trong prompt của người dùng để triệu hồi kỹ năng tương ứng (được khai báo trong trường `triggers` của `SKILL.md` và `catalog.yaml`).
3. **CLI Terminal Command**: Các lệnh công cụ hoặc kiểm thử tự động, ví dụ:
   ```bash
   python -m ccba_harness verify-patch --preset skill
   python scripts/validate_skills.py --file .agents/skills/ccba-implement/SKILL.md
   ```

### Q5: Tại sao một số kỹ năng có cờ `disable-model-invocation: true`?
Các kỹ năng mang tính điều phối chiến lược (như `ccba-ask`, `ccba-grilling`, `ccba-handoff`) hoặc có tác động lớn đến kiến trúc được gắn cờ `disable-model-invocation: true` để **chỉ cho phép kỹ sư con người chủ động triệu hồi** qua Slash Command, tránh việc AI Agent tự ý kích hoạt ngầm khi chưa có chỉ định rõ ràng.

### Q6: Kỹ năng Kernel (Tier 2B) và Composite Orchestrator (Tier 3) khác nhau ra sao?
- **Tier 2B — Standalone Kernel Skill**: Kỹ năng chuyên biệt giải quyết một bài toán kỹ thuật độc lập (ví dụ: `ccba-tdd`, `bigbim-classification`, `ccba-maskara`). Phải đạt điểm GPI $\ge 12.0$ theo ADR-0057.
- **Tier 3 — Composite Orchestrator**: Kỹ năng cấp cao điều phối chuỗi nhiều Kernel Skills tuần tự qua cơ chế Deep Seam (ví dụ: `ccba-ai-qc`, `ccba-markdown-document-processing`).

---

## 3. Đồng Bộ & Cập Nhật Kỹ Năng (Hub $\rightarrow$ Spoke)

### Q7: Làm thế nào để cài đặt hoặc cập nhật một kỹ năng mới vào Spoke?
Từ thư mục gốc của Spoke, chạy lệnh:
```bash
python [hub_path]/scripts/spoke/sync_spoke.py --skills <tên_kỹ_năng>
```
Hoặc triệu hồi Slash Command `/ccba-update-spoke` trong IDE Chat.

### Q8: Khi đồng bộ sang Spoke, tệp `AGENTS.md` có bị ghi đè mất các cấu hình riêng không?
**Tuyệt đối không**. Động cơ đồng bộ áp dụng nguyên tắc **Non-Destructive Section Merge (Bảo tồn Hiến pháp Spoke)**. Nó chỉ cập nhật phần Hiến pháp Nền tảng (Platform Constitution), bảo toàn nguyên vẹn 100% các phần tùy biến cục bộ của Spoke như Issue Tracker, Domain Docs, và Local Rules.

---

## 4. Quản Trị Chất Lượng & Rào Chắn Kỷ Luật

### Q9: ADR-0058 "Deterministic Hard Completion Lock" là gì?
Đây là rào chắn bất biến: **Agent tuyệt đối không được tuyên bố hoàn thành nhiệm vụ hoặc yêu cầu người dùng nghiệm thu nếu bất kỳ lệnh kiểm thử tự động nào thoát với mã khác 0 (`exit code != 0`)**. Mọi thay đổi mã nguồn, kỹ năng và tài liệu bắt buộc phải vượt qua:
```bash
python -m ccba_harness verify-patch --preset skill
```

### Q10: ADR-0030 "Cognitive Prompt Budget" bảo vệ điều gì?
Tệp `SKILL.md` của mỗi kỹ năng được nạp trực tiếp vào Context Window của AI Agent ở Runtime. Do đó:
- `SKILL.md` phải súc tích, chỉ chứa hướng dẫn tác nghiệp và rào chắn thực thi cốt lõi.
- Tuyệt đối không chèn văn xuôi tiếp thị, câu hỏi FAQ rác hay mã HTML dài dòng vào `SKILL.md`.
- Toàn bộ tài liệu cho con người, trang web tra cứu và các endpoint máy đọc được quản lý tách rời tại thư mục `docs/`.

### Q11: Gặp lỗi metadata drift hoặc `catalog.yaml is OUT OF SYNC` thì xử lý thế nào?
Chỉ cần chạy lệnh tái biên dịch tất định:
```bash
python scripts/governance/compile_catalog.py --write
python scripts/governance/compile_skills_docs.py --write
```
Sau đó chạy lại `python scripts/validate_skills.py` để xác nhận hệ thống đã đồng bộ 100%.

---

## 5. Bàn Giao Phiên Làm Việc (Session Handoff & Learnings)

### Q12: Tại sao phải sử dụng `/ccba-handoff` khi kết thúc phiên?
Trong môi trường phát triển đa tác nhân hoặc phiên làm việc kéo dài, Context Window sẽ bị bão hòa. Kỹ năng `/ccba-handoff` giúp:
1. Tóm tắt súc tích tiến độ thực tế, những gì đã làm và những gì còn dang dở.
2. Cập nhật các bài học kinh nghiệm mới vào `.md/knowledge/session_learnings.md`.
3. Đảm bảo phiên làm việc tiếp theo của Agent có thể khởi động ngay lập tức với context sạch mà không bị mất mát thông tin.
