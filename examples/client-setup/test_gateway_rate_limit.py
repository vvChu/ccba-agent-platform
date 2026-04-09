import concurrent.futures
import time
import os
import sys

# Đảm bảo ccba_ai có thể load được (trong trường hợp chạy từ thư mục khác)
from ccba_ai import ai

def worker(req_id: int) -> dict:
    """Gửi một request giả lập đến 'reasoning-gemma' để bóc tách siêu dữ liệu."""
    start_time = time.time()
    try:
        prompt = f"Trích xuất JSON metadata cho khối lượng công việc ID: TASK-{req_id:04d}. Chỉ trả về JSON hợp lệ."
        
        # Gọi qua AI Gateway sử dụng ccba-ai
        response = ai.chat(
            prompt,
            model="reasoning-gemma",
            system="Bạn là AI chuyên bóc tách dữ liệu có cấu trúc. Phản hồi định dạng JSON.",
            max_tokens=60,
            temperature=0.1
        )
        latency = time.time() - start_time
        
        # Truncate response để in cho gọn
        res_snippet = response.replace('\n', ' ')
        if len(res_snippet) > 40:
            res_snippet = res_snippet[:40] + "..."
            
        return {
            "id": req_id,
            "status": "success",
            "latency": latency,
            "response": res_snippet
        }
    except Exception as e:
        latency = time.time() - start_time
        return {
            "id": req_id,
            "status": "error",
            "latency": latency,
            "error": str(e)
        }

def main():
    # Fix unicode printing error on Windows powershell
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Tham số bài test (30-50 JSON requests)
    num_requests = 40
    max_workers = 20  # Gọi đồng thời 20 luồng để ép LiteLLM phải rải tải
    
    # Cảnh báo nếu chưa có env keys
    if not os.environ.get("AI_GATEWAY_KEY") and not os.environ.get("OPENAI_API_KEY"):
        print("⚠️ WRN: Chưa thấy biến môi trường 'AI_GATEWAY_KEY' hoặc 'OPENAI_API_KEY'. System sẽ dùng API Key mặc định nếu có trong .env", file=sys.stderr)

    print("=" * 60)
    print("🚀 BẮT ĐẦU STRESS-TEST AI GATEWAY (LITELLM LOAD BALANCING)")
    print(f"🎯 Model mục tiêu: reasoning-gemma (Alias)")
    print(f"📦 Tổng block    : {num_requests} requests")
    print(f"⚡ Số luồng đồng thời: {max_workers}")
    print("=" * 60)

    start_total = time.time()
    results = []
    
    # Sử dụng ThreadPoolExecutor để tạo request đồng thời
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_req = {executor.submit(worker, i): i for i in range(1, num_requests + 1)}
        
        for future in concurrent.futures.as_completed(future_to_req):
            req_id = future_to_req[future]
            try:
                res = future.result()
                results.append(res)
                if res["status"] == "success":
                    print(f"[Req {req_id:02d}] ✅ OK  | Latency: {res['latency']:^5.2f}s | {res['response']}")
                else:
                    print(f"[Req {req_id:02d}] ❌ ERR | Latency: {res['latency']:^5.2f}s | Lỗi: {res['error']}")
            except Exception as exc:
                print(f"[Req {req_id:02d}] 💥 LỖI QUẢN LÝ THREAD: {exc}")

    total_time = time.time() - start_total
    
    # Thống kê
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = len(results) - success_count
    
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ ĐÁNH GIÁ (SUMMARY)")
    print(f"⏱️ Tổng thời gian chạy: {total_time:.2f} giây")
    print(f"✅ Thành công       : {success_count}/{num_requests}")
    print(f"❌ Thất bại (Lỗi)   : {error_count}/{num_requests}")
    
    if success_count == num_requests:
        print("\n🎉 XUẤT SẮC: LiteLLM đã phân hồi rải đều tải thành công đè lên Rate-Limit 15 RPM!")
    else:
        print("\n⚠️ Cảnh báo: Tồn tại request lỗi. Hãy kiểm tra LiteLLM log để xem bị rớt tại Key nào.")

if __name__ == "__main__":
    main()
