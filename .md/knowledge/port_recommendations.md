<!-- AUTO-GENERATED-START -->
# 📋 Upstream Porting Recommendations

Báo cáo tự động đánh giá các tính năng mới từ thượng nguồn. Cập nhật ngày: 2026-07-09 04:49:02

---

### 🟡 [UPGRADE/INTEGRATE] Skill: `batch-grill-me` (Score: 30/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: Kỹ năng 'batch-grill-me' có sự trùng lặp chức năng cốt lõi với kỹ năng 'grilling' và workflow 'ccba-grill-with-docs' hiện có trong hệ thống. Mặc dù cơ chế 'design tree' và 'batching' của nó rất mạnh mẽ, việc port thêm một kỹ năng phỏng vấn/xác định yêu cầu mới sẽ gây phân mảnh quy trình làm việc (workflow fragmentation). Thay vào đó, kiến trúc nên ưu tiên nâng cấp kỹ năng 'grilling' hiện tại để hỗ trợ tư duy theo 'frontier' và 'design tree' thay vì tạo thêm một thực thể mới.
*   **Các bước triển khai**:
    *   Đánh giá lại kỹ năng 'grilling' hiện tại và xác định các thiếu hụt về khả năng quản lý trạng thái theo 'design tree'.
    *   Tích hợp tư duy 'frontier' (phân loại câu hỏi dựa trên dependencies) vào prompt template của 'grilling' thay vì port 'batch-grill-me'.
    *   Nếu cần thiết, cập nhật 'ccba-grill-with-docs' để hỗ trợ việc dispatch sub-agent tìm kiếm thông tin môi trường thay vì hỏi người dùng.
    *   Bỏ qua (IGNORE) việc port 'batch-grill-me' để giữ cho danh mục kỹ năng hiện tại tinh gọn.

---

### 🟢 [RECOMMEND PORT] Skill: `to-questionnaire` (Score: 85/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: Kỹ năng 'to-questionnaire' cung cấp một phương pháp luận chuyên biệt về thu thập tri thức (knowledge extraction) mà hệ thống hiện tại chưa có. Mặc dù chúng ta có 'grilling', 'ask', và 'triage', nhưng các kỹ năng đó tập trung vào việc truy vấn trực tiếp hoặc phân loại, trong khi 'to-questionnaire' tập trung vào việc tạo ra một 'artifact' (tài liệu bảng hỏi) có cấu trúc để làm việc bất đồng bộ (async). Nó bổ trợ hoàn hảo cho các workflow hiện có như 'ccba-research' và 'handoff'.
*   **Các bước triển khai**:
    *   Tạo thư mục mới cho kỹ năng trong cấu trúc quản lý kỹ năng của ccba-agent-platform.
    *   Sao chép nội dung SKILL.md và cấu hình metadata tương ứng vào thư mục mới.
    *   Tích hợp với hệ thống 'platform-loader' để đảm bảo kỹ năng được nhận diện trong môi trường runtime.
    *   Kiểm tra tính tương thích với 'markdown-document-processing' để đảm bảo việc tạo tệp .md đầu ra tuân thủ tiêu chuẩn tài liệu của nền tảng.
    *   Thực hiện thử nghiệm (dry-run) bằng cách kết hợp với workflow 'ccba-research' để kiểm chứng khả năng trích xuất thông tin.

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