# LangChain Agent Demo

A demonstration of LangChain agent capabilities using Marimo for an interactive notebook experience.

## Features

This demo showcases:

- 🤖 **Agent Planning & Decision Making**: Watch the agent decide which tools to use and in what order
- 💭 **Conversation Memory**: The agent remembers previous interactions
- 📧 **Real Email Reading**: Connect to GMX IMAP server to read actual emails from alois_wirth@gmx.de
- 📅 **GMX Calendar Integration**: Create calendar events directly in your GMX calendar via CalDAV (with local fallback)
- 🔍 **Introspection Tools**: View the agent's decisions, memory, and available tools

## Quick Start

### Prerequisites

- Python 3.8 or higher
- `python3-venv` package (on Debian/Ubuntu: `sudo apt install python3-venv`)
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- GMX email account credentials (for real email reading)

### Installation

#### Option 1: Automated Setup (Recommended)

Run the setup script:
```bash
./setup.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Create a `.env` file from the template

Then edit `.env` and add your OpenAI API key.

#### Option 2: Manual Setup

1. Install python3-venv (if not already installed):
   ```bash
   sudo apt install python3-venv  # On Debian/Ubuntu
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key and GMX password
   ```

5. Test the GMX connection (optional):
   ```bash
   python test_gmx_connection.py
   ```

### Running the Demo

```bash
marimo edit agent_demo.py
```

This will open an interactive notebook in your browser at `http://localhost:2718`.

## Usage Examples

Try these prompts in the chat interface:

1. **Read recent emails**: `"Read my email"` (reads last 10 emails by default)
2. **Read specific number**: `"Read my last 5 emails"`
3. **Create a calendar event**: `"Create a calendar event for [event details]"`
4. **View agent decisions**: `"Show me your decision-making process"`
5. **Check available tools**: `"What tools do you have?"`
6. **View conversation history**: `"Show me the conversation history"`
7. **Combined operation**: `"Read my email and create a calendar event if there's an invitation"`

## Project Structure

```
.
├── agent_demo.py           # Main Marimo notebook with agent implementation
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── README.md              # This file
├── docs/
│   └── agent_demo.md      # Detailed documentation
└── test/
    └── test_agent_demo.py # Unit tests
```

## How It Works

### Agent Architecture

The demo uses LangChain's OpenAI Functions Agent with:

- **LLM**: GPT-4o-mini (configurable)
- **Memory**: ConversationBufferMemory for maintaining context
- **Tools**: Five custom tools built with LangChain's BaseTool

### Custom Tools

1. **read_email**: Connects to GMX IMAP server and fetches real emails from alois_wirth@gmx.de
   - Supports configurable count (default: 10 emails)
   - Decodes email headers and body content
   - Handles multipart MIME messages
   - Truncates long emails for display
2. **create_calendar_event**: Creates calendar events in GMX calendar via CalDAV
   - Attempts to sync with GMX calendar first
   - Falls back to local storage if CalDAV fails
   - Flexible date/time parsing
   - Automatic timezone handling (Europe/Berlin)
   - Skips read-only calendars
3. **show_decisions**: Displays the agent's decision-making process
4. **show_memory**: Shows conversation history
5. **show_tools**: Lists all available tools

### State Tracking

The agent maintains state in a global dictionary:
- `decisions`: List of actions and reasoning
- `calendar_events`: Created calendar entries
- `emails_read`: Email read operations
- `memory_history`: Conversation turns with timestamps

## Testing

Run the test suite:

```bash
# Run all tests
pytest test/test_agent_demo.py -v

# Run with coverage
pytest test/test_agent_demo.py -v --cov --cov-branch --cov-report=html

# View coverage report
open htmlcov/index.html  # On macOS
# or
xdg-open htmlcov/index.html  # On Linux
```

## Documentation

Detailed documentation is available in `docs/agent_demo.md`, including:
- Complete API reference
- Usage examples
- Technical architecture
- Assumptions and limitations

## Configuration

### Environment Variables

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `OPENAI_MODEL` (optional): Model to use (default: `gpt-4o-mini`)
- `GMX_PW` (required): Your GMX email password for IMAP access
- `GMX_KALENDER` (required): Your GMX app-specific password for CalDAV calendar access
  - Generate this in GMX account settings under Security > App Passwords

### Customization

You can customize the demo by:
- Changing the email account (modify GMX_EMAIL, GMX_IMAP_SERVER, GMX_IMAP_PORT, GMX_CALDAV_URL in `agent_demo.py`)
- Adjusting the default number of emails to read
- Changing the calendar timezone (default: Europe/Berlin)
- Modifying event duration (default: 1 hour)
- Adding new tools by extending the `BaseTool` class
- Changing the agent's system prompt
- Adjusting the LLM temperature and other parameters

## Limitations

- Email reading is read-only (no sending capability)
- Email body truncated to 500 characters for display
- No support for email attachments
- HTML emails converted to plain text or skipped
- Calendar events may fall back to local storage if CalDAV sync fails
- GMX CalDAV may have authorization issues (known limitation)
- Calendar events default to 1-hour duration
- Requires OpenAI API (not compatible with local models without modification)
- Maximum 10 agent iterations per query
- Requires active internet connection for email and calendar access

## Troubleshooting

### "No module named 'marimo'"
Make sure you've activated the virtual environment and installed dependencies:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "OpenAI API key not found"
Ensure you've created a `.env` file with your API key and GMX password:
```bash
cp .env.example .env
# Edit .env and add:
# OPENAI_API_KEY=sk-your-key-here
# GMX_PW=your-gmx-password
```

### "Error reading emails"
- Check your GMX credentials in the `.env` file
- Verify your internet connection
- Ensure GMX IMAP access is enabled for your account
- Run `python test_gmx_connection.py` to diagnose connection issues

### "Could not sync to GMX calendar"
- This is a known issue with GMX CalDAV authorization (returns 403 Forbidden)
- Events will be stored locally instead
- The system now uses an app-specific password (GMX_KALENDER) for calendar access
- Despite successful authentication, GMX CalDAV may still block event creation
- Run `python test_gmx_caldav.py` to diagnose CalDAV connection issues
- Calendar events will automatically fall back to local storage

### "Rate limit exceeded"
You may need to wait a moment or upgrade your OpenAI API plan.

## License

This is a demonstration project for educational purposes.

## Contributing

This is a demo project, but feel free to fork and extend it for your own use cases!

## Learn More

- [LangChain Documentation](https://python.langchain.com/)
- [Marimo Documentation](https://docs.marimo.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
