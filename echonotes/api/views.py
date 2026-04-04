from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db.models import Count, Q
from blog.models import Post, Comment, Like, UserProfile
from .serializers import (
    PostSerializer, PostListSerializer,
    CommentSerializer, UserSerializer, LikeSerializer,
)


# ─── Permission Helpers ───────────────────────────────────────────────────────

class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """Allow read to everyone; write only to the object's author or staff."""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        author = getattr(obj, 'author', None)
        return author == request.user or request.user.is_staff


# ─── Post Endpoints ───────────────────────────────────────────────────────────

class PostListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/posts/        → list all posts (newest first)
    POST /api/posts/        → create a new post (auth required)
    """
    queryset = Post.objects.all().order_by('-created_date')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PostListSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/posts/<pk>/  → retrieve a single post with comments
    PUT    /api/posts/<pk>/  → update (author/admin only)
    DELETE /api/posts/<pk>/  → delete (author/admin only)
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]


class PopularPostsAPIView(generics.ListAPIView):
    """GET /api/posts/popular/ → top 6 most-liked posts"""
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Post.objects.annotate(
            like_count=Count('likes')
        ).order_by('-like_count', '-created_date')[:6]


class SearchPostsAPIView(generics.ListAPIView):
    """GET /api/posts/search/?q=<term> → search posts by title/content/author"""
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        query = self.request.query_params.get('q', '').strip()
        if not query:
            return Post.objects.none()
        return Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(author__username__icontains=query)
        ).order_by('-created_date')


# ─── Like Endpoint ────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def like_post_api(request, pk):
    """
    POST /api/posts/<pk>/like/
    Toggles like on a post. Returns JSON with liked status and total count.
    This is the endpoint used by the AJAX like button in post_detail.html.
    """
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if not created:
        like.delete()
        liked = False
        message = 'Post unliked'
    else:
        liked = True
        message = 'Post liked'

    return Response({
        'liked': liked,
        'total_likes': post.total_likes(),
        'message': message,
    })


# ─── Comment Endpoints ────────────────────────────────────────────────────────

class CommentListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/posts/<pk>/comments/   → list comments for a post
    POST /api/posts/<pk>/comments/   → add a comment (auth required)
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs['pk']).order_by('created_date')

    def perform_create(self, serializer):
        post = Post.objects.get(pk=self.kwargs['pk'])
        serializer.save(author=self.request.user, post=post)


class CommentDestroyAPIView(generics.DestroyAPIView):
    """DELETE /api/comments/<pk>/ → delete a comment (author/admin only)"""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrAdminOrReadOnly]


# ─── User / Profile Endpoints ─────────────────────────────────────────────────

class UserProfileAPIView(generics.RetrieveAPIView):
    """GET /api/users/<username>/ → public profile + posts"""
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'username'
    queryset = User.objects.all()


class CurrentUserAPIView(APIView):
    """GET /api/me/ → current authenticated user's data"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)


# ─── Stats Endpoint ───────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def site_stats(request):
    """GET /api/stats/ → site-wide counts (used by landing page)"""
    return Response({
        'total_posts': Post.objects.count(),
        'total_users': User.objects.count(),
        'total_comments': Comment.objects.count(),
        'total_likes': Like.objects.count(),
    })