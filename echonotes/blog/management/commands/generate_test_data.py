"""
Management command to generate AI test users with sample posts, comments, and likes.
Usage: python manage.py generate_test_data
"""
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from blog.models import Post, Comment, Like, UserProfile, Category, Follow, Bookmark


USERNAMES = [
    'alex_writes', 'maria_poet', 'jose_stories', 'anna_essays',
    'carlo_journal', 'nina_voice', 'miguel_ink', 'sarah_echoes',
    'juan_quill', 'elena_words',
]

BIOS = [
    "Poetry lover from Cebu. I write about the sea and the people I've loved.",
    "Storyteller. Coffee addict. Believer in the power of honest writing.",
    "Essays on life, love, and everything in between. Based in Cebu City.",
    "Fiction writer exploring the quiet moments of everyday Filipino life.",
    "Poet, dreamer, and occasional philosopher. Words are my home.",
    "Writing is how I make sense of the world. Join me on the journey.",
    "Short stories and personal essays. Finding beauty in ordinary days.",
    "I write what I feel. No filter, just honesty.",
    "Nature writer and amateur philosopher based in the Visayas.",
    "Sharing my thoughts one post at a time. Slow writer, deep thinker.",
]

POETRY_POSTS = [
    ("The Rain on Osmeña Boulevard", """
The rain comes without warning,
like most things worth feeling.

I stand under the awning of a bakery
that smells of pan de sal and yesterday,
watching the water trace paths
down the faces of strangers.

Every drop a small decision —
left, right, pooling at the curb,
finding its way to wherever
lost things go.

I think of you, the way water thinks
of the sea: inevitable, unhurried,
already there before I knew
I was heading toward you.
"""),
    ("Lola's Hands", """
Her hands remember everything
her mind has started to forget.

The fold of banana leaves around rice,
the press of thumb into dough,
the particular weight of a rosary
worn smooth by decades of asking.

I watch her hands move in the kitchen
like they know something
the rest of her has let go —
muscle memory older than language,
older than names.

When she holds mine
I feel all the years she carried
before I existed to be carried by her.
"""),
    ("Cebu at 3am", """
The city doesn't sleep, it just
changes shifts.

The jeepneys thin out.
The vendors pack their carts.
A security guard checks his phone
for the seventh time.

This is the hour of honest conversations
and cold coffee.
The hour when the heart admits
what it's been rehearsing all day.

I like it here, in the in-between.
When the city shows you
who it is when no one's watching.
"""),
]

STORY_POSTS = [
    ("The Last Tricycle Driver on Colon Street", """
Mang Eddie has been driving the same route for thirty-two years. He knows which potholes appear after heavy rain, which traffic lights run three seconds longer than they should, and exactly how long it takes a passenger to realize they've forgotten something at home.

"They're building a new road," his wife told him last week. "Your route will change."

He nodded and said nothing. Routes change. That's what routes do.

What he didn't say was this: he's mapped thirty-two years of this city's changes on the back of his memory. Every building that went up, every stall that closed, every new school uniform he's seen board his tricycle on Monday mornings.

The new road will be fine. He'll learn it.

He always does.
"""),
    ("A Sunday in Lahug", """
My grandmother doesn't understand why I moved to the city, but she visits anyway.

She arrived on a Sunday with a bag of mangoes and opinions about my apartment. Too small. Too high up. "What if there's a fire?" she asked, looking at the elevator with suspicion.

"Then I run down the stairs, Lola."

"Good. Always know where the stairs are."

We ate lunch at the small table by the window. She talked about her garden. I talked about my work. Neither of us said what we meant, which is: I miss you. I worry about you. The distance between us is not just kilometers.

Before she left, she tucked two hundred pesos under my coffee mug.

"For rice," she said.

I didn't tell her I have rice. I just said thank you.
"""),
]

OPINION_POSTS = [
    ("Why We Need to Talk About Filipino Reading Culture", """
Walk into any bookstore in Cebu and you'll notice something: the self-help section is always packed. The literary fiction section? Mostly untouched.

I'm not here to judge what people read. Reading anything is better than reading nothing. But I do want to ask: why does our relationship with reading feel transactional? We read to improve, to gain skills, to become more productive. Rarely do we read simply to feel something.

Literature — real, difficult, uncomfortable literature — does something productivity books cannot. It builds empathy. It lets you inhabit a life completely unlike your own. It teaches you that other people's inner worlds are just as complex and valid as yours.

A country of readers is a country harder to manipulate. A country of literary readers is a country more capable of compassion.

Maybe that's worth making time for.
"""),
    ("On Being From a Place That Changes Too Fast", """
Cebu is not the city I grew up in.

I don't mean that as a complaint. Change is not inherently bad. New roads mean shorter commutes. New buildings mean jobs. Progress is real and it matters.

But something gets lost in the pace of it. The small bakery where my mother bought pandesal every morning is now a convenience store. The empty lot where we played as kids is a parking building. The old movie house on the boulevard — gone.

I understand why these things happen. I understand the economics.

What I struggle to articulate is this: when the places that shaped you disappear, a part of your story disappears with them. Not from your memory, but from the shared world. No one else can point to it and say, "I remember that too."

Memory becomes solitary. And solitary memory is a lonelier thing.
"""),
]

