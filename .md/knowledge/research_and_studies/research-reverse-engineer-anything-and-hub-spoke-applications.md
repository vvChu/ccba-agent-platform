# Nghiên Cứu Kiến Trúc: Hệ Sinh Thái "Reverse Engineer Anything" (`morluto/rea`) & Bản Đồ Chuyển Hóa Cho CCBA 4-Hubs × Federated Spokes

- **Ngày thực hiện**: 2026-11-06
- **Phương pháp luận**: Double-Pass Adversarial Review (Vòng 1: Code-First Research qua GitHub API `[đo thực tế]` $\to$ Vòng 2: Self-Adversarial Review & Đối sánh Kiến trúc Hub-Spoke)
- **Liên kết ADRs nội bộ**: ADR-0057 (Two-Stage Granularity & GPI), ADR-0058 (Hard Completion Lock), ADR-0059 (Cryptographic Provenance), ADR-0060 (4-Hubs × Federated Spokes), ADR-0061 (Platform-Aware KISS v2), ADR-0063 (Level-2 Peer Delegation), ADR-0065 (Peer Runtime Hardening & Topological Fail-Closed)

---

## Phần 1: Giải Phẫu Kiến Trúc `morluto/rea` (Reverse Engineer Anything)

### 1.1. Hồ sơ Repository `[đo thực tế]`
- **Repository**: https://github.com/morluto/rea (`npm: rea-agents`, `mcpName: io.github.morluto/rea`)
- **Phiên bản**: `v6.8.0` (TypeScript ESM + Python/Java/Swift/C++ Node-API bridges)
- **Quy mô**: **436.213 Stars**, **108.199 Forks**, License **MIT** (tính đến 06/11/2026)
- **Định vị**: Một MCP Server và CLI hợp nhất chạy 100% cục bộ (local-only, read-only), kết nối AI Coding Agents với các bộ máy phân tích sâu từ hành vi trình duyệt/ứng dụng xuống tới mã máy nhị phân.

### 1.2. Kiến trúc Phân Tầng Hướng Nội (Inward Dependency Flow)
Từ `docs/architecture.mermaid` và 46 phân hệ trong `src/` `[đo thực tế]`:
1. **Entry Points & Adapters**: `scripts/rea.mjs` điều phối về `src/cli/` (one-shot CLI) hoặc `src/main/` + `src/server/` (MCP stdio mặc định, Streamable HTTP opt-in).
2. **Production Composition (`src/composition/`)**: Khởi tạo các provider factories có kiểu tĩnh (typed capability bindings), quản lý vòng đời phiên (`CapabilityScope`) và thu hồi tài nguyên thất bại (`retained cleanup retry`).
3. **Application Layer (`src/application/`)**:
   - `SessionProviderRouter` + `BinarySession`: Mỗi mục tiêu (target) gắn với một deep provider bất biến duy nhất.
   - `EvidenceLedger` + `InvestigationRecords`: Quản lý chuỗi bằng chứng và các ẩn số chưa giải quyết (`Unknowns`).
4. **Provider Layer**: Ghidra (`bridge/ghidra/ReaGhidraBridge.java`), Hopper (`bridge/hopper_bridge.py`), IDA (`ida-pro-mcp`), Kuna, Rizin, GDB/pwndbg, pwntools, JADX (`ReaJadxBridge.java`), Apktool, ADB, Frida, Playwright/CDP, V8 Inspector, WABT, EVMole, SQLite, GGUF/safetensors, CUDA/HIP fatbin/PTX.
5. **Contracts & Domain (`src/contracts/`, `src/domain/`)**: Định nghĩa Zod schemas (`evidence.ts`, `errorSchemas.ts`), hàm băm định danh ngữ nghĩa `canonicalJsonDigestSteps.js`.

### 1.3. 5 Trụ cột Kỹ thuật Đặc sắc của `morluto/rea`

