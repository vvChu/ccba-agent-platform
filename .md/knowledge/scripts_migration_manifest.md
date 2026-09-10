# 📦 Báo Cáo Khảo Sát & Ma Trận Ánh Xạ Di Trú Scripts (Ticket 3 Manifest)

> **Cơ chế thực hiện**: Double-Pass Adversarial Review (Rule 8) — Đo lường thực tế trên mã nguồn Monorepo.  
> **Tham chiếu**: [Wayfinder Upgrade Map](../wayfinder/ccba-upgrade-roadmap/map.md) | [ADR-0057: Two-Stage Granularity Framework](../knowledge/adr/adr-0057.md)

---

## 1. Kết Quả Đo Lường Thực Tế `[đo thực tế]`

Qua đợt quét toàn diện thư mục `.agents/skills/*/scripts/` trong toàn bộ 67 kỹ năng hiện có:
- **Số skill có chứa thư mục `scripts/`**: **11 skills** (56 skills còn lại tuân thủ chuẩn Declarative, chỉ chứa `SKILL.md`, `references/`, `resources/` hoặc `templates/`).
- **Tổng số tệp script tồn tại**: **52 files** (gồm **48 tệp `.py`**, **3 tệp `.js`**, **1 tệp `.ps1`**) và bộ XML schemas.
- **Tổng dung lượng mã nguồn**: **9,909 LOC**.
- **Phân loại hiện trạng**:
  1. **17 files (~580 LOC)**: Đã là **Thin CLI Adapters** (chỉ làm nhiệm vụ nhận CLI args và delegate trực tiếp vào `packages/mdconverter`, `packages/ccba-ooxml`, `packages/ccba-pdf-prep`). Nhóm này đã tuân thủ Cổng 0 ADR-0057, không cần di chuyển code logic.
  2. **35 files (~9,329 LOC)**: Còn chứa **Core Logic trần** (thuật toán phân tích, bóc tách ảnh/PDF, gọi LLM, xử lý XML). Đây là đối tượng cần di trú vào các Monorepo Packages.

---

## 2. Thống Kê Chi Tiết 11 Skills Chứa Scripts

| STT | Tên Skill | Số tệp | Định dạng | Tổng LOC `[đo thực tế]` | Trạng thái hiện tại |
|:---:|:---|:---:|:---:|:---:|:---|
| 1 | `ccba-academic-writing` | 3 | `.py` | 107 | **Thin Adapter** (gọi `mdconverter`) |
| 2 | `ccba-ai-qc-pccc-audit` | 2 | `.py` (1), `.ps1` (1) | 254 | Core Logic (Map-Reduce PCCC) |
| 3 | `ccba-ai-qc` | 6 | `.py` | 1,534 | Core Logic (Discovery, Quad-view, Semantic, Reporter) |
| 4 | `ccba-copywriting` | 1 | `.py` | 245 | Core Logic (Style Extractor) |
| 5 | `ccba-design` | 9 | `.py` | 2,841 | Core Logic (CIP, Logo, Icon Generator & BM25 Search) |
| 6 | `ccba-eval-gate` | 1 | `.py` | 568 | Core Logic (Harness Eval Runner) |
| 7 | `ccba-markdown-document-processing` | 3 | `.py` | 101 | **Thin Adapter** (gọi `mdconverter.tables`) |
| 8 | `ccba-pptx` | 5 | `.py` (4), `.js` (1) | 1,131 | 4 file Python **đã là Thin Adapter** (`ccba_ooxml.pptx`); 1 file JS (`html2pptx.js`) |
| 9 | `ccba-web-testing` | 2 | `.js` | 515 | Tooling JS (Playwright Config & Test Analyzer) |
| 10 | `ccba-xu-ly-van-phong` | 17 | `.py` (+ XSD) | 2,511 | 6 file **đã là Thin Adapter**; còn lại là Validators, Helpers & PDF tools |
| 11 | `ccba-youtube-learn` | 3 | `.py` | 871 | 1 file Thin Adapter; 2 file Core Logic (`visual_extractor`, `watch_video`) |
| **Tổng** | **11 skills** | **52 files** | **48 py, 3 js, 1 ps1** | **9,909 LOC** | **17 Thin Adapters / 35 Core Logic files** |

---

## 3. Ma Trận Ánh Xạ Di Trú (Mapping Matrix)

