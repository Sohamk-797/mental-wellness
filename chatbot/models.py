from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class MoodEntry(models.Model):
    MOOD_CHOICES = [
        ('very_happy', 'Very Happy'),
        ('happy', 'Happy'),
        ('neutral', 'Neutral'),
        ('sad', 'Sad'),
        ('very_sad', 'Very Sad'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s mood: {self.mood} on {self.created_at.strftime('%Y-%m-%d')}"

class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Journal entries"

    def __str__(self):
        return f"{self.user.username}'s journal entry on {self.created_at.strftime('%Y-%m-%d')}"

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    response_time = models.FloatField(null=True, blank=True)  # Store response time in seconds

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_user']),
        ]

    def __str__(self):
        return f"Chat with {self.user.username} on {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @classmethod
    def get_recent_chat_history(cls, user, limit=5):
        """Get recent chat history for a user"""
        return cls.objects.filter(user=user).order_by('-created_at')[:limit]

class SelfCareSuggestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    suggestion = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('relaxation', 'Relaxation'),
        ('physical', 'Physical Activity'),
        ('social', 'Social Connection'),
        ('mindfulness', 'Mindfulness'),
        ('creative', 'Creative Expression'),
    ])
    sentiment = models.CharField(max_length=20, choices=[
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative'),
    ])
    created_at = models.DateTimeField(default=timezone.now)
    is_completed = models.BooleanField(default=False)
    is_saved = models.BooleanField(default=False)
    duration = models.CharField(max_length=50, default='15 minutes')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s {self.category} suggestion: {self.suggestion[:50]}..."

class BreathingExercise(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    inhale_duration = models.IntegerField(help_text="Duration in seconds")
    hold_duration = models.IntegerField(help_text="Duration in seconds")
    exhale_duration = models.IntegerField(help_text="Duration in seconds")
    cycles = models.IntegerField(default=5)
    audio_guide = models.FileField(upload_to='breathing_guides/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class MeditationSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(BreathingExercise, on_delete=models.CASCADE)
    duration = models.IntegerField(help_text="Duration in minutes")
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.username}'s {self.exercise.name} session on {self.started_at.strftime('%Y-%m-%d')}"

class WellnessGoal(models.Model):
    GOAL_TYPES = [
        ('water', 'Drink Water'),
        ('sleep', 'Sleep Duration'),
        ('exercise', 'Exercise'),
        ('meditation', 'Meditation'),
        ('custom', 'Custom Goal'),
    ]

    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    custom_goal = models.CharField(max_length=200, blank=True, null=True)
    target = models.CharField(max_length=100)  # e.g., "8 hours" for sleep, "2L" for water
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_check_in = models.DateTimeField(null=True, blank=True)
    streak_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        if self.goal_type == 'custom':
            return f"{self.custom_goal} - {self.user.username}"
        return f"{self.get_goal_type_display()} - {self.user.username}"

class GoalProgress(models.Model):
    goal = models.ForeignKey(WellnessGoal, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    progress = models.CharField(max_length=100)  # e.g., "7 hours" for sleep, "1.5L" for water
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('goal', 'date')

    def __str__(self):
        return f"{self.goal} - {self.date}" 