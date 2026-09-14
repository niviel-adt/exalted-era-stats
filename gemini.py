import os
import json
from google import genai
from PIL import Image

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_valorant_image(image_path):
    image = Image.open(image_path)

    prompt = """
You are a Valorant statistics extraction system.

Analyze this Valorant screenshot and extract the player's statistics.

Return ONLY valid JSON using this format:

{
    "player_name": null,
    "kills": null,
    "deaths": null,
    "assists": null,
    "acs": null,
    "headshot_percentage": null,
    "result": null
}

Rules:
- Use null if a statistic cannot be clearly read.
- Do not guess.
- Return numbers as numbers, not strings.
- result should be "win", "loss", or null.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image]
    )

    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)
