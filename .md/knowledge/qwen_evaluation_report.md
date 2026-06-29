# Báo cáo Đánh giá Model `qwen-local-primary`

Dựa trên các bài benchmark thông qua thư viện `ccba-ai` kết nối tới AI Gateway Server (`http://100.83.192.30:8090/v1`), dưới đây là báo cáo đánh giá chi tiết về hiệu năng, tính năng và cách khai thác tối ưu nhất cho model `qwen-local-primary`.

---

## 1. Hiệu năng (Performance Metrics)

Model mang lại thông số hiệu năng rất ấn tượng đối với một model chạy local (tương đương tốc độ của nhiều cloud APIs hàng đầu):

*   **Thời gian bắt đầu luồng (TTFT - Time To First Token):** `~0.114 giây`. 
    *   Model phản hồi và bắt đầu trả token gần như ngay lập tức. Đây là yếu tố cực kỳ tốt để xây dựng ứng dụng thời gian thực có sử dụng tính năng Streaming.
*   **Tốc độ sinh text (Generation Speed):** `~45.24 tokens/giây`.
    *   Tốc độ này thừa sức đáp ứng các pipeline xử lý luồng lớn của CCBA (như đọc hiểu bản vẽ, trích xuất CV) một cách mượt mà và không gây thắt cổ chai.
*   **Redis Caching tích hợp:** AI Gateway có bật cache tĩnh. Với các prompt trùng lặp hoàn toàn, kết quả trả về trong `~0.01s` (hơn 600,000 tokens/s). Để test hiệu năng thực sự, prompt luôn cần gắn thêm UUID/Timestamp (Nonce).

---

## 2. Tính năng Cốt lõi (Core Capabilities)

### 2.1. Natively Chain-of-Thought (Cơ chế Suy luận ẩn)
*   **Mô tả:** Giống như OpenAI `o1` hay `DeepSeek-R1`, `qwen-local-primary` là một "Reasoning Model". Nó tự động sinh ra một quá trình suy nghĩ, kiểm tra ràng buộc, và lên dàn ý trước khi đưa ra kết quả. Toàn bộ phần nháp này được model bọc trong khối `<think> ... </think>`.
*   **Tác dụng:** 
    *   Tự phân tích prompt của người dùng.
    *   Tự đếm số chữ, số câu, định dạng văn bản (Ví dụ: khi bị ép ràng buộc "dưới 3 câu", model đã chủ động đếm nháp và rút gọn câu từ trong thẻ `<think>`).
    *   Giảm thiểu đáng kể tình trạng "ảo giác" (hallucination) trong các suy luận logic.

### 2.2. Khả năng tuân thủ System Prompt & Ràng buộc cực tốt
*   Model làm theo **rất nghiêm ngặt** các yêu cầu được đưa vào `system_prompt`.
*   Nó không bị "bỏ quên" các yêu cầu ẩn như format file, ngôn ngữ hay đóng vai (Persona) do nó đã rà soát lại toàn bộ quy tắc trong thẻ `<think>` trước khi đưa ra câu trả lời thực tế.

### 2.3. Ngữ điệu & Ngôn ngữ Tiếng Việt xuất sắc
*   Quá trình `<think>` của model là sự kết hợp phân tích bằng Tiếng Anh và Tiếng Việt, nhưng câu trả lời đầu ra (final output) luôn được tinh chỉnh với văn phong Tiếng Việt chuẩn mực, mượt mà và đúng ngữ cảnh chuyên ngành.

---

## 3. Khuyến nghị Cách Khai thác Hiệu quả (Best Practices)

Để khai thác model này trên CCBA Agent Platform, đặc biệt là trong các Pipeline Tự động, bạn nên áp dụng các cấu trúc sau:

### 💡 1. Xử lý triệt để thẻ `<think>` (Parse Output)
Vì model luôn luôn in ra thẻ `<think>`, nếu ứng dụng của bạn yêu cầu trả về chuẩn **JSON** hoặc định dạng cứng, hãy đảm bảo **lọc bỏ khối `<think>`** trước khi chạy JSON Parser.
```python
import re

# Ví dụ lọc bỏ thẻ <think> trong Python
clean_response = re.sub(r'<think>.*?</think>\n*', '', raw_response, flags=re.DOTALL).strip()
```

### 💡 2. Kích hoạt tính năng Streaming
*   Với thời gian đáp ứng token đầu tiên (`TTFT < 0.2s`), giao diện UI (nếu có) nên **bắt buộc dùng hàm `ai.stream()`**.
*   **UX Tối ưu:** Hãy hiển thị phần `<think>` cho user dưới dạng Text màu xám mờ (hoặc collapsible block kiểu "Thinking..."). Điều này giúp user không có cảm giác phải chờ đợi 15-20s, thay vào đó họ thấy AI đang làm việc liên tục.

### 💡 3. Tối ưu hóa Prompt Engineering
*   **Không cần:** Thêm câu lệnh `"Hãy suy nghĩ từng bước" (Think step by step)` vì việc này là thừa thãi; model mặc định đã tư duy theo chuỗi.
*   **Khuyến khích:** Nhồi nhét càng nhiều quy tắc/ràng buộc (constraints) khắt khe vào prompt càng tốt. Quá trình tư duy nội tại của nó sinh ra để rà soát những ràng buộc phức tạp này. 
*   **Zero-shot:** Model này hoạt động cực tốt với dạng Zero-shot (không cần nhiều ví dụ mẫu) nhờ khả năng phân tích độc lập bên trong khối `<think>`.

### 💡 4. Vượt qua Cache khi Benchmark/Testing
*   Nếu thực hiện gọi model trong vòng lặp thử nghiệm, hãy luôn chèn một ID, UUID hoặc chuỗi thời gian ngẫu nhiên vào cuối prompt để tránh AI Gateway chặn lại và trả về kết quả cache từ Redis.
