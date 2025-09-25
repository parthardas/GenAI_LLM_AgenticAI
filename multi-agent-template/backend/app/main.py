from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from agents.graph import healthcare_graph
from models.schemas import GraphState
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Healthcare Multi-Agent System",
    description="An intelligent healthcare assistant with automatic tool-based routing",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    routing_info: Optional[Dict[str, Any]] = None
    agent_used: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint using automatic tool-based routing.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Create initial state as a dictionary (LangGraph expects dict, not Pydantic model)
        initial_state = {
            "user_input": request.message,
            "session_id": session_id,
            "response": "",
            "route_to": "",
            "done": False,
            "routing_message": None,
            "medical_context": {},
            "agent_data": {},
            "conversation_history": [],
            "error": None
        }
        
        logger.info(f"Processing message for session {session_id}: {request.message}")
        
        # Run the graph with automatic tool-based routing
        graph_result = healthcare_graph.invoke(initial_state)
        
        logger.info(f"Graph result type: {type(graph_result)}")
        logger.info(f"Graph result keys: {list(graph_result.keys()) if hasattr(graph_result, 'keys') else 'No keys'}")
        
        # Extract values from the AddableValuesDict
        response = graph_result.get("response", "")
        medical_context = graph_result.get("medical_context", {})
        routing_message = graph_result.get("routing_message", None)
        agent_data = graph_result.get("agent_data", {})
        
        # Extract response text
        if isinstance(response, dict):
            response_text = response.get("content", str(response))
            agent_used = response.get("agent", "unknown")
        elif isinstance(response, str):
            response_text = response
            agent_used = medical_context.get("selected_agent", "router")
        else:
            response_text = str(response)
            agent_used = "unknown"
        
        # Handle empty responses
        if not response_text or response_text.strip() == "":
            response_text = "I'm here to help! Could you please tell me more about what you need assistance with?"
        
        # Prepare routing info
        routing_info = {
            "routing_method": medical_context.get("routing_method", "automatic"),
            "confidence": medical_context.get("routing_confidence", "high"),
            "urgency": medical_context.get("urgency_level", "medium"),
            "routing_message": routing_message,
            "selected_agent": medical_context.get("selected_agent", agent_used)
        }
        
        # Determine agent used
        if agent_used == "unknown":
            agent_used = medical_context.get("selected_agent", "router")
        
        logger.info(f"Successfully processed message. Agent: {agent_used}, Method: {routing_info['routing_method']}")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            routing_info=routing_info,
            agent_used=agent_used
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return a user-friendly error response instead of raising HTTPException
        return ChatResponse(
            response="I apologize, but I'm experiencing some technical difficulties. Please try again in a moment.",
            session_id=session_id or str(uuid.uuid4()),
            routing_info={"routing_method": "error_fallback", "confidence": "low", "urgency": "medium", "routing_message": None, "selected_agent": "error_handler"},
            agent_used="error_handler"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "routing_method": "automatic_tool_selection"
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Healthcare Multi-Agent System with Automatic Tool-Based Routing",
        "version": "2.0.0",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "docs": "/docs"
        },
        "features": [
            "Automatic LLM tool selection for routing",
            "Intelligent healthcare triage",
            "Multi-agent specialization",
            "Emergency detection",
            "Session management"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)