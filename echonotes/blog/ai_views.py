"""
ADD this function to blog/views.py
It handles the manual AI prompt generation endpoint
"""

@login_required
@require_POST  
def generate_prompt_ai(request):
    import json
    import urllib.request
    import random

    try:
        data = json.loads(request.body) if request.body else {}
        theme = data.get('theme', 'general creative writing')

        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 100,
            "messages": [{
                "role": "user",
                "content": f"""Generate ONE writing prompt for a Filipino literary community called EchoNotes.
Theme: {theme}
- One sentence only, no numbering, no prefix
- Evocative, specific, emotionally resonant
Just the prompt text:"""
            }]
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={'Content-Type': 'application/json', 'anthropic-version': '2023-06-01'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            prompt_text = result['content'][0]['text'].strip()
            return JsonResponse({'prompt': prompt_text, 'success': True})

    except Exception:
        fallbacks = [
            "Write about a moment when silence said more than words ever could.",
            "Describe the smell of rain on a street you used to walk every day.",
            "Write a letter to the city that raised you.",
            "What does hope look like at 3 in the morning?",
            "Write about something you lost that you never told anyone about.",
        ]
        return JsonResponse({'prompt': random.choice(fallbacks), 'success': True, 'fallback': True})


def ai_broadcast(request):
    """GET /ai-broadcast/ — returns the latest AI broadcast"""
    from .models import AIBroadcast
    broadcast = AIBroadcast.objects.filter(is_active=True).first()
    if broadcast:
        return JsonResponse({
            'message': broadcast.message,
            'created_date': broadcast.created_date.strftime('%b %d, %H:%M'),
            'stats': broadcast.get_stats(),
        })
    return JsonResponse({
        'message': 'EchoNotes is alive and growing. Share your story today!',
        'created_date': '',
        'stats': {}
    })
