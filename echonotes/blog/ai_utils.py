import json
import urllib.request
import os

def call_claude(prompt_text, max_tokens=300):
    """
    Centralized Claude API caller using urllib to avoid external dependencies.
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("DEBUG: ANTHROPIC_API_KEY not found in environment.")
        return "I'm having trouble thinking right now. (API Key Missing)"

    payload = json.dumps({
        "model": "claude-3-haiku-20240307", # Faster/cheaper for summaries/moderation
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt_text}]
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01',
            'x-api-key': api_key
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['content'][0]['text'].strip()
    except Exception as e:
        print(f"DEBUG: Claude API Call failed: {e}")
        return f"ERROR: {e}"
