import os
import json
from google import genai
from PIL import Image

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_valorant_image(image_path):
    image = Image.open(image_path)

  prompt = """
You are a Valorant Mobile statistics extraction system.

The screenshot may be from Valorant Mobile China and may contain Chinese text.

Your job is to:
1. Read and understand the Chinese text and numbers in the screenshot.
2. Identify the player's match statistics.
3. Translate any relevant Chinese labels or results into English.
4. Return the final data ONLY in English.

Return ONLY valid JSON in this exact format:

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
- The input screenshot may contain Chinese.
- Translate the result into English.
- result must ONLY be "win", "loss", or null.
- Keep the player's name exactly as shown unless it is Chinese, in which case provide an English/romanized version if clearly possible.
- Do not guess.
- Use null if a value cannot be clearly read.
- Numbers must be numbers, not strings.
- Return ONLY raw valid JSON.
- Do not include explanations or markdown.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image]
    )

    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)
