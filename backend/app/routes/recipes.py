
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from app.services.ai import analyze

router = APIRouter()

VALID_PROVIDERS = {"gemini", "groq"}

class RecipeRequest(BaseModel):
    pantry: str = Field(min_length=2, max_length=3000)
    cuisine: str = Field(default="Any", min_length=1, max_length=50)
    dietary: list[str] = Field(default_factory=list)
    max_minutes: int = Field(default=30, ge=10, le=180)
    servings: int = Field(default=2, ge=1, le=12)
    provider: str = "gemini"
    api_key: str = Field(default="", max_length=500)
    demo: bool = False

    @field_validator("pantry")
    @classmethod
    def validate_pantry(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Please provide at least one pantry ingredient.")
        return value

    @field_validator("dietary")
    @classmethod
    def validate_dietary(cls, value):
        cleaned = list(dict.fromkeys(
            item.strip() for item in value if item.strip()
        ))
        if len(cleaned) > 15:
            raise ValueError("Please provide no more than 15 dietary preferences.")
        return cleaned

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value):
        value = value.strip().lower()
        if value not in VALID_PROVIDERS:
            raise ValueError("Provider must be gemini or groq.")
        return value


@router.post("/generate")
def generate_recipes(body: RecipeRequest):

    prompt = f"""
You are Food Verse AI, an intelligent recipe generation assistant.

Generate up to 3 practical recipes using the user's available pantry.

PANTRY INVENTORY:
{body.pantry}

USER PREFERENCES:
Cuisine: {body.cuisine}
Dietary restrictions/preferences: {', '.join(body.dietary) or 'None specified'}
Maximum preparation and cooking time: {body.max_minutes} minutes
Servings: {body.servings}

REQUIREMENTS:
1. Prioritize ingredients already available in the pantry.
2. Do not assume unavailable ingredients are present.
3. Clearly identify additional ingredients that must be purchased.
4. Respect all dietary restrictions.
5. Flag any dietary conflicts rather than silently ignoring them.
6. Keep preparation time within the requested limit.
7. Provide realistic ingredient quantities and clear instructions.
8. Give approximate nutritional values per serving.
9. Do not invent exact nutritional precision.

RETURN ONLY VALID JSON in this structure:

{{
    "recipes": [
        {{
            "name": "Recipe name",
            "description": "Short description",
            "time_minutes": 25,
            "difficulty": "Easy",
            "servings": {body.servings},
            "ingredients": [
                {{
                    "name": "Ingredient",
                    "quantity": "1 cup",
                    "available_in_pantry": true
                }}
            ],
            "instructions": [
                "Step 1",
                "Step 2"
            ],
            "substitutions": [
                "Suggested alternative"
            ],
            "additional_ingredients": [
                "Items not available in pantry"
            ],
            "nutrition_per_serving": {{
                "calories_kcal": 350,
                "protein_g": 15,
                "carbohydrates_g": 40,
                "fats_g": 12,
                "fiber_g": 6
            }},
            "nutrition_note": "Approximate values; actual nutrition varies."
        }}
    ],
    "dietary_warnings": [],
    "confidence_note": "Nutrition and ingredient availability are estimates."
}}
"""

    try:
        result = analyze(
            kind="recipes",
            prompt=prompt,
            provider=body.provider,
            api_key=body.api_key.strip() or None,
            demo=body.demo
        )

        return result

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Recipe generation failed. Please try again."
        )
