import os
from dotenv import load_dotenv

ENV_FILE = r"D:\react-app-oct\txta\.env"

load_dotenv(ENV_FILE, override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(f"GEMINI_API_KEY was not found in {ENV_FILE}")

print("Environment file loaded successfully")
print(f"Key starts with: {api_key[:4]}")
print(f"Key ends with: {api_key[-4:]}")
print(f"Key length: {len(api_key)}")