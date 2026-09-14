import os
import json
import re

from google import genai
from PIL import Image


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from Railway environment variables."
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def clean_json(text: str):
    """
    Removes ```json formatting if Gemini returns it.
    """

    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


def analyze_valorant_image(image_path: str):

    print("Opening Valorant screenshot...")

    image = Image.open(image_path)

    prompt = """
You are the Exalted Era Valorant Mobile statistics analyzer.

Analyze the uploaded Valorant Mobile statistics screenshot.

Read ONLY information clearly visible in the screenshot.

Return ONLY valid JSON.

Use exactly this structure:

{
    "player_name": "Player name",
    "kills": 0,
    "deaths": 0,
    "assists": 0,
    "acs": 0,
    "headshot_percentage": 0,
    "result": "WIN or LOSS"
}

RULES:

- Do not invent statistics.
- If the player name cannot be identified, use "Unknown Player".
- If a numerical statistic cannot be found, use null.
- kills must only contain kills.
- deaths must only contain deaths.
- assists must only contain assists.
- acs means Average Combat Score.
- headshot_percentage must contain the number only.
- Do not include the % symbol inside headshot_percentage.
- result should be WIN, LOSS, DRAW, or UNKNOWN.
- Do not add markdown.
- Do not add explanations.
- Return JSON only.
"""

    print("Sending image to Gemini 3.6 Flash...")

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            prompt,
            image
        ]
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    print("Raw Gemini response:")
    print(response.text)

    cleaned_response = clean_json(
        response.text
    )

    try:

        result = json.loads(
            cleaned_response
        )

    except json.JSONDecodeError as error:

        print("Gemini returned invalid JSON:")
        print(cleaned_response)

        raise RuntimeError(
            f"Gemini returned invalid JSON: {error}"
        )

    return result
