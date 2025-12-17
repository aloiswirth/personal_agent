# Quick Start Guide

Get the LangChain Agent Demo running in 5 minutes!

## Step 1: Install System Requirements

On Debian/Ubuntu:
```bash
sudo apt install python3-venv
```

## Step 2: Run Setup Script

```bash
./setup.sh
```

This will:
- ✅ Create a virtual environment
- ✅ Install all Python dependencies
- ✅ Create a `.env` file template

## Step 3: Add Your OpenAI API Key

1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Edit the `.env` file:
   ```bash
   nano .env  # or use your favorite editor
   ```
3. Replace `your_openai_api_key_here` with your actual API key

## Step 4: Run the Demo

```bash
source .venv/bin/activate
marimo edit agent_demo.py
```

Your browser will open at `http://localhost:2718` with the interactive demo!

## Step 5: Try It Out

In the chat interface, try these prompts:

1. **"Read my email"** - The agent will read a fake birthday party invitation
2. **"Create a calendar event for the birthday party"** - The agent will extract details and create an event
3. **"Show me your decision-making process"** - See how the agent planned its actions
4. **"What tools do you have?"** - View all available tools

## What You'll See

The demo showcases:

- 🧠 **Planning**: The agent decides which tools to use
- 💭 **Memory**: Conversation context is maintained
- 🔧 **Tools**: Five custom tools for email, calendar, and introspection
- 📊 **State Tracking**: Real-time display of agent activity

## Troubleshooting

### Setup script fails
Make sure you have `python3-venv` installed:
```bash
sudo apt install python3-venv
```

### "OpenAI API key not found"
Edit `.env` and add your API key:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### Port 2718 already in use
Marimo will automatically use a different port. Check the terminal output for the actual URL.

## Next Steps

- Read the full [README.md](README.md) for detailed information
- Check [docs/agent_demo.md](docs/agent_demo.md) for technical documentation
- Run tests: `pytest test/test_agent_demo.py -v`
- Customize the agent by editing `agent_demo.py`

## Need Help?

- [LangChain Documentation](https://python.langchain.com/)
- [Marimo Documentation](https://docs.marimo.io/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

Happy exploring! 🚀
