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

    from google.generativeai.types import HarmCategory, HarmBlockThreshold

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Generation configuration
        config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.7,
        )

        # Relaxed safety settings for literary/creative writing
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }
        
        response = model.generate_content(
            prompt_text, 
            generation_config=config,
            safety_settings=safety_settings
        )
        
        # Check if response was blocked
        try:
            return response.text.strip()
        except ValueError:
            # If the response was blocked, return an indicator
            print(f"DEBUG: Gemini response blocked by safety filters. Finish reason: {response.candidates[0].finish_reason}")
            return "ERROR: Safety Filter Block"
        
    except Exception as e:
        print(f"DEBUG: Gemini API Call failed: {e}")
        return f"ERROR: {e}"
