import traceback

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationError

from app.services.ai import analyze

router = APIRouter()

FACTORS = {
    "Sedentary": 1.2,
    "Light": 1.375,
    "Moderate": 1.55,
    "Very active": 1.725,
    "Extra active": 1.9
}

GOAL_ADJUSTMENTS = {
    "Fat Loss": -300,
    "Muscle Gain": 250,
    "Maintain Weight": 0
}


class PlannerRequest(BaseModel):
    age: int = Field(ge=18, le=100)

    sex: Literal["Male", "Female", "Other"]

    weight_kg: float = Field(ge=30, le=300)
    height_cm: float = Field(ge=120, le=230)

    activity: Literal[
        "Sedentary",
        "Light",
        "Moderate",
        "Very active",
        "Extra active"
    ]

    goal: Literal[
        "Fat Loss",
        "Muscle Gain",
        "Maintain Weight"
    ]

    dietary: list[str] = Field(default_factory=list, max_length=15)
    meals_per_day: int = Field(default=3, ge=3, le=5)

    cuisine: str = Field(default="Indian", min_length=1, max_length=50)
    exclusions: str = Field(default="", max_length=1000)

    provider: Literal["gemini", "groq"] = "gemini"
    api_key: str = Field(default="", max_length=500)
    demo: bool = False

    @field_validator("dietary")
    @classmethod
    def clean_dietary(cls, value):
        return list(dict.fromkeys(
            item.strip()
            for item in value
            if item.strip()
        ))

    @field_validator("cuisine")
    @classmethod
    def clean_cuisine(cls, value):
        return value.strip()

    @field_validator("exclusions")
    @classmethod
    def clean_exclusions(cls, value):
        return value.strip()




# --------------------------------------------------
# AI RESPONSE SCHEMAS
# --------------------------------------------------

class PlannerMeal(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    meal: str = Field(min_length=1, max_length=40)
    dish: str = Field(min_length=2, max_length=160)
    approximate_calories: int = Field(gt=0, le=2500)
    notes: str = Field(default="", max_length=500)


class PlannerDay(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    day: str = Field(min_length=1, max_length=20)
    meals: list[PlannerMeal] = Field(min_length=1, max_length=5)


class GroceryItem(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    item: str = Field(min_length=1, max_length=120)
    quantity: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=60)


class EnergyEstimates(BaseModel):
    bmr_kcal: int = Field(gt=0, le=10000)
    tdee_kcal: int = Field(gt=0, le=15000)
    target_kcal: int = Field(gt=0, le=10000)


class PlannerResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    daily_calories: int = Field(gt=0, le=10000)
    meal_plan: list[PlannerDay] = Field(min_length=7, max_length=7)
    grocery_list: list[GroceryItem] = Field(min_length=1, max_length=150)
    nutrition_notes: list[str] = Field(min_length=1, max_length=30)

    provider_used: Literal["gemini", "groq"] | None = None
    fallback_used: bool | None = None
    fallback_reason: str | None = Field(default=None, max_length=300)
    demo: bool = False
    energy_estimates: EnergyEstimates | None = None

    @field_validator("nutrition_notes")
    @classmethod
    def validate_notes(cls, values):
        cleaned = [note.strip() for note in values if isinstance(note, str) and note.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty nutrition note is required.")
        return cleaned

    @field_validator("meal_plan")
    @classmethod
    def validate_unique_days(cls, days):
        names = [day.day.strip().casefold() for day in days]
        if len(set(names)) != 7:
            raise ValueError("Meal plan must contain seven uniquely named days.")
        return days

@router.post("/seven-day")
def seven_day_plan(body: PlannerRequest):

    # 1. Calculate estimated BMR
    base = (
        10 * body.weight_kg
        + 6.25 * body.height_cm
        - 5 * body.age
    )

    sex_adjustment = {
        "Male": 5,
        "Female": -161,
        "Other": -78
    }

    bmr = base + sex_adjustment[body.sex]

    # 2. Calculate estimated daily energy expenditure
    tdee = bmr * FACTORS[body.activity]

    # 3. Adjust according to the selected goal
    calorie_adjustment = GOAL_ADJUSTMENTS[body.goal]

    target = round(
        max(1200, tdee + calorie_adjustment) / 50
    ) * 50

    # 4. Prepare the AI prompt
    prompt = f"""
You are Food Verse AI, an intelligent meal planning assistant.

Create a practical and varied seven-day meal plan.

USER PROFILE:
Age: {body.age}
Sex category used for BMR equation: {body.sex}
Weight: {body.weight_kg} kg
Height: {body.height_cm} cm
Activity level: {body.activity}
Goal: {body.goal}

NUTRITION PREFERENCES:
Estimated daily calorie target: {target} kcal
Dietary preferences: {', '.join(body.dietary) or 'None specified'}
Meals per day: {body.meals_per_day}
Preferred cuisine: {body.cuisine}
Excluded ingredients: {body.exclusions or 'None'}

REQUIREMENTS:
1. Generate exactly 7 days.
2. Include exactly {body.meals_per_day} meals per day.
3. Respect all dietary preferences and ingredient exclusions.
4. Keep meals practical and reasonably affordable.
5. Include variety across the seven days.
6. Avoid repeating the same main dish excessively.
7. Make daily calories approximately match the target.
8. Use realistic portion sizes.
9. Provide a consolidated grocery list for the entire week.
10. Include approximate calories for each meal.
11. Never claim that estimated calories are medically prescribed.
12. Clearly mention if a dietary requirement cannot be satisfied.

RETURN ONLY VALID JSON:

{{
    "daily_calories": {target},
    "meal_plan": [
        {{
            "day": "Monday",
            "meals": [
                {{
                    "meal": "Breakfast",
                    "dish": "Example dish",
                    "approximate_calories": 350,
                    "notes": "Serving or preparation details"
                }}
            ]
        }}
    ],
    "grocery_list": [
        {{
            "item": "Rice",
            "quantity": "1 kg",
            "category": "Grains"
        }}
    ],
    "nutrition_notes": [
        "All calorie values are approximate."
    ]
}}

Return exactly seven day objects and exactly
{body.meals_per_day} meals in each day.
"""

    # 5. Call AI service
    try:
        result = analyze(
            kind="planner",
            prompt=prompt,
            provider=body.provider,
            api_key=body.api_key.strip() or None,
            demo=body.demo
        )

        result["energy_estimates"] = {
            "bmr_kcal": round(bmr),
            "tdee_kcal": round(tdee),
            "target_kcal": target
        }

        # Validate the AI-generated structure before returning it to the frontend.
        validated = PlannerResponse.model_validate(result)

        if validated.daily_calories != target:
            raise ValueError(
                f"AI daily_calories ({validated.daily_calories}) does not "
                f"match the calculated target ({target})."
            )

        for day in validated.meal_plan:
            if len(day.meals) != body.meals_per_day:
                raise ValueError(
                    f"{day.day} contains {len(day.meals)} meals; "
                    f"{body.meals_per_day} were requested."
                )

        return validated.model_dump(exclude_none=True)

  
    except Exception as exc:
        print("\n========== MEAL PLANNER ERROR ==========")
        print(f"Error type: {type(exc).__name__}")
        print(f"Error message: {exc}")
        traceback.print_exc()
        print("========================================\n")

        raise HTTPException(
            status_code=502,
            detail="Meal planning failed. Check backend terminal logs."
        ) from exc

