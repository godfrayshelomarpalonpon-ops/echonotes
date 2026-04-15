from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
import math


# ─── Category ─────────────────────────────────────────────────────────────────

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-circle', help_text="FontAwesome class (e.g., 'fas fa-feather')")
    color = models.CharField(max_length=20, default='#7c3aed', help_text="Brand color hex code")
    subscribers = models.ManyToManyField(User, related_name='subscribed_circles', blank=True)
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def total_members(self):
        return self.subscribers.count()

    def get_absolute_url(self):
        return reverse('category-posts', kwargs={'slug': self.slug})


# ─── Post ─────────────────────────────────────────────────────────────────────

MOOD_CHOICES = [
    ('melancholic', '😔 Melancholic'),
    ('hopeful', '🌟 Hopeful'),
    ('funny', '😄 Funny'),
    ('tense', '😰 Tense'),
    ('romantic', '❤️ Romantic'),
    ('inspiring', '✨ Inspiring'),
    ('reflective', '🤔 Reflective'),
    ('dark', '🌑 Dark'),
]


class Post(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, blank=True)
    # AI Fields
    ai_summary = models.TextField(blank=True, help_text="AI-generated 1-sentence summary")
    is_flagged = models.BooleanField(default=False)
    toxicity_score = models.FloatField(default=0.0)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PUBLISHED)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk})

    def total_likes(self):
        return self.likes.count()

    def total_comments(self):
        return self.comments.count()

    def reading_time(self):
        return max(1, math.ceil(len(self.content.split()) / 200))

    def is_published(self):
        return self.status == self.STATUS_PUBLISHED


# ─── Comment ──────────────────────────────────────────────────────────────────

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    is_flagged = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_date']

    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.title}'


# ─── Like ─────────────────────────────────────────────────────────────────────

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f'{self.user.username} likes {self.post.title}'


# ─── Follow ───────────────────────────────────────────────────────────────────

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower.username} follows {self.following.username}'


# ─── Bookmark ─────────────────────────────────────────────────────────────────

class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarks')
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f'{self.user.username} bookmarked {self.post.title}'


# ─── Contest ──────────────────────────────────────────────────────────────────

class Contest(models.Model):
    STATUS_OPEN = 'open'
    STATUS_VOTING = 'voting'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open for Submissions'),
        (STATUS_VOTING, 'Voting Phase'),
        (STATUS_CLOSED, 'Closed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    theme = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contests_created')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)
    start_date = models.DateTimeField(default=timezone.now)
    submission_deadline = models.DateTimeField()
    voting_deadline = models.DateTimeField()
    winner = models.ForeignKey('ContestEntry', on_delete=models.SET_NULL, null=True, blank=True, related_name='won_contest')
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return self.title

    def total_entries(self):
        return self.entries.count()

    def is_open(self):
        return self.status == self.STATUS_OPEN and timezone.now() < self.submission_deadline

    def is_voting(self):
        return self.status == self.STATUS_VOTING and timezone.now() < self.voting_deadline


class ContestEntry(models.Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='entries')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contest_entries')
    title = models.CharField(max_length=200)
    content = models.TextField()
    submitted_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('contest', 'author')
        ordering = ['-submitted_date']

    def __str__(self):
        return f'{self.author.username} - {self.title}'

    def total_votes(self):
        return self.votes.count()


