# HUB-ADR 0063: Level-2 Peer Agent Delegation Protocol and Cost Guardrails (Grok ↔ Antigravity)

- **Trạng thái**: ✅ ACCEPTED *(Cập nhật v2.6 ngày 2026-11-25)*
- **Ngày quyết định**: 2026-10-05
- **Tác giả**: CCBA Core Architecture & Antigravity Agent
- **Người phản biện**: Grok Peer Reviewer (`APPROVE_WITH_CONDITIONS`, req-level2-discuss-001; `APPROVE_PLAN` v2.6, `3ed0be38`)
- **Tương thích**: ADR-0007 (Peer Exchange), ADR-0009 (Pstack Disciplines), ADR-0058 (Live Collaboration), ADR-0061 (Platform-Aware KISS v2), ADR-0062 (Declarative Sync Registry), ADR-0064..0067

---

## 1. Bối Cảnh (Context)

Trong đợt nâng cấp ADR-0062 vừa qua và xuyên suốt **57 ngày vận hành thực tế (`2026-09-29` → `2026-11-24`, `1,072` biên bản trên 7 repo)**, mô hình cộng tác đã hội tụ rõ nét về kiến trúc **"Antigravity Build + Grok Adversarial Gatekeeper"**: Antigravity gánh toàn bộ thiết kế, viết mã, Git/PR/CI và verification, còn Grok chuyên trách thẩm định phản biện kế hoạch (`audit_plan`), kiến trúc (`arch_audit`), nghiệm thu delta (`signoff_diff`) và review mã nguồn (`code_review`) với `99.4%` lưu lượng chạy theo luồng Gatekeeper (chi phí trung vị chỉ `\$0.52`/chuỗi nhờ `80.6%` Prefix KV-Cache). Các nhánh ủy thác viết mã (`agentic_code`, `patch_fast` dùng `qwen-local`) gần như không phát sinh trong vận hành thực tế nên được hạ cấp thành **tùy chọn / thực nghiệm** thay vì KPI bắt buộc.

Tuy nhiên, trong giai đoạn khởi đầu trước khi có trần turns (`grok usage`):
- Chuỗi 4 phiên tiêu tốn **$10.49 USD** cho **151 model calls** (Planning: $4.87, PR-1: $2.51, PR-2: $1.19, PR-3: $1.92).
- Mặc dù prompt caching của xAI đạt 91–95%, nhưng do Grok CLI chạy ở chế độ ReAct loop không trần vòng lặp (`--max-turns` vô hạn), Grok tự kích hoạt từ 30 đến 54 calls/PR (tự scan thư mục, đọc từng đoạn file lặp lại, chạy pytest nhiều lần).
- Đồng thời, Grok CLI trên hệ thống đã được tích hợp sẵn sàng với **AI Gateway (Server Spark :8090)** và cụm GPU **DGX Spark Blackwell GB10**, cung cấp các mô hình:
  + `qwen-local` (Qwen 35B Local on DGX GB10): **100% Offline, Chi phí 0 USD token!**
  + `gemini-38-flash` (Gemini 3.8 Flash High): Siêu rẻ, Context 1M tokens.
  + `claude-sonnet-4-6` & `claude-opus-4-6`: Coding & reasoning chuẩn mực.
  + `grok-4.7` & `grok-4.7-build-fast`: Direct xAI cloud models.

---

## 2. Quyết Định Kiến Trúc (Decision)

Hệ thống thiết lập **Level-2 Peer Agent Delegation Protocol (ADR-0063)** với trọng tâm chính thức là **Antigravity Build + Grok Adversarial Gatekeeper**, gồm 4 trụ cột kỹ thuật (xem thêm `ADR-0064..0067` cho 8 profiles chuẩn hóa đầy đủ):

### 2.1. Phân Tầng Execution Profiles Cốt Lõi (Gatekeeper Chính + Coding Tùy Chọn)

| Profile | Model CLI (`-m`) | Trần Turns | Danh Mục Tool Cho Phép | Nhiệm Vụ & Ranh Giới |
| :--- | :--- | :---: | :--- | :--- |
| **`AUDIT_PLAN`** *(Chính)* | `grok-4.7` (`xhigh`). *Fallback*: `gemini-38-flash` | **9** | `read_file`, `grep`, `list_dir` *(Chặn terminal, write, subagent)* | Thẩm định kế hoạch, kiến trúc, rà soát pháp lý (kèm Bản đồ `file:line` & batching song song) |
| **`AGENTIC_CODE`** *(Tùy chọn)* | `grok-4.7-build-fast` hoặc `claude-sonnet-4-6` | **8** | Đọc file, `search_replace`, scoped `pytest` | Tùy chọn: viết mã logic theo test đỏ TDD có sẵn khi cần ủy thác cục bộ |
| **`PATCH_FAST`** *(Tùy chọn)* | `qwen-local` (0 USD) hoặc `grok-4.7-build-fast` | **1** | **Không dùng tool** (`--max-turns 1`) | Tùy chọn thực nghiệm: sinh Anchor Replacement cho task nhỏ $\le 100$ LOC |

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
- **Hiệu Quả Kinh Tế Gatekeeper Tối Ưu**: Với Prefix KV-Cache `> 80%` và trần 8–9 turns (`audit_plan = 9`, `arch_audit = 8`, `signoff_diff = 8`, `code_review = 8`), chi phí trung vị mỗi chuỗi đa vòng chỉ `~$0.52 USD` trong khi giữ nguyên khả năng bắt lỗi chặn sâu (các chế độ tùy chọn `qwen-local`/`PATCH_FAST` vẫn sẵn sàng khi cần).
- **Ngăn Chặn Bão Token**: Trần cứng 8–9 turns kết hợp 2 pha `Explore-Then-Synthesize` chặn đứng nguy cơ ReAct loop lặp 30–54 calls vô tận.
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
