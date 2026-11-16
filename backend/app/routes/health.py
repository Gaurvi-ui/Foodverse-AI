
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.services.ai import analyze

router = APIRouter()

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}

MAX_IMAGE_SIZE = 12 * 1024 * 1024


@router.post("/visual-review")
async def kitchen_review(
    image: UploadFile = File(...),
    provider: str = Form("gemini"),
    api_key: str = Form(""),
    demo: bool = Form(False)
):
    # Validate image type
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Please upload a JPG, PNG, or WEBP kitchen image."
        )

    # Read and validate image
    raw = await image.read()

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

    prompt = """
    You are a cautious food hygiene visual assessment assistant.

    Analyze the uploaded kitchen image for visible hygiene indicators.

    Return ONLY a valid JSON object with this structure:

    {
        "compliance_score": 0,
        "indicators": [
            {
                "indicator": "Hair restraint",
                "status": "Compliant / Needs Attention / Not observable",
                "severity": "Low / Medium / High",
                "observation": "Visual observation"
            }
        ],
        "priority_actions": [
            "Recommended corrective action"
        ],
        "confidence_note": "Limitations of this visual assessment"
    }

    Assess the following:
    1. Hair restraint
    2. Hand and glove hygiene
    3. Surface cleanliness and sanitization
    4. Raw meat or poultry separation
    5. Separation of raw and ready-to-eat food
    6. Food storage practices

    Important rules:
    - Never invent observations.
    - If something cannot be seen, mark it as Not observable.
    - Do not assume that gloves guarantee clean hands.
    - Do not certify a kitchen as safe based on an image.
    - Explain visible risks and practical corrective actions.

    This is a preliminary visual review, not an official inspection
    or food safety certification.
    """

    try:
        result = analyze(
            kind="hygiene",
            prompt=prompt,
            image_bytes=raw,
            mime_type=image.content_type,
            provider=provider,
            api_key=api_key.strip() or None,
            demo=demo
        )

        return result

    except Exception:
        # Keep internal provider errors out of the public response.
        raise HTTPException(
            status_code=502,
            detail="Kitchen hygiene analysis failed. Please try again."
        )
