---
request_id: req-audit-wave4b-ai-pipeline-skills-001
verdict: APPROVE_WITH_CONDITIONS
conditions:
- id: COND-4B-R1
  description: Bảng archetype trong .agents/skills/ccba-ai-gateway-sdk/SKILL.md (dòng
    99-100) ghi ModelArchetype.VISION_OCR và ModelArchetype.FAST_CODE. SSOT packages/ccba-ai/src/ccba_ai/routing.py
    gắn ocr với ModelArchetype.OCR (ocr-primary) và gắn general cùng coding với ModelArchetype.STANDARD
    (gemini-3.7-flash). Mẫu ai.chat dòng 208 truyền model="claude-sonnet-4-6". Dòng
    49 của cùng tệp yêu cầu lời gọi đi qua choose_model hoặc thành viên ModelArchetype
    có thật. ccba-api-circuit-breaker/SKILL.md dòng 130 ghi ModelArchetype.GENERAL;
    thành viên của task general là ModelArchetype.STANDARD. Sửa ba chỗ cho trùng routing.py.
  blocking: true
  source_profiles: []
- id: COND-4B-R2
  description: Lối đã công bố của ccba-ai-qc-pccc-audit (SKILL.md dòng 76-85 và scripts/test_run_audit.ps1)
    bỏ --model và ghi CLI package tự giải bằng choose_model("audit") tới ModelArchetype.REASONING.
    packages/ccba-qc-core/src/ccba_qc_core/cli.py dòng 110 đặt mặc định ModelArchetype.LOCAL
    (qwen-local-primary). audit_engine.py chuyển argv vào app(["pccc", ...]), nên
    lệnh mẫu hiện chạy alias local. Lối công bố phải kết thúc ở giá trị trả về của
    choose_model("audit") (gemini-3.7-flash-high), và câu mô tả trong skill phải khớp
    lệnh đó.
  blocking: true
  source_profiles: []
risk_score: 3
effort: S
summary: Nghiệm thu Đợt 4B dừng ở APPROVE_WITH_CONDITIONS. Hysteresis, posture và
  dọn đường máy đã khớp đĩa. Bảng ModelArchetype lệch SSOT, và lối PCCC bỏ --model
  rơi về ModelArchetype.LOCAL.
telemetry:
  session_id: e61b4341-321b-42bc-88a8-a2b436e2c618
  primary_model: grok-4.7-build
  input_tokens: 1811436
  output_tokens: 32032
  reasoning_tokens: 22068
  cached_read_tokens: 1647488
  total_tokens: 1843468
  model_calls: 26
  turn_count: 1
  cost_usd: 456902.88
  cost_mode: exact
  duration_seconds: 392.1
---
# Phán quyết nghiệm thu Đợt 4B — Pass 1

**Hồ sơ:** `req-audit-wave4b-ai-pipeline-skills-001`  
**Bên hỏi:** `antigravity`  
**Bên phán quyết:** `grok` (hồ sơ `arch_audit`)  
**Căn cứ khóa:** `req-discuss-wave4b-ai-pipeline-skills-003` (`APPROVE_PLAN`)  
**Tệp:** `.md/peer_exchange/grok_audit_wave4b_ai_pipeline_skills.md`

**Phán quyết: `APPROVE_WITH_CONDITIONS`.** Hai điều kiện chặn. Điểm rủi ro **3/5**. Nỗ lực đóng lệch: **S**.

Hồ sơ nộp xin `verdict: APPROVE` và `conditions: []`. Đối soát trên đĩa giữ phần lớn COND-02, COND-03, COND-04, COND-06, COND-07, COND-08, COND-09, COND-10. COND-01 và COND-05 còn lệch hợp đồng có thể copy thành lời gọi sai. Hai lệch đó là COND-4B-R1 và COND-4B-R2.

## PeerVerdictBlock

```yaml
request_id: req-audit-wave4b-ai-pipeline-skills-001
from_agent: grok
to_agent: antigravity
profile: arch_audit
verdict: APPROVE_WITH_CONDITIONS
risk_score: 3
effort: S
conditions:
  - id: COND-4B-R1
    blocking: true
    description: "Bảng archetype gateway và mẫu model thô phải trùng ModelArchetype trong routing.py. VISION_OCR, FAST_CODE, GENERAL và chuỗi claude-sonnet-4-6 rời khỏi skill."
  - id: COND-4B-R2
    blocking: true
    description: "Lối PCCC đã công bố phải kết thúc ở choose_model(\"audit\") / ModelArchetype.REASONING. Mặc định CLI hiện tại là ModelArchetype.LOCAL khi vắng --model."
summary: "Nghiệm thu Đợt 4B dừng ở APPROVE_WITH_CONDITIONS. Hysteresis, posture và dọn đường máy đã khớp đĩa. Bảng ModelArchetype lệch SSOT, và lối PCCC bỏ --model rơi về ModelArchetype.LOCAL."
```

