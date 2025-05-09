from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import MoodEntry, JournalEntry, ChatMessage, WellnessGoal, GoalProgress

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class MoodEntryForm(forms.ModelForm):
    class Meta:
        model = MoodEntry
        fields = ['mood', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'mood': forms.Select(attrs={'class': 'form-select'})
        }

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'})
        }

class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Type your message here...'
            })
        }

class WellnessGoalForm(forms.ModelForm):
    class Meta:
        model = WellnessGoal
        fields = ['goal_type', 'custom_goal', 'target', 'frequency', 'end_date', 'notes']
        widgets = {
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        goal_type = cleaned_data.get('goal_type')
        custom_goal = cleaned_data.get('custom_goal')

        if goal_type == 'custom' and not custom_goal:
            raise forms.ValidationError("Please provide a description for your custom goal.")

        return cleaned_data

class GoalProgressForm(forms.ModelForm):
    class Meta:
        model = GoalProgress
        fields = ['progress', 'completed', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        } 