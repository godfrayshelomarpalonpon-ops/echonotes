from rest_framework import serializers
from django.contrib.auth.models import User
from blog.models import Post, Comment, Like, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    profile_pic_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_pic_url', 'created_date']

    def get_profile_pic_url(self, obj):
        request = self.context.get('request')
        if obj.profile_pic and obj.profile_pic.name != 'default.jpg':
            if request:
                return request.build_absolute_uri(obj.profile_pic.url)
            return obj.profile_pic.url
        return None


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'date_joined', 'profile', 'post_count']

    def get_post_count(self, obj):
        return obj.posts.count()


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Comment
        fields = ['id', 'author_username', 'content', 'created_date']
        read_only_fields = ['id', 'author_username', 'created_date']


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')
    total_likes = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author_username',
            'created_date', 'updated_date',
            'total_likes', 'total_comments', 'is_liked_by_user',
            'comments',
        ]
        read_only_fields = ['id', 'author_username', 'created_date', 'updated_date']

    def get_total_likes(self, obj):
        return obj.total_likes()

    def get_total_comments(self, obj):
        return obj.total_comments()

    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(post=obj, user=request.user).exists()
        return False


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for post lists (no nested comments)."""
    author_username = serializers.ReadOnlyField(source='author.username')
    total_likes = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'author_username',
            'created_date', 'total_likes', 'total_comments',
        ]

    def get_total_likes(self, obj):
        return obj.total_likes()

    def get_total_comments(self, obj):
        return obj.total_comments()


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'post', 'user', 'created_date']
        read_only_fields = ['id', 'user', 'created_date']