# Worldview: AI là Thực thể Cần Giới hạn Nhận thức (Cognitively Bounded AI)

## Nguồn gốc
- **Speaker:** Matt Pocock
- **Video:** New Skills! v1.1 brings /wayfinder, /research, /implement, /to-spec, /to-tickets
- **Ngày phân tích:** 2024-05-20

## Phân tích

| Mục | Nội dung |
|-----|----------|
| 📍 Hiện tượng | Diễn giả liên tục chia nhỏ quy trình làm việc của AI: đổi tên PRD thành Spec/Tickets để cụ thể hóa hành trình; tạo `Wayfinder` để bẻ gãy các task vượt quá "vùng thông minh" (smart zone) của AI; tách biệt việc tìm kiếm sự thật (facts) và ra quyết định (decisions); gỡ bỏ bước Refactor ra khỏi TDD để đưa vào Code Review; và dùng các thuật ngữ kinh điển của Martin Fowler để AI tự nhận diện "code smell". |
| 💡 Niềm tin ẩn | **1. AI có "vùng thông minh" (Smart Zone) hữu hạn:** AI không phải là phép thuật toàn năng. Nếu nhồi nhét quá nhiều bối cảnh hoặc bắt AI đa nhiệm (vừa implement vừa refactor, vừa hỏi vừa tự quyết định), năng lực tư duy của nó sẽ sụp đổ. <br><br>**2. Kỷ luật Kỹ thuật (SDLC) là rào chắn cho AI, không phải cho con người:** Các quy trình như Spec, Tickets, Code Review không bị AI thay thế, mà ngược lại, chúng chính là bộ khung bắt buộc để "neo" sự tập trung của AI, ngăn nó đi chệch hướng (hallucination).<br><br>**3. Thuật ngữ chuyên ngành là "Thần chú" (LLM Priors):** Không cần giải thích dài dòng cho AI. Việc dùng đúng các từ khóa kinh điển (như *primitive obsession, feature envy*) sẽ kích hoạt trực tiếp "tiềm thức" (dữ liệu huấn luyện khổng lồ) của LLM, mang lại hiệu quả cao hơn với chi phí (token) rẻ hơn.<br><br>**4. Con người là Người điều phối (Orchestrator), AI là Công cụ đơn nhiệm:** Sự tồn tại của "confirmation gate" (cổng xác nhận trước khi code) và việc AI không được hỏi nhiều câu cùng lúc cho thấy niềm tin cốt lõi: Con người phải nắm quyền kiểm soát nhịp độ và định hướng, AI chỉ nên thực thi từng bước nhỏ trong một không gian đã được rào sẵn. |
| ✅ Đúng khi | Xây dựng các dự án phần mềm thực tế, phức tạp; làm việc trong môi trường nhóm cần lưu vết quyết định (GitHub issues); sử dụng các LLM hiện tại vốn có giới hạn về Context Window và khả năng suy luận dài hạn (long-horizon reasoning). |
| ❌ Sai khi | Thực hiện các tác vụ sáng tạo tự do (brainstorming); viết các script ngắn dùng một lần (throwaway code); hoặc trong tương lai khi các mô hình AI đạt đến mức độ AGI có khả năng tự duy trì bối cảnh và tự sửa sai hoàn hảo mà không bị tràn bộ nhớ nhận thức. |
| 🎯 Áp dụng cho Minh | **1. Ngừng viết Prompt "Tất cả trong một":** Thay vì yêu cầu AI "Hãy code cho tôi tính năng X", hãy thiết kế quy trình: Phân tích -> Viết Spec -> Chia Ticket -> Code từng Ticket -> Review. <br>**2. Tận dụng "Priors":** Khi muốn AI làm gì đó, hãy tìm xem trong ngành có thuật ngữ/sách kinh điển nào định nghĩa việc đó không, và ném từ khóa đó vào prompt thay vì tự mô tả bằng lời lẽ thông thường. <br>**3. Bảo vệ "Smart Zone":** Luôn tự hỏi: "Task này có đang bắt AI phải suy nghĩ quá nhiều hướng cùng lúc không?". Nếu có, hãy chặt đôi nó ra. |

## Vault Check
- **Trạng thái:** 🟢 Củng cố
- **KI liên quan:** Agentic Workflows, LLM Priors, Context Window Management, Software Development Life Cycle (SDLC), Prompt Engineering vs Prompt Orchestration.
- **Ghi chú đối chiếu:** Góc nhìn này củng cố mạnh mẽ triết lý "Agentic Design Patterns" của Andrew Ng. Nó đánh dấu sự chuyển dịch từ kỷ nguyên "Zero-shot prompting" (hy vọng AI làm đúng ngay từ đầu) sang kỷ nguyên "Cognitive Architecture" (xây dựng kiến trúc nhận thức và quy trình làm việc để bọc lót cho những điểm yếu của AI).

## Ghi chú cá nhân
(User thêm sau khi internalize)