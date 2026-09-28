from .config import get_settings
from .gemini_client import generate_text


def update_workout_plan(
    *,
    original_plan: str,
    feedback: str,
    goal: str,
    intensity: str,
) -> str:

    settings = get_settings()

    prompt = f"""
You are updating a FitBuddy 7-day workout plan.

Fitness Goal:

{goal}

Preferred Intensity:

{intensity}


ORIGINAL PLAN:

{original_plan}


USER FEEDBACK:

{feedback}


TASK

Create a revised seven-day workout plan.

Incorporate the user's feedback while keeping
the plan appropriate for the user's goal
and requested intensity.

Keep this structure:

Day
Focus
Warm-up
Main workout
Cooldown/recovery

Keep the plan practical and safe.

Do not:

- diagnose injuries
- prescribe medication
- recommend dangerous exercise
- recommend extreme dieting

If the user's feedback requests something
unsafe, provide a safer alternative.

Finish with a short Safety Note.
"""

    return generate_text(
        model=settings.gemini_workout_model,
        prompt=prompt,
        max_output_tokens=5000,
        temperature=0.6,
    )