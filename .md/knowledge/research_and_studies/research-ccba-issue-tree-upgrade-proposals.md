# Báo Cáo Nghiên Cứu: Đánh Giá Đối Kháng & Đề Xuất Nâng Cấp Kỹ Năng `/ccba-issue-tree` (v1.2.0+)

**Phương pháp thực hiện:** Nghiên cứu phản biện đa tác nhân đối kháng kép (Dual-Agent Adversarial Research qua `/ccba-research`).  
**Tác nhân thực hiện:** Subagent A (`Solution Explorer`) đối soát song song với Subagent B (`Risk & Boundary Challenger`).  
**Thời điểm hoàn tất:** 2026-09-17T20:47:00+07:00  
**Tệp mục tiêu:** [`.agents/skills/ccba-issue-tree/SKILL.md`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-issue-tree/SKILL.md) (v1.1.0)

---

## 1. Tóm Tắt Thực Thi (Executive Summary)

Kỹ năng master [`/ccba-issue-tree`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-issue-tree/SKILL.md) hiện đóng vai trò là "bộ não điều phối phân rã bài toán" thuộc tầng Kernel (`bundle: _core`). Sau đợt nâng cấp v1.1.0 bổ sung cơ chế **Adaptive Fast-Tree** và **OS/Shell Awareness Guard**, câu hỏi đặt ra là: *Làm thế nào để nâng cấp kỹ năng này lên tầm cao mới mà không vi phạm nguyên tắc KISS và không phá vỡ trần ngân sách Token của hệ thống?*

Qua nghiên cứu đối kháng kép, chúng tôi xác định:
1. **Các ranh giới bất biến (Non-Negotiable Invariants):** Tuyệt đối duy trì `disable-model-invocation: true` (bảo toàn trần cứng 10 skills của `_core` theo ADR-0040), giữ nguyên tắc **Stateless thuần Markdown** (không sinh file `.yaml` rác), và bảo vệ cấu trúc phân tầng **Progressive Disclosure** (không nhồi nhét templates vào `SKILL.md`).
2. **Top 3 ý tưởng đột phá có giá trị thực tiễn cao nhất:**
   - **Cascading Branch Pruning & Discriminative Testing:** Cắt tỉa nhánh giả thuyết tự động khi nhánh cha bị bác bỏ (`FALSIFIED_BY_CASCADE`) và thiết kế bài kiểm tra nhị phân loại bỏ 50% không gian tìm kiếm.
   - **What-to-Checklist Pipeline (`/ccba-issue-tree` $\rightarrow$ `/ccba-completion-checklist`):** Tự động bóc tách các nút lá `[SYNTHESIS]` và `[COMMITMENT]` thành danh mục hồ sơ hoàn thành theo **Nghị định 207/2026/NĐ-CP** (văn bản hiện hành chính thức thay thế Nghị định 06/2021/NĐ-CP từ ngày 01/07/2026).
   - **Cryptographic SHA-256 Provenance Stamping (ADR-0059 Hardening):** Neo giữ mã băm mật mã cho các nút `VERIFIED_FACT` để đảm bảo tính toàn vẹn pháp lý trong giám định sự cố và tranh chấp.

---

## 2. Kết Quả Nghiên Cứu Chi Tiết (Key Findings)

### 2.1. Tổng Quan & Xu Hướng Phát Triển (Trends & Architecture)
* **Phương pháp luận Cây Vấn Đề McKinsey kết hợp Vòng đời Động (Governed Lifecycle):** Xu hướng giải quyết vấn đề bằng AI hiện đại không dừng lại ở việc vẽ sơ đồ tĩnh (Mindmap/Mermaid) mà đòi hỏi chuyển dịch trạng thái có trách nhiệm gắn với các vai trò phê duyệt (12 Ghế CCBA Charter).
* **Kiến trúc Progressive Disclosure 3 Tầng:**
  - *Tầng 1 (Frontmatter & Invariants):* Cực kỳ tinh gọn, quản trị metadata và cờ `disable-model-invocation: true`.
  - *Tầng 2 (Workflow 4 Pha & Fast-Tree):* Hướng dẫn vận hành cô đọng trong `SKILL.md`.
  - *Tầng 3 (References Index):* Chứa toàn bộ kho mẫu biểu chuyên ngành và cẩm nang vận hành chi tiết trong thư mục `references/`.

