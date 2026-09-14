# Exalted Era Stats Bot V5 PLAYER CARD

This version keeps the working V4 system and upgrades `/player` to generate a **PNG player card** using your supplied Exalted Era template.

## New `/player`
`/player` now:
1. loads the member's latest saved stats
2. loads `player_card_template.png`
3. uses the member's **Discord avatar** as the photo
4. inserts:
   - Player Name
   - Rating
   - ACS
   - K/D
   - HS%
   - Kills
   - Matches
   - First Bloods
5. sends the finished PNG card in Discord

## Included template
This ZIP already includes:
- `player_card_template.png`

Detected template size:
- `1024 x 1536`

## Commands
- `/analyze`
- `/stats`
- `/progress`
- `/player`
- `/leaderboard`

## Important
- `/player` uses the player's **Discord avatar** automatically.
- You still need `/analyze` first so the bot has stats saved in the database.
- `/progress` still shows the latest saved screenshot for that player.

## Files at repo root
- `bot.py`
- `gemini.py`
- `database.py`
- `ratings.py`
- `player_card.py`
- `player_card_template.png`
- `requirements.txt`
- `Procfile`
- `.env.example`
- `.gitignore`
- `README.md`

## Railway variables
Required:
- `DISCORD_TOKEN`
- `GEMINI_API_KEY`
- `GUILD_ID=1545457876552655008`

Recommended:
- `DATABASE_URL`
- `STATS_ARCHIVE_CHANNEL_ID`

## Expected startup
```text
Global command cleanup complete: 0 global command(s) remain.
Guild sync complete: 5 command(s): /analyze, /stats, /progress, /player, /leaderboard
Exalted Era Stats Bot V5 PLAYER CARD is online.
```
