# ⚙️ Progressive Reference: Pha 2A — Điều Phối Hàng Chờ & Async Batcher

> Thuộc Master Skill [`ccba-ai-qc`](../SKILL.md).

Module này quản lý hàng chờ tác vụ (Task Queue), điều phối song song các cuộc gọi AI Vision để kiểm tra xung đột đa bộ môn (Kiến trúc, Kết cấu, MEP, PCCC) theo cơ chế Quad-View dựa trên ma trận phối hợp `Coordination_Matrix.csv`.

---

## 1. Kiến Trúc Hoạt Động (Internal Logic)

1. **Parser Module:** Phân tích cột `NormalizedLevel` và danh sách các tệp tin bản vẽ tương ứng trong `Coordination_Matrix.csv`.
2. **Missing Document Handler (Blank Fallback):** Nếu một cấu kiện bị thiếu sheet, hoặc không tìm thấy trang thực tế thì tự động sinh ra một khung ảnh trắng `blank.png` làm fallback để tránh ngắt quãng pipeline.
3. **Async Batcher:** Quản lý hàng chờ tác vụ (Task Queue), thực thi song song các cuộc gọi Quad-View (L01, L02...) lên AI Gateway với `concurrency` kiểm soát.
4. **Integration Handoff:** Chuyển kết quả phân tích JSON về cho Reporter Engine để biên soạn thành báo cáo Markdown/Docx hoàn chỉnh.

---

## 2. Lệnh Chạy Độc Lập

```powershell
python .agents/skills/ccba-ai-qc/scripts/orchestrator.py --project-dir "[project_dir]" --matrix ".md/extracts/discovery/Coordination_Matrix.csv" --concurrency 4
```
