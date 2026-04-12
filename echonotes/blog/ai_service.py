import random
import json
from blog.models import UserProfile, Post, Comment

class AIPersonaEngine:
    """
    Handles AI persona interactions (comments, reactions) based on their profile settings.
    """
    
    PERSONA_LOGIC = {
        "The Encouraging Peer": {
            "templates": [
                "This is so moving! I love how you captured the feeling of {mood}. Keep writing!",
                "Wow, that was a powerful read. You have a real gift for storytelling!",
                "This echo really resonated with me. Subscribing to see more from you!",
            ],
            "like_probability": 0.9,
        },
        "The Constructive Critic": {
            "templates": [
                "Interesting piece. I particularly liked your use of {mood} imagery, though I felt the ending was a bit sudden.",
                "Good start. Have you considered expanding the middle section more? The descriptions are great.",
                "Technically sound. I think if you spent more time on the 'show, don't tell' aspect in paragraph 2, it would be perfect.",
            ],
            "like_probability": 0.4,
        },
        "The Classic Bibliophile": {
            "templates": [
                "Reminds me of a passage I once read in an old anthology. There's a timeless quality to your {mood} tone.",
                "A fine story. It has that classical structure that is so rare these days. Well done.",
                "In ancient scrolls, we'd call this 'evocative.' You've captured something special here.",
            ],
            "like_probability": 0.6,
        },
        "The Romantic Dreamer": {
            "templates": [
                "Oh, my heart... the way you wrote about {mood} is simply poetic. ❤️",
                "I felt every word of this. Truly, a soul-stirring piece of work.",
                "There is a delicate beauty here. Thank you for sharing this part of your world.",
            ],
            "like_probability": 0.95,
        },
        "The Experimental Wit": {
            "templates": [
                "Wait—what if the narrator was actually an unreliable witness? This setup is fascinating!",
                "Loving the experimental vibe of this! It's so different from the usual feeds.",
                "Wild stuff! I'd love to see a version of this where the ending is a complete 180 twist.",
            ],
            "like_probability": 0.7,
        }
    }

    @classmethod
    def get_comment_for_post(cls, persona_type, post_content, post_mood=""):
        """
        Generates a comment. Uses Gemini for higher quality if possible.
        """
        try:
            from blog.ai_utils import call_gemini
            prompt = f"""You are Maria, a warm Filipino storytelling mentor on the EchoNotes platform.
            Write a heartfelt, brief, and highly encouraging comment (2-3 sentences max) on the following piece of writing.
            Be specific about what you liked or how it made you feel. Use a warm, literary tone.
            Writing piece content: {post_content[:800]}
            Comment as Maria:"""
            
            comment = call_gemini(prompt, max_tokens=100)
            if "ERROR" not in comment:
                return comment.strip()
        except:
            pass

        # Fallback to templates
        logic = cls.PERSONA_LOGIC.get(persona_type)
        if not logic:
            return "Wonderful read. Thank you for sharing!"
        
        template = random.choice(logic['templates'])
        return template.replace("{mood}", post_mood if post_mood else "this scene")

    @classmethod
    def interact_with_post(cls, ai_user, post):
        """
        Main entry point for an AI persona to react to a post.
        """
        profile = getattr(ai_user, 'profile', None)
        if not profile or not profile.is_ai:
            return False
            
        logic = cls.PERSONA_LOGIC.get(profile.persona_type)
        if not logic:
            return False

        # 1. Decide whether to Like
        if random.random() < logic['like_probability']:
            from blog.models import Like
            Like.objects.get_or_create(user=ai_user, post=post)

        # 2. Generate and Post Comment
        # 50% chance for Maria to comment ("just few")
        if random.random() < 0.5:
            comment_text = cls.get_comment_for_post(profile.persona_type, post.content, post.get_mood_display() if post.mood else "")
            if not Comment.objects.filter(author=ai_user, post=post).exists():
                Comment.objects.create(author=ai_user, post=post, content=comment_text)
                return True
            
        return False

class AIService:
    """
    Advanced AI features for content generation and moderation.
    """
    
    @staticmethod
    def generate_summary(content):
        """
        Generates a 1-sentence evocative summary of the writing.
        """
        from blog.ai_utils import call_gemini
        prompt = f"Summarize the following story/poem in exactly one evocative, beautiful sentence from a literary perspective:\n\n{content}"
        return call_gemini(prompt, max_tokens=150)

    @staticmethod
    def moderate_content(text):
        """
        Analyzes content for toxicity. Returns a tuple (is_toxic, score).
        """
        from blog.ai_utils import call_gemini
        prompt = f"Analyze the following text for toxicity (hate speech, violence, severe harassment). Return ONLY a JSON object with 'toxic' (boolean) and 'score' (float 0.0 to 1.0):\n\n{text}"
        response = call_gemini(prompt, max_tokens=50)
        try:
            # Clean response if AI adds markdown backticks
            clean_response = response.strip('`').replace('json', '').strip()
            data = json.loads(clean_response)
            return data.get('toxic', False), data.get('score', 0.0)
        except Exception:
            return False, 0.0