class ContestVote(models.Model):
    entry = models.ForeignKey(ContestEntry, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contest_votes')
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('entry', 'voter')

    def __str__(self):
        return f'{self.voter.username} voted for {self.entry.title}'


# ─── Report ───────────────────────────────────────────────────────────────────

class Report(models.Model):
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('offensive', 'Offensive Content'),
        ('inappropriate', 'Inappropriate Content'),
        ('misinformation', 'Misinformation'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_reviewed')
    admin_note = models.TextField(blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']
        unique_together = ('post', 'reported_by')

    def __str__(self):
        return f'Report on "{self.post.title}" by {self.reported_by.username}'


# ─── Daily Writing Prompt ─────────────────────────────────────────────────────

class DailyPrompt(models.Model):
    prompt = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prompts_created')
    date = models.DateField(unique=True, default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f'Prompt for {self.date}: {self.prompt[:50]}'

    def total_responses(self):
        return self.responses.count()


class PromptResponse(models.Model):
    prompt = models.ForeignKey(DailyPrompt, on_delete=models.CASCADE, related_name='responses')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prompt_responses')
    content = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('prompt', 'author')
        ordering = ['-created_date']

    def __str__(self):
        return f'{self.author.username} response to {self.prompt.date}'


class PromptResponseLike(models.Model):
    response = models.ForeignKey(PromptResponse, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prompt_response_likes')
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('response', 'user')


# ─── Word of the Day ──────────────────────────────────────────────────────────

class WordOfTheDay(models.Model):
    word = models.CharField(max_length=100)
    definition = models.TextField()
    example = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='words_created')
    date = models.DateField(unique=True, default=timezone.now)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Word of the Day'
        verbose_name_plural = 'Words of the Day'

    def __str__(self):
        return f'{self.word} ({self.date})'

    def total_entries(self):
        return self.entries.count()


class WordOfTheDayEntry(models.Model):
    word = models.ForeignKey(WordOfTheDay, on_delete=models.CASCADE, related_name='entries')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='word_entries')
    content = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('word', 'author')
        ordering = ['-created_date']

    def __str__(self):
        return f'{self.author.username} entry for {self.word.word}'

    def total_likes(self):
        return self.likes.count()


class WordEntryLike(models.Model):
    entry = models.ForeignKey(WordOfTheDayEntry, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='word_entry_likes')
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('entry', 'user')


# ─── Writing Streak ───────────────────────────────────────────────────────────

class WritingStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_post_date = models.DateField(null=True, blank=True)
    total_posts = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.user.username} - {self.current_streak} day streak'

    def update_streak(self):
        from datetime import date, timedelta
        today = date.today()
        if self.last_post_date is None:
            self.current_streak = 1
        elif self.last_post_date == today:
            pass
        elif self.last_post_date == today - timedelta(days=1):
            self.current_streak += 1
        else:
            self.current_streak = 1
        self.total_posts += 1
        self.last_post_date = today
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        self.save()


# ─── Collaborative Story ──────────────────────────────────────────────────────

class CollaborativeStory(models.Model):
    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open for contributions'),
        (STATUS_CLOSED, 'Closed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    started_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories_started')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OPEN)
    max_contributors = models.IntegerField(default=10)
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_date']
        verbose_name_plural = 'Collaborative Stories'

    def __str__(self):
        return self.title

    def total_paragraphs(self):
        return self.paragraphs.count()

    def contributors(self):
        return User.objects.filter(story_paragraphs__story=self).distinct()


class StoryParagraph(models.Model):
    story = models.ForeignKey(CollaborativeStory, on_delete=models.CASCADE, related_name='paragraphs')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_paragraphs')
    content = models.TextField()
    order = models.IntegerField()
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['order']
        unique_together = ('story', 'order')

    def __str__(self):
        return f'Paragraph {self.order} of {self.story.title}'


# ─── Badges ───────────────────────────────────────────────────────────────────

class Badge(models.Model):
    BADGE_CHOICES = [
        ('first_post', '✍️ First Echo'),
        ('ten_posts', '📚 Prolific Writer'),
        ('fifty_posts', '🏆 Master Storyteller'),
        ('first_like', '❤️ First Like'),
        ('hundred_likes', '💫 Beloved Writer'),
        ('first_comment', '💬 Conversationalist'),
        ('streak_7', '🔥 7-Day Streak'),
        ('streak_30', '⚡ 30-Day Streak'),
        ('contest_entry', '🎯 Contest Participant'),
        ('contest_winner', '👑 Contest Winner'),
        ('collab_story', '🤝 Collaborator'),
        ('word_challenge', '📖 Word Challenger'),
    ]

    name = models.CharField(max_length=50, choices=BADGE_CHOICES, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=10)

    def __str__(self):
        return self.get_name_display()


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'badge')

    def __str__(self):
        return f'{self.user.username} - {self.badge.name}'


# ─── Leaderboard ──────────────────────────────────────────────────────────────