COMMENT_TEXTS = [
    "This really moved me. Thank you for writing it.",
    "I feel this deeply. You put words to something I couldn't express.",
    "Beautiful writing. The last line especially.",
    "This is exactly what I needed to read today.",
    "Wow. Just wow. Please keep writing.",
    "I shared this with my friend who needed it. Thank you.",
    "The imagery here is stunning. So vivid.",
    "This made me tear up a little. Honest and beautiful.",
    "Such an important perspective. Thank you for sharing.",
    "I've read this three times now. It keeps giving.",
    "This reminds me of my own lola. Thank you.",
    "You have a real gift. Please don't stop.",
    "I felt this in my chest. Incredible writing.",
    "The rhythm of this is perfect. Every word earned.",
    "This is why EchoNotes exists. Writing like this.",
]


class Command(BaseCommand):
    help = 'Generate AI test users with sample posts, comments, and likes'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=5, help='Number of test users to create (max 10)')
        parser.add_argument('--clear', action='store_true', help='Clear existing test users first')

    def handle(self, *args, **options):
        num_users = min(options['users'], 10)

        if options['clear']:
            deleted = User.objects.filter(username__in=USERNAMES).delete()
            self.stdout.write(self.style.WARNING(f'Cleared existing test users.'))

        # Ensure categories exist
        categories = {}
        for name, slug in [('Poetry', 'poetry'), ('Stories', 'stories'), ('Opinion', 'opinion'), ('Journal', 'journal')]:
            cat, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name})
            categories[slug] = cat

        created_users = []

        for i in range(num_users):
            username = USERNAMES[i]

            if User.objects.filter(username=username).exists():
                self.stdout.write(f'  Skipping {username} — already exists.')
                user = User.objects.get(username=username)
                created_users.append(user)
                continue

            user = User.objects.create_user(
                username=username,
                email=f'{username}@echonotes.test',
                password='testpass123',
                first_name=username.split('_')[0].capitalize(),
            )

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.bio = BIOS[i]
            profile.save()

            created_users.append(user)
            self.stdout.write(f'  Created user: {username}')

        # Create posts
        all_post_data = (
            [(title, content, 'poetry') for title, content in POETRY_POSTS] +
            [(title, content, 'stories') for title, content in STORY_POSTS] +
            [(title, content, 'opinion') for title, content in OPINION_POSTS]
        )

        created_posts = []
        for idx, (title, content, cat_slug) in enumerate(all_post_data):
            author = created_users[idx % len(created_users)]

            if Post.objects.filter(title=title).exists():
                post = Post.objects.get(title=title)
                created_posts.append(post)
                continue

            post = Post.objects.create(
                title=title,
                content=content.strip(),
                author=author,
                category=categories.get(cat_slug),
                status='published',
                created_date=timezone.now() - timedelta(days=random.randint(1, 30)),
            )
            created_posts.append(post)
            self.stdout.write(f'  Created post: "{title[:40]}..."')

        # Add likes and comments
        for post in created_posts:
            likers = random.sample(created_users, min(random.randint(2, 5), len(created_users)))
            for liker in likers:
                if liker != post.author:
                    Like.objects.get_or_create(post=post, user=liker)

            commenters = random.sample(created_users, min(random.randint(1, 3), len(created_users)))
            for commenter in commenters:
                if commenter != post.author:
                    if not Comment.objects.filter(post=post, author=commenter).exists():
                        Comment.objects.create(
                            post=post,
                            author=commenter,
                            content=random.choice(COMMENT_TEXTS),
                            created_date=timezone.now() - timedelta(days=random.randint(0, 10)),
                        )

        # Add some follows
        for user in created_users:
            to_follow = random.sample(
                [u for u in created_users if u != user],
                min(2, len(created_users) - 1)
            )
            for target in to_follow:
                Follow.objects.get_or_create(follower=user, following=target)

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Done! Created {len(created_users)} test users with posts, comments, and likes.'
            f'\n  Login with any username above and password: testpass123'
        ))
