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
1. Read and understand the Chinese text.
2. Identify the player's statistics.
3. Translate relevant Chinese labels into English.
4. Return the final data in English.

Return ONLY valid JSON using this exact format:

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
- Translate Chinese labels and match results into English.
- "result" must be "win", "loss", or null.
- Do not guess.
- Use null if a value cannot be clearly read.
- Numbers must be numbers, not strings.
- Keep the player's name as shown when possible.
- Return ONLY raw JSON.
- Do not include markdown.
- Do not include explanations.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            prompt,
            image
        ]
    )

    text = response.text.strip()

    # Remove markdown code fences if Gemini adds them
    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    return json.loads(text)
