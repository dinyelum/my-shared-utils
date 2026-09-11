import json
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError


def generate_gemini_content(
    client,
    prompt: str,
    system_instruction: str,
    model: str = 'gemini-3.5-flash-lite',
    max_retry: int = 3
) -> dict:
    """Generates structured JSON content using the Gemini API.

    Args:
        client: An initialized genai.Client instance.
        prompt: The complete text prompt, including any formatted input data.
        system_instruction: Behavioral instructions for the model.
        model: The Gemini model identifier. Defaults to 'gemini-3.5-flash-lite'.
    """

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)

    except APIError as e:
        if e.code == 429:
            print(
                f"Rate limit hit (429). Waiting 60 seconds... | Error: {e.message}")

            retry_attempt = 3 - max_retry
            time.sleep(60 * (2 ** retry_attempt))

            # Pro-tip: Proactively retry once rather than returning None immediately
            if max_retry > 0:
                return generate_gemini_content(
                    client=client,
                    prompt=prompt,
                    system_instruction=system_instruction,
                    model=model,
                    max_retry=max_retry - 1
                )
            print(f"All retries failed. Returning None.")
        else:
            print(f"Google API Error ({e.code}): {e.message}")
    except json.JSONDecodeError:
        print("Failed to decode JSON from model response.")

    except Exception as e:
        # Catch-all for any other Python/network exceptions
        print(f"An unexpected error occurred: {e}")

    return None
