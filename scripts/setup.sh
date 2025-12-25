#!/bin/bash

# Mathvidya Setup Script
# This script helps set up the development environment

set -e  # Exit on error

echo "🚀 Mathvidya Setup Script"
echo "=========================="
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version found"

# Check Node.js version
echo "📋 Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    exit 1
fi
node_version=$(node --version | grep -oP '\d+' | head -1)
if [ "$node_version" -lt 18 ]; then
    echo "❌ Node.js 18 or higher is required"
    exit 1
fi
echo "✅ Node.js $(node --version) found"

# Check PostgreSQL
echo "📋 Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL client not found. Please install PostgreSQL 14+"
else
    echo "✅ PostgreSQL found"
fi

# Check Redis
echo "📋 Checking Redis..."
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis client not found. Please install Redis 6+"
else
    echo "✅ Redis found"
fi

echo ""
echo "🔧 Setting up backend..."
echo "========================"

# Setup backend
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Python dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

cd ..

echo ""
echo "🎨 Setting up frontend..."
echo "========================"

# Setup frontend
cd frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
    echo "✅ Node.js dependencies installed"
else
    echo "✅ Node.js dependencies already installed"
fi

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Configure backend/.env with your database credentials"
echo "2. Create PostgreSQL database: createdb mathvidya"
echo "3. Start backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "4. Start frontend: cd frontend && npm start"
echo "5. Access API docs: http://localhost:8000/api/docs"
echo "6. Access frontend: http://localhost:3000"
echo ""
echo "Or use Docker Compose:"
echo "docker-compose up --build"
echo ""
echo "Happy coding! 🚀"
