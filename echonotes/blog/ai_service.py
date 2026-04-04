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
    def get_comment_for_post(cls, persona_type, post_mood):
        logic = cls.PERSONA_LOGIC.get(persona_type)
        if not logic:
            return "Wonderful read. Thank you for sharing!"
        
        template = random.choice(logic['templates'])
        # Simple string formatting for mood if mentioned
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
        comment_text = cls.get_comment_for_post(profile.persona_type, post.get_mood_display() if post.mood else "")
        if not Comment.objects.filter(author=ai_user, post=post).exists():
            Comment.objects.create(author=ai_user, post=post, content=comment_text)
            return True
            
        return False
