import asyncio
import io
import os
import tempfile
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from dotenv import load_dotenv

from database import Database
from gemini import analyze_valorant_image
from player_card import render_player_card
from ratings import calculate_rating, rating_label

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "1545457876552655008"))
ARCHIVE_CHANNEL_ID = int(os.getenv("STATS_ARCHIVE_CHANNEL_ID", "0") or 0)

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing in Railway Variables.")

GUILD = discord.Object(id=GUILD_ID)
db = Database()


def show(value, digits: Optional[int] = None):
    if value is None:
        return "N/A"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        digits = 2 if digits is None else digits
        text = f"{value:.{digits}f}"
        return text.rstrip("0").rstrip(".")
    return str(value)


def show_percent(value):
    return "N/A" if value is None else f"{show(value, 1)}%"


def hit_line(part: dict):
    if not part:
        return "N/A"
    count = part.get("count")
    pct = part.get("percentage")
    if count is None and pct is None:
        return "N/A"
    return f"**{show_percent(pct)}**\n{show(count)} Hits"


def delta_text(current, previous, *, percent=False, digits=2):
    if current is None or previous is None:
        return "N/A"
    change = current - previous
    arrow = "▲" if change > 0 else "▼" if change < 0 else "•"
    sign = "+" if change > 0 else ""
    suffix = "%" if percent else ""
    return f"{arrow} {sign}{show(change, digits)}{suffix}"


def snapshot_stats(snapshot: dict):
    return {
        "kills": snapshot.get("kills"),
        "acs": snapshot.get("acs"),
        "headshot_percentage": snapshot.get("headshot_percentage"),
        "total_matches": snapshot.get("total_matches"),
        "kd_ratio": snapshot.get("kd_ratio"),
        "first_bloods": snapshot.get("first_bloods"),
        "hit_distribution": {
            "head": {
                "count": snapshot.get("head_count"),
                "percentage": snapshot.get("head_percentage"),
            },
            "torso": {
                "count": snapshot.get("torso_count"),
                "percentage": snapshot.get("torso_percentage"),
            },
            "leg": {
                "count": snapshot.get("leg_count"),
                "percentage": snapshot.get("leg_percentage"),
            },
        },
    }


def add_core_stats(embed: discord.Embed, stats: dict):
    embed.add_field(name="⚔️ Kills", value=show(stats.get("kills")), inline=True)
    embed.add_field(name="🎯 ACS", value=show(stats.get("acs"), 1), inline=True)
    embed.add_field(name="💥 HS%", value=show_percent(stats.get("headshot_percentage")), inline=True)
    embed.add_field(name="🎮 Total Matches", value=show(stats.get("total_matches")), inline=True)
    embed.add_field(name="⚔️ K/D", value=show(stats.get("kd_ratio"), 2), inline=True)
    embed.add_field(name="🔥 First Bloods", value=show(stats.get("first_bloods")), inline=True)


def add_hit_distribution(embed: discord.Embed, stats: dict):
    dist = stats.get("hit_distribution") or {}
    embed.add_field(name="──────── HIT DISTRIBUTION ────────", value="\u200b", inline=False)
    embed.add_field(name="🎯 Head", value=hit_line(dist.get("head") or {}), inline=True)
    embed.add_field(name="🛡️ Torso", value=hit_line(dist.get("torso") or {}), inline=True)
    embed.add_field(name="🦵 Legs", value=hit_line(dist.get("leg") or {}), inline=True)


async def archive_screenshot(
    client: discord.Client,
    image_path: str,
    original_name: str,
    target: discord.Member,
    submitted_by: discord.Member,
):
    if not ARCHIVE_CHANNEL_ID:
        return None

    try:
        channel = client.get_channel(ARCHIVE_CHANNEL_ID)
        if channel is None:
            channel = await client.fetch_channel(ARCHIVE_CHANNEL_ID)

        message = await channel.send(
            content=(
                "📊 **Exalted Era Stats Snapshot**\n"
                f"Player: {target.mention} (`{target.id}`)\n"
                f"Submitted by: {submitted_by.mention}"
            ),
            file=discord.File(image_path, filename=original_name),
        )

        if not message.attachments:
            return None

        attachment = message.attachments[0]
        return {
            "channel_id": message.channel.id,
            "message_id": message.id,
            "image_url": attachment.url,
        }

    except Exception as error:
        print("Archive upload failed:", repr(error))
        return None


class ExaltedEraBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await db.initialize()

        self.tree.clear_commands(guild=None)
        global_synced = await self.tree.sync()
        print(f"Global command cleanup complete: {len(global_synced)} global command(s) remain.")

        guild_synced = await self.tree.sync(guild=GUILD)
        names = ", ".join(f"/{cmd.name}" for cmd in guild_synced)
        print(f"Guild sync complete: {len(guild_synced)} command(s): {names}")

    async def close(self):
        await db.close()
        await super().close()


bot = ExaltedEraBot()


@bot.event
async def on_ready():
    print("=" * 64)
    print(f"Logged in as: {bot.user}")
    print(f"Guild ID: {GUILD_ID}")
    print(f"Database: {db.backend_name}")
    print(f"Stats archive channel: {ARCHIVE_CHANNEL_ID if ARCHIVE_CHANNEL_ID else 'NOT SET'}")
    print("Exalted Era Stats Bot V6 CARD FIX is online.")
    print("=" * 64)


@bot.tree.command(
    name="analyze",
    description="Analyze and save a Valorant Mobile stats screenshot.",
    guild=GUILD,
)
@app_commands.describe(
    screenshot="Upload the player's Valorant Mobile statistics screenshot.",
    player="Player this screenshot belongs to. Defaults to you.",
)
async def analyze(
    interaction: discord.Interaction,
    screenshot: discord.Attachment,
    player: Optional[discord.Member] = None,
):
    await interaction.response.defer(thinking=True)

    target = player or interaction.user
    if not isinstance(target, discord.Member):
        await interaction.followup.send("❌ I could not resolve that Discord member.", ephemeral=True)
        return

    suffix = Path(screenshot.filename).suffix.lower()
    content_type = (screenshot.content_type or "").lower()
    allowed = {".png", ".jpg", ".jpeg", ".webp"}

    if not (content_type.startswith("image/") or suffix in allowed):
        await interaction.followup.send(
            "❌ Upload a PNG, JPG, JPEG, or WEBP screenshot.",
            ephemeral=True,
        )
        return

    if suffix not in allowed:
        suffix = ".png"

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name

        print("")
        print("========== ANALYZE ==========")
        print(f"Requested by: {interaction.user}")
        print(f"Player: {target}")
        print(f"Filename: {screenshot.filename}")

        await screenshot.save(temp_path)

        stats = await asyncio.wait_for(
            asyncio.to_thread(analyze_valorant_image, temp_path, content_type or None),
            timeout=240,
        )

        score, grade = calculate_rating(stats)

        archived = await archive_screenshot(
            bot,
            temp_path,
            screenshot.filename,
            target,
            interaction.user,
        )

        image_url = archived["image_url"] if archived else screenshot.url

        snapshot_id = await db.add_snapshot(
            guild_id=interaction.guild_id,
            user_id=target.id,
            username=target.name,
            display_name=target.display_name,
            stats=stats,
            rating_score=score,
            rating_grade=grade,
            archive_channel_id=archived["channel_id"] if archived else None,
            archive_message_id=archived["message_id"] if archived else None,
            image_url=image_url,
        )

        embed = discord.Embed(
            title="🏆 EXALTED ERA PLAYER ANALYSIS",
            description=f"### {target.display_name}\nSnapshot **#{snapshot_id}** saved.",
            color=discord.Color.gold(),
        )
        add_core_stats(embed, stats)
        add_hit_distribution(embed, stats)
        embed.add_field(
            name="🏅 Exalted Performance",
            value=f"**{grade} — {rating_label(grade)}**\n{score:.1f} / 100",
            inline=False,
        )
        embed.set_footer(text="EXALTED ERA • VALORANT MOBILE")
        await interaction.followup.send(embed=embed)

    except asyncio.TimeoutError:
        await interaction.followup.send(
            "⏱️ Analysis timed out after several Gemini attempts. Try again shortly.",
            ephemeral=True,
        )

    except Exception as error:
        print("========== ANALYZE ERROR ==========")
        print(type(error).__name__)
        print(str(error))
        print("===================================")
        await interaction.followup.send(
            "❌ I couldn't analyze or save this screenshot. Check Railway logs.",
            ephemeral=True,
        )

    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except FileNotFoundError:
                pass
            except Exception as error:
                print("Temporary file cleanup error:", repr(error))


