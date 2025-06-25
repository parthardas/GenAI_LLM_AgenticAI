// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
      },
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      }
    },
  },
  plugins: [],
}

// frontend/postcss.config.js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}

// frontend/index.html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/calculator.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Multi-Agent Calculator</title>
    <meta name="description" content="Advanced multi-agent arithmetic system powered by AI" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>

// backend/app/__init__.py
"""
Multi-Agent Arithmetic System

A sophisticated system using LangGraph for coordinating specialized arithmetic agents.
"""

__version__ = "1.0.0"
__author__ = "Multi-Agent Systems Team"

# backend/app/models/__init__.py
"""
Data models and schemas for the multi-agent system.
"""

from .schemas import (
    OperationType,
    ArithmeticInput,
    ArithmeticOutput,
    AgentStep,
    ReasoningPlan,
    GraphState,
    ChatRequest,
    ChatResponse
)

__all__ = [
    "OperationType",
    "ArithmeticInput", 
    "ArithmeticOutput",
    "AgentStep",
    "ReasoningPlan",
    "GraphState",
    "ChatRequest",
    "ChatResponse"
]

# backend/app/agents/__init__.py
"""
Agent implementations for the multi-agent arithmetic system.
"""

from .meta_agent import MetaAgent
from .arithmetic_agents import ArithmeticAgents

__all__ = ["MetaAgent", "ArithmeticAgents"]

# backend/app/services/__init__.py
"""
Service layer for external integrations and utilities.
"""

from .llm_service import LLMService

__all__ = ["LLMService"]

# Makefile
.PHONY: help build run stop clean test lint format

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker containers
	docker-compose build

run: ## Run the application
	docker-compose up -d

stop: ## Stop the application
	docker-compose down

clean: ## Clean up containers and volumes
	docker-compose down -v
	docker system prune -f

logs: ## Show application logs
	docker-compose logs -f

restart: ## Restart the application
	make stop
	make run

test-backend: ## Run backend tests
	cd backend && python -m pytest

lint-backend: ## Lint backend code
	cd backend && python -m flake8 app/
	cd backend && python -m black --check app/

format-backend: ## Format backend code
	cd backend && python -m black app/
	cd backend && python -m isort app/

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint

dev-backend: ## Run backend in development mode
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run frontend in development mode
	cd frontend && npm run dev

install-backend: ## Install backend dependencies
	cd backend && pip install -r requirements.txt

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

# Scripts for easy setup
# setup.sh
#!/bin/bash

echo "Setting up Multi-Agent Arithmetic System..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file and add your GROQ_API_KEY"
    echo "You can get a free API key from: https://console.groq.com/"
    read -p "Press enter after you've added your API key to .env..."
fi

# Install frontend dependencies for development
echo "Installing frontend dependencies..."
cd frontend && npm install
cd ..

# Install backend dependencies for development
echo "Setting up Python virtual environment..."
cd backend
python -m venv venv
source venv/bin/activate 2>/dev/null || venv\Scripts\activate
pip install -r requirements.txt
cd ..

echo "Setup complete!"
echo ""
echo "To run the application:"
echo "  Development mode: make dev-backend (in one terminal) && make dev-frontend (in another)"
echo "  Production mode: make build && make run"
echo ""
echo "The application will be available at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"

# Extended backend requirements for production
# backend/requirements-prod.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
instructor==0.4.5
groq==0.4.1
langgraph==0.0.62
langchain==0.1.0
langchain-core==0.1.0
python-multipart==0.0.6
httpx==0.25.2
python-dotenv==1.0.0
redis==5.0.1
gunicorn==21.2.0
prometheus-client==0.19.0
structlog==23.2.0

# Development requirements
# backend/requirements-dev.txt
-r requirements.txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1
pre-commit==3.5.0

# Test configuration
# backend/pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html

# backend/tests/test_agents.py
import pytest
from app.agents.arithmetic_agents import ArithmeticAgents
from app.models.schemas import ArithmeticInput, OperationType

class TestArithmeticAgents:
    
    def test_addition_agent(self):
        input_data = ArithmeticInput(
            operation=OperationType.ADDITION,
            operands=[5.0, 3.0, 2.0]
        )
        result = ArithmeticAgents.addition_agent(input_data)
        
        assert result.success is True
        assert result.result == 10.0
        assert result.operation == OperationType.ADDITION
    
    def test_subtraction_agent(self):
        input_data = ArithmeticInput(
            operation=OperationType.SUBTRACTION,
            operands=[10.0, 3.0, 2.0]
        )
        result = ArithmeticAgents.subtraction_agent(input_data)
        
        assert result.success is True
        assert result.result == 5.0
    
    def test_multiplication_agent(self):
        input_data = ArithmeticInput(
            operation=OperationType.MULTIPLICATION,
            operands=[4.0, 3.0, 2.0]
        )
        result = ArithmeticAgents.multiplication_agent(input_data)
        
        assert result.success is True
        assert result.result == 24.0
    
    def test_division_agent(self):
        input_data = ArithmeticInput(
            operation=OperationType.DIVISION,
            operands=[20.0, 4.0]
        )
        result = ArithmeticAgents.division_agent(input_data)
        
        assert result.success is True
        assert result.result == 5.0
    
    def test_division_by_zero(self):
        input_data = ArithmeticInput(
            operation=OperationType.DIVISION,
            operands=[10.0, 0.0]
        )
        result = ArithmeticAgents.division_agent(input_data)
        
        assert result.success is False
        assert "Division by zero" in result.error_message