#### (A) Hợp đồng Bằng chứng Mật mã (`Evidence` Schema - `src/domain/evidence.ts`) `[đo thực tế]`
- Mọi kết quả phân tích đều kết tinh thành bản ghi `Evidence` bất biến có `evidence_id: "ev_<sha256>"`.
- Phân định rõ:
  - `confidence`: `"observed" | "derived" | "inferred"`
  - `authority`: `"shipped-artifact" | "controlled-replay" | "historical-reference" | "external-service" | "analyst-inference"`
  - `limitations`: Danh sách các giới hạn phạm vi quan sát.
  - `relationship_coverage`: Phạm vi các cạnh đồ thị đã kiểm chứng so với chưa phân giải (`unresolved`).

#### (B) Tiết kiệm Ngữ cảnh bằng Con trỏ Bằng chứng (`Retained Evidence Summary`) `[đo thực tế]`
- Khi chạy các công cụ trả dữ liệu lớn (`analyze_function`, `list_procedures`, `inspect_web_network_capture`), REA không trả toàn bộ dữ liệu thô làm tràn context của LLM.
- Nó lưu hồ sơ đầy đủ (complete dossier) vào bộ nhớ phiên và chỉ trả về một `inspect_analysis_view` summary chứa `parent_evidence_id`.
- Các công cụ hậu kiểm (`compare_functions`, `match_native_functions`, `compare_artifacts`) nhận trực tiếp tham chiếu `{"kind": "retained-evidence", "evidence_id": "ev_..."}` thay vì bắt LLM gửi lại toàn bộ JSON.

#### (C) Chiếu Lược đồ Kép (`Compact` vs `Full` Schema Advertisement) `[đo thực tế]`
- Để tương thích với giới hạn kích thước JSON Schema của nhiều LLM Gateways (Gemini function declarations từ chối `dependentRequired` và `items` đa kiểu; Moonshot Kimi / Anthropic gateways lỗi với `oneOf`/`allOf` sâu quá 10 tầng), REA mặc định dùng `REA_MCP_INPUT_SCHEMA_PROFILE=compact`:
  - Loại bỏ prose mô tả lồng nhau, làm phẳng root object unions, giữ nguyên tên trường và kiểu cơ bản.
  - Tuy nhiên, tại tầng thực thi (`MCP Handler`), REA vẫn chạy bộ kiểm tra **Canonical Runtime Validation** đầy đủ để chặn mọi request sai quy cách trước khi gọi xuống Provider.

#### (D) Sổ cái Nghĩa vụ Tái tạo (`Reconstruction Obligation Ledger`) `[đo thực tế]`
- Công cụ `build_reconstruction_obligation_ledger` (`docs/reconstruction-obligation-ledgers.md`) biến các quan sát tĩnh/động thành danh sách các nghĩa vụ (`Obligations`) mà bản code viết lại (reconstructed app) bắt buộc phải chứng minh.
- Một nghĩa vụ chỉ được phép đóng (`closed`) khi bản kê (`manifest`) cung cấp đủ:
  1. Định danh chủ sở hữu duy nhất kèm SHA-256 của file code thực thi.
  2. Kiểu dữ liệu parser/schema đầu vào (`requires_parser_type`).
  3. Đầy đủ các loại test cases yêu cầu (`positive`, `negative`, `malformed`, `cancellation`).
  4. Bằng chứng chạy trình kiểm tra (`verifier`) có cấp thẩm quyền (`authority`) tương đương với bản gốc (ví dụ `controlled-replay` trên tiến trình thực) và không còn ẩn số tồn đọng (`residual_unknown_ids`).

