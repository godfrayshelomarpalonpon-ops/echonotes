"""
Management command: python manage.py ai_monitor
Runs two tasks:
1. Auto-generates a new writing prompt every hour using Gemini AI
2. Monitors system activity and generates a "What's Hot" broadcast

Run this in a separate terminal:
    python manage.py ai_monitor

Or schedule it with Windows Task Scheduler / cron for production.
"""
import json
import time
from datetime import date, datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from blog.ai_utils import call_gemini


PROMPT_THEMES = [
    "love and longing in Filipino culture",
    "the streets of Cebu at night",
    "a childhood memory that shaped who you are",
    "loss and the things we carry",
    "hope in unexpected places",
    "the sea and what it means to you",
    "a conversation you never got to finish",
    "belonging and being a stranger",
    "the silence between two people",
    "forgiveness — giving or receiving it",
    "something beautiful you almost missed",
    "the weight of unspoken words",
    "a place that no longer exists",
    "what home means when you are far from it",
    "the last time you were truly afraid",
]


# call_claude replaced by call_gemini from ai_utils


def generate_writing_prompt(theme):
    return call_gemini(f"""You are the writing prompt curator for EchoNotes, a Filipino literary community based in Cebu.

Generate ONE writing prompt with theme: {theme}

Rules:
- One sentence only, no numbering, no prefix
- Evocative, specific, emotionally resonant
- Suitable for poetry, fiction, or personal essays
- Should feel like it was written by a thoughtful Filipino writer

Just the prompt text, nothing else.""", max_tokens=100)


def generate_hot_broadcast(stats):
    return call_gemini(f"""You are the AI broadcaster for EchoNotes, a Filipino literary community.

Here is what happened in the last hour on the platform:
- New posts published: {stats['new_posts']}
- Total likes given: {stats['new_likes']}
- New comments: {stats['new_comments']}
- Most liked post: "{stats['top_post_title']}" by {stats['top_post_author']} ({stats['top_post_likes']} likes)
- Most active writer: {stats['most_active_writer']}
- New users joined: {stats['new_users']}
- Active contests: {stats['active_contests']}
- Trending category: {stats['trending_category']}

Write a short, engaging broadcast (2-3 sentences max) about what's happening on EchoNotes right now.
Make it feel like a live literary radio announcement — warm, excited, community-focused.
Mention specific names and numbers. Keep it under 80 words.

Just the broadcast text, nothing else.""", max_tokens=150)


