import os
import django
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'echonotes.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import Post, UserProfile, Comment, Like, WritingStreak
from blog.ai_service import AIService, AIPersonaEngine

def verify():
    print("🧪 Starting Verification...")
    
    # 1. Ensure we have an AI user
    ai_user, _ = User.objects.get_or_create(username='test_ai_critic', defaults={'email': 'ai@test.com'})
    profile, _ = UserProfile.objects.get_or_create(user=ai_user)
    profile.is_ai = True
    profile.persona_type = "The Constructive Critic"
    profile.save()
    print(f"✅ AI User: {ai_user.username} ({profile.persona_type})")

    # 2. Create a normal user for posting
    human_user, _ = User.objects.get_or_create(username='human_tester', defaults={'email': 'human@test.com'})
    WritingStreak.objects.get_or_create(user=human_user)
    print(f"✅ Human User: {human_user.username}")

    # 3. Create a post
    test_content = "The river flowed silently under the moonlight, carrying with it the secrets of a thousand years."
    post = Post.objects.create(
        title="Moonlight River",
        content=test_content,
        author=human_user,
        status='published',
        mood='melancholic'
    )
    print(f"📝 Created Post: '{post.title}'")

    # 4. Trigger AI Summary (manually if signal is slow or for direct test)
    print("🤖 Triggering AI Summary...")
    post.ai_summary = AIService.generate_summary(post.content)
    post.save()
    print(f"✨ AI Summary: {post.ai_summary}")

    # 5. Trigger AI Interaction
    print("🤖 Triggering AI Interaction...")
    interacted = AIPersonaEngine.interact_with_post(ai_user, post)
    print(f"💬 AI Interacted: {interacted}")

    # 6. Check results
    comment = Comment.objects.filter(post=post, author=ai_user).first()
    if comment:
        print(f"💬 AI Comment: '{comment.content}'")
    
    like_exists = Like.objects.filter(post=post, user=ai_user).exists()
    print(f"❤️ AI Liked: {like_exists}")

    if post.ai_summary and not post.ai_summary.startswith("ERROR"):
        print("🎉 VERIFICATION SUCCESSFUL!")
    else:
        print("❌ VERIFICATION FAILED (Summary missing or error)")

if __name__ == "__main__":
    verify()
