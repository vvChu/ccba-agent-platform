# mypy: ignore-errors
import argparse
import os
import time

from openai import OpenAI

from mdconverter.writer import save_markdown_to_docx

# --- CONFIGURATION ---
# Use Antigravity Env Vars if available
PROXY_URL = os.getenv("ANTIGRAVITY_PROXY", "http://100.79.241.120:8045")
if not PROXY_URL.endswith("/v1"):
    PROXY_URL += "/v1"

API_KEY = os.getenv("ANTIGRAVITY_ACCESS_TOKEN", "sk-83d6b377249445638f597ae9ea4657e7")
client = OpenAI(base_url=PROXY_URL, api_key=API_KEY)


def save_to_docx(text: str, filename: str = "Output_Gemini.docx") -> bool:
    """Saves text to a .docx file via mdconverter.writer."""
    try:
        save_markdown_to_docx(text, filename)
        print(f"\n--- Saved successfully to: {filename} ---")
        return True
    except Exception as e:
        print(f"Error saving file: {e}")
        return False


def generate_ultra_long_content(prompt, target_cycles=3, model_name="gemini-3-pro"):
    """
    Uses OpenAI Client (via Proxy) to force long-form writing.
    """

    # Initialize the conversation history
    messages = [
        {
            "role": "system",
            "content": "You are a helpful, professional AI consultant specialized in writing detailed corporate governance documents.",
        },
        {"role": "user", "content": prompt},
    ]

    full_text = ""
    print(f"--- Initializing content generation with {model_name} ---")
    print(f"--- Proxy: {PROXY_URL} ---")

    # -----------------
    # Cycle 1: The functionality
    # -----------------
    try:
        print(f"Sending Prompt (First 50 chars): {prompt[:50]}...")

        # NOTE: OpenAI client streaming yields chunks with .choices[0].delta.content
        stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=8192,  # Adjust if model supports less/more
        )

        current_response_text = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_text += content
                current_response_text += content

        # Append the assistant's reply to history for the next cycle
        messages.append({"role": "assistant", "content": current_response_text})

    except Exception as e:
        print(f"\nError in Cycle 1: {e}")
        return full_text

    # -----------------
    # Subsequent Cycles
    # -----------------
    for i in range(target_cycles - 1):
        print(f"\n\n--- [Cycle {i + 2}/{target_cycles}: Forcing Continuation...] ---\n")

        # Context-aware continuation prompt
        cont_prompt = "Hãy viết tiếp mạch văn trên một cách chi tiết hơn nữa. Tập trung vào các điều khoản cụ thể, quy trình chi tiết, ví dụ minh họa hoặc biểu mẫu cần thiết. Tuyệt đối không tóm tắt lại ý cũ, hãy mở rộng nội dung sâu hơn."
        messages.append({"role": "user", "content": cont_prompt})

        try:
            time.sleep(1)  # Be nice to the API
            stream = client.chat.completions.create(
                model=model_name, messages=messages, stream=True, temperature=0.7, max_tokens=8192
            )

            current_response_text = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_text += content
                    current_response_text += content

            messages.append({"role": "assistant", "content": current_response_text})

        except Exception as e:
            print(f"Error in Cycle {i + 2}: {e}")
            break

    return full_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate long-form governance docs using Gemini via Proxy."
    )
    parser.add_argument("--prompt", type=str, required=True, help="The prompt for the document.")
    parser.add_argument("--output", type=str, required=True, help="The output .docx filename.")
    parser.add_argument("--cycles", type=int, default=3, help="Number of continuation cycles.")
    parser.add_argument("--model", type=str, default="gemini-3-pro", help="Model name.")

    args = parser.parse_args()

    # Inject env vars if not present (for local testing flexibility)
    if not os.getenv("ANTIGRAVITY_PROXY"):
        os.environ["ANTIGRAVITY_PROXY"] = "http://100.79.241.120:8045"
    if not os.getenv("ANTIGRAVITY_ACCESS_TOKEN"):
        os.environ["ANTIGRAVITY_ACCESS_TOKEN"] = "sk-83d6b377249445638f597ae9ea4657e7"

    print(f"Starting generation for: {args.output}")
    print(f"Target Cycles: {args.cycles}")

    final_output = generate_ultra_long_content(args.prompt, args.cycles, args.model)

    if final_output:
        save_to_docx(final_output, args.output)
    else:
        print("Generation failed or produced no output.")
