# Food Verse AI — API

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

Set `GEMINI_API_KEY` or `GROQ_API_KEY` as environment variables, or send a key
from the local frontend settings. Do not commit secrets. Demo mode is explicitly
labelled and returns sample data; it does not analyze uploaded images.
