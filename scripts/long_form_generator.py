import google.generativeai as genai
from docx import Document
from docx.shared import Pt
import os
import argparse
import sys

# --- CONFIGURATION ---
# Attempt to get API key from environment, fallback to hardcoded (passed from agent memory)
# ideally this should be set in the environment
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCtKIai4qH5TGJvFRPVY9wLUqq5tU-vUT0") 
genai.configure(api_key=API_KEY)

def save_to_docx(text, filename="Output_Gemini.docx"):
    """Saves text to a .docx file with Vietnamese-friendly font settings."""
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    # Simple markdown-to-docx line handling
    # In a real app, we might use a markdown parser, but splitting by line works for basic drafts.
    for line in text.split('\n'):
        doc.add_paragraph(line)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    
    doc.save(filename)
    print(f"\n--- Saved successfully to: {filename} ---")

def generate_ultra_long_content(prompt, target_cycles=3, model_name="gemini-1.5-pro"):
    """
    Uses ChatSession to force Gemini to write deeply by chaining prompts.
    """
    generation_config = {
        "temperature": 0.7, # Slightly lower for more structured regulation text
        "top_p": 0.95,
        "max_output_tokens": 8192, # Limit per response (standard for 1.5 Pro)
    }

    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config
        )
        chat = model.start_chat(history=[])
    except Exception as e:
        print(f"Error initializing model: {e}")
        return ""

    full_text = ""
    print("--- Initializing content generation... ---")
    
    # Cycle 1: The functionality
    try:
        print(f" sending Prompt: {prompt[:50]}...")
        response = chat.send_message(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                print(chunk.text, end="", flush=True)
                full_text += chunk.text
    except Exception as e:
        print(f"\nError in Cycle 1: {e}")
        return full_text

    # Subsequent Cycles
    for i in range(target_cycles - 1):
        print(f"\n\n--- [Forcing Continuation Cycle {i+2}/{target_cycles}...] ---\n")
        cont_prompt = "Hãy viết tiếp mạch văn trên một cách chi tiết hơn nữa, đi sâu vào các quy định cụ thể, quy trình thực hiện, và các biểu mẫu liên quan. Tuyệt đối không tóm tắt lại ý cũ."
        
        try:
            response = chat.send_message(cont_prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    print(chunk.text, end="", flush=True)
                    full_text += chunk.text
        except Exception as e:
            print(f"Error in Cycle {i+2}: {e}")
            break

    return full_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate long-form governance docs using Gemini.")
    parser.add_argument("--prompt", type=str, required=True, help="The prompt for the document.")
    parser.add_argument("--output", type=str, required=True, help="The output .docx filename.")
    parser.add_argument("--cycles", type=int, default=3, help="Number of continuation cycles.")
    parser.add_argument("--model", type=str, default="gemini-1.5-pro", help="Model name.")

    args = parser.parse_args()

    print(f"Starting generation for: {args.output}")
    final_output = generate_ultra_long_content(args.prompt, args.cycles, args.model)
    
    if final_output:
        save_to_docx(final_output, args.output)
    else:
        print("Generation failed or produced no output.")
