# Walkthrough: Hoàn Tất Chính Thức Hóa ADR-0059 & Nạp Bundle Địa Phương Vào Spoke `ccba-legal-knowledge`

## 1. Tổng Quan Nhiệm Vụ Hoàn Thành

Đã thực hiện trọn vẹn 2 nhiệm vụ tiếp theo theo phê duyệt của người dùng:
1. **Chính thức hóa HUB-ADR-0059 trên Hub (`ccba-agent-platform`):**
   - Soạn thảo tài liệu kiến trúc chính thức [`docs/adr/0059-legal-verbatim-grounding-and-mandatory-acquisition-invariant.md`](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0059-legal-verbatim-grounding-and-mandatory-acquisition-invariant.md).
   - Tái biên dịch mục lục [`docs/adr/README.md`](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/README.md) và quét radar cập nhật ma trận truy vết [`docs/adr/TRACEABILITY_MATRIX.md`](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/TRACEABILITY_MATRIX.md) (53 ADRs, đạt 100% parity `[PASS]`).
2. **Đồng bộ Hub sang Spoke & Nạp Bundle Thực Tế vào `ccba-legal-knowledge`:**
   - Đồng bộ Hiến pháp Layer 1, rules, và ADR matrix sang Spoke [`ccba-legal-knowledge`](file:///D:/GitHubProjects/ccba-legal-knowledge).
   - Nạp bundle thực tế **Quyết định 38/2026/QĐ-UBND của UBND TP. Hà Nội** (về phân cấp quản lý quy hoạch đô thị, nông thôn và kiến trúc) vào `legal_docs/01_vbpl/vn_hn_qd_38_2026_qd_ubnd/`.
   - Vượt qua kiểm định **15 Gates** của Spoke với kết quả tuyệt đối: **0 Errors | 0 Warnings**.

---

## 2. Chi Tiết Thực Hiện Trên Hub (`ccba-agent-platform`)

### A. Quyết định kiến trúc HUB-ADR-0059
- **Tiêu đề:** *Legal Verbatim Grounding, Zero-Hallucination Invariant, and Cryptographic Provenance Stamping*
- **Trạng thái:** `ACCEPTED & ADOPTED` (2026-09-16)
- **Nội dung cốt lõi:**
  1. **Zero-Hallucination Invariant:** Cấm tuyệt đối sáng tác câu chữ, điều khoản giả định cho VBPL. Mọi nội dung trích dẫn phải nguyên văn 100% từ văn bản chính thức.
  2. **Mandatory Acquisition First Policy:** Bắt buộc thu thập tệp gốc (PDF/DOCX) qua `TVPLCrawler` hoặc yêu cầu người dùng cung cấp tài liệu nguồn chính thức trước khi tạo bundle.
  3. **Cryptographic Provenance Stamping:** Đóng dấu mã băm SHA-256 (`pdf_sha256`) và tự động kiểm định nguồn gốc xuất xứ qua `validate_bundle_provenance()`.
  4. **Temporal Local Jurisdictions:** Phân định lãnh thổ theo chuẩn ISO 3166-2:VN (`VN-HN`, `VN-HCM`...), mô hình hóa đồ thị kế thừa cơ quan pháp lý theo trục thời gian và kích hoạt RAG Geofencing.

### B. Kiểm chuẩn Parity Gate
```powershell
python scripts/sync_hub_adr_matrix.py --check
```
- **Kết quả:**
  ```
  [sync_hub_adr_matrix] Running in HUB mode (53 ADRs found)
  [PASS] D:\GitHubProjects\ccba-agent-platform\docs\adr\README.md is in sync.
  [PASS] D:\GitHubProjects\ccba-agent-platform\docs\adr\TRACEABILITY_MATRIX.md is in sync.
  ```

---

## 3. Chi Tiết Thực Hiện Trên Spoke (`ccba-legal-knowledge`)

### A. Đồng bộ cấu trúc & Two-Tier ADR Matrix
- Đồng bộ các quy tắc mới nhất:
  - `.agents/rules/legal_verbatim_grounding_guardrail.md`
  - `.agents/rules/administrative_succession_guardrail.md`
  - `AGENTS.md` (Hiến pháp Layer 1)
- Tái đồng bộ ma trận truy vết Two-Tier tại Spoke (53 Hub ADRs + 42 Spoke Domain ADRs).

### B. Đăng ký & Nạp Bundle QĐ 38/2026/QĐ-UBND Hà Nội
- **Đăng ký SSoT:** Cập nhật [`legal_registry.yaml`](file:///D:/GitHubProjects/ccba-legal-knowledge/legal_registry.yaml) với mục `vn_hn_qd_38_2026_qd_ubnd`, nâng tổng số VBPL lên **25** (tổng tài liệu: **53**).
- **Thư mục bundle:** [`legal_docs/01_vbpl/vn_hn_qd_38_2026_qd_ubnd/`](file:///D:/GitHubProjects/ccba-legal-knowledge/legal_docs/01_vbpl/vn_hn_qd_38_2026_qd_ubnd)
  - `sources/702686.pdf`: Tệp scan gốc 14 trang có dấu đỏ (4.67 MB, SHA-256: `d826eaf192b238acd1b465854babc8a884d8e12e2d330ecc4c262ed64eb8767b`).
  - `metadata.yaml`: Cấu hình chuẩn OKF v2.4 Universal, khai báo đầy đủ `source_assets`, `jurisdiction: VN-HN`, `administrative_tier: PROVINCIAL`.
  - `clauses.json`: Cấu trúc AST phân đoạn 20 Điều theo chuẩn máy đọc.
  - `vn_hn_qd_38_2026_qd_ubnd.md`: Toàn văn 100% nguyên văn, đã chuẩn hóa theo chuẩn **Pure Normative Body** (loại bỏ nhiễu tiêu ngữ hành chính và chữ ký nơi nhận, giữ nguyên văn toàn bộ 4 Chương, 20 Điều).

### C. Kiểm định 15 Gates Chất Lượng Pháp Điển
Chạy kiểm định toàn diện trên Spoke:
```powershell
python D:\GitHubProjects\ccba-legal-knowledge\scripts\validate_legal_spoke.py
```
- **Kết quả:**
  ```
  -> Gate 1: Registry Check completed.
  -> Gate 2: OKF Bundles Structure Check completed.
  -> Gate 3: Table Attachments Check completed.
  -> Gate 4: Fake Data Gate Check completed.
  -> Gate 5: PDF Metadata & AST Jurisdiction Gate Check completed.
  -> Gate 6: Pure Normative Body & Scoped Noise Gate Check completed.
  -> Gate 7: Spoke Cleanliness & Zero-Wrapper Gate completed.
  -> Gate 8: Template & Table Structural Integrity Gate completed.
  -> Gate 9: Visual Parity & Formatting Clutter Gate completed.
  -> Gate 10: ADR Living Traceability & Self-Healing Sync completed.
  -> Gate 11: DOCX-to-Markdown Verbatim Normative Parity Gate completed.
  -> Gate 12: Multimodal Decoupled Asset & SVG/Cards Integrity Gate (ADR 0040) completed.
  -> Gate 13: Table Knowledge Extraction & 2D Matrix Regularity Gate (ADR 0041) completed.
  -> Gate 14: KaTeX Math Syntax & Rendering Integrity Gate (ADR 0038) completed.
  -> Gate 15: OKF Provenance & Algorithm Version Attestation Gate completed.

  -----------------------------------------------------------------
  SUMMARY REPORT: Errors: 0 | Warnings: 0
  -----------------------------------------------------------------

  ✅ PASSED: All legal knowledge gates validated successfully!
  ```

---

## 4. Trạng Thái Git Kho Chứa

- **Hub (`ccba-agent-platform`):**
  - Commit `50b59f7b`: `docs(adr): formalize HUB-ADR-0059 and update traceability matrix`
  - Commit `bf2a6a69`: `chore(sync): update spoke registry heartbeat for ccba-legal-knowledge`
  - Nhánh `main` đồng bộ với `origin/main`, working tree sạch 100%.
- **Spoke (`ccba-legal-knowledge`):**
  - Commit `17cdddc`: `feat(legal): ingest QĐ 38/2026/QĐ-UBND Hà Nội bundle and sync Hub ADR-0059`
  - Đã vượt qua pre-commit hook 15 Gates, working tree sạch 100%.
