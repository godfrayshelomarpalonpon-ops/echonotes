from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),

    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),


    # Direct Messages (Private)
    path('messages/', views.inbox, name='inbox'),
    path('messages/<str:username>/', views.conversation, name='conversation'),
    path('messages/<str:username>/poll/', views.get_dm_messages, name='get_dm_messages'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.profile_detail, name='profile-detail'),
    path('delete-profile-pic/', views.delete_profile_pic, name='delete-profile-pic'),

    # Follow
    path('follow/<str:username>/', views.follow_user, name='follow-user'),

    # Posts
    path('post/new/', views.create_post, name='create-post'),
    path('post/<int:pk>/', views.post_detail, name='post-detail'),
    path('post/<int:pk>/update/', views.update_post, name='update-post'),
    path('post/<int:pk>/delete/', views.delete_post, name='delete-post'),
    path('post/<int:pk>/like/', views.like_post, name='like-post'),
    path('post/<int:pk>/bookmark/', views.bookmark_post, name='bookmark-post'),
    path('post/<int:pk>/report/', views.report_post, name='report-post'),

    # Bookmarks
    path('bookmarks/', views.my_bookmarks, name='my-bookmarks'),

    # Categories & Moods
    path('category/<slug:slug>/', views.category_posts, name='category-posts'),
    path('mood/<str:mood>/', views.mood_posts, name='mood-posts'),

    # Comments
    path('comment/<int:pk>/delete/', views.delete_comment, name='delete-comment'),

    # Contests
    path('contests/', views.contest_list, name='contest-list'),
    path('contests/<int:pk>/', views.contest_detail, name='contest-detail'),
    path('contests/<int:pk>/enter/', views.submit_contest_entry, name='contest-enter'),
    path('contests/vote/<int:entry_pk>/', views.vote_contest_entry, name='contest-vote'),

    # ── Interactive Features ──────────────────────────────────

    # 1. Daily Prompt
    path('prompt/', views.daily_prompt, name='daily-prompt'),
    path('prompt/like/<int:pk>/', views.like_prompt_response, name='like-prompt-response'),

    # 2. Word of the Day
    path('word/', views.word_of_the_day, name='word-of-the-day'),
    path('word/like/<int:pk>/', views.like_word_entry, name='like-word-entry'),

    # 3. Collaborative Stories
    path('stories/', views.collaborative_stories, name='story-list'),
    path('stories/new/', views.create_collaborative_story, name='create-story'),
    path('stories/<int:pk>/', views.collaborative_story_detail, name='story-detail'),

    # 4. Writing Timer
    path('timer/', views.writing_timer, name='writing-timer'),
    path('timer/save/', views.save_writing_session, name='save-session'),

    # 5. Leaderboard
    path('leaderboard/', views.leaderboard, name='leaderboard'),

    # 6. Badges
    path('badges/', views.badges_page, name='badges'),

    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('manage/users/', views.manage_users, name='manage-users'),
    path('manage/posts/', views.manage_posts, name='manage-posts'),
    path('manage/reports/', views.manage_reports, name='manage-reports'),
    path('manage/reports/<int:pk>/review/', views.review_report, name='review-report'),
    path('manage/contests/', views.manage_contests, name='manage-contests'),
    path('manage/contests/create/', views.create_contest, name='create-contest'),
    path('manage/contests/<int:pk>/status/', views.update_contest_status, name='contest-status'),
    path('manage/contests/<int:pk>/winner/', views.declare_winner, name='declare-winner'),
    path('manage/prompts/', views.manage_prompts, name='manage-prompts'),
    path('manage/words/', views.manage_words, name='manage-words'),

    # Search
    path('search/', views.search, name='search'),

    # Static
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy-policy/', views.privacy_policy, name='privacy-policy'),

    path('ai-broadcast/', views.ai_broadcast, name='ai-broadcast'),
    path('prompt/generate/', views.generate_prompt_ai, name='generate-prompt-ai'),
    path('word/generate/', views.generate_word_ai, name='generate-word-ai'),

    # ── Friend System ─────────────────────────────────────────────
    path('friend/request/<str:username>/', views.send_friend_request, name='send-friend-request'),
    path('friend/accept/<int:pk>/', views.accept_friend_request, name='accept-friend-request'),
    path('friend/decline/<int:pk>/', views.decline_friend_request, name='decline-friend-request'),
    path('friend/remove/<str:username>/', views.remove_friend, name='remove-friend'),

    # ── Notifications ─────────────────────────────────────────────
    path('notifications/', views.get_notifications, name='get-notifications'),
    path('notifications/read/', views.mark_notifications_read, name='mark-notifications-read'),
]
