# ADR 0054: Antigravity Lifecycle Hooks & Security Bridge — Adapter Bridge Architecture

| Trường | Giá trị |
|:-------|:--------|
| **Mã ADR** | 0054 |
| **Trạng thái** | ✅ ACCEPTED |
| **Ngày ban hành** | 2026-09-01 |
| **Tác giả** | CCBA AI Agent (Orchestrator) |
| **Bối cảnh** | Teamwork ADR 0053, Subagent Guardrails ADR 0035 |

---

## Bối Cảnh

CCBA Agent Services Platform đã có một hệ thống hook nội bộ hoàn chỉnh gồm 7 hooks (`PrivacyHook`, `ScoutBlockHook`, `NamingHook`, `SimplifyGateHook`, `BrandHook`, `SessionInitHook`, `TestSpeedHook`) được điều phối qua `HookCoordinator` trong `scripts/hooks/`. Hệ thống này hoạt động qua Python function calls (in-process), được gọi bởi CLI `hook_runner.py`.

Antigravity Platform (IDE) cung cấp cơ chế **Lifecycle Hooks** (`hooks.json`) cho phép chạy shell commands tại các sự kiện vòng đời Agent (`PreToolUse`, `PostToolUse`, `PreInvocation`, `Stop`). Giao tiếp qua stdin/stdout JSON camelCase.

Cần kết nối hai hệ thống này mà không tạo trùng lặp logic.

---

## Quyết Định

Triển khai **Adapter Bridge Architecture** — một bridge layer mỏng (`antigravity_hook_bridge.py`) chỉ dịch schema giữa Antigravity I/O contract và CCBA `HookCoordinator`, không chứa business logic.

### Kiến Trúc

```
Antigravity Engine → stdin JSON (camelCase) → Bridge (translate) → HookCoordinator → 7 hooks
                   ← stdout JSON (camelCase) ← Bridge (translate) ← HookResult      ←
```

### Schema Translation

| Antigravity (camelCase) | CCBA (snake_case) |
|:------------------------|:-------------------|
| `toolCall.name` | `tool` |
| `toolCall.args` (object) | `args` (JSON string) |
| `decision` (allow/deny/ask) | `exit_code` (0/1/2) |

### Phase 1 Scope
- Chỉ `PreToolUse` trên matcher `run_command|write_to_file|replace_file_content|multi_replace_file_content`.
- Phase 2 (hoãn): `PostToolUse`, `PreInvocation`, `Stop`.

---

## Giải Pháp Đã Loại Bỏ

1. **Viết logic chặn mới trong bridge** — Vi phạm DRY với 7 hooks hiện tại. Gây duplicated maintenance burden.
2. **Loại bỏ hệ thống hook Python hiện tại** — Mất khả năng test offline qua `hook_runner.py` và CI integration.
3. **Không tích hợp** — Bỏ lỡ cơ hội kết nối security hooks với Antigravity's native gating (deny/ask/force_ask).

---

## Hệ Quả

### Tích Cực
- **Hai entry point cùng codebase**: CLI (`hook_runner.py`) cho CI/offline, Antigravity (`hooks.json`) cho IDE — cùng dẫn về `HookCoordinator`.
- **Không trùng lặp logic**: Bridge chỉ dịch, mọi business logic nằm trong hooks hiện tại.
- **Fail-safe**: Exception trong bridge → `{"decision": "allow"}`, không block IDE.

### Cần Lưu Ý
- **Performance**: Python subprocess overhead ~200-500ms trên Windows (cold start). Matcher scope giới hạn giảm tần suất gọi.
- **stdout contamination**: Hooks dùng `print()` cho diagnostic — bridge phải redirect stdout → stderr khi hooks chạy.
- **Phase 2 debt**: `PostToolUse`, `PreInvocation`, `Stop` chưa triển khai.

---

## Tệp Tin Liên Quan

| Tệp | Vai trò |
|:-----|:--------|
| `.agents/hooks.json` | Cấu hình Antigravity hooks (PreToolUse) |
| `scripts/hooks/antigravity_hook_bridge.py` | Adapter Bridge layer |
| `scripts/hooks/coordinator.py` | HookCoordinator (7 hooks) |
| `scripts/eval/hook_runner.py` | CLI entry point (CI/offline) |
| `scripts/tests/test_antigravity_hook_bridge.py` | 19 test cases |
| `docs/rules/execution_guardrails.md` | Mục 11 — Hooks Policy |
