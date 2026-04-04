import os
import django

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'echonotes.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import Follow

def verify():
    # Check if duplicates are gone
    all_users = User.objects.all()
    usernames = [u.username for u in all_users]
    from collections import Counter
    counts = Counter(usernames)
    duplicates = [name for name, count in counts.items() if count > 1]
    
    if duplicates:
        print(f"FAILED: Still have duplicate usernames: {duplicates}")
        return
    else:
        print("SUCCESS: Zero duplicate usernames found.")
        
    # Check follow functionality
    tester = User.objects.get(username='tester')
    godfray = User.objects.get(username='Godfray')
    
    # Follow
    follow, created = Follow.objects.get_or_create(follower=tester, following=godfray)
    print(f"Followed: created={created}, current count for Godfray={Follow.objects.filter(following=godfray).count()}")
    
    # Unfollow
    follow.delete()
    print(f"Unfollowed: current count for Godfray={Follow.objects.filter(following=godfray).count()}")
    
    # Verify no numbered users remain
    for u in all_users:
        if u.username.endswith('1') or u.username.endswith('123'):
            # Check if they are actually duplicates like 'admin1'
            if u.username[:-1] in counts and u.username != 'tester':
                print(f"WARNING: Numbered user still exists: {u.username}")

if __name__ == '__main__':
    verify()
