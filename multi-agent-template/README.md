# Multi-Agent Arithmetic System

A sophisticated multi-agent system built with LangGraph, FastAPI, and React that performs mathematical calculations using specialized sub-agents. This project demonstrates advanced AI agent coordination, conversation management, and real-time processing capabilities.

## 🚀 Features

- **Meta-Agent Coordination**: Intelligent routing and orchestration of sub-agents using LangGraph StateGraph
- **Specialized Sub-Agents**: Dedicated agents for addition, subtraction, multiplication, and division
- **React Prompting**: Advanced reasoning capabilities using React (Reasoning + Acting) methodology
- **Conversation Memory**: Client-side conversation history management with persistent storage
- **Real-time Processing**: Fast and efficient calculation processing with status indicators
- **Dockerized Deployment**: Complete containerization for easy deployment and scaling
- **Error Handling**: Robust error handling and graceful degradation
- **Responsive UI**: Modern React interface with Tailwind CSS

## 🏗️ Architecture

### Backend (FastAPI + LangGraph)
- **Meta-Agent**: Orchestrates the entire calculation process using LangGraph StateGraph
- **Sub-Agents**: Four specialized agents for arithmetic operations with proper PEMDAS/BODMAS support
- **LLM Service**: Groq-powered reasoning and natural language processing
- **Structured I/O**: JSON-based communication using Instructor SDK
- **State Management**: Comprehensive state tracking through LangGraph

### Frontend (React)
- **Chat Interface**: User-friendly conversation interface with message history
- **History Management**: Local storage of conversation history with persistence
- **Real-time Status**: Connection status and processing indicators
- **Responsive Design**: Modern, accessible UI with Tailwind CSS
- **Component Architecture**: Modular React components for maintainability

### System Flow
```
User Input → Meta-Agent (Reasoning) → Sub-Agents (Execution) → Response Generation → User Interface
```

## ⚡ Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.8+ (for local development)
- Groq API key

### 🐳 Docker Deployment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd multi-agent-template
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

### 🛠️ Development Setup

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 💡 Usage Examples

The system can handle various mathematical expressions:

- **Simple Operations**: "What's 5 + 3?"
- **Complex Expressions**: "Calculate (10 - 4) * 2"
- **Division**: "Divide 20 by 4"
- **Order of Operations**: "What's 15 + 7 - 3 * 2?"
- **Natural Language**: "Add five and three, then multiply by two"

## 🔧 System Design

### LangGraph StateGraph Structure
```
Entry Point: reasoning
    ↓
reasoning → execute_operations → generate_response → END
```

### Agent Coordination Flow
1. **Reasoning Node**: Meta-agent analyzes user input using React prompting
2. **Execution Node**: Sub-agents perform arithmetic operations in correct order
3. **Response Node**: Natural language response generation with explanation

### Key Technical Features
- **Maximum Call Limits**: Prevents infinite loops and excessive processing (configurable)
- **Order of Operations**: Proper mathematical precedence (PEMDAS/BODMAS)
- **Error Handling**: Graceful handling of invalid inputs and edge cases
- **Structured Output**: Consistent JSON-based agent communication
- **State Persistence**: Conversation state management across interactions

## ⚙️ Configuration

### Environment Variables
```env
GROQ_API_KEY=your_groq_api_key_here
DEBUG=false
MAX_AGENT_CALLS=5
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### LLM Settings
- **Model**: mixtral-8x7b-32768 (Groq)
- **Temperature**: 0.3 (balanced reasoning and creativity)
- **Max Agent Calls**: 5 (prevents excessive processing)
- **Context Window**: Optimized for mathematical reasoning

### Future Extensibility
The system is designed for easy extension with:
- **Memory Systems**: Long-term and short-term memory storage
- **Database Integration**: PostgreSQL/MongoDB support
- **Advanced Agents**: Web search, document RAG, API calls, CRUD operations
- **Multi-modal Support**: Image and document processing
- **Additional Math Operations**: Scientific calculations, statistics, calculus

## 📡 API Endpoints

### POST /chat
Process a mathematical query
```json
{
  "message": "What's 5 + 3?",
  "conversation_id": "optional-uuid"
}
```

**Response:**
```json
{
  "response": "5 + 3 equals 8",
  "calculation_steps": ["5", "+", "3", "=", "8"],
  "conversation_id": "uuid",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### GET /health
Service health check

### GET /status
System status and metrics

## 🧪 Testing

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --build
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use ESLint and Prettier for JavaScript/React code
- Write comprehensive tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Common Issues

1. **Groq API Key Issues**
   - Ensure your GROQ_API_KEY is set correctly in .env
   - Check API key validity and rate limits
   - Verify API key has access to mixtral-8x7b-32768 model

2. **Docker Issues**
   - Ensure Docker and Docker Compose are installed
   - Check port availability (3000, 8000)
   - Clear Docker cache: `docker system prune -a`

3. **Connection Issues**
   - Verify backend is running on port 8000
   - Check CORS configuration for frontend-backend communication
   - Ensure firewall allows connections on required ports

4. **Performance Issues**
   - Check agent call limits in configuration
   - Monitor memory usage during complex calculations
   - Review LangGraph state management logs

### Debug Mode
Set environment variable `DEBUG=true` for detailed logging and state inspection.

### Logging
- Backend logs: Check Docker logs or console output
- Frontend logs: Browser developer console
- LangGraph traces: Available in debug mode

## 🚀 Performance Considerations

- **Agent Call Limits**: Configurable maximum to prevent runaway processes
- **Response Caching**: Redis integration ready for performance optimization
- **Lightweight Operations**: Efficient arithmetic operations with minimal overhead
- **Error Recovery**: Graceful degradation and error handling
- **Resource Management**: Memory and CPU optimization for agent coordination

## 🔮 Roadmap

- [ ] Database integration for conversation persistence
- [ ] Advanced mathematical functions (trigonometry, calculus)
- [ ] Multi-user support with authentication
- [ ] Web search integration for mathematical references
- [ ] Export calculations to different formats (PDF, CSV)
- [ ] Mobile application support
- [ ] Advanced analytics and usage metrics

---

**Built with ❤️ using LangGraph, FastAPI, and React**