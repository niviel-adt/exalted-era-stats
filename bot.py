import asyncio
import os
import tempfile
from pathlib import Path

import discord
from discord import app_commands
from dotenv import load_dotenv

from gemini import analyze_valorant_image

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1545457876552655008
GUILD = discord.Object(id=GUILD_ID)

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is missing. Add it in Railway > Variables."
    )


def show(value):
    """Display a normal value without turning 0 into N/A."""
    return "N/A" if value is None else str(value)


def show_percent(value):
    return "N/A" if value is None else f"{value}%"


class ExaltedEraBot(discord.Client):
    def __init__(self):
        # Slash commands do not require Message Content intent.
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # The local guild tree contains only /analyze.
        # Syncing it also removes stale guild commands such as an old /test.
        synced = await self.tree.sync(guild=GUILD)
        names = ", ".join(f"/{cmd.name}" for cmd in synced) or "(none)"
        print(
            f"Synced {len(synced)} slash command(s) "
            f"to Exalted Era: {names}"
        )


bot = ExaltedEraBot()


@bot.event
async def on_ready():
    print("=" * 50)
    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id if bot.user else 'Unknown'}")
    print("Exalted Era Stats Bot is online!")
    print("=" * 50)


@bot.tree.command(
    name="analyze",
    description="Analyze a Valorant Mobile player statistics screenshot.",
    guild=GUILD,
)
@app_commands.describe(
    screenshot="Upload the Valorant Mobile statistics screenshot."
)
async def analyze(
    interaction: discord.Interaction,
    screenshot: discord.Attachment,
):
    # Acknowledge Discord immediately so the interaction does not time out.
    await interaction.response.defer(thinking=True)

    content_type = (screenshot.content_type or "").lower()
    suffix = Path(screenshot.filename).suffix.lower()
    allowed_suffixes = {".png", ".jpg", ".jpeg", ".webp"}

    if not (
        content_type.startswith("image/")
        or suffix in allowed_suffixes
    ):
        await interaction.followup.send(
            "❌ Please upload a PNG, JPG, JPEG, or WEBP screenshot.",
            ephemeral=True,
        )
        return

    if suffix not in allowed_suffixes:
        suffix = ".png"

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            temp_path = temp_file.name

        print("")
        print("========== ANALYZE COMMAND ==========")
        print(f"Requested by: {interaction.user}")
        print(f"User ID: {interaction.user.id}")
        print(f"Filename: {screenshot.filename}")
        print("Downloading screenshot...")

        await screenshot.save(temp_path)

        print(f"Saved to: {temp_path}")
        print("Sending screenshot to Gemini...")

        stats = await asyncio.wait_for(
            asyncio.to_thread(
                analyze_valorant_image,
                temp_path,
                content_type or None,
            ),
            timeout=90,
        )

        print("Gemini analysis completed.")
        print(stats)

        hit_distribution = stats.get("hit_distribution") or {}
        head = hit_distribution.get("head") or {}
        torso = hit_distribution.get("torso") or {}
        leg = hit_distribution.get("leg") or {}

        embed = discord.Embed(
            title="🏆 EXALTED ERA PLAYER STATS",
            description="**VALORANT MOBILE • PERFORMANCE ANALYSIS**",
            color=discord.Color.gold(),
        )

        # 1–3
        embed.add_field(
            name="⚔️ Kills",
            value=show(stats.get("kills")),
            inline=True,
        )
        embed.add_field(
            name="🎯 ACS",
            value=show(stats.get("acs")),
            inline=True,
        )
        embed.add_field(
            name="💥 HS%",
            value=show_percent(stats.get("headshot_percentage")),
            inline=True,
        )

        # 4–6
        embed.add_field(
            name="🎮 Total Matches",
            value=show(stats.get("total_matches")),
            inline=True,
        )
        embed.add_field(
            name="⚔️ K/D",
            value=show(stats.get("kd_ratio")),
            inline=True,
        )
        embed.add_field(
            name="🔥 First Bloods",
            value=show(stats.get("first_bloods")),
            inline=True,
        )

        # 7: Head / Torso / Leg hit distribution
        embed.add_field(
            name="──────── HIT DISTRIBUTION ────────",
            value="\u200b",
            inline=False,
        )

        embed.add_field(
            name="🎯 Head",
            value=(
                f"**{show_percent(head.get('percentage'))}**\n"
                f"{show(head.get('count'))} Hits"
            ),
            inline=True,
        )
        embed.add_field(
            name="🛡️ Torso",
            value=(
                f"**{show_percent(torso.get('percentage'))}**\n"
                f"{show(torso.get('count'))} Hits"
            ),
            inline=True,
        )
        embed.add_field(
            name="🦵 Legs",
            value=(
                f"**{show_percent(leg.get('percentage'))}**\n"
                f"{show(leg.get('count'))} Hits"
            ),
            inline=True,
        )

        embed.set_footer(
            text="EXALTED ERA • VALORANT MOBILE"
        )

        await interaction.followup.send(embed=embed)
        print("Result sent to Discord.")

    except asyncio.TimeoutError:
        print("Gemini analysis timed out.")
        await interaction.followup.send(
            "⏱️ Analysis took too long. Please try the screenshot again.",
            ephemeral=True,
        )

    except Exception as error:
        print("")
        print("========== ANALYSIS ERROR ==========")
        print(type(error).__name__)
        print(str(error))
        print("====================================")
        print("")

        try:
            await interaction.followup.send(
                "❌ I couldn't analyze this screenshot. "
                "Please check the Railway logs for the exact error.",
                ephemeral=True,
            )
        except Exception as followup_error:
            print(
                "Could not send the Discord error message:",
                repr(followup_error),
            )

    finally:
        if temp_path:
            try:
                os.remove(temp_path)
                print("Temporary screenshot deleted.")
            except FileNotFoundError:
                pass
            except Exception as cleanup_error:
                print(
                    "Could not delete temporary screenshot:",
                    repr(cleanup_error),
                )


print("Starting Exalted Era Stats Bot...")
bot.run(TOKEN)
