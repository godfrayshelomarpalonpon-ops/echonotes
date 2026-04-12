import os
import google.generativeai as genai
from dotenv import load_dotenv

def test_key():
    # Try multiple paths for .env.local
    paths = ['.env.local', '.env', 'echonotes/.env.local', '../.env.local']
    for p in paths:
        load_dotenv(p)
    
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY NOT FOUND in environment.")
        return

    print(f"✅ Found API Key: {api_key[:10]}...")
    
    try:
        genai.configure(api_key=api_key)
        
        # List available models
        print("🔍 Listing available models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}")

        model_to_try = 'gemini-1.5-flash'
        print(f"🚀 Trying model: {model_to_try}")
        model = genai.GenerativeModel(model_to_try)
        response = model.generate_content("Say 'Hello EchoNotes' in exactly three words.")
        print(f"🚀 Gemini Response: {response.text.strip()}")
        print("✨ API KEY IS WORKING!")
    except Exception as e:
        print(f"❌ Gemini API Call failed with {model_to_try}: {e}")
        
        print("🔄 Trying fallback: gemini-flash-latest")
        try:
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content("Say 'Hello EchoNotes' in exactly three words.")
            print(f"🚀 Gemini Response: {response.text.strip()}")
            print("✨ API KEY IS WORKING with gemini-flash-latest!")
        except Exception as e2:
            print(f"❌ Fallback failed too: {e2}")

if __name__ == "__main__":
    test_key()
