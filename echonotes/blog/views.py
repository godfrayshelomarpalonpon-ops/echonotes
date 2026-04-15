from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date, timedelta
import json

from .models import (
    Post, Comment, Like, Follow, Bookmark, Category, Contest, ContestEntry,
    ContestVote, Report, DailyPrompt, PromptResponse, PromptResponseLike,
    WordOfTheDay, WordOfTheDayEntry, WordEntryLike, WritingStreak,
    CollaborativeStory, StoryParagraph, Badge, UserBadge, LeaderboardEntry,
    WritingSession, AIBroadcast, DirectMessage, Friend, FriendRequest,
    Notification, UserProfile, ChatGroup, ChatGroupMember, ChatMessage,
)
from .forms import (
    UserRegisterForm, UserUpdateForm, ProfileUpdateForm, PostForm, CommentForm,
    ContestForm, ContestEntryForm, ReportForm, PromptResponseForm,
    WordEntryForm, CollaborativeStoryForm, StoryParagraphForm,
)
from .badges import award_badge, award_badges


# ─── Auth ─────────────────────────────────────────────────────────────────────

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


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            if hasattr(user, 'profile'):
                user.profile.password_plain = request.POST.get('password1', '')
                user.profile.save()
            login(request, user)
            messages.success(request, f'Welcome to EchoNotes, {user.username}! 🎉')
            return redirect('profile-detail', username=user.username)
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('profile-detail', username=request.user.username)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # Capture password for admin visibility
            if hasattr(user, 'profile'):
                user.profile.password_plain = password
                user.profile.save()
            return redirect(request.GET.get('next', reverse('profile-detail', kwargs={'username': user.username})))
        messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('landing')


# ─── Dashboard (redirects to profile) ─────────────────────────────────────────

@login_required
def dashboard(request):
    return redirect('profile-detail', username=request.user.username)


# ─── Posts ────────────────────────────────────────────────────────────────────

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            if post.status == 'published':
                streak, _ = WritingStreak.objects.get_or_create(user=request.user)
                streak.update_streak()
                award_badges(request.user)
            messages.success(request, '✨ Your echo has been published!')
            return redirect('post-detail', pk=post.pk)
    else:
        form = PostForm(user=request.user)
    return render(request, 'create_post.html', {'form': form})


@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.select_related('author').all()
    form = CommentForm()
    user_liked = False
    user_bookmarked = False

    if request.user.is_authenticated:
        user_liked = Like.objects.filter(post=post, user=request.user).exists()
        user_bookmarked = Bookmark.objects.filter(post=post, user=request.user).exists()

        if request.method == 'POST':
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.post = post
                comment.author = request.user
                comment.save()
                award_badge(request.user, 'first_comment')
                # Notification
                if post.author != request.user:
                    Notification.objects.create(
                        recipient=post.author,
                        sender=request.user,
                        notification_type='comment',
                        post_reference=post,
                        text_preview=comment.content[:100],
                    )
                messages.success(request, 'Comment added!')
                return redirect('post-detail', pk=pk)

    return render(request, 'post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': form,
        'user_liked': user_liked,
        'user_bookmarked': user_bookmarked,
    })


@login_required
def update_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Post updated!')
            return redirect('post-detail', pk=post.pk)
    else:
        form = PostForm(instance=post, user=request.user)
    return render(request, 'update_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted.')
        return redirect('profile-detail', username=request.user.username)
    return render(request, 'confirm_delete.html', {'type': 'post', 'obj': post})


@login_required
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                notification_type='like_post',
                post_reference=post,
            )
        award_badges(post.author)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'total': post.total_likes()})
    return redirect('post-detail', pk=pk)


@login_required
def bookmark_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    bookmark, created = Bookmark.objects.get_or_create(post=post, user=request.user)
    if not created:
        bookmark.delete()
        bookmarked = False
    else:
        bookmarked = True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'bookmarked': bookmarked})
    return redirect('post-detail', pk=pk)