@bot.tree.command(
    name="stats",
    description="Show a player's latest saved Valorant Mobile stats.",
    guild=GUILD,
)
@app_commands.describe(player="Player to view. Defaults to you.")
async def stats_command(interaction: discord.Interaction, player: Optional[discord.Member] = None):
    target = player or interaction.user
    latest = await db.get_latest_snapshot(interaction.guild_id, target.id)

    if not latest:
        await interaction.response.send_message(
            f"📭 No saved analysis for **{target.display_name}** yet. Use `/analyze` first.",
            ephemeral=True,
        )
        return

    current = snapshot_stats(latest)
    embed = discord.Embed(
        title="📊 EXALTED ERA STATS",
        description=f"### {latest['display_name']}",
        color=discord.Color.gold(),
    )
    add_core_stats(embed, current)
    add_hit_distribution(embed, current)
    embed.add_field(
        name="🏅 Exalted Performance",
        value=f"**{latest['rating_grade']} — {rating_label(latest['rating_grade'])}**\n{latest['rating_score']:.1f} / 100",
        inline=False,
    )
    embed.set_footer(text=f"Latest snapshot #{latest['id']}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="progress",
    description="Show a player's latest screenshot and progress.",
    guild=GUILD,
)
@app_commands.describe(player="Player to view. Defaults to you.")
async def progress_command(interaction: discord.Interaction, player: Optional[discord.Member] = None):
    target = player or interaction.user
    snapshots = await db.get_latest_snapshots(interaction.guild_id, target.id, limit=2)

    if not snapshots:
        await interaction.response.send_message(
            f"📭 No saved analysis for **{target.display_name}** yet.",
            ephemeral=True,
        )
        return

    latest = snapshots[0]
    previous = snapshots[1] if len(snapshots) > 1 else None

    embed = discord.Embed(
        title="📈 EXALTED ERA PROGRESS REPORT",
        description=f"### {latest['display_name']}",
        color=discord.Color.gold(),
    )

    if latest.get("image_url"):
        embed.set_image(url=latest["image_url"])

    if previous is None:
        embed.add_field(
            name="📊 Baseline Established",
            value="This is the player's first saved snapshot.\nRun `/analyze` again later to measure progress.",
            inline=False,
        )
    else:
        embed.add_field(
            name="🎮 Matches",
            value=(
                f"{show(previous.get('total_matches'))} → {show(latest.get('total_matches'))}\n"
                f"{delta_text(latest.get('total_matches'), previous.get('total_matches'), digits=0)}"
            ),
            inline=True,
        )
        embed.add_field(
            name="⚔️ Kills",
            value=(
                f"{show(previous.get('kills'))} → {show(latest.get('kills'))}\n"
                f"{delta_text(latest.get('kills'), previous.get('kills'), digits=0)}"
            ),
            inline=True,
        )
        embed.add_field(
            name="🎯 ACS",
            value=(
                f"{show(previous.get('acs'), 1)} → {show(latest.get('acs'), 1)}\n"
                f"{delta_text(latest.get('acs'), previous.get('acs'), digits=1)}"
            ),
            inline=True,
        )
        embed.add_field(
            name="💥 HS%",
            value=(
                f"{show_percent(previous.get('headshot_percentage'))} → {show_percent(latest.get('headshot_percentage'))}\n"
                f"{delta_text(latest.get('headshot_percentage'), previous.get('headshot_percentage'), percent=True, digits=1)}"
            ),
            inline=True,
        )
        embed.add_field(
            name="⚔️ K/D",
            value=(
                f"{show(previous.get('kd_ratio'), 2)} → {show(latest.get('kd_ratio'), 2)}\n"
                f"{delta_text(latest.get('kd_ratio'), previous.get('kd_ratio'), digits=2)}"
            ),
            inline=True,
        )
        embed.add_field(
            name="🔥 First Bloods",
            value=(
                f"{show(previous.get('first_bloods'))} → {show(latest.get('first_bloods'))}\n"
                f"{delta_text(latest.get('first_bloods'), previous.get('first_bloods'), digits=0)}"
            ),
            inline=True,
        )

        rating_delta = latest["rating_score"] - previous["rating_score"]
        marker = "▲ +" if rating_delta > 0 else "▼ " if rating_delta < 0 else "• "
        embed.add_field(
            name="🏅 Performance Rating",
            value=(
                f"{previous['rating_grade']} {previous['rating_score']:.1f} → **{latest['rating_grade']} {latest['rating_score']:.1f}**\n"
                f"{marker}{rating_delta:.1f}"
            ),
            inline=False,
        )

    current = snapshot_stats(latest)
    dist = current.get("hit_distribution") or {}
    embed.add_field(
        name="🎯 Latest Hit Distribution",
        value=(
            f"Head: {hit_line(dist.get('head') or {}).replace(chr(10), ' • ')}\n"
            f"Torso: {hit_line(dist.get('torso') or {}).replace(chr(10), ' • ')}\n"
            f"Legs: {hit_line(dist.get('leg') or {}).replace(chr(10), ' • ')}"
        ),
        inline=False,
    )
    embed.set_footer(text=f"Latest snapshot #{latest['id']}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(
    name="player",
    description="Generate the player card image for a player.",
    guild=GUILD,
)
@app_commands.describe(player="Player profile to view. Defaults to you.")
async def player_command(interaction: discord.Interaction, player: Optional[discord.Member] = None):
    await interaction.response.defer(thinking=True)

    target = player or interaction.user
    latest = await db.get_latest_snapshot(interaction.guild_id, target.id)

    if not latest:
        await interaction.followup.send(
            f"📭 **{target.display_name}** has no saved stats profile yet.",
            ephemeral=True,
        )
        return

    try:
        avatar_bytes = await target.display_avatar.read()

        card_bytes = await asyncio.to_thread(
            render_player_card,
            template_path="player_card_template.png",
            player_name=latest["display_name"],
            rating_score=latest.get("rating_score"),
            rating_grade=latest.get("rating_grade"),
            acs=latest.get("acs"),
            kd_ratio=latest.get("kd_ratio"),
            hs_percent=latest.get("headshot_percentage"),
            kills=latest.get("kills"),
            total_matches=latest.get("total_matches"),
            first_bloods=latest.get("first_bloods"),
            avatar_bytes=avatar_bytes,
        )

        filename = f"{target.display_name.lower().replace(' ', '_')}_player_card.png"
        file = discord.File(io.BytesIO(card_bytes), filename=filename)

        await interaction.followup.send(
            content=f"👤 **{latest['display_name']}** • Exalted Era player card",
            file=file,
        )

    except Exception as error:
        print("========== PLAYER CARD ERROR ==========")
        print(type(error).__name__)
        print(str(error))
        print("=======================================")
        await interaction.followup.send(
            "❌ I couldn't generate the player card image. Check Railway logs.",
            ephemeral=True,
        )


