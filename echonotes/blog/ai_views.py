"""
ADD this function to blog/views.py
It handles the manual AI prompt generation endpoint
"""

@login_required
@require_POST  
def generate_prompt_ai(request):
    import json
    import random
    from .ai_utils import call_gemini

    try:
        data = json.loads(request.body) if request.body else {}
        theme = data.get('theme', 'general creative writing')

        prompt = f"""Generate ONE writing prompt for a Filipino literary community called EchoNotes.
Theme: {theme}
- One sentence only, no numbering, no prefix
- Evocative, specific, emotionally resonant
Just the prompt text:"""

        response_text = call_gemini(prompt, max_tokens=100)
        
        if "ERROR" in response_text:
            raise Exception(response_text)

        # Clean up any potential AI formatting
        clean_prompt = response_text.replace('Just the prompt text:', '').strip().strip('"')
        return JsonResponse({'prompt': clean_prompt, 'success': True})

    except Exception as e:
        print(f"DEBUG: generate_prompt_ai failed: {e}")
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
