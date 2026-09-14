import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from gemini import analyze_valorant_image

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Exalted Era Stats Bot is online!")

@bot.command()
async def test(ctx):
    await ctx.send("🏆 Exalted Era Stats Bot is online.")

@bot.command()
async def analyze(ctx):
    if not ctx.message.attachments:
        await ctx.send("📸 Please attach a Valorant screenshot.")
        return

    attachment = ctx.message.attachments[0]
    if not attachment.content_type or not attachment.content_type.startswith("image"):
        await ctx.send("❌ Please upload an image.")
        return

    await ctx.send("🔍 Reading your Valorant statistics...")
    image_path = "temp_image.png"
    await attachment.save(image_path)

    try:
        stats = analyze_valorant_image(image_path)

        embed = discord.Embed(
            title="🏆 EXALTED ERA PERFORMANCE",
            description=f"**{stats.get('player_name') or 'Unknown Player'}**",
        )
        embed.add_field(name="⚔️ Kills", value=str(stats.get("kills") or "N/A"), inline=True)
        embed.add_field(name="💀 Deaths", value=str(stats.get("deaths") or "N/A"), inline=True)
        embed.add_field(name="🤝 Assists", value=str(stats.get("assists") or "N/A"), inline=True)
        embed.add_field(name="🎯 ACS", value=str(stats.get("acs") or "N/A"), inline=True)
        embed.add_field(name="💥 HS%", value=str(stats.get("headshot_percentage") or "N/A"), inline=True)
        embed.add_field(name="🏁 Result", value=str(stats.get("result") or "N/A").upper(), inline=True)
        embed.set_footer(text="EXALTED ERA • THE ERA IS HERE.")
        await ctx.send(embed=embed)

    except Exception as e:
        print(e)
        await ctx.send("❌ I couldn't read the screenshot. Please try a clearer Valorant scoreboard.")

    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

bot.run(TOKEN)
