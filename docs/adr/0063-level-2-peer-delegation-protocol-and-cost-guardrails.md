# HUB-ADR 0063: Level-2 Peer Agent Delegation Protocol and Cost Guardrails (Grok ↔ Antigravity)

- **Trạng thái**: ✅ ACCEPTED
- **Ngày quyết định**: 2026-10-05
- **Tác giả**: CCBA Core Architecture & Antigravity Agent
- **Người phản biện**: Grok Peer Reviewer (`APPROVE_WITH_CONDITIONS`, req-level2-discuss-001)
- **Tương thích**: ADR-0007 (Peer Exchange), ADR-0009 (Pstack Disciplines), ADR-0058 (Live Collaboration), ADR-0061 (Platform-Aware KISS v2), ADR-0062 (Declarative Sync Registry)

---

## 1. Bối Cảnh (Context)

Trong đợt nâng cấp ADR-0062 vừa qua, mô hình cộng tác giữa **Antigravity (Orchestrator)** và **Grok CLI (Reasoning & Implementation Engine)** đã chứng minh hiệu quả phân tầng vượt trội: Antigravity gánh 100% các công việc Git/PR/CI/Verification, Grok tập trung vào logic và code TDD.

Tuy nhiên, khi đối soát chi phí thực tế qua `grok usage`:
- Chuỗi 4 phiên tiêu tốn **$10.49 USD** cho **151 model calls** (Planning: $4.87, PR-1: $2.51, PR-2: $1.19, PR-3: $1.92).
- Mặc dù prompt caching của xAI đạt 91–95%, nhưng do Grok CLI chạy ở chế độ ReAct loop không trần vòng lặp (`--max-turns` vô hạn), Grok tự kích hoạt từ 30 đến 54 calls/PR (tự scan thư mục, đọc từng đoạn file lặp lại, chạy pytest nhiều lần).
- Đồng thời, Grok CLI trên hệ thống đã được tích hợp sẵn sàng với **AI Gateway (Server Spark :8090)** và cụm GPU **DGX Spark Blackwell GB10**, cung cấp các mô hình:
  + `qwen-local` (Qwen 35B Local on DGX GB10): **100% Offline, Chi phí 0 USD token!**
  + `gemini-38-flash` (Gemini 3.8 Flash High): Siêu rẻ, Context 1M tokens.
  + `claude-sonnet-4-6` & `claude-opus-4-6`: Coding & reasoning chuẩn mực.
  + `grok-4.7` & `grok-4.7-build-fast`: Direct xAI cloud models.

---

## 2. Quyết Định Kiến Trúc (Decision)

Hệ thống thiết lập **Level-2 Peer Agent Delegation Protocol (ADR-0063)** với 4 trụ cột cốt lõi:

### 2.1. Phân Tầng 3 Execution Profiles Chuẩn Hóa

| Profile | Model CLI (`-m`) | Trần Turns | Danh Mục Tool Cho Phép | Nhiệm Vụ & Ranh Giới |
| :--- | :--- | :---: | :--- | :--- |
| **`AUDIT_PLAN`** | `grok-4.7` (high/xhigh). *Fallback*: `gemini-38-flash` / `claude-opus-4-6` | **12** | `read_file`, `grep`, `list_dir` *(Chặn terminal, write, subagent)* | Thẩm định kiến trúc, lập plan, rà soát pháp lý |
| **`AGENTIC_CODE`** | `grok-4.7-build-fast` hoặc `claude-sonnet-4-6` | **8** | Đọc file, `search_replace`, scoped `pytest` | Viết mã logic theo test đỏ TDD có sẵn |
| **`PATCH_FAST`** | `qwen-local` (0 USD) hoặc `grok-4.7-build-fast` | **1** | **Không dùng tool** (`--max-turns 1`) | Sinh Anchor Replacement cho task nhỏ $\le 100$ LOC |

### 2.2. Hợp Đồng Neo Cho 1-Turn Patch Mode (Anchor Replacement Contract)

