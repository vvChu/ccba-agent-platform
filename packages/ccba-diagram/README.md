# CCBA Diagram (`ccba-diagram`)

Thư viện thuật toán bố cục sơ đồ tất định (8 Deterministic Layout Engines) và công thái học thị giác (Visual Ergonomics Standard v8.15.10) cho hệ sinh thái CCBA Agent Services Platform.

---

## 🌟 Tính Năng Cốt Lõi

1. **8 Layout Engines Tất Định:**
   - **`sugiyama`**: Phân tầng thứ bậc theo DAG (Hierarchical Layered).
   - **`wheel`**: Tâm Hub với vòng xuyến chu trình biên xoay chiều kim đồng hồ (Wheel / Star-Cycle).
   - **`matrix`**: Ma trận 4 góc phần tư 2x2 hoặc phân tán toạ độ (Axis/Cross).
   - **`tree`**: Cấu trúc cây Top-Down hoặc Left-to-Right.
   - **`radial`**: Bố cục toả tròn Hub-and-Spoke.
   - **`concentric`**: Vành đai đồng tâm đa tầng.
   - **`value_chain`**: Chuỗi giá trị / pipeline tuần tự ngang.
   - **`cycle`**: Vòng lặp phản hồi khép kín (Closed feedback loop).

2. **Router Điều Phối Bố Cục Thông Minh:**
   - Tự động nhận diện layout hint `#layout:<engine>` do LLM cung cấp.
   - Tự động phân tích cấu trúc đồ thị bằng NetworkX (cycle basis, degree distribution, tree detection) khi không có hint.

3. **Chuẩn Công Thái Học Thị Giác 16:9:**
   - Khóa chiều rộng $1.000\text{px} \le W \le 1.150\text{px}$ tối ưu hóa hiển thị báo cáo.
   - Cắt tỉa mũi tên chính xác theo biên ellipse/rectangle (`get_shape_boundary_point`), triệt tiêu đè khối hoặc ngược đầu mũi tên.
   - Tự động sinh **Bảng Đặc Tả Ma Trận Kiến Trúc Markdown** phân tầng 2 nhịp (`↳&nbsp;Text`) và escape pipe wikilinks.

---

## 🚀 Cài Đặt & Sử Dụng

```bash
# Cài đặt nội bộ trong Hub Monorepo
pip install -e packages/ccba-diagram
```

### Python API

```python
from ccba_diagram import apply_smart_layout, generate_markdown_spec_table

# 1. Tối ưu bố cục Excalidraw elements
elements = [...]  # Danh sách Excalidraw element dicts
apply_smart_layout(elements)

# 2. Sinh bảng đặc tả Markdown
spec_table = generate_markdown_spec_table(elements)
print(spec_table)
```

### CLI Command Line

```bash
# Tự động chọn engine và xuất file bố cục mới
ccba-diagram layout input.json -o output.json

# Ép buộc sử dụng layout cụ thể
ccba-diagram layout input.json -o output.json --engine wheel

# Xuất bảng đặc tả ma trận Markdown
ccba-diagram spec-table input.json
```
