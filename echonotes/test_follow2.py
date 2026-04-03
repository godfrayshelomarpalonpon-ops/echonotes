import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'echonotes.settings')
django.setup()
from django.contrib.auth.models import User
u1 = User.objects.first()
u2 = User.objects.last()
from django.test import Client
c = Client()
c.force_login(u1)
resp = c.post(f'/follow/{u2.username}/')
if resp.status_code == 500:
    import re
    html = resp.content.decode('utf-8')
    m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
    with open('error_out.txt', 'w') as f:
        f.write(m.group(1) if m else "No title")
