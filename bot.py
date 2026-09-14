import os
import asyncio
import discord
from discord import app_commands
from dotenv import load_dotenv

from gemini import analyze_valorant_image

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1545457876552655008
GUILD = discord.Object(id=GUILD_ID)


class ExaltedEraBot(discord.Client):

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync(guild=GUILD)

        print("Slash commands synced to Exalted Era server.")


bot = ExaltedEraBot()


@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")
    print("Exalted Era Stats Bot is online!")


@bot.tree.command(
    name="test",
    description="Check if the Exalted Era Stats Bot is working.",
    guild=GUILD
)
async def test(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🏆 **EXALTED ERA STATS BOT**\n"
        "Bot is online and working.\n\n"
        "THE ERA IS HERE."
    )


@bot.tree.command(
    name="analyze",
    description="Analyze a Valorant Mobile statistics screenshot.",
    guild=GUILD
)
@app_commands.describe(
    screenshot="Upload your Valorant Mobile statistics screenshot."
)
async def analyze(
    interaction: discord.Interaction,
    screenshot: discord.Attachment
):

    # Respond to Discord immediately
    await interaction.response.defer(thinking=True)

    print("Analyze command received.")

    # Check file
    if not screenshot.content_type:
        await interaction.followup.send(
            "❌ Please upload an image."
        )
        return

    if not screenshot.content_type.startswith("image"):
        await interaction.followup.send(
            "❌ Please upload a valid image file."
        )
        return

    image_path = "temp_image.png"

    try:

        print("Downloading screenshot...")

        await screenshot.save(image_path)

        print("Screenshot downloaded.")
        print("Sending screenshot to Gemini...")

        # Run Gemini without blocking Discord
        stats = await asyncio.to_thread(
            analyze_valorant_image,
            image_path
        )

        print("Gemini analysis completed.")
        print(stats)

        player = stats.get("player_name") or "Unknown Player"
        kills = stats.get("kills")
        deaths = stats.get("deaths")
        assists = stats.get("assists")
        acs = stats.get("acs")
        hs = stats.get("headshot_percentage")
        result = stats.get("result")

        embed = discord.Embed(
            title="🏆 EXALTED ERA PERFORMANCE",
            description=f"**{player}**"
        )

        embed.add_field(
            name="⚔️ Kills",
            value=str(kills if kills is not None else "N/A"),
            inline=True
        )

        embed.add_field(
            name="💀 Deaths",
            value=str(deaths if deaths is not None else "N/A"),
            inline=True
        )

        embed.add_field(
            name="🤝 Assists",
            value=str(assists if assists is not None else "N/A"),
            inline=True
        )

        embed.add_field(
            name="🎯 ACS",
            value=str(acs if acs is not None else "N/A"),
            inline=True
        )

        embed.add_field(
            name="💥 HS%",
            value=str(hs if hs is not None else "N/A"),
            inline=True
        )

        embed.add_field(
            name="🏁 Result",
            value=str(result if result else "N/A").upper(),
            inline=True
        )

        embed.set_footer(
            text="EXALTED ERA • THE ERA IS HERE."
        )

        await interaction.followup.send(
            embed=embed
        )

        print("Result sent to Discord.")

    except Exception as e:

        print("================================")
        print("ANALYSIS ERROR")
        print(type(e).__name__)
        print(str(e))
        print("================================")

        await interaction.followup.send(
            "❌ **I couldn't analyze this screenshot.**\n\n"
            "The bot received your image, but Gemini could not process it."
        )

    finally:

        if os.path.exists(image_path):
            os.remove(image_path)


bot.run(TOKEN))
@app_commands.describe(
    screenshot="Upload your Valorant Mobile statistics screenshot."
)
async def analyze(
    interaction: discord.Interaction,
    screenshot: discord.Attachment
):

    await interaction.response.defer()

    if not screenshot.content_type:
        await interaction.followup.send(
            "❌ Please upload an image."
        )
        return

    if not screenshot.content_type.startswith("image"):
        await interaction.followup.send(
            "❌ Please upload a valid image file."
        )
        return

    image_path = "temp_image.png"

    try:

        await screenshot.save(image_path)

        await interaction.followup.send(
            "🔍 **Reading your Valorant Mobile screenshot...**\n"
            "🇨🇳 Chinese text detected → translating statistics to English."
        )

        stats = analyze_valorant_image(image_path)

        player = stats.get("player_name") or "Unknown Player"
        kills = stats.get("kills")
        deaths = stats.get("deaths")
        assists = stats.get("assists")
        acs = stats.get("acs")
        hs = stats.get("headshot_percentage")
        result = stats.get("result")

        embed = discord.Embed(
            title="🏆 EXALTED ERA PERFORMANCE",
            description=f"**{player}**",
        )

        embed.add_field(
            name="⚔️ Kills",
            value=str(kills if kills is not None else "N/A"),
            inline=True
        )

        embed.add_field(
            name="💀 Deaths",
            value=str(deaths if deaths is not None else "N/A"),
            inline=True
        )

        embed.add_field(
            name="🤝 Assists",
            value=str(assists if assists is not None else "N/A"),
            inline=True
        )

        embed.add_field(
            name="🎯 ACS",
            value=str(acs if acs is not None else "N/A"),
            inline=True
        )

        embed.add_field(
            name="💥 HS%",
            value=str(hs if hs is not None else "N/A"),
            inline=True
        )

        embed.add_field(
            name="🏁 Result",
            value=str(result if result else "N/A").upper(),
            inline=True
        )

        embed.set_footer(
            text="EXALTED ERA • THE ERA IS HERE."
        )

        await interaction.followup.send(embed=embed)

    except Exception as e:

        print("ANALYSIS ERROR:", e)

        await interaction.followup.send(
            "❌ **I couldn't read this screenshot.**\n"
            "Please upload a clear Valorant Mobile China statistics screen."
        )

    finally:

        if os.path.exists(image_path):
            os.remove(image_path)


bot.run(TOKEN)
