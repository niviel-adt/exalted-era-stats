# Exalted Era Stats Bot - Slash Command Fix

This folder fixes the `/analyze` `CommandNotFound` issue in the Exalted Era Stats Bot.

## What changed

The old `setup_hook()` ran:

```python
self.tree.clear_commands(guild=GUILD)
self.tree.copy_global_to(guild=GUILD)
```

Those lines removed the guild-only `/test` and `/analyze` commands from the bot's local tree before syncing.

The fixed version only runs:

```python
synced = await self.tree.sync(guild=GUILD)
```

## Railway environment variables

Set these in Railway Variables:

- `DISCORD_TOKEN`
- `GEMINI_API_KEY`

Do not put either secret in GitHub.

## Discord server

Guild ID:

`1545457876552655008`

The bot registers these commands directly to that guild:

- `/test`
- `/analyze`

## Railway start command

Use:

```text
python bot.py
```

## Expected startup log

```text
Synced 2 slash command(s) to Exalted Era.
Logged in as <your bot>
Exalted Era Stats Bot is online!
```

## After deploying

1. Wait for Railway to finish deploying.
2. Check the Railway logs for `Synced 2 slash command(s)`.
3. Refresh Discord with `Ctrl + R`.
4. Run `/test`.
5. Run `/analyze` and upload a Valorant Mobile statistics screenshot.
