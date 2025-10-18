#!/bin/bash

# Incident Commander Dashboard Build Script

echo "🚀 Building Incident Commander Dashboard..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ to continue."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node -v)"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Type check
echo "🔍 Running type check..."
npm run type-check

if [ $? -ne 0 ]; then
    echo "❌ Type check failed"
    exit 1
fi

# Build the project
echo "🏗️ Building Next.js application..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Dashboard build completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "   • Run 'npm run dev' to start development server"
echo "   • Run 'npm run start' to start production server"
echo "   • Dashboard will be available at http://localhost:3000"
echo ""
echo "🔗 Integration:"
echo "   • Backend API should be running on http://localhost:8000"
echo "   • WebSocket endpoint: ws://localhost:8000/ws"