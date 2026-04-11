from django.contrib.auth.models import User
import os

username = 'admin'
email = 'admin@echonotes.com'
password = 'admin123'

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Successfully created superuser: {username}")
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f"Updated password for existing superuser: {username}")
