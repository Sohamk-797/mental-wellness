from django.core.management.base import BaseCommand
from chatbot.models import BreathingExercise

class Command(BaseCommand):
    help = 'Adds default breathing exercises to the database'

    def handle(self, *args, **kwargs):
        exercises = [
            {
                'name': '4-7-8 Breathing',
                'description': 'A calming breathing technique that helps reduce anxiety and promote better sleep.',
                'inhale_duration': 4,
                'hold_duration': 7,
                'exhale_duration': 8,
                'cycles': 4
            },
            {
                'name': 'Box Breathing',
                'description': 'A simple but powerful technique that helps maintain focus and reduce stress.',
                'inhale_duration': 4,
                'hold_duration': 4,
                'exhale_duration': 4,
                'cycles': 5
            },
            {
                'name': 'Deep Breathing',
                'description': 'A basic breathing exercise that helps relax the body and mind.',
                'inhale_duration': 5,
                'hold_duration': 2,
                'exhale_duration': 5,
                'cycles': 5
            },
            {
                'name': 'Calming Breath',
                'description': 'A gentle breathing pattern designed to reduce stress and anxiety.',
                'inhale_duration': 4,
                'hold_duration': 2,
                'exhale_duration': 6,
                'cycles': 6
            }
        ]

        for exercise_data in exercises:
            exercise, created = BreathingExercise.objects.get_or_create(
                name=exercise_data['name'],
                defaults=exercise_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created exercise "{exercise.name}"')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Exercise "{exercise.name}" already exists')
                ) 