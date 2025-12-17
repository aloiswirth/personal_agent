#!/bin/bash
# Setup script for LangChain Agent Demo

set -e

echo "🚀 Setting up LangChain Agent Demo..."

# Check if python3-venv is available
if ! python3 -m venv --help &> /dev/null; then
    echo "⚠️  python3-venv is not installed."
    echo "Please install it with: sudo apt install python3-venv"
    echo "Then run this script again."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate and install dependencies
echo "📥 Installing dependencies..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY"
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OpenAI API key"
echo "2. Activate the virtual environment: source .venv/bin/activate"
echo "3. Run the demo: marimo edit agent_demo.py"
