import os
import json
from google import genai
from PIL import Image

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from Railway environment variables."
    )

client = genai.Client(api_key=API_KEY)


def analyze_valorant_image(image_path):
    image = Image.open(image_path)

    prompt = """
You are a Valorant Mobile China statistics extraction system.
The screenshot may contain Chinese text.
Read the screenshot and extract the player's match statistics.

Return ONLY valid JSON in exactly this structure:

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
- Understand and translate Chinese labels into English.
- Keep the player's name as shown when possible.
- "result" must be "win", "loss", or null.
- Do not guess.
- Use null when a value cannot be clearly read.
- Numeric values must be JSON numbers, not strings.
- Return raw JSON only. No markdown or explanations.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image],
    )

    text = (response.text or "").strip()

    if text.startswith("```"):
        text = text.replace("```json", "", 1)
        text = text.replace("```", "", 1).strip()

    return json.loads(text)
