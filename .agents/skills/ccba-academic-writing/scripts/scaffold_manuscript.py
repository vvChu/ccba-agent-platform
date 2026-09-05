#!/usr/bin/env python3
"""scaffold_manuscript.py - Generates a blank academic research paper template in Markdown.

Usage: python scaffold_manuscript.py <output_file.md>
"""

import sys
import os
from pathlib import Path

TEMPLATE_CONTENT = """---
title: "Enter Your Research Paper Title Here"
authors:
  - name: "Author 1 Name"
    affiliation: "CCBA - Institute of Construction BIM, Vietnam"
    email: "author1@ccba.vn"
    corresponding: true
  - name: "Author 2 Name"
    affiliation: "Department of Construction IT, Vietnam"
---

# Abstract
<!-- 
Tóm tắt ngắn gọn bài báo khoa học (150 - 250 từ):
- Đặt vấn đề và mục tiêu nghiên cứu.
- Phương pháp chính được sử dụng.
- Kết quả nổi bật và đóng góp lớn nhất của nghiên cứu.
-->
Write a concise summary of your research, methodologies, and key findings here.

# Introduction
<!-- 
Chương Mở đầu - Cần tuân thủ mô hình CARS (3 Moves):
1. Bối cảnh nghiên cứu: Nêu tính cấp thiết, vai trò của chủ đề.
   *Từ khóa gợi ý: play a key role, recent advances in, has been widely studied*
2. Khoảng trống nghiên cứu: Chỉ ra lỗ hổng tri thức, giới hạn của giải pháp hiện có.
   *Từ khóa gợi ý: however, remains unclear, is limited, little research*
3. Giải pháp đề xuất: Tuyên bố giải pháp của bạn, tính mới và cấu trúc bài báo.
   *Từ khóa gợi ý: in this paper, we propose, this study aims to*
-->

### 1.1. Bối cảnh nghiên cứu
Enter research territory details here...

### 1.2. Khoảng trống nghiên cứu
Highlight the niche/gap in current literature here...

### 1.3. Giải pháp đề xuất
Introduce your proposed solution and paper outline here...

# Materials and Methods
<!-- 
Phương pháp nghiên cứu:
- Sử dụng chủ yếu Thể bị động (Passive Voice) để duy trì tính khách quan.
- Mô tả chi tiết dữ liệu (BIM models, IFC files, dataset size) và các bước xử lý.
- Công thức toán học có thể biểu diễn bằng LaTeX:
  Ví dụ phương trình nội văn: \\(E = mc^2\\)
  Ví dụ phương trình khối:
  \\[S = \\frac{\\sum_{i=1}^n x_i}{n}\\]
- Sơ đồ quy trình hệ thống có thể viết dưới dạng khối Mermaid:
  ```mermaid
  graph TD
      A[Data Collection] --> B[Spell Checking]
      B --> C[BERT Classification]
  ```
-->
Describe your experimental setup, materials, dataset, and methodology here.

# Results
<!-- 
Kết quả nghiên cứu:
- Liệt kê kết quả khách quan, không lồng ghép nhận định chủ quan.
- Trích dẫn hình vẽ hoặc bảng biểu đầy đủ: 'As illustrated in Figure 1...'
- Tham chiếu tới bảng số liệu: 'Table 2 summarizes the performance...'
-->
Present your objective data, graphs, tables, and accuracy metrics here.

# Discussion
<!-- 
Thảo luận - Trọng tâm khẳng định thẩm quyền (Authority):
- Sử dụng Thể chủ động (Active Voice) kết hợp ngôi thứ nhất 'We found', 'Our findings indicate'.
- Cấu trúc phản chiếu (Zoom-out):
  Move 1: Khẳng định kết quả cốt lõi (Major Findings) và các cách giải thích khác.
  Move 2: So sánh, đối chiếu với các công trình nghiên cứu cũ (Research Context).
  Move 3: Thừa nhận giới hạn nghiên cứu (Limitations) và đề xuất định hướng tương lai.
-->
Interpret your results, compare with previous works, state limitations, and propose future research.

# References
<!-- 
Tài liệu tham khảo:
- Liệt kê tài liệu theo thứ tự số hiệu trích dẫn [1], [2] xuất hiện trong bài viết.
- Đảm bảo mọi trích dẫn trong văn bản đều có nguồn khai báo tương ứng tại đây.
-->
[1] Author, A. (Year). Title of the book or article. Journal Name, Volume(Issue), Pages.
[2] Author, B. (Year). Title of the book or article. Journal Name, Volume(Issue), Pages.
"""


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
        
    if len(sys.argv) < 2:
        print("Usage: python scaffold_manuscript.py <output_file.md>")
        sys.exit(1)
        
    output_path = Path(sys.argv[1])
    if output_path.exists():
        print(f"Error: Target file '{output_path}' already exists. Operation aborted to prevent overwriting.")
        sys.exit(1)
        
    try:
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Write template
        output_path.write_text(TEMPLATE_CONTENT.strip() + "\n", encoding="utf-8")
        print(f"Successfully generated manuscript skeleton at: {output_path.absolute()}")
    except Exception as e:
        print(f"Error writing template: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
