# Exalted Era Stats Bot V6 CARD FIX

This is the **full replacement folder** using your new player-card image template.

## What V6 fixes
- uses the new player-card template image
- `/player` now covers the old sample text/numbers before drawing new values
- the player name now replaces the placeholder cleanly
- the portrait area is larger and rectangular instead of a small circle
- stat values are larger and centered better
- `/analyze`, `/stats`, `/progress`, and `/leaderboard` still work the same

## `/player` uses
- Discord avatar as the photo
- latest saved database stats from `/analyze`

Displayed on the card:
- Rating (numeric performance score)
- ACS
- K/D
- HS%
- Kills
- Matches
- First Bloods
- Grade subtitle under player name

## Replace your repo with these files at the ROOT
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

## Important
Delete the old player-card template and old player_card.py if they are still in your repo before committing.

## Expected startup
```text
Global command cleanup complete: 0 global command(s) remain.
Guild sync complete: 5 command(s): /analyze, /stats, /progress, /player, /leaderboard
Exalted Era Stats Bot V6 CARD FIX is online.
```

## Included template size
- 941 x 1672
