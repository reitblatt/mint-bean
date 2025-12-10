#!/bin/bash

# MintBean Setup Script
# This script helps you get started with local development

set -e

echo "🫘 MintBean Setup Script"
echo "========================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env with your configuration before continuing"
    echo ""
    read -p "Press enter when you've updated .env..."
fi

# Create data directory
echo ""
echo "📁 Creating data directory..."
mkdir -p data
echo "✅ Data directory created"

# Backend setup
echo ""
echo "🐍 Setting up backend..."
cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Backend dependencies installed"

# Create database
echo "Creating database..."
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
echo "✅ Database created"

cd ..

# Frontend setup
echo ""
echo "⚛️  Setting up frontend..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
    echo "✅ Frontend dependencies installed"
else
    echo "✅ Node modules already installed"
fi

cd ..

# Pre-commit hooks
echo ""
echo "🪝 Setting up pre-commit hooks..."
pip install pre-commit
pre-commit install
echo "✅ Pre-commit hooks installed"

# Summary
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo ""
echo "Option 1: Run with Docker (Recommended)"
echo "  docker-compose up"
echo ""
echo "Option 2: Run locally"
echo "  Terminal 1 (Backend):"
echo "    cd backend"
echo "    source venv/bin/activate"
echo "    uvicorn app.main:app --reload"
echo ""
echo "  Terminal 2 (Frontend):"
echo "    cd frontend"
echo "    npm run dev"
echo ""
echo "Then visit:"
echo "  - Frontend: http://localhost:5173"
echo "  - API Docs: http://localhost:8000/api/docs"
echo ""
echo "Happy coding! 🚀"
