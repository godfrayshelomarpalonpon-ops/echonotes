import json
import random
import urllib.request
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .badges import award_badges, award_badge
from .decorators import admin_required
from .forms import (
    UserRegisterForm, UserUpdateForm, ProfileUpdateForm,
    PostForm, CommentForm, ContestForm, ContestEntryForm,
    ReportForm, PromptResponseForm, WordEntryForm,
    CollaborativeStoryForm, StoryParagraphForm,
)
from .models import (
    Post, Comment, Like, UserProfile, Follow, Bookmark,
    Category, Contest, ContestEntry, ContestVote, Report,
    DailyPrompt, PromptResponse, PromptResponseLike,
    WordOfTheDay, WordOfTheDayEntry, WordEntryLike,
    WritingStreak, CollaborativeStory, StoryParagraph,
    Badge, UserBadge, LeaderboardEntry, WritingSession,
    AIBroadcast, ChatMessage, ChatGroup, ChatGroupMember, DirectMessage,
    Friend, FriendRequest, Notification,
)


# ─── Landing ──────────────────────────────────────────────────────────────────

def landing(request):
    context = {
        'recent_posts': Post.objects.filter(status='published').order_by('-created_date')[:6],
        'popular_posts': Post.objects.filter(status='published').annotate(
            like_count=Count('likes')
        ).order_by('-like_count', '-created_date')[:6],
        'total_posts': Post.objects.filter(status='published').count(),
        'total_users': UserProfile.objects.count(),
        'categories': Category.objects.all(),
        'active_contests': Contest.objects.filter(status__in=['open', 'voting']).order_by('-created_date')[:3],
        'today_prompt': DailyPrompt.objects.filter(date=date.today(), is_active=True).first(),
        'today_word': WordOfTheDay.objects.filter(date=date.today()).first(),
        'latest_broadcast': AIBroadcast.objects.filter(is_active=True).first(),
    }
    return render(request, 'landing.html', context)


# ─── Auth ─────────────────────────────────────────────────────────────────────

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            WritingStreak.objects.get_or_create(user=user)
            messages.success(request, f'Account created! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_active:
                messages.error(request, 'Your account has been blocked. Contact support@echonotes.com.')
                return render(request, 'login.html')
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing')


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user_posts = Post.objects.filter(author=request.user).order_by('-created_date')
    feed_posts_list = Post.objects.filter(status='published').exclude(author=request.user).order_by('-created_date')
    feed_posts = Paginator(feed_posts_list, 10).get_page(request.GET.get('page'))
    streak, _ = WritingStreak.objects.get_or_create(user=request.user)

    friends_qs = Friend.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1', 'user1__profile', 'user2', 'user2__profile')
    friends_list = [f.user2 if f.user1 == request.user else f.user1 for f in friends_qs]

    context = {
        'user_posts': user_posts[:5],
        'feed_posts': feed_posts,
        'post_count': user_posts.count(),
        'draft_count': user_posts.filter(status='draft').count(),
        'total_likes_received': sum(p.total_likes() for p in user_posts),
        'total_comments_received': sum(p.total_comments() for p in user_posts),
        'streak': streak,
        'user_badges': UserBadge.objects.filter(user=request.user).select_related('badge'),
        'today_prompt': DailyPrompt.objects.filter(date=date.today(), is_active=True).first(),
        'today_word': WordOfTheDay.objects.filter(date=date.today()).first(),
        'latest_broadcast': AIBroadcast.objects.filter(is_active=True).first(),
        'user_entries': ContestEntry.objects.filter(author=request.user).count(),
        'followers': Follow.objects.filter(following=request.user).select_related('follower', 'follower__profile'),
        'following_list': Follow.objects.filter(follower=request.user).select_related('following', 'following__profile'),
        'friends': friends_list,
        'pending_requests': FriendRequest.objects.filter(receiver=request.user, is_active=True).select_related('sender', 'sender__profile'),
    }
    return render(request, 'dashboard.html', context)


# ─── Profile ──────────────────────────────────────────────────────────────────

@login_required
def profile(request):
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=prof)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=prof)

    return render(request, 'profile.html', {
        'u_form': u_form,
        'p_form': p_form,
        'user_posts': Post.objects.filter(author=request.user).order_by('-created_date')[:5],
    })


def profile_detail(request, username):
    profile_user = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(author=profile_user, status='published').order_by('-created_date')
    streak, _ = WritingStreak.objects.get_or_create(user=profile_user)

    is_friend = False
    friend_request_sent = None
    friend_request_received = None
    if request.user.is_authenticated and request.user != profile_user:
        is_friend = Friend.objects.filter(
            Q(user1=request.user, user2=profile_user) | Q(user1=profile_user, user2=request.user)
        ).exists()
        friend_request_sent = FriendRequest.objects.filter(
            sender=request.user, receiver=profile_user, is_active=True
        ).first()
        friend_request_received = FriendRequest.objects.filter(
            sender=profile_user, receiver=request.user, is_active=True
        ).first()

    return render(request, 'profile_detail.html', {
        'profile_user': profile_user,
        'user_posts': user_posts,
        'post_count': user_posts.count(),
        'follower_count': profile_user.followers.count(),
        'following_count': profile_user.following.count(),
        'is_following': Follow.objects.filter(follower=request.user, following=profile_user).exists() if request.user.is_authenticated else False,
        'user_badges': UserBadge.objects.filter(user=profile_user).select_related('badge'),
        'streak': streak,
        'is_friend': is_friend,
        'friend_request_sent': friend_request_sent,
        'friend_request_received': friend_request_received,
    })


