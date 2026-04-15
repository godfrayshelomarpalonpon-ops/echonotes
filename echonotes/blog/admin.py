from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    Post, Comment, Like, Category, Contest, ContestEntry, Report,
    DailyPrompt, WordOfTheDay, CollaborativeStory, StoryParagraph, 
    Badge, WritingStreak, UserProfile, Follow, Bookmark,
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
    list_display = ('title', 'author', 'category', 'status_badge', 'created_date', 'get_total_likes')
    list_filter = ('status', 'category', 'mood', 'created_date')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('author', 'category', 'created_date')

    def status_badge(self, obj):
        colors = {
            'published': '#28a745',
            'draft': '#6c757d',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def get_total_likes(self, obj):
        return obj.total_likes()
    get_total_likes.short_description = 'Likes'

    def has_add_permission(self, request):
        return False


class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_date', 'content_preview')
    search_fields = ('content', 'author__username')
    readonly_fields = ('post', 'author', 'content', 'created_date')

    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

    def has_add_permission(self, request):
        return False


class LikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_date')
    search_fields = ('user__username', 'post__title')
    readonly_fields = ('post', 'user', 'created_date')

    def has_add_permission(self, request):
        return False


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count')
    prepopulated_fields = {'slug': ('name',)}

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Posts'


class ContestAdmin(admin.ModelAdmin):
    list_display = ('title', 'theme', 'status_badge', 'total_entries', 'submission_deadline')
    list_filter = ('status',)

    def status_badge(self, obj):
        colors = {
            'open': '#007bff',
            'voting': '#ffc107',
            'closed': '#dc3545',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ReportAdmin(admin.ModelAdmin):
    list_display = ('post', 'reported_by', 'reason', 'status_badge', 'created_date')
    list_filter = ('status', 'reason')
    readonly_fields = ('post', 'reported_by', 'reason', 'description', 'created_date')

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'reviewed': '#17a2b8',
            'resolved': '#28a745',
            'dismissed': '#6c757d',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


class DailyPromptAdmin(admin.ModelAdmin):
    list_display = ('date', 'prompt_preview', 'total_responses', 'is_active')
    list_filter = ('is_active',)

    def prompt_preview(self, obj):
        return obj.prompt[:50] + ("..." if len(obj.prompt) > 50 else "")

    def total_responses(self, obj):
        return obj.responses.count()

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


class CollaborativeStoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'started_by', 'status', 'total_paragraphs', 'created_date')
    list_filter = ('status',)


class StoryParagraphAdmin(admin.ModelAdmin):
    list_display = ('story', 'author', 'order', 'created_date')
    readonly_fields = ('story', 'author', 'order', 'created_date')


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    readonly_fields = ('password_plain',)
    verbose_name_plural = 'Profile Info'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, )
    list_display = ('username', 'email', 'is_staff', 'account_status', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    actions = [block_users, unblock_users]

    def account_status(self, obj):
        color = '#28a745' if obj.is_active else '#dc3545'
        text = 'Active' if obj.is_active else 'Blocked'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, text
        )
    account_status.short_description = 'Status'

    def has_add_permission(self, request):
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
admin.site.register(CollaborativeStory, CollaborativeStoryAdmin)
admin.site.register(StoryParagraph, StoryParagraphAdmin)

admin.site.register(Follow)
admin.site.register(Bookmark)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

