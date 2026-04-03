# ADD these functions to blog/views.py

@login_required
def chat_room(request):
    from .models import ChatMessage
    messages_list = ChatMessage.objects.filter(room='general').order_by('-created_date')[:50]
    messages_list = list(reversed(messages_list))
    return render(request, 'chat.html', {'chat_messages': messages_list})


@login_required
@require_POST
def send_chat_message(request):
    from .models import ChatMessage
    message = request.POST.get('message', '').strip()
    if message and len(message) <= 500:
        ChatMessage.objects.create(
            author=request.user,
            message=message,
            room='general'
        )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Invalid message'}, status=400)


def get_chat_messages(request):
    from .models import ChatMessage
    since_id = request.GET.get('since', 0)
    messages_qs = ChatMessage.objects.filter(
        room='general',
        id__gt=since_id
    ).order_by('created_date')[:20]

    messages_data = [{
        'id': m.id,
        'author': m.author.username,
        'message': m.message,
        'time': m.created_date.strftime('%H:%M'),
        'is_me': m.author == request.user if request.user.is_authenticated else False,
    } for m in messages_qs]

    return JsonResponse({'messages': messages_data})
