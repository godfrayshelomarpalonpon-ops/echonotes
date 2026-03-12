from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Post, Comment, Like, UserProfile
from .forms import (
    UserRegisterForm, UserUpdateForm, ProfileUpdateForm,
    PostForm, CommentForm
)
from .decorators import admin_required

# Landing Page
def landing(request):
    """Landing page - visible to everyone"""
    recent_posts = Post.objects.all()[:6]  # Show 6 most recent posts
    popular_posts = Post.objects.annotate(
        like_count=Count('likes')
    ).order_by('-like_count', '-created_date')[:6]
    
    context = {
        'recent_posts': recent_posts,
        'popular_posts': popular_posts,
        'total_posts': Post.objects.count(),
        'total_users': UserProfile.objects.count(),
    }
    return render(request, 'landing.html', context)

# Authentication Views
def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.get_or_create(user=user)
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')

def logout_view(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('landing')

# Dashboard (User Home)
@login_required
def dashboard(request):
    """User dashboard showing their posts and feed"""
    user_posts = Post.objects.filter(author=request.user).order_by('-created_date')
    feed_posts = Post.objects.exclude(author=request.user).order_by('-created_date')[:20]
    
    # Calculate total likes and comments
    total_likes_received = 0
    total_comments_received = 0
    for post in user_posts:
        total_likes_received += post.total_likes()
        total_comments_received += post.total_comments()
    
    context = {
        'user_posts': user_posts,
        'feed_posts': feed_posts,
        'post_count': user_posts.count(),
        'total_likes_received': total_likes_received,
        'total_comments_received': total_comments_received,
    }
    return render(request, 'dashboard.html', context)

# Profile Views
@login_required
def profile(request):
    """User profile view and edit"""
    # Create profile if it doesn't exist
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)
    
    user_posts = Post.objects.filter(author=request.user).order_by('-created_date')[:5]
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'user_posts': user_posts,
    }
    return render(request, 'profile.html', context)

@login_required
def profile_detail(request, username):
    """View another user's profile"""
    user = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(author=user).order_by('-created_date')
    
    context = {
        'profile_user': user,
        'user_posts': user_posts,
        'post_count': user_posts.count(),
    }
    return render(request, 'profile_detail.html', context)

# Post Views
@login_required
def create_post(request):
    """Create a new post"""
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Your post has been created!')
            return redirect('post-detail', pk=post.pk)
    else:
        form = PostForm()
    
    return render(request, 'create_post.html', {'form': form})

def post_detail(request, pk):
    """View a single post with comments"""
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all()
    
    # Check if user liked the post
    user_liked = False
    if request.user.is_authenticated:
        user_liked = Like.objects.filter(post=post, user=request.user).exists()
    
    # Comment form
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Your comment has been added!')
            return redirect('post-detail', pk=post.pk)
    else:
        comment_form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'user_liked': user_liked,
    }
    return render(request, 'post_detail.html', context)

@login_required
def update_post(request, pk):
    """Update a post"""
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user is author
    if post.author != request.user and not request.user.is_staff:
        messages.error(request, 'You can only edit your own posts!')
        return redirect('post-detail', pk=post.pk)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your post has been updated!')
            return redirect('post-detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'update_post.html', {'form': form, 'post': post})

@login_required
def delete_post(request, pk):
    """Delete a post"""
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user is author or admin
    if post.author != request.user and not request.user.is_staff:
        messages.error(request, 'You can only delete your own posts!')
        return redirect('post-detail', pk=post.pk)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Your post has been deleted!')
        return redirect('dashboard')
    
    return render(request, 'confirm_delete.html', {'obj': post, 'type': 'post'})

# Comment Views
@login_required
def delete_comment(request, pk):
    """Delete a comment"""
    comment = get_object_or_404(Comment, pk=pk)
    
    # Check if user is author or admin
    if comment.author != request.user and not request.user.is_staff:
        messages.error(request, 'You can only delete your own comments!')
        return redirect('post-detail', pk=comment.post.pk)
    
    if request.method == 'POST':
        post_pk = comment.post.pk
        comment.delete()
        messages.success(request, 'Your comment has been deleted!')
        return redirect('post-detail', pk=post_pk)
    
    return render(request, 'confirm_delete.html', {'obj': comment, 'type': 'comment'})

# Like Views
@login_required
@require_POST
def like_post(request, pk):
    """Like or unlike a post (AJAX)"""
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    
    if not created:
        # User already liked, so unlike
        like.delete()
        liked = False
        message = 'Post unliked'
    else:
        liked = True
        message = 'Post liked'
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'total_likes': post.total_likes(),
            'message': message
        })
    
    return redirect('post-detail', pk=post.pk)

# Profile Picture Delete View
@login_required
def delete_profile_pic(request):
    """Delete profile picture"""
    if request.method == 'GET':
        try:
            profile = request.user.profile
            if profile.profile_pic and profile.profile_pic.name != 'default.jpg':
                # Delete the file from storage
                profile.profile_pic.delete()
                # Set to default
                profile.profile_pic = 'default.jpg'
                profile.save()
                messages.success(request, 'Profile picture deleted successfully!')
            else:
                messages.info(request, 'No custom profile picture to delete.')
        except UserProfile.DoesNotExist:
            messages.error(request, 'Profile not found.')
        
        return redirect('profile')

# Admin Views
@admin_required
def admin_dashboard(request):
    """Admin dashboard for monitoring"""
    total_users = User.objects.count()
    total_posts = Post.objects.count()
    total_comments = Comment.objects.count()
    total_likes = Like.objects.count()
    
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_posts = Post.objects.order_by('-created_date')[:10]
    recent_comments = Comment.objects.order_by('-created_date')[:10]
    
    context = {
        'total_users': total_users,
        'total_posts': total_posts,
        'total_comments': total_comments,
        'total_likes': total_likes,
        'recent_users': recent_users,
        'recent_posts': recent_posts,
        'recent_comments': recent_comments,
    }
    return render(request, 'admin_dashboard.html', context)

@admin_required
def manage_users(request):
    """Manage users (admin only)"""
    users = User.objects.all().order_by('-date_joined')
    
    # Handle user deletion
    if request.method == 'POST' and 'delete_user' in request.POST:
        user_id = request.POST.get('user_id')
        user_to_delete = get_object_or_404(User, id=user_id)
        
        # Don't allow deleting yourself
        if user_to_delete == request.user:
            messages.error(request, 'You cannot delete your own account!')
        else:
            username = user_to_delete.username
            user_to_delete.delete()
            messages.success(request, f'User {username} has been deleted.')
        
        return redirect('manage-users')
    
    context = {
        'users': users,
    }
    return render(request, 'manage_users.html', context)

@admin_required
def manage_posts(request):
    """Manage all posts (admin only)"""
    posts = Post.objects.all().order_by('-created_date')
    
    context = {
        'posts': posts,
    }
    return render(request, 'manage_posts.html', context)

# Search
def search(request):
    """Search posts"""
    query = request.GET.get('q', '')
    if query:
        posts = Post.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(author__username__icontains=query)
        ).order_by('-created_date')
    else:
        posts = Post.objects.none()
    
    context = {
        'query': query,
        'posts': posts,
        'result_count': posts.count(),
    }
    return render(request, 'search_results.html', context)

    # Static Pages
def about(request):
    """About page"""
    return render(request, 'about.html')

def contact(request):
    """Contact page"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you would typically send an email or save to database
        # For now, just show a success message
        messages.success(request, f'Thank you {name}! Your message has been sent. We\'ll get back to you soon.')
        return redirect('contact')
    
    return render(request, 'contact.html')

def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'privacy_policy.html')