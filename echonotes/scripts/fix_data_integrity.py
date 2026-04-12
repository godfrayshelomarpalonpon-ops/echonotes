import os
import django
import sys

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'echonotes.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import UserProfile, WritingStreak

def fix_integrity():
    users = User.objects.all()
    print(f"🔍 Checking integrity for {users.count()} users...")
    
    fixed_profiles = 0
    fixed_streaks = 0
    
    for user in users:
        # 1. Fix Profiles
        profile, created = UserProfile.objects.get_or_create(user=user)
        if created:
            fixed_profiles += 1
            print(f"  + Created missing profile for {user.username}")
        
        # 2. Fix Writing Streaks
        streak, s_created = WritingStreak.objects.get_or_create(user=user)
        if s_created:
            fixed_streaks += 1
            print(f"  + Created missing streak for {user.username}")

    print(f"\n✨ Integrity check complete!")
    print(f"✅ Profiles created: {fixed_profiles}")
    print(f"✅ Writing streaks created: {fixed_streaks}")

if __name__ == "__main__":
    fix_integrity()
