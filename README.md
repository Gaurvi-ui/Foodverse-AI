# Food Verse AI — Multimodal Food Intelligence

This is the first React + FastAPI development foundation, replacing the Streamlit-only interface while retaining the existing product's five intelligence pillars.

## Project structure
- `frontend/` — React + Vite responsive web interface.
- `backend/` — FastAPI service, provider integration, and API routes.
- Demo mode is labelled and returns sample data; it does **not** inspect uploaded images.

## Run locally (Windows PowerShell)

### 1. Backend
```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API docs: http://localhost:8000/docs

### 2. Frontend (new terminal)
```powershell
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## AI provider setup
Use the settings icon in the web app to select Gemini or Groq, paste a key for the current browser session, and switch off demo mode. For local backend-only configuration, copy `backend/.env.example` to `.env` and export the relevant environment variable before starting the API. Never commit real keys.

## Important first-release limitations
- Kitchen review currently accepts still images, not video.
- User profiles and analysis history are not yet persisted.
- Nutrition and freshness results are visual estimates; images cannot establish exact nutrient values, pathogen absence, or food safety.
- The first version is a local development build. Production deployment still needs HTTPS, managed secrets, rate limiting, logging, privacy disclosures, and a persistent data strategy.
