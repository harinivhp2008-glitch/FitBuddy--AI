from .config import get_settings
from .gemini_client import generate_text


def generate_nutrition_tip_with_flash(
    goal: str,
) -> str:

    settings = get_settings()

    prompt = f"""
You are FitBuddy's nutrition and recovery assistant.

Fitness goal:

{goal}

Give the user ONE concise and practical
nutrition or recovery recommendation.

Keep it between 2 and 4 sentences.

Prefer advice involving:

- balanced meals
- hydration
- adequate protein
- fruits and vegetables
- sleep
- recovery
- sustainable habits

Do not recommend:

- extreme calorie restriction
- dangerous diets
- medication
- supplements as medical treatment

Do not diagnose medical conditions.

Mention that individual nutrition needs
can vary between people.
"""

    return generate_text(
        model=settings.gemini_nutrition_model,
        prompt=prompt,
        max_output_tokens=500,
        temperature=0.5,
    )