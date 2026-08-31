---
id: 221
title: "feat(legal-intel): establish automated legal sync pipeline and mock data isolation for spokes"
state: "needs-triage"
labels:

assignee: "none"
created_at: "2026-08-31T08:45:37Z"
updated_at: "2026-08-31T11:11:36Z"
---

# 📖 Mô tả (Description)
### 1. Bối cảnh & Vấn đề (Context & Problem):
- Tại Spoke \vc_working_space\, khi Agent thực hiện các tác vụ tư vấn pháp lý và xây dựng tài liệu dự án theo Luật Xây dựng năm 2025 (Luật số 135/2025/QH15) và các văn bản hướng dẫn mới, phát hiện:
  1. Spoke chưa có cơ chế đồng bộ tự động dữ liệu AST / OKF v2.2 của các văn bản quy phạm pháp luật mới nhất được phát hành từ Hub.
  2. Dữ liệu mock/test từ các script kiểm thử nền tảng (ví dụ: chuỗi demo NĐ 175 trong \demo_vbhn_delta_patch.py\) chưa được cô lập, dẫn tới tình trạng Agent quét trúng và hiểu nhầm là văn bản pháp luật hiện hành.
  3. \egistry.json\ chưa hỗ trợ đầy đủ các trường trạng thái hiệu lực động (\ACTIVE\, \SUPERSEDED\, \PARTIALLY_AMENDED\), khiến Agent khó nhận biết văn bản đã hết hiệu lực (như Luật 50/2014, NĐ 15/2021).

### 2. Đề xuất giải pháp (RFC Proposal):
- **Cơ chế Phân phối & Đồng bộ 1-Lệnh (\One-Click Sync CLI\)**: Bổ sung lệnh CLI \python -m ccba_legal sync --pull-latest\ (hoặc tích hợp vào \sync_spoke.py\) để Spoke tự động cập nhật kho dữ liệu OKF v2.2 chuẩn từ Hub/Cloud Vault.
- **Cách ly dữ liệu Mock/Test (\Mock Data Isolation Guard\)**: Di chuyển toàn bộ dữ liệu mock trong demo/unit tests vào thư mục \	ests/fixtures/\ có gắn namespace riêng biệt.
- **Nâng cấp Schema \egistry.json\**: Bổ sung các trường \status\, \^[ffective_date\, \supersedes\, \guiding_decrees\ và tích hợp cảnh báo khi tra cứu văn bản cũ.
- **High-level Python API**: Cung cấp hàm tra cứu trực tiếp trong \ccba_legal\ (ví dụ: \legal.query()\, \legal.get_lifecycle()\) phục vụ các Spoke.

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [ ] Bổ sung module \ccba_legal.sync\ hỗ trợ đồng bộ dữ liệu OKF v2.2 về Spoke.
- [ ] Cập nhật \egistry.json\ với trường trạng thái hiệu lực động cho Luật 135/2025/QH15, Luật 55/2024/QH15, NĐ 105/2025/NĐ-CP và các văn bản mới.
- [ ] Di chuyển toàn bộ mock data ra khỏi thư mục thực thi/scripts sang \	ests/fixtures/\.
- [ ] Viết unit tests kiểm thử cơ chế sync và kiểm định visual parity.

---
*Được đề xuất tự động từ Spoke \vc_working_space\ qua workflow \/ccba-issue-to-hub\.*

---

# 💬 Thảo luận (Discussion Log)
*(Chưa có thảo luận)*
