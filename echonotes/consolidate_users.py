import os
import django
import sqlite3

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'echonotes.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection

def consolidate_users():
    # Mapping of secondary username/id to primary username/id
    # From research: 
    # Godfray1 (19) -> Godfray (3)
    # admin1 (17) -> admin (4)
    # mich123 (16) -> mich (5)
    
    mapping = {
        19: 3, # Godfray1 -> Godfray
        17: 4, # admin1 -> admin
        16: 5, # mich123 -> mich
    }
    
    cursor = connection.cursor()
    
    # Tables and their foreign key columns to auth_user
    fk_configs = [
        ('blog_post', 'author_id'),
        ('blog_follow', 'follower_id'),
        ('blog_follow', 'following_id'),
        ('blog_like', 'user_id'),
        ('blog_comment', 'author_id'),
        ('blog_bookmark', 'user_id'),
        ('blog_contest', 'created_by_id'),
        ('blog_contestentry', 'author_id'),
        ('blog_contestvote', 'voter_id'),
        ('blog_report', 'reported_by_id'),
        ('blog_report', 'reviewed_by_id'),
        ('blog_dailyprompt', 'created_by_id'),
        ('blog_promptresponse', 'author_id'),
        ('blog_promptresponselike', 'user_id'),
        ('blog_wordoftheday', 'created_by_id'),
        ('blog_wordofthedayentry', 'author_id'),
        ('blog_wordentrylike', 'user_id'),
        ('blog_writingstreak', 'user_id'),
        ('blog_collaborativestory', 'started_by_id'),
        ('blog_storyparagraph', 'author_id'),
        ('blog_userbadge', 'user_id'),
        ('blog_leaderboardentry', 'user_id'),
        ('blog_writingsession', 'user_id'),
        ('blog_chatgroup', 'created_by_id'),
        ('blog_chatgroupmember', 'user_id'),
        ('blog_chatmessage', 'author_id'),
        ('blog_directmessage', 'sender_id'),
        ('blog_directmessage', 'recipient_id'),
        ('blog_friend', 'user1_id'),
        ('blog_friend', 'user2_id'),
        ('blog_friendrequest', 'sender_id'),
        ('blog_friendrequest', 'receiver_id'),
        ('blog_notification', 'recipient_id'),
        ('blog_notification', 'sender_id'),
        ('blog_userprofile', 'user_id'),
    ]
    
    for secondary_id, primary_id in mapping.items():
        print(f"Consolidating user {secondary_id} to {primary_id}...")
        
        for table, col in fk_configs:
            # Handle unique constraints (e.g. unique_together follower/following)
            # For simpler consolidation, we try to update and ignore if it already exists
            try:
                cursor.execute(f"UPDATE {table} SET {col} = %s WHERE {col} = %s", [primary_id, secondary_id])
                print(f"  Updated {table}.{col}")
            except Exception as e:
                # If unique constraint fails, we delete the duplicate relation
                # For this specific task, we'll just ignore for now and delete later
                print(f"  Error updating {table}.{col}: {e}")
                cursor.execute(f"DELETE FROM {table} WHERE {col} = %s", [secondary_id])
                print(f"  Deleted duplicates from {table}.{col}")
        
        # Finally, delete the secondary user
        try:
            sec_user = User.objects.get(id=secondary_id)
            sec_user.delete()
            print(f"  Deleted secondary user {secondary_id}")
        except User.DoesNotExist:
            print(f"  Secondary user {secondary_id} not found.")

    print("Consolidation complete.")

if __name__ == '__main__':
    consolidate_users()
