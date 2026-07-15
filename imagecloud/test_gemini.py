import json
import os
import traceback

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

from prompt import IMAGE_PROMPT


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

ENV_FILE = r"D:\react-app-oct\txta\.env"

IMAGE_PATH = (
    r"D:\react-app-oct\txta\brahma\Miracle Red Juice.png"
)

MODEL_NAME = "gemini-3.5-flash"


# ---------------------------------------------------------
# Load API key
# ---------------------------------------------------------

load_dotenv(ENV_FILE, override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        f"GEMINI_API_KEY was not found in {ENV_FILE}"
    )


# ---------------------------------------------------------
# Validate image
# ---------------------------------------------------------

if not os.path.isfile(IMAGE_PATH):
    raise FileNotFoundError(
        f"Image not found: {IMAGE_PATH}"
    )


# ---------------------------------------------------------
# Create Gemini client
# ---------------------------------------------------------

client = genai.Client(api_key=api_key)


# ---------------------------------------------------------
# Send image
# ---------------------------------------------------------

print("=" * 70)
print("Sending image to Gemini...")
print(f"Model: {MODEL_NAME}")
print(f"Image: {IMAGE_PATH}")
print("=" * 70)

try:
    with Image.open(IMAGE_PATH) as source_image:
        image = source_image.convert("RGB")

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                IMAGE_PROMPT,
                image,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    # -----------------------------------------------------
    # Raw response
    # -----------------------------------------------------

    print("\n" + "=" * 70)
    print("RAW RESPONSE")
    print("=" * 70)
    print(response.text)

    # -----------------------------------------------------
    # Parse JSON
    # -----------------------------------------------------

    text = response.text.strip()

    text = text.removeprefix("```json")
    text = text.removeprefix("```")
    text = text.removesuffix("```")
    text = text.strip()

    result = json.loads(text)

    print("\n" + "=" * 70)
    print("PARSED JSON")
    print("=" * 70)
    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False,
        )
    )

except json.JSONDecodeError as error:
    print("\nGemini responded, but the result was not valid JSON.")
    print(f"JSON error: {error}")
    print(f"Response: {response.text!r}")
    raise

except Exception as error:
    print("\nGemini image request failed.")
    print(f"Error type: {type(error).__name__}")
    print(f"Error message: {error}")

    print("\nFULL TRACEBACK")
    traceback.print_exc()

    raise

finally:
    client.close()

print("\nFinished.")