@login_required
def my_bookmarks(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('post', 'post__author')
    return render(request, 'bookmarks.html', {'bookmarks': bookmarks})


@login_required
def report_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if Report.objects.filter(post=post, reported_by=request.user).exists():
        messages.warning(request, 'You have already reported this post.')
        return redirect('post-detail', pk=pk)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.post = post
            report.reported_by = request.user
            report.save()
            messages.success(request, 'Report submitted. Thank you for keeping EchoNotes safe.')
            return redirect('post-detail', pk=pk)
    else:
        form = ReportForm()
    return render(request, 'report_post.html', {'form': form, 'post': post})


@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.author == request.user or request.user.is_staff:
        post_pk = comment.post.pk
        comment.delete()
        messages.success(request, 'Comment deleted.')
        return redirect('post-detail', pk=post_pk)
    messages.error(request, 'Permission denied.')
    return redirect('profile-detail', username=request.user.username)


# ─── Categories & Circles ─────────────────────────────────────────────────────

@login_required
def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)

    # Handle join/leave
    if request.user.is_authenticated:
        action = request.GET.get('action')
        if action == 'join':
            category.subscribers.add(request.user)
            messages.success(request, f'You joined the {category.name} circle!')
            return redirect('category-posts', slug=slug)
        elif action == 'leave':
            category.subscribers.remove(request.user)
            messages.info(request, f'You left the {category.name} circle.')
            return redirect('category-posts', slug=slug)

    is_member = request.user.is_authenticated and category.subscribers.filter(pk=request.user.pk).exists()
    posts = Post.objects.filter(category=category, status='published').order_by('-created_date')

    paginator = Paginator(posts, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'category_posts.html', {
        'category': category,
        'posts': page_obj,
        'is_member': is_member,
        'member_count': category.total_members(),
    })


@login_required
def mood_posts(request, mood):
    posts = Post.objects.filter(mood=mood, status='published').order_by('-created_date')
    return render(request, 'mood_posts.html', {'posts': posts, 'mood': mood})


@login_required
def circle_discovery(request):
    query = request.GET.get('q', '').strip()

    if query:
        categories = Category.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).annotate(
            member_count=Count('subscribers', distinct=True),
            post_count=Count('posts', distinct=True),
        )
        trending_circles = []
        new_circles = []
    else:
        # Trending: most new posts in past 7 days
        one_week_ago = timezone.now() - timedelta(days=7)
        trending_circles = Category.objects.annotate(
            member_count=Count('subscribers', distinct=True),
            recent_posts=Count('posts', filter=Q(posts__created_date__gte=one_week_ago), distinct=True),
        ).order_by('-recent_posts', '-member_count')[:6]

        # New: created in past 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_circles = Category.objects.filter(
            created_date__gte=thirty_days_ago
        ).annotate(
            member_count=Count('subscribers', distinct=True),
        ).order_by('-created_date')[:6]

        categories = Category.objects.annotate(
            member_count=Count('subscribers', distinct=True),
            post_count=Count('posts', distinct=True),
        ).order_by('-member_count')

    user_circles_ids = set()
    if request.user.is_authenticated:
        user_circles_ids = set(
            Category.objects.filter(subscribers=request.user).values_list('id', flat=True)
        )

    return render(request, 'circle_discovery.html', {
        'categories': categories,
        'trending_circles': trending_circles,
        'new_circles': new_circles,
        'query': query,
        'user_circles_ids': user_circles_ids,
    })


# ─── Profile ──────────────────────────────────────────────────────────────────


