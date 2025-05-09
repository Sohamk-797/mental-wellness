from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('mood-history/', views.mood_history, name='mood_history'),
    path('journal-history/', views.journal_history, name='journal_history'),
    path('chat-history/', views.chat_history, name='chat_history'),
    path('add-mood/', views.add_mood, name='add_mood'),
    path('add-journal/', views.add_journal, name='add_journal'),
    path('chat/', views.chat, name='chat'),
    path('complete-suggestion/<int:suggestion_id>/', views.complete_suggestion, name='complete_suggestion'),
    path('save-suggestion/<int:suggestion_id>/', views.save_suggestion, name='save_suggestion'),
    path('refresh-suggestions/', views.refresh_suggestions, name='refresh_suggestions'),
    path('breathing-coach/', views.breathing_coach, name='breathing_coach'),
    path('get-exercise/<int:exercise_id>/', views.get_exercise, name='get_exercise'),
    path('complete-meditation/<int:session_id>/', views.complete_meditation, name='complete_meditation'),
    path('wellness-goals/', views.wellness_goals, name='wellness_goals'),
    path('update-goal-progress/<int:goal_id>/', views.update_goal_progress, name='update_goal_progress'),
    path('toggle-goal-status/<int:goal_id>/', views.toggle_goal_status, name='toggle_goal_status'),
    path('get-goal-check-ins/', views.get_goal_check_ins, name='get_goal_check_ins'),
] 