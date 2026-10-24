"""
Food Verse AI - Multimodal Food Intelligence Agent

Run locally:
    pip install -r requirements.txt
    streamlit run app.py

Secrets (recommended for deployment):
    [gemini]
    api_key = "YOUR_GEMINI_API_KEY"

or:
    [groq]
    api_key = "YOUR_GROQ_API_KEY"

You can also enter a key in the sidebar. Demo mode works without an API key.
"""

from __future__ import annotations

import base64
import json
import math
import mimetypes
import os
import random
import re
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st
import plotly.express as px

APP_TITLE = "Food Verse AI"
APP_SUBTITLE = "Multimodal Food Intelligence Agent"
DEMO_MODE_LABEL = "Standalone demo mode"

st.set_page_config(
    page_title=f"{APP_TITLE} | Food Intelligence",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
      :root { --fv-ink: #17252a; --fv-green: #1f9d78; --fv-lime: #d7f36b; --fv-orange: #ff9f68; }
      html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
      .stApp { background: linear-gradient(140deg, #f6fbf7 0%, #f6f8ff 55%, #fff8f1 100%); color: var(--fv-ink); }
      h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.03em; }
      .hero { padding: 1.6rem 1.8rem; border-radius: 24px; color: #fff; background: linear-gradient(120deg, #123b35, #1f9d78 65%, #7bbf67); margin-bottom: 1rem; box-shadow: 0 12px 35px rgba(24, 90, 70, .16); }
      .hero h1 { font-size: clamp(2rem, 4vw, 3.2rem); margin: 0; color: white; }
      .hero p { margin: .55rem 0 0; color: #e7fff4; font-size: 1.05rem; }
      .eyebrow { text-transform: uppercase; letter-spacing: .14em; font-size: .72rem; font-weight: 700; opacity: .85; }
      .metric-card { background: rgba(255,255,255,.88); border: 1px solid #e2ece5; border-radius: 18px; padding: 1rem 1.1rem; min-height: 110px; box-shadow: 0 6px 20px rgba(26, 56, 44, .04); }
      .metric-label { color: #5d7269; font-size: .82rem; font-weight: 600; }
      .metric-value { font-family: 'Space Grotesk', sans-serif; font-size: 1.75rem; font-weight: 700; color: #173c32; }
      .pill { display: inline-block; border-radius: 999px; padding: .32rem .7rem; font-size: .78rem; font-weight: 700; margin: .15rem .15rem .15rem 0; }
      .pill-green { background: #dff8eb; color: #126343; }
      .pill-amber { background: #fff0d6; color: #8b4e08; }
      .pill-red { background: #ffe1df; color: #9c2d28; }
      .note { background: #eef7f1; border-left: 4px solid #1f9d78; border-radius: 8px; padding: .8rem 1rem; }
      .small-muted { color: #65766e; font-size: .85rem; }
      div[data-testid="stMetric"] { background: rgba(255,255,255,.82); padding: .8rem 1rem; border: 1px solid #e2ece5; border-radius: 16px; }
      .stButton button[kind="primary"] { background: linear-gradient(90deg, #168565, #24a47f); border: 0; border-radius: 12px; font-weight: 700; }
      .stTabs [data-baseweb="tab-list"] { gap: .4rem; }
      .stTabs [data-baseweb="tab"] { background: rgba(255,255,255,.72); border-radius: 12px 12px 0 0; padding: .7rem 1rem; }
      [data-testid="stSidebar"] { background: #f0f7f2; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- API / AI helpers ----------
def get_secret(provider: str) -> str:
    """Read API key from Streamlit secrets or environment, without exposing it."""
    secret_names = {
        "Gemini": (("gemini", "api_key"), "GEMINI_API_KEY", "GOOGLE_API_KEY"),
        "Groq": (("groq", "api_key"), "GROQ_API_KEY"),
    }
    config = secret_names.get(provider, ())
    if config:
        nested = config[0]
        try:
            value = st.secrets[nested[0]][nested[1]]
            if value:
                return str(value).strip()
        except Exception:
            pass
        for env_name in config[1:]:
            value = os.getenv(env_name)
            if value:
                return value.strip()
    return ""


def image_mime(uploaded_file) -> str:
    mime = getattr(uploaded_file, "type", None)
    if mime and mime.startswith("image/"):
        return mime
    return mimetypes.guess_type(getattr(uploaded_file, "name", ""))[0] or "image/jpeg"


def image_to_data_url(uploaded_file) -> str:
    raw = uploaded_file.getvalue()
    return f"data:{image_mime(uploaded_file)};base64,{base64.b64encode(raw).decode('utf-8')}"


def extract_json(text: str) -> dict[str, Any]:
    """Parse a JSON object from model output, including fenced responses."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, flags=re.S)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    raise ValueError("The AI response was not valid JSON. Please retry or use demo mode.")


def ask_gemini(prompt: str, uploaded_file=None, model: str = "gemini-2.5-flash") -> dict[str, Any]:
    from google import genai
    from google.genai import types

    api_key = st.session_state.get("api_key", "")
    client = genai.Client(api_key=api_key)
    contents: list[Any] = [prompt]
    if uploaded_file is not None:
        contents.append(types.Part.from_bytes(data=uploaded_file.getvalue(), mime_type=image_mime(uploaded_file)))
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.25,
        ),
    )
    return extract_json(response.text or "")


def ask_groq(prompt: str, uploaded_file=None, model: str = "meta-llama/llama-4-scout-17b-16e-instruct") -> dict[str, Any]:
    """Groq vision path uses an OpenAI-compatible chat completion API."""
    from groq import Groq

    api_key = st.session_state.get("api_key", "")
    client = Groq(api_key=api_key)
    user_content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    if uploaded_file is not None:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": image_to_data_url(uploaded_file)},
        })
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a cautious food science assistant. Return only valid JSON matching the requested schema. Do not claim certainty from images when evidence is limited."},
            {"role": "user", "content": user_content},
        ],
        temperature=0.25,
        response_format={"type": "json_object"},
    )
    return extract_json(completion.choices[0].message.content or "")


def call_ai(prompt: str, uploaded_file=None) -> dict[str, Any]:
    provider = st.session_state.get("provider", "Gemini")
    key = st.session_state.get("api_key", "")
    if not key or st.session_state.get("demo_mode", False):
        return demo_response(prompt, uploaded_file)
    try:
        if provider == "Gemini":
            return ask_gemini(prompt, uploaded_file)
        return ask_groq(prompt, uploaded_file)
    except Exception as exc:
        st.error(f"{provider} request failed: {exc}")
        st.info("You can correct the API configuration or switch to standalone demo mode.")
        raise


def demo_response(prompt: str, uploaded_file=None) -> dict[str, Any]:
    """Deterministic, clearly labeled demo outputs; never presented as actual image analysis."""
    p = prompt.lower()
    if "nutrition" in p or "health_score" in p:
        return {
            "dish_name": "Demo grain bowl",
            "cuisine": "Fusion",
            "ingredients": ["brown rice", "roasted chickpeas", "mixed vegetables", "yogurt dressing"],
            "portion_size": "1 medium bowl (estimated 350 g)",
            "nutrition": {"calories_kcal": 520, "protein_g": 19, "carbohydrates_g": 72, "fats_g": 16, "fiber_g": 11},
            "allergens": ["Dairy (if yogurt dressing is present)"],
            "health_score": 82,
            "score_reasoning": ["Fiber-rich vegetables and legumes", "Moderate protein", "Sodium and dressing quantity are unknown"],
            "confidence_note": "Demonstration data only; this is not an analysis of your uploaded image.",
        }
    if "freshness" in p or "freshness_stage" in p:
        return {
            "item": "Demo produce item",
            "freshness_stage": "Moderately Fresh",
            "visual_observations": ["Example: slight surface wrinkling", "Image-only checks cannot assess smell or internal condition"],
            "action": "Consume within 24h",
            "storage_tips": ["Refrigerate perishables promptly", "Keep raw meat separate from ready-to-eat foods"],
            "safety_note": "Demonstration data only. Do not use this output to decide whether food is safe.",
        }
    if "hygiene" in p or "compliance_score" in p:
        return {
            "compliance_score": 78,
            "indicators": [
                {"indicator": "Hair restraint", "status": "Needs visual check", "severity": "Medium", "observation": "Demo entry; image not assessed"},
                {"indicator": "Glove/hand hygiene", "status": "Needs visual check", "severity": "Medium", "observation": "Demo entry; image not assessed"},
                {"indicator": "Sanitization", "status": "Needs visual check", "severity": "High", "observation": "Demo entry; image not assessed"},
                {"indicator": "Cross-contamination", "status": "Needs visual check", "severity": "High", "observation": "Demo entry; image not assessed"},
            ],
            "priority_actions": ["Verify handwashing and sanitizing logs", "Separate raw animal products from ready-to-eat foods"],
            "confidence_note": "Demonstration score only; not a real inspection or certification.",
        }
    if "recipe" in p or "recipes" in p:
        return {
            "recipes": [
                {
                    "name": "Chickpea & Veggie Skillet",
                    "description": "A flexible one-pan meal built around pantry staples.",
                    "time_minutes": 20,
                    "difficulty": "Easy",
                    "servings": 2,
                    "ingredients": ["1 can chickpeas, drained", "2 cups mixed vegetables", "1 tbsp olive oil", "1 tsp cumin", "salt and pepper"],
                    "instructions": ["Warm oil in a pan and add cumin.", "Add vegetables and cook until tender.", "Stir in chickpeas and season.", "Cook for 5–7 minutes and serve."],
                    "substitutions": ["Chickpeas → beans or lentils", "Olive oil → another cooking oil", "Fresh vegetables → frozen vegetables"],
                    "nutrition_note": "Nutrition varies with brands, quantities, and preparation.",
                }
            ]
        }
    return {
        "daily_calories": 2000,
        "meal_plan": [],
        "grocery_list": [],
        "note": "Demo response. Enter an API key for generated results.",
    }


def safe_ai_call(prompt: str, uploaded_file=None) -> dict[str, Any] | None:
    try:
        return call_ai(prompt, uploaded_file)
    except Exception:
        return None


# ---------- UI helpers ----------
def metric_card(label: str, value: str, hint: str = "") -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="small-muted">{hint}</div></div>',
        unsafe_allow_html=True,
    )


def health_pill(text: str, tone: str = "green") -> None:
    st.markdown(f'<span class="pill pill-{tone}">{text}</span>', unsafe_allow_html=True)


def show_json_download(data: dict[str, Any], filename: str) -> None:
    st.download_button(
        "Download analysis (JSON)",
        data=json.dumps(data, indent=2, ensure_ascii=False),
        file_name=filename,
        mime="application/json",
    )


def validate_numeric(value: float, low: float, high: float, label: str) -> float:
    if not low <= value <= high:
        raise ValueError(f"{label} must be between {low} and {high}.")
    return value


# ---------- Sidebar / Persona ----------
with st.sidebar:
    st.markdown("## 🥑 Food Verse AI")
    st.caption("Food intelligence, from plate to pantry.")
    st.markdown("---")
    provider = st.selectbox("AI provider", ["Gemini", "Groq"], help="Choose the provider matching the API key you supply.")
    st.session_state["provider"] = provider
    default_key = get_secret(provider)
    key_input = st.text_input(
        f"{provider} API key",
        value=st.session_state.get("api_key", default_key),
        type="password",
        placeholder="Paste API key (optional in demo mode)",
        help="The key is used for this session only. For deployment, prefer Streamlit Secrets.",
    )
    st.session_state["api_key"] = key_input.strip()
    st.session_state["demo_mode"] = st.toggle(
        "Use standalone demo mode",
        value=not bool(key_input.strip()),
        help="Demo outputs are illustrative and do not analyze uploaded media.",
    )
    if st.session_state["demo_mode"]:
        health_pill("DEMO MODE", "amber")
        st.caption("No API call is made. Results are sample data.")
    elif not key_input.strip():
        st.warning("Add an API key or enable demo mode.")
    st.markdown("---")
    st.markdown("### Your AI food science guide")
    st.write("A practical assistant for nutrition awareness, visual food checks, kitchen hygiene, recipes, and meal planning.")
    st.caption("Not a substitute for a clinician, certified food inspector, or sensory food-safety checks.")

st.markdown(
    f"""
    <div class="hero">
      <div class="eyebrow">Skill Wallet · Capstone Project 3</div>
      <h1>Food Verse AI</h1>
      <p>{APP_SUBTITLE} — make more informed decisions about food, freshness, and your kitchen.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Navigation is an interactive set of core intelligence pillars.
pages = [
    "🍽️ Nutrition Audit",
    "🍓 Freshness Diagnostic",
    "🧼 Kitchen Hygiene",
    "👩‍🍳 Recipe Assistant",
    "📅 Meal Planner",
]
selected_page = st.radio("Explore intelligence pillars", pages, horizontal=True, label_visibility="collapsed")

# ---------- Tab 1: Food recognition & nutrition ----------
if selected_page == "🍽️ Nutrition Audit":
    st.subheader("Food Recognition & Nutrition Audit")
    st.write("Upload a meal photo for an AI-assisted dish description and approximate nutrition estimate.")
    col_img, col_action = st.columns([1, 1.25], gap="large")
    with col_img:
        food_image = st.file_uploader("Upload meal / dish photo", type=["png", "jpg", "jpeg", "webp"], key="nutrition_image")
        if food_image:
            st.image(food_image, caption="Uploaded meal image", use_container_width=True)
    with col_action:
        serving_note = st.text_input("Serving context (optional)", placeholder="e.g., homemade, 1 plate, restaurant portion")
        dietary_context = st.text_input("Dietary context (optional)", placeholder="e.g., vegetarian, low-sodium")
        st.markdown('<div class="note">Nutrition from a photo is an estimate. Exact values depend on recipe, ingredients, oil, sauces, and portion weights.</div>', unsafe_allow_html=True)
        run_nutrition = st.button("✨ Analyze meal", type="primary", use_container_width=True)
    if run_nutrition:
        prompt = f"""
Analyze this food photo for nutrition awareness. Context: {serving_note or 'not supplied'}; dietary context: {dietary_context or 'not supplied'}.
Return one JSON object with:
dish_name (string), cuisine (string), ingredients (array of strings), portion_size (string),
nutrition (object with calories_kcal, protein_g, carbohydrates_g, fats_g, fiber_g as non-negative numbers),
allergens (array of strings; say 'uncertain' when not inferable), health_score (integer 1-100),
score_reasoning (array of short strings), confidence_note (string).
Estimate only visible food and clearly state uncertainty. Do not infer hidden ingredients as fact. Use common portion assumptions and note that this is not laboratory measurement.
"""
        result = safe_ai_call(prompt, food_image)
        if result:
            st.session_state["nutrition_result"] = result
    result = st.session_state.get("nutrition_result")
    if result:
        st.markdown("---")
        if st.session_state.get("demo_mode"):
            st.warning("Demo output: sample values only; uploaded image was not analyzed.")
        n = result.get("nutrition", {}) or {}
        a, b, c = st.columns(3)
        with a:
            metric_card("Dish", str(result.get("dish_name", "Unidentified"))[:36], str(result.get("cuisine", "Cuisine uncertain")))
        with b:
            metric_card("Portion estimate", str(result.get("portion_size", "Not available"))[:34], "Confirm with a kitchen scale for accuracy")
        with c:
            metric_card("Health score", f"{result.get('health_score', '—')}/100", "Indicative score, not medical advice")
        st.markdown("#### Estimated nutrition")
        macro_cols = st.columns(5)
        macro_items = [
            ("Calories", n.get("calories_kcal", 0), "kcal"),
            ("Protein", n.get("protein_g", 0), "g"),
            ("Carbs", n.get("carbohydrates_g", 0), "g"),
            ("Fat", n.get("fats_g", 0), "g"),
            ("Fiber", n.get("fiber_g", 0), "g"),
        ]
        for col, (label, value, unit) in zip(macro_cols, macro_items):
            with col:
                metric_card(label, f"{value} {unit}", "Estimate")
        chart_data = pd.DataFrame({
            "Macro": ["Protein", "Carbohydrates", "Fat", "Fiber"],
            "Grams": [float(n.get("protein_g", 0) or 0), float(n.get("carbohydrates_g", 0) or 0),
                      float(n.get("fats_g", 0) or 0), float(n.get("fiber_g", 0) or 0)],
        })
        left, right = st.columns([1, 1])
        with left:
            st.plotly_chart(px.bar(chart_data, x="Macro", y="Grams", color="Macro", title="Macronutrient profile", text_auto=".1f"), use_container_width=True)
        with right:
            kcal_data = pd.DataFrame({"Source": ["Protein", "Carbohydrates", "Fat"], "Approx. kcal": [
                float(n.get("protein_g", 0) or 0) * 4,
                float(n.get("carbohydrates_g", 0) or 0) * 4,
                float(n.get("fats_g", 0) or 0) * 9,
            ]})
            st.plotly_chart(px.pie(kcal_data, names="Source", values="Approx. kcal", title="Estimated calorie contribution", hole=.55), use_container_width=True)
        st.markdown("#### Ingredients & allergen alerts")
        st.write(", ".join(result.get("ingredients", [])) or "No ingredients returned.")
        allergens = result.get("allergens", []) or ["No allergens identified; verify ingredients manually."]
        for allergen in allergens:
            health_pill(f"⚠️ {allergen}", "red" if "uncertain" not in str(allergen).lower() else "amber")
        st.markdown("#### Why this score?")
        for reason in result.get("score_reasoning", []) or ["No score explanation returned."]:
            st.write(f"• {reason}")
        st.caption(result.get("confidence_note", "Estimates are uncertain and may not represent hidden ingredients."))
        show_json_download(result, "food_verse_nutrition_audit.json")

# ---------- Tab 2: Freshness ----------
elif selected_page == "🍓 Freshness Diagnostic":
    st.subheader("Food Freshness & Spoilage Diagnostic")
    st.write("Use visual observations as a screening aid only. A photo cannot reliably detect pathogens, toxins, or internal spoilage.")
    left, right = st.columns([1, 1.2], gap="large")
    with left:
        fresh_image = st.file_uploader("Upload fruit, vegetable, meat, or dairy photo", type=["png", "jpg", "jpeg", "webp"], key="freshness_image")
        item_type = st.selectbox("Food category", ["Fruit", "Vegetable", "Raw meat / poultry", "Fish / seafood", "Dairy", "Other"])
        storage_context = st.selectbox("Current storage", ["Unknown", "Refrigerated", "Room temperature", "Frozen", "Previously opened"])
        if fresh_image:
            st.image(fresh_image, caption="Uploaded food item", use_container_width=True)
    with right:
        st.markdown("### Visual screening checklist")
        st.write("The model will consider surface texture, discoloration, wrinkling, visible mold, packaging condition, and obvious leakage.")
        st.warning("Do not taste food to test safety. When in doubt, throw it out—especially for meat, seafood, dairy, cooked leftovers, and food served to vulnerable people.")
        run_freshness = st.button("🔎 Assess visible freshness", type="primary", use_container_width=True)
    if run_freshness:
        prompt = f"""
Assess visible freshness of the uploaded food image. Category: {item_type}. Storage context: {storage_context}.
Return JSON: item (string), freshness_stage (exactly Fresh, Moderately Fresh, or Spoiled), visual_observations (array),
action (exactly one of Safe to consume, Consume within 24h, Discard immediately), storage_tips (array),
safety_note (string).
Be conservative. Do not claim food is safe from an image alone. If visible mold/decay or suspicious discoloration is present, advise discarding. For raw animal products, stress time-temperature controls and that smell/appearance cannot rule out pathogens. Avoid recommending cutting mold off soft foods.
"""
        result = safe_ai_call(prompt, fresh_image)
        if result:
            st.session_state["freshness_result"] = result
    result = st.session_state.get("freshness_result")
    if result:
        st.markdown("---")
        if st.session_state.get("demo_mode"):
            st.warning("Demo output: sample classification only; uploaded image was not analyzed.")
        stage = result.get("freshness_stage", "Unknown")
        tone = "green" if stage == "Fresh" else ("amber" if stage == "Moderately Fresh" else "red")
        health_pill(f"Freshness stage: {stage}", tone)
        action = result.get("action", "Verify manually")
        st.subheader(f"Recommended action: {action}")
        for obs in result.get("visual_observations", []) or []:
            st.write(f"• {obs}")
        st.markdown("#### Storage & handling")
        for tip in result.get("storage_tips", []) or []:
            st.write(f"• {tip}")
        st.info(result.get("safety_note", "Image assessment is limited; follow food-safety guidance and use caution."))
        show_json_download(result, "food_verse_freshness_report.json")

# ---------- Tab 3: Kitchen hygiene ----------
elif selected_page == "🧼 Kitchen Hygiene":
    st.subheader("Kitchen Hygiene & Food Safety Compliance")
    st.write("Run a preliminary visual review of a commercial kitchen. This tool is not a regulatory inspection or certification.")
    left, right = st.columns([1, 1.2], gap="large")
    with left:
        kitchen_file = st.file_uploader("Upload kitchen photo or short video", type=["png", "jpg", "jpeg", "webp", "mp4", "mov"], key="kitchen_media")
        if kitchen_file:
            if kitchen_file.type.startswith("image/"):
                st.image(kitchen_file, caption="Kitchen image", use_container_width=True)
            else:
                st.video(kitchen_file)
                st.caption("Video support depends on the chosen provider/model. If analysis fails, upload a representative still image.")
    with right:
        st.markdown("### Inspection areas")
        st.write("• Hair restraint / chef hat compliance")
        st.write("• Glove use and hand hygiene")
        st.write("• Sanitization and visible cleanliness")
        st.write("• Raw poultry / meat separation from vegetables and ready-to-eat food")
        st.write("• Food contact surfaces, waste, and storage separation")
        st.warning("A single frame cannot confirm actual handwashing, sanitizer concentration, temperatures, or time-based practices.")
        run_hygiene = st.button("🧼 Run visual compliance review", type="primary", use_container_width=True)
    if run_hygiene:
        prompt = """
Review this kitchen media for visible food hygiene indicators. Return JSON:
compliance_score (integer 0-100), indicators (array of objects with indicator, status, severity [Low, Medium, High], observation),
priority_actions (array of actionable items), confidence_note (string).
Review hair restraint/chef hat, glove use (do not assume gloves replace handwashing), sanitization, raw poultry/meat near vegetables or ready-to-eat food, food-contact surfaces, waste and storage. Be evidence-based: if an indicator is not visible, mark 'Not observable' rather than inventing a violation. The score is a preliminary visual estimate only, not official compliance certification.
"""
        result = safe_ai_call(prompt, kitchen_file)
        if result:
            st.session_state["hygiene_result"] = result
    result = st.session_state.get("hygiene_result")
    if result:
        st.markdown("---")
        if st.session_state.get("demo_mode"):
            st.warning("Demo output: sample score only; uploaded media was not analyzed.")
        score = max(0, min(100, int(result.get("compliance_score", 0) or 0)))
        m1, m2 = st.columns([1, 2])
        with m1:
            st.metric("Visual compliance score", f"{score}%")
            st.progress(score / 100)
        with m2:
            st.markdown("#### Priority actions")
            for action in result.get("priority_actions", []) or []:
                st.write(f"• {action}")
        indicators = result.get("indicators", []) or []
        if indicators:
            df = pd.DataFrame(indicators)
            st.markdown("#### Itemized observation log")
            st.dataframe(df, use_container_width=True, hide_index=True)
            if "severity" in df.columns:
                st.plotly_chart(px.histogram(df, x="severity", color="severity", title="Findings by severity"), use_container_width=True)
        st.caption(result.get("confidence_note", "Visual findings can be incomplete."))
        show_json_download(result, "food_verse_kitchen_hygiene.json")

# ---------- Tab 4: Recipe assistant ----------
elif selected_page == "👩‍🍳 Recipe Assistant":
    st.subheader("Smart Kitchen Recipe Assistant")
    st.write("Turn the ingredients you already have into practical recipes.")
    with st.form("recipe_form"):
        pantry = st.text_area("Pantry inventory", placeholder="e.g., eggs, spinach, rice, tomatoes, chickpeas, yogurt", height=110)
        cuisine = st.selectbox("Cuisine inspiration", ["Any", "Indian", "Mediterranean", "East Asian", "Mexican", "Italian"])
        dietary = st.multiselect("Dietary preferences", ["Vegetarian", "Vegan", "High protein", "Gluten-free", "Dairy-free", "Low sodium"])
        time_limit = st.slider("Maximum cooking time (minutes)", 10, 90, 30, step=5)
        servings = st.number_input("Servings", min_value=1, max_value=12, value=2)
        submitted = st.form_submit_button("🍳 Create recipes", type="primary", use_container_width=True)
    if submitted:
        if not pantry.strip():
            st.error("Add at least one ingredient to generate a recipe.")
        else:
            prompt = f"""
Create up to 3 creative, practical recipes using this pantry inventory: {pantry}.
Cuisine: {cuisine}. Dietary preferences: {', '.join(dietary) or 'None specified'}. Maximum cooking time: {time_limit} minutes. Servings: {servings}.
Return JSON with recipes (array of objects): name, description, time_minutes (number), difficulty (Easy/Medium/Hard), servings (number), ingredients (array of strings with quantities), instructions (array of numbered step strings), substitutions (array of strings), nutrition_note (string). Prioritize food safety and realistic instructions. Respect dietary preferences and flag any ingredient that may conflict.
"""
            result = safe_ai_call(prompt)
            if result:
                st.session_state["recipe_result"] = result
    result = st.session_state.get("recipe_result")
    if result:
        if st.session_state.get("demo_mode"):
            st.warning("Demo output: illustrative recipe content, not generated from your pantry.")
        for i, recipe in enumerate(result.get("recipes", []) or []):
            with st.container(border=True):
                st.markdown(f"### 🍲 {recipe.get('name', f'Recipe {i+1}')}")
                st.write(recipe.get("description", ""))
                c1, c2, c3 = st.columns(3)
                c1.metric("Cooking time", f"{recipe.get('time_minutes', '—')} min")
                c2.metric("Difficulty", recipe.get("difficulty", "—"))
                c3.metric("Servings", recipe.get("servings", "—"))
                lcol, rcol = st.columns(2)
                with lcol:
                    st.markdown("**Ingredients**")
                    for item in recipe.get("ingredients", []) or []:
                        st.write(f"• {item}")
                with rcol:
                    st.markdown("**Instructions**")
                    for step_num, step in enumerate(recipe.get("instructions", []) or [], 1):
                        st.write(f"{step_num}. {step}")
                st.markdown("**Substitutions**")
                for sub in recipe.get("substitutions", []) or []:
                    st.write(f"• {sub}")
                st.caption(recipe.get("nutrition_note", "Nutrition depends on exact quantities and products."))
        show_json_download(result, "food_verse_recipes.json")

# ---------- Tab 5: Meal planner ----------
elif selected_page == "📅 Meal Planner":
    st.subheader("Personalized 7-Day Meal Planner")
    st.write("Calculate an estimated energy target and create a flexible meal plan. Use clinical advice for medical nutrition needs.")
    with st.form("meal_planner_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            age = st.number_input("Age (years)", min_value=18, max_value=100, value=25)
            sex = st.selectbox("Sex used for BMR equation", ["Female", "Male", "Prefer not to specify"])
            weight = st.number_input("Weight (kg)", min_value=30.0, max_value=300.0, value=65.0, step=0.5)
            height = st.number_input("Height (cm)", min_value=120.0, max_value=230.0, value=165.0, step=0.5)
        with c2:
            activity = st.selectbox("Activity level", [
                "Sedentary (little exercise)", "Lightly active (1–3 days/week)",
                "Moderately active (3–5 days/week)", "Very active (6–7 days/week)",
                "Extra active (physical job / intense training)"
            ])
            goal = st.selectbox("Fitness goal", ["Maintain Weight", "Fat Loss", "Muscle Gain"])
            diet = st.multiselect("Dietary constraints", ["Vegan", "Vegetarian", "Keto", "Diabetic-Friendly", "Gluten-Free", "Dairy-Free"])
        with c3:
            meals_per_day = st.selectbox("Meals per day", [3, 4, 5], index=0)
            cuisine_pref = st.selectbox("Preferred food style", ["Indian", "Mixed / global", "Mediterranean", "East Asian"])
            budget = st.selectbox("Grocery budget", ["Budget-conscious", "Moderate", "Flexible"])
            exclusions = st.text_input("Foods to avoid (optional)", placeholder="e.g., peanuts, mushrooms")
        make_plan = st.form_submit_button("🗓️ Build my 7-day plan", type="primary", use_container_width=True)

    if make_plan:
        activity_factors = {
            "Sedentary (little exercise)": 1.2,
            "Lightly active (1–3 days/week)": 1.375,
            "Moderately active (3–5 days/week)": 1.55,
            "Very active (6–7 days/week)": 1.725,
            "Extra active (physical job / intense training)": 1.9,
        }
        # Mifflin-St Jeor equation. If sex is not specified, use a midpoint rather than guessing.
        base = 10 * float(weight) + 6.25 * float(height) - 5 * int(age)
        if sex == "Male":
            bmr = base + 5
        elif sex == "Female":
            bmr = base - 161
        else:
            bmr = base - 78
        tdee = bmr * activity_factors[activity]
        adjustment = {"Maintain Weight": 0, "Fat Loss": -300, "Muscle Gain": 250}[goal]
        target = int(round(max(1200, tdee + adjustment) / 50) * 50)
        st.session_state["meal_profile"] = {
            "age": age, "sex": sex, "weight_kg": weight, "height_cm": height,
            "activity": activity, "goal": goal, "diet": diet, "meals_per_day": meals_per_day,
            "cuisine": cuisine_pref, "budget": budget, "exclusions": exclusions,
            "bmr": round(bmr), "tdee": round(tdee), "target": target,
        }
        prompt = f"""
Create a flexible 7-day meal schedule and consolidated grocery list. Profile:
age {age}, sex for BMR equation {sex}, weight {weight} kg, height {height} cm, activity {activity},
goal {goal}, daily calorie target approximately {target} kcal, dietary constraints {', '.join(diet) or 'none'},
preferred style {cuisine_pref}, budget {budget}, meals per day {meals_per_day}, avoid {exclusions or 'none'}.
Return JSON with daily_calories (number), meal_plan (array of 7 objects each with day, meals (array of objects with meal, dish, approximate_calories, notes)), grocery_list (array of objects with item, quantity, category), nutrition_notes (array of strings).
Ensure exactly 7 days, practical variety, avoid listed foods, respect constraints, and make clear calories are approximate. For Diabetic-Friendly, suggest balanced meals and carbohydrate awareness but do not promise glucose outcomes. Do not prescribe treatment. Avoid dangerously low calorie targets.
"""
        result = safe_ai_call(prompt)
        if result:
            st.session_state["meal_plan_result"] = result
    profile = st.session_state.get("meal_profile")
    result = st.session_state.get("meal_plan_result")
    if profile:
        st.markdown("---")
        st.markdown("#### Your estimated energy targets")
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("BMR", f"{profile['bmr']:,} kcal/day", "Resting energy estimate")
        with c2:
            metric_card("TDEE", f"{profile['tdee']:,} kcal/day", "Estimated maintenance calories")
        with c3:
            metric_card("Daily target", f"{profile['target']:,} kcal/day", profile["goal"])
        st.caption("Mifflin–St Jeor estimate × activity factor. Individual needs vary; the equation is not a diagnosis or prescription.")
    if result:
        if st.session_state.get("demo_mode"):
            st.warning("Demo output: sample result; no personalized meal plan was generated.")
        st.markdown("#### Your 7-day schedule")
        meal_plan = result.get("meal_plan", []) or []
        if meal_plan:
            for day_entry in meal_plan:
                with st.expander(str(day_entry.get("day", "Day"))):
                    for meal_entry in day_entry.get("meals", []) or []:
                        st.markdown(f"**{meal_entry.get('meal', 'Meal')}:** {meal_entry.get('dish', '—')} · ~{meal_entry.get('approximate_calories', '—')} kcal")
                        if meal_entry.get("notes"):
                            st.caption(meal_entry["notes"])
        else:
            st.info("The current demo payload does not include a full meal schedule. Add an API key to generate a personalized seven-day plan.")
        st.markdown("#### Grocery shopping list")
        grocery = result.get("grocery_list", []) or []
        if grocery:
            grocery_df = pd.DataFrame(grocery)
            st.dataframe(grocery_df, use_container_width=True, hide_index=True)
            csv = grocery_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download grocery list (CSV)", csv, "food_verse_grocery_list.csv", "text/csv")
        else:
            st.info("A grocery list will appear here when available.")
        for note in result.get("nutrition_notes", []) or []:
            st.write(f"• {note}")
        show_json_download(result, "food_verse_7_day_meal_plan.json")

st.markdown("---")
footer1, footer2 = st.columns([2, 1])
with footer1:
    st.caption("Food Verse AI · Skill Wallet Capstone Project 3 · Built with Streamlit and multimodal AI")
with footer2:
    st.caption(f"Session date: {date.today().isoformat()}")

with st.expander("ℹ️ Important limitations and safe use"):
    st.markdown("""
    - **Nutrition estimates:** Image-based portion and nutrient estimates are approximate. Verify recipes, labels, and weights for accuracy.
    - **Allergens:** Never rely on image recognition to confirm allergen absence. Check ingredient labels and cross-contact information.
    - **Freshness:** Visual appearance cannot detect all pathogens or toxins. Follow local time-temperature guidance and discard food when in doubt.
    - **Kitchen compliance:** This is a preliminary visual checklist, not a substitute for a trained inspection, logs, or local regulations.
    - **Meal planning:** BMR/TDEE values are estimates, not prescriptions. For pregnancy, eating-disorder history, chronic conditions, or clinical dietary needs, consult a qualified professional.
    - **Privacy:** Uploaded images are sent to the selected AI provider only when live AI mode is enabled. Review that provider's data policies before uploading sensitive material.
    """)
