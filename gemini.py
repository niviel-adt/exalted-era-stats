import json
import mimetypes
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it in Railway > Variables."
    )

client = genai.Client(api_key=API_KEY)


PROMPT = r"""
You are the Exalted Era Valorant Mobile statistics extraction system.

Analyze the uploaded PLAYER STATISTICS screenshot.
The interface may be in Chinese.

IMPORTANT SCREEN RULE:
- IGNORE the radar / polygon chart on the LEFT.
- Use the printed NUMBERED statistics on the RIGHT side.
- Extract ONLY the seven categories requested below.
- Do not return any other statistics.

EXTRACT ONLY:

1. Kills
2. Average Combat Score (ACS)
3. HS%
4. Total Matches
5. K/D
6. First Bloods
7. Head / Torso / Leg hit distribution
   - hit count
   - percentage

CHINESE LABEL MAPPING:

击败 = Kills
平均战斗评分 = ACS
精准击败率 = HS%
总场次 = Total Matches
击败/败阵 = K/D
率先击败 = First Bloods

头部占比 = Head hit distribution
躯干占比 = Torso hit distribution
腿部占比 = Leg hit distribution

VERY IMPORTANT:
- HS% MUST come from 精准击败率 when that label is visible.
- Do NOT use 头部占比 as HS% if 精准击败率 is present.
- 头部占比 belongs only to Head hit distribution.
- For Head / Torso / Leg distribution, read BOTH the printed hit count
  and the printed percentage.

RETURN ONLY VALID JSON WITH EXACTLY THIS STRUCTURE:

{
  "kills": null,
  "acs": null,
  "headshot_percentage": null,
  "total_matches": null,
  "kd_ratio": null,
  "first_bloods": null,
  "hit_distribution": {
    "head": {
      "count": null,
      "percentage": null
    },
    "torso": {
      "count": null,
      "percentage": null
    },
    "leg": {
      "count": null,
      "percentage": null
    }
  }
}

RULES:
- Read only values clearly printed in the screenshot.
- Never estimate a value from the radar chart.
- Never invent a value.
- If a requested value is unreadable, return null.
- All numeric values must be JSON numbers, not strings.
- Percentage values must NOT contain the % symbol.
  Example: 23.2% becomes 23.2.
- Do not return player name.
- Do not return win rate.
- Do not return MVP count.
- Do not return recent record.
- Do not return deaths.
- Do not return assists.
- Do not return match result.
- Do not include markdown.
- Do not include commentary.
- Output JSON only.
"""


def _clean_json(text: str) -> str:
    text = (text or "").strip()

    # Defensive cleanup in case a model still wraps JSON in fences.
    text = re.sub(
        r"^\s*```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s*```\s*$", "", text)
    return text.strip()


def _normalize_result(data: dict) -> dict:
    """
    Keep only the seven requested categories even if the model
    unexpectedly returns extra keys.
    """
    distribution = data.get("hit_distribution")
    if not isinstance(distribution, dict):
        distribution = {}

    def part(name):
        value = distribution.get(name)
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
            "head": {
                "count": head.get("count"),
                "percentage": head.get("percentage"),
            },
            "torso": {
                "count": torso.get("count"),
                "percentage": torso.get("percentage"),
            },
            "leg": {
                "count": leg.get("count"),
                "percentage": leg.get("percentage"),
            },
        },
    }


def analyze_valorant_image(
    image_path: str,
    discord_content_type: str | None = None,
) -> dict:
    path = Path(image_path)

    mime_type = (
        discord_content_type
        if discord_content_type
        and discord_content_type.startswith("image/")
        else mimetypes.guess_type(path.name)[0]
    ) or "image/png"

    image_bytes = path.read_bytes()

    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=mime_type,
    )

    print(f"Gemini model: {MODEL}")

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            PROMPT,
            image_part,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0,
        ),
    )

    text = _clean_json(response.text)

    if not text:
        raise RuntimeError("Gemini returned an empty response.")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        print("Raw Gemini response:")
        print(response.text)
        raise RuntimeError(
            f"Gemini returned invalid JSON: {error}"
        ) from error

    if not isinstance(data, dict):
        raise RuntimeError(
            "Gemini returned JSON, but it was not a JSON object."
        )

    return _normalize_result(data)
