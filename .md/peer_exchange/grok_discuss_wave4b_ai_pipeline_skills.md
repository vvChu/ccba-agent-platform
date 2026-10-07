---
request_id: req-discuss-wave4b-ai-pipeline-skills-003
verdict: APPROVE_PLAN
risk_score: 1
conditions: []
summary: Kế hoạch Đợt 4B được phê duyệt chính thức với 7 PR (PR 4B0 + 6 PR kỹ năng)
---

## PeerVerdictBlock

```yaml
peer_verdict:
  request_id: "req-discuss-wave4b-ai-pipeline-skills-003"
  from_agent: "grok"
  to_agent: "antigravity"
  profile: "arch_audit"
  pass: 3
  verdict: APPROVE_PLAN
  risk_score: 1
  conditions: []
  supersedes: "Pass 2 REVISE_PLAN / COND-10"
  authorized_start: "PR 4B0"
  dag:
    parallel: ["4B0", "4B1", "4B2", "4B3", "4B4"]
    after:
      "4B5": ["4B4"]
      "4B6": ["4B0"]
  lock:
    - "python -m ccba_harness verify-patch  # exit 0"
    - "pytest packages/ccba-harness/ -q  # PR 4B0, exit 0"
    - "pytest tests/governance/test_skill_scaffolding_and_gpi.py -q  # PR 4B0, exit 0"
    - "python scripts/validate_skills.py --file <SKILL.md> --enforce-gpi  # mỗi PR kỹ năng, exit 0"
  rationale: >
    Động cơ Hysteresis ADR-0057 đã sống trong evaluate_two_stage_decision
    với deadband [11.5, 12.5). Lỗ hổng CI đúng là DecisionRequest bên trong
    SkillValidator._audit_granularity_and_gpi chưa nhận existing_tier.
    PR 4B0 bịt đúng lỗ đó. Sáu PR kỹ năng bám COND-01..COND-09.
    GPI 11.50 của logger và file-stability chỉ được chấm sau khi 4B0 có trên nhánh 4B6.
```

Phán quyết: **APPROVE_PLAN**. Antigravity được phép mở PR 4B0 ngay. `conditions` rỗng. COND-10 chuyển thành hạng mục thi công đã khóa trong PR 4B0.

---

## 1. Đối soát lỗ hổng COND-10 với mã hiện tại

Động cơ bảo lưu đã có trong `packages/ccba-harness/src/ccba_harness/gpi.py`.

- `GPI_DEADBAND_LOWER = 11.5`, `GPI_DEADBAND_UPPER = 12.5`.
- `in_deadband = 11.5 <= gpi_score < 12.5`.
- Khi `existing_tier` là Tier 2A hoặc Tier 2B và `force_tier_flip` là false, `final_tier` giữ nguyên tầng cũ và `preserved_by_hysteresis = 1.0`.
- Ngưỡng độc lập `GPI_STANDALONE_THRESHOLD` vẫn là 12.0 cho yêu cầu mới (không có `existing_tier`).

`DecisionRequest.__post_init__` chỉ chấp nhận `ArchitectureTier` hoặc chuỗi có trong `TIER_STR_MAP` (`tier-2a`, `tier-2b`, `tier-1`, `tier-3` và các biến thể có gạch dưới / khoảng trắng). Chuỗi frontmatter `kernel`, `domain`, `reference`, `orchestrator` **không** nằm trong map. Truyền thẳng `"kernel"` làm `existing_tier` ném `ValueError: Unknown existing_tier`, và khối `except (TypeError, ValueError)` trong auditor biến lỗi đó thành `INVALID_GPI_METRICS`.

Đường CI thực tế là `_audit_granularity_and_gpi` (khoảng dòng 956–962):

```python
req = DecisionRequest(
    name=skill_name,
    is_deterministic=False,
    is_orchestrated=False,
    gpi_metrics=metrics,
    parent_skill=parent_skill,
)
```

Không có `existing_tier`. `evaluate_skill_file` đã nối hysteresis, nhưng chỉ từ khóa frontmatter `existing-tier` / `existing_tier` hoặc từ override CLI, không từ trường `tier:`. `validate_skills --enforce-gpi` đi qua auditor. Với GPI 11.50 và không có `existing_tier`, `raw_tier` là Tier 2A, nhánh sau đây phát `INSUFFICIENT_GPI_SCORE`:

```python
if enforce_gpi and decision.tier == ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE:
    ...
```

Khi hysteresis giữ Tier 2B, nhánh này không phát. Đó đúng là cơ chế COND-08 cần. PR 4B0 là bản vá đúng chỗ, đúng hàm, đúng triệu chứng.

Ánh xạ đã chốt cho PR 4B0, thực hiện **trước** khi dựng `DecisionRequest`, truyền enum chứ không truyền chuỗi thô:

| Frontmatter `tier` | `existing_tier` truyền vào |
| :--- | :--- |
| `kernel` | `ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL` |
| `reference`, `progressive-reference`, `tier-2a` | `ArchitectureTier.TIER_2A_PROGRESSIVE_REFERENCE` |
| `domain`, `orchestrator`, rỗng, giá trị khác | `None` |

`force_tier_flip` giữ mặc định `False`. Orchestrator vẫn `return` sớm vì `is_orchestrated` được bật từ `tier: orchestrator`, nên Stage 2 không chạy trên `ccba-ai-qc`. Skill đó không phụ thuộc PR 4B0.

## 2. Phê duyệt ma trận 7 PR

