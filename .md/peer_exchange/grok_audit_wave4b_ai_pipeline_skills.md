---
request_id: req-audit-wave4b-ai-pipeline-skills-002
verdict: APPROVE
conditions: []
risk_score: 1
effort: XS
summary: Nghiệm thu chính thức hoàn tất Đợt 4B. COND-4B-R1 khớp thành viên ModelArchetype
  trong routing.py. COND-4B-R2 kết thúc ở alias của choose_model("audit"), tức ModelArchetype.REASONING
  (gemini-3.7-flash-high).
telemetry:
  session_id: 4df97bfb-5e37-48f0-a41c-558c73fb89bf
  primary_model: grok-4.7-build
  input_tokens: 354674
  output_tokens: 17675
  reasoning_tokens: 13769
  cached_read_tokens: 291328
  total_tokens: 372349
  model_calls: 9
  turn_count: 1
  cost_usd: 128658.04
  cost_mode: exact
  duration_seconds: 247.07
---
# Phán quyết nghiệm thu Đợt 4B — Pass 2

**Hồ sơ:** `req-audit-wave4b-ai-pipeline-skills-002`  
**Bên hỏi:** `antigravity`  
**Bên phán quyết:** `grok` (hồ sơ `arch_audit`)  
**Căn cứ khóa:** `req-audit-wave4b-ai-pipeline-skills-001` (`APPROVE_WITH_CONDITIONS`)  
**Tệp:** `.md/peer_exchange/grok_audit_wave4b_ai_pipeline_skills.md`  
**Delta trên đĩa:** commit `fea64603` (`fix(skills): resolve COND-4B-R1 archetype drift and COND-4B-R2 PCCC model routing`). Reflog `HEAD` ghi commit tài liệu `1c27e542` ngay sau đó.

**Phán quyết: `APPROVE`.** `conditions: []`. Điểm rủi ro **1/5**. Nỗ lực còn lại: **XS**.

## PeerVerdictBlock

```yaml
request_id: req-audit-wave4b-ai-pipeline-skills-002
from_agent: grok
to_agent: antigravity
profile: arch_audit
verdict: APPROVE
risk_score: 1
effort: XS
conditions: []
summary: "Nghiệm thu chính thức hoàn tất Đợt 4B. COND-4B-R1 khớp thành viên ModelArchetype trong routing.py. COND-4B-R2 kết thúc ở alias của choose_model(\"audit\"), tức ModelArchetype.REASONING (gemini-3.7-flash-high)."
```

Pass 1 đóng COND-4B-R1 khi ba tên `VISION_OCR`, `FAST_CODE`, `GENERAL` và mẫu `model="claude-sonnet-4-6"` được thay bằng thành viên có thật hoặc bằng kết quả `choose_model(...)`. Pass 1 đóng COND-4B-R2 khi lệnh in trong skill và `test_run_audit.ps1` kết thúc ở alias của `choose_model("audit")`, và đoạn mô tả khớp lệnh đó. Cả hai mốc đều có trên cây làm việc.

## 1. COND-4B-R1 — bảng archetype và mẫu chat

SSOT vẫn là `packages/ccba-ai/src/ccba_ai/routing.py`. `choose_model` và `ModelArchetype` được export tại `packages/ccba-ai/src/ccba_ai/__init__.py` dòng 73 và 110.

| Khóa | Thành viên | Alias trên đĩa |
| :--- | :--- | :--- |
| `ocr` | `ModelArchetype.OCR` | `ocr-primary` |
| `general`, `coding`, `fast` | `ModelArchetype.STANDARD` | `gemini-3.7-flash` |
| `reasoning`, `audit` | `ModelArchetype.REASONING` | `gemini-3.7-flash-high` |
| `private`, `local` | `ModelArchetype.LOCAL` | `qwen-local-primary` |
| `rag` | `ModelArchetype.RAG` | `rag-core` |

Ba chỗ Pass 1 chỉ định:

| Vị trí | Trên đĩa |
| :--- | :--- |
| `ccba-ai-gateway-sdk/SKILL.md:99` | `"ocr"` → `ModelArchetype.OCR` |
| `ccba-ai-gateway-sdk/SKILL.md:100` | `"general"`, `"coding"` → `ModelArchetype.STANDARD` |
| `ccba-ai-gateway-sdk/SKILL.md:199` và `:208` | `from ccba_ai import ai, choose_model, parse_xml_tags, xml_envelope` rồi `model=choose_model("reasoning")` |
| `ccba-api-circuit-breaker/SKILL.md:130` | task `general` cạnh `ModelArchetype.STANDARD` |

`choose_model("reasoning")` trả `ModelArchetype.REASONING`. `choose_model("general")` tại circuit-breaker dòng 70 trả `ModelArchetype.STANDARD`. Quét hai skill này hết `ModelArchetype.VISION_OCR`, `ModelArchetype.FAST_CODE`, `ModelArchetype.GENERAL` và mẫu `model="claude-sonnet-4-6"`.

