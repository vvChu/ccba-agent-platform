---
request_id: "req-plan-skills-governance-001"
verdict: "APPROVE_PLAN"
confidence: 0.96
risk_score: 1.2
conditions:
  - id: "COND-01"
    description: "Chuẩn hóa tiêu chí phân định giữa bundle _core và _software bằng Invariant 'Platform Operations vs Application Domain', đảm bảo _core chỉ chứa các công cụ điều phối vòng lặp SDLC chung của nền tảng."
    blocking: true
  - id: "COND-02"
    description: "Bổ sung thuộc tính khai báo 'scope: hub | spoke | universal' vào metadata YAML của SKILL.md làm cơ chế chính tắc cho Linter, đặt comment '# ccba:allow-hub-only-command' ở vai trò thứ cấp cho các trường hợp đặc biệt."
    blocking: true
  - id: "COND-03"
    description: "Ban hành đề xuất dưới dạng ADR-0066 độc lập kế thừa ADR-0057, đồng thời cập nhật Living Traceability Matrix và đồng bộ chỉ dẫn vào docs/rules/code_quality.md."
    blocking: false
summary: "Kế hoạch phản ánh chính xác nguyên nhân gốc rễ của sự cố phân phối Slash Command, thiết lập cơ chế 3 trụ cột khoa học kết hợp chặt chẽ giữa định lượng kiến trúc, ma trận phân nhóm và chốt chặn tự động CI. Đề xuất được phê duyệt kèm các điều kiện hoàn thiện cơ chế khai báo metadata."
---

# Báo Cáo Thẩm Định & Phản Biện Đối Kháng: Khung Quản Trị & Ma Trận Phân Nhóm Kỹ Năng Hub

Kế hoạch giải quyết trọn vẹn bài toán cân bằng giữa kiểm soát phình kỹ năng (Anti-Bloat) và trải nghiệm lập trình viên trên Spoke (Developer Ergonomics). Việc gắn kết Cổng 0 (Seam-First), Cổng 1 (GPI) cùng Cây quyết định phân nhóm bundle mang lại tính hệ thống cao, giải quyết triệt để lỗi phân loại kỹ năng sai môi trường.

Dưới đây là các nhận định phản biện chuyên sâu theo 4 câu hỏi định hướng của Antigravity.

---

## 1. Tính Chặt Chẽ Kiến Trúc & Nguy Cơ Bẫy Ranh Giới Giữa `_core` và `_software`

Cơ chế 2 Cổng kết hợp ma trận phân phối bundle đáp ứng tốt tiêu chuẩn thiết kế kiến trúc phân tán Hub-Spoke. Tuy nhiên, ranh giới giữa `_core` và `_software` tiềm ẩn nguy cơ chồng lấn nếu thiếu tiêu chí định lượng bổ trợ.

### Rủi ro bẫy ranh giới (Boundary Trap)
- Mọi Spoke trong hệ sinh thái CCBA đều là workspace kỹ thuật có cấu trúc mã nguồn. Nếu định nghĩa `_software` theo cảm tính là "các việc liên quan đến viết code hoặc script", nhà phát triển dễ gán nhầm các kỹ năng vận hành vòng đời mã nguồn chung (như harness, verify patch, create verification skill, review PR) vào `_software`.
- Ngược lại, nếu nới lỏng `_core` để chứa mọi công cụ hỗ trợ code, `_core` sẽ nhanh chóng phình to. Khi đó, các dự án Spoke thuần nghiệp vụ (như Spoke Tư vấn Pháp điển hoặc Thẩm tra PCCC) sẽ bị tải về hàng loạt kỹ năng thừa, gây loãng gợi ý autocomplete trên thanh lệnh Slash Command.

### Giải pháp chuẩn hóa
Áp dụng **Nguyên Tắc Phân Định Vận Hành Nền Tảng (Platform Operations Invariant)**:
- **`bundle: _core` (Platform Lifecycle Operations)**: Dành riêng cho các kỹ năng điều phối vòng lặp phát triển chuẩn của Agent (SDLC Loop) có mặt ở mọi Spoke:
  - Đồng bộ và kiểm tra tính toàn vẹn Spoke (`ccba-update-spoke`, `sync-spoke`).
  - Thẩm định, tạo bằng chứng và xác thực mã nguồn (`ccba-create-verification-skill`, `verify-patch`).
  - Quy trình Git, PR và tương tác Agent-to-Agent (`git-commit`, `review-proposal`).
- **`bundle: _software` (Application Engineering Domain)**: Dành riêng cho kỹ năng nghiệp vụ lập trình ứng dụng chuyên sâu:
  - Tối ưu hóa mô hình AI và triển khai runtime (`ccba-vllm-manager`, `ccba-ai-gateway-sdk`).
  - Xử lý pipeline streaming, circuit breaker, batch architecture.
  - Các framework lập trình frontend/backend đặc thù.

Bảng đối chiếu phân nhóm chuẩn:

| Tiêu chí | `bundle: _core` | `bundle: _software` |
| :--- | :--- | :--- |
| **Phạm vi hiện diện** | 100% mọi Spoke bất kể `project_type` | Đồng bộ có chọn lọc khi Spoke có `project_type: software` |
| **Mục đích sử dụng** | Vận hành vòng lặp SDLC của Agent & Hub-Spoke sync | Nghiệp vụ kỹ thuật phần mềm và phát triển tính năng |
| **Trải nghiệm Slash Command** | Luôn hiển thị trên thanh gõ lệnh của mọi lập trình viên | Chỉ hiển thị trong các workspace phần mềm chuyên biệt |

