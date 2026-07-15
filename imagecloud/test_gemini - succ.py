import os
import traceback

from dotenv import load_dotenv
from google import genai


ENV_FILE = r"D:\react-app-oct\txta\.env"

load_dotenv(ENV_FILE, override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(f"GEMINI_API_KEY was not found in {ENV_FILE}")

print("=" * 70)
print("Gemini text connection test")
print("=" * 70)
print(f"Key detected: {api_key[:4]}...{api_key[-4:]}")
print(f"Key length: {len(api_key)}")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents="Reply with exactly: Gemini connection successful",
    )

    print("\nSUCCESS")
    print(response.text)

except Exception as error:
    print("\nFAILED")
    print(f"Error type: {type(error).__name__}")
    print(f"Error message: {error}")

    print("\nFULL TRACEBACK")
    traceback.print_exc()

finally:
    client.close()