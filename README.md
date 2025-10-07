# Planner Telegram Bot (Windows-friendly)

A minimal Telegram planner bot that remembers a basic user profile and generates a compact, prioritized day-by-day plan using an LLM (OpenAI-compatible). Designed for easy setup on Windows.

## Features
- Onboarding: tell the bot your name, role/study, availability, and goals
- Lightweight memory stored per user (JSON file)
- Command to generate a concise, prioritized plan for upcoming days
- Uses OpenAI-compatible API (works with OpenAI or compatible providers)

## Prerequisites
- Windows 10/11
- Python 3.10+ (`python --version`)
- A Telegram Bot Token (create via @BotFather)
- An OpenAI API key (or compatible provider key)

## Quick Start (5–10 minutes)

### 1) Download the code
Create a folder, e.g. `C:\Users\<YOU>\Desktop\Chatbot`, and place these project files there.

### 2) Create and activate a virtual environment
Open PowerShell in the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If execution policy blocks activation, run PowerShell as Administrator once:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Then activate again.

### 3) Install dependencies
```powershell
pip install -r requirements.txt
```

### 4) Configure environment
Create a `.env` file in the project root with:

```
TELEGRAM_BOT_TOKEN=123456:ABC...         # from @BotFather
OPENAI_API_KEY=sk-...                    # or provider-specific key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini                 # adjust if you like
PLANNING_DAYS=7                          # how many days to plan
MEMORY_PATH=./data/memory.json
```

Notes:
- `OPENAI_BASE_URL` can point to other compatible endpoints if you prefer
- `PLANNING_DAYS` sets planning horizon

### 5) Run the bot
```powershell
python bot.py
```

In Telegram, find your bot and send `/start`.

## Usage
- `/start`: begins onboarding; the bot asks about you and your time availability
- After onboarding, you can send a free-form message like:
  "my name is anna im computer science student ... gimmi a plan for my upcoming days day by day"
- `/plan`: generate a prioritized day-by-day plan using your saved profile and recent goals
- `/profile`: show what the bot remembers about you
- `/reset`: clear your saved memory

## Files
- `bot.py`: entry point and Telegram handlers
- `planner.py`: constructs prompts and calls the LLM
- `memory.py`: simple JSON-based persistence per-user
- `config.py`: loads settings from `.env`
- `requirements.txt`: Python dependencies

## Updating the model/provider
Change `OPENAI_MODEL` or `OPENAI_BASE_URL` in `.env`. If using an OpenAI-compatible provider, keep the schema of the Chat Completions API or update `planner.py` accordingly.

## Troubleshooting
- If the bot won’t start: verify tokens in `.env` are correct and the virtual environment is active
- If messages lag: check your internet and provider status; reduce `PLANNING_DAYS`
- If file permission issues on Windows: run PowerShell as Administrator

## Next steps
- Add task editing and marking complete
- Calendar integration
- Long-term memory and weekly reviews
