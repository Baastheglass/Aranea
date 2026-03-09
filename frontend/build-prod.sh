#!/bin/bash

# Sentinel Electron Build Script
# Builds production-ready desktop applications

echo "🕷️  Sentinel - Production Build"
echo "=============================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the frontend directory"
    exit 1
fi

# Check dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install || exit 1
fi

# Check backend
if [ ! -d "../backend/env" ]; then
    echo "❌ Error: Backend virtual environment not found"
    echo "   Set it up first: cd ../backend && python3 -m venv env && pip install -r requirements.txt"
    exit 1
fi

echo "🔨 Building Next.js static export..."
npm run export
if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo ""
echo "📦 Select build platform:"
echo "  1) macOS"
echo "  2) Windows"
echo "  3) Linux"
echo "  4) All platforms"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "🍎 Building for macOS..."
        npm run dist-mac
        ;;
    2)
        echo "🪟 Building for Windows..."
        npm run dist-win
        ;;
    3)
        echo "🐧 Building for Linux..."
        npm run dist-linux
        ;;
    4)
        echo "🌍 Building for all platforms..."
        npm run dist
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build complete!"
    echo "📁 Output directory: $(pwd)/dist/"
    echo ""
    ls -lh dist/ | grep -E '\.(dmg|exe|AppImage|deb)$'
else
    echo ""
    echo "❌ Build failed. Check errors above."
    exit 1
fi
