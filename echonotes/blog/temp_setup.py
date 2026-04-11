    return JsonResponse({'status': 'ok'})


# ─── Temporary Setup (Delete or secure after use) ─────────────────────────────

def init_admin(request):
    from django.contrib.auth.models import User
    from django.http import HttpResponse
    from django.core.management import call_command
    import io

    # Simple security check
    if 'key' not in request.GET or request.GET.get('key') != 'echo99':
        return HttpResponse("Unauthorized", status=401)

    output = io.StringIO()
    try:
        # 1. Run Migrations
        call_command('migrate', no_input=True, stdout=output)
        migration_output = output.getvalue()
        
        # 2. Setup Superuser
        username = 'admin'
        email = 'admin@echonotes.com'
        password = 'admin123'

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            status_msg = f"Successfully created superuser: {username}"
        else:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            status_msg = f"Updated password for existing superuser: {username}"
            
        return HttpResponse(f"✅ Migrations applied!<br><pre>{migration_output}</pre><br>✅ {status_msg}")
        
    except Exception as e:
        return HttpResponse(f"❌ Error during setup: {str(e)}<br><pre>{output.getvalue()}</pre>", status=500)
