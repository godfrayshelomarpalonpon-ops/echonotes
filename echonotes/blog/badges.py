"""
Badge awarding system — call award_badges(user) after any relevant action.
"""
from .models import Badge, UserBadge, WritingStreak


BADGE_DEFINITIONS = [
    ('first_post',      '✍️',  'Published your first post on EchoNotes.'),
    ('ten_posts',       '📚',  'Published 10 posts. You are a prolific writer!'),
    ('fifty_posts',     '🏆',  'Published 50 posts. A true master storyteller.'),
    ('first_like',      '❤️',  'Received your first like from the community.'),
    ('hundred_likes',   '💫',  'Received 100 likes across all your posts.'),
    ('first_comment',   '💬',  'Left your first comment on a post.'),
    ('streak_7',        '🔥',  'Maintained a 7-day writing streak.'),
    ('streak_30',       '⚡',  'Maintained a 30-day writing streak. Incredible!'),
    ('contest_entry',   '🎯',  'Submitted an entry to a writing contest.'),
    ('contest_winner',  '👑',  'Won a writing contest. Champion!'),
    ('collab_story',    '🤝',  'Contributed to a collaborative story.'),
    ('word_challenge',  '📖',  'Participated in the Word of the Day challenge.'),
]


def ensure_badges_exist():
    for name, icon, description in BADGE_DEFINITIONS:
        Badge.objects.get_or_create(
            name=name,
            defaults={'icon': icon, 'description': description}
        )


def award_badge(user, badge_name):
    ensure_badges_exist()
    try:
        badge = Badge.objects.get(name=badge_name)
        _, created = UserBadge.objects.get_or_create(user=user, badge=badge)
        return created
    except Badge.DoesNotExist:
        return False


def award_badges(user):
    """Call this after any user action to check and award eligible badges."""
    from .models import Post, Comment, Like
    from django.db.models import Sum

    # Post count badges
    post_count = Post.objects.filter(author=user, status='published').count()
    if post_count >= 1:
        award_badge(user, 'first_post')
    if post_count >= 10:
        award_badge(user, 'ten_posts')
    if post_count >= 50:
        award_badge(user, 'fifty_posts')

    # Like badges
    total_likes = sum(p.total_likes() for p in Post.objects.filter(author=user))
    if total_likes >= 1:
        award_badge(user, 'first_like')
    if total_likes >= 100:
        award_badge(user, 'hundred_likes')

    # Comment badges
    if Comment.objects.filter(author=user).exists():
        award_badge(user, 'first_comment')

    # Streak badges
    try:
        streak = user.streak
        if streak.current_streak >= 7:
            award_badge(user, 'streak_7')
        if streak.current_streak >= 30:
            award_badge(user, 'streak_30')
    except Exception:
        pass
