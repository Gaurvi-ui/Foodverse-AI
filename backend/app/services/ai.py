import base64

import json

import os

import re

import time

from typing import Any





# ==================================================
# CONFIGURATION
# ==================================================
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")



VALID_PROVIDERS = {"gemini", "groq"}

VALID_ANALYSIS_TYPES = {

    "nutrition",

    "freshness",

    "hygiene",

    "recipes",

    "planner",

}





class AIResponseFormatError(RuntimeError):
    """Raised when an AI provider returns malformed or truncated JSON."""


# ==================================================
# JSON RESPONSE PARSER
# ==================================================
def _json_object(raw: str) -> dict[str, Any]:

    """Parse a JSON object, tolerating surrounding Markdown fences/text."""

    if not raw or not raw.strip():

        raise ValueError("AI provider returned an empty response.")



    raw = raw.strip()

    raw = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", raw, flags=re.IGNORECASE).strip()



    try:

        data = json.loads(raw)

    except json.JSONDecodeError:

        start = raw.find("{")

        if start == -1:

            raise ValueError("AI provider did not return valid JSON.")

        try:

            data, _ = json.JSONDecoder().raw_decode(raw[start:])

        except json.JSONDecodeError as exc:

            print("AI JSON PARSE ERROR: response may be truncated or malformed.")
            raise AIResponseFormatError(
                "AI provider returned malformed or incomplete JSON."
            ) from exc



    if not isinstance(data, dict):

        raise ValueError("Expected a JSON object from AI provider.")



    return data





# ==================================================
# DEMO RESPONSES
# ==================================================
def _demo(kind: str) -> dict[str, Any]:

    if kind == "nutrition":

        return {

            "demo": True,

            "dish_name": "Demo grain bowl",

            "cuisine": "Fusion",

            "ingredients": ["brown rice", "roasted chickpeas", "mixed vegetables", "yogurt dressing"],

            "portion_size": "1 medium bowl (estimated 350 g)",

            "nutrition": {

                "calories_kcal": 520,

                "protein_g": 19,

                "carbohydrates_g": 72,

                "fats_g": 16,

                "fiber_g": 11,

            },

            "allergens": ["Dairy may be present"],

            "health_score": 82,

            "score_reasoning": [

                "Legumes and vegetables contribute fiber",

                "Dressing and sodium quantities are unknown",

            ],

            "confidence_note": "Illustrative sample only. The uploaded image was not analyzed.",

        }



    if kind == "freshness":

        return {

            "demo": True,

            "item": "Demo produce item",

            "freshness_stage": "Moderately Fresh",

            "visual_observations": ["Sample observation only; media was not analyzed."],

            "action": "Consume within 24h",

            "storage_tips": ["Refrigerate perishables promptly."],

            "safety_note": "A photo cannot establish food safety. Do not taste-test questionable food.",

        }



    if kind == "hygiene":

        return {

            "demo": True,

            "compliance_score": 78,

            "indicators": [

                {

                    "indicator": indicator,

                    "status": "Not assessed in demo",

                    "severity": "Medium",

                    "observation": "Sample entry only.",

                }

                for indicator in [

                    "Hair restraint",

                    "Hand hygiene",

                    "Sanitization",

                    "Cross-contamination",

                ]

            ],

            "priority_actions": [

                "Verify cleaning records",

                "Keep raw animal products separate from ready-to-eat foods",

            ],

            "confidence_note": "Sample score only; not an inspection or certification.",

        }



    if kind == "planner":

        return {

            "demo": True,

            "daily_calories": 2000,

            "meal_plan": [

                {

                    "day": f"Day {day}",

                    "meals": [

                        {

                            "meal": "Breakfast",

                            "dish": "Vegetable poha",

                            "approximate_calories": 350,

                            "notes": "Illustrative demo meal.",

                        },

                        {

                            "meal": "Lunch",

                            "dish": "Dal, rice and salad",

                            "approximate_calories": 650,

                            "notes": "Illustrative demo meal.",

                        },

                        {

                            "meal": "Dinner",

                            "dish": "Vegetable khichdi",

                            "approximate_calories": 550,

                            "notes": "Illustrative demo meal.",

                        },

                    ],

                }

                for day in range(1, 8)

            ],

            "grocery_list": [

                {"item": "Rice", "quantity": "1 kg", "category": "Grains"},

                {"item": "Dal", "quantity": "500 g", "category": "Pulses"},

                {"item": "Mixed vegetables", "quantity": "1 kg", "category": "Vegetables"},

            ],

            "nutrition_notes": [

                "Illustrative sample only. Not a personalized nutrition plan."

            ],

        }



    # Recipe demo is the default for the recipes analysis type.
    if kind == "recipes":

        return {

            "demo": True,

            "recipes": [

                {

                    "name": "Chickpea & vegetable skillet",

                    "description": "A flexible one-pan meal.",

                    "time_minutes": 20,

                    "difficulty": "Easy",

                    "servings": 2,

                    "ingredients": ["1 cup chickpeas", "2 cups vegetables", "1 tsp cumin"],

                    "instructions": [

                        "Warm spices in a pan.",

                        "Add vegetables and cook until tender.",

                        "Stir in chickpeas and heat through.",

                    ],

                    "substitutions": [

                        "Chickpeas → beans",

                        "Fresh vegetables → frozen vegetables",

                    ],

                    "nutrition_note": "Nutrition depends on exact quantities.",

                }

            ],

        }



    raise ValueError(f"No demo response is configured for analysis type: {kind}")





