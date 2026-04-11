import os
import google.generativeai as genai

def call_gemini(prompt_text, max_tokens=300):
    """
    Centralized Gemini API caller using the Google Generative AI SDK.
    """
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("DEBUG: GOOGLE_API_KEY not found in environment.")
        return "I'm having trouble thinking right now. (API Key Missing)"

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Generation configuration
        config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.7,
        )
        
        response = model.generate_content(prompt_text, generation_config=config)
        return response.text.strip()
        
    except Exception as e:
        print(f"DEBUG: Gemini API Call failed: {e}")
        return f"ERROR: {e}"
