# backend/app/main.py
from unittest import result
from fastapi import FastAPI, HTTPException
from langgraph.graph import StateGraph, END
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import ChatRequest, ChatResponse
#from app.agents.meta_agent import MetaAgent
from agents.graph import compiled_graph
from models.schemas import GraphState
import logging
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Agent Distributed Template", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Meta Agent
#meta_agent = MetaAgent()

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    try:
        logger.info(f"Processing chat request: {request.message}")
        
        # Initialize state
        initial_state = GraphState(
            user_input=request.message,
            agent_call_count=0,
            conversation_history=[]
        )

        logger.info(f"initial state: {initial_state}")

        # compiled_graph.invoke() returns a dictionary, not a GraphState object
        result_dict = compiled_graph.invoke(initial_state, config={"recursion_limit": 5})

        logger.info(f"Result response: {result_dict.get('response', 'No response')}")

        # Extract values from the dictionary
        response_value = result_dict.get('response')
        medical_context = result_dict.get('medical_context', {})
        routing_message = result_dict.get('routing_message', '')
        route_to = result_dict.get('route_to')

        # Extract the content from the response
        if isinstance(response_value, dict):
            # For dictionary responses (from conversation agent)
            response_content = response_value.get('content', str(response_value))
            response_data = {
                "response": response_content,
                "medical_context": medical_context,
                "routing_info": {
                    "routing_message": routing_message,
                    "route_to": route_to,
                    "agent_used": response_value.get('agent') if isinstance(response_value, dict) else None
                }
            }
        else:
            # For string responses (from other agents)
            response_data = {
                "response": response_value or "No response generated",
                "medical_context": medical_context,
                "routing_info": {
                    "routing_message": routing_message,
                    "route_to": route_to
                }
            }

        return ChatResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "multi-agent-template"}

if __name__ == "__main__":
    uvicorn.run(
        app=app, 
        host="0.0.0.0", 
        port=8000,
        #reload=True,
        log_level="debug"
    )
