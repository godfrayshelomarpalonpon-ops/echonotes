from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import (
    Post, Comment, UserProfile, Category, Contest, ContestEntry,
    Report, PromptResponse, WordOfTheDayEntry, CollaborativeStory, StoryParagraph,
)


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_pic']

    def clean_profile_pic(self):
        profile_pic = self.cleaned_data.get('profile_pic')
        if profile_pic and hasattr(profile_pic, 'content_type'):
            try:
                if profile_pic.size > 2 * 1024 * 1024:
                    raise forms.ValidationError("Image file too large ( > 2MB )")
                if not profile_pic.content_type.startswith('image'):
                    raise forms.ValidationError("File is not an image")
            except forms.ValidationError:
                raise
            except Exception:
                pass
        return profile_pic


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category', 'mood', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter post title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write your thoughts here...', 'rows': 12, 'id': 'post-content'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'mood': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {'status': 'Publish or save as Draft?', 'mood': 'Story Mood (optional)'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write a comment...', 'rows': 3}),
        }
        labels = {'content': ''}


class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['title', 'description', 'theme', 'submission_deadline', 'voting_deadline']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'theme': forms.TextInput(attrs={'class': 'form-control'}),
            'submission_deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'voting_deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class ContestEntryForm(forms.ModelForm):
    class Meta:
        model = ContestEntry
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your entry title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 12, 'id': 'entry-content'}),
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional details (optional)...'}),
        }
        labels = {'description': 'Additional details (optional)'}


class PromptResponseForm(forms.ModelForm):
    class Meta:
        model = PromptResponse
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write your response to today\'s prompt...',
                'id': 'prompt-content',
            }),
        }
        labels = {'content': 'Your Response'}


class WordEntryForm(forms.ModelForm):
    class Meta:
        model = WordOfTheDayEntry
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Write a short piece (100 words max) using today\'s word...',
                'id': 'word-content',
                'maxlength': '600',
            }),
        }
        labels = {'content': 'Your Entry (100 words max)'}


class CollaborativeStoryForm(forms.ModelForm):
    first_paragraph = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Write the opening paragraph to start the story...',
        }),
        label='Opening Paragraph',
        help_text='This will be the first paragraph of the collaborative story.'
    )

    class Meta:
        model = CollaborativeStory
        fields = ['title', 'description', 'max_contributors']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Story title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description of the story...'}),
            'max_contributors': forms.NumberInput(attrs={'class': 'form-control', 'min': 2, 'max': 20}),
        }


class StoryParagraphForm(forms.ModelForm):
    class Meta:
        model = StoryParagraph
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Continue the story with your paragraph...',
            }),
        }
        labels = {'content': 'Your Paragraph'}