@login_required
def delete_profile_pic(request):
    try:
        prof = request.user.profile
        if prof.profile_pic and prof.profile_pic.name != 'default.jpg':
            prof.profile_pic.delete()
            prof.profile_pic = 'default.jpg'
            prof.save()
            messages.success(request, 'Profile picture deleted.')
        else:
            messages.info(request, 'No custom profile picture to delete.')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
    return redirect('profile')


# ─── Follow ───────────────────────────────────────────────────────────────────

@login_required
@require_POST
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if user_to_follow == request.user:
        return JsonResponse({'error': 'You cannot follow yourself'}, status=400)
    follow, created = Follow.objects.get_or_create(follower=request.user, following=user_to_follow)
    if not created:
        follow.delete()
        following = False
    else:
        following = True
        _create_notification(user_to_follow, request.user, 'follow',
                             text=f'{request.user.username} started following you')
    
    # Force a fresh count from the DB for the target user ID
    follower_count = Follow.objects.filter(following_id=user_to_follow.id).count()
    return JsonResponse({'following': following, 'follower_count': follower_count})


# ─── Posts ────────────────────────────────────────────────────────────────────

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            if post.status == 'published':
                streak, _ = WritingStreak.objects.get_or_create(user=request.user)
                streak.update_streak()
                award_badges(request.user)
                messages.success(request, 'Post published!')
                return redirect('post-detail', pk=post.pk)
            messages.success(request, 'Saved as draft!')
            return redirect('dashboard')
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.status == 'draft' and post.author != request.user:
        messages.error(request, 'This post is not available.')
        return redirect('landing')

    user_liked = user_bookmarked = user_reported = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(post=post, user=request.user).exists()
        user_bookmarked = Bookmark.objects.filter(post=post, user=request.user).exists()
        user_reported = Report.objects.filter(post=post, reported_by=request.user).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            award_badges(request.user)
            _create_notification(post.author, request.user, 'comment', post=post,
                                 text=f'{request.user.username} commented on "{post.title[:40]}"”')
            messages.success(request, 'Comment added!')
            return redirect('post-detail', pk=post.pk)
    else:
        comment_form = CommentForm()

    return render(request, 'post_detail.html', {
        'post': post,
        'comments': post.comments.all(),
        'comment_form': comment_form,
        'user_liked': user_liked,
        'user_bookmarked': user_bookmarked,
        'user_reported': user_reported,
    })


@login_required
def update_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user and not request.user.is_staff:
        messages.error(request, 'You can only edit your own posts!')
        return redirect('post-detail', pk=post.pk)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated!')
            return redirect('post-detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'update_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user and not request.user.is_staff:
        messages.error(request, 'You can only delete your own posts!')
        return redirect('post-detail', pk=post.pk)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted!')
        return redirect('dashboard')
    return render(request, 'confirm_delete.html', {'obj': post, 'type': 'post'})


# ─── Category & Mood ──────────────────────────────────────────────────────────

def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Paginator(
        Post.objects.filter(category=category, status='published').order_by('-created_date'), 10
    ).get_page(request.GET.get('page'))
    return render(request, 'category_posts.html', {'category': category, 'posts': posts})


def mood_posts(request, mood):
    mood_display = dict(Post._meta.get_field('mood').choices).get(mood, mood)
    posts = Paginator(
        Post.objects.filter(mood=mood, status='published').order_by('-created_date'), 10
    ).get_page(request.GET.get('page'))
    return render(request, 'mood_posts.html', {'mood': mood, 'mood_display': mood_display, 'posts': posts})


# ─── Likes & Bookmarks ────────────────────────────────────────────────────────

@login_required
@require_POST
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        award_badges(post.author)
        _create_notification(post.author, request.user, 'like_post', post=post,
                             text=f'{request.user.username} liked your post "{post.title[:40]}"”')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'total_likes': post.total_likes(), 'message': 'Liked' if liked else 'Unliked'})
    return redirect('post-detail', pk=post.pk)


@login_required
@require_POST
def bookmark_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, post=post)
    if not created:
        bookmark.delete()
    return JsonResponse({'bookmarked': created, 'message': 'Bookmarked' if created else 'Removed'})


@login_required
def my_bookmarks(request):
    return render(request, 'bookmarks.html', {
        'bookmarks': Bookmark.objects.filter(user=request.user).order_by('-created_date')
    })


# ─── Comments ─────────────────────────────────────────────────────────────────

@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.author != request.user and not request.user.is_staff:
        messages.error(request, 'You can only delete your own comments!')
        return redirect('post-detail', pk=comment.post.pk)
    if request.method == 'POST':
        post_pk = comment.post.pk
        comment.delete()
        messages.success(request, 'Comment deleted!')
        return redirect('post-detail', pk=post_pk)
    return render(request, 'confirm_delete.html', {'obj': comment, 'type': 'comment'})


# ─── Reports ──────────────────────────────────────────────────────────────────

