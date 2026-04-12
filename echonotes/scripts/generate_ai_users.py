import os
import django
import random
import json
# import urllib.request (removed unused)

import sys

# Setup Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'echonotes.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import UserProfile

PERSONAS = [
    {
        "username": "Enrico_Encourage",
        "first_name": "Enrico",
        "persona_type": "The Encouraging Peer",
        "bio_theme": "A positive soul who believes every story deserves to be heard. Loves uplifting others.",
    },
    {
        "username": "Lucia_Critic",
        "first_name": "Lucia",
        "persona_type": "The Constructive Critic",
        "bio_theme": "A seasoned reader with a keen eye for metaphor and structure. Blunt but fair.",
    },
    {
        "username": "Boni_Bookworm",
        "first_name": "Bonifacio",
        "persona_type": "The Classic Bibliophile",
        "bio_theme": "Obsessed with the classics. Often quotes Rizal or Shakespeare while reading modern echoes.",
    },
    {
        "username": "Malaya_Heart",
        "first_name": "Malaya",
        "persona_type": "The Romantic Dreamer",
        "bio_theme": "Sees the world through rose-tinted glasses. Hunts for the beauty in every tragedy.",
    },
    {
        "username": "Kulas_Creative",
        "first_name": "Kulas",
        "persona_type": "The Experimental Wit",
        "bio_theme": "A fan of plot twists and surrealism. Always asking 'what if?'",
    }
]

def generate_bio(theme):
    # Fallback bios if AI fails
    fallbacks = [
        f"Writer and dreamer. Theme: {theme}",
        f"Lost in words and stories. {theme}",
        f"Part of the EchoNotes community. {theme}"
    ]
    return random.choice(fallbacks)

def create_ai_users():
    print("Starting AI User Generation...")
    for p in PERSONAS:
        user, created = User.objects.get_or_create(
            username=p['username'],
            defaults={
                'first_name': p['first_name'],
                'email': f"{p['username']}@echonotes.ai"
            }
        )
        if created:
            user.set_password('EchoNotesAI2026!')
            user.save()
            print(f"Created user: {user.username}")
        else:
            print(f"User {user.username} already exists.")

        # Update Profile
        profile = user.profile
        profile.is_ai = True
        profile.persona_type = p['persona_type']
        profile.bio = generate_bio(p['bio_theme'])
        profile.save()
        print(f"  Updated profile for {user.username} as {p['persona_type']}")

    print("AI User Generation Complete.")

if __name__ == '__main__':
    create_ai_users()