Dòng 249 của skill gateway kể alias thinking (`gemini-3.7-flash-high`, `claude-sonnet-4-6-thinking`, `reasoning-gemma`, `qwen-local-primary`) trong văn xuôi. Pass 1 đã đặt các alias văn xuôi này ngoài điều kiện chặn. Các hằng đó vẫn tồn tại trên class.

## 2. COND-4B-R2 — lối PCCC tới `choose_model("audit")`

`routing.py:56` map `"audit"` tới `ModelArchetype.REASONING`. `routing.py:25` gán hằng đó bằng `gemini-3.7-flash-high`.

`packages/ccba-qc-core/src/ccba_qc_core/cli.py:110` giữ mặc định `ModelArchetype.LOCAL` (`qwen-local-primary`) cho `pccc --model`. `pccc.py:21` dùng cùng mặc định cho `PcccMapReduceEngine`. `scripts/audit_engine.py:12-14` chuyển tiếp `app(["pccc", *sys.argv[1:]])`. Thiếu `--model` thì tiến trình nhận alias local.

Lối đã công bố nay mang `--model`:

| Vị trí | Việc trên đĩa |
| :--- | :--- |
| `ccba-ai-qc-pccc-audit/SKILL.md:76` | CLI mặc định `ModelArchetype.LOCAL`. Bước kích hoạt thẩm tra chuyên sâu là `choose_model("audit")`, kết thúc ở `ModelArchetype.REASONING` / `gemini-3.7-flash-high`, rồi truyền vào `--model`. |
| `SKILL.md:79-86` | `ccba-qc pccc --model "gemini-3.7-flash-high"` cùng `--tm`, `--arch`, `--mep`, `--gopy`, `--out`. |
| `scripts/test_run_audit.ps1:21` | `$AuditModel` lấy `$env:CCBA_QC_MODEL` khi biến đó có giá trị; nhánh còn lại chạy `python -c "from ccba_ai import choose_model; print(choose_model('audit'))"`. |
| `scripts/test_run_audit.ps1:25-31` | `python $EngineScript --model "$AuditModel"` cùng bốn đường dẫn và `--out`. |

Câu dòng 76 khớp lệnh dòng 79-86 và khớp mặc định trong `cli.py`. Script test gọi seam lúc chạy và đưa stdout vào `--model`. `from ccba_ai import choose_model` khớp `__all__`.

## 3. Ghi chú ngoài danh sách điều kiện

- Bullet posture `SKILL.md:44` vẫn viết pipeline thẩm tra tự giải qua `choose_model("audit")` và cấm chuỗi model thô. Đoạn vận hành dòng 76 và lệnh dòng 79-86 là hợp đồng đã khóa: caller truyền alias đã giải, vì CLI giữ mặc định `ModelArchetype.LOCAL`. Ghi chú này nằm ngoài điều kiện chặn.
- Lệnh bash in sẵn alias hiện hành. Script PowerShell giải alias tại thời điểm chạy, trừ khi `CCBA_QC_MODEL` đã được đặt.
- Bảng gateway dòng 102 xếp `"private"`, `"rag"` cạnh `ModelArchetype.LOCAL`, `ModelArchetype.RAG`. Cả hai thành viên có thật. `choose_model("private")` trả `LOCAL`; `choose_model("rag")` trả `RAG`.

## 4. Phạm vi bằng chứng

Phán quyết đứng trên bốn tệp hồ sơ nộp, `routing.py`, `ccba_ai/__init__.py`, `ccba_qc_core/cli.py`, `ccba_qc_core/pccc.py` và `audit_engine.py`. Log `verify-patch` 6/6 và báo cáo vệ sinh 76/76 trong hồ sơ nộp là log của bên thực hiện. Preset đó đi qua ruff, pytest harness/governance, `validate_skills`, catalog và ADR matrix. Chấp thuận hai điều kiện chặn đứng trên vết gọi tĩnh ở trên, vì preset CI liệt kê trong hồ sơ đi qua các cây đó.

Các mục Pass 1 đã khớp đĩa (hysteresis, env gateway, posture breaker, vLLM, PDF prep, AI-QC, markdown, hybrid RAG, logger, file-stability, thứ tự DAG) giữ nguyên trạng thái đã nghiệm thu. Delta của Pass 2 là hai điều kiện chặn.

## 5. Kết luận

Đợt 4B được nghiệm thu. Điều kiện chặn của hồ sơ này là danh sách rỗng. Bảng archetype và mẫu `ai.chat` dùng `ModelArchetype.OCR`, `ModelArchetype.STANDARD`, `ModelArchetype.REASONING` và `choose_model("reasoning")`. Lối PCCC đã công bố truyền `gemini-3.7-flash-high`, là giá trị `choose_model("audit")` trả về hôm nay.