from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Post, Comment, Like, UserProfile

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_date', 'total_likes', 'total_comments')
    list_filter = ('created_date', 'author')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_date'
    ordering = ('-created_date',)
    
    def total_likes(self, obj):
        return obj.total_likes()
    total_likes.short_description = 'Likes'
    
    def total_comments(self, obj):
        return obj.total_comments()
    total_comments.short_description = 'Comments'

class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_date', 'content_preview')
    list_filter = ('created_date', 'author')
    search_fields = ('content',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

class LikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_date')
    list_filter = ('created_date',)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_date')
    search_fields = ('user__username', 'user__email')

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

# Register your models here
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Like, LikeAdmin)
admin.site.register(UserProfile, UserProfileAdmin)

# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