@login_required
def profile_detail(request, username):
    view_user = get_object_or_404(User, username=username)
    is_own_profile = request.user == view_user
    posts = Post.objects.filter(author=view_user, status='published').order_by('-created_date')
    is_following = False
    is_friend = False
    friend_request_sent = False
    friend_request_received = None

    if request.user.is_authenticated and request.user != view_user:
        is_following = Follow.objects.filter(follower=request.user, following=view_user).exists()
        is_friend = Friend.objects.filter(
            Q(user1=request.user, user2=view_user) | Q(user1=view_user, user2=request.user)
        ).exists()
        friend_request_sent = FriendRequest.objects.filter(
            sender=request.user, receiver=view_user, is_active=True
        ).exists()
        friend_request_received = FriendRequest.objects.filter(
            sender=view_user, receiver=request.user, is_active=True
        ).first()

    followers_count = Follow.objects.filter(following=view_user).count()
    following_count = Follow.objects.filter(follower=view_user).count()
    user_badges = UserBadge.objects.filter(user=view_user).select_related('badge')

    # Social Lists (Available for all visitors)
    friend_qs = Friend.objects.filter(Q(user1=view_user) | Q(user2=view_user))
    friends = []
    for f in friend_qs:
        other = f.user2 if f.user1 == view_user else f.user1
        friends.append(other)
    
    followers = Follow.objects.filter(following=view_user).select_related('follower', 'follower__profile')
    following_list = Follow.objects.filter(follower=view_user).select_related('following', 'following__profile')

    context = {
        'profile_user': view_user,
        'user_posts': posts,
        'post_count': posts.count(),
        'is_following': is_following,
        'is_friend': is_friend,
        'friend_request_sent': friend_request_sent,
        'friend_request_received': friend_request_received,
        'follower_count': followers_count,
        'following_count': following_count,
        'user_badges': user_badges,
        'streak': WritingStreak.objects.get_or_create(user=view_user)[0],
        'is_own_profile': is_own_profile,
        'friends': friends,
        'followers': followers,
        'following_list': following_list,
    }

    # ── If viewing own profile, load all dashboard data ──
    if is_own_profile:
        user = request.user

        # Handle Profile Update POST
        if request.method == 'POST':
            u_form = UserUpdateForm(request.POST, instance=user)
            p_form = ProfileUpdateForm(request.POST, request.FILES, instance=user.profile)
            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
                messages.success(request, 'Profile updated!')
                return redirect('profile-detail', username=user.username)
        else:
            u_form = UserUpdateForm(instance=user)
            p_form = ProfileUpdateForm(instance=user.profile)

        # Include drafts for own profile
        user_posts_all = Post.objects.filter(author=user).order_by('-created_date')
        context['user_posts'] = user_posts_all[:10]
        context['post_count'] = user_posts_all.count()
        context['draft_count'] = user_posts_all.filter(status='draft').count()

        # Stats
        total_likes_received = sum(p.total_likes() for p in user_posts_all)
        total_comments_received = sum(p.total_comments() for p in user_posts_all)
        context['total_likes_received'] = total_likes_received
        context['total_comments_received'] = total_comments_received

        # Activity feed
        following_ids = list(Follow.objects.filter(follower=user).values_list('following_id', flat=True))
        following_user_ids = set(following_ids)

        activity_items = []
        if following_ids:
            recent_posts_by_followed = Post.objects.filter(
                author_id__in=following_ids, status='published'
            ).order_by('-created_date')[:15]
            for p in recent_posts_by_followed:
                activity_items.append({
                    'type': 'post',
                    'user': p.author,
                    'text': f'published "{p.title}"',
                    'timestamp': p.created_date,
                    'post': p,
                })
            recent_likes = Like.objects.filter(
                user_id__in=following_ids
            ).select_related('user', 'post').order_by('-created_date')[:10]
            for like in recent_likes:
                activity_items.append({
                    'type': 'like',
                    'user': like.user,
                    'text': f'liked "{like.post.title}"',
                    'timestamp': like.created_date,
                    'post': like.post,
                })
            recent_comments = Comment.objects.filter(
                author_id__in=following_ids
            ).select_related('author', 'post').order_by('-created_date')[:10]
            for comment in recent_comments:
                activity_items.append({
                    'type': 'comment',
                    'user': comment.author,
                    'text': f'commented on "{comment.post.title}"',
                    'timestamp': comment.created_date,
                    'post': comment.post,
                })
            activity_items.sort(key=lambda x: x['timestamp'], reverse=True)
            activity_items = activity_items[:20]

        # Suggested users
        suggested_users = User.objects.filter(
            profile__is_ai=False
        ).exclude(id=user.id).exclude(id__in=following_ids).annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        ).order_by('-post_count')[:5]

        # Circle feed
        user_circles = list(Category.objects.filter(subscribers=user))
        user_circles_ids = set(c.id for c in user_circles)
        circle_feed = []
        if user_circles:
            circle_feed = Post.objects.filter(
                category__in=user_circles, status='published'
            ).select_related('author', 'category').order_by('-created_date')[:15]

        # Recommended circles
        recommended_circles = Category.objects.exclude(subscribers=user).annotate(
            member_count=Count('subscribers')
        ).order_by('-member_count')[:5]

        # Global feed
        global_feed = Post.objects.filter(status='published').exclude(
            author=user
        ).order_by('-created_date')[:15]

        # Friends & social (Pending requests are owner-only)
        pending_requests = FriendRequest.objects.filter(
            receiver=user, is_active=True
        ).select_related('sender', 'sender__profile')

        # Sidebar
        today_prompt = DailyPrompt.objects.filter(date=date.today(), is_active=True).first()
        today_word = WordOfTheDay.objects.filter(date=date.today()).first()
        latest_broadcast = AIBroadcast.objects.filter(is_active=True).first()
        feed_posts = Post.objects.filter(status='published').exclude(
            author=user
        ).order_by('-created_date')[:8]

        context.update({
            'u_form': u_form,
            'p_form': p_form,
            'activity_items': activity_items,
            'suggested_users': suggested_users,
            'following_user_ids': following_user_ids,
            'circle_feed': circle_feed,
            'global_feed': global_feed,
            'user_circles': user_circles,
            'user_circles_ids': user_circles_ids,
            'recommended_circles': recommended_circles,
            'friends': friends,
            'pending_requests': pending_requests,
            'followers': followers,
            'following_list': following_list,
            'today_prompt': today_prompt,
            'today_word': today_word,
            'latest_broadcast': latest_broadcast,
            'feed_posts': feed_posts,
            'user_entries': ContestEntry.objects.filter(author=user).count(),
        })

    return render(request, 'profile_detail.html', context)