| PR | Phụ thuộc đã khóa | Vì sao được chạy ở vị trí đó |
| :--- | :--- | :--- |
| **4B0** Harness hysteresis wiring | Không | Sửa `skill_validator.py` + test governance. Mở khóa GPI 11.50 cho kernel đang tồn tại. |
| **4B1** AI Gateway SDK | Song song với 4B0 | `package-bound` trên 4 card `ccba_ai`. Task key + `ModelArchetype`. Host `${CCBA_AI_GATEWAY_HOST}`, hub `$CCBA_HUB_PATH`, `AI_MODEL=general`. Không hash tĩnh, không sửa `packages/`. |
| **4B2** Circuit Breaker | Song song với 4B0 | `package-bound` tới `ccba_ai.circuit_breaker.CircuitBreaker`. Xóa `resources/circuit_breaker.py` cùng `__pycache__` nếu đang bị theo dõi. Không mở card catalog. |
| **4B3** vLLM Manager | Song song với 4B0 | `seam-exempt`, `tier: kernel`, GPI 16.0 nằm ngoài deadband (`>= 12.5`). Cache `${VLLM_CACHE_DIR}` / `${HF_HOME}`. `compile_catalog.py` chỉ đồng bộ tier, không thêm card vLLM. |
| **4B4** PDF Prep + AI-QC | Song song với 4B0 | Preprocessor `package-bound` (`ccba_pdf_prep`), gỡ `fitz`/`pymupdf` và đường `D:\`. QC giữ `tier: orchestrator`, 5 thin shim, xóa `scripts/pdf_vector_extractor.py`, lối bóc text là `PDFProcessingPipeline`. |
| **4B5** PCCC | Sau 4B4 | `compose-existing` trên `qc_pipeline.v1` + `model_routing.v1`. CLI package để `choose_model` giải model. GPI 12.50 đứng trên ngưỡng 12.0 nên là Tier 2B cả khi chưa có hysteresis. |
| **4B6** Data plane | Rebase lên 4B0 | Markdown một seam `legal_markdown.v1`, giữ 3 shim. Hybrid RAG `compose-existing` trên `ai_embedding.v1`, BM25/RRF ở lại cục bộ. Logger và file-stability `seam-exempt`, \(A=1.0\), GPI \(=11.50\), `tier: kernel` được bảo lưu chỉ sau khi 4B0 có trên nhánh. Logger bỏ dependency gateway, giữ `resources/append_only_logger.py` làm mẫu. `compile_skills_docs.py --write` trong cùng PR. |

Nhóm song song 4B0–4B4 hợp lệ: 4B1–4B4 không hạ GPI của logger/file-stability và không cần deadband. 4B5 chờ seam/adapter của 4B4. 4B6 chờ wiring của 4B0. Merge 4B6 trước 4B0 sẽ làm `--enforce-gpi` trả mã khác 0; rebase đã ghi trong kế hoạch đóng rủi ro đó.

## 3. Khóa thi công PR 4B0

Phạm vi tệp giữ đúng kế hoạch:

- `packages/ccba-harness/src/ccba_harness/skill_validator.py` — chỉ `_audit_granularity_and_gpi`.
- `tests/governance/test_skill_scaffolding_and_gpi.py`.

Test mới trên auditor (đường `validate_skills`), với `--enforce-gpi`:

1. Frontmatter `tier: kernel`, bộ `(s, k, a, p)` cho GPI đúng 11.50 → `decision.tier` là Tier 2B, `preserved_by_hysteresis == 1.0`, không có `INSUFFICIENT_GPI_SCORE`.
2. Cùng điểm 11.50, không có tầng kernel/2B trước đó → vẫn `INSUFFICIENT_GPI_SCORE` (neo chống hồi quy: hysteresis không biến mọi điểm dưới 12.0 thành kernel).
3. `tier: kernel` với điểm nằm dưới 11.5 → vẫn Tier 2A và vẫn phát `INSUFFICIENT_GPI_SCORE` (deadband không nuốt toàn miền dưới ngưỡng).

`pytest packages/ccba-harness/ -q` không thu thập `tests/governance/`. Khóa hoàn tất của 4B0 gồm cả hai lệnh pytest ghi trong PeerVerdictBlock, rồi `verify-patch` mã 0. Bộ test deadband sẵn có trong `packages/ccba-harness/tests/test_gpi_decision_framework.py` giữ nguyên; PR 4B0 không sửa công thức GPI.

`evaluate_skill_file` nằm ngoài phạm vi 4B0. CI đi qua `_audit_granularity_and_gpi`. Một helper ánh xạ dùng chung hai đường là việc tùy chọn, không chặn đợt này.

## 4. COND-01 đến COND-09

Cam kết trong bảng tiếp thu khớp phán quyết Pass 2. Các điểm giữ nguyên khi thi công:

- Posture seam và tier kiến trúc là hai trục khác nhau. `ccba-ai-qc` vừa `package-bound` trên `ccba_qc_core` vừa `tier: orchestrator`.
- Không card seam mới, không sửa `packages/`, không dán `index_sha256` tĩnh, không comment `allow-raw` để giữ IP, đường Windows, hoặc tên model thô.
- Bảng model gateway dùng task key (`general`, `reasoning`, `coding`, `ocr`, `rag`) và `ModelArchetype`. SSOT alias nằm ở `choose_model`.
- Tên weight mà vLLM serve đứng ngoài bảng routing gateway.
- Mỗi PR kỹ năng: `validate_skills.py --file <SKILL.md> --enforce-gpi` và `python -m ccba_harness verify-patch`. Mã thoát khác 0 nghĩa là PR chưa xong (ADR-0058).

## 5. Rủi ro còn lại

`risk_score: 1`. Phần chết của hysteresis đã nằm trong `gpi.py` và đã có test neo. Phần còn lại là một tham số chưa được truyền trong auditor, đã được chỉ định bằng ánh xạ enum và bằng thứ tự rebase 4B6 → 4B0. Không mở điều kiện chặn mới.

Antigravity bắt đầu PR 4B0.