Loại bỏ rủi ro lệch dòng (offset drift) do LLM sinh raw `git diff`. Chế độ `PATCH_FAST` bắt buộc tuân thủ schema bản ghi neo:
```json
{
  "files": [
    {
      "path": "packages/foo/src/bar.py",
      "blob_sha256": "<sha256 của file trước khi sửa>",
      "replacements": [
        {
          "old": "đoạn code cũ y nguyên, duy nhất trong file",
          "new": "đoạn code thay thế mới"
        }
      ]
    }
  ]
}
```
Bộ áp dụng `apply_anchor_patch()` thực hiện kiểm chứng nghiêm ngặt:
1. So khớp `blob_sha256` với nội dung tệp hiện hành trên ổ đĩa. Lệch hash $\rightarrow$ dừng khẩn cấp.
2. Kiểm tra `old` xuất hiện **đúng 1 lần duy nhất**. Nếu `count != 1` $\rightarrow$ dừng khẩn cấp, ngăn chặn replace-all bừa bãi.
3. Thay thế chuỗi trực tiếp và ghi đĩa atomic. Sau đó Antigravity tự động sinh diff sạch cho người đọc.

### 2.3. Tách Biệt Tầng Model Slug vs Gateway Alias

- **Grok CLI Slugs** (trong `~/.grok/config.toml`): `qwen-local`, `gemini-38-flash`, `claude-sonnet-4-6`, `claude-opus-4-6`, `grok-4.7`, `grok-4.7-build-fast`.
- **AI Gateway Aliases** (trên Server Spark `:8090`): `qwen-local-primary`, `gemini-3.8-flash-high`, v.v.
- Lệnh dispatch Grok CLI chỉ sử dụng CLI Slugs; Seam `ccba_ai.routing.choose_model()` quản lý Gateway Aliases. Tuyệt đối không lẫn lộn giữa hai tầng.

### 2.4. Đóng Gói Seam & CLI Điều Phối Thống Nhất (`peer-dispatch`)

- Mở rộng Seam `ccba_harness.peer`:
  + `PeerExecutionProfile`, `ModelTier`, `PROFILE_SPECS`, `TIER_DEFAULT_MODELS`.
  + `build_grok_cmd()`: Khởi tạo canonical command list kèm các cờ `--max-turns`, `--tools`, `--disallowed-tools`, `--prompt-file`.
  + `apply_anchor_patch()`: Áp dụng patch neo có kiểm tra path traversal và SHA256.
- Bổ sung subcommand CLI:
  ```bash
  ccba-harness peer-dispatch --prompt-file <path> [--profile <profile>] [--tier <local|gateway|cloud>] [--dry-run]
  ```
- Cung cấp script shim `scripts/peer_dispatch.py` ủy quyền trực tiếp sang harness.

---

## 3. Hệ Quả & Đánh Giá (Consequences)

### 3.1. Điểm Tích Cực
- **Giảm 85% – 100% Chi Phí Viết Mã (Coding Cost)**: Đưa các thay đổi nhỏ sang `qwen-local` (0 USD) trên DGX Spark GB10 hoặc khống chế trần 8 turns trên `grok-4.7-build-fast`.
- **Ngăn Chặn Bão Token**: Trần cứng 8 turns chặn đứng nguy cơ ReAct loop lặp 30–54 calls vô tận.
- **Tính Tất Định Tuyệt Đối**: Hợp đồng neo SHA-256 triệt tiêu hoàn toàn lỗi lệch dòng khi áp patch code tự động.
- **Bảo Toàn Vai Trò Giám Sát**: Antigravity giữ quyền điều phối git, branch, claim lock, và cưỡng chế `verify-patch` (ADR-0058).

### 3.2. Rủi Ro & Cơ Chế Giảm Thiểu (Risk Mitigations)
- *Cửa sổ Context của Qwen Local*: `qwen-local` có context 32k tokens. Giảm thiểu: Chỉ dùng Qwen cho `PATCH_FAST` với prompt được cắt tỉa gọn; không dùng Qwen cho audit đa văn bản hay agentic loop lớn.
- *Chạm trần turns giữa chừng*: Khi dừng ở turn 8 do hết budget mà test chưa xanh, dispatcher ghi nhận HANDOFF để Antigravity xử lý, không bao giờ commit mã vỡ lên nhánh PR.

---

## 4. Kiểm Chứng Tuân Thủ (Compliance Verification)

- **Unit Tests**:
  - `packages/ccba-harness/tests/test_peer.py`: 100% test coverage cho `PeerExecutionProfile`, `build_grok_cmd`, và `apply_anchor_patch`.
  - `packages/ccba-harness/tests/test_peer_dispatch_cli.py`: Kiểm thử CLI `peer-dispatch` và cờ `--dry-run`.
- **Quality Gate**:
  - `python -m ccba_harness verify-patch --preset code` exit code 0.