@login_required
def delete_profile_pic(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.profile_pic = 'default.jpg'
        profile.save()
        messages.success(request, 'Profile picture removed.')
    return redirect('profile')


# ─── Follow ───────────────────────────────────────────────────────────────────

@login_required
def follow_user(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return redirect('profile-detail', username=username)

    follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if not created:
        follow.delete()
        following = False
    else:
        following = True
        Notification.objects.create(
            recipient=target,
            sender=request.user,
            notification_type='follow',
        )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'following': following,
            'followers_count': Follow.objects.filter(following=target).count(),
        })
    return redirect('profile-detail', username=username)


# ─── Friends ──────────────────────────────────────────────────────────────────

@login_required
def send_friend_request(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return redirect('profile-detail', username=username)

    is_friend = Friend.objects.filter(
        Q(user1=request.user, user2=target) | Q(user1=target, user2=request.user)
    ).exists()
    if is_friend:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'already_friends'})
        return redirect('profile-detail', username=username)

    req, created = FriendRequest.objects.get_or_create(sender=request.user, receiver=target)
    if created:
        Notification.objects.create(
            recipient=target,
            sender=request.user,
            notification_type='friend_request',
        )
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'sent'})
        messages.success(request, f'Friend request sent to {username}!')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'already_sent'})

    return redirect('profile-detail', username=username)


@login_required
def accept_friend_request(request, pk):
    freq = get_object_or_404(FriendRequest, pk=pk, receiver=request.user)
    freq.is_active = False
    freq.save()
    # Create friendship (order user1 < user2 by id)
    u1, u2 = sorted([request.user, freq.sender], key=lambda u: u.id)
    Friend.objects.get_or_create(user1=u1, user2=u2)
    Notification.objects.create(
        recipient=freq.sender,
        sender=request.user,
        notification_type='friend_accept',
    )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'accepted'})
    messages.success(request, f'You are now friends with {freq.sender.username}!')
    return redirect('profile-detail', username=request.user.username)


@login_required
def decline_friend_request(request, pk):
    freq = get_object_or_404(FriendRequest, pk=pk, receiver=request.user)
    freq.is_active = False
    freq.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'declined'})
    messages.info(request, 'Friend request declined.')
    return redirect('profile-detail', username=request.user.username)


@login_required
def remove_friend(request, username):
    target = get_object_or_404(User, username=username)
    Friend.objects.filter(
        Q(user1=request.user, user2=target) | Q(user1=target, user2=request.user)
    ).delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'removed'})
    messages.info(request, f'You are no longer friends with {username}.')
    return redirect('profile-detail', username=username)


# ─── Notifications ────────────────────────────────────────────────────────────

@login_required
def get_notifications(request):
    notifs = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).order_by('-created_date')[:20]
    data = [{
        'id': n.id,
        'type': n.notification_type,
        'sender': n.sender.username,
        'text_preview': n.text_preview,
        'post_id': n.post_reference_id,
        'created': n.created_date.strftime('%b %d, %H:%M'),
    } for n in notifs]
    return JsonResponse({'notifications': data, 'count': len(data)})


@login_required
@require_POST
def mark_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})


# ─── Messages (DMs) ──────────────────────────────────────────────────────────

@login_required
def inbox(request):
    # Get all unique conversations
    sent_to = DirectMessage.objects.filter(sender=request.user).values_list('recipient_id', flat=True).distinct()
    received_from = DirectMessage.objects.filter(recipient=request.user).values_list('sender_id', flat=True).distinct()
    contact_ids = set(list(sent_to) + list(received_from))
    contacts = User.objects.filter(id__in=contact_ids).exclude(id=request.user.id)

    # Most recent message per contact
    conversations = []
    for contact in contacts:
        last_msg = DirectMessage.objects.filter(
            Q(sender=request.user, recipient=contact) | Q(sender=contact, recipient=request.user)
        ).order_by('-created_date').first()
        unread = DirectMessage.objects.filter(
            sender=contact, recipient=request.user, is_read=False
        ).count()
        conversations.append({
            'partner': contact,
            'last_msg': last_msg,
            'unread': unread,
        })
    conversations.sort(key=lambda x: x['last_msg'].created_date if x['last_msg'] else timezone.now(), reverse=True)

    return render(request, 'inbox.html', {'conversations': conversations})


