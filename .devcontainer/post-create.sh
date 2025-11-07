#!/bin/bash

# Post-create script - runs after devcontainer is created
set -e

echo "🚀 Setting up AI Video Clipper development environment..."

# Copy .env.example if .env doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Remember to update .env with your actual credentials!"
fi

# Backend setup
echo "🐍 Setting up Python backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e ".[dev]" 2>/dev/null || echo "No editable install configured"

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until pg_isready -h localhost -p 5432 -U postgres; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Run database migrations
echo "🗄️  Running database migrations..."
alembic upgrade head || echo "⚠️  No migrations found or migration failed. Run 'alembic revision --autogenerate -m \"Initial migration\"' to create your first migration."

cd ..

# Frontend setup
echo "⚛️  Setting up Next.js frontend..."
cd frontend

# Install Node dependencies
echo "Installing Node.js dependencies..."
npm install

cd ..

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p backend/uploads
mkdir -p backend/temp
mkdir -p backend/logs

# Git setup
echo "🔧 Configuring git..."
git config --global --add safe.directory /workspace

# Display success message
echo ""
echo "✨ Development environment setup complete!"
echo ""
echo "📚 Quick start commands:"
echo "  Backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  Worker:   cd backend && source venv/bin/activate && arq app.worker.WorkerSettings"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "  Or use docker-compose:"
echo "  docker-compose up backend worker frontend"
echo ""
echo "🔗 Services:"
echo "  Frontend:   http://localhost:3000"
echo "  Backend:    http://localhost:8000"
echo "  API Docs:   http://localhost:8000/docs"
echo "  PostgreSQL: localhost:5432"
echo "  Redis:      localhost:6379"
echo ""
echo "📖 Read .claude/SETUP-GUIDE.md for more information"
echo ""
