# Personal Agent - Usage Guide

## Quick Start

### 1. Setup (First Time Only)

```bash
# Navigate to project directory
cd /home/alois/Dokumente/development/github/personal_agent

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -e .
```

### 2. Configure Environment

Ensure your `.env` file contains the required credentials:

```bash
# Copy template if needed
cp .env.example .env

# Edit with your credentials
nano .env
```

Required variables:
```
OPENAI_API_KEY=sk-your-key-here
GMX_PW=your-gmx-password
GMX_KALENDER=your-gmx-calendar-app-password
```

### 3. Run the Agent

```bash
# Option 1: Direct Python
python -m src.cli

# Option 2: Using Make
make run
```

## Using the Agent

### Available Commands

The Communication Agent understands natural language. Here are example prompts:

#### Email Operations
| Prompt | Action |
|--------|--------|
| `Read my emails` | Reads last 10 emails |
| `Read my last 5 emails` | Reads last 5 emails |
| `Read my last 20 emails and categorize them` | Reads and categorizes emails |
| `Summarize my unread emails` | Summarizes email content |

#### Calendar Operations
| Prompt | Action |
|--------|--------|
| `Show my calendar` | Lists upcoming events (7 days) |
| `What's on my calendar next week?` | Shows next week's events |
| `Create a meeting with John tomorrow at 3pm` | Creates calendar event |
| `Schedule dinner at Restaurant XYZ on Friday at 7pm` | Creates event with location |

#### Combined Operations
| Prompt | Action |
|--------|--------|
| `Read my emails and create calendar events for any invitations` | Reads emails, creates events |
| `Check if I have a meeting scheduled for Wednesday` | Checks calendar |

### Example Session

```
🤖 Personal Agent - Communication Module
==================================================

Capabilities:
- 📧 Email reading
- 📅 Calendar management

Type 'quit' or 'exit' to stop.
==================================================

👤 You: Read my last 5 emails

🤖 Agent: 📧 Reading last 5 emails from alois_wirth@gmx.de
...

👤 You: Create a calendar event for dinner with Maria on Saturday at 7pm at Pizzeria Roma

🤖 Agent: ✅ Calendar event created successfully!

Event: Dinner with Maria
Date: Saturday
Time: 7:00 PM
Location: Pizzeria Roma

🔗 Synced to your calendar.

👤 You: quit

👋 Goodbye!
```

## Running Options

### From VSCode Terminal
1. Press `` Ctrl+` `` to open terminal
2. Run: `source .venv/bin/activate`
3. Run: `python -m src.cli`

### From External Terminal
```bash
cd /home/alois/Dokumente/development/github/personal_agent
source .venv/bin/activate
python -m src.cli
```

### Using Make Commands
```bash
make run          # Run the agent
make run-legacy   # Run old demo (lg_agent_demo.py)
make test         # Run tests
make help         # Show all commands
```

## Troubleshooting

### "ModuleNotFoundError"
```bash
# Reinstall dependencies
uv pip install -e .
```

### "OPENAI_API_KEY not set"
```bash
# Check your .env file
cat .env | grep OPENAI
```

### "Error reading emails"
- Verify GMX credentials in `.env`
- Check internet connection
- Run: `python test_gmx_connection.py`

### "Calendar sync failed"
- Events are stored locally as fallback
- Check GMX_KALENDER app password
- Run: `python test_gmx_caldav.py`

## Project Structure

```
personal_agent/
├── src/
│   ├── cli.py                    # Main entry point
│   ├── config/settings.py        # Configuration
│   ├── agents/
│   │   ├── base.py               # Base agent class
│   │   └── communication/        # Email & Calendar agent
│   └── storage/                  # Storage abstraction
├── .env                          # Your credentials (not in git)
├── Makefile                      # Common commands
└── pyproject.toml                # Dependencies
```

## Next Steps

See [ARCHITECTURE.md](ARCHITECTURE.md) for:
- Adding new agents (Finance, Media)
- Storage backend configuration
- Deployment options
