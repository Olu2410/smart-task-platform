# team_chat/forms.py
from django import forms
from .models import ChannelMessage, FileShare, TeamChannel

class ChannelMessageForm(forms.ModelForm):
    class Meta:
        model = ChannelMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Type your message here...',
                'class': 'form-control message-input',
                'style': 'resize: none;'
            }),
        }

class FileShareForm(forms.ModelForm):
    class Meta:
        model = FileShare
        fields = ['file', 'description']
        widgets = {
            'description': forms.TextInput(attrs={
                'placeholder': 'Optional description...',
                'class': 'form-control'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (50MB limit)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 50MB')
            
            # Check file extension
            import os
            from django.conf import settings
            
            ext = os.path.splitext(file.name)[1].lower()
            allowed_extensions = []
            for extensions in settings.ALLOWED_FILE_EXTENSIONS.values():
                allowed_extensions.extend(extensions)
            
            if ext not in allowed_extensions:
                raise forms.ValidationError('File type not allowed')
        
        return file