@bot.tree.command(
    name="leaderboard",
    description="Show the Exalted Era performance leaderboard.",
    guild=GUILD,
)
async def leaderboard_command(interaction: discord.Interaction):
    leaders = await db.get_leaderboard(interaction.guild_id, limit=10)

    if not leaders:
        await interaction.response.send_message(
            "📭 No player snapshots have been saved yet.",
            ephemeral=True,
        )
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = []

    for index, row in enumerate(leaders, start=1):
        prefix = medals[index - 1] if index <= 3 else f"`#{index}`"
        lines.append(
            f"{prefix} **{row['display_name']}** — "
            f"**{row['rating_grade']} {row['rating_score']:.1f}** "
            f"• ACS {show(row.get('acs'), 1)} "
            f"• K/D {show(row.get('kd_ratio'), 2)} "
            f"• HS {show_percent(row.get('headshot_percentage'))}"
        )

    embed = discord.Embed(
        title="🏆 EXALTED ERA LEADERBOARD",
        description="\n\n".join(lines),
        color=discord.Color.gold(),
    )
    embed.set_footer(text="Internal Exalted Performance Score • Latest snapshot per player")
    await interaction.response.send_message(embed=embed)


print("Starting Exalted Era Stats Bot V6 CARD FIX...")
bot.run(TOKEN)
