from dotenv import load_dotenv
from google import genai
from google.genai import types
import os

load_dotenv(".env", override=True)

key = os.getenv("GEMINI_API_KEY", "").strip()

if not key:
    raise ValueError("GEMINI_API_KEY missing from .env")

client = genai.Client(
    api_key=key,
    http_options=types.HttpOptions(timeout=15000)
)

model = "gemini-3.5-flash"

print("Testing:", model)

try:
    response = client.models.generate_content(
        model=model,
        contents="Reply with OK only."
    )
    print("SUCCESS:", response.text)

except Exception as error:
    print("ERROR TYPE:", type(error).__name__)
    print("ERROR DETAILS:", str(error)[:500])