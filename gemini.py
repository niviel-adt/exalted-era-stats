import os
import json

from google import genai
from PIL import Image


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def analyze_valorant_image(image_path):

    image = Image.open(image_path)

    prompt = """
You are a Valorant Mobile China statistics extraction system.

The screenshot may contain Chinese text.

Your job is to:
1. Read the screenshot.
2. Understand Chinese labels.
3. Identify the player's statistics.
4. Translate the relevant information into English.
5. Return ONLY valid JSON.

Use exactly this format:

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

- The screenshot may contain Chinese.
- Translate Chinese labels into English.
- "result" must be "win", "loss", or null.
- Do not guess values.
- Use null when a value cannot be clearly read.
- Numbers must be numbers, not strings.
- Keep the player's name as shown when possible.
- Return ONLY raw JSON.
- Do not use markdown.
- Do not add explanations.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            prompt,
            image
        ]
    )

    text = response.text.strip()

    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    return json.loads(text)
