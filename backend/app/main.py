
from pathlib import Path

from dotenv import load_dotenv

# --------------------------------------------------
# ENVIRONMENT CONFIGURATION
# --------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[1]

load_dotenv(
    BACKEND_DIR / ".env",
    override=True
)

# --------------------------------------------------
# FASTAPI IMPORTS
# --------------------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import food, health, recipes, planner


# --------------------------------------------------
# APPLICATION INITIALIZATION
# --------------------------------------------------

app = FastAPI(
    title="Food Verse AI API",
    version="1.0.0",
    description="Multimodal food intelligence services"
)


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# ROUTE REGISTRATION
# --------------------------------------------------

app.include_router(
    food.router,
    prefix="/api/food",
    tags=["Food Intelligence"]
)

app.include_router(
    health.router,
    prefix="/api/kitchen",
    tags=["Kitchen Safety"]
)

app.include_router(
    recipes.router,
    prefix="/api/recipes",
    tags=["Recipes"]
)

app.include_router(
    planner.router,
    prefix="/api/planner",
    tags=["Meal Planner"]
)


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "Food Verse AI",
        "version": "1.0.0"
    }


# --------------------------------------------------
# ROOT ENDPOINT
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Welcome to Food Verse AI API",
        "docs": "/docs",
        "status": "running"
    }
