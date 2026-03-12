from django.urls import path
from . import views

urlpatterns = [
    # Landing page
    path('', views.landing, name='landing'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.profile_detail, name='profile-detail'),
    path('delete-profile-pic/', views.delete_profile_pic, name='delete-profile-pic'),
    
    # Posts
    path('post/new/', views.create_post, name='create-post'),
    path('post/<int:pk>/', views.post_detail, name='post-detail'),
    path('post/<int:pk>/update/', views.update_post, name='update-post'),
    path('post/<int:pk>/delete/', views.delete_post, name='delete-post'),
    path('post/<int:pk>/like/', views.like_post, name='like-post'),
    
    # Comments
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete-comment'),
    
    # Admin pages
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin/users/', views.manage_users, name='manage-users'),
    path('admin/posts/', views.manage_posts, name='manage-posts'),
    
    # Search
    path('search/', views.search, name='search'),
    
    # Static pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy-policy/', views.privacy_policy, name='privacy-policy'),
]