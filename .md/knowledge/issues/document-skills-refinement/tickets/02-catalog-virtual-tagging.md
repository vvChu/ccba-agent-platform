# Ticket 2: [Bổ sung Phân loại Ảo Virtual Tag _document trong catalog.yaml](02-catalog-virtual-tagging.md)

* **Thuộc bản đồ**: [Document Skills Refinement Map](../map.md)
* **Loại tác vụ**: Research / Config [AFK]
* **Người thực hiện (Assignee)**: Unassigned
* **Trạng thái**: Open (Unblocked)

## 📋 Mục tiêu
Cập nhật tệp `.agents/skills/platform-loader/catalog.yaml` để bổ sung tag phân loại ảo `category: _document` hoặc `tags: [document, writing]`.

## 🔍 Chi tiết công việc
- Đọc `catalog.yaml` và rà soát entries của 9 skills xử lý văn bản.
- Chèn thêm thuộc tính `tags` hoặc nhóm phân loại ảo `category: _document` giúp các công cụ tìm kiếm và lọc skill tra cứu chính xác.
- Bảo đảm file `catalog.yaml` sau khi sửa vẫn pass qua linter `yaml.safe_load()`.

## 📌 Đầu ra mong muốn
Tệp `catalog.yaml` được cập nhật metadata tags sạch sẽ.