@login_required
@login_required
def conversation(request, username):
    partner = get_object_or_404(User, username=username)
    if request.method == 'POST':
        msg_text = request.POST.get('message', '').strip()
        if msg_text:
            dm = DirectMessage.objects.create(
                sender=request.user,
                recipient=partner,
                message=msg_text,
            )
            # Handle AJAX POST
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'ok',
                    'id': dm.id,
                    'message': dm.message,
                    'timestamp': dm.created_date.strftime('%H:%M'),
                    'is_me': True
                })
        return redirect('conversation', username=username)

    # Mark as read
    DirectMessage.objects.filter(sender=partner, recipient=request.user, is_read=False).update(is_read=True)
    dms_qs = DirectMessage.objects.filter(
        Q(sender=request.user, recipient=partner) | Q(sender=partner, recipient=request.user)
    ).order_by('created_date')

    last_id = dms_qs.last().id if dms_qs.exists() else 0

    return render(request, 'conversation.html', {
        'partner': partner,
        'dms': dms_qs,
        'last_id': last_id,
    })


@login_required
def get_dm_messages(request, username):
    partner = get_object_or_404(User, username=username)
    since = request.GET.get('since')
    qs = DirectMessage.objects.filter(
        Q(sender=request.user, recipient=partner) | Q(sender=partner, recipient=request.user)
    ).order_by('created_date')
    if since:
        qs = qs.filter(id__gt=since)
    DirectMessage.objects.filter(sender=partner, recipient=request.user, is_read=False).update(is_read=True)
    data = [{
        'id': m.id,
        'sender': m.sender.username,
        'message': m.message,
        'timestamp': m.created_date.strftime('%H:%M'),
        'is_me': m.sender == request.user,
    } for m in qs]
    return JsonResponse({'messages': data})


# ─── Contests ─────────────────────────────────────────────────────────────────

@login_required
def contest_list(request):
    active = Contest.objects.filter(status__in=['open', 'voting']).order_by('-created_date')
    past = Contest.objects.filter(status='closed').order_by('-created_date')[:10]
    return render(request, 'contest_list.html', {'active_contests': active, 'past_contests': past})


@login_required
def contest_detail(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    entries = contest.entries.all().annotate(vote_count=Count('votes')).order_by('-vote_count')
    user_entry = None
    user_voted_entry = None
    if request.user.is_authenticated:
        user_entry = ContestEntry.objects.filter(contest=contest, author=request.user).first()
        user_voted_entry = ContestVote.objects.filter(
            entry__contest=contest, voter=request.user
        ).first()
    return render(request, 'contest_detail.html', {
        'contest': contest,
        'entries': entries,
        'user_entry': user_entry,
        'user_voted_entry': user_voted_entry,
    })


@login_required
def submit_contest_entry(request, pk):
    contest = get_object_or_404(Contest, pk=pk)

    if contest.status == 'closed':
        messages.error(request, 'This contest is closed.')
        return redirect('contest-detail', pk=pk)
    if contest.status == 'voting':
        messages.error(request, 'This contest is in the voting phase — no more submissions.')
        return redirect('contest-detail', pk=pk)
    if timezone.now() > contest.submission_deadline:
        messages.error(request, 'The submission deadline has passed.')
        return redirect('contest-detail', pk=pk)
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


@login_required
def vote_contest_entry(request, entry_pk):
    entry = get_object_or_404(ContestEntry, pk=entry_pk)
    contest = entry.contest
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.method == 'POST':
        if not contest.is_voting():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Voting is not active for this contest.'}, status=400)
            messages.error(request, 'Voting is not active for this contest.')
            return redirect('contest-detail', pk=contest.pk)
            
        if entry.author == request.user:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'You cannot vote for your own entry.'}, status=400)
            messages.error(request, 'You cannot vote for your own entry.')
            return redirect('contest-detail', pk=contest.pk)
            
        # Check if user already voted for ANY entry in THIS contest
        existing = ContestVote.objects.filter(entry__contest=contest, voter=request.user).first()
        
        if existing:
            if existing.entry == entry:
                # Toggle vote off
                existing.delete()
                voted = False
            else:
                # Change vote
                existing.entry = entry
                existing.save()
                voted = True
        else:
            ContestVote.objects.create(entry=entry, voter=request.user)
            voted = True
            
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'voted': voted,
                'total_votes': entry.total_votes(),
                'status': 'success'
            })
            
        messages.success(request, 'Vote cast!' if voted else 'Vote removed.')
        return redirect('contest-detail', pk=contest.pk)

    return redirect('contest-detail', pk=contest.pk)


