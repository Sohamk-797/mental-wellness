import os
from django.conf import settings
from datetime import datetime
from dotenv import load_dotenv
from django.contrib.auth.models import User
from chatbot.models import MoodEntry, JournalEntry, ChatMessage, SelfCareSuggestion
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import logging

load_dotenv()

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize model and tokenizer as None
model = None
tokenizer = None

def load_model():
    """Load the DialoGPT model and tokenizer."""
    global model, tokenizer
    
    try:
        # Set environment variables for offline mode
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['HF_DATASETS_OFFLINE'] = '1'
        
        # Define model paths
        model_path = os.path.join(settings.BASE_DIR, 'models', 'dialoGPT-small')
        config_path = os.path.join(model_path, 'config.json')
        
        # Check if model files exist
        if not os.path.exists(config_path):
            logger.warning(f"Model files not found at {model_path}. Using fallback responses.")
            return False
            
        # Load model and tokenizer from local path
        tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True)
        logger.info("Successfully loaded DialoGPT model from local files")
        return True
        
    except Exception as e:
        logger.error(f"Error loading DialoGPT model: {str(e)}")
        return False

def format_chat_history(chat_history):
    """
    Format chat history into a string for the model.
    """
    if not chat_history:
        return ""
    
    formatted_history = []
    for msg in chat_history.split('\n'):
        if msg.strip():
            formatted_history.append(msg.strip())
    return '\n'.join(formatted_history)

def get_response(user_input):
    """Get a response from the model or fallback to predefined responses."""
    global model, tokenizer
    
    # Fallback responses if model fails to load
    fallback_responses = [
        "I understand you're feeling down. Would you like to talk about what's bothering you?",
        "It's okay to feel this way. Remember, you're not alone in this journey.",
        "I'm here to listen. Would you like to try some breathing exercises?",
        "Let's take a moment to breathe together. Would that help?",
        "I'm sorry you're feeling this way. Would you like to explore some coping strategies?"
    ]
    
    try:
        if model is None or tokenizer is None:
            if not load_model():
                # Return a random fallback response if model loading fails
                import random
                return random.choice(fallback_responses)
        
        # Encode the input and generate response
        input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors='pt')
        response_ids = model.generate(
            input_ids,
            max_length=1000,
            pad_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=3,
            do_sample=True,
            top_k=100,
            top_p=0.7,
            temperature=0.8
        )
        
        # Decode and return the response
        response = tokenizer.decode(response_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
        return response if response.strip() else random.choice(fallback_responses)
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
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
        
        response = get_response(prompt)
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

        response = get_response(prompt)
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