@login_required
def report_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author == request.user:
        messages.error(request, 'You cannot report your own post.')
        return redirect('post-detail', pk=post.pk)
    if Report.objects.filter(post=post, reported_by=request.user).exists():
        messages.warning(request, 'You have already reported this post.')
        return redirect('post-detail', pk=post.pk)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.post = post
            report.reported_by = request.user
            report.save()
            messages.success(request, 'Report submitted.')
            return redirect('post-detail', pk=post.pk)
    else:
        form = ReportForm()
    return render(request, 'report_post.html', {'form': form, 'post': post})


# ─── Daily Prompt ─────────────────────────────────────────────────────────────

def daily_prompt(request):
    today_prompt = DailyPrompt.objects.filter(is_active=True).order_by('-date').first()
    user_response = None
    liked_responses = []

    if request.user.is_authenticated and today_prompt:
        user_response = PromptResponse.objects.filter(prompt=today_prompt, author=request.user).first()
        liked_responses = list(PromptResponseLike.objects.filter(
            user=request.user, response__prompt=today_prompt
        ).values_list('response_id', flat=True))

    if request.method == 'POST' and request.user.is_authenticated and today_prompt and not user_response:
        form = PromptResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.prompt = today_prompt
            response.author = request.user
            response.save()
            messages.success(request, 'Response posted!')
            return redirect('daily-prompt')
    else:
        form = PromptResponseForm()

    return render(request, 'daily_prompt.html', {
        'today_prompt': today_prompt,
        'past_prompts': DailyPrompt.objects.filter(is_active=True).exclude(pk=today_prompt.pk if today_prompt else None).order_by('-date')[:5],
        'responses': today_prompt.responses.all() if today_prompt else [],
        'user_response': user_response,
        'form': form,
        'liked_responses': liked_responses,
    })


@login_required
@require_POST
def like_prompt_response(request, pk):
    response = get_object_or_404(PromptResponse, pk=pk)
    like, created = PromptResponseLike.objects.get_or_create(user=request.user, response=response)
    if not created:
        like.delete()
    return JsonResponse({'liked': created, 'total_likes': response.likes.count()})


# ─── Word of the Day ──────────────────────────────────────────────────────────

def word_of_the_day(request):
    today_word = WordOfTheDay.objects.order_by('-date').first()
    user_entry = None
    liked_entries = []

    if request.user.is_authenticated and today_word:
        user_entry = WordOfTheDayEntry.objects.filter(word=today_word, author=request.user).first()
        liked_entries = list(WordEntryLike.objects.filter(
            user=request.user, entry__word=today_word
        ).values_list('entry_id', flat=True))

    if request.method == 'POST' and request.user.is_authenticated and today_word and not user_entry:
        form = WordEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.word = today_word
            entry.author = request.user
            entry.save()
            award_badge(request.user, 'word_challenge')
            award_badges(request.user)
            messages.success(request, 'Entry submitted!')
            return redirect('word-of-the-day')
    else:
        form = WordEntryForm()

    return render(request, 'word_of_the_day.html', {
        'today_word': today_word,
        'past_words': WordOfTheDay.objects.exclude(pk=today_word.pk if today_word else None).order_by('-date')[:5],
        'entries': today_word.entries.annotate(like_count=Count('likes')).order_by('-like_count') if today_word else [],
        'user_entry': user_entry,
        'form': form,
        'liked_entries': liked_entries,
    })


@login_required
@require_POST
def like_word_entry(request, pk):
    entry = get_object_or_404(WordOfTheDayEntry, pk=pk)
    like, created = WordEntryLike.objects.get_or_create(user=request.user, entry=entry)
    if not created:
        like.delete()
    return JsonResponse({'liked': created, 'total_likes': entry.total_likes()})


# ─── Collaborative Stories ────────────────────────────────────────────────────

def collaborative_stories(request):
    stories = Paginator(CollaborativeStory.objects.all().order_by('-created_date'), 10).get_page(request.GET.get('page'))
    return render(request, 'collaborative_stories.html', {'stories': stories})


def collaborative_story_detail(request, pk):
    story = get_object_or_404(CollaborativeStory, pk=pk)
    user_has_contributed = (
        request.user.is_authenticated and
        StoryParagraph.objects.filter(story=story, author=request.user).exists()
    )

    if request.method == 'POST' and request.user.is_authenticated:
        if story.status == 'open' and not user_has_contributed:
            form = StoryParagraphForm(request.POST)
            if form.is_valid():
                para = form.save(commit=False)
                para.story = story
                para.author = request.user
                para.order = story.total_paragraphs() + 1
                para.save()
                award_badge(request.user, 'collab_story')
                award_badges(request.user)
                messages.success(request, 'Paragraph added!')
                return redirect('story-detail', pk=pk)
        elif user_has_contributed:
            messages.warning(request, 'You have already contributed to this story.')
        else:
            messages.error(request, 'This story is closed.')
    else:
        form = StoryParagraphForm()

    return render(request, 'story_detail.html', {
        'story': story,
        'paragraphs': story.paragraphs.all(),
        'user_has_contributed': user_has_contributed,
        'form': form,
        'contributors': story.contributors(),
    })