#### (E) Biên dịch File `.har` thành Môi trường MCP & RL (`Environment Manifest & Serve`) `[đo thực tế]`
- Từ một file `.har` (sau khi đã xác nhận `sensitive_value_count: 0`, giải mã cả Protobuf/gRPC/gRPC-Web), lệnh `rea environment-build` dùng 4 quy tắc nội suy đường dẫn (`after-uid-literal`, `opaque-token`, `sibling-variance`, `prefix-variance`) để gom nhóm URL thành các MCP Tools có khuôn mẫu `body_shape` không chứa giá trị nhạy cảm.
- Lệnh `rea environment-serve` dựng lại **Trạng thái quan sát được (`Observed State`)** từ file `.har`: phục vụ các lệnh đọc từ trạng thái này và chỉ cho phép các lệnh ghi thay đổi trạng thái nếu bản ghi `.har` gốc xác nhận hiệu ứng thay đổi đó (hoặc chạy ở chế độ `--replay-only`), đồng thời xuất chuẩn `/.well-known/agent-env.json` cho huấn luyện RL.

---

## Phần 2: Toàn Cảnh Hệ Sinh Thái GitHub Tương Tự & Phân Tích Chuyên Sâu 3 Đại Diện

Khảo sát toàn bộ GitHub tính đến **06/11/2026** `[đo thực tế]` cho thấy hệ sinh thái xoay quanh AI Reverse Engineering chia thành 4 nhóm vệ tinh:
1. **Engine-Specific MCPs**: `mrexodia/ida-pro-mcp` (13.382 ⭐), `LaurieWired/GhidraMCP` (11.783 ⭐), `bethington/ghidra-mcp` (6.136 ⭐), `P4nda0s/IDA-NO-MCP` (2.073 ⭐), `HexRaysSA/ida-mcp` (1.546 ⭐), `blacktop/ida-mcp-rs` (900 ⭐), `zinja-coder/apktool-mcp-server` (708 ⭐).
2. **Autonomous Binary Pipelines & LLM Decompilers**: `albertan017/LLM4Decompile` (7.258 ⭐), `amruth-sn/kong` (1.243 ⭐), `416rehman/DeepZero` (770 ⭐).
3. **SaaS/Web App Cloning & Internal API Compilers**: `Jakeschincariol/replica-skill` (7.832 ⭐), `unbrowse-ai/unbrowse` (904 ⭐), `alextnetto/res` (270 ⭐).
4. **Meta-Indexes & Specialty**: `cranebeaker/coop-anything` (1.919 ⭐), `alexgaoth/awesome-reverse-engineered` (1.252 ⭐ — 17.714 tools), `AIshihzong/awesome-reverse-engineer-anything` (503 ⭐), `zhuyansen/awesome-ai-reverse-engineering` (60 ⭐), `utabk/marrow` (GUI cho REA).

### 2.1. Giải phẫu `amruth-sn/kong`: Thuật toán Bottom-Up Call-Graph & 2 Lỗi Thực thi Phát hiện từ Code `[đo thực tế]`
- **Cơ chế (`kong/agent/queue.py`, `kong/agent/supervisor.py`)**:
  - Chạy Ghidra trực tiếp trong tiến trình Python qua `PyGhidra`/`JPype`.
  - Lọc bỏ hàm `IMPORTED` và `THUNK`, tìm các hàm lá (`leaves`, `depth = 0`) và duyệt ngược lên hàm gọi (`caller`) để gán độ sâu: `priority = depth * 1_000_000 + func.size`.
  - Chuẩn hóa cú pháp mã C (`kong/normalizer/syntactic.py`) trước khi gọi LLM; tách luồng hàm thường (gom chunk) và hàm bị obfuscate (chạy tuần tự với Deobfuscator), sau đó ghi ngược tên hàm/biến/struct vào Ghidra DB và chạy `SemanticSynthesizer`.