| Nhóm Script Nguồn (Skill) | Các tệp cụ thể | Đích đến đề xuất trong `packages/` | Deep Seam / Namespace dự kiến | Lý do & Giải pháp kỹ thuật |
|:---|:---|:---|:---|:---|
| **`ccba-ai-qc` & `ccba-ai-qc-pccc-audit`** (1,788 LOC) | `discovery_engine.py`<br>`legacy_quadview_engine.py`<br>`semantic_audit_engine.py`<br>`orchestrator.py`<br>`reporter_engine.py`<br>`audit_engine.py` (pccc) | **ĐỀ XUẤT PACKAGE MỚI**: `packages/ccba-qc-core` | `ccba_qc_core.discovery`<br>`ccba_qc_core.quadview`<br>`ccba_qc_core.semantic`<br>`ccba_qc_core.orchestrator`<br>`ccba_qc_core.reporter`<br>`ccba_qc_core.pccc` | Nghiệp vụ Thẩm tra Thiết kế Đa bộ môn (BIM/CAD/PDF QC) là năng lực lõi độc lập, không nên trộn lẫn vào `ccba-ai` (làm phình SDK Gateway) hoặc `ccba-pdf-prep` (sai trách nhiệm). Xóa bỏ hoàn toàn hack `importlib.util`. |
| **`ccba-eval-gate`** (568 LOC) | `eval_runner.py` | `packages/ccba-harness` | `ccba_harness.evals.runner` | `eval_runner` là động cơ kiểm định kỹ năng, hoàn toàn tương thích với kiến trúc harness evaluation hiện tại của repo. |
| **`ccba-xu-ly-van-phong` (OOXML phần dư)** (~2,300 LOC) | `office/helpers/merge_runs.py`<br>`office/helpers/simplify_redlines.py`<br>`office/clone_text.py`<br>`office/validators/*` | `packages/ccba-ooxml` | `ccba_ooxml.docx.cleanup`<br>`ccba_ooxml.validation.*` | Hợp nhất trọn vẹn các module dọn dẹp XML run, gộp redline, và schema validator vào thư viện `ccba-ooxml` đã có sẵn. |
| **`ccba-xu-ly-van-phong` (PDF tools) & `ccba-ai-qc` (Vector)** (~180 LOC) | `process_pdf.py`<br>`convert_pdf_to_docx.py`<br>`pdf_vector_extractor.py` | `packages/ccba-pdf-prep` | `ccba_pdf_prep.manipulation`<br>`ccba_pdf_prep.vector_extractor` | Bổ sung tính năng merge/split PDF và trích xuất khối chữ vector vào gói `ccba-pdf-prep`. |
| **`ccba-youtube-learn` (Media Ingestion)** (824 LOC) | `visual_extractor.py`<br>`watch_video.py` | `packages/ccba-pdf-prep` | `ccba_pdf_prep.media.youtube`<br>`ccba_pdf_prep.media.orchestrator` | `packages/ccba-pdf-prep` hiện đã sở hữu module `media.py` (chứa `extract_youtube_video_id`, `fetch_youtube_transcript`). Mở rộng sang trích xuất visual slides là phù hợp. |
| **`ccba-copywriting` & `ccba-design` (LLM routing)** (~490 LOC) | `extract-writing-styles.py`<br>`llm_adapter.py` | `packages/ccba-ai` | `ccba_ai.style_extractor`<br>`ccba_ai.fallback_adapter` | Hợp nhất tiện ích phân tích văn phong và fallback LLM adapter nhiều tầng vào `ccba-ai` SDK. |
| **`ccba-design` (CIP / Logo / Icon)** (2,598 LOC) | `cip/*`<br>`logo/*`<br>`icon/*` | **Khuyến nghị KISS**: Tạm giữ làm Standalone Skill Tooling | `ccba-design/scripts/` | Nghiệp vụ sinh ấn phẩm đồ họa marketing/branding mang tính chất nội bộ, không thuộc luồng tư vấn kỹ thuật chính của AEC; tạm thời giữ nguyên để tránh phân tán nguồn lực. |
| **`ccba-web-testing` & `ccba-pptx` (Node.js)** (~1,500 LOC) | `analyze-test-results.js`<br>`init-playwright.js`<br>`html2pptx.js` | `packages/ccba-harness` (scripts/tools) | `packages/ccba-harness/tools/` | Các script JS phục vụ tooling kiểm thử và chuyển đổi trình duyệt, đặt tại thư mục công cụ phụ trợ của harness. |

---

## 4. Kế Hoạch Triển Khai Di Trú (Actionable Phases)

1. **Giai đoạn 1 (Quick Wins - Đóng gói vào packages hiện có)**:
   - Chuyển `eval_runner.py` $\rightarrow$ `packages/ccba-harness`
   - Chuyển OOXML helpers & validators $\rightarrow$ `packages/ccba-ooxml`
   - Chuyển PDF tools $\rightarrow$ `packages/ccba-pdf-prep`
2. **Giai đoạn 2 (Thành lập Package Nòng Cốt `packages/ccba-qc-core`)**:
   - Khởi tạo scaffolding `packages/ccba-qc-core` với Deep Seam `QCAuditPipeline`.
   - Di chuyển 6 files của `ccba-ai-qc` và 2 files của `ccba-ai-qc-pccc-audit`.
   - Viết fast unit test suite (< 2s) với mock response.
3. **Giai đoạn 3 (Chuyển đổi Skill thành Pure Thin Adapters)**:
   - Cập nhật lại các file trong `.agents/skills/*/scripts/` chỉ còn gọi CLI hoặc imports từ packages.
