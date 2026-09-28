import json
import os
from typing import Any

from google import genai
from google.genai import types


# Gemini client
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_WORKOUT_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=API_KEY) if API_KEY else None


def fallback_workout(goal: str, intensity: str) -> dict[str, Any]:
    """Fallback workout if Gemini is unavailable."""

    return {
        "title": f"{goal.title()} Workout Plan",
        "goal": goal,
        "intensity": intensity,
        "duration": "30-40 minutes",
        "warmup": [
            "5 minutes brisk walking",
            "Arm circles - 30 seconds",
            "Leg swings - 30 seconds"
        ],
        "exercises": [
            {
                "name": "Bodyweight Squats",
                "sets": 3,
                "reps": 12,
                "rest": "60 seconds"
            },
            {
                "name": "Push Ups",
                "sets": 3,
                "reps": 10,
                "rest": "60 seconds"
            },
            {
                "name": "Lunges",
                "sets": 3,
                "reps": 10,
                "rest": "60 seconds"
            },
            {
                "name": "Plank",
                "sets": 3,
                "reps": 30,
                "rest": "45 seconds"
            }
        ],
        "cooldown": [
            "5 minutes slow walking",
            "Full body stretching"
        ]
    }


def fallback_tip(goal: str) -> str:
    """Fallback nutrition/recovery tip."""

    return (
        "Drink enough water throughout the day, eat balanced meals "
        "with adequate protein, vegetables and whole grains, and get "
        "7-9 hours of sleep for proper recovery."
    )


def generate_workout(
    name: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str
) -> dict[str, Any]:

    if not client:
        return fallback_workout(goal, intensity)

    prompt = f"""
You are FitBuddy, an AI fitness assistant.

Create a safe beginner-friendly workout plan.

User:
Name: {name}
Age: {age}
Weight: {weight} kg
Goal: {goal}
Intensity: {intensity}

Return ONLY valid JSON.

Use this structure:

{{
    "title": "string",
    "goal": "string",
    "intensity": "string",
    "duration": "string",
    "warmup": ["string"],
    "exercises": [
        {{
            "name": "string",
            "sets": 3,
            "reps": 10,
            "rest": "60 seconds"
        }}
    ],
    "cooldown": ["string"]
}}

Do not include markdown.
Do not include explanations outside JSON.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2000,
            ),
        )

        text = response.text.strip()

        # Remove markdown fences if Gemini adds them
        if text.startswith("```"):
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

        return json.loads(text)

    except Exception as e:
        print("Gemini workout error:", e)
        return fallback_workout(goal, intensity)


def generate_nutrition_tip(
    goal: str,
    age: int,
    weight: float
) -> str:

    if not client:
        return fallback_tip(goal)

    prompt = f"""
Give one short and practical nutrition/recovery tip for a person with:

Goal: {goal}
Age: {age}
Weight: {weight} kg

Return only the tip.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.6,
                max_output_tokens=300,
            ),
        )

        return response.text.strip()

    except Exception as e:
        print("Gemini nutrition error:", e)
        return fallback_tip(goal)


def update_workout(
    original_plan: dict[str, Any],
    feedback: str,
    goal: str,
    intensity: str
) -> dict[str, Any]:

    if not client:
        return original_plan

    prompt = f"""
You are FitBuddy.

Update the following workout plan based on user feedback.

Original workout:
{json.dumps(original_plan)}

User feedback:
{feedback}

Goal:
{goal}

Intensity:
{intensity}

Return ONLY valid JSON using this structure:

{{
    "title": "string",
    "goal": "string",
    "intensity": "string",
    "duration": "string",
    "warmup": ["string"],
    "exercises": [
        {{
            "name": "string",
            "sets": 3,
            "reps": 10,
            "rest": "60 seconds"
        }}
    ],
    "cooldown": ["string"]
}}

Do not include markdown.
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2000,
            ),
        )

        text = response.text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

        return json.loads(text)

    except Exception as e:
        print("Gemini update error:", e)
        return original_plan