# ─── Daily Prompt ─────────────────────────────────────────────────────────────

@login_required
def daily_prompt(request):
    prompt = DailyPrompt.objects.filter(date=date.today(), is_active=True).first()
    if not prompt:
        prompt = DailyPrompt.objects.filter(is_active=True).order_by('-date').first()

    responses = []
    user_response = None
    form = PromptResponseForm()

    if prompt:
        responses = PromptResponse.objects.filter(prompt=prompt).select_related('author').order_by('-created_date')
        if request.user.is_authenticated:
            user_response = PromptResponse.objects.filter(prompt=prompt, author=request.user).first()
            if request.method == 'POST' and not user_response:
                form = PromptResponseForm(request.POST)
                if form.is_valid():
                    resp = form.save(commit=False)
                    resp.prompt = prompt
                    resp.author = request.user
                    resp.save()
                    messages.success(request, 'Your response has been shared!')
                    return redirect('daily-prompt')

    return render(request, 'daily_prompt.html', {
        'today_prompt': prompt,
        'responses': responses,
        'user_response': user_response,
        'form': form,
    })


@login_required
def like_prompt_response(request, pk):
    response = get_object_or_404(PromptResponse, pk=pk)
    like, created = PromptResponseLike.objects.get_or_create(response=response, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        if response.author != request.user:
            Notification.objects.create(
                recipient=response.author,
                sender=request.user,
                notification_type='like_prompt',
            )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'total': response.likes.count()})
    return redirect('daily-prompt')


# ─── Word of the Day ──────────────────────────────────────────────────────────

@login_required
def word_of_the_day(request):
    word = WordOfTheDay.objects.filter(date=date.today()).first()
    if not word:
        word = WordOfTheDay.objects.order_by('-date').first()

    entries = []
    user_entry = None
    form = WordEntryForm()

    if word:
        entries = WordOfTheDayEntry.objects.filter(word=word).select_related('author').order_by('-created_date')
        if request.user.is_authenticated:
            user_entry = WordOfTheDayEntry.objects.filter(word=word, author=request.user).first()
            if request.method == 'POST' and not user_entry:
                form = WordEntryForm(request.POST)
                if form.is_valid():
                    entry = form.save(commit=False)
                    entry.word = word
                    entry.author = request.user
                    entry.save()
                    award_badge(request.user, 'word_challenge')
                    messages.success(request, 'Entry submitted!')
                    return redirect('word-of-the-day')

    return render(request, 'word_of_the_day.html', {
        'today_word': word,
        'entries': entries,
        'user_entry': user_entry,
        'form': form,
    })


@login_required
def like_word_entry(request, pk):
    entry = get_object_or_404(WordOfTheDayEntry, pk=pk)
    like, created = WordEntryLike.objects.get_or_create(entry=entry, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        if entry.author != request.user:
            Notification.objects.create(
                recipient=entry.author,
                sender=request.user,
                notification_type='like_word',
            )
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'total': entry.likes.count()})
    return redirect('word-of-the-day')


# ─── Collaborative Stories ────────────────────────────────────────────────────

@login_required
def collaborative_stories(request):
    stories = CollaborativeStory.objects.filter(status='open').order_by('-created_date')
    return render(request, 'collaborative_stories.html', {'stories': stories})


@login_required
def create_collaborative_story(request):
    if request.method == 'POST':
        form = CollaborativeStoryForm(request.POST)
        if form.is_valid():
            story = form.save(commit=False)
            story.started_by = request.user
            story.save()
            # Save first paragraph
            first_para = form.cleaned_data.get('first_paragraph')
            if first_para:
                StoryParagraph.objects.create(
                    story=story,
                    author=request.user,
                    content=first_para,
                    order=1,
                )
            award_badge(request.user, 'collab_story')
            messages.success(request, 'Story created!')
            return redirect('story-detail', pk=story.pk)
    else:
        form = CollaborativeStoryForm()
    return render(request, 'create_story.html', {'form': form})


@login_required
def collaborative_story_detail(request, pk):
    story = get_object_or_404(CollaborativeStory, pk=pk)
    paragraphs = story.paragraphs.all().order_by('order')
    form = StoryParagraphForm()

    if request.user.is_authenticated and story.status == 'open':
        if request.method == 'POST':
            form = StoryParagraphForm(request.POST)
            if form.is_valid():
                para = form.save(commit=False)
                para.story = story
                para.author = request.user
                para.order = paragraphs.count() + 1
                para.save()
                award_badge(request.user, 'collab_story')
                messages.success(request, 'Paragraph added!')
                return redirect('story-detail', pk=pk)

    return render(request, 'story_detail.html', {
        'story': story,
        'paragraphs': paragraphs,
        'form': form,
    })