### 2.2. Quy Chuẩn Kỹ Thuật Tốt Nhất (Best Practices)
* **Khai thác Năng Lực Sẵn Có Của Monorepo (Reuse-First Gate):** Thay vì viết thêm module mới, việc liên kết luồng công việc giữa `/ccba-issue-tree` (bóc tách việc) với các công cụ downstream như `/ccba-completion-checklist` (nghiệm thu hồ sơ), `ccba-legal-advisor` (thẩm định pháp lý), và `bigbim-risk` (xung đột BIM) tạo ra giá trị gia tăng gấp nhiều lần.
* **Suy Luận Nhị Phân Phân Định (Discriminative Binary RCA):** Trong chẩn đoán nguyên nhân sự cố (*Diagnostic Why-Tree*), việc thiết kế các câu hỏi hoặc bài đo đạc nhị phân ($0$ hoặc $1$) có khả năng loại trừ một nửa số nhánh (Binary Search on Problem Space) giúp giảm thời gian khoanh vùng sự cố từ hàng giờ xuống vài phút.

### 2.3. Bẫy Thường Gặp & Rủi Ro Đối Kháng (Adversarial Risks & Pitfalls)
Qua phân biện đối kháng từ Subagent Challenger, **5 cạm bẫy thiết kế nghiêm trọng** đã được nhận diện và lập rào chắn:

| Đề Xuất Tiềm Năng | Rủi Ro Đối Kháng (Challenger Findings) | Kết Luận Phản Biện |
| :--- | :--- | :---: |
| **Bật `disable-model-invocation: false`** để AI tự gọi cây | Gây vỡ trần `MAX_MODEL_INVOKED_PER_BUNDLE = 10` của `_core` (ADR-0040), làm nổ CI validator và gây lãng phí hàng ngàn token nền cho các câu hỏi đơn giản. | **BÁC BỎ 100%** |
| **Lưu trạng thái bằng file `.yaml` / `.json`** | Gây bẩn Git working tree, xung đột merge conflict khi làm việc nhóm trên Spoke, vi phạm nguyên tắc KISS. | **BÁC BỎ 100%** |
| **Cho AI tự động chạy script ở nút lá** | Vi phạm ranh giới an toàn của các Ghế RACI (`CHU_TRI_BO_MON`, `GIAM_DOC`), nguy cơ phá hoại mã nguồn ngoài kiểm soát. | **BÁC BỎ 100%** |
| **Nhồi nhét template PCCC/MEP vào `SKILL.md`** | Làm phình to file từ 150 dòng lên hàng ngàn dòng, gây loãng prompt và giảm khả năng bám sát logic MECE. | **ĐIỀU HƯỚNG SANG LEVEL 3** |
| **Thêm quá nhiều cờ tham số (`--why-only`, `--strict`...)** | Gây quá tải nhận thức, phức tạp hóa giao diện dòng lệnh, vi phạm triết lý tối giản của hệ thống. | **BÁC BỎ (GIỮ FAST/FULL)** |

### 2.4. Bảo Mật & Hiệu Năng (Security & Seam Boundaries)
* **Bảo vệ Deep Seams (ADR-0035):** Việc kết nối giữa các kỹ năng không được import chéo mã nguồn trực tiếp mà phải thông qua CLI Contracts và tài liệu Level 3.
* **Nguyên tắc Verbatim Grounding (ADR-0059):** Mọi bằng chứng pháp lý chuyển sang `VERIFIED_FACT` phải có liên kết tới tài liệu gốc nội bộ trong `.md/extracted_docs/` và mã băm SHA-256, cấm tuyệt đối sinh dữ liệu giả định (mock statutes).

---

## 3. Khuyến Nghị Triển Khai (Implementation Recommendations)

### Giai đoạn 1 (v1.2.0 - Ưu tiên cao, Không sửa đổi mã nguồn harness)
1. **Nâng cấp Cẩm nang Vận hành Level 3 ([`references/governed_lifecycle_guide.md`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-issue-tree/references/governed_lifecycle_guide.md)):**
   - Bổ sung quy tắc **Cascading Falsification**: Khi một nút cha bị `FALSIFIED`, tự động gán nhãn `FALSIFIED_BY_CASCADE` cho toàn bộ nhánh con phụ thuộc.
   - Bổ sung quy tắc **Discriminative Test Matrix**: Hướng dẫn kỹ sư thiết kế 1 bài kiểm tra nhị phân để loại trừ 50% số nhánh giả thuyết cùng lúc.
   - Thể chế hóa định dạng **Cryptographic Evidence Stamping** với mã băm SHA-256 cho nút `VERIFIED_FACT`.
2. **Bổ sung Mẫu Cây Phân Định Vào Level 3 ([`references/tree_templates.md`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-issue-tree/references/tree_templates.md)):**
   - Đưa vào mẫu biểu Mermaid biểu diễn nhánh bị cắt tỉa (`classDef pruned fill:#f9f9f9,stroke:#ccc,stroke-dasharray: 5 5`).

### Giai đoạn 2 (v1.3.0 - Tích hợp Hệ sinh thái)
1. **Cầu nối What-Tree $\rightarrow$ Checklist Hoàn Thành:**
   - Xây dựng quy tắc ánh xạ tự động từ các gói việc `[SYNTHESIS]` sang các danh mục hồ sơ nghiệm thu trong `ccba-completion-checklist/resources/checklist_master.yaml`.
2. **Interactive HTML Artifact Viewer (Tùy chọn hiển thị đối ngoại):**
   - Cung cấp script mẫu tạo file Artifact HTML tự lập (`.md/issue_tree_viewer.html`) có tính năng collapse/expand và filter màu theo trạng thái phục vụ trình chiếu cho Ban Quản lý dự án.

---

## 4. Ma Trận Đánh Giá Giải Pháp (Giá Trị × Độ Phức Tạp × Rủi Ro × KISS)

| Ý Tưởng Nâng Cấp | Giá Trị Thực Tiễn | Độ Phức Tạp | Rủi Ro | Tuân Thủ KISS | Quyết Định / Trạng Thái |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Cascading Branch Pruning** | 9.0 / 10 | Rất thấp | Cực thấp | 10 / 10 | **CHẤP THUẬN (Triển khai vào Level 3)** |
| **2. Cryptographic SHA-256 Grounding** | 9.0 / 10 | Rất thấp | Cực thấp | 10 / 10 | **CHẤP THUẬN (Triển khai vào Level 3)** |
| **3. What-to-Checklist Pipeline** | 9.5 / 10 | Thấp | Cực thấp | 9.5 / 10 | **CHẤP THUẬN (Lộ trình v1.3.0)** |
| **4. Interactive HTML Viewer** | 8.0 / 10 | Trung bình | Thấp | 8.0 / 10 | **CÂN NHẮC (Chỉ làm Artifact tùy chọn)** |
| **5. Stateful File Persistence (`.yaml`)** | 4.0 / 10 | Cao | Cao | 2.0 / 10 | **BÁC BỎ (Vi phạm KISS & Clean Tree)** |
| **6. Auto-execute Scripts tại Nút Lá** | 3.0 / 10 | Rất cao | Nghiêm trọng | 3.0 / 10 | **BÁC BỎ (Nguy cơ phá hoại dữ liệu)** |
| **7. Bật `model-invocation: true`** | 2.0 / 10 | Thấp | Nghiêm trọng | 1.0 / 10 | **BÁC BỎ (Vỡ Context Budget Ceiling)** |

---

## 5. Tài Liệu Tham Chiếu & Citations

1. [`.agents/skills/ccba-issue-tree/SKILL.md`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-issue-tree/SKILL.md) — Đặc tả kỹ năng v1.1.0.
2. [`references/governed_lifecycle_guide.md`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-issue-tree/references/governed_lifecycle_guide.md) — Hướng dẫn tầng vận hành 6 trạng thái và ma trận RACI.
3. [`references/tree_templates.md`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-issue-tree/references/tree_templates.md) — Mẫu biểu Mermaid và Text Tree chuẩn hóa.
4. [`AGENTS.md`](file:///d:/GitHubProjects/ccba-agent-platform/AGENTS.md) — Hiến chương nền tảng CCBA Layer 1.
5. [`packages/ccba-harness/src/ccba_harness/skill_validator.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/skill_validator.py) — Ngưỡng kiểm soát `MAX_MODEL_INVOKED_PER_BUNDLE = 10` (ADR-0040).
6. [`docs/adr/0059-legal-verbatim-grounding-and-mandatory-acquisition-invariant.md`](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0059-legal-verbatim-grounding-and-mandatory-acquisition-invariant.md) — Quy chuẩn mã băm chứng cứ SHA-256.
7. [`.agents/skills/ccba-completion-checklist/resources/checklist_master.yaml`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/ccba-completion-checklist/resources/checklist_master.yaml) — Khung danh mục hồ sơ hoàn thành (đang quy chiếu NĐ 06/2021 chuyển tiếp; đang được chuẩn bị nâng cấp lên Nghị định 207/2026/NĐ-CP hiện hành).

---

## 6. Câu Hỏi Chưa Làm Rõ (Unresolved Questions)

1. **Hiệu năng hiển thị khi cây vượt quá 30 nút lá:** Cần kiểm chứng thực nghiệm xem cú pháp Mermaid trong các trình duyệt hiện tại có bị giảm tốc độ render khi kích thước cây mở rộng quá lớn hay không; nếu có thì khi nào là ngưỡng tối ưu để kích hoạt Interactive HTML Viewer.
2. **Mức độ sẵn sàng của Spoke khi tích hợp Checklist:** Cần khảo sát xem các dự án Spoke chuyên ngành (như BIM hoặc Pháp lý) đã cài đặt đầy đủ gói `python-docx` để xuất biên bản Word khi kích hoạt pipeline What-to-Checklist hay chưa.