- **Phản biện Vòng 2 (2 lỗi phát hiện trực tiếp trong code của `kong`)**:
  1. Tại `kong/agent/queue.py#L97-L106`: Hàm `_compute_depths` dùng tập `visited` chặn đẩy lại nút vào hàng đợi BFS. Trên đồ thị DAG đa nhánh (khi `A` gọi cả nhánh nông `B` và nhánh sâu `C`), các hàm gọi `A` không được lan truyền độ sâu mới sau khi nhánh `C` hoàn tất.
  2. Tại `kong/agent/supervisor.py#L237`: Hàm `_analyze_chunks` gọi `items.sort(key=lambda x: len(x[1]))` làm **mất hoàn toàn thứ tự `depth` của `WorkQueue`** đối với các hàm xử lý theo lô.

### 2.2. Giải phẫu `Jakeschincariol/replica-skill`: Máy Trạng Thái 11 Skills & Cổng Kiểm Định Python Stdlib `[đo thực tế]`
- **Cơ chế**: Chuỗi 11 skills (`recon -> architect -> design -> build -> backend -> test -> diff -> entrepreneur -> brand -> launch -> deploy`) giao tiếp qua thư mục hợp đồng `replica/` (`recon.md`, `features.csv`, `tokens.json`, `reviews.csv`).
- **Điểm sáng kỹ thuật (Zero-Dependency Python Gates)**:
  - `replica-diff/imgdiff.py`: Tự viết bộ đọc và giải nén bộ lọc Paeth của PNG 8/16-bit bằng thư viện chuẩn `zlib` và `struct`; chuyển ảnh gốc và ảnh clone sang bản đồ cạnh (Edge Maps) chia lưới để chấm điểm bố cục bất biến với việc đổi màu thương hiệu (`mode="layout"`).
  - `replica-diff/parity.py`: Kết hợp ma trận `features.csv` và điểm thị giác từ `imgdiff.py`, trả về `exit code 1` nếu dưới ngưỡng `--fail-under`.
  - `replica-entrepreneur/reviews.py`: Bắt buộc mọi đánh giá phải có `url` và trích dẫn nguyên văn (`substring`), tính trọng số theo số sao (1 sao = `+1.0`, 5 sao = `+0.2`) kèm suy giảm thời gian (`0.5x` cho đánh giá cũ hơn 18 tháng) và gắn cờ `thin` nếu dưới 3 nguồn.
  - `replica-design/contrast.py`: Tính độ tương phản WCAG 2.2 AA/AAA trực tiếp từ `tokens.json`.

### 2.3. Giải phẫu `unbrowse-ai/unbrowse`: Biên dịch HAR sang HTTP Harness (`arXiv:2604.00694`) `[đo thực tế]`
- **Cơ chế 2 pha (`Learn` $\to$ `Replay`)**:
  - Gom nhóm họ request, lọc bỏ tracking/analytics; so sánh chênh lệch giữa 2 phiên chạy (Cross-session diff) để tìm biến đầu vào (`slots`) và tham số tùy chọn.
  - Truy vết ngược (Backward Data-Flow Tracing) mọi CSRF token/ID trong Request $N$ về Response $M < N$ đã sinh ra nó, xuất ra gói `unbrowse/v1alpha1` YAML.
  - Kiểm chứng kết quả nghiệp vụ độc lập (`HTTP 200 != succeeded`), chặn gửi lại lệnh ghi khi mất kết nối (`outcome_unknown`), và kiểm tra cờ `typed_input_unused`.
- **Phản biện Vòng 2**: Theo `docs/whitepaper/system-today.md`, toàn bộ trình biên dịch lõi của `unbrowse` là **Closed-Source trên Cloud (`unbrowse.ai`)**, trong khi repo GitHub chỉ là thin client. Do đó, với nguyên tắc tự chủ hạ tầng của CCBA, cơ chế `environment-build` mở hoàn toàn của `morluto/rea` có giá trị tham khảo và sử dụng trực tiếp cao hơn hẳn.

---

## Phần 3: Bản Đồ Chuyển Hóa Tri Thức Vào Kiến Trúc CCBA 4-Hubs × Federated Spokes

