# Biên Niên Sử Tiến Hóa: Quản Trị Kỹ Năng & Hệ Thống Kiểm Định 5 Khối (`2026-11-03`)

> **Chủ đề:** Lịch sử các quyết định kiến trúc về Khung Quyết Định Hai Giai Đoạn (`ADR-0057`), Khóa Cứng Kiểm Định Tất Định (`ADR-0058`), Chuyển Dịch Thượng Nguồn `mattpocock/skills` (`v1.3.2`) và Kiến Trúc Single-Source 5-Block Verification Harnesses.  
> **Mục lục Wiki:** [`.md/knowledge/wiki/index.md`](index.md) | **Mục lục Gốc:** [`.md/knowledge/index.md`](../index.md)

---

## 1. Decisions (Biên niên sử Quyết định Kiến trúc)

- **Vào ngày `2026-09-19` (`ccba-agent-platform@27101e01` / [ADR-0057](../../../docs/adr/0057-two-stage-granularity-decision-framework-and-gpi.md))**: Nhóm dự án ban hành Khung Quyết Định Hai Giai Đoạn (Cổng 0 Determinism $\to$ Deep Seams; Cổng 1 Orchestration $\to$ Tier 3) và công thức $\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$ với ngưỡng cắt $\text{GPI} \ge 12.0$ cho Standalone Kernel Skill (Tier 2B) và $\text{GPI} < 12.0$ cho Tier 2A Progressive Reference (`references/*.md`).
- **Vào ngày `2026-11-01` (`ccba-agent-platform@27101e01`)**: Bộ kiểm thử [`test_skills_docs_integrity.py`](../../../tests/governance/test_skills_docs_integrity.py) khóa cứng trần **76 Active Hub Skills** tại `.agents/skills/` để ngăn chặn suy giảm độ chính xác định tuyến ngữ nghĩa (routing dilution).
- **Vào ngày `2026-11-02` (`ccba-agent-platform@fb84a076` — PR `#587`)**: Khi tiếp thu 13 cập nhật từ `mattpocock/skills` `v1.3.2` (`4ae2317`), qua thẩm định đối kháng 2 vòng với Grok (`Session: 6acfc77b-69f8-446a-8f2d-59b5e40ff5a3` & `c8938996-3ee7-4309-9c61-25902f319059`), nhóm dự án quyết định áp dụng chiến lược **Hybrid Adopt + Tier 2A Progressive Reference (Zero Skill Bloat)**:
  - Đóng gói 3 quy trình mới có $\text{GPI} < 12.0$ thành Tier 2A References: [`implement-spec.md`](../../../.agents/skills/ccba-implement/references/implement-spec.md) (`COND-01` First-Unit Canary & Single-Writer), [`llm-wiki.md`](../../../.agents/skills/ccba-knowledge-loop/references/llm-wiki.md) (`COND-02` cô lập `.md/knowledge/wiki/index.md`), và [`to-questionnaire.md`](../../../.agents/skills/ccba-grilling/references/to-questionnaire.md).
  - Nâng cấp tại chỗ 10 tệp kỹ năng và tài liệu tham chiếu hiện hữu, giữ nguyên tổng số `76` Hub Skills.
- **Vào ngày `2026-11-11` (`ccba-agent-platform@a67d7cfc..c8aef4f7` — PR `#721`..`#724`, Grok Consultation `Session: 1388f962-b10f-4169-9f97-31896a38f9f5`)**: Nhóm dự án bổ sung chính sách `COMMERCIAL_LICENSED` (`licensed_use: true` trong [`.md/knowledge/upstream_sources.yaml`](../upstream_sources.yaml) kèm khóa cache tiền kẹp `v2:`) cho các kho thương mại có bản quyền (`claudekit-marketing`, `claudekit-engineer`) trên kho `PUBLIC`, áp dụng rào chắn Clean-Room 8-word n-gram & forbidden-token ([`test_skills_docs_integrity.py`](../../../tests/governance/test_skills_docs_integrity.py)), và hoàn tất chuyển dịch 13 mục tồn đọng (`pstack`, `impeccable`, `web-quality-skills`, `claudekit-*`) qua 6 tệp Tier 2A `references/*.md` cùng 2 cập nhật tại chỗ, giữ nguyên `76` Hub Skills và đưa hàng đợi `port_recommendations.md` về `0` mục mở.
- **Vào ngày `2026-11-12` (PR `#725`)**: Mở rộng [`compile_knowledge.py`](../../../scripts/spoke/compile_knowledge.py) (`compile_skills(..., include_references=True)`) để biên dịch toàn bộ tài liệu Tier 2A `references/**/*.md` vào `skills_compiled.md` (`~257K` từ `< 500K` trần nguồn của Google NotebookLM), giúp hệ thống RAG/NotebookLM truy xuất đầy đủ tri thức chuyên sâu của Tier 2A.

---

## 2. Subsystems (Tiến hóa Phân hệ Kiểm định 5 Khối `ccba-harness`)

