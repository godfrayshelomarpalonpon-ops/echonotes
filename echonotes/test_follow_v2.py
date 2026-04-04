import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'echonotes.settings')
django.setup()
from django.contrib.auth.models import User
from django.test import RequestFactory
from blog.views import follow_user
from blog.models import Follow
import traceback

u1 = User.objects.first()
u2 = User.objects.last()

if u1 == u2:
    print("Not enough users to test")
    exit()

# Ensure we are not following
Follow.objects.filter(follower=u1, following=u2).delete()

print(f'Following {u2.username} using {u1.username}')

rf = RequestFactory()
req = rf.post(f'/follow/{u2.username}/')
req.user = u1

try:
    resp = follow_user(req, u2.username)
    print("FOLLOW RESULT:", resp.content)
    
    # Try unfollowing
    req = rf.post(f'/follow/{u2.username}/')
    req.user = u1
    resp = follow_user(req, u2.username)
    print("UNFOLLOW RESULT:", resp.content)
    
except Exception as e:
    traceback.print_exc()
