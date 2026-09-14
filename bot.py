import os
import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


class ExaltedEraBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


bot = ExaltedEraBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Exalted Era Stats Bot is online!")


@bot.tree.command(
    name="test",
    description="Check if the Exalted Era Stats Bot is working."
)
async def test(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🏆 **EXALTED ERA STATS BOT**\n"
        "Bot is online and working.\n\n"
        "THE ERA IS HERE."
    )


bot.run(TOKEN)
