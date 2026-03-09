
#!/bin/bash

# Sentinel Electron Dev Quick Start Script
# This script helps you quickly start the Electron development environment

echo "🕷️  Sentinel - Electron Development Startup"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the frontend directory"
    echo "   cd frontend && ./dev-start.sh"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Check if backend env exists
if [ ! -d "../backend/env" ]; then
    echo "⚠️  Warning: Python virtual environment not found"
    echo "   Please set up the backend first:"
    echo "   cd ../backend && python3 -m venv env && source env/bin/activate && pip install -r requirements.txt"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if backend .env exists
if [ ! -f "../backend/.env" ]; then
    echo "⚠️  Warning: Backend .env file not found"
    echo "   Please create ../backend/.env with your API keys"
    echo ""
fi

# Check if Metasploit is installed
if ! command -v msfconsole &> /dev/null; then
    echo "⚠️  Warning: Metasploit Framework not found"
    echo "   Some features may not work without Metasploit"
    echo "   Install: brew install metasploit (macOS)"
    echo ""
fi

# Start the application
echo "🚀 Starting Sentinel in development mode..."
echo "   - Next.js dev server will start on http://localhost:3000"
echo "   - Python backend will start on http://localhost:8000"
echo "   - Electron window will open automatically"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

npm run electron-dev
