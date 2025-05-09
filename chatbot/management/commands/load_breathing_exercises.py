from django.core.management.base import BaseCommand
from chatbot.models import BreathingExercise

class Command(BaseCommand):
    help = 'Loads default breathing exercises into the database'

    def handle(self, *args, **kwargs):
        exercises = [
            {
                'name': '4-7-8 Breathing',
                'description': 'A calming breathing technique that helps reduce anxiety and promote sleep. Inhale for 4 seconds, hold for 7 seconds, and exhale for 8 seconds.',
                'inhale_duration': 4,
                'hold_duration': 7,
                'exhale_duration': 8,
                'cycles': 4
            },
            {
                'name': 'Box Breathing',
                'description': 'A technique used by Navy SEALs to maintain calm and focus. Equal duration for inhale, hold, exhale, and hold.',
                'inhale_duration': 4,
                'hold_duration': 4,
                'exhale_duration': 4,
                'cycles': 5
            },
            {
                'name': 'Deep Calming Breath',
                'description': 'A gentle breathing exercise to reduce stress and anxiety. Longer exhale than inhale.',
                'inhale_duration': 4,
                'hold_duration': 2,
                'exhale_duration': 6,
                'cycles': 6
            },
            {
                'name': 'Morning Energizer',
                'description': 'An invigorating breathing pattern to start your day with energy and focus.',
                'inhale_duration': 6,
                'hold_duration': 2,
                'exhale_duration': 4,
                'cycles': 5
            },
            {
                'name': 'Stress Relief',
                'description': 'A quick breathing exercise to help manage stress in the moment.',
                'inhale_duration': 5,
                'hold_duration': 3,
                'exhale_duration': 7,
                'cycles': 3
            }
        ]

        for exercise_data in exercises:
            BreathingExercise.objects.get_or_create(
                name=exercise_data['name'],
                defaults=exercise_data
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created breathing exercise: {exercise_data["name"]}')
            ) 