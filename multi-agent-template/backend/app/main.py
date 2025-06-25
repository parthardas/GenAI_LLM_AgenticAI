# backend/app/main.py
from fastapi import FastAPI, HTTPException
from langgraph.graph import StateGraph, END
from fastapi.middleware.cors import CORSMiddleware
from .models.schemas import ChatRequest, ChatResponse
#from app.agents.meta_agent import MetaAgent
from .agents.graph import compiled_graph
from .models.schemas import GraphState
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

        #result = meta_agent.process_query(
        result = compiled_graph.invoke(initial_state, config={"recursion_limit": 5})
        #{"response": result["response"]}
        logger.info(f"Result response: {result.response}")
        #logger.info(f"Result object type: {type(result)}")
        #logger.info(f"Result object dir: {dir(result)}")
        #logger.info(f"Result object dict: {getattr(result, '__dict__', str(result))}")
        
        # Convert GraphState to dict for ChatResponse, or access attributes directly
        return ChatResponse(
            user_input=result.user_input,
            agent_call_count=result.agent_call_count,
            conversation_history=result.conversation_history
        )
        
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