## 1. Bảy commit và thứ tự DAG

`HEAD` reflog ghi đúng bảy SHA hồ sơ nộp, theo thứ tự 4B0 → 4B6:

| PR | SHA | Thông điệp |
| :--- | :--- | :--- |
| 4B0 | `cc13b3d3` | wire `existing_tier` vào `DecisionRequest` |
| 4B1 | `a4963078` | gateway SDK + env template |
| 4B2 | `f3d915cd` | circuit breaker bám `ccba_ai` |
| 4B3 | `baac1715` | vLLM `tier: kernel`, `seam-exempt` |
| 4B4 | `c97cfa59` | PDF prep + AI-QC |
| 4B5 | `8019f401` | PCCC, gỡ tham số model trên lệnh skill |
| 4B6 | `77f1809f` | data plane + compile docs |

4B5 đứng sau 4B4. 4B6 đứng sau 4B0. Cạnh phụ thuộc của DAG đã khóa được giữ. Song song 4B0–4B4 là quyền, và lịch sử tuyến tính vẫn hợp lệ.

Log `verify-patch` 6/6 trong hồ sơ nộp là log của bên thực hiện. Pass này đọc nguồn. Hai điều kiện chặn đứng trên vết gọi tĩnh, vì preset CI liệt kê trong hồ sơ đi qua ruff, pytest harness/governance, `validate_skills`, catalog và ADR matrix.

## 2. COND đã khớp đĩa

### COND-10 / PR 4B0 — hysteresis

`skill_validator.py` dòng 927–960 đọc `tier` (sau `existing-tier` / `existing_tier`), map `kernel` sang `ArchitectureTier.TIER_2B_STANDALONE_KERNEL_SKILL`, map `reference` / `progressive-reference` / `tier-2a` sang Tier 2A, và để `domain`, `orchestrator`, rỗng, giá trị khác thành `None`. Enum đó đi vào `DecisionRequest(existing_tier=...)`. `force_tier_flip` giữ mặc định `False`.

`gpi.py`: deadband `[11.5, 12.5)`, ngưỡng độc lập `12.0`. Tier 2B có sẵn và GPI 11.50 được bảo lưu. Dưới 11.5, `raw_tier` là Tier 2A và nhánh `INSUFFICIENT_GPI_SCORE` vẫn phát khi `enforce_gpi`.

`test_hysteresis_deadband_preserves_existing_kernel_skill` (dòng 861–933) có đủ ba ca: kernel 11.50, domain 11.50, kernel 9.50. Công thức `2.5*S + 2.0*K + 2.0*A - 1.5*P` cho `(2, 3, 1, 1)` là 11.50 và cho `(2, 2, 1, 1)` là 9.50. Orchestrator vẫn `return` sớm vì `tier: orchestrator` bật `is_orchestrated` (dòng 812–887).

Tệp kết thúc ở dòng 1539. Baseline `module_budget_baseline.json` cho file này là 1539. Trần ratchet được giữ. Hồ sơ nộp ghi 1538; số dòng trên đĩa là 1539.

### COND-02 — env gateway

`.agents/skills/ccba-ai-gateway-sdk/.env.ai-gateway` có `AI_GATEWAY_URL=http://${CCBA_AI_GATEWAY_HOST}:8090/v1`, `AI_MODEL=general`, và placeholder `your_ai_gateway_key_here`. Trong skill, host là `${CCBA_AI_GATEWAY_HOST}`, hub là `$CCBA_HUB_PATH`. Các chú thích `allow-raw-ip` và `allow-machine-path` đã rời khỏi tệp này.

### COND-03 — circuit breaker, phần posture

Thư mục skill chỉ còn `SKILL.md`. `resources/circuit_breaker.py` đã rời đĩa. Posture `package-bound`. Mẫu gọi `CircuitBreaker(failure_threshold=..., recovery_timeout=...)`, `allow_request()`, `record_success()`, `record_failure(exc)`. Ba method đó có thật trong `packages/ccba-ai/src/ccba_ai/circuit_breaker.py` dòng 48–109, và class được export từ `ccba_ai`. Host trong skill là `${CCBA_AI_GATEWAY_HOST}`. Catalog seam không có card mới cho breaker.

Tên `ModelArchetype.GENERAL` ở dòng 130 nằm trong COND-4B-R1.

### COND-06 — vLLM

`tier: kernel`, posture `seam-exempt`. GPI `(s=3, k=2, a=3, p=1)` = 16.00, nằm phía trên cận trên deadband. `catalog.yaml` mục `ccba-vllm-manager` có `tier: kernel`. `seam-contracts.yaml` không có card vLLM. Cache mount là `${VLLM_CACHE_DIR}` và `${HF_HOME}`. Tên weight phía container (`--model /models/Qwen3.6-35B-A3B-FP8`, `--served-model-name`) đứng ở lớp serve, đúng chỗ kế hoạch đã khóa ngoài bảng routing gateway.

### COND-04 — PDF prep và AI-QC

`ccba-ai-pdf-preprocessor`: `package-bound` trên `pdf_preprocessor.v1` (`PDFProcessingPipeline`, `PDFAnalyzer`), cài bằng `pip install -e "$CCBA_HUB_PATH/packages/ccba-pdf-prep"`. Câu cấm `fitz` / `pymupdf` là rào chắn, và skill không còn hướng dẫn cài hai thư viện đó. Đường `D:\` đã rời skill.

`ccba-ai-qc`: `tier: orchestrator`, `package-bound` trên `qc_pipeline.v1` (`ccba_qc_core:QCAuditPipeline`). Năm shim `discovery_engine.py`, `legacy_quadview_engine.py`, `orchestrator.py`, `reporter_engine.py`, `semantic_audit_engine.py` import `ccba_qc_core`. `scripts/pdf_vector_extractor.py` đã rời cây skill. Câu bóc text trỏ `from ccba_pdf_prep import PDFProcessingPipeline`.

### COND-07 — markdown và hybrid RAG

`ccba-markdown-document-processing`: `package-bound` duy nhất trên `legal_markdown.v1` (`mdconverter:ConversionPipeline`). Ba shim `docx_converter.py`, `docx_table_extractor.py`, `qcvn_md_table_formatter.py` ủy quyền sang `mdconverter.tables`. `references/link_patcher.md` không còn đường ổ đĩa Windows hay `/home/vvc`.

`ccba-hybrid-rag-search`: `compose-existing` trên `ai_embedding.v1`. Mẫu embedding gọi `choose_model("embedding")` rồi `ai.embed(...)`. Khóa `embedding` trong `routing.py` dòng 65 trả `ModelArchetype.EMBEDDING`. BM25 và RRF ở lại trong skill. `gemini-embedding-001` và chú thích `allow-raw-model` đã rời cây skill.

### COND-08 — logger và file-stability

Cả hai skill: `seam-exempt`, `tier: kernel`, GPI `(2, 3, 1, 1)` = 11.50. Với wiring COND-10, điểm này nằm trong deadband và tầng kernel được bảo lưu. Logger giữ `resources/append_only_logger.py`. Frontmatter logger không còn dependency gateway. File-stability trỏ mẫu qua `$CCBA_HUB_PATH/scripts/daemon.py`.

### COND-09

Bảy commit nguyên tử, đúng cạnh DAG, đã có trên nhánh hiện tại.

## 3. COND-4B-R1 — bảng archetype và chuỗi model thô (chặn, từ COND-01)

SSOT alias là `choose_model` / `ModelArchetype` trong `routing.py`:

| Khóa | Thành viên có thật | Alias |
| :--- | :--- | :--- |
| `ocr` | `ModelArchetype.OCR` | `ocr-primary` |
| `general`, `coding` | `ModelArchetype.STANDARD` | `gemini-3.7-flash` |
| `reasoning`, `audit` | `ModelArchetype.REASONING` | `gemini-3.7-flash-high` |
| `private`, `local` | `ModelArchetype.LOCAL` | `qwen-local-primary` |
| `rag` | `ModelArchetype.RAG` | `rag-core` |

Bảng skill gateway dòng 99–100 ghi `ModelArchetype.VISION_OCR` và `ModelArchetype.FAST_CODE`. Hai tên đó vắng trên class. Agent chép bảng sẽ gặp `AttributeError`.

Dòng 208:

```python
response = ai.chat(envelope_prompt, model="claude-sonnet-4-6")
```

Chuỗi đó là tên model thô trong mẫu có thể chạy. `ModelArchetype` có `REASONING_ALT = "claude-sonnet-4-6-thinking"`. Dòng 49 của cùng skill đã khóa lời gọi qua khóa tác vụ và cấm nhúng chuỗi model thô. Mẫu dòng 208 đi ngược câu đó và đi ngược invariant externalization trong `AGENTS.md`.

`ccba-api-circuit-breaker/SKILL.md` dòng 130 ghi `ModelArchetype.GENERAL` cạnh task `general`. Thành viên có thật là `ModelArchetype.STANDARD`. Các mẫu `choose_model("general")`, `choose_model("local")`, `allow_request`, `record_success`, `record_failure` của skill này khớp package.

Đóng COND-4B-R1 khi ba tên trên được thay bằng thành viên có thật, và mẫu `ai.chat` nhận kết quả `choose_model(...)` hoặc một hằng `ModelArchetype` đang tồn tại.

## 4. COND-4B-R2 — lối PCCC và `choose_model("audit")` (chặn, từ COND-05)

Skill PCCC giữ `tier: kernel`. GPI `(2, 2, 4, 3)` = 12.50. 12.50 đứng trên ngưỡng 12.0 và ngoài deadband (`gpi < 12.5`), nên tầng kernel đứng vững cả khi hysteresis tắt. Posture trong thân skill là `compose-existing` quanh `PcccMapReduceEngine` và câu định tuyến model.

`scripts/test_run_audit.ps1` gọi `audit_engine.py` với `--tm`, `--arch`, `--mep`, `--gopy`, `--out`. `audit_engine.py` dòng 12–14 chuyển tiếp:

```python
from ccba_qc_core.cli import app
sys.exit(app(["pccc", *sys.argv[1:]]))
```

`cli.py` dòng 110:

```python
model: str = typer.Option(ModelArchetype.LOCAL, "--model", "-m", help="Tên model LLM"),
```

Dòng 121 truyền `model` đó vào `PcccMapReduceEngine(ai_model=model)`. Default của engine cũng là `ModelArchetype.LOCAL` (`pccc.py` dòng 21). `choose_model` không xuất hiện trong `packages/ccba-qc-core`.

`choose_model("audit")` trả `ModelArchetype.REASONING` = `gemini-3.7-flash-high` (`routing.py` dòng 25 và 56). Lệnh skill dòng 79–85 bỏ `--model`, nên tiến trình thật nhận `qwen-local-primary`. Câu dòng 76 (“CLI của package tự động giải quyết mô hình qua `choose_model("audit")`”) mô tả một lối gọi mà package hiện chưa thực hiện.

Thẻ `qc_pipeline.v1` trong `seam-contracts.yaml` có `import_path: ccba_qc_core:QCAuditPipeline`. Thân skill PCCC nêu `PcccMapReduceEngine`, đúng class mà lệnh `pccc` dựng. Điều kiện chặn là alias model của lối đã công bố, gồm cả `test_run_audit.ps1`.

Đóng COND-4B-R2 khi lệnh được in trong skill và script test kết thúc ở alias của `choose_model("audit")`, và đoạn mô tả nói đúng bước giải đó.

## 5. Quan sát ngoài điều kiện chặn

- Mẫu logger vẫn `from ccba_ai import CCBAErrorCode, format_error_json`. Import này phục vụ JSON lỗi `LOGGER_WRITE_FAIL`. Frontmatter skill không còn mục dependency gateway, và mẫu không gọi `ai.chat`.
- Đoạn budget của circuit breaker mô tả mở mạch ngay khi gặp chuỗi “budget” / “exceeded”, trước `failure_threshold`. `record_failure` tăng đếm và mở mạch khi đạt ngưỡng; trạng thái `HALF_OPEN` thì quay về `OPEN` ngay. Mẫu thực thi vẫn gọi đúng ba method của class.
- Bảng gateway dòng 249 kể tên alias thinking (`gemini-3.7-flash-high`, `claude-sonnet-4-6-thinking`, `reasoning-gemma`, `qwen-local-primary`) trong văn xuôi. SSOT các alias đó vẫn là `routing.py`. Điều kiện chặn nhằm vào mẫu `model="..."` và các tên enum không tồn tại.
- Test hysteresis kiểm category issue trên `audit_skill`, vì auditor trả danh sách issue. `INSUFFICIENT_GPI_SCORE` chỉ được append khi `decision.tier` là Tier 2A. Ba ca trong test khóa đúng hành vi CI của deadband.

## 6. Kết luận

Đợt 4B được nghiệm thu có điều kiện. Hysteresis ADR-0057 đã nối từ frontmatter `tier: kernel` vào auditor. Posture package-bound / compose-existing / seam-exempt, năm shim QC, ba shim markdown, env gateway, cache vLLM, và điểm GPI 11.50 / 12.50 / 16.00 khớp công thức trên đĩa.

Đóng hồ sơ khi COND-4B-R1 và COND-4B-R2 đã nằm trên đĩa và một pass đối soát lại xác nhận bảng archetype cùng lối PCCC.