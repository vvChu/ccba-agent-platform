# 📈 CCBA Token Economy & Prompt Density Audit Report

## 1. Executive Summary

- **Total Skills Audited:** 67
- **Average Prompt Density Index (PDI):** 73.3 / 100.0
- **Total Estimated Prompt Tokens:** 148,839
- **Overhead / Bloated Skills Count:** 4
- **Potential Token Savings Per Swarm Run:** ~12,134 tokens

## 3. Top Skills Requiring Prompt Pruning / Optimization

| Skill Name | Tokens | Directives | PDI Score | Status | Recommendations |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `ccba-pptx` | 6,968 | 77 | 61.3 | Bloated / High Overhead | Prompt is 6,968 tokens. Consider splitting into progressive reference files. |
| `ccba-ai-gateway-sdk` | 5,331 | 73 | 88.2 | Bloated / High Overhead | Prompt is 5,331 tokens. Consider splitting into progressive reference files. |
| `ccba-xia` | 4,943 | 16 | 35.9 | Bloated / High Overhead | Prompt is 4,943 tokens. Consider splitting into progressive reference files. |
| `ccba-excalidraw-diagram` | 4,892 | 94 | 99.0 | Bloated / High Overhead | Prompt is 4,892 tokens. Consider splitting into progressive reference files. |
| `ccba-setup-skills` | 3,483 | 15 | 49.5 | Moderate Overhead | Low directive density. Trim narrative explanations into bullet lists.; Contains 4 duplicated sentences found in other skills. |
| `ccba-design` | 3,467 | 66 | 99.0 | Moderate Overhead | Well structured |
| `ccba-teamwork` | 3,310 | 30 | 70.6 | Moderate Overhead | Well structured |
| `ccba-llm-pipeline-patterns` | 3,145 | 63 | 99.0 | Moderate Overhead | Well structured |
| `ccba-legal-ingest` | 3,128 | 24 | 64.3 | Moderate Overhead | Well structured |
| `bigbim-classification` | 3,075 | 14 | 49.9 | Moderate Overhead | Low directive density. Trim narrative explanations into bullet lists.; Contains 4 duplicated sentences found in other skills. |
| `ccba-contribute-to-hub` | 2,953 | 26 | 69.9 | Moderate Overhead | Contains 4 duplicated sentences found in other skills. |
| `ccba-hybrid-rag-search` | 2,902 | 38 | 99.0 | Moderate Overhead | Excessive embedded code. Move large code examples to scripts/ or references/. |
| `ccba-wayfinder` | 2,857 | 9 | 42.6 | Moderate Overhead | Low directive density. Trim narrative explanations into bullet lists. |
| `ccba-legal-intel` | 2,832 | 35 | 86.3 | Moderate Overhead | Well structured |
| `bigbim-governance` | 2,788 | 12 | 47.2 | Moderate Overhead | Low directive density. Trim narrative explanations into bullet lists.; Contains 4 duplicated sentences found in other skills. |


## 4. Actionable HITL Prompt Pruning Recommendations

> [!TIP]
> Áp dụng nguyên tắc **Progressive Disclosure** (ADR-0030, ADR-0057): Kỹ năng `SKILL.md` chỉ giữ các chỉ dẫn điều phối cốt lõi. Các ví dụ chi tiết, template dài, hoặc cẩm nang hướng dẫn nên chuyển vào thư mục `references/*.md`.

### 🔍 Skill `bigbim-classification` (3,075 tokens | PDI: 49.9)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/bigbim-classification/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Low directive density. Trim narrative explanations into bullet lists.
  - ⚠️ Contains 4 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk]: '📚 bigbim method kb — tài liệu tham chiếu'
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk]: '> trước khi thực thi, agent phải đọc các articles sau trong bigbim method kb:'
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk, ccba-academic-writing]: '⚙️ quy trình thực thi của ai agent (execution logic)'

### 🔍 Skill `bigbim-governance` (2,788 tokens | PDI: 47.2)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/bigbim-governance/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Low directive density. Trim narrative explanations into bullet lists.
  - ⚠️ Contains 4 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk]: '📚 bigbim method kb — tài liệu tham chiếu'
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk]: '> trước khi thực thi, agent phải đọc các articles sau trong bigbim method kb:'
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk, ccba-academic-writing]: '⚙️ quy trình thực thi của ai agent (execution logic)'