Đối chiếu với hệ thống **4-Hubs × Federated Spokes (`ADR-0060`)** trên máy chủ **NVIDIA DGX Spark Blackwell GB10** và giao thức **Level-2 Peer Delegation (`ADR-0063`, `ADR-0065`)**, dưới đây là 6 hạng mục chuyển hóa cụ thể:

| TT | Hạng mục Chuyển hóa | Nguồn Tham chiếu | Phân hệ CCBA Đích | Bài toán Giải quyết tại CCBA | Phân loại & Độ ưu tiên |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **1** | **Retained Evidence Pointer (`ev_<sha256>`) & Summary Paging** | `morluto/rea` (`src/domain/evidence.ts`) | `ccba-harness`, `ccba-qc-core`, `ccba-legal-intel` | Ngăn chặn tràn context 32k–98k của `qwen-local` trên DGX Spark và giảm 70–90% chi phí token khi truyền kết quả lớn giữa Antigravity $\leftrightarrow$ Grok CLI (`ADR-0063`). | **Mở rộng Seam hiện có — Ưu tiên P0** |
| **2** | **Zero-Dependency Stdlib Verification Scripts cho Tier 2 Skills** | `replica-skill` (`parity.py`, `reviews.py`, `contrast.py`) | `.agents/skills/ccba-*`, `bigbim-*` (`ADR-0057`, `ADR-0066`) | Giúp các Federated Spokes (`tta`, `tat`, `mtt`, laptop công trường) chạy được Gate 0 (`--fail-under`) bằng Python chuẩn mà không bị gãy do thiếu thư viện của Hub (`Issue #374`). | **Áp dụng cho Skills — Ưu tiên P0** |
| **3** | **Bottom-Up Call-Graph Context Propagation + Syntactic Normalizer** | `amruth-sn/kong` + Kahn's Fail-Closed Topo (`ADR-0065`) | `ccba-legal-intel` & `ccba-legal-knowledge` (Neo4j / VBHN) | Phân tích các điều khoản lá (không viện dẫn đi đâu) trước, chuẩn hóa cụm từ viện dẫn thành mã định danh tường minh trước khi đưa vào LLM phân tích điều khoản cha. | **Nâng cấp Pipeline — Ưu tiên P1** |
| **4** | **Obligation Ledger (`open` / `closed` / `unknown` + `residual_unknowns`)** | `morluto/rea` (`obligationLedger.ts`) | `ccba-qc-core` (`QCAuditPipeline`), `ccba-completion-checklist` | Cưỡng chế khóa trạng thái `unknown` khi thẩm tra thiết kế PCCC/MEP hoặc hồ sơ pháp lý nếu còn giả định chưa kiểm chứng, mở rộng nguyên tắc `COND-02` của `ADR-0065`. | **Chuẩn hóa Contract — Ưu tiên P1** |
| **5** | **Dual Schema Advertisement (`compact` vs `full` profile)** | `morluto/rea` (`docs/mcp-contracts.md`) | `ccba-ai` & FastMCP RAG Server trên DGX Spark (`:8090`) | Đảm bảo 1 bộ MCP/Tool definition chạy thông suốt trên cả 22 models của LiteLLM Gateway (không bị lỗi từ khóa JSON Schema trên Gemini, Qwen hay Claude). | **Triển khai mới — Ưu tiên P2** |
| **6** | **Offline HAR-to-Mock Environment (`rea environment-build`) & Cross-Session Diff** | `morluto/rea` & `unbrowse-ai/unbrowse` | `IDOP-CCBA-WAY` (SharePoint Bridge) & `TVPLCrawler` | Tạo môi trường giả lập SharePoint / TVPL từ file `.har` (đã qua `ccba-maskara`) để chạy CI test offline an toàn mà không bắn request thật lên Microsoft 365 Production. | **Sử dụng Tool / Pattern — Ưu tiên P2** |
