import os
import google.generativeai as genai
from dotenv import load_dotenv

# Ensure environment variables are loaded from .env.local if it exists
# utils.py is in c:\Users\Admin\Desktop\echonotes\echonotes\blog\
# We need to go 2 levels up to reach c:\Users\Admin\Desktop\echonotes\
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../.env.local')
load_dotenv(env_path)
# Also try standard .env at root
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../.env'))
# Try looking in the current working directory too as a fallback
load_dotenv('.env.local')
load_dotenv()

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
        model = genai.GenerativeModel('gemini-flash-latest')
        
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