### 🔍 Skill `bigbim-rase` (2,437 tokens | PDI: 60.5)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/bigbim-rase/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 5 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk]: '📚 bigbim method kb — tài liệu tham chiếu'
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk]: '> trước khi thực thi, agent phải đọc các articles sau trong bigbim method kb:'
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk, ccba-academic-writing]: '⚙️ quy trình thực thi của ai agent (execution logic)'

### 🔍 Skill `bigbim-risk` (2,552 tokens | PDI: 58.8)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/bigbim-risk/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 5 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk]: '📚 bigbim method kb — tài liệu tham chiếu'
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk]: '> trước khi thực thi, agent phải đọc các articles sau trong bigbim method kb:'
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk, ccba-academic-writing]: '⚙️ quy trình thực thi của ai agent (execution logic)'

### 🔍 Skill `ccba-academic-writing` (2,257 tokens | PDI: 53.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-academic-writing/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 5 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [bigbim-classification, bigbim-governance, bigbim-rase, bigbim-risk, ccba-academic-writing]: '⚙️ quy trình thực thi của ai agent (execution logic)'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'

### 🔍 Skill `ccba-adr-lifecycle` (1,696 tokens | PDI: 99.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-adr-lifecycle/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-ai-gateway-sdk` (5,331 tokens | PDI: 88.2)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-ai-gateway-sdk/SKILL.md`
- **Trạng thái:** `Bloated / High Overhead`
  - ⚠️ Prompt is 5,331 tokens. Consider splitting into progressive reference files.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-ai-gateway-sdk, ccba-xia]: '| :--- | :--- | :--- | :--- |'

### 🔍 Skill `ccba-ai-qc` (1,744 tokens | PDI: 70.4)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-ai-qc/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'

### 🔍 Skill `ccba-ai-qc-pccc-audit` (1,273 tokens | PDI: 67.3)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-ai-qc-pccc-audit/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-api-circuit-breaker` (1,351 tokens | PDI: 99.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-api-circuit-breaker/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-api-circuit-breaker, ccba-append-only-logger]: 'kỹ sư hoặc agent tại dự án spoke có thể dễ dàng import và sử dụng trực tiếp:'
    * Duplicated across [ccba-api-circuit-breaker, ccba-append-only-logger]: 'tự động kiểm soát và sửa lỗi (self-healing)'

### 🔍 Skill `ccba-append-only-logger` (1,361 tokens | PDI: 98.4)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-append-only-logger/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-api-circuit-breaker, ccba-append-only-logger]: 'kỹ sư hoặc agent tại dự án spoke có thể dễ dàng import và sử dụng trực tiếp:'
    * Duplicated across [ccba-api-circuit-breaker, ccba-append-only-logger]: 'tự động kiểm soát và sửa lỗi (self-healing)'

### 🔍 Skill `ccba-ask` (1,583 tokens | PDI: 40.1)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-ask/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 4 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'

### 🔍 Skill `ccba-autoresearch` (807 tokens | PDI: 75.6)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-autoresearch/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'

### 🔍 Skill `ccba-build-skill` (2,377 tokens | PDI: 71.1)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-build-skill/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 3 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-code-review` (1,910 tokens | PDI: 53.5)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-code-review/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'

### 🔍 Skill `ccba-codebase-design` (1,796 tokens | PDI: 78.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-codebase-design/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-contribute-to-hub` (2,953 tokens | PDI: 69.9)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-contribute-to-hub/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 4 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-copywriting` (2,051 tokens | PDI: 39.8)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-copywriting/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 4 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'

### 🔍 Skill `ccba-design` (3,467 tokens | PDI: 99.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-design/SKILL.md`
- **Trạng thái:** `Moderate Overhead`

### 🔍 Skill `ccba-diagnosing-bugs` (2,444 tokens | PDI: 72.6)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-diagnosing-bugs/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-docs-manager` (1,834 tokens | PDI: 66.4)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-docs-manager/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 4 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'

