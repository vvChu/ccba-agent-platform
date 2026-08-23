# 🎫 Ticket WF-02: [AFK / Research] Ma trận Cấp phát Quota & Routing Rule cho AI Gateway Server Spark

> **Thuộc bản đồ**: [🗺️ Bản đồ Định hướng IDOP Hub-Spoke Ecosystem](../idop_spoke_ecosystem_map.md)  
> **Loại ticket**: `AFK / Research`  
> **Trạng thái**: `OPEN` (Frontier)  
> **Assignee**: *Chưa gán*

---

## 1. Bối cảnh & Mục tiêu

AI Gateway trên Server Spark (`100.83.192.30:8090/v1`) là cổng kết nối duy nhất cho toàn bộ hệ sinh thái CCBA:
- Tích hợp 22 models bao gồm:
  - Local GPU models: `qwen-local-primary` (Qwen 3.5 35B FP8 - chạy trên GPU của Spark Server), `reasoning-gemma`, v.v.
  - Cloud Frontier models: Gemini 2.5 / 1.5 Pro, Claude Sonnet 3.5 / Opus, GPT-4o, DeepSeek R1/V3.
- Mạng lưới truy cập: Kết nối bảo mật qua Tailscale VPN.

Cần thiết kế ma trận phân quyền, phân bổ hạn mức (Rate Limiter / Token Bucket / Quota per User) và chính sách Virtual Keys để:
1. Cho phép Personal Sandbox Spokes sử dụng không giới hạn các model Local GPU.
2. Kiểm soát ngân sách cho các model Cloud cao cấp khi chạy thẩm tra chuyên sâu hoặc Auto-Tuner.

---

## 2. Nhiệm vụ Nghiên cứu

1. **Khảo sát cấu hình LiteLLM trên Server Spark**:
   - Xác định cơ chế Virtual Key và Team Quota trong LiteLLM.
   - Kiểm tra các Alias định tuyến hiện có (`ocr-primary`, `ocr-fallback`, `rag-core`, `qwen-local-primary`).
2. **Xây dựng Ma trận Phân quyền & Hạn mức (Tiered Quota Matrix)**:
   - *Tier Free/Dev (Personal Sandbox)*: Không giới hạn Local GPU, giới hạn 50k tokens/ngày cho Cloud models.
   - *Tier Project Delivery (Spoke Dự án)*: Đầy đủ quyền gọi Multimodal Vision (Quad-view PCCC QC) và Gemini 1.5 Pro cho hồ sơ lớn.
   - *Tier Hub Engineering / Auto-Tuner*: Cấp quyền batch processing qua API Circuit Breaker.
3. **Đóng gói tài liệu cấu hình**:
   - Xuất file khuyến nghị cấu hình LiteLLM `config.yaml` và hướng dẫn tích hợp vào `.env` của Kỹ sư.

---

## 3. Tiêu chí Hoàn thành (Completion Criteria)

- [ ] Lập bảng ma trận phân quyền 3 Tier kèm routing fallback logic.
- [ ] Soạn thảo bản tóm tắt khuyến nghị cấu hình LiteLLM.
- [ ] Cập nhật kết quả vào mục *Decisions so far* trên Bản đồ Wayfinder.
