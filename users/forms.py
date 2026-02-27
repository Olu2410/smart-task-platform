from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import authenticate
from .models import CustomUser, Team, Invitation, UserAvailability
from timezone_field.choices import with_gmt_offset

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'bio', 'phone_number', 
                 'job_title', 'department', 'timezone', 'country', 'avatar',
                 'workday_start', 'workday_end', 'working_days')

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise forms.ValidationError("Invalid username or password.")
            if not user.is_active:
                raise forms.ValidationError("This account is inactive.")
        return cleaned_data

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'bio', 'phone_number',
                 'job_title', 'department', 'timezone', 'country', 'avatar',
                 'workday_start', 'workday_end', 'working_days',
                 'email_notifications', 'desktop_notifications', 'daily_digest',
                 'ai_task_suggestions', 'ai_time_optimization')
        widgets = {
            'workday_start': forms.TimeInput(attrs={'type': 'time'}),
            'workday_end': forms.TimeInput(attrs={'type': 'time'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['working_days'].help_text = "Comma-separated days (e.g., monday,tuesday,wednesday)"

class TeamCreationForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ('name', 'description', 'is_public', 'allow_self_join')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class TeamUpdateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ('name', 'description', 'is_public', 'allow_self_join')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class InvitationForm(forms.ModelForm):
    emails = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Enter multiple email addresses separated by commas"
    )
    
    class Meta:
        model = Invitation
        fields = ('emails', 'role')
    
    def clean_emails(self):
        emails = self.cleaned_data['emails']
        email_list = [email.strip() for email in emails.split(',') if email.strip()]
        
        # Validate email format
        for email in email_list:
            if not forms.EmailField().clean(email):
                raise forms.ValidationError(f"Invalid email address: {email}")
        
        return email_list

class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = UserAvailability
        fields = ('day_of_week', 'start_time', 'end_time', 'is_working_day')
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("End time must be after start time.")
        
        return cleaned_data







# from django import forms
# from django.contrib.auth.forms import UserCreationForm, UserChangeForm
# from django.contrib.auth import authenticate
# from .models import CustomUser, Team, Invitation, UserAvailability
# from timezone_field.choices import with_gmt_offset

# class CustomUserCreationForm(UserCreationForm):
#     email = forms.EmailField(required=True)
#     first_name = forms.CharField(max_length=30, required=True)
#     last_name = forms.CharField(max_length=30, required=True)
    
#     class Meta:
#         model = CustomUser
#         fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
#     def clean_email(self):
#         email = self.cleaned_data['email']
#         if CustomUser.objects.filter(email=email).exists():
#             raise forms.ValidationError("This email address is already registered.")
#         return email

# class CustomUserChangeForm(UserChangeForm):
#     class Meta:
#         model = CustomUser
#         fields = ('username', 'email', 'first_name', 'last_name', 'bio', 'phone_number', 
#                  'job_title', 'department', 'timezone', 'country', 'avatar',
#                  'workday_start', 'workday_end', 'working_days')

# class LoginForm(forms.Form):
#     username = forms.CharField()
#     password = forms.CharField(widget=forms.PasswordInput)
    
#     def clean(self):
#         cleaned_data = super().clean()
#         username = cleaned_data.get('username')
#         password = cleaned_data.get('password')
        
#         if username and password:
#             user = authenticate(username=username, password=password)
#             if not user:
#                 raise forms.ValidationError("Invalid username or password.")
#             if not user.is_active:
#                 raise forms.ValidationError("This account is inactive.")
#         return cleaned_data

# class ProfileUpdateForm(forms.ModelForm):
#     class Meta:
#         model = CustomUser
#         fields = ('first_name', 'last_name', 'email', 'bio', 'phone_number',
#                  'job_title', 'department', 'timezone', 'country', 'avatar',
#                  'workday_start', 'workday_end', 'working_days')
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['working_days'].help_text = "Comma-separated days (e.g., monday,tuesday,wednesday)"

# class TeamCreationForm(forms.ModelForm):
#     class Meta:
#         model = Team
#         fields = ('name', 'description', 'is_public', 'allow_self_join')
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 4}),
#         }

# class TeamUpdateForm(forms.ModelForm):
#     class Meta:
#         model = Team
#         fields = ('name', 'description', 'is_public', 'allow_self_join')
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 4}),
#         }

# class InvitationForm(forms.ModelForm):
#     emails = forms.CharField(
#         widget=forms.Textarea(attrs={'rows': 3}),
#         help_text="Enter multiple email addresses separated by commas"
#     )
    
#     class Meta:
#         model = Invitation
#         fields = ('emails', 'role')
    
#     def clean_emails(self):
#         emails = self.cleaned_data['emails']
#         email_list = [email.strip() for email in emails.split(',') if email.strip()]
        
#         # Validate email format
#         for email in email_list:
#             if not forms.EmailField().clean(email):
#                 raise forms.ValidationError(f"Invalid email address: {email}")
        
#         return email_list

# class AvailabilityForm(forms.ModelForm):
#     class Meta:
#         model = UserAvailability
#         fields = ('day_of_week', 'start_time', 'end_time', 'is_working_day')
#         widgets = {
#             'start_time': forms.TimeInput(attrs={'type': 'time'}),
#             'end_time': forms.TimeInput(attrs={'type': 'time'}),
#         }