# ─── Writing Timer ────────────────────────────────────────────────────────────

@login_required
def writing_timer(request):
    sessions = WritingSession.objects.filter(user=request.user).order_by('-created_date')[:10]
    return render(request, 'writing_timer.html', {'sessions': sessions})


@login_required
@require_POST
def save_writing_session(request):
    try:
        data = json.loads(request.body)
        session = WritingSession.objects.create(
            user=request.user,
            duration_minutes=data.get('duration_minutes', 25),
            words_written=data.get('words_written', 0),
            completed=data.get('completed', False),
        )
        return JsonResponse({'status': 'ok', 'id': session.id})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# ─── Leaderboard ──────────────────────────────────────────────────────────────

@login_required
def leaderboard(request):
    period = request.GET.get('period', 'alltime')
    days = None
    if period == 'weekly':
        days = 7
    elif period == 'monthly':
        days = 30

    post_filter = Q(posts__status='published')
    if days:
        cutoff = timezone.now() - timedelta(days=days)
        post_filter &= Q(posts__created_date__gte=cutoff)

    # Real-time leaderboard from DB with template-matching names
    most_liked = User.objects.filter(
        profile__is_ai=False
    ).annotate(
        total_likes=Count('posts__likes', filter=post_filter, distinct=True)
    ).order_by('-total_likes')[:10]

    most_posts = User.objects.filter(
        profile__is_ai=False
    ).annotate(
        post_count=Count('posts', filter=post_filter, distinct=True)
    ).order_by('-post_count')[:10]

    most_comments = User.objects.filter(
        profile__is_ai=False
    ).annotate(
        comment_count=Count('comments', distinct=True)
    ).order_by('-comment_count')[:10]

    return render(request, 'leaderboard.html', {
        'most_liked': most_liked,
        'most_posts': most_posts,
        'most_comments': most_comments,
        'period': period,
    })


# ─── Badges ───────────────────────────────────────────────────────────────────

@login_required
def badges_page(request):
    all_badges = Badge.objects.all()
    user_badges = set(UserBadge.objects.filter(user=request.user).values_list('badge__name', flat=True))
    return render(request, 'badges.html', {
        'all_badges': all_badges,
        'user_badges': user_badges,
    })


# ─── Search ───────────────────────────────────────────────────────────────────

@login_required
def search(request):
    q = request.GET.get('q', '').strip()
    posts = []
    users = []
    categories = []
    if q:
        posts = Post.objects.filter(
            Q(title__icontains=q) | Q(content__icontains=q),
            status='published'
        ).order_by('-created_date')[:20]
        users = User.objects.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )[:10]
        categories = Category.objects.filter(name__icontains=q)[:10]
    return render(request, 'search_results.html', {
        'query': q,
        'posts': posts,
        'users': users,
        'categories': categories,
    })


# ─── Static Pages ─────────────────────────────────────────────────────────────

def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        messages.success(request, "Message received! We'll get back to you soon.")
        return redirect('contact')
    return render(request, 'contact.html')


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


# ─── Admin Panel ──────────────────────────────────────────────────────────────

def admin_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            messages.error(request, 'Admin access required.')
            return redirect('landing')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard(request):
    stats = {
        'total_posts': Post.objects.count(),
        'total_users': User.objects.count(),
        'total_comments': Comment.objects.count(),
        'pending_reports': Report.objects.filter(status='pending').count(),
        'active_contests': Contest.objects.filter(status__in=['open', 'voting']).count(),
    }
    return render(request, 'admin_dashboard.html', {'stats': stats})


