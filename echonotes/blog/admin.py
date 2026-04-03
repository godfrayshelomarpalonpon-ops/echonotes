from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import (
    Post, Comment, Like, Category, Contest, ContestEntry, Report,
    DailyPrompt, WordOfTheDay, CollaborativeStory, Badge, WritingStreak,
)
from .badges import ensure_badges_exist


def block_users(modeladmin, request, queryset):
    queryset.exclude(is_superuser=True).update(is_active=False)
    modeladmin.message_user(request, "Selected users have been blocked.")
block_users.short_description = "Block selected users"


def unblock_users(modeladmin, request, queryset):
    queryset.update(is_active=True)
    modeladmin.message_user(request, "Selected users have been unblocked.")
unblock_users.short_description = "Unblock selected users"


class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'mood', 'status', 'created_date', 'get_total_likes')
    list_filter = ('status', 'category', 'mood', 'created_date')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('title', 'content', 'author', 'category', 'status', 'created_date')

    def get_total_likes(self, obj):
        return obj.total_likes()
    get_total_likes.short_description = 'Likes'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_date')
    search_fields = ('content', 'author__username')
    readonly_fields = ('post', 'author', 'content', 'created_date')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class LikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_date')
    search_fields = ('user__username', 'post__title')
    readonly_fields = ('post', 'user', 'created_date')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class ContestAdmin(admin.ModelAdmin):
    list_display = ('title', 'theme', 'status', 'total_entries', 'submission_deadline')
    list_filter = ('status',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ReportAdmin(admin.ModelAdmin):
    list_display = ('post', 'reported_by', 'reason', 'status', 'created_date')
    list_filter = ('status', 'reason')
    readonly_fields = ('post', 'reported_by', 'reason', 'description', 'created_date')


class DailyPromptAdmin(admin.ModelAdmin):
    list_display = ('date', 'prompt_preview', 'total_responses', 'is_active')
    list_filter = ('is_active',)

    def prompt_preview(self, obj):
        return obj.prompt[:60] + '...' if len(obj.prompt) > 60 else obj.prompt
    prompt_preview.short_description = 'Prompt'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class WordOfTheDayAdmin(admin.ModelAdmin):
    list_display = ('date', 'word', 'total_entries')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'description')

    def get_queryset(self, request):
        ensure_badges_exist()
        return super().get_queryset(request)


class WritingStreakAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_streak', 'longest_streak', 'total_posts', 'last_post_date')
    search_fields = ('user__username',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'account_status', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    actions = [block_users, unblock_users]

    def account_status(self, obj):
        return '✅ Active' if obj.is_active else '🚫 Blocked'
    account_status.short_description = 'Status'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Like, LikeAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Contest, ContestAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(DailyPrompt, DailyPromptAdmin)
admin.site.register(WordOfTheDay, WordOfTheDayAdmin)
admin.site.register(Badge, BadgeAdmin)
admin.site.register(WritingStreak, WritingStreakAdmin)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
