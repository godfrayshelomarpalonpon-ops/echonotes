import os
import django
import sys

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'echonotes.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import UserProfile

def initialize_maria():
    username = 'Maria'
    email = 'maria@echonotes.ai'
    password = 'ai_password_123' # Not used for login typically
    
    user, created = User.objects.get_or_create(username=username, defaults={'email': email})
    if created:
        user.set_password(password)
        user.save()
        print(f"✅ User '{username}' created.")
    else:
        print(f"ℹ️ User '{username}' already exists.")

    profile, p_created = UserProfile.objects.get_or_create(user=user)
    profile.is_ai = True
    profile.persona_type = 'The Encouraging Peer'
    profile.bio = 'A classic Filipino storyteller and literary mentor. Here to support every voice in EchoNotes. ✨'
    profile.save()
    
    if p_created:
        print(f"✅ AI Profile for '{username}' created.")
    else:
        print(f"✅ AI Profile for '{username}' updated.")

if __name__ == "__main__":
    initialize_maria()