@admin_required
def manage_users(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        target = get_object_or_404(User, pk=user_id)
        if request.POST.get('delete_user') and target != request.user:
            target.delete()
            messages.success(request, f'User "{target.username}" deleted.')
            return redirect('manage-users')
        if request.POST.get('toggle_staff') and target != request.user:
            target.is_staff = not target.is_staff
            target.save()
            status = 'granted' if target.is_staff else 'revoked'
            messages.success(request, f'Staff access {status} for {target.username}.')
            return redirect('manage-users')
    users = User.objects.select_related('profile').annotate(
        post_count=Count('posts')
    ).order_by('-date_joined')
    return render(request, 'manage_users.html', {'users': users})


@admin_required
def manage_posts(request):
    posts = Post.objects.select_related('author').order_by('-created_date')
    paginator = Paginator(posts, 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'manage_post.html', {'posts': page_obj})


@admin_required
def manage_reports(request):
    reports = Report.objects.select_related('post', 'reported_by').filter(status='pending')
    return render(request, 'manage_reports.html', {'reports': reports})


@admin_required
def review_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        report.admin_note = request.POST.get('admin_note', '')
        report.reviewed_by = request.user
        if action == 'resolve':
            report.status = 'resolved'
            report.post.is_flagged = True
            report.post.save()
        elif action == 'dismiss':
            report.status = 'dismissed'
        report.save()
        messages.success(request, 'Report reviewed.')
        return redirect('manage-reports')
    return render(request, 'review_report.html', {'report': report})


@admin_required
def manage_contests(request):
    contests = Contest.objects.all().order_by('-created_date')
    return render(request, 'manage_contests.html', {'contests': contests})


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
        contest.status = request.POST.get('status', contest.status)
        contest.save()
        messages.success(request, 'Contest status updated.')
    return redirect('manage-contests')


@admin_required
def declare_winner(request, pk):
    contest = get_object_or_404(Contest, pk=pk)
    if request.method == 'POST':
        entry_pk = request.POST.get('entry_pk')
        entry = get_object_or_404(ContestEntry, pk=entry_pk, contest=contest)
        contest.winner = entry
        contest.status = 'closed'
        contest.save()
        award_badge(entry.author, 'contest_winner')
        messages.success(request, f'Winner declared: {entry.author.username}!')
    return redirect('contest-detail', pk=pk)


@admin_required
def manage_prompts(request):
    prompts = DailyPrompt.objects.all().order_by('-date')
    return render(request, 'manage_prompts.html', {'prompts': prompts})


@admin_required
def manage_words(request):
    words = WordOfTheDay.objects.all().order_by('-date')
    return render(request, 'manage_words.html', {'words': words})


# ─── AI Features ──────────────────────────────────────────────────────────────

def ai_broadcast(request):
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
        'stats': {},
    })


@login_required
@require_POST
def generate_prompt_ai(request):
    import random
    from .ai_utils import call_gemini

    try:
        data = json.loads(request.body) if request.body else {}
        theme = data.get('theme', 'general creative writing')

        prompt_text = f"""Generate ONE writing prompt for a Filipino literary community called EchoNotes.
Theme: {theme}
- One sentence only, no numbering, no prefix
- Evocative, specific, emotionally resonant
Just the prompt text:"""

        response_text = call_gemini(prompt_text, max_tokens=100)
        if 'ERROR' in response_text:
            raise Exception(response_text)

        clean_prompt = response_text.replace('Just the prompt text:', '').strip().strip('"')
        return JsonResponse({'prompt': clean_prompt, 'success': True})

    except Exception as e:
        print(f'generate_prompt_ai failed: {e}')
        fallbacks = [
            'Write about a moment when silence said more than words ever could.',
            'Describe the smell of rain on a street you used to walk every day.',
            'Write a letter to the city that raised you.',
            'What does hope look like at 3 in the morning?',
            'Write about something you lost that you never told anyone about.',
        ]
        return JsonResponse({'prompt': random.choice(fallbacks), 'success': True, 'fallback': True})


@login_required
@require_POST
def generate_word_ai(request):
    import random
    from .ai_utils import call_gemini

    try:
        prompt_text = """Suggest ONE uncommon but beautiful English word suitable for Filipino literary writers.
Return ONLY JSON in this exact format: {"word": "...", "definition": "...", "example": "..."}
No markdown, no extra text."""

        response_text = call_gemini(prompt_text, max_tokens=150)
        data = json.loads(response_text)
        return JsonResponse({'success': True, **data})

    except Exception as e:
        print(f'generate_word_ai failed: {e}')
        fallbacks = [
            {'word': 'Saudade', 'definition': 'A deep emotional state of nostalgic longing.', 'example': 'She felt saudade for the streets of her childhood.'},
            {'word': 'Hiraeth', 'definition': 'A homesickness for a home you cannot return to.', 'example': 'His writing was filled with hiraeth for a simpler time.'},
            {'word': 'Serendipity', 'definition': 'The occurrence of events by chance in a happy way.', 'example': 'Their meeting was pure serendipity.'},
        ]
        return JsonResponse({'success': True, 'fallback': True, **random.choice(fallbacks)})




# ─── Init Admin ───────────────────────────────────────────────────────────────

def init_admin(request):
    if User.objects.filter(is_superuser=True).exists():
        return JsonResponse({'status': 'Admin already exists.'})
    try:
        user = User.objects.create_superuser('admin', 'admin@echonotes.com', 'Admin123!')
        return JsonResponse({'status': f'Admin created: {user.username}'})
    except Exception as e:
        return JsonResponse({'status': f'Error: {e}'})