# ==================================================
# PROVIDER FALLBACK ERRORS
# ==================================================
class GeminiTemporaryError(RuntimeError):

    """Raised when Gemini fails with a retryable availability/rate-limit error."""





def _is_retryable_gemini_error(exc: Exception) -> bool:

    message = str(exc).lower()

    return any(

        term in message

        for term in (

            "429", "500", "502", "503", "504",

            "resource exhausted", "unavailable", "high demand",

            "temporarily", "deadline exceeded", "timeout",

        )

    )





# ==================================================
# GEMINI AI PROVIDER
# ==================================================
def _analyze_gemini(

    prompt: str,

    image_bytes: bytes | None,

    mime_type: str,

    api_key: str,

) -> dict[str, Any]:

    from google import genai

    from google.genai import types



    client = genai.Client(api_key=api_key)

    contents: list[Any] = [prompt]



    if image_bytes:

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        contents.append(image_part)



    response = None



    # Retry transient server/rate-limit errors, but expose the actual error in logs.
    for attempt in range(3):

        try:

            response = client.models.generate_content(

                model=GEMINI_MODEL,

                contents=contents,

                config=types.GenerateContentConfig(

                    response_mime_type="application/json",

                    max_output_tokens=8192,

                ),

            )

            break



        except Exception as exc:

            retryable = _is_retryable_gemini_error(exc)



            if not retryable:

                print(f"GEMINI FINAL ERROR: {type(exc).__name__}: {exc}")

                raise RuntimeError(f"Gemini analysis failed: {exc}") from exc



            if attempt == 2:

                print(f"GEMINI FINAL TEMPORARY ERROR: {type(exc).__name__}: {exc}")

                raise GeminiTemporaryError(

                    f"Gemini temporarily unavailable after retries: {exc}"

                ) from exc



            wait_time = 2 ** attempt

            print(f"Gemini temporary failure: {type(exc).__name__}: {exc}")

            print(f"Retrying in {wait_time} seconds.")

            time.sleep(wait_time)



    if response is None:

        raise RuntimeError("Gemini returned no response.")



    response_text = response.text

    if not response_text:

        raise ValueError("Gemini returned an empty text response.")



    return _json_object(response_text)





