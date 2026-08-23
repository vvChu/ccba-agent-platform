# 🎫 Ticket WF-02: [AFK / Research] Ma trận Cấp phát Quota & Routing Rule cho AI Gateway Server Spark

> **Thuộc bản đồ**: [🗺️ Bản đồ Định hướng IDOP Hub-Spoke Ecosystem](../idop_spoke_ecosystem_map.md)  
> **Loại ticket**: `AFK / Research`  
> **Trạng thái**: `CLOSED` (Đã hoàn thành)  
> **Tài liệu nghiên cứu chi tiết**: [ai_gateway_quota_matrix_and_routing_architecture.md](../../knowledge/research_and_studies/ai_gateway_quota_matrix_and_routing_architecture.md)  
> **Assignee**: *AI Platform Engineering*

---

## 1. Bối cảnh & Mục tiêu

AI Gateway trên Server Spark (`100.83.192.30:8090/v1`) là cổng kết nối duy nhất cho toàn bộ hệ sinh thái CCBA:
- Tích hợp 22 models bao gồm:
  - Local GPU models: `qwen-local-primary` (Qwen 35B FP8 - chạy trên GPU của Spark Server), `reasoning-gemma`, v.v.
  - Cloud Frontier models: Gemini 3.7 / 2.5 Pro & Flash, Claude Sonnet 4.6, Claude Haiku 4.5.
- Mạng lưới truy cập: Kết nối bảo mật qua Tailscale VPN.

---

## 2. Kết Quả Nghiên Cứu Đạt Được

1. **Ma Trận Cấp Phát 3 Tầng**:
   - **Tier 1 (Personal Sandbox)**: Không giới hạn Local GPU; Capped \$5/tháng Cloud (~50k tokens/ngày); Tự động giáng cấp (Graceful Fallback) về Qwen 35B khi cạn quota Cloud.
   - **Tier 2 (Project Delivery & Governance)**: Phân bổ theo Hợp đồng (\$50-\$200/dự án); Cấp quyền Multimodal Vision Quad-view PCCC.
   - **Tier 3 (Platform Hub & Nightly Daemon)**: Dynamic Pool \$10/đêm, ưu tiên chạy 00:00-05:00 kết hợp Circuit Breaker.
2. **Khuyến Nghị Cấu Hình LiteLLM (`config.yaml`)**:
   - Đã biên soạn đầy đủ đặc tả `config.yaml` gồm `router_settings`, `fallbacks`, `model_list` và `team_list` tại [ai_gateway_quota_matrix_and_routing_architecture.md](../../knowledge/research_and_studies/ai_gateway_quota_matrix_and_routing_architecture.md).

---

## 3. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Lập bảng ma trận phân quyền 3 Tier kèm routing fallback logic.
- [x] Soạn thảo bản tóm tắt khuyến nghị cấu hình LiteLLM.
- [x] Cập nhật kết quả vào mục *Decisions so far* trên Bản đồ Wayfinder.