@login_required
def create_collaborative_story(request):
    if request.method == 'POST':
        form = CollaborativeStoryForm(request.POST)
        if form.is_valid():
            story = form.save(commit=False)
            story.started_by = request.user
            story.save()
            first_para = request.POST.get('first_paragraph', '').strip()
            if first_para:
                StoryParagraph.objects.create(story=story, author=request.user, content=first_para, order=1)
            messages.success(request, 'Story started!')
            return redirect('story-detail', pk=story.pk)
    else:
        form = CollaborativeStoryForm()
    return render(request, 'create_story.html', {'form': form})


# ─── Writing Timer ────────────────────────────────────────────────────────────

@login_required
def writing_timer(request):
    sessions = WritingSession.objects.filter(user=request.user)
    return render(request, 'writing_timer.html', {
        'recent_sessions': sessions.order_by('-created_date')[:10],
        'total_words': sessions.filter(completed=True).aggregate(total=Sum('words_written'))['total'] or 0,
        'total_sessions': sessions.filter(completed=True).count(),
    })


@login_required
@require_POST
def save_writing_session(request):
    session = WritingSession.objects.create(
        user=request.user,
        duration_minutes=int(request.POST.get('duration', 25)),
        words_written=int(request.POST.get('words', 0)),
        completed=request.POST.get('completed', 'false') == 'true',
    )
    return JsonResponse({'status': 'saved', 'session_id': session.pk})


# ─── Leaderboard ──────────────────────────────────────────────────────────────

def leaderboard(request):
    period = request.GET.get('period', 'weekly')
    start_date = timezone.now().date() - timedelta(days=7 if period == 'weekly' else 30) if period != 'alltime' else None
    date_q = Q(posts__created_date__date__gte=start_date) if start_date else Q()
    published = Q(posts__status='published')
    like_q = Q(posts__likes__created_date__date__gte=start_date) if start_date else Q()
    comment_q = Q(comments__created_date__date__gte=start_date) if start_date else Q()

    return render(request, 'leaderboard.html', {
        'period': period,
        'most_liked': User.objects.annotate(total_likes=Count('posts__likes', filter=published & like_q)).order_by('-total_likes')[:10],
        'most_posts': User.objects.annotate(post_count=Count('posts', filter=published & date_q)).filter(post_count__gt=0).order_by('-post_count')[:10],
        'most_comments': User.objects.annotate(comment_count=Count('comments', filter=comment_q)).filter(comment_count__gt=0).order_by('-comment_count')[:10],
    })


# ─── Badges ───────────────────────────────────────────────────────────────────

def badges_page(request):
    user_badge_names = list(UserBadge.objects.filter(user=request.user).values_list('badge__name', flat=True)) if request.user.is_authenticated else []
    return render(request, 'badges.html', {'all_badges': Badge.objects.all(), 'user_badge_names': user_badge_names})


# ─── Contests ─────────────────────────────────────────────────────────────────

def contest_list(request):
    contests = Paginator(Contest.objects.all().order_by('-created_date'), 10).get_page(request.GET.get('page'))
    return render(request, 'contest_list.html', {'contests': contests})


