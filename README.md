# Exalted Era Stats Bot V4 CLEAN

This version fixes duplicate Discord slash commands.

## Why you were seeing two `/analyze` commands

Your GitHub repository still had the older bot at the repository root.
The newer folder had not actually replaced the root project.

V4 does two command sync operations on startup:

1. Deletes old GLOBAL commands for this bot application.
2. Syncs exactly these five GUILD commands to Exalted Era:

- `/analyze`
- `/stats`
- `/progress`
- `/player`
- `/leaderboard`

## IMPORTANT upload instructions

The ZIP has the project files directly at its root.

In GitHub, your repository root should show:

- bot.py
- gemini.py
- database.py
- ratings.py
- requirements.txt
- Procfile
- README.md
- .gitignore

Do NOT leave the old bot.py beside a nested `exalted-era-stats-v4-clean/` folder.

## Railway variables

Required:

- `DISCORD_TOKEN`
- `GEMINI_API_KEY`
- `GUILD_ID=1545457876552655008`

Recommended:

- `DATABASE_URL`
- `STATS_ARCHIVE_CHANNEL_ID`

## Expected Railway startup log

```text
Global command cleanup complete: 0 global command(s) remain.
Guild sync complete: 5 command(s): /analyze, /stats, /progress, /player, /leaderboard
Exalted Era Stats Bot V4 CLEAN is online.
```

If Discord still shows two `/analyze` commands after this exact log:
- press Ctrl+R / restart Discord;
- confirm there is not a second Discord bot/application installed in the server with its own `/analyze`;
- confirm only one Railway service is running this bot token.

## `/progress`

`/progress` shows the latest screenshot saved for the selected player and compares it with the previous snapshot.
