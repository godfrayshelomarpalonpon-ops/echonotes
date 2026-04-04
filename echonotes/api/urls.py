from django.urls import path
from . import views

urlpatterns = [
    # Posts
    path('posts/', views.PostListCreateAPIView.as_view(), name='api-post-list'),
    path('posts/popular/', views.PopularPostsAPIView.as_view(), name='api-post-popular'),
    path('posts/search/', views.SearchPostsAPIView.as_view(), name='api-post-search'),
    path('posts/<int:pk>/', views.PostDetailAPIView.as_view(), name='api-post-detail'),
    path('posts/<int:pk>/like/', views.like_post_api, name='api-like-post'),

    # Comments
    path('posts/<int:pk>/comments/', views.CommentListCreateAPIView.as_view(), name='api-comment-list'),
    path('comments/<int:pk>/', views.CommentDestroyAPIView.as_view(), name='api-comment-delete'),

    # Users
    path('users/<str:username>/', views.UserProfileAPIView.as_view(), name='api-user-profile'),
    path('me/', views.CurrentUserAPIView.as_view(), name='api-me'),

    # Stats
    path('stats/', views.site_stats, name='api-stats'),
]