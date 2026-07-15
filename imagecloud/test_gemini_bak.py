import json
import os

from dotenv import load_dotenv
from google import genai
from PIL import Image

from prompt import IMAGE_PROMPT


# ---------------------------------------------------------
# Load Environment Variables
# ---------------------------------------------------------

load_dotenv(r"D:\react-app-oct\txta\.env")

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise Exception("GEMINI_API_KEY not found in .env")


# ---------------------------------------------------------
# Gemini Client
# ---------------------------------------------------------

client = genai.Client(api_key=API_KEY)


# ---------------------------------------------------------
# Test Image
# ---------------------------------------------------------

IMAGE_PATH = r"D:\react-app-oct\txta\brahma\Miracle Red Juice.png"


if not os.path.exists(IMAGE_PATH):
    raise Exception(f"Image not found : {IMAGE_PATH}")


# ---------------------------------------------------------
# Open Image
# ---------------------------------------------------------

image = Image.open(IMAGE_PATH)


# ---------------------------------------------------------
# Call Gemini
# ---------------------------------------------------------

print("=" * 70)
print("Sending image to Gemini...")
print("=" * 70)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        IMAGE_PROMPT,
        image
    ]
)


# ---------------------------------------------------------
# Raw Response
# ---------------------------------------------------------

print("\n")
print("=" * 70)
print("RAW RESPONSE")
print("=" * 70)
print(response.text)


# ---------------------------------------------------------
# Convert JSON
# ---------------------------------------------------------

print("\n")
print("=" * 70)
print("PARSED JSON")
print("=" * 70)

text = response.text.strip()

# remove markdown if Gemini returns ```json

text = text.replace("```json", "")
text = text.replace("```", "")
text = text.strip()

try:

    result = json.loads(text)

    print(json.dumps(result, indent=4))

except Exception as ex:

    print("Unable to parse JSON")
    print(ex)

print("\nFinished.")