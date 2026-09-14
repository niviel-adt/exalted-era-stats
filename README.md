# Exalted Era Stats Bot

Discord bot for reading Valorant screenshots with Gemini and preparing player performance statistics.

## Commands

- `!test` — checks whether the bot is online.
- `!analyze` + attached image — reads a Valorant screenshot.

## Local setup

1. Install Python 3.11+.
2. Open a terminal in this folder.
3. Run:

```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env`.
5. Put your Discord bot token and Gemini API key in `.env`.
6. Run:

```bash
python bot.py
```

Do not commit `.env` to GitHub.