# ==================================================
# OPTIONAL GROQ AI PROVIDER
# ==================================================
def _analyze_groq(

    prompt: str,

    image_bytes: bytes | None,

    mime_type: str,

    api_key: str,

) -> dict[str, Any]:

    from groq import Groq



    client = Groq(api_key=api_key)

    content: Any = prompt



    if image_bytes:

        encoded = base64.b64encode(image_bytes).decode("utf-8")

        content = [

            {"type": "text", "text": prompt},

            {

                "type": "image_url",

                "image_url": {"url": f"data:{mime_type};base64,{encoded}"},

            },

        ]



    try:

        result = client.chat.completions.create(

            model=GROQ_MODEL,

            messages=[

                {

                    "role": "system",

                    "content": (

                        "You are a cautious food science assistant. "

                        "Return only valid JSON. Never invent visual observations. "

                        "Clearly state uncertainty."

                    ),

                },

                {"role": "user", "content": content},

            ],

            response_format={"type": "json_object"},

            max_completion_tokens=4096,

        )

    except Exception as exc:

        raise RuntimeError(f"Groq analysis failed: {exc}") from exc



    response_text = result.choices[0].message.content or ""

    return _json_object(response_text)





# ==================================================
# MAIN ANALYSIS FUNCTION
# ==================================================
def analyze(

    kind: str,

    prompt: str,

    image_bytes: bytes | None = None,

    mime_type: str = "image/jpeg",

    provider: str = "gemini",

    api_key: str | None = None,

    demo: bool = False,

) -> dict[str, Any]:

    kind = kind.strip().lower()

    provider = provider.strip().lower()



    if kind not in VALID_ANALYSIS_TYPES:

        raise ValueError(f"Unsupported analysis type: {kind}")



    if provider not in VALID_PROVIDERS:

        raise ValueError("Provider must be 'gemini' or 'groq'.")



    if demo:

        print(f"STATUS: Explicit demo mode - {kind}")

        return _demo(kind)



    if kind in {"nutrition", "freshness", "hygiene"} and not image_bytes:

        raise ValueError(f"An image is required for {kind} analysis.")



    if image_bytes and not mime_type.startswith("image/"):

        raise ValueError("Unsupported image MIME type.")



    if not prompt or not prompt.strip():

        raise ValueError("Analysis prompt cannot be empty.")



    environment_key = "GEMINI_API_KEY" if provider == "gemini" else "GROQ_API_KEY"

    key = api_key or os.getenv(environment_key)



    print("\n========== FOOD VERSE DEBUG ==========")

    print("Analysis type:", kind)

    print("Provider:", provider)

    print("Model:", GEMINI_MODEL if provider == "gemini" else GROQ_MODEL)

    print("Demo mode:", demo)

    print("API key received:", bool(key))

    print("Image received:", bool(image_bytes))

    print("Image size:", len(image_bytes) if image_bytes else 0)



    if not key:

        raise ValueError(

            f"{environment_key} is missing. Please configure your API key."

        )



    print("STATUS: Calling REAL AI provider")



    if provider == "gemini":

        try:

            result = _analyze_gemini(

                prompt=prompt,

                image_bytes=image_bytes,

                mime_type=mime_type,

                api_key=key,

            )

            result["provider_used"] = "gemini"

            result["fallback_used"] = False



        except (GeminiTemporaryError, AIResponseFormatError) as exc:

            groq_key = os.getenv("GROQ_API_KEY")

            if not groq_key:

                print("FALLBACK UNAVAILABLE: GROQ_API_KEY is not configured.")

                raise RuntimeError(

                    "Gemini is temporarily unavailable and Groq fallback is not configured."

                ) from exc



            print(

                "STATUS: Gemini temporarily unavailable. "

                f"Switching to Groq model {GROQ_MODEL}."

            )

            result = _analyze_groq(

                prompt=prompt,

                image_bytes=image_bytes,

                mime_type=mime_type,

                api_key=groq_key,

            )

            result["provider_used"] = "groq"

            result["fallback_used"] = True

            result["fallback_reason"] = (
                "Gemini returned malformed or incomplete JSON."
                if isinstance(exc, AIResponseFormatError)
                else "Gemini temporarily unavailable or rate-limited."
            )



    else:

        result = _analyze_groq(

            prompt=prompt,

            image_bytes=image_bytes,

            mime_type=mime_type,

            api_key=key,

        )

        result["provider_used"] = "groq"

        result["fallback_used"] = False



    result["demo"] = False

    print("STATUS: REAL AI analysis successful via", result["provider_used"])

    print("Fallback used:", result["fallback_used"])

    print("=====================================\n")

    return result
