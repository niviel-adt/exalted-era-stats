import json
import mimetypes
import os
import random
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing in Railway Variables.")

client = genai.Client(api_key=API_KEY)

PROMPT = r"""
You are the Exalted Era Valorant Mobile statistics extraction system.

Analyze the uploaded PLAYER STATISTICS screenshot.
The interface may be in Chinese.

IGNORE the radar/polygon chart on the LEFT.
Use the printed numerical statistics on the RIGHT side.

Extract ONLY:
1. Kills
2. Average Combat Score (ACS)
3. HS%
4. Total Matches
5. K/D
6. First Bloods
7. Head / Torso / Leg hit distribution:
   - hit count
   - percentage

Chinese mappings:
击败 = Kills
平均战斗评分 = ACS
精准击败率 = HS%
总场次 = Total Matches
击败/败阵 = K/D
率先击败 = First Bloods
头部占比 = Head distribution
躯干占比 = Torso distribution
腿部占比 = Leg distribution

Important:
- HS% must come from 精准击败率 when visible.
- Do not substitute 头部占比 for HS%.
- 头部占比 belongs only to Head hit distribution.
- Read both hit count and percentage for Head/Torso/Leg.
- Never estimate from the radar graph.
- Never invent unreadable values; use null.
- Numeric values must be JSON numbers, not strings.
- Percentages must omit the %% symbol.
- Do not return player name, win rate, MVP, recent record, deaths,
  assists, or result.
- Return JSON only.

Exact JSON structure:
{
  "kills": null,
  "acs": null,
  "headshot_percentage": null,
  "total_matches": null,
  "kd_ratio": null,
  "first_bloods": null,
  "hit_distribution": {
    "head": {"count": null, "percentage": null},
    "torso": {"count": null, "percentage": null},
    "leg": {"count": null, "percentage": null}
  }
}
"""

DEFAULT_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]


def model_chain():
    preferred = os.getenv("GEMINI_MODEL", "").strip()
    configured = os.getenv("GEMINI_MODEL_CHAIN", "").strip()

    models = []
    if configured:
        models.extend(x.strip() for x in configured.split(",") if x.strip())
    elif preferred:
        models.append(preferred)

    models.extend(DEFAULT_MODELS)

    unique = []
    for model in models:
        if model not in unique:
            unique.append(model)
    return unique


def clean_json(text: str):
    text = (text or "").strip()
    text = re.sub(r"^\s*```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text)
    return text.strip()


def normalize(data: dict):
    dist = data.get("hit_distribution")
    if not isinstance(dist, dict):
        dist = {}

    def part(name):
        value = dist.get(name)
        return value if isinstance(value, dict) else {}

    head = part("head")
    torso = part("torso")
    leg = part("leg")

    return {
        "kills": data.get("kills"),
        "acs": data.get("acs"),
        "headshot_percentage": data.get("headshot_percentage"),
        "total_matches": data.get("total_matches"),
        "kd_ratio": data.get("kd_ratio"),
        "first_bloods": data.get("first_bloods"),
        "hit_distribution": {
            "head": {"count": head.get("count"), "percentage": head.get("percentage")},
            "torso": {"count": torso.get("count"), "percentage": torso.get("percentage")},
            "leg": {"count": leg.get("count"), "percentage": leg.get("percentage")},
        },
    }


def error_code(error):
    for name in ("code", "status_code"):
        value = getattr(error, name, None)
        try:
            return int(value)
        except (TypeError, ValueError):
            pass
    return None


def generate_with_fallback(image_part):
    models = model_chain()
    last_error = None

    print("Gemini chain:", " -> ".join(models))

    for model in models:
        for attempt in range(1, 3):
            try:
                print(f"Trying {model}, attempt {attempt}/2")
                response = client.models.generate_content(
                    model=model,
                    contents=[PROMPT, image_part],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                )
                print(f"Gemini success: {model}")
                return response

            except errors.APIError as error:
                last_error = error
                code = error_code(error)
                print(f"Gemini API error: model={model}, code={code}")
                print(str(error))

                if code == 404:
                    break

                if code in {429, 500, 502, 503, 504}:
                    if attempt < 2:
                        delay = (2 ** attempt) + random.uniform(0.5, 1.5)
                        print(f"Temporary error. Retry in {delay:.1f}s.")
                        time.sleep(delay)
                        continue
                    break

                raise

    raise RuntimeError(f"All Gemini fallback models failed. Last error: {last_error}")


def analyze_valorant_image(image_path: str, discord_content_type: str | None = None):
    path = Path(image_path)

    mime_type = (
        discord_content_type
        if discord_content_type and discord_content_type.startswith("image/")
        else mimetypes.guess_type(path.name)[0]
    ) or "image/png"

    image_part = types.Part.from_bytes(data=path.read_bytes(), mime_type=mime_type)

    response = generate_with_fallback(image_part)
    text = clean_json(response.text)

    if not text:
        raise RuntimeError("Gemini returned an empty response.")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        print("Raw Gemini response:", response.text)
        raise RuntimeError(f"Gemini returned invalid JSON: {error}") from error

    if not isinstance(data, dict):
        raise RuntimeError("Gemini response was not a JSON object.")

    return normalize(data)