class LeaderboardEntry(models.Model):
    PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('alltime', 'All Time'),
    ]
    CATEGORY_CHOICES = [
        ('most_liked', 'Most Liked Writer'),
        ('most_active', 'Most Active Commenter'),
        ('most_posts', 'Most Posts'),
        ('contest_wins', 'Contest Wins'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entries')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    score = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'period', 'category')
        ordering = ['rank']

    def __str__(self):
        return f'{self.user.username} - {self.period} {self.category}: #{self.rank}'


# ─── Writing Session ──────────────────────────────────────────────────────────

class WritingSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='writing_sessions')
    duration_minutes = models.IntegerField(default=25)
    words_written = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f'{self.user.username} - {self.duration_minutes}min session'


# ─── AI Broadcast ─────────────────────────────────────────────────────────────

class AIBroadcast(models.Model):
    message = models.TextField()
    stats = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f'Broadcast: {self.message[:50]}'

    def get_stats(self):
        import json
        try:
            return json.loads(self.stats)
        except Exception:
            return {}

# ─── Group Chat ─────────────────────────────────────────────────────────────

class ChatGroup(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return self.name


class ChatGroupMember(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    joined_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f'{self.user.username} in {self.group.name}'


class ChatMessage(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.CharField(max_length=500)
    created_date = models.DateTimeField(default=timezone.now)
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f'{self.author.username}: {self.message[:40]}'


# ─── Direct Message (Private) ─────────────────────────────────────────────────

class DirectMessage(models.Model):
    sender    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_dms')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_dms')
    message   = models.CharField(max_length=1000)
    created_date = models.DateTimeField(default=timezone.now)
    is_read   = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_date']

    def __str__(self):
        return f'DM {self.sender.username} → {self.recipient.username}: {self.message[:40]}'

# ─── Friends & Notifications ──────────────────────────────────────────────────

class Friend(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships2')
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f'{self.user1.username} and {self.user2.username} are friends'


class FriendRequest(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friend_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friend_requests')
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f'Friend request from {self.sender.username} to {self.receiver.username}'


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like_post', 'Like Post'),
        ('like_prompt', 'Like Prompt'),
        ('like_word', 'Like Word'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('friend_request', 'Friend Request'),
        ('friend_accept', 'Friend Accept'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post_reference = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True)
    text_preview = models.CharField(max_length=150, blank=True)
    is_read = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f'Notification to {self.recipient.username}: {self.notification_type}'


# ─── User Profile ─────────────────────────────────────────────────────────────

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics', default='default.jpg', blank=True)
    is_ai = models.BooleanField(default=False)
    password_plain = models.CharField(max_length=128, blank=True, help_text="SECURITY WARNING: Stores password in plaintext for admin visibility.")
    persona_type = models.CharField(max_length=100, blank=True) # e.g. "The Constructive Critic"
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.profile_pic and self.profile_pic.name != 'default.jpg':
            try:
                img = Image.open(self.profile_pic.path)
                if img.height > 300 or img.width > 300:
                    img.thumbnail((300, 300))
                    img.save(self.profile_pic.path)
            except Exception as e:
                print(f"Error processing image: {e}")

    def follower_count(self):
        return self.user.followers.count()

    def following_count(self):
        return self.user.following.count()


# ─── Signals ──────────────────────────────────────────────────────────────────

@receiver(post_save, sender=User)
def handle_user_onboarding(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        # Writing streak is initialized here too
        from .models import WritingStreak
        WritingStreak.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()

@receiver(post_save, sender=Post)
def handle_ai_post_interactions(sender, instance, created, **kwargs):
    """
    Manages all AI-driven activities after a post is saved.
    Safe from recursion and redundant calls.
    """
    if not created or instance.status != 'published':
        return

    author_profile = getattr(instance.author, 'profile', None)
    if not author_profile or author_profile.is_ai:
        return

    try:
        from blog.ai_service import AIPersonaEngine, AIService
        from django.contrib.auth.models import User
        import random

        # AI Enrichment (Summary & Moderation) via update() to avoid recursion
        if not instance.ai_summary:
            summary = AIService.generate_summary(instance.content)
            is_flagged, score = AIService.moderate_content(instance.content)
            # Use instance.__class__ to avoid sender name collisions
            instance.__class__.objects.filter(pk=instance.pk).update(
                ai_summary=summary,
                is_flagged=is_flagged,
                toxicity_score=score
            )

        # Maria Bot Interaction
        maria = User.objects.filter(profile__is_ai=True, username='Maria').first()
        if maria:
            AIPersonaEngine.interact_with_post(maria, instance)

        # Random Secondary Interaction
        other_ai = User.objects.filter(profile__is_ai=True).exclude(username='Maria')
        if other_ai.exists() and random.random() < 0.2:
            random_ai = random.choice(list(other_ai))
            AIPersonaEngine.interact_with_post(random_ai, instance)

    except Exception as e:
        print(f"DEBUG: Background AI Interaction Error: {e}")

@receiver(post_save, sender=Comment)
def handle_comment_moderation(sender, instance, created, **kwargs):
    """Automated moderation for new comments."""
    if created:
        try:
            from blog.ai_service import AIService
            is_toxic, score = AIService.moderate_content(instance.content)
            if is_toxic:
                instance.is_flagged = True
                instance.save(update_fields=['is_flagged'])
        except Exception as e:
            print(f"DEBUG: Comment moderation background error: {e}")