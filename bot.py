import os
import asyncio
import tempfile

import discord
from discord import app_commands
from dotenv import load_dotenv

from gemini import analyze_valorant_image


# =========================
# LOAD ENVIRONMENT VARIABLES
# =========================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is missing from Railway environment variables."
    )


# =========================
# EXALTED ERA SERVER
# =========================

GUILD_ID = 1545457876552655008
GUILD = discord.Object(id=GUILD_ID)


# =========================
# BOT CLASS
# =========================

class ExaltedEraBot(discord.Client):

    def __init__(self):
        intents = discord.Intents.default()

        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):

        try:
            synced = await self.tree.sync(guild=GUILD)

            print(
                f"Synced {len(synced)} slash command(s) "
                f"to Exalted Era."
            )

            for command in synced:
                print(f"Synced command: /{command.name}")

        except Exception as error:

            print("========== COMMAND SYNC ERROR ==========")
            print(type(error).__name__)
            print(str(error))
            print("=========================================")


bot = ExaltedEraBot()


# =========================
# BOT READY
# =========================

@bot.event
async def on_ready():

    print("")
    print("========================================")
    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print("Exalted Era Stats Bot is online!")
    print("========================================")
    print("")


# =========================
# /TEST COMMAND
# =========================

@bot.tree.command(
    name="test",
    description="Check if the Exalted Era Stats Bot is working.",
    guild=GUILD
)
async def test(interaction: discord.Interaction):

    await interaction.response.send_message(
        "🏆 **EXALTED ERA STATS BOT**\n\n"
        "✅ Bot is online and working.\n"
        "✅ Slash commands are responding.\n\n"
        "**THE ERA IS HERE.**"
    )


# =========================
# /ANALYZE COMMAND
# =========================

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

    # Immediately acknowledge Discord
    # so it does not show "Application did not respond"
    try:
        await interaction.response.defer(thinking=True)

    except Exception as error:

        print("Could not defer interaction:")
        print(type(error).__name__)
        print(str(error))

        return

    print("")
    print("========== ANALYZE COMMAND ==========")
    print(f"Requested by: {interaction.user}")
    print(f"User ID: {interaction.user.id}")
    print(f"Filename: {screenshot.filename}")
    print(f"Content type: {screenshot.content_type}")
    print("=====================================")


    # =========================
    # VALIDATE IMAGE
    # =========================

    valid_extensions = (
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    )

    filename = screenshot.filename.lower()

    is_image_type = (
        screenshot.content_type
        and screenshot.content_type.startswith("image/")
    )

    is_image_extension = filename.endswith(valid_extensions)

    if not is_image_type and not is_image_extension:

        await interaction.followup.send(
            "❌ Please upload a valid image.\n\n"
            "Supported formats:\n"
            "`PNG`, `JPG`, `JPEG`, `WEBP`"
        )

        return


    # =========================
    # CREATE UNIQUE TEMP FILE
    # =========================

    suffix = os.path.splitext(screenshot.filename)[1]

    if not suffix:
        suffix = ".png"

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    )

    image_path = temp_file.name

    temp_file.close()


    try:

        # =========================
        # DOWNLOAD SCREENSHOT
        # =========================

        print("Downloading screenshot...")

        await screenshot.save(image_path)

        print(f"Screenshot saved to: {image_path}")


        # =========================
        # SEND TO GEMINI
        # =========================

        print("Sending screenshot to Gemini...")

        stats = await asyncio.wait_for(
            asyncio.to_thread(
                analyze_valorant_image,
                image_path
            ),
            timeout=90
        )

        print("Gemini analysis completed.")

        print("Gemini result:")
        print(stats)


        # =========================
        # VALIDATE RESULT
        # =========================

        if not isinstance(stats, dict):

            raise ValueError(
                "Gemini did not return a valid statistics dictionary."
            )


        # =========================
        # FORMAT RESULTS
        # =========================

        player_name = (
            stats.get("player_name")
            or "Unknown Player"
        )

        kills = (
            stats.get("kills")
            if stats.get("kills") is not None
            else "N/A"
        )

        deaths = (
            stats.get("deaths")
            if stats.get("deaths") is not None
            else "N/A"
        )

        assists = (
            stats.get("assists")
            if stats.get("assists") is not None
            else "N/A"
        )

        acs = (
            stats.get("acs")
            if stats.get("acs") is not None
            else "N/A"
        )

        headshot = (
            stats.get("headshot_percentage")
            if stats.get("headshot_percentage") is not None
            else "N/A"
        )

        result = stats.get("result") or "N/A"


        # Add percent symbol if Gemini returns a number
        if headshot != "N/A":

            headshot = f"{headshot}%"


        # =========================
        # CREATE DISCORD EMBED
        # =========================

        embed = discord.Embed(
            title="🏆 EXALTED ERA PERFORMANCE",
            description=f"### {player_name}",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="⚔️ Kills",
            value=str(kills),
            inline=True
        )

        embed.add_field(
            name="💀 Deaths",
            value=str(deaths),
            inline=True
        )

        embed.add_field(
            name="🤝 Assists",
            value=str(assists),
            inline=True
        )

        embed.add_field(
            name="🎯 ACS",
            value=str(acs),
            inline=True
        )

        embed.add_field(
            name="💥 HS%",
            value=str(headshot),
            inline=True
        )

        embed.add_field(
            name="🏁 Result",
            value=str(result).upper(),
            inline=True
        )

        embed.set_footer(
            text="EXALTED ERA • THE ERA IS HERE."
        )


        # =========================
        # SEND RESULT
        # =========================

        await interaction.followup.send(
            embed=embed
        )

        print("Analysis result sent successfully.")


    # =========================
    # TIMEOUT
    # =========================

    except asyncio.TimeoutError:

        print("Gemini analysis timed out.")

        await interaction.followup.send(
            "⏱️ **Analysis timed out.**\n\n"
            "Gemini took longer than 90 seconds. "
            "Please try the screenshot again."
        )


    # =========================
    # OTHER ERRORS
    # =========================

    except Exception as error:

        print("")
        print("========== ANALYSIS ERROR ==========")
        print(type(error).__name__)
        print(str(error))
        print("====================================")
        print("")

        try:

            await interaction.followup.send(
                "❌ **I couldn't analyze this screenshot.**\n\n"
                "Please try again. If it keeps happening, "
                "check the Railway logs for the error."
            )

        except Exception as followup_error:

            print("Could not send error response:")
            print(type(followup_error).__name__)
            print(str(followup_error))


    # =========================
    # DELETE TEMP IMAGE
    # =========================

    finally:

        try:

            if os.path.exists(image_path):

                os.remove(image_path)

                print("Temporary screenshot deleted.")

        except Exception as cleanup_error:

            print(
                f"Could not delete temporary image: "
                f"{cleanup_error}"
            )


# =========================
# RUN BOT
# =========================

print("Starting Exalted Era Stats Bot...")

bot.run(TOKEN)