### 🔍 Skill `ccba-eval-gate` (1,363 tokens | PDI: 58.8)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-eval-gate/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 3 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-excalidraw-diagram` (4,892 tokens | PDI: 99.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-excalidraw-diagram/SKILL.md`
- **Trạng thái:** `Bloated / High Overhead`
  - ⚠️ Prompt is 4,892 tokens. Consider splitting into progressive reference files.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-git-guardrails` (1,285 tokens | PDI: 82.9)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-git-guardrails/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-graduate-rd` (1,995 tokens | PDI: 83.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-graduate-rd/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-contribute-to-hub, ccba-graduate-rd]: 'git checkout main && git pull origin main && git checkout -b "$branchname"'

### 🔍 Skill `ccba-grilling` (2,559 tokens | PDI: 40.9)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-grilling/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Low directive density. Trim narrative explanations into bullet lists.
  - ⚠️ Contains 4 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'

### 🔍 Skill `ccba-implement` (1,654 tokens | PDI: 69.3)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-implement/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 3 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'
    * Duplicated across [ccba-implement, ccba-tdd]: 'python -m ccbaharness verify-patch --preset code --target <packageordir>'

### 🔍 Skill `ccba-init-spoke` (2,670 tokens | PDI: 79.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-init-spoke/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 3 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-issue-to-hub` (1,800 tokens | PDI: 86.1)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-issue-to-hub/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 3 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-knowledge-loop` (2,527 tokens | PDI: 41.1)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-knowledge-loop/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Low directive density. Trim narrative explanations into bullet lists.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'

### 🔍 Skill `ccba-legal-document-tracker` (1,606 tokens | PDI: 72.5)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-legal-document-tracker/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-legal-ingest` (3,128 tokens | PDI: 64.3)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-legal-ingest/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-legal-ingest, ccba-legal-intel]: 'python -m ccbalegal ingest "<tvplurl>" --category <01vbpl|02qcvn|03tcvn> --uploa...'
    * Duplicated across [ccba-legal-ingest, ccba-markdown-document-processing]: '| tiêu chí | trạng thái | yêu cầu kiểm tra |'

### 🔍 Skill `ccba-legal-intel` (2,832 tokens | PDI: 86.3)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-legal-intel/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-legal-ingest, ccba-legal-intel]: 'python -m ccbalegal ingest "<tvplurl>" --category <01vbpl|02qcvn|03tcvn> --uploa...'

### 🔍 Skill `ccba-llm-pipeline-patterns` (3,145 tokens | PDI: 99.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-llm-pipeline-patterns/SKILL.md`
- **Trạng thái:** `Moderate Overhead`

### 🔍 Skill `ccba-markdown-document-processing` (2,081 tokens | PDI: 71.7)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-markdown-document-processing/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-legal-ingest, ccba-markdown-document-processing]: '| tiêu chí | trạng thái | yêu cầu kiểm tra |'

### 🔍 Skill `ccba-maskara` (1,149 tokens | PDI: 99.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-maskara/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'

### 🔍 Skill `ccba-new-feature` (2,356 tokens | PDI: 88.2)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-new-feature/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-new-feature, ccba-release-feature]: 'git checkout main && git pull origin main'

### 🔍 Skill `ccba-notebooklm-connector` (2,319 tokens | PDI: 84.5)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-notebooklm-connector/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'

### 🔍 Skill `ccba-pptx` (6,968 tokens | PDI: 61.3)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-pptx/SKILL.md`
- **Trạng thái:** `Bloated / High Overhead`
  - ⚠️ Prompt is 6,968 tokens. Consider splitting into progressive reference files.

### 🔍 Skill `ccba-release-feature` (2,273 tokens | PDI: 99.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-release-feature/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-new-feature, ccba-release-feature]: 'git checkout main && git pull origin main'

### 🔍 Skill `ccba-research` (2,067 tokens | PDI: 66.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-research/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 4 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'

### 🔍 Skill `ccba-seminar-builder` (2,073 tokens | PDI: 68.7)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-seminar-builder/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-session-retrospective` (2,420 tokens | PDI: 64.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-session-retrospective/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'

### 🔍 Skill `ccba-setup-skills` (3,483 tokens | PDI: 49.5)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-setup-skills/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Low directive density. Trim narrative explanations into bullet lists.
  - ⚠️ Contains 4 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'

### 🔍 Skill `ccba-skill-repair` (2,240 tokens | PDI: 72.9)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-skill-repair/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'

### 🔍 Skill `ccba-spoke-adopter` (1,352 tokens | PDI: 94.7)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-spoke-adopter/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'

### 🔍 Skill `ccba-tdd` (1,910 tokens | PDI: 57.7)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-tdd/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Contains 3 duplicated sentences found in other skills.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'
    * Duplicated across [ccba-implement, ccba-tdd]: 'python -m ccbaharness verify-patch --preset code --target <packageordir>'

### 🔍 Skill `ccba-teamwork` (3,310 tokens | PDI: 70.6)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-teamwork/SKILL.md`
- **Trạng thái:** `Moderate Overhead`

### 🔍 Skill `ccba-to-spec` (1,006 tokens | PDI: 65.8)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-to-spec/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-update-spoke` (2,083 tokens | PDI: 99.0)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-update-spoke/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-wayfinder` (2,857 tokens | PDI: 42.6)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-wayfinder/SKILL.md`
- **Trạng thái:** `Moderate Overhead`
  - ⚠️ Low directive density. Trim narrative explanations into bullet lists.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'

### 🔍 Skill `ccba-xia` (4,943 tokens | PDI: 35.9)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-xia/SKILL.md`
- **Trạng thái:** `Bloated / High Overhead`
  - ⚠️ Prompt is 4,943 tokens. Consider splitting into progressive reference files.
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-ai-gateway-sdk, ccba-xia]: '| :--- | :--- | :--- | :--- |'

### 🔍 Skill `ccba-xu-ly-van-phong` (2,284 tokens | PDI: 56.5)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-xu-ly-van-phong/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: 'khi thực thi các tác vụ chuyên sâu, agent sử dụng công cụ viewfile để nạp hướng ...'
    * Duplicated across [ccba-academic-writing, ccba-adr-lifecycle, ccba-ai-qc-pccc-audit, ccba-ask, ccba-build-skill, ccba-codebase-design, ccba-contribute-to-hub, ccba-copywriting, ccba-diagnosing-bugs, ccba-docs-manager, ccba-eval-gate, ccba-excalidraw-diagram, ccba-git-guardrails, ccba-grilling, ccba-implement, ccba-init-spoke, ccba-issue-to-hub, ccba-legal-document-tracker, ccba-research, ccba-seminar-builder, ccba-setup-skills, ccba-to-spec, ccba-update-spoke, ccba-xu-ly-van-phong]: '| tệp tham chiếu | ngữ cảnh triệu hồi & mục đích sử dụng |'

### 🔍 Skill `ccba-youtube-learn` (2,017 tokens | PDI: 50.9)
- **Đường dẫn:** `C:/Users/chuvu/.gemini/antigravity/worktrees/ccba-agent-platform/super_halo_rises_18h17/.agents/skills/ccba-youtube-learn/SKILL.md`
- **Trạng thái:** `Optimal`
  - 🔄 **Trùng lặp cần khử (DRY Rule):**
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-autoresearch, ccba-build-skill, ccba-code-review, ccba-contribute-to-hub, ccba-copywriting, ccba-docs-manager, ccba-eval-gate, ccba-grilling, ccba-init-spoke, ccba-issue-to-hub, ccba-knowledge-loop, ccba-maskara, ccba-new-feature, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-spoke-adopter, ccba-tdd, ccba-wayfinder, ccba-youtube-learn]: 'tạo bởi ccba — trung tâm tư vấn và ứng dụng bim trong xây dựng'
    * Duplicated across [ccba-academic-writing, ccba-ai-qc, ccba-ask, ccba-code-review, ccba-copywriting, ccba-docs-manager, ccba-grilling, ccba-knowledge-loop, ccba-maskara, ccba-notebooklm-connector, ccba-research, ccba-session-retrospective, ccba-setup-skills, ccba-skill-repair, ccba-tdd, ccba-youtube-learn]: 'nội dung này được tạo bởi ai agent và cần được xem xét bởi chuyên gia pháp lý và...'
