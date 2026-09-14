# Exalted Era Valorant Mobile Stats Bot

Clean replacement project for the Exalted Era Discord stats bot.

## What `/analyze` returns

Only these 7 categories:

1. Kills
2. ACS
3. HS%
4. Total Matches
5. K/D
6. First Bloods
7. Head / Torso / Leg hit distribution (count + percentage)

The AI is explicitly told to ignore the left-side radar/polygon chart and read the printed numerical panel on the right.

## Railway variables

Add these in **Railway > Variables**:

- `DISCORD_TOKEN`
- `GEMINI_API_KEY`

Optional:

- `GEMINI_MODEL` — defaults to `gemini-3.6-flash`

Do **not** put your Discord token or Gemini API key in GitHub.

## Replace your current repository

1. Download and extract this folder.
2. Delete the old project files from your GitHub repository.
3. Upload the contents of this folder to the repository root.
4. Commit the changes.
5. Let Railway redeploy.
6. In Railway, verify the two required variables above still exist.
7. Refresh Discord after Railway finishes deploying.

## Expected Railway startup log

```text
Starting Exalted Era Stats Bot...
Synced 1 slash command(s) to Exalted Era: /analyze
Logged in as: ...
Exalted Era Stats Bot is online!
```

This version intentionally registers only `/analyze`. Syncing the current guild command tree should remove stale old guild commands such as `/test`.

## Screenshot support

- PNG
- JPG / JPEG
- WEBP

The command is:

```text
/analyze
```

Attach the Valorant Mobile player-statistics screenshot when Discord asks for the screenshot.