def contest_detail(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    user_entry = user_voted_for = None
    if request.user.is_authenticated:
        user_entry = ContestEntry.objects.filter(contest=contest, author=request.user).first()
        user_voted_for = ContestVote.objects.filter(voter=request.user, entry__contest=contest).first()
    return render(request, 'contest_detail.html', {
        'contest': contest,
        'entries': contest.entries.annotate(vote_count=Count('votes')).order_by('-vote_count'),
        'user_entry': user_entry,
        'user_voted_for': user_voted_for,
    })


@login_required
def submit_contest_entry(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    if contest.status == 'closed':
        messages.error(request, 'This contest is closed.')
        return redirect('contest-detail', pk=pk)
    if contest.status == 'voting':
        messages.error(request, 'Submissions are closed — voting is in progress.')
        return redirect('contest-detail', pk=pk)
    if timezone.now() > contest.submission_deadline:
        messages.error(request, 'The submission deadline has passed.')
        return redirect('contest-detail', pk=pk)
    if ContestEntry.objects.filter(contest=contest, author=request.user).exists():
        messages.warning(request, 'You have already submitted an entry.')
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
            messages.success(request, 'Entry submitted! Good luck!')
            return redirect('contest-detail', pk=pk)
    else:
        form = ContestEntryForm()
    return render(request, 'submit_entry.html', {'form': form, 'contest': contest})


@login_required
@require_POST
def vote_contest_entry(request, entry_pk):
    entry = get_object_or_404(ContestEntry, pk=entry_pk)
    contest = entry.contest
    if not contest.is_voting():
        return JsonResponse({'error': 'Voting is not open.'}, status=400)
    if entry.author == request.user:
        return JsonResponse({'error': 'You cannot vote for your own entry.'}, status=400)
    existing = ContestVote.objects.filter(voter=request.user, entry__contest=contest).first()
    if existing:
        if existing.entry == entry:
            existing.delete()
            voted = False
        else:
            existing.entry = entry
            existing.save()
            voted = True
    else:
        ContestVote.objects.create(entry=entry, voter=request.user)
        voted = True
    return JsonResponse({'voted': voted, 'total_votes': entry.total_votes()})


# ─── AI Features ──────────────────────────────────────────────────────────────

def ai_broadcast(request):
    broadcast = AIBroadcast.objects.filter(is_active=True).first()
    if broadcast:
        return JsonResponse({
            'message': broadcast.message,
            'created_date': broadcast.created_date.strftime('%b %d, %H:%M'),
            'stats': broadcast.get_stats(),
        })
    return JsonResponse({'message': 'EchoNotes is alive and growing. Share your story today!', 'created_date': '', 'stats': {}})


@login_required
@require_POST
def generate_prompt_ai(request):
    try:
        data = json.loads(request.body) if request.body else {}
        theme = data.get('theme', 'general creative writing')
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": f"Generate ONE writing prompt for a Filipino literary community.\nTheme: {theme}\nOne sentence only, evocative, no prefix.\nJust the prompt:"}]
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={'Content-Type': 'application/json', 'anthropic-version': '2023-06-01'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            return JsonResponse({'prompt': result['content'][0]['text'].strip(), 'success': True})
    except Exception:
        fallbacks = [
            "Write about a moment when silence said more than words ever could.",
            "Describe the smell of rain on a street you used to walk every day.",
            "Write a letter to the city that raised you.",
            "What does hope look like at 3 in the morning?",
        ]
        return JsonResponse({'prompt': random.choice(fallbacks), 'success': True})


@login_required
@require_POST
def generate_word_ai(request):
    try:
        data = json.loads(request.body) if request.body else {}
        theme = data.get('theme', 'obscure but beautiful English words')
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 150,
            "messages": [{"role": "user", "content": f"Generate ONE word of the day for a literary community.\nTheme: {theme}\nProvide a JSON object with 'word', 'definition', and 'example'. Do not add markdown blocks."}]
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={'Content-Type': 'application/json', 'anthropic-version': '2023-06-01'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            text = result['content'][0]['text'].strip()
            # Try to safely parse the JSON block (it might have markdown ticks)
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            parsed = json.loads(match.group(0)) if match else json.loads(text)
            return JsonResponse({'word_data': parsed, 'success': True})
    except Exception as e:
        fallbacks = [
            {"word": "Petrichor", "definition": "A pleasant smell that frequently accompanies the first rain after a long period of warm, dry weather.", "example": "Other than the petrichor emanating from the rapidly drying grass, there was not a trace of evidence that it had rained at all."},
            {"word": "Sonder", "definition": "The realization that each random passerby has a life as vivid and complex as your own.", "example": "Sitting on the train, a profound sense of sonder washed over her as she watched the commuters."},
        ]
        return JsonResponse({'word_data': random.choice(fallbacks), 'success': True})


# ─── Chat APIs for Widget ────────────────────────────────────────────────────────

@login_required
def get_chat_contacts(request):
    """Returns lists of Fans (users who follow me) and Groups I am in."""
    me = request.user
    
    fans = Follow.objects.filter(following=me).select_related('follower', 'follower__profile')
    fans_data = []
    for f in fans:
        u = f.follower
        has_pic = hasattr(u, 'profile') and u.profile.profile_pic and u.profile.profile_pic.name != 'default.jpg'
        fans_data.append({
            'id': u.id,
            'username': u.username,
            'avatar': u.profile.profile_pic.url if has_pic else None
        })
        
    memberships = ChatGroupMember.objects.filter(user=me).select_related('group')
    groups_data = []
    for m in memberships:
        groups_data.append({
            'id': m.group.id,
            'name': m.group.name
        })
        
    return JsonResponse({'fans': fans_data, 'groups': groups_data})


@login_required
def post_chat_message(request):
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        chat_type = request.POST.get('chat_type') # 'fan' or 'group'
        target_id = request.POST.get('target_id')
        
        if not message or not target_id:
            return JsonResponse({'status': 'error', 'message': 'Invalid input'}, status=400)
            
        if chat_type == 'fan':
            partner = get_object_or_404(User, id=target_id)
            dm = DirectMessage.objects.create(sender=request.user, recipient=partner, message=message)
            has_pic = hasattr(dm.sender, 'profile') and dm.sender.profile.profile_pic and dm.sender.profile.profile_pic.name != 'default.jpg'
            return JsonResponse({
                'status': 'ok', 'id': dm.id, 'user': dm.sender.username,
                'message': dm.message, 'timestamp': dm.created_date.strftime('%H:%M'),
                'avatar': dm.sender.profile.profile_pic.url if has_pic else None, 'is_me': True
            })
            
        elif chat_type == 'group':
            group = get_object_or_404(ChatGroup, id=target_id)
            if not ChatGroupMember.objects.filter(group=group, user=request.user).exists():
                return JsonResponse({'error': 'Not in group'}, status=403)
            msg = ChatMessage.objects.create(author=request.user, message=message, group=group)
            has_pic = hasattr(msg.author, 'profile') and msg.author.profile.profile_pic and msg.author.profile.profile_pic.name != 'default.jpg'
            return JsonResponse({
                'status': 'ok', 'id': msg.id, 'user': msg.author.username,
                'message': msg.message, 'timestamp': msg.created_date.strftime('%H:%M'),
                'avatar': msg.author.profile.profile_pic.url if has_pic else None, 'is_me': True
            })
            
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def get_chat_messages(request):
    chat_type = request.GET.get('chat_type')
    target_id = request.GET.get('target_id')
    since_id = int(request.GET.get('since', 0))
    me = request.user
    
    if not chat_type or not target_id:
        return JsonResponse({'messages': []})

    data = []
    if chat_type == 'fan':
        from django.db.models import Q as DQ
        partner = get_object_or_404(User, id=target_id)
        dms = DirectMessage.objects.filter(
            DQ(sender=me, recipient=partner) | DQ(sender=partner, recipient=me),
            id__gt=since_id
        ).select_related('sender', 'sender__profile').order_by('created_date')[:30]
        DirectMessage.objects.filter(sender=partner, recipient=me, is_read=False, id__gt=since_id).update(is_read=True)
        
        for m in dms:
            has_pic = hasattr(m.sender, 'profile') and m.sender.profile.profile_pic and m.sender.profile.profile_pic.name != 'default.jpg'
            data.append({
                'id': m.id, 'user': m.sender.username, 'message': m.message,
                'timestamp': m.created_date.strftime('%H:%M'),
                'avatar': m.sender.profile.profile_pic.url if has_pic else None,
                'is_me': m.sender == me
            })
    elif chat_type == 'group':
        group = get_object_or_404(ChatGroup, id=target_id)
        if not ChatGroupMember.objects.filter(group=group, user=request.user).exists():
            return JsonResponse({'messages': []})
            
        msgs = ChatMessage.objects.filter(group=group, id__gt=since_id).select_related('author', 'author__profile').order_by('created_date')[:30]
        for m in msgs:
            has_pic = hasattr(m.author, 'profile') and m.author.profile.profile_pic and m.author.profile.profile_pic.name != 'default.jpg'
            data.append({
                'id': m.id, 'user': m.author.username, 'message': m.message,
                'timestamp': m.created_date.strftime('%H:%M'),
                'avatar': m.author.profile.profile_pic.url if has_pic else None,
                'is_me': m.author == me
            })

    return JsonResponse({'messages': data})


# ─── Direct Messages (Private) ────────────────────────────────────────────────

@login_required
def inbox(request):
    """
    Shows a list of unique conversation partners for the logged-in user,
    sorted by the most recent message.
    """
    from django.db.models import Max, Q as DQ

    me = request.user

    # All DMs involving me
    threads = (
        DirectMessage.objects
        .filter(DQ(sender=me) | DQ(recipient=me))
        .values('sender', 'recipient')
        .annotate(last_at=Max('created_date'))
        .order_by('-last_at')
    )

    seen_partners = set()
    conversations = []
    for t in threads:
        partner_id = t['recipient'] if t['sender'] == me.id else t['sender']
        if partner_id in seen_partners:
            continue
        seen_partners.add(partner_id)
        partner = User.objects.select_related('profile').get(pk=partner_id)
        # Latest message in this thread
        last_msg = (
            DirectMessage.objects
            .filter(
                DQ(sender=me, recipient=partner) | DQ(sender=partner, recipient=me)
            )
            .order_by('-created_date')
            .first()
        )
        unread = DirectMessage.objects.filter(sender=partner, recipient=me, is_read=False).count()
        conversations.append({
            'partner': partner,
            'last_msg': last_msg,
            'unread': unread,
        })

    return render(request, 'inbox.html', {'conversations': conversations})


@login_required
def conversation(request, username):
    """
    Private 1-on-1 conversation between request.user and `username`.
    Only these two users can access it.
    """
    from django.db.models import Q as DQ

    partner = get_object_or_404(User, username=username)
    if partner == request.user:
        messages.warning(request, "You can't message yourself.")
        return redirect('inbox')

    me = request.user

    if request.method == 'POST':
        text = request.POST.get('message', '').strip()
        if text and len(text) <= 1000:
            dm = DirectMessage.objects.create(sender=me, recipient=partner, message=text)
            has_pic = (
                hasattr(dm.sender, 'profile') and
                dm.sender.profile.profile_pic and
                dm.sender.profile.profile_pic.name != 'default.jpg'
            )
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'ok',
                    'id': dm.id,
                    'user': dm.sender.username,
                    'message': dm.message,
                    'timestamp': dm.created_date.strftime('%H:%M'),
                    'avatar': dm.sender.profile.profile_pic.url if has_pic else None,
                    'is_me': True,
                })
            return redirect('conversation', username=username)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Invalid message'}, status=400)

    # Mark received messages as read
    DirectMessage.objects.filter(sender=partner, recipient=me, is_read=False).update(is_read=True)

    dms_list = list(
        DirectMessage.objects.filter(
            DQ(sender=me, recipient=partner) | DQ(sender=partner, recipient=me)
        ).select_related('sender', 'sender__profile').order_by('created_date')[:100]
    )

    return render(request, 'conversation.html', {
        'partner': partner,
        'dms': dms_list,
        'last_id': dms_list[-1].id if dms_list else 0,
    })


@login_required
def get_dm_messages(request, username):
    """
    Ajax polling: returns new DMs in the conversation since `since_id`.
    Only the two participants can call this.
    """
    from django.db.models import Q as DQ

    partner = get_object_or_404(User, username=username)
    me = request.user
    since_id = int(request.GET.get('since', 0))

    dms = DirectMessage.objects.filter(
        DQ(sender=me, recipient=partner) | DQ(sender=partner, recipient=me),
        id__gt=since_id
    ).select_related('sender', 'sender__profile').order_by('created_date')[:30]

    # Mark incoming as read
    DirectMessage.objects.filter(sender=partner, recipient=me, is_read=False, id__gt=since_id).update(is_read=True)

    data = []
    for m in dms:
        has_pic = (
            hasattr(m.sender, 'profile') and
            m.sender.profile.profile_pic and
            m.sender.profile.profile_pic.name != 'default.jpg'
        )
        data.append({
            'id': m.id,
            'user': m.sender.username,
            'message': m.message,
            'timestamp': m.created_date.strftime('%H:%M'),
            'avatar': m.sender.profile.profile_pic.url if has_pic else None,
            'is_me': m.sender == me,
        })
    return JsonResponse({'messages': data})


# ─── Admin ────────────────────────────────────────────────────────────────────

@admin_required
def admin_dashboard(request):
    today = timezone.now().date()
    days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

    context = {
        'total_users': User.objects.count(),
        'total_posts': Post.objects.filter(status='published').count(),
        'total_comments': Comment.objects.count(),
        'total_likes': Like.objects.count(),
        'pending_reports': Report.objects.filter(status='pending').count(),
        'active_contests': Contest.objects.filter(status__in=['open', 'voting']).count(),
        'recent_users': User.objects.order_by('-date_joined')[:10],
        'recent_posts': Post.objects.filter(status='published').order_by('-created_date')[:10],
        'recent_comments': Comment.objects.order_by('-created_date')[:10],
        'posts_per_day': json.dumps([{'date': str(d), 'count': Post.objects.filter(created_date__date=d, status='published').count()} for d in days]),
        'top_writers': User.objects.annotate(post_count=Count('posts', filter=Q(posts__status='published'))).order_by('-post_count')[:5],
        'category_stats': Category.objects.annotate(post_count=Count('posts', filter=Q(posts__status='published'))).order_by('-post_count'),
    }
    return render(request, 'admin_dashboard.html', context)


@admin_required
def manage_users(request):
    if request.method == 'POST' and 'delete_user' in request.POST:
        user_to_delete = get_object_or_404(User, id=request.POST.get('user_id'))
        if user_to_delete == request.user:
            messages.error(request, 'You cannot delete your own account!')
        else:
            user_to_delete.delete()
            messages.success(request, 'User deleted.')
        return redirect('manage-users')
    return render(request, 'manage_users.html', {'users': User.objects.all().order_by('-date_joined')})


@admin_required
def manage_posts(request):
    return render(request, 'manage_posts.html', {'posts': Post.objects.all().order_by('-created_date')})


@admin_required
def manage_reports(request):
    reports = Report.objects.all().order_by('-created_date')
    status_filter = request.GET.get('status', '')
    if status_filter:
        reports = reports.filter(status=status_filter)
    return render(request, 'manage_reports.html', {
        'reports': reports,
        'status_filter': status_filter,
        'pending_count': Report.objects.filter(status='pending').count(),
    })


@admin_required
def review_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        report.reviewed_by = request.user
        report.admin_note = request.POST.get('admin_note', '')
        if action == 'resolve':
            report.status = 'resolved'
            report.post.delete()
            report.save()
            messages.success(request, 'Report resolved — post deleted.')
            return redirect('manage-reports')
        report.status = 'dismissed' if action == 'dismiss' else 'reviewed'
        report.save()
        messages.success(request, f'Report {report.status}.')
        return redirect('manage-reports')
    return render(request, 'review_report.html', {'report': report})


@admin_required
def manage_contests(request):
    return render(request, 'manage_contests.html', {'contests': Contest.objects.all().order_by('-created_date')})


@admin_required
def create_contest(request):
    if request.method == 'POST':
        form = ContestForm(request.POST)
        if form.is_valid():
            contest = form.save(commit=False)
            contest.created_by = request.user
            contest.save()
            messages.success(request, 'Contest created!')
            return redirect('manage-contests')
    else:
        form = ContestForm()
    return render(request, 'create_contest.html', {'form': form})


@admin_required
def update_contest_status(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['open', 'voting', 'closed']:
            contest.status = new_status
            contest.save()
            messages.success(request, 'Contest status updated.')
    return redirect('manage-contests')


@admin_required
def declare_winner(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    if request.method == 'POST':
        entry = get_object_or_404(ContestEntry, pk=request.POST.get('entry_id'), contest=contest)
        contest.winner = entry
        contest.status = 'closed'
        contest.save()
        award_badge(entry.author, 'contest_winner')
        messages.success(request, f'Winner: {entry.author.username}')
    return redirect('contest-detail', pk=pk)


@admin_required
def manage_prompts(request):
    if request.method == 'POST':
        prompt_text = request.POST.get('prompt', '').strip()
        prompt_date = request.POST.get('date', str(date.today()))
        if prompt_text:
            DailyPrompt.objects.get_or_create(date=prompt_date, defaults={'prompt': prompt_text, 'created_by': request.user})
            messages.success(request, 'Prompt created!')
        return redirect('manage-prompts')
    return render(request, 'manage_prompts.html', {'prompts': DailyPrompt.objects.all().order_by('-date'), 'today': str(date.today())})


@admin_required
def manage_words(request):
    if request.method == 'POST':
        word = request.POST.get('word', '').strip()
        definition = request.POST.get('definition', '').strip()
        word_date = request.POST.get('date', str(date.today()))
        if word and definition:
            WordOfTheDay.objects.get_or_create(date=word_date, defaults={
                'word': word, 'definition': definition,
                'example': request.POST.get('example', '').strip(),
                'created_by': request.user
            })
            messages.success(request, 'Word created!')
        return redirect('manage-words')
    return render(request, 'manage_words.html', {'words': WordOfTheDay.objects.all().order_by('-date')})


# ─── Search & Static Pages ────────────────────────────────────────────────────

def search(request):
    query = request.GET.get('q', '').strip()
    posts = Post.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query) | Q(author__username__icontains=query),
        status='published'
    ).order_by('-created_date') if query else Post.objects.none()
    users = User.objects.filter(
        Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
    ).select_related('profile').order_by('username')[:10] if query else User.objects.none()
    return render(request, 'search_results.html', {
        'query': query,
        'posts': posts,
        'users': users,
        'result_count': posts.count(),
        'user_count': users.count(),
    })


def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        messages.success(request, f'Thank you {name}! Your message has been sent.')
        return redirect('contact')
    return render(request, 'contact.html')


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


# ─── Notification Helper ──────────────────────────────────────────────────────

def _create_notification(recipient, sender, notif_type, post=None, text=''):
    """Create a notification, silently skip self-notifications and dupes."""
    if recipient == sender:
        return
    from django.utils import timezone
    Notification.objects.filter(
        recipient=recipient,
        sender=sender,
        notification_type=notif_type,
        post_reference=post
    ).delete() # Simple way to ensure only one exists, or we could just use first()
    
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notif_type,
        post_reference=post,
        text_preview=text,
        is_read=False,
        created_date=timezone.now()
    )


# ─── Friend System ────────────────────────────────────────────────────────────

@login_required
@require_POST
def send_friend_request(request, username):
    to_user = get_object_or_404(User, username=username)
    if to_user == request.user:
        return JsonResponse({'error': 'Cannot friend yourself'}, status=400)
    already = Friend.objects.filter(
        Q(user1=request.user, user2=to_user) | Q(user1=to_user, user2=request.user)
    ).exists()
    if already:
        return JsonResponse({'status': 'already_friends'})
    req, created = FriendRequest.objects.get_or_create(
        sender=request.user, receiver=to_user,
        defaults={'is_active': True},
    )
    if not created and not req.is_active:
        req.is_active = True
        req.save()
    _create_notification(
        to_user, request.user, 'friend_request',
        text=f'{request.user.username} sent you a friend request',
    )
    return JsonResponse({'status': 'sent'})


@login_required
@require_POST
def accept_friend_request(request, pk):
    freq = get_object_or_404(FriendRequest, pk=pk, receiver=request.user, is_active=True)
    freq.is_active = False
    freq.save()
    u1, u2 = (freq.sender, freq.receiver) if freq.sender.id < freq.receiver.id else (freq.receiver, freq.sender)
    Friend.objects.get_or_create(user1=u1, user2=u2)
    _create_notification(
        freq.sender, request.user, 'friend_accept',
        text=f'{request.user.username} accepted your friend request',
    )
    return JsonResponse({'status': 'accepted'})


@login_required
@require_POST
def decline_friend_request(request, pk):
    freq = get_object_or_404(FriendRequest, pk=pk, receiver=request.user, is_active=True)
    freq.is_active = False
    freq.save()
    return JsonResponse({'status': 'declined'})


@login_required
@require_POST
def remove_friend(request, username):
    other = get_object_or_404(User, username=username)
    Friend.objects.filter(
        Q(user1=request.user, user2=other) | Q(user1=other, user2=request.user)
    ).delete()
    return JsonResponse({'status': 'removed'})


# ─── Notifications API ────────────────────────────────────────────────────────

TYPE_ICONS = {
    'like_post':      '❤️',
    'like_prompt':    '💜',
    'like_word':      '📖',
    'comment':        '💬',
    'follow':         '👤',
    'friend_request': '🤝',
    'friend_accept':  '✅',
}

TYPE_LABELS = {
    'like_post':      '{sender} liked your post',
    'like_prompt':    '{sender} liked your prompt response',
    'like_word':      '{sender} liked your word entry',
    'comment':        '{sender} commented on your post',
    'follow':         '{sender} started following you',
    'friend_request': '{sender} sent you a friend request',
    'friend_accept':  '{sender} accepted your friend request',
}


@login_required
def get_notifications(request):
    notifs = (
        Notification.objects
        .filter(recipient=request.user)
        .select_related('sender', 'sender__profile', 'post_reference')
        .order_by('-created_date')[:25]
    )
    data = []
    for n in notifs:
        default = TYPE_LABELS.get(n.notification_type, 'New notification').format(sender=n.sender.username)
        has_pic = hasattr(n.sender, 'profile') and n.sender.profile.profile_pic and n.sender.profile.profile_pic.name != 'default.jpg'
        data.append({
            'id':       n.id,
            'type':     n.notification_type,
            'icon':     TYPE_ICONS.get(n.notification_type, '🔔'),
            'sender':   n.sender.username,
            'avatar':   n.sender.profile.profile_pic.url if has_pic else None,
            'text':     n.text_preview or default,
            'is_read':  n.is_read,
            'post_id':  n.post_reference.id if n.post_reference else None,
            'created':  n.created_date.strftime('%b %d, %H:%M'),
        })
    unread = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'notifications': data, 'unread_count': unread})


@login_required
@require_POST
def mark_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})