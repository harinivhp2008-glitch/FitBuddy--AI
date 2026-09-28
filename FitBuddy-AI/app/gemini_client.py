from functools import lru_cache

from .config import get_settings


class GeminiServiceError(RuntimeError):
    """
    Raised when Gemini is unavailable or returns an unusable response.
    """


@lru_cache
def get_client():

    try:
        from google import genai

    except ImportError as exc:
        raise GeminiServiceError(
            "The Gemini SDK is not installed. "
            "Run: pip install -r requirements.txt"
        ) from exc

    settings = get_settings()

    if not settings.gemini_api_key:
        raise GeminiServiceError(
            "GEMINI_API_KEY is not configured. "
            "Add it to your .env file."
        )

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def generate_text(
    *,
    model: str,
    prompt: str,
    max_output_tokens: int = 4096,
    temperature: float = 0.7,
) -> str:

    try:
        from google.genai import types

        client = get_client()

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )

        text = (
            response.text
            or ""
        ).strip()

        if not text:
            raise GeminiServiceError(
                "Gemini returned an empty response."
            )

        return text

    except GeminiServiceError:
        raise

    except ImportError as exc:
        raise GeminiServiceError(
            "The Gemini SDK is not installed. "
            "Run: pip install -r requirements.txt"
        ) from exc

    except Exception as exc:
        raise GeminiServiceError(
            f"Gemini request failed: {exc}"
        ) from exc