def generate_word_of_the_day_data():
    prompt = "Generate ONE word of the day for a literary community. It should be an obscure but beautiful English word. Provide a JSON object with 'word', 'definition', and 'example'. Return ONLY the JSON object, no markdown, no other text."
    response = call_gemini(prompt, max_tokens=150)
    
    # Clean up response
    import re
    # Remove markdown code blocks if present
    content = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', response, flags=re.DOTALL)
    # Find the first { and last } to isolate the JSON object
    match = re.search(r'(\{.*\})', content, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        json_str = content.strip()
        
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # If still fails, try one more aggressive cleanup
        json_str = re.sub(r'[^{]*(\{. *\}). *', r'\1', json_str, flags=re.DOTALL)
        return json.loads(json_str)


class Command(BaseCommand):
    help = 'AI Monitor: auto-generates prompts hourly and broadcasts hot activity'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true', help='Run once instead of looping')
        parser.add_argument('--prompt-only', action='store_true', help='Only generate prompt')
        parser.add_argument('--broadcast-only', action='store_true', help='Only generate broadcast')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🤖 EchoNotes AI Monitor started...'))

        run_once = options.get('once', False)

        while True:
            try:
                if not options.get('broadcast_only'):
                    self.generate_prompt()
                    self.generate_word()
                if not options.get('prompt_only'):
                    self.generate_broadcast()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {e}'))

            if run_once:
                break

            self.stdout.write(f'  Next run in 1 hour...')
            time.sleep(3600)

    def generate_prompt(self):
        from blog.models import DailyPrompt

        import random
        theme = random.choice(PROMPT_THEMES)
        today = date.today()

        # Check if we already have a prompt for today
        existing = DailyPrompt.objects.filter(date=today).first()
        if existing:
            self.stdout.write(f'  ✓ Prompt already exists for today.')
            return

        try:
            admin = User.objects.filter(is_superuser=True).first()
            if not admin:
                self.stdout.write(self.style.WARNING('  No superuser found for prompt creation.'))
                return

            prompt_text = generate_writing_prompt(theme)

            DailyPrompt.objects.create(
                prompt=prompt_text,
                created_by=admin,
                date=today,
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS(f'  ✓ Generated prompt: "{prompt_text[:60]}..."'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Prompt generation failed: {e}'))
            # Fallback
            fallbacks = [
                "Write about a moment when silence said more than words ever could.",
                "Describe the smell of rain on a street you used to walk every day.",
                "Write a letter to the city that raised you.",
                "What does hope look like at 3 in the morning?",
            ]
            import random
            DailyPrompt.objects.get_or_create(
                date=today,
                defaults={
                    'prompt': random.choice(fallbacks),
                    'created_by': User.objects.filter(is_superuser=True).first(),
                    'is_active': True,
                }
            )
            self.stdout.write(self.style.WARNING('  Used fallback prompt.'))

    def generate_broadcast(self):
        from blog.models import Post, Like, Comment, Contest, Category, AIBroadcast
        from django.db.models import Count

        one_hour_ago = timezone.now() - timedelta(hours=1)

        new_posts = Post.objects.filter(created_date__gte=one_hour_ago, status='published').count()
        new_likes = Like.objects.filter(created_date__gte=one_hour_ago).count()
        new_comments = Comment.objects.filter(created_date__gte=one_hour_ago).count()
        new_users = User.objects.filter(date_joined__gte=one_hour_ago).count()
        active_contests = Contest.objects.filter(status__in=['open', 'voting']).count()

        top_post = Post.objects.filter(status='published').annotate(
            like_count=Count('likes')
        ).order_by('-like_count').first()

        most_active = User.objects.annotate(
            recent_posts=Count('posts', filter=Q(posts__created_date__gte=one_hour_ago, posts__status='published'))
        ).order_by('-recent_posts').first()

        trending_cat = Category.objects.annotate(
            recent_count=Count('posts', filter=Q(posts__created_date__gte=one_hour_ago))
        ).order_by('-recent_count').first()

        stats = {
            'new_posts': new_posts,
            'new_likes': new_likes,
            'new_comments': new_comments,
            'new_users': new_users,
            'active_contests': active_contests,
            'top_post_title': top_post.title if top_post else 'None yet',
            'top_post_author': top_post.author.username if top_post else 'Unknown',
            'top_post_likes': top_post.total_likes() if top_post else 0,
            'most_active_writer': most_active.username if most_active else 'Unknown',
            'trending_category': trending_cat.name if trending_cat else 'General',
        }

        if new_posts == 0 and new_likes == 0 and new_comments == 0:
            broadcast_text = "The community is quietly building. New stories are waiting to be written — why not be the first today?"
        else:
            try:
                broadcast_text = generate_hot_broadcast(stats)
            except Exception as e:
                broadcast_text = f"EchoNotes is alive with {new_posts} new posts and {new_likes} likes in the last hour. Keep the voices echoing!"

        AIBroadcast.objects.create(
            message=broadcast_text,
            stats=json.dumps(stats),
        )
        self.stdout.write(self.style.SUCCESS(f'  ✓ Broadcast: "{broadcast_text[:60]}..."'))

    def generate_word(self):
        from blog.models import WordOfTheDay
        today = date.today()

        if WordOfTheDay.objects.filter(date=today).exists():
            self.stdout.write(f'  ✓ Word of the Day already exists for today.')
            return

        try:
            admin = User.objects.filter(is_superuser=True).first()
            data = generate_word_of_the_day_data()
            WordOfTheDay.objects.create(
                word=data['word'],
                definition=data['definition'],
                example=data.get('example', ''),
                created_by=admin,
                date=today
            )
            self.stdout.write(self.style.SUCCESS(f"  ✓ Generated Word: {data['word']}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Word generation failed: {e}'))
            # Minimal fallback
            WordOfTheDay.objects.get_or_create(
                date=today,
                defaults={
                    'word': 'Ephemeral',
                    'definition': 'Lasting for a very short time.',
                    'example': 'The beauty of the sunset was ephemeral.',
                    'created_by': User.objects.filter(is_superuser=True).first()
                }
            )
