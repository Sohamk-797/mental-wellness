from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
import json
from .models import MoodEntry, JournalEntry, ChatMessage, SelfCareSuggestion, BreathingExercise, MeditationSession, WellnessGoal
from .forms import MoodEntryForm, JournalEntryForm, UserRegistrationForm, WellnessGoalForm, GoalProgressForm
from .utils import generate_chat_response, get_mood_insights, generate_self_care_suggestions
from collections import Counter
from datetime import datetime, timedelta, timezone
import logging
import time

logger = logging.getLogger(__name__)

@login_required
def home(request):
    # Get recent entries
    recent_moods = MoodEntry.objects.filter(user=request.user).order_by('-created_at')[:5]
    recent_journals = JournalEntry.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get mood analytics data
    mood_entries = MoodEntry.objects.filter(user=request.user).order_by('created_at')
    
    # Calculate mood statistics
    if mood_entries:
        # Get most common mood
        mood_counts = Counter(entry.mood for entry in mood_entries)
        most_common_mood = max(mood_counts.items(), key=lambda x: x[1])[0]
        
        # Calculate average mood
        mood_values = {
            'very_sad': 1,
            'sad': 2,
            'neutral': 3,
            'happy': 4,
            'very_happy': 5
        }
        avg_mood_value = sum(mood_values[entry.mood] for entry in mood_entries) / len(mood_entries)
        average_mood = next(mood for mood, value in mood_values.items() if value == round(avg_mood_value))
        
        # Prepare chart data
        mood_dates = [entry.created_at.strftime('%Y-%m-%d') for entry in mood_entries]
        mood_values = [mood_values[entry.mood] for entry in mood_entries]
        mood_labels = [entry.get_mood_display() for entry in mood_entries]
        
        # Get mood insights
        mood_insights = get_mood_insights(mood_entries)
    else:
        most_common_mood = None
        average_mood = None
        mood_dates = []
        mood_values = []
        mood_labels = []
        mood_insights = None

    # Generate self-care suggestions
    suggestions = generate_self_care_suggestions(request.user, recent_moods, recent_journals)
    
    # Save suggestions to database
    for suggestion_data in suggestions:
        SelfCareSuggestion.objects.create(
            user=request.user,
            suggestion=suggestion_data['suggestion'],
            category=suggestion_data['category'],
            sentiment=suggestion_data['sentiment']
        )
    
    # Get recent suggestions
    recent_suggestions = SelfCareSuggestion.objects.filter(
        user=request.user,
        is_completed=False
    ).order_by('-created_at')[:3]

    context = {
        'recent_moods': recent_moods,
        'recent_journals': recent_journals,
        'mood_insights': mood_insights,
        'most_common_mood': most_common_mood,
        'average_mood': average_mood,
        'mood_dates': json.dumps(mood_dates),
        'mood_values': json.dumps(mood_values),
        'mood_labels': json.dumps(mood_labels),
        'recent_suggestions': recent_suggestions,
    }
    
    return render(request, 'chatbot/home.html', context)

@login_required
def add_mood(request):
    if request.method == 'POST':
        form = MoodEntryForm(request.POST)
        if form.is_valid():
            mood_entry = form.save(commit=False)
            mood_entry.user = request.user
            mood_entry.save()
            messages.success(request, 'Mood entry added successfully!')
            return redirect('home')
    else:
        form = MoodEntryForm()
    return render(request, 'chatbot/add_mood.html', {'form': form})

@login_required
def add_journal(request):
    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            journal_entry = form.save(commit=False)
            journal_entry.user = request.user
            journal_entry.save()
            messages.success(request, 'Journal entry added successfully!')
            return redirect('home')
    else:
        form = JournalEntryForm()
    return render(request, 'chatbot/add_journal.html', {'form': form})

