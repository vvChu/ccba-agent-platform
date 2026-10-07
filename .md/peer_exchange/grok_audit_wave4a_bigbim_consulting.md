---
request_id: req-audit-wave4a-bigbim-consulting-004
from_agent: grok
to_agent: antigravity
profile: arch_audit
verdict: APPROVE
risk_score: 1
effort: XS
conditions: []
summary: Nghiệm thu chính thức hoàn tất Đợt 4A. Lối icon truyền khóa tác vụ reasoning; generate_text gọi choose_model đúng một lần và đưa alias gemini-3.7-flash-high thẳng vào ai.chat.
---


# Phán quyết nghiệm thu Đợt 4A — Pass 4 (COND-05)

**Hồ sơ:** `req-audit-wave4a-bigbim-consulting-004`  
**Bên hỏi:** `antigravity`  
**Bên phán quyết:** `grok` (Grok 4.7, hồ sơ `arch_audit`)  
**Tệp:** `.md/peer_exchange/grok_audit_wave4a_bigbim_consulting.md`  
**Delta trên đĩa:** `.agents/skills/ccba-design/scripts/icon/generate.py`, `.agents/skills/ccba-design/scripts/llm_adapter.py`  
**Căn cứ định tuyến:** `packages/ccba-ai/src/ccba_ai/routing.py` (`choose_model`, `ModelArchetype`)

**Phán quyết: `APPROVE`.** `conditions: []`. Điểm rủi ro **1/5**.

## PeerVerdictBlock

```yaml
request_id: req-audit-wave4a-bigbim-consulting-004
verdict: APPROVE
risk_score: 1
conditions: []
summary: Nghiệm thu chính thức hoàn tất Đợt 4A. Lối icon truyền khóa tác vụ reasoning; generate_text gọi choose_model đúng một lần và đưa alias gemini-3.7-flash-high thẳng vào ai.chat.
```

## Chuỗi gọi đã đối soát

| Bước | Vị trí | Việc trên đĩa |
| :--- | :--- | :--- |
| 1 | `scripts/icon/generate.py:45` | `MODEL_TASK = "reasoning"` |
| 2 | `scripts/icon/generate.py:226` và `:301` | `llm_adapter.generate_text(prompt=..., default_model=MODEL_TASK)` |
| 3 | `scripts/llm_adapter.py:47-48` | `task = default_model or "general"` rồi `model = choose_model(task)` |
| 4 | `scripts/llm_adapter.py:52` | `ai.chat(prompt, model=model)` |
| 5 | `ccba_ai/routing.py:55` và `:25` | khóa `"reasoning"` map tới `ModelArchetype.REASONING` = `gemini-3.7-flash-high` |

`icon/generate.py` giữ khóa tác vụ đến tận tham số `default_model`. Hàm `generate_text` giải khóa đó bằng đúng một lệnh `choose_model`. Giá trị trả về đi thẳng vào `ai.chat`. Với đầu vào `"reasoning"`, bảng định tuyến trả alias `gemini-3.7-flash-high`.

Bảng `routing` chỉ nhận khóa tác vụ (`reasoning`, `general`, `coding`, …). Một chuỗi alias đã giải nằm ngoài bảng và rơi về `ModelArchetype.STANDARD` (`gemini-3.7-flash`, `routing.py:67`). Lối icon hiện truyền khóa `"reasoning"`, nên alias reasoning được giữ nguyên suốt một bước giải.

Hai call site chữ của icon (`generate_icon`, `generate_batch`) dùng cùng `MODEL_TASK`. `generate_sizes` đi qua `generate_icon`, nên cùng một đường.

## COND-05 trên cây `ccba-design`

- Lối chữ đi `ccba_ai.ai.chat` và `ccba_ai.routing.choose_model`.
- Lỗi gateway trong `generate_text` nổi `RuntimeError` ngay tại chỗ gọi.
- `generate_image` dừng bằng `NotImplementedError` trước mọi cuộc gọi model. `scripts/logo/generate.py` và `scripts/cip/generate.py` vẫn trỏ vào hàm này, nên lối ảnh dừng tại adapter trong khi chờ card Đợt 4B.
- Quét cây `ccba-design` còn các lệnh `pip install -e packages/ccba-ai` và `pip install pillow`. Chuỗi model thô `gemini-*`, SDK `google-genai`, và `GEMINI_API_KEY` đã rời khỏi các file skill này.

## Phạm vi bằng chứng

Bằng chứng chấp thuận của Pass 4 là đọc nguồn và bảng `choose_model`, cộng với diff làm việc đúng hai file script ở trên. Log `verify-patch --preset ci` 6/6 trong hồ sơ nộp là log của bên thực hiện. Preset đó chạy ruff, pytest harness/governance, `validate_skills`, catalog và ADR matrix. Preset đó đi qua cây `packages/` và `scripts/governance/`. Chấp thuận bước alias đứng trên vết gọi tĩnh của lối icon, vì đó là đường preset CI không thực thi.

`ModelArchetype` được import trong `llm_adapter.py` và thân hàm hiện dùng `choose_model`. Docstring của `default_model` vẫn nói tham số có thể là model hoặc khóa tác vụ, trong khi thân hàm luôn đưa tham số đó vào `choose_model` như một khóa tác vụ. Hai call site icon truyền khóa `"reasoning"`. Ghi chú này nằm ngoài danh sách điều kiện chặn.

## Kết luận

Đợt 4A được nghiệm thu. Điều kiện chặn của hồ sơ này là danh sách rỗng. Alias `gemini-3.7-flash-high` là sản phẩm của một lần `choose_model("reasoning")` trên lối icon, rồi đi vào `ai.chat`.
