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
        self.tree.clear_commands(guild=GUILD)
        self.tree.copy_global_to(guild=GUILD)
        synced = await self.tree.sync(guild=GUILD)
        print(f"Synced {len(synced)} slash command(s) to Exalted Era.")

bot = ExaltedEraBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Exalted Era Stats Bot is online!")

@bot.tree.command(name="test", description="Check if the bot is working.", guild=GUILD)
async def test(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🏆 **EXALTED ERA STATS BOT**\nBot is online and working.\n\nTHE ERA IS HERE."
    )

@bot.tree.command(name="analyze", description="Analyze a Valorant Mobile statistics screenshot.", guild=GUILD)
@app_commands.describe(screenshot="Upload your Valorant Mobile statistics screenshot.")
async def analyze(interaction: discord.Interaction, screenshot: discord.Attachment):
    await interaction.response.defer(thinking=True)
    print("Analyze command received.")

    if not screenshot.content_type or not screenshot.content_type.startswith("image"):
        await interaction.followup.send("❌ Please upload a valid image.")
        return

    image_path = "temp_valorant_image.png"

    try:
        print(f"Downloading screenshot: {screenshot.filename}")
        await screenshot.save(image_path)
        print("Screenshot downloaded.")
        print("Sending screenshot to Gemini...")

        stats = await asyncio.wait_for(
            asyncio.to_thread(analyze_valorant_image, image_path),
            timeout=90
        )

        print("Gemini analysis completed.")

        embed = discord.Embed(
            title="🏆 EXALTED ERA PERFORMANCE",
            description=f"**{stats.get('player_name') or 'Unknown Player'}**"
        )
        embed.add_field(name="⚔️ Kills", value=str(stats.get("kills") if stats.get("kills") is not None else "N/A"), inline=True)
        embed.add_field(name="💀 Deaths", value=str(stats.get("deaths") if stats.get("deaths") is not None else "N/A"), inline=True)
        embed.add_field(name="🤝 Assists", value=str(stats.get("assists") if stats.get("assists") is not None else "N/A"), inline=True)
        embed.add_field(name="🎯 ACS", value=str(stats.get("acs") if stats.get("acs") is not None else "N/A"), inline=True)
        embed.add_field(name="💥 HS%", value=str(stats.get("headshot_percentage") if stats.get("headshot_percentage") is not None else "N/A"), inline=True)
        embed.add_field(name="🏁 Result", value=str(stats.get("result") or "N/A").upper(), inline=True)
        embed.set_footer(text="EXALTED ERA • THE ERA IS HERE.")

        await interaction.followup.send(embed=embed)
        print("Result sent to Discord.")

    except asyncio.TimeoutError:
        print("Gemini analysis timed out after 90 seconds.")
        await interaction.followup.send("⏱️ **Gemini took too long to analyze the screenshot.**")

    except Exception as e:
        print("========== ANALYSIS ERROR ==========")
        print(type(e).__name__)
        print(str(e))
        print("====================================")
        await interaction.followup.send("❌ **I couldn't analyze this screenshot.** Check Railway logs.")

    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from Railway environment variables.")

bot.run(TOKEN)
