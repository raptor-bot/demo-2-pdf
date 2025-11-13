#!/bin/bash

# Demo2PDF Setup Script
# This script sets up the backend environment

set -e  # Exit on error

echo "╔══════════════════════════════════════════════╗"
echo "║       Demo2PDF Setup Script                  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "   Please install Python 3.11+ from https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | grep -oE '[0-9]+\.[0-9]+')
echo "✅ Found Python $PYTHON_VERSION"

# Navigate to backend
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo "✅ Dependencies installed"

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "⚙️  Creating .env configuration..."
    cp .env.example .env
    echo "✅ Created .env file (edit this to add your API keys)"
else
    echo "✅ .env file already exists"
fi

# Create storage directory
mkdir -p storage
echo "✅ Storage directory ready"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║           Setup Complete! ✅                  ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate environment:"
echo "   cd backend && source venv/bin/activate"
echo ""
echo "2. (Optional) Add API keys to backend/.env"
echo ""
echo "3. Start backend:"
echo "   python main.py"
echo ""
echo "4. Load extension in browser:"
echo "   - Chrome: chrome://extensions/"
echo "   - Firefox: about:debugging#/runtime/this-firefox"
echo "   - Load the 'extension' folder"
echo ""
echo "5. Read PROTOTYPE_GUIDE.md for detailed usage"
echo ""
echo "Happy documenting! 📄✨"
echo ""
