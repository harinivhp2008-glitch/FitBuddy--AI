from .config import get_settings
from .gemini_client import generate_text
from .schemas import UserInput


def generate_workout_gemini(
    data: UserInput,
) -> str:

    settings = get_settings()

    prompt = f"""
You are FitBuddy, an AI fitness-planning assistant.

Create a personalized 7-day workout plan for this user.

USER INFORMATION

Name:
{data.username}

Age:
{data.age}

Weight:
{data.weight} kg

Fitness Goal:
{data.goal}

Preferred Intensity:
{data.intensity}


REQUIREMENTS

1. Create exactly seven labeled days.

2. For every day include:
   - Focus
   - Warm-up
   - Main workout
   - Cooldown/recovery

3. For the main workout include exercises with:
   - Sets and repetitions OR duration
   - Rest periods where useful

4. Match the requested fitness goal.

5. Match the requested intensity.

6. Include an appropriate recovery or rest day.

7. Keep the routine practical for a general
   beginner/intermediate user.

8. Do not prescribe medication.

9. Do not diagnose medical conditions.

10. Do not recommend dangerous exercise.

11. If an exercise has an obvious safety concern,
    provide a safer alternative.

12. Avoid extreme dieting recommendations.

13. End with a short Safety Note.

The Safety Note should advise the user to stop
exercise if they experience significant pain,
dizziness, or unusual symptoms and to consult
a qualified healthcare or fitness professional
when appropriate.

Use clear plain-text headings.

Do not use unnecessary markdown tables.
"""

    return generate_text(
        model=settings.gemini_workout_model,
        prompt=prompt,
        max_output_tokens=5000,
        temperature=0.6,
    )