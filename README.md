# Exalted Era Stats Bot V7 CLEAN CARD

## Rating validation

All six rating inputs must be readable, finite, nonnegative numbers. Match
count must be positive, counts must be whole numbers, HS% cannot exceed 100,
and first bloods cannot exceed kills. Invalid or incomplete uploads are rejected
before archiving or saving, so they cannot replace a player's profile with an
artificially low grade. Numeric strings are normalized before saving.

The original score weights and S/A/B/C/D thresholds are unchanged. Identical
validated stats produce identical scores. Gemini uses temperature zero to reduce
extraction variation, but OCR can still misread valid-looking numbers; this does
not guarantee identical extraction of every screenshot. Existing saved snapshots
are not rewritten. The performance grade is not the player's in-game rank.

Run regression checks with `python -m unittest -v test_ratings`.

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