@login_required
@require_http_methods(["POST"])
def chat(request):
    start_time = time.time()
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'error': 'Message cannot be empty',
                'status': 'error'
            }, status=400)
        
        # Get recent chat history using the new method
        recent_messages = ChatMessage.get_recent_chat_history(request.user)
        
        # Build chat history string
        chat_history = ""
        for msg in reversed(recent_messages):
            prefix = "User: " if msg.is_user else "Assistant: "
            chat_history += f"{prefix}{msg.message}\n"
        
        # Save user message
        user_chat = ChatMessage.objects.create(
            user=request.user,
            message=user_message,
            is_user=True
        )
        
        try:
            # Generate AI response with chat history
            ai_response = generate_chat_response(user_message, chat_history)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Save AI response
            ChatMessage.objects.create(
                user=request.user,
                message=ai_response,
                is_user=False,
                response_time=response_time
            )
            
            return JsonResponse({
                'response': ai_response,
                'status': 'success',
                'response_time': round(response_time, 2)
            })
            
        except Exception as e:
            logger.error(f"Error generating chat response: {str(e)}")
            # Save error message
            ChatMessage.objects.create(
                user=request.user,
                message="I apologize, but I'm having trouble responding right now.",
                is_user=False,
                is_error=True,
                error_message=str(e),
                response_time=time.time() - start_time
            )
            
            return JsonResponse({
                'error': 'An error occurred while generating the response',
                'status': 'error'
            }, status=500)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in chat request")
        return JsonResponse({
            'error': 'Invalid JSON',
            'status': 'error'
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in chat: {str(e)}")
        return JsonResponse({
            'error': 'An unexpected error occurred',
            'status': 'error'
        }, status=500)

@login_required(login_url='login')
def mood_history(request):
    mood_entries = MoodEntry.objects.filter(user=request.user)
    return render(request, 'chatbot/mood_history.html', {'mood_entries': mood_entries})

@login_required(login_url='login')
def journal_history(request):
    journal_entries = JournalEntry.objects.filter(user=request.user)
    return render(request, 'chatbot/journal_history.html', {'journal_entries': journal_entries})

@login_required(login_url='login')
def chat_history(request):
    chat_messages = ChatMessage.objects.filter(user=request.user)
    return render(request, 'chatbot/chat_history.html', {'chat_messages': chat_messages})

@login_required
@require_http_methods(['POST'])
@csrf_exempt
def complete_suggestion(request, suggestion_id):
    try:
        suggestion = SelfCareSuggestion.objects.get(id=suggestion_id, user=request.user)
        suggestion.is_completed = True
        suggestion.save()
        return JsonResponse({'status': 'success'})
    except SelfCareSuggestion.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Suggestion not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def breathing_coach(request):
    exercises = BreathingExercise.objects.all()
    completed_sessions = MeditationSession.objects.filter(
        user=request.user,
        completed=True
    ).order_by('-completed_at')[:5]
    return render(request, 'chatbot/breathing_coach.html', {
        'exercises': exercises,
        'completed_sessions': completed_sessions
    })

@login_required
@require_http_methods(['GET'])
def get_exercise(request, exercise_id):
    try:
        exercise = BreathingExercise.objects.get(id=exercise_id)
        data = {
            'id': exercise.id,
            'name': exercise.name,
            'description': exercise.description,
            'inhale_duration': exercise.inhale_duration,
            'hold_duration': exercise.hold_duration,
            'exhale_duration': exercise.exhale_duration,
            'cycles': exercise.cycles,
            'audio_guide': exercise.audio_guide.url if exercise.audio_guide else None
        }
        return JsonResponse(data)
    except BreathingExercise.DoesNotExist:
        return JsonResponse({'error': 'Exercise not found'}, status=404)

@login_required
@require_http_methods(['POST'])
def complete_meditation(request, exercise_id):
    try:
        exercise = BreathingExercise.objects.get(id=exercise_id)
        session = MeditationSession.objects.create(
            user=request.user,
            exercise=exercise,
            duration=exercise.cycles * (exercise.inhale_duration + exercise.hold_duration + exercise.exhale_duration) // 60,
            completed=True,
            completed_at=timezone.now()
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Exercise completed successfully',
            'session_id': session.id
        })
    except BreathingExercise.DoesNotExist:
        return JsonResponse({'error': 'Exercise not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'chatbot/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'chatbot/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@require_http_methods(['POST'])
@csrf_exempt
def refresh_suggestions(request):
    try:
        # Get recent entries for context
        recent_moods = MoodEntry.objects.filter(user=request.user).order_by('-created_at')[:5]
        recent_journals = JournalEntry.objects.filter(user=request.user).order_by('-created_at')[:5]
        
        # Generate new suggestions
        suggestions = generate_self_care_suggestions(request.user, recent_moods, recent_journals)
        
        # Mark old suggestions as completed
        SelfCareSuggestion.objects.filter(
            user=request.user,
            is_completed=False
        ).update(is_completed=True)
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_http_methods(['POST'])
@csrf_exempt
def save_suggestion(request, suggestion_id):
    try:
        suggestion = SelfCareSuggestion.objects.get(id=suggestion_id, user=request.user)
        suggestion.is_saved = True
        suggestion.save()
        return JsonResponse({'status': 'success'})
    except SelfCareSuggestion.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Suggestion not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def wellness_goals(request):
    active_goals = WellnessGoal.objects.filter(user=request.user, is_active=True)
    completed_goals = WellnessGoal.objects.filter(user=request.user, is_active=False)
    
    if request.method == 'POST':
        form = WellnessGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, 'Goal created successfully!')
            return redirect('wellness_goals')
    else:
        form = WellnessGoalForm()
    
    return render(request, 'chatbot/wellness_goals.html', {
        'form': form,
        'active_goals': active_goals,
        'completed_goals': completed_goals,
    })

@login_required
def update_goal_progress(request, goal_id):
    goal = get_object_or_404(WellnessGoal, id=goal_id, user=request.user)
    
    if request.method == 'POST':
        form = GoalProgressForm(request.POST)
        if form.is_valid():
            progress = form.save(commit=False)
            progress.goal = goal
            progress.save()
            
            # Update streak count
            if progress.completed:
                goal.streak_count += 1
            else:
                goal.streak_count = 0
            goal.last_check_in = timezone.now()
            goal.save()
            
            messages.success(request, 'Progress updated successfully!')
            return redirect('wellness_goals')
    else:
        form = GoalProgressForm()
    
    return render(request, 'chatbot/update_progress.html', {
        'form': form,
        'goal': goal,
    })

@login_required
def toggle_goal_status(request, goal_id):
    goal = get_object_or_404(WellnessGoal, id=goal_id, user=request.user)
    goal.is_active = not goal.is_active
    goal.save()
    return redirect('wellness_goals')

def generate_goal_check_in(goal):
    """Generate an AI check-in message for a goal"""
    if not goal.is_active:
        return None
    
    last_check_in = goal.last_check_in
    if last_check_in and (timezone.now() - last_check_in).days < 1:
        return None
    
    streak_message = ""
    if goal.streak_count > 0:
        streak_message = f" You're on a {goal.streak_count}-day streak! Keep it up!"
    
    if goal.goal_type == 'water':
        return f"Time to check in on your water intake goal! Remember to drink {goal.target} today.{streak_message}"
    elif goal.goal_type == 'sleep':
        return f"Don't forget to aim for {goal.target} of sleep tonight.{streak_message}"
    elif goal.goal_type == 'exercise':
        return f"Ready for your {goal.target} exercise session today?{streak_message}"
    elif goal.goal_type == 'meditation':
        return f"Take a moment for your {goal.target} meditation practice.{streak_message}"
    else:
        return f"Time to check in on your goal: {goal.custom_goal}. Target: {goal.target}.{streak_message}"

@login_required
def get_goal_check_ins(request):
    """Get AI check-ins for all active goals"""
    active_goals = WellnessGoal.objects.filter(user=request.user, is_active=True)
    check_ins = []
    
    for goal in active_goals:
        check_in = generate_goal_check_in(goal)
        if check_in:
            check_ins.append({
                'goal': goal,
                'message': check_in
            })
    
    return JsonResponse({'check_ins': check_ins}) 