# Food Verse AI — Multimodal Food Intelligence Agent

**Skill Wallet Capstone Project 3**

A modular Streamlit app with five food-intelligence pillars:
1. Food recognition & nutrition audit
2. Food freshness & spoilage diagnostic
3. Kitchen hygiene & food safety compliance
4. Smart kitchen recipe assistant
5. Personalized 7-day meal planner

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

The app works in **standalone demo mode** without an API key. Demo results are illustrative and explicitly labeled; they do not analyze uploaded media.

## Enable live AI

Use the sidebar to choose Gemini or Groq and paste the corresponding API key. For a deployed app, use Streamlit Secrets instead of hardcoding keys.

Create `.streamlit/secrets.toml`:

```toml
[gemini]
api_key = "YOUR_GEMINI_API_KEY"

# Or, instead:
[groq]
api_key = "YOUR_GROQ_API_KEY"
```

Never commit `secrets.toml` to version control. Add it to `.gitignore`.

### Provider notes
- **Gemini:** Uses the Google Gen AI SDK and `gemini-2.5-flash` for JSON-formatted multimodal responses.
- **Groq:** Uses the Groq SDK and an OpenAI-compatible image input format with `meta-llama/llama-4-scout-17b-16e-instruct`. Model availability can change; if your account does not have access to this model, update the model constant in `app.py` to a currently supported vision model.

## Deploy to Streamlit Community Cloud

1. Push `app.py`, `requirements.txt`, and this README to a GitHub repository.
2. Create a new app in Streamlit Community Cloud and select `app.py`.
3. Add provider credentials under the app's **Secrets** settings using the TOML format above.
4. Deploy. Demo mode can be used if no secrets are configured.

## Safety, accuracy, and privacy
- Photo-based nutrition values and portion sizes are estimates, not laboratory measurements.
- Image analysis cannot confirm that food is pathogen-free or safe to eat.
- Allergen detection must never replace label checking or direct confirmation with the food preparer.
- The kitchen hygiene score is a preliminary visual aid, not an official inspection or certification.
- BMR/TDEE are estimates. The meal planner is not medical advice; users with clinical needs should consult a qualified professional.
- In live AI mode, uploaded images are sent to the selected provider for processing. Review provider policies before uploading sensitive content.

## Project structure

```text
food_verse_ai/
├── app.py
├── requirements.txt
└── README.md
```
