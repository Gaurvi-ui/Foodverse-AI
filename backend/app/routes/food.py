
import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.ai import analyze


# ==================================================
# CONFIGURATION
# ==================================================

router = APIRouter()

logger = logging.getLogger(__name__)

IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}

MAX_IMAGE_SIZE = 12 * 1024 * 1024  # 12 MB


# ==================================================
# IMAGE VALIDATION
# ==================================================

async def read_valid_image(image: UploadFile) -> bytes:

    if image.content_type not in IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Upload a JPG, PNG, or WEBP image."
        )

    raw = await image.read(MAX_IMAGE_SIZE + 1)

    if not raw:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty."
        )

    if len(raw) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image must be 12 MB or smaller."
        )

    return raw


# ==================================================
# AI ANALYSIS HANDLER
# ==================================================

def run_food_analysis(
    kind: str,
    prompt: str,
    image_bytes: bytes,
    mime_type: str
) -> dict:

    try:

        result = analyze(
            kind=kind,
            prompt=prompt,
            image_bytes=image_bytes,
            mime_type=mime_type,
            provider="gemini",
            api_key=None,
            demo=False
        )

        if result.get("demo") is True:
            raise RuntimeError(
                "Unexpected demo response received in production mode."
            )

        return result

    except Exception as exc:

        logger.exception(
            "Food Verse AI analysis failed. Analysis type: %s",
            kind
        )

        raise HTTPException(
            status_code=502,
            detail=(
                f"{kind.capitalize()} analysis failed. "
                "Check the backend terminal for the detailed error."
            )
        ) from exc


# ==================================================
# 1. FOOD RECOGNITION & NUTRITION AUDIT
# ==================================================

@router.post("/nutrition")
async def nutrition_audit(
    image: UploadFile = File(...),
    serving_context: str = Form(""),
    dietary_context: str = Form("")
):

    raw = await read_valid_image(image)

    prompt = f"""
You are Food Verse AI, a multimodal food intelligence assistant.

Analyze the uploaded meal photograph.

SERVING CONTEXT:
{serving_context or "Not supplied"}

DIETARY CONTEXT:
{dietary_context or "Not supplied"}

YOUR TASK:

1. Identify the visible dish.
2. Identify its likely cuisine.
3. List visible ingredients.
4. Estimate the serving size and portion weight.
5. Estimate nutritional values for the visible portion.
6. Identify potential allergens based on visible evidence.
7. Calculate a balanced health score from 1 to 100.
8. Explain the reasoning behind the score.

RETURN ONLY A VALID JSON OBJECT WITH THIS STRUCTURE:

{{
    "dish_name": "Identified dish",
    "cuisine": "Cuisine type",
    "ingredients": [
        "ingredient 1",
        "ingredient 2"
    ],
    "portion_size": "Estimated portion and weight",
    "nutrition": {{
        "calories_kcal": 0,
        "protein_g": 0,
        "carbohydrates_g": 0,
        "fats_g": 0,
        "fiber_g": 0
    }},
    "allergens": [],
    "health_score": 0,
    "score_reasoning": [],
    "confidence_note": "Explain estimation uncertainty"
}}

IMPORTANT RULES:

- Analyze the actual uploaded image.
- Estimate only food that is visibly identifiable.
- Never invent hidden ingredients.
- Return numeric nutritional values.
- Do not claim exact nutritional measurements from photographs.
- State uncertainty where portion sizes or ingredients are unclear.
- Allergens must be described as potential risks, not confirmed ingredients.
- Health score must be between 1 and 100.
- Return valid JSON without Markdown.
"""

    return run_food_analysis(
        kind="nutrition",
        prompt=prompt,
        image_bytes=raw,
        mime_type=image.content_type
    )


# ==================================================
# 2. FOOD FRESHNESS & SPOILAGE DIAGNOSTIC
# ==================================================

@router.post("/freshness")
async def freshness_check(
    image: UploadFile = File(...),
    category: str = Form("Other"),
    storage: str = Form("Unknown")
):

    raw = await read_valid_image(image)

    prompt = f"""
You are Food Verse AI, a cautious food freshness assessment assistant.

Analyze the actual uploaded photograph of a food item.

FOOD CATEGORY:
{category}

STORAGE CONDITIONS:
{storage}

YOUR TASK:

1. Identify the visible food item.
2. Examine its visible surface texture.
3. Look for discoloration, wrinkles, mold and visible decay.
4. Assess its apparent visual freshness.
5. Recommend an appropriate next action.
6. Provide practical storage recommendations.

RETURN ONLY A VALID JSON OBJECT:

{{
    "item": "Identified food item",
    "freshness_stage": "Fresh",
    "visual_observations": [
        "Visible observation 1",
        "Visible observation 2"
    ],
    "action": "Safe to consume",
    "storage_tips": [
        "Storage recommendation"
    ],
    "safety_note": "Explain limitations of visual assessment"
}}

ALLOWED FRESHNESS STAGES:

- Fresh
- Moderately Fresh
- Spoiled

ALLOWED ACTIONS:

- Safe to consume
- Consume within 24h
- Discard immediately

IMPORTANT RULES:

- Analyze the actual uploaded image.
- Do not invent visible defects.
- If visual evidence is inconclusive, explicitly state uncertainty.
- Visible mold or significant decay should result in a discard recommendation.
- A photograph cannot detect pathogens, toxins, smell or internal spoilage.
- Never guarantee that food is safe to consume.
- Return valid JSON without Markdown.
"""

    return run_food_analysis(
        kind="freshness",
        prompt=prompt,
        image_bytes=raw,
        mime_type=image.content_type
    )
