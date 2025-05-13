import os
from django.conf import settings
from datetime import datetime
from dotenv import load_dotenv
from django.contrib.auth.models import User
from chatbot.models import MoodEntry, JournalEntry, ChatMessage, SelfCareSuggestion
from openai import OpenAI

load_dotenv()

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def generate_chat_response(message, chat_history=None):
    """
    Generate a response using OpenAI's GPT model.
    """
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Prepare messages for the chat
        messages = [
            {"role": "system", "content": "You are a supportive and empathetic mental wellness assistant. Your responses should be helpful, understanding, and focused on promoting mental well-being. Keep responses concise and natural."}
        ]
        
        # Add chat history if available
        if chat_history:
            messages.append({"role": "user", "content": chat_history})
        
        # Add the current message
        messages.append({"role": "user", "content": message})
        
        # Generate response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.5
        )
        
        # Extract and return the response
        ai_response = response.choices[0].message.content.strip()
        if not ai_response:
            raise Exception("Empty response generated")
            
        return ai_response
            
    except Exception as e:
        print(f"OpenAI Error: {str(e)}")
        # Provide more natural fallback responses
        fallback_responses = [
            "I understand you're reaching out. Could you tell me more about what's on your mind?",
            "I'm here to chat. What would you like to talk about?",
            "I'm listening. Feel free to share your thoughts or feelings.",
            "I'm here to support you. What's been going on lately?",
            "I'd love to hear more about what you're experiencing. Would you like to share?"
        ]
        import random
        return random.choice(fallback_responses)

def get_mood_insights(mood_entries):
    """
    Generate insights based on mood entries.
    """
    if not mood_entries:
        return "No mood entries available for analysis."
    
    try:
        # Format mood entries safely
        mood_data = []
        for entry in mood_entries[:10]:
            try:
                # Safely format the date
                if hasattr(entry, 'created_at'):
                    date_str = entry.created_at.strftime('%Y-%m-%d')
                else:
                    date_str = datetime.now().strftime('%Y-%m-%d')
                
                # Safely get mood and notes
                mood = getattr(entry, 'mood', 'Unknown')
                notes = getattr(entry, 'notes', '')
                
                mood_data.append(f"Date: {date_str}, Mood: {mood}, Notes: {notes}")
            except Exception:
                continue
        
        if not mood_data:
            return "I notice you've been tracking your moods. That's a great step towards self-awareness. Would you like to share more about how you're feeling today?"
        
        mood_data_str = "\n".join(mood_data)
        
        # Use DialoGPT for mood insights
        prompt = f"""Based on these mood entries, provide a brief, supportive analysis:
        {mood_data_str}
        
        Focus on:
        1. Identifying patterns or trends
        2. Offering positive observations
        3. Suggesting coping strategies
        4. Maintaining an encouraging tone"""
        
        response = generate_chat_response(prompt)
        return response if response else "I notice you've been tracking your moods. That's a great step towards self-awareness. Would you like to share more about how you're feeling today?"
        
    except Exception as e:
        return "I notice you've been tracking your moods. That's a great step towards self-awareness. Would you like to share more about how you're feeling today?"

def generate_self_care_suggestions(user, mood_entries=None, journal_entries=None):
    """
    Generate personalized self-care suggestions based on user's mood, journal entries, and conversation context.
    """
    try:
        # Get recent mood and journal entries if not provided
        if not mood_entries:
            mood_entries = MoodEntry.objects.filter(user=user).order_by('-created_at')[:5]
        if not journal_entries:
            journal_entries = JournalEntry.objects.filter(user=user).order_by('-created_at')[:5]

        # Get recent chat messages for context
        recent_chats = ChatMessage.objects.filter(user=user).order_by('-created_at')[:10]

        # Analyze sentiment from recent entries
        sentiment = 'neutral'
        sentiment_scores = []
        
        # Analyze mood entries
        if mood_entries:
            mood_values = {
                'very_sad': 1,
                'sad': 2,
                'neutral': 3,
                'happy': 4,
                'very_happy': 5
            }
            mood_scores = [mood_values[entry.mood] for entry in mood_entries]
            sentiment_scores.extend(mood_scores)

        # Analyze journal entries
        for entry in journal_entries:
            label, score = get_sentiment(entry.content)
            sentiment_scores.append(score if label == 'POSITIVE' else -score)

        # Analyze chat messages
        for chat in recent_chats:
            if not chat.is_user:  # Only analyze bot responses
                label, score = get_sentiment(chat.message)
                sentiment_scores.append(score if label == 'POSITIVE' else -score)

        # Calculate overall sentiment
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            if avg_sentiment <= -0.3:
                sentiment = 'negative'
            elif avg_sentiment >= 0.3:
                sentiment = 'positive'

        # Prepare context for suggestion generation
        context = f"User's emotional state: {sentiment}\n"
        
        # Add recent themes from journal entries
        if journal_entries:
            context += "Recent themes:\n"
            for entry in journal_entries:
                context += f"- {entry.content[:100]}...\n"

        # Add recent activities from chat
        if recent_chats:
            context += "Recent conversation context:\n"
            for chat in recent_chats:
                context += f"- {chat.message[:100]}...\n"

        # Generate suggestions based on sentiment and context
        prompt = f"""Based on the following user context, generate 5 personalized self-care suggestions:
        {context}
        
        Consider:
        1. User's current emotional state ({sentiment})
        2. Recent activities and themes
        3. Different categories:
           - relaxation (e.g., music, breathing exercises, warm baths)
           - physical activity (e.g., walks, stretching, gentle exercise)
           - social connection (e.g., reaching out to friends, group activities)
           - mindfulness (e.g., meditation, grounding exercises)
           - creative expression (e.g., art, writing, music)
        4. Practical and achievable activities
        5. Time of day and typical user schedule
        
        Format each suggestion as: category|suggestion|duration
        Example: relaxation|Take a warm bath with lavender essential oils|20 minutes
        """

        response = generate_chat_response(prompt)
        if not response:
            return []

        # Parse suggestions
        suggestions = []
        for line in response.strip().split('\n'):
            if '|' in line:
                try:
                    category, suggestion, duration = line.split('|', 2)
                    category = category.strip().lower()
                    suggestion = suggestion.strip()
                    duration = duration.strip()

                    # Map category to model choices
                    category_mapping = {
                        'relaxation': 'relaxation',
                        'physical': 'physical',
                        'social': 'social',
                        'mindfulness': 'mindfulness',
                        'creative': 'creative'
                    }

                    if category in category_mapping:
                        # Create and save the suggestion
                        suggestion_obj = SelfCareSuggestion.objects.create(
                            user=user,
                            suggestion=f"{suggestion} (Duration: {duration})",
                            category=category_mapping[category],
                            sentiment=sentiment
                        )
                        suggestions.append({
                            'category': category_mapping[category],
                            'suggestion': suggestion,
                            'duration': duration,
                            'sentiment': sentiment
                        })
                except Exception as e:
                    print(f"Error parsing suggestion: {str(e)}")
                    continue

        return suggestions

    except Exception as e:
        print(f"Error generating self-care suggestions: {str(e)}")
        return [] 