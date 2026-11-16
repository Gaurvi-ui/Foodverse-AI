# Food Verse AI — Multimodal Food Intelligence Platform

Food Verse AI is an AI-powered food-tech application designed to make food analysis, kitchen intelligence, and personalized meal planning more accessible.

The platform combines multimodal AI capabilities with a modern web application experience.

## Core Features

1. **Food Recognition & Nutrition Audit** — Identify dishes, ingredients, estimated portions, nutritional values, and potential allergens.
2. **Food Freshness & Spoilage Detection** — Analyze visible indicators such as discoloration, texture changes, wrinkles, and mold.
3. **Kitchen Hygiene & Food Safety Review** — Evaluate visible cleanliness indicators and provide preliminary safety observations.
4. **Smart Kitchen Recipe Assistant** — Generate recipes based on available ingredients and dietary preferences.
5. **Personalized 7-Day Meal Planner** — Generate meal plans with estimated nutritional targets and grocery lists.

## Technology Stack

### Modern Application
- Frontend: React.js, Vite, CSS
- Backend: Python, FastAPI
- AI integration: Google Gemini and Groq
- API communication: REST

### Original Prototype
- Python
- Streamlit
- Gemini and Groq integrations

## Project Structure

```text
Foodverse-AI/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Run the Modern React + FastAPI Application

### 1. Backend Setup

```bash
cd backend
py -m venv .venv
```

Activate the environment on Windows:

```cmd
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure your API credentials using the provided `.env.example` as a reference. Keep actual credentials in your local `.env` file.

Start the backend:

```bash
uvicorn app.main:app --reload
```

Backend API documentation:

http://localhost:8000/docs

### 2. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

http://localhost:5173

## Run the Original Streamlit Prototype

The original prototype is preserved in the repository.

From the project root:

```bash
py -m venv .venv
```

Activate the environment and install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
streamlit run app.py
```

## AI Configuration

The application supports Gemini and Groq integrations.

- Configure credentials locally through environment variables.
- Never hardcode API keys in source files.
- Never commit `.env` or Streamlit secrets.
- Demo mode provides illustrative sample responses and should not be confused with real image analysis.

## Important Limitations

- Nutrition values and portion sizes are AI-generated estimates.
- Image-based freshness analysis cannot guarantee that food is safe to consume.
- Allergen alerts should not replace ingredient-label verification.
- Visual hygiene analysis cannot verify invisible contamination or actual sanitation practices.
- Meal plans are informational and are not a substitute for professional medical or dietary advice.

## Development Status

Food Verse AI is under active development. The React + FastAPI implementation is the primary direction for the product, while the original Streamlit prototype remains preserved for reference and functionality.

## Security

Never upload API keys, `.env` files, virtual environments, or dependency directories to GitHub.

---

**Food Verse AI — Making food intelligence smarter, more accessible, and more personal.**