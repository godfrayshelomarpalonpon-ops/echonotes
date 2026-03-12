from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Post, Comment, UserProfile

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
        if profile_pic:
            # Check file size (max 2MB)
            if profile_pic.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Image file too large ( > 2MB )")
            
            # Check file type
            if not profile_pic.content_type.startswith('image'):
                raise forms.ValidationError("File is not an image")
            
            # Check dimensions
            try:
                from PIL import Image
                import io
                # Reset file pointer to beginning
                profile_pic.seek(0)
                image = Image.open(io.BytesIO(profile_pic.read()))
                if image.width > 1000 or image.height > 1000:
                    raise forms.ValidationError("Image dimensions too large (max 1000x1000)")
                
                # Reset file pointer for further use
                profile_pic.seek(0)
            except Exception as e:
                # If PIL is not available or image processing fails, just return the file
                pass
        
        return profile_pic

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter post title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write your thoughts here...', 'rows': 8}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write a comment...', 'rows': 3}),
        }
        labels = {
            'content': '',
        }