<!-- AUTO-GENERATED-START -->
# 📋 Upstream Porting Recommendations

Báo cáo tự động đánh giá các tính năng mới từ thượng nguồn. Cập nhật ngày: 2026-07-09 04:49:02

---

### 🟠 [COMPARE ONLY — LICENSE RESTRICTED] Skill: `ab-test-setup` (Score: 80/100) — Tier 3: Composite Orchestrator
*   **Kho chứa nguồn**: `marketing` (https://github.com/claudekit/claudekit-marketing)
*   **Bản quyền**: `Bản quyền đóng (Không được sao chép)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 3: Composite Orchestrator` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cần địa hóa sang môi trường Python / Ruff / PyTest.
*   **Lý do**: Kỹ năng mới chưa có trên catalog (PROPRIETARY). Định tuyến: Cổng 1 (Orchestration Gate): Tác vụ có điều phối nhiều tác tử song song, chuyển trạng thái StateGraph checkpoints hoặc cần con người phê duyệt (HITL). Bắt buộc triển khai tại Tầng 3 (Composite Orchestrator).
*   **Các bước triển khai**:
    *   Chạy lệnh `/ccba-xia .md/scratch/repos/claudekit-marketing ab-test-setup --compare` để trinh sát
    *   Định tuyến tới Tầng 3: Composite Orchestrator (.agents/workflows/) theo ADR-0057
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/claudekit-marketing ab-test-setup --compare`

---

### 🟠 [COMPARE ONLY — LICENSE RESTRICTED] Skill: `ai-artist` (Score: 80/100) — Tier 2A: Progressive Reference (GPI: 5.00)
*   **Kho chứa nguồn**: `marketing` (https://github.com/claudekit/claudekit-marketing)
*   **Bản quyền**: `Bản quyền đóng (Không được sao chép)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 2A: Progressive Reference` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cần địa hóa sang môi trường Python / Ruff / PyTest.
*   **Lý do**: Kỹ năng mới chưa có trên catalog (PROPRIETARY). Định tuyến: Chỉ số GPI (5.00) < 12.0. Phân loại: Tier 2A (Progressive Reference). Cần lưu trữ dưới dạng tài liệu tham chiếu trong references/*.md của Master Skill 'codebase-design'; cảnh báo/từ chối tạo thư mục Skill độc lập.
*   **Các bước triển khai**:
    *   Chạy lệnh `/ccba-xia .md/scratch/repos/claudekit-marketing ai-artist --compare` để trinh sát
    *   Định tuyến tới references/ai-artist.md (của Master Skill 'codebase-design') theo ADR-0057
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/claudekit-marketing ai-artist --compare`

---

### 🟠 [COMPARE ONLY — LICENSE RESTRICTED] Skill: `competitor-alternatives` (Score: 80/100) — Tier 2A: Progressive Reference (GPI: 5.00)
*   **Kho chứa nguồn**: `marketing` (https://github.com/claudekit/claudekit-marketing)
*   **Bản quyền**: `Bản quyền đóng (Không được sao chép)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 2A: Progressive Reference` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cần địa hóa sang môi trường Python / Ruff / PyTest.
*   **Lý do**: Kỹ năng mới chưa có trên catalog (PROPRIETARY). Định tuyến: Chỉ số GPI (5.00) < 12.0. Phân loại: Tier 2A (Progressive Reference). Cần lưu trữ dưới dạng tài liệu tham chiếu trong references/*.md của Master Skill 'codebase-design'; cảnh báo/từ chối tạo thư mục Skill độc lập.
*   **Các bước triển khai**:
    *   Chạy lệnh `/ccba-xia .md/scratch/repos/claudekit-marketing competitor-alternatives --compare` để trinh sát
    *   Định tuyến tới references/competitor-alternatives.md (của Master Skill 'codebase-design') theo ADR-0057
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/claudekit-marketing competitor-alternatives --compare`

---

### 🔴 [IGNORE] Skill: `ask-matt` (Score: 25/100) — Tier 2A: Progressive Reference (GPI: 3.25)
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills) — 🟢 FRESH (last commit: 2026-10-31, 10d ago, 553 commits)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 2A: Progressive Reference` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Là meta-prompt/hướng dẫn tra cứu quy trình dưới dạng Markdown thuần. Về mặt kỹ thuật hoàn toàn tương thích, nhưng nội dung gắn chặt với taxonomy riêng biệt của upstream repository thay vì Python Monorepo của CCBA.
*   **Lý do**: Kỹ năng này hoạt động như một router tĩnh dành riêng cho danh mục skills của tác giả Matt Pocock (grill-with-docs, handoff, to-spec...). Hệ sinh thái CCBA Agent Platform hiện đã có 'ccba-ask' đóng vai trò định tuyến toàn diện cho hơn 76 skills hiện hữu (BIM, AI-QC, PCCC, ADR,...). Việc tích hợp 'ask-matt' sẽ gây trùng lặp tính năng và sai lệch ngữ cảnh điều phối tác tử.
*   **Các bước triển khai**:
    *   Từ chối tích hợp 'ask-matt' vào ccba-agent-platform theo ADR-0057.
    *   Tham chiếu sơ đồ workflow (idea → spec/prototype → tickets → implement → retro) từ nội dung của kỹ năng để đối chiếu, cải tiến luồng điều hướng trong 'ccba-ask' nếu cần.
    *   Tiếp tục bảo trì và sử dụng 'ccba-ask' làm router trung tâm cho toàn bộ nền tảng.
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/mattpocock-skills ask-matt --compare`

---

### 🟢 [RECOMMEND PORT] Skill: `chief-of-staff` (Score: 80/100) — Tier 2A: Progressive Reference (GPI: 5.00)
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills) — 🟢 FRESH (last commit: 2026-10-31, 10d ago, 553 commits)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 2A: Progressive Reference` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cần địa hóa sang môi trường Python / Ruff / PyTest.
*   **Lý do**: Kỹ năng mới chưa có trên catalog (PERMISSIVE). Định tuyến: Chỉ số GPI (5.00) < 12.0. Phân loại: Tier 2A (Progressive Reference). Cần lưu trữ dưới dạng tài liệu tham chiếu trong references/*.md của Master Skill 'codebase-design'; cảnh báo/từ chối tạo thư mục Skill độc lập.
*   **Các bước triển khai**:
    *   Chạy lệnh `/ccba-xia .md/scratch/repos/mattpocock-skills chief-of-staff --compare` để trinh sát
    *   Định tuyến tới references/chief-of-staff.md (của Master Skill 'codebase-design') theo ADR-0057
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/mattpocock-skills chief-of-staff --port`

---

### 🔵 [UPSTREAM DELTA] Skill: `claude-handoff` (Score: 85/100) — Delta -> ccba-handoff
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills) — 🟢 FRESH (last commit: 2026-10-31, 10d ago, 553 commits)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0057)**: `Delta -> ccba-handoff` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cập nhật gia tăng cho `ccba-handoff` (skills/in-progress/claude-handoff/SKILL.md).
*   **Lý do**: UPSTREAM DELTA (mattpocock-skills): `claude-handoff` có thay đổi mới sau `24fe0ef7` khớp với `ccba-handoff`.
*   **Các bước triển khai**:
    *   Chạy `/ccba-xia .md/scratch/repos/mattpocock-skills claude-handoff --improve --since 24fe0ef7 --target ccba-handoff` để thẩm định diff từ `24fe0ef7` vào `ccba-handoff`
    *   Cập nhật reviewed_sha trong triage_ledger sau khi hoàn tất
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/mattpocock-skills claude-handoff --improve --since 24fe0ef7 --target ccba-handoff`

---

### 🟢 [RECOMMEND PORT] Skill: `software-factory` (Score: 85/100) — Tier 2A: Progressive Reference (GPI: 11.25)
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills) — 🟢 FRESH (last commit: 2026-10-31, 10d ago, 553 commits)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 2A: Progressive Reference` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Hoàn toàn tương thích. Kỹ năng là một Domain Ontology / Prompt Blueprint định nghĩa bộ thuật ngữ nhất quán (Ubiquitous Language) và cấu trúc kiến trúc cho Software Factory. Khi chuyển sang Python Monorepo, có thể ánh xạ trực tiếp các khái niệm (Orchestrator -> LangGraph/Temporal, Runner -> Disposable Container/Docker, Tasks/Runs -> StateGraph Workflows).
*   **Lý do**: Kỹ năng cung cấp ngôn ngữ chuẩn hóa và nguyên lý thiết kế tối quan trọng cho hệ sinh thái multi-agent (Task, Run, Runner, Ticket tracker, Brakes). Việc chuẩn hóa thuật ngữ giúp ngăn ngừa hiện tượng hallucination về khái niệm kiến trúc khi xây dựng và vận hành các luồng tự động hóa code trong monorepo.
*   **Các bước triển khai**:
    *   Khởi tạo thư mục kỹ năng tại bundles/_software/skills/ccba-software-factory.
    *   Bảo lưu cờ disable-model-invocation: true để tránh LLM tự động nạp tràn ngữ cảnh khi không thiết kế kiến trúc.
    *   Bổ sung phần ánh xạ thực tế (Architecture Mapping) tương thích với hạ tầng Python Monorepo: LangGraph làm Orchestrator, GitHub API SDK làm Git Host/Ticket Tracker, và Runner chạy trong sandbox.
    *   Đăng ký kỹ năng vào Registry manifest của platform-loader trong bundle _software.
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/mattpocock-skills software-factory --port`

---

### 🟢 [RECOMMEND PORT] Skill: `teach` (Score: 80/100) — Tier 2A: Progressive Reference (GPI: 5.00)
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills) — 🟢 FRESH (last commit: 2026-10-31, 10d ago, 553 commits)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 2A: Progressive Reference` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cần địa hóa sang môi trường Python / Ruff / PyTest.
*   **Lý do**: Kỹ năng mới chưa có trên catalog (PERMISSIVE). Định tuyến: Chỉ số GPI (5.00) < 12.0. Phân loại: Tier 2A (Progressive Reference). Cần lưu trữ dưới dạng tài liệu tham chiếu trong references/*.md của Master Skill 'codebase-design'; cảnh báo/từ chối tạo thư mục Skill độc lập.
*   **Các bước triển khai**:
    *   Chạy lệnh `/ccba-xia .md/scratch/repos/mattpocock-skills teach --compare` để trinh sát
    *   Định tuyến tới references/teach.md (của Master Skill 'codebase-design') theo ADR-0057
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/mattpocock-skills teach --port`

---

### 🟢 [RECOMMEND PORT] Skill: `impeccable` (Score: 88/100) — Tier 2B: Standalone Kernel Skill (GPI: 23.25)
*   **Kho chứa nguồn**: `impeccable` (https://github.com/pbakaus/impeccable) — 🟢 FRESH (last commit: 2026-11-11, 0d ago, 2825 commits)
*   **Bản quyền**: `Apache 2.0 License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 2B: Standalone Kernel Skill` (Bundle: `_software`, `disable-model-invocation: false`)
*   **Đánh giá tương thích Python**: Phù hợp tốt. Phần cốt lõi của skill là hệ thống playbook, quy tắc thẩm mỹ, craft-floor và quy trình UX design director bằng markdown. Cơ chế launcher binary/npx có thể được thay thế hoặc hỗ trợ bằng Python helper script để đọc context trực tiếp (PRODUCT.md, DESIGN.md), hoàn toàn tương thích với cơ chế fallback sẵn có của skill.
*   **Lý do**: Kỹ năng cung cấp bộ hướng dẫn UI/UX design, visual craft, typography và component review ở cấp độ chuyên gia cao cấp, giải quyết bài toán hoàn thiện frontend sản phẩm mà platform đang thiếu (kỹ năng `ccba-design` hiện tại chỉ tập trung vào kiến trúc hệ thống tổng quát). Skill có cơ chế tự vận hành độc lập, tuân thủ giấy phép Apache 2.0.
*   **Các bước triển khai**:
    *   Bước 1: Port skill vào thư mục bundles/_software/ccba-frontend-craft (hoặc giữ tên ccba-impeccable-design) kèm các tài liệu playbook trong thư mục reference/.
    *   Bước 2: Viết script Python (scripts/context_loader.py) để thay thế launcher nhị phân npx/bash, đọc tự động PRODUCT.md, DESIGN.md và các token thiết kế trong project người dùng.
    *   Bước 3: Cập nhật SKILL.md khai báo allowed-tools và đường dẫn Python script tương thích với Python Monorepo runtime.
    *   Bước 4: Đăng ký skill vào registry của bundle _software và bổ sung test case e2e cho workflow thiết kế UI.
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/impeccable impeccable --port`

---

### 🟢 [RECOMMEND PORT] Skill: `seo` (Score: 80/100) — Tier 2A: Progressive Reference (GPI: 5.00)
*   **Kho chứa nguồn**: `web-quality-skills` (https://github.com/addyosmani/web-quality-skills) — 🟢 FRESH (last commit: 2026-08-24, 78d ago, 34 commits)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 2A: Progressive Reference` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cần địa hóa sang môi trường Python / Ruff / PyTest.
*   **Lý do**: Kỹ năng mới chưa có trên catalog (PERMISSIVE). Định tuyến: Chỉ số GPI (5.00) < 12.0. Phân loại: Tier 2A (Progressive Reference). Cần lưu trữ dưới dạng tài liệu tham chiếu trong references/*.md của Master Skill 'codebase-design'; cảnh báo/từ chối tạo thư mục Skill độc lập.
*   **Các bước triển khai**:
    *   Chạy lệnh `/ccba-xia .md/scratch/repos/web-quality-skills seo --compare` để trinh sát
    *   Định tuyến tới references/seo.md (của Master Skill 'codebase-design') theo ADR-0057
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/web-quality-skills seo --port`

---

### 🟢 [RECOMMEND PORT] Skill: `web-quality-audit` (Score: 80/100) — Tier 2A: Progressive Reference (GPI: 5.00)
*   **Kho chứa nguồn**: `web-quality-skills` (https://github.com/addyosmani/web-quality-skills) — 🟢 FRESH (last commit: 2026-08-24, 78d ago, 34 commits)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 2A: Progressive Reference` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cần địa hóa sang môi trường Python / Ruff / PyTest.
*   **Lý do**: Kỹ năng mới chưa có trên catalog (PERMISSIVE). Định tuyến: Chỉ số GPI (5.00) < 12.0. Phân loại: Tier 2A (Progressive Reference). Cần lưu trữ dưới dạng tài liệu tham chiếu trong references/*.md của Master Skill 'codebase-design'; cảnh báo/từ chối tạo thư mục Skill độc lập.
*   **Các bước triển khai**:
    *   Chạy lệnh `/ccba-xia .md/scratch/repos/web-quality-skills web-quality-audit --compare` để trinh sát
    *   Định tuyến tới references/web-quality-audit.md (của Master Skill 'codebase-design') theo ADR-0057
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/web-quality-skills web-quality-audit --port`

---

### 🟢 [RECOMMEND PORT] Skill: `power-platform-skills (corpus)` (Score: 80/100) — Corpus Digest -> ccba-sharepoint-iac (GPI: 5.00)
*   **Kho chứa nguồn**: `power-platform-skills` (https://github.com/microsoft/power-platform-skills) — 🟢 FRESH (last commit: 2026-11-11, 0d ago, 372 commits)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0057)**: `Corpus Digest -> ccba-sharepoint-iac` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cần địa hóa sang môi trường Python / Ruff / PyTest.
*   **Lý do**: Kỹ năng mới chưa có trên catalog (PERMISSIVE). Định tuyến: Chỉ số GPI (5.00) < 12.0. Phân loại: Tier 2A (Progressive Reference). Cần lưu trữ dưới dạng tài liệu tham chiếu trong references/*.md của Master Skill 'codebase-design'; cảnh báo/từ chối tạo thư mục Skill độc lập.
*   **Các bước triển khai**:
    *   Chạy lệnh `/ccba-xia .md/scratch/repos/power-platform-skills power-platform-skills-corpus --compare` để trinh sát
    *   Định tuyến tới references/power-platform-skills-corpus.md (của Master Skill 'codebase-design') theo ADR-0057
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/power-platform-skills . --improve --target ccba-sharepoint-iac`

---

### 🟢 [RECOMMEND PORT] Skill: `pnp-list-formatting (corpus)` (Score: 80/100) — Corpus Digest -> ccba-sharepoint-iac
*   **Kho chứa nguồn**: `pnp-list-formatting` (https://github.com/pnp/List-Formatting) — 🟢 FRESH (last commit: 2026-11-03, 7d ago, 1944 commits)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0057)**: `Corpus Digest -> ccba-sharepoint-iac` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cần địa hóa sang môi trường Python / Ruff / PyTest.
*   **Lý do**: Kỹ năng mới chưa có trên catalog (PERMISSIVE). Định tuyến: Cổng 0 (Determinism Gate): Tác vụ có thể giải quyết 100% bằng giải thuật xác định (regex, AST parse, math, file I/O). Bắt buộc triển khai tại Tầng 1 (Package Function / Deep Seam trong packages/*). Cấm tạo Skill độc lập.
*   **Các bước triển khai**:
    *   Chạy lệnh `/ccba-xia .md/scratch/repos/pnp-list-formatting pnp-list-formatting-corpus --compare` để trinh sát
    *   Định tuyến tới packages/*/src theo ADR-0057
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/pnp-list-formatting . --improve --target ccba-sharepoint-iac`
<!-- AUTO-GENERATED-END -->

<!-- DEVELOPER-NOTES-START -->
## 📝 Ghi chú của Kỹ sư (Developer Notes)
*Kỹ sư có thể tự do ghi chép các phân tích, đánh giá thủ công tại đây. Phần này sẽ được tự động bảo toàn khi đồng bộ thượng nguồn.*

- **[2026-11-01 — `/ccba-xia` Upstream Adaptation `mattpocock/skills@4ae2317` (`v1.3.2` — ADOPTED)]:**
  - Đã hoàn tất chuyển dịch theo **Phương án A (Hybrid Adopt + Tier 2A Progressive Reference — Zero Skill Bloat)**, bảo toàn trần 76 Hub Skills:
    - **Tier 2A Progressive References mới (`[NEW]`):** `ccba-implement/references/implement-spec.md` (`COND-01` First-Unit Canary & Orchestrator Single-Writer), `ccba-knowledge-loop/references/llm-wiki.md` (`COND-02` `.md/knowledge/wiki/index.md` Dated & Commit-Pinned Historical Wiki), `ccba-grilling/references/to-questionnaire.md` (*Grill the send, not the subject*).
    - **Nâng cấp tại chỗ (`[MODIFY]`):** `ccba-build-skill/references/skill_authoring_guide.md` (`writing-for-agents` + `SKILL-MECHANICS.md` v1.3.2), `ccba-implement/references/prototype_logic.md` & `prototyping_patterns.md` (`Shareable HTML` + `Guided Walkthroughs`), `ccba-diagnosing-bugs/SKILL.md` (`v1.1.0` `<REDACTED>` & Phase 5 `git diff` Forced Mutation Gate), `ccba-tdd/SKILL.md` (`v1.3.0` Seam catches/misses), `ccba-code-review/SKILL.md` (`v1.7.0` `fresh context window` & explicit standards handoff), `ccba-create-pr/SKILL.md` (`v1.3.0` Show-Me Visual Summary + Evidence + Merge Danger), `ccba-implement/SKILL.md` (`v1.1.0`), `ccba-grilling/SKILL.md` (`v1.2.0`), `ccba-knowledge-loop/SKILL.md` (`v1.1.0`).
- **[2026-11-03 — Triage Closure `retro` & `writing-beats` (`COND-05` — DECLINED / SUPERSEDED)]:**
  - **`retro` (`mattpocock/skills`) — `[DECLINED / SUPERSEDED]`**: Chức năng phân tích nhật ký phiên và cải tiến quy trình đã được bao phủ toàn diện bởi kỹ năng nội bộ `/ccba-session-retrospective` kết hợp bộ nén bộ nhớ phân tầng `scripts/governance/compact_session_learnings.py` và Historical LLM Wiki (`.md/knowledge/wiki/`). Từ chối port riêng để bảo toàn trần 76 Hub Skills (`ADR-0057`).
  - **`writing-beats` (`mattpocock/skills`) — `[DECLINED / OUT-OF-SCOPE]`**: Quy trình viết lách tương tác dạng *choose-your-own-adventure* nằm ngoài phạm vi cốt lõi của nền tảng tư vấn xây dựng và kỹ thuật phần mềm CCBA; các nhu cầu biên soạn tài liệu kỹ thuật/pháp lý đã được đáp ứng bởi `/ccba-copywriting`, `/ccba-seminar-builder`, và `/ccba-xu-ly-van-phong`.
<!-- DEVELOPER-NOTES-END -->