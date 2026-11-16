
import os
from pathlib import Path
from dotenv import load_dotenv

# Load backend environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing from .env")

from app.services.ai import _analyze_groq, GROQ_MODEL

print("Testing Groq connection...")
print("Model:", GROQ_MODEL)

try:
    result = _analyze_groq(
        prompt=(
            "Return a JSON object with two fields: "
            "status set to success and message set to "
            "Groq connection working."
        ),
        image_bytes=None,
        mime_type="image/jpeg",
        api_key=api_key
    )

    print("\nGROQ CONNECTION SUCCESSFUL")
    print(result)

except Exception as exc:
    print("\nGROQ CONNECTION FAILED")
    print(type(exc).__name__, str(exc))
