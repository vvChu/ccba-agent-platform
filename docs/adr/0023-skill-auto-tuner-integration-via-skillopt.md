# ADR 0023: Tích hợp CCBA Skill Auto-Tuner dựa trên phương pháp Microsoft SkillOpt

## Bối cảnh (Context)
Trong quá trình nghiên cứu repository `microsoft/SkillOpt`, hệ thống CCBA Agent Services Platform nhận thấy cơ hội tối ưu hóa tự động chất lượng của các tệp `SKILL.md` (hướng dẫn kỹ năng bằng ngôn ngữ tự nhiên cho Agent). SkillOpt coi các câu lệnh prompt trong `SKILL.md` như những "tham số có thể huấn luyện" (trainable parameters) thông qua chu trình 4 bước: **Rollout -> Reflect -> Edit -> Validate**.

Phiên chất vấn Socrates (Grilling with Docs) đã thảo luận và chốt các quyết định kiến trúc cốt lõi để thích ứng SkillOpt vào CCBA Platform.

## Quyết định (Decisions)

### 1. Phạm vi ứng dụng: Tập trung xây dựng CCBA Skill Auto-Tuner
* **Quyết định**: Ưu tiên xây dựng module **Skill Auto-Tuner** tích hợp trực tiếp vào quy trình kiểm định kỹ năng hiện có (`/ccba-skills-eval` và `/ccba-review-skill`), thay vì tập trung vào tối ưu đa mô hình (Multi-Model Adaptation) trên AI Gateway.
* **Lý do**: CCBA đã có hạ tầng kiểm định `writing-great-skills` và `/ccba-skills-eval`. Việc auto-tune trực tiếp các `SKILL.md` chuyên môn (PCCC, RASE, Legal, Copywriting) mang lại giá trị gia tăng tức thì cho chất lượng thực thi dự án.

### 2. Chiến lược Benchmark Hỗn hợp (Hybrid Benchmark Strategy)
* **Quyết định**: Sử dụng mô hình **Hybrid Benchmark**:
  * **Rollout Stage**: Sử dụng **Synthetic Tasks** (sinh tự động các tình huống edge-cases đa dạng bằng AI Gateway) giúp Agent va chạm liên tục với các kịch bản mới trong lúc điều chỉnh prompt.
  * **Validation Gate**: Bắt buộc sử dụng **Real Benchmark Logs** (các bài toán/hồ sơ thực tế đã qua kiểm định thủ công trong `.md/knowledge/` và `.md/extracted_docs/`) để đánh giá bản prompt đề xuất, chống hiện tượng **Prompt Drift** (suy giảm chất lượng ở các tác vụ thực địa).

### 3. Giao diện điều khiển (CLI Seam): Mở rộng `/ccba-skills-eval` bằng cờ `--auto-tune`
* **Quyết định**: Tái sử dụng workflow `/ccba-skills-eval` hiện có và mở rộng bằng cờ `--auto-tune` (e.g., `/ccba-skills-eval --skill <name> --auto-tune`), không tạo workflow mới để tuân thủ triệt để nguyên tắc **KISS** và **Reuse-First Gate** của `AGENTS.md`.

## Hệ quả (Consequences)
* Bổ sung các thuật ngữ mới (`Skill Auto-Tuner`, `Validation Gate`, `Prompt Drift`) vào `CONTEXT.md`.
* Chuẩn bị lộ trình mở rộng cho workflow `/ccba-skills-eval` để hỗ trợ cờ `--auto-tune` chạy ngầm.
* Bảo đảm tính an toàn khi cập nhật prompt: không có thay đổi prompt nào được phép commit lên Hub nếu chưa vượt qua Validation Gate trên tập Real Benchmark.

