"""
ADDITIONS AND FIXES for blog/views.py

1. Fixed submit_contest_entry
2. AI prompt generator endpoint
3. AI broadcast view
4. Updated landing and dashboard to include broadcast
"""


# ── FIX 1: Replace submit_contest_entry in views.py ──────────────────────────

def submit_contest_entry(request, pk):
    from django.utils import timezone as tz
    contest = get_object_or_404(Contest, pk=pk)

    if contest.status == 'closed':
        messages.error(request, 'This contest is closed.')
        return redirect('contest-detail', pk=pk)

    if contest.status == 'voting':
        messages.error(request, 'This contest is in the voting phase — no more submissions.')
        return redirect('contest-detail', pk=pk)

    if tz.now() > contest.submission_deadline:
        messages.error(request, 'The submission deadline has passed.')
        return redirect('contest-detail', pk=pk)

    if not request.user.is_authenticated:
        messages.info(request, 'Please login to submit an entry.')
        return redirect('login')

    if ContestEntry.objects.filter(contest=contest, author=request.user).exists():
        messages.warning(request, 'You have already submitted an entry for this contest.')
        return redirect('contest-detail', pk=pk)

    if request.method == 'POST':
        form = ContestEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.contest = contest
            entry.author = request.user
            entry.save()
            award_badge(request.user, 'contest_entry')
            award_badges(request.user)
            messages.success(request, '🎉 Your entry has been submitted! Good luck!')
            return redirect('contest-detail', pk=pk)
    else:
        form = ContestEntryForm()

    return render(request, 'submit_entry.html', {'form': form, 'contest': contest})


# ── FIX 2: Add this AI broadcast view ────────────────────────────────────────

def ai_broadcast(request):
    """GET /ai-broadcast/ — returns the latest AI broadcast as JSON"""
    from .models import AIBroadcast
    broadcast = AIBroadcast.objects.filter(is_active=True).first()
    if broadcast:
        return JsonResponse({
            'message': broadcast.message,
            'created_date': broadcast.created_date.strftime('%b %d, %H:%M'),
            'stats': broadcast.get_stats(),
        })
    return JsonResponse({'message': 'The community is quiet right now. Be the first to write something!', 'created_date': '', 'stats': {}})


# ── FIX 3: Updated landing view — add broadcast ───────────────────────────────

def landing(request):
    from .models import AIBroadcast
    recent_posts = Post.objects.filter(status='published').order_by('-created_date')[:6]
    popular_posts = Post.objects.filter(status='published').annotate(
        like_count=Count('likes')
    ).order_by('-like_count', '-created_date')[:6]
    categories = Category.objects.all()
    active_contests = Contest.objects.filter(status__in=['open', 'voting']).order_by('-created_date')[:3]
    today_prompt = DailyPrompt.objects.filter(date=date.today(), is_active=True).first()
    today_word = WordOfTheDay.objects.filter(date=date.today()).first()
    latest_broadcast = AIBroadcast.objects.filter(is_active=True).first()

    context = {
        'recent_posts': recent_posts,
        'popular_posts': popular_posts,
        'total_posts': Post.objects.filter(status='published').count(),
        'total_users': UserProfile.objects.count(),
        'categories': categories,
        'active_contests': active_contests,
        'today_prompt': today_prompt,
        'today_word': today_word,
        'latest_broadcast': latest_broadcast,
    }
    return render(request, 'landing.html', context)


# ── FIX 4: Updated dashboard view — add broadcast ────────────────────────────

def dashboard(request):
    from .models import AIBroadcast, WritingStreak, UserBadge
    user_posts = Post.objects.filter(author=request.user).order_by('-created_date')
    feed_posts_list = Post.objects.filter(
        status='published'
    ).exclude(author=request.user).order_by('-created_date')

    paginator = Paginator(feed_posts_list, 10)
    feed_posts = paginator.get_page(request.GET.get('page'))

    total_likes_received = sum(p.total_likes() for p in user_posts)
    total_comments_received = sum(p.total_comments() for p in user_posts)

    streak, _ = WritingStreak.objects.get_or_create(user=request.user)
    user_badges = UserBadge.objects.filter(user=request.user).select_related('badge')
    today_prompt = DailyPrompt.objects.filter(date=date.today(), is_active=True).first()
    today_word = WordOfTheDay.objects.filter(date=date.today()).first()
    latest_broadcast = AIBroadcast.objects.filter(is_active=True).first()

    context = {
        'user_posts': user_posts[:5],
        'feed_posts': feed_posts,
        'post_count': user_posts.count(),
        'draft_count': user_posts.filter(status='draft').count(),
        'total_likes_received': total_likes_received,
        'total_comments_received': total_comments_received,
        'streak': streak,
        'user_badges': user_badges,
        'today_prompt': today_prompt,
        'today_word': today_word,
        'latest_broadcast': latest_broadcast,
        'user_entries': ContestEntry.objects.filter(author=request.user).count(),
    }
    return render(request, 'dashboard.html', context)
