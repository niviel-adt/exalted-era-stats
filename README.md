# Exalted Era Stats Bot V7 CLEAN CARD

This version fixes the player-card output where the original template's
sample values and placeholder name were still visible behind the real data.

## Main fixes

- removes only the baked-in `PLAYER NAME` placeholder
- removes only the baked-in sample stat values
- keeps all labels, icons, borders, logo and background artwork
- fills the real portrait frame with the Discord avatar
- removes the huge black runtime cover boxes
- writes the actual player name cleanly
- makes all stat values large and centered
- keeps `/analyze`, `/stats`, `/progress`, `/player`, and `/leaderboard`

## Important changed files

- `player_card.py`
- `player_card_template.png`

For the safest deployment, replace the whole repo with this ZIP.