---

## 2. Đánh Giá Quy Tắc Linter Mới & Xử Lý False Positive Cho Lệnh Quản Trị Hub

Quy tắc Linter cảnh báo khi phát hiện `user-invocable: true` + `command: /...` đi kèm `bundle: _governance` là chốt chặn bắt buộc để phòng ngừa lỗi tái diễn.

### Giải pháp xử lý False Positive
Các kỹ năng quản trị hệ thống của Hub (như `ccba-adr-lifecycle`, `ccba-review-proposal`) phục vụ trực tiếp các Maintainer tại Hub thông qua Slash Command. Nếu chỉ dựa vào comment bypass `# ccba:allow-hub-only-command`, mã nguồn sẽ phụ thuộc vào các chú thích đặc biệt thay vì cấu hình tường minh.

Thiết lập cơ chế kiểm định hai lớp:
1. **Lớp Khai Báo Chính Tắc (Declarative Metadata First)**:
   Bổ sung trường `scope` vào frontmatter của `SKILL.md`:
   ```yaml
   user-invocable: true
   command: "/ccba-adr-lifecycle"
   scope: "hub"        # Các giá trị hợp lệ: hub | spoke | universal
   bundle: "_governance"
   ```
   Linter kiểm tra logic: Khi `scope: hub`, việc gán `bundle: _governance` là hoàn toàn hợp lệ. Linter tự động bỏ qua mà không phát sinh cảnh báo.
2. **Lớp Miễn Trừ Cục Bộ (Fallback Annotation)**:
   Giữ chú thích `# ccba:allow-hub-only-command` cho các file catalog hoặc trường hợp ngoại lệ chuyển tiếp, đảm bảo tương thích ngược với các file hiện hữu.

---

## 3. Hình Thức Pháp Điển Hóa: Lựa Chọn ADR-0066 Độc Lập

Kế hoạch nên được ban hành dưới dạng **ADR-0066 (Skills Taxonomy & Multi-Environment Distribution Matrix)** độc lập, kế thừa ADR-0057.

### Căn cứ kiến trúc:
- **Bảo toàn lịch sử quyết định**: ADR-0057 tập trung giải quyết bài toán ngưỡng tiếp nhận kỹ năng độc lập thông qua Cổng 0 (Determinism) và Cổng 1 (GPI). Đây là quyết định đã đóng (Closed Decision).
- **Phân tách trách nhiệm kiến trúc**: Vấn đề phân phối bundle (`_core`, `_software`, `_governance`), cơ chế đồng bộ có điều kiện dựa trên `project_type` và tính công thái học Slash Command thuộc tầng phân phối đa môi trường Hub-Spoke. Việc ban hành ADR-0066 giúp tách bạch ranh giới giữa *đánh giá chất lượng kỹ năng* và *chiến lược phân phối kỹ năng*.
- **Chuẩn hóa hạ tầng quy tắc**: Sau khi thông qua ADR-0066, bổ sung các quy tắc thực thi tương ứng vào `docs/rules/code_quality.md` và cập nhật Living Traceability Matrix tại `docs/adr/README.md`.

---

## 4. Các Ràng Buộc Bổ Sung (Conditions for Success)

Để bảo đảm tính toàn vẹn khi đưa vào vận hành thực tế, đề xuất áp dụng 4 điều kiện ràng buộc sau:

1. **`COND-01` — Kiểm Soát Chỉ Số GPI Bằng CI Deterministic**:
   Cập nhật `scripts/validate_skills.py` để tính toán lại điểm GPI tự động từ các tham số `{s, k, a, p}` khai báo trong frontmatter, ngăn chặn việc nhập thủ công điểm tổng kết sai lệch với công thức:
   $$\mathbf{GPI} = 2.5S + 2.0K + 2.0A - 1.5P$$

2. **`COND-02` — Thông Báo Điều Hướng Cho Virtual Hub Fallback**:
   Khi một Spoke kích hoạt một kỹ năng thuộc `bundle: _governance` qua cơ chế Virtual Hub Fallback, runtime của Agent hiển thị thông báo trạng thái: kỹ năng được nạp từ Hub từ xa, giúp người dùng nắm rõ ngữ cảnh thực thi.

3. **`COND-03` — Bộ Test Suite Cho Linter Phân Phối Lệnh**:
   Bổ sung các ca kiểm thử đơn vị trong harness kiểm tra 3 trạng thái của Linter:
   - Lỗi: Kỹ năng có command, thuộc `_governance`, thiếu `scope: hub` và thiếu annotation bypass.
   - Hợp lệ: Kỹ năng có command, thuộc `_governance`, có khai báo `scope: hub`.
   - Hợp lệ: Kỹ năng có command, thuộc `_core` hoặc các bundle nghiệp vụ được phân phối tới Spoke.

4. **`COND-04` — Cơ Chế Tự Động Gợi Ý Bundle Trong CLI**:
   Tích hợp cây quyết định phân nhóm vào lệnh khởi tạo kỹ năng mới, hỗ trợ nhà phát triển chọn đúng bundle ngay từ bước scaffold ban đầu.

---

## 🎯 Kết Luận

Đề xuất đạt mức độ hoàn thiện cao, giải quyết thấu đáo khoảng trống giữa quy chuẩn lý thuyết và thực tiễn trải nghiệm của lập trình viên. Antigravity có thể tiến hành soạn thảo **ADR-0066** và triển khai các chốt chặn Linter theo các điều kiện đã thống nhất.
