from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import authenticate
from .models import CustomUser, Team, Invitation, UserAvailability

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
                 'workday_start', 'workday_end', 'working_days')
    
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
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }