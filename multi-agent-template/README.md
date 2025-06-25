# README.md
# Multi-Agent Arithmetic System

A sophisticated multi-agent system built with LangGraph, FastAPI, and React that performs mathematical calculations using specialized sub-agents.

## Features

- **Meta-Agent Coordination**: Intelligent routing and orchestration of sub-agents
- **Specialized Sub-Agents**: Dedicated agents for addition, subtraction, multiplication, and division
- **React Prompting**: Advanced reasoning capabilities using React (Reasoning + Acting) methodology
- **Conversation Memory**: Client-side conversation history management
- **Real-time Processing**: Fast and efficient calculation processing
- **Dockerized Deployment**: Complete containerization for easy deployment

## Architecture

### Backend (FastAPI + LangGraph)
- **Meta-Agent**: Orchestrates the entire calculation process using LangGraph StateGraph
- **Sub-Agents**: Four specialized agents for arithmetic operations
- **LLM Service**: Groq-powered reasoning and natural language processing
- **Structured I/O**: JSON-based communication using Instructor SDK

### Frontend (React)
- **Chat Interface**: User-friendly conversation interface
- **History Management**: Local storage of conversation history
- **Real-time Status**: Connection status and processing indicators
- **Responsive Design**: Modern, accessible UI with Tailwind CSS

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Groq API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd multi-agent-arithmetic
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development Setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Usage Examples

- "What's 5 + 3?"
- "Calculate (10 - 4) * 2"
- "Divide 20 by 4"
- "What's 15 + 7 - 3 * 2?"

## System Design

### LangGraph StateGraph Structure
```
Entry Point: reasoning
    ↓
reasoning → execute_operations → generate_response → END
```

### Agent Coordination
1. **Reasoning Node**: Meta-agent analyzes user input using React prompting
2. **Execution Node**: Sub-agents perform arithmetic operations in correct order
3. **Response Node**: Natural language response generation

### Key Features
- **Maximum Call Limits**: Prevents infinite loops and excessive processing
- **Order of Operations**: Proper mathematical precedence (PEMDAS/BODMAS)
- **Error Handling**: Graceful handling of invalid inputs and edge cases
- **Structured Output**: Consistent JSON-based agent communication

## Configuration

### LLM Settings
- **Model**: mixtral-8x7b-32768 (Groq)
- **Temperature**: 0.3 (balanced reasoning and creativity)
- **Max Agent Calls**: 5 (prevents excessive processing)

### Future Extensibility
The system is designed to be easily extended with:
- **Memory Systems**: Long-term and short-term memory storage
- **Database Integration**: Persistent storage capabilities
- **Advanced Agents**: Web search, document RAG, API calls, CRUD operations
- **Multi-modal Support**: Image and document processing

## API Endpoints

### POST /chat
Process a mathematical query
```json
{
  "message": "What's 5 + 3?",
  "conversation_id": "optional"
}
```

### GET /health
Service health check

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License

## Troubleshooting

### Common Issues

1. **Groq API Key Issues**
   - Ensure your GROQ_API_KEY is set correctly in .env
   - Check API key validity and rate limits

2. **Docker Issues**
   - Ensure Docker and Docker Compose are installed
   - Check port availability (3000, 8000, 6379)

3. **Connection Issues**
   - Verify backend is running on port 8000
   - Check CORS configuration for frontend-backend communication

### Debug Mode
Set environment variable `DEBUG=true` for detailed logging.

## Performance Considerations

- **Agent Call Limits**: Configurable maximum to prevent runaway processes
- **Response Caching**: Redis integration for future performance optimization
- **Lightweight Operations**: Efficient arithmetic operations with minimal overhead
- **Error Recovery**: Graceful degradation and error handling