- **Vào ngày `2026-11-02` (`ccba-agent-platform@fb84a076` — PR `#587`)**: Khởi tạo 2 bộ kiểm định 5 khối đầu tiên (`verify-ccba-harness` bảo vệ `FEAT-001`..`006` và `verify-ccba-xia` bảo vệ `FEAT-XIA-001`..`008`) tại `packages/ccba-harness/.agents/skills/`.
- **Vào ngày `2026-11-03` (`ccba-agent-platform@cd09c566` — PR `#589`)**: `[Superseded by 2026-11-03 @ COND-02 Single-Source Refactor]` Mở rộng thêm 4 bộ kiểm định 5 khối (`verify-ccba-wayfinder`, `verify-ccba-grilling`, `verify-ccba-implement`, `verify-ccba-knowledge-loop`), nâng [`packages/ccba-harness/features/INDEX.md`](../../../packages/ccba-harness/features/INDEX.md) từ 14 lên 42 features và duy trì bản sao kép của `harness/*.py` tại cả `packages/ccba-harness/.agents/skills/verify-ccba-*/harness/` lẫn `.agents/skills/ccba-*/harness/`.
- **Vào ngày `2026-11-03` (`ccba-agent-platform@ae5c1b28` — Grok Consultation `Session: 0a350328-e4e3-4a69-8da7-5ac5ea5dfdeb`)**: Theo điều kiện chặn `COND-02`, kiến trúc bản sao kép (Dual-Tree Mirroring) được thay thế bằng **Canonical Single-Source 5-Block Harnesses** đặt duy nhất tại `packages/ccba-harness/.agents/skills/verify-ccba-<slug>/harness/`, đồng thời mở rộng thêm 4 bộ kiểm định SDLC (`verify-ccba-diagnosing-bugs`, `verify-ccba-tdd`, `verify-ccba-code-review`, `verify-ccba-create-pr`), nâng tổng số lên **70 verified features**.

---

## 3. Recurring Problems & Mitigation Chronicle (Sự cố Lặp lại)

- **Shadowing Không Gian Tên `tests.governance` Trong Kiểm Thử Cô Lập (`2026-11-02`, `ccba-agent-platform@fb84a076`)**:
  - *Nguyên nhân:* Tệp [`scripts/tests/__init__.py`](../../../scripts/tests/__init__.py) định nghĩa một regular package tên `tests`, che khuất thư mục gốc `./tests/` (implicit namespace package) khi `run_isolated_tests.py --all --stress` gọi `pytest scripts/tests`.
  - *Giải pháp neo tại `ccba-agent-platform@fb84a076`:* Mở rộng `__path__` trong `scripts/tests/__init__.py` để nối thêm `Path(__file__).resolve().parents[2] / "tests"`, giúp mọi câu lệnh `from tests.governance...` hoạt động nhất quán ở cả hai chế độ chạy.
- **Trần Bộ Nhớ Tác Nghiệp `10.0 KB` Trên `session_learnings.md` (`2026-11-03`, `ccba-agent-platform@ae5c1b28`)**:
  - *Nguyên nhân:* Tính đến `ccba-agent-platform@ae5c1b28`, tệp [`.md/knowledge/session_learnings.md`](../session_learnings.md) đạt `10,185` bytes (`9.95 KB`), chỉ còn `55` bytes dư địa dưới ngưỡng `10,240` bytes của [`DocAutoEvolutionEngine`](../../../packages/ccba-harness/src/ccba_harness/docs/daemon.py).
  - *Giải pháp (`COND-01`):* Thu gọn từng `RULE-X.Y` về định dạng 1 dòng cô đọng (`< 7.0 KB`), bảo toàn 100% định danh `RULE-\d+\.\d+` cho `ZeroDeletionGuard` và chuyển toàn bộ diễn giải lịch sử sang [`.md/knowledge/archive/session_learnings_history.md`](../archive/session_learnings_history.md).
- **Lệch Phiên Bản `ruff format` Giữa `.venv` Cục Bộ Và GitHub Actions CI (`2026-11-11`, `ccba-agent-platform@a67d7cfc` — PR `#721`)**:
  - *Nguyên nhân:* `.venv` cục bộ cài đặt phiên bản `ruff` cũ hơn `ruff 0.17.4` trên CI, dẫn đến khác biệt ngắt dòng chuỗi đa dòng trong `packages/ccba-harness/tests/`.
  - *Giải pháp:* Luôn chạy `uvx ruff format --check` / `uvx ruff format` đồng bộ với phiên bản mới nhất trên CI trước khi tính lại mã băm `covered_sha256` hoặc đẩy nhánh.
- **Phân Giải Đường Dẫn Kịch Bản Tương Đối Bên Trong `references/*.md` (`2026-11-11`, `ccba-agent-platform@35e8f42e` — PR `#723`)**:
  - *Nguyên nhân:* Bộ kiểm thử [`test_workflow_script_parity.py`](../../../tests/governance/test_workflow_script_parity.py) phân giải đường dẫn code-span tương đối tính từ thư mục cha của tệp Markdown (`references/`) hoặc gốc Hub, nên cú pháp trần `` `scripts/ui/search.py` `` bên trong `.agents/skills/ccba-design/references/*.md` bị báo lỗi không tồn tại.
  - *Giải pháp:* Sử dụng tiền tố tương đối `../scripts/...` hoặc đường dẫn đầy đủ tính từ gốc Hub `.agents/skills/<skill>/scripts/...` bên trong mọi tệp `references/*.md`.

---

## 4. User Preferences & Engineering Posture (Khẩu vị Kỹ thuật)

- **Zero Skill Bloat (`2026-11-02`, `ccba-agent-platform@fb84a076`)**: Luôn ưu tiên nâng cấp tại chỗ các Master Skills hiện hữu hoặc tạo Tier 2A Progressive Reference (`references/*.md`) thay vì sinh thêm thư mục skill mới tại `.agents/skills/`.
- **Single Source of Truth (`2026-11-03`, `ccba-agent-platform@ae5c1b28`, `COND-02`)**: Không chấp nhận duy trì hai tệp mã nguồn vật lý giống hệt nhau ở hai cây thư mục chỉ để phục vụ khám phá đường dẫn; sử dụng phân giải đường dẫn động từ một nguồn chuẩn duy nhất.
