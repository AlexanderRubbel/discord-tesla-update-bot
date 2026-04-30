# Tesla Software Update Bot

A Discord bot that automatically tracks new Tesla software versions from [notateslaapp.com](https://www.notateslaapp.com/software-updates/) and posts updates to a Discord channel.

> **Disclaimer:** This bot is **not affiliated with, endorsed by, or connected to Tesla, Inc.** in any way. Software version information is provided as-is with no guarantees of accuracy or completeness.

## Features

- Automatically checks for new Tesla software versions every 15 minutes
- Posts a rich embed with release notes when a new version is detected
- Optional HW3/HW4 compatibility poll (currently disabled, easy to re-enable)
- Slash commands for manual control (`/check_now`, `/add_version`, `/summary`, `/set_channel`)
- SQLite database to track known versions
- Docker support with auto-restart

## Prerequisites

- Python 3.11+ (or Docker)
- A Discord Bot Token ([create one here](https://discord.com/developers/applications))

## Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** and give it a name
3. Go to **Bot** in the sidebar and click **Reset Token** to get your bot token
4. Go to **OAuth2** in the sidebar
5. Under **Scopes**, select `bot` and `applications.commands`
6. Under **Bot Permissions**, select:
   - View Channels
   - Send Messages
   - Embed Links
   - Read Message History
   - Create Polls
7. Copy the generated invite URL and open it in your browser to add the bot to your server
8. Note the **Channel ID** where you want updates posted (right-click the channel in Discord > Copy Channel ID; enable Developer Mode in Discord settings if you don't see this option)

## Installation

### Option A: Docker (recommended)

```bash
git clone https://github.com/AlexanderRubbel/discord-tesla-update-bot.git
cd discord-tesla-update-bot

# Create your config
cp .env.example .env
# Edit .env with your bot token and channel ID

# Build and run
docker compose up -d
```

The container is configured with `restart: always`, so it will automatically start on boot.

### Option B: Run directly with Python

```bash
git clone https://github.com/AlexanderRubbel/discord-tesla-update-bot.git
cd discord-tesla-update-bot

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt

# Create your config
cp .env.example .env
# Edit .env with your bot token and channel ID

python bot.py
```

## Configuration

Create a `.env` file (or copy from `.env.example`):

```env
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
CHECK_INTERVAL_MINUTES=15
RSS_FEED_URL=https://www.notateslaapp.com/rss
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | - | Your Discord bot token |
| `DISCORD_CHANNEL_ID` | Yes | - | Channel ID for update posts |
| `CHECK_INTERVAL_MINUTES` | No | `15` | How often to check for new versions |
| `RSS_FEED_URL` | No | `https://www.notateslaapp.com/rss` | Data source URL (not currently used for detection, kept for future use) |

## Slash Commands

| Command | Permission | Description |
|---------|------------|-------------|
| `/check_now` | Admin | Force an immediate check for new versions |
| `/add_version <version>` | Admin | Manually add a version and post it |
| `/summary [version]` | Everyone | Show poll results for a version |
| `/set_channel #channel` | Admin | Change the update channel |

## Project Structure

```
discord-tesla-update-bot/
  bot.py                  # Entry point
  requirements.txt        # Python dependencies
  Dockerfile              # Docker image definition
  docker-compose.yml      # Docker Compose config
  .env                    # Your config (not in git)
  cogs/
    version_tracker.py    # Background task: checks for new versions
    commands.py           # Slash commands
  services/
    rss_checker.py        # Scrapes notateslaapp.com for version links
    scraper.py            # Extracts release notes from version pages
    database.py           # SQLite persistence
  models/
    version.py            # TeslaVersion dataclass
  utils/
    embed_builder.py      # Builds Discord embeds
    poll_builder.py       # Builds Discord polls (currently disabled)
  data/
    bot.db                # SQLite database (created at runtime)
```

## Re-enabling Polls

The HW3/HW4 compatibility poll is currently commented out. To re-enable it, uncomment the poll lines in:

- `cogs/version_tracker.py` (lines in `_post_version`)
- `cogs/commands.py` (lines in `add_version`)

Search for `# poll disabled for now` to find the relevant sections.

## Data Source

Version data is scraped from the [notateslaapp.com software updates page](https://www.notateslaapp.com/software-updates/). The bot checks every 15 minutes for new version links and compares them against its local database. On first run, it silently registers all existing versions and only posts the newest one to avoid spamming the channel.

## License

MIT
