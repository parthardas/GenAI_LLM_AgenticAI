from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from instructor import patch
from langchain_groq import ChatGroq
import os
import uvicorn

from agents.guideline_agent import guideline_agent
from agents.account_agent import account_agent
from agents.billing_agent import billing_agent

from dotenv import load_dotenv

load_dotenv()

lc_api_key = os.environ.get('LANGCHAIN_API_KEY')
os.environ["LANGCHAIN_API_URL"] = "https://api.langchain.com/v1/graphql"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "multi-agent-assistant"


# Initialize FastAPI with metadata
app = FastAPI(
    title="Banking Helpdesk API",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared state and models
class AgentState(dict):
    """Shared state for agents"""
    user_input: str = Field(..., description="User's input query")
    user_id: str = Field(..., description="Unique identifier for the user")
    #pass

class UserQuery(BaseModel):
    user_id: str
    user_input: str

class RoutingDecision(BaseModel):
    agent_name: str = Field(..., description="One of: 'guidelines', 'accounts', 'billing'")
    user_query: str = Field(..., description="Rewritten user query for the selected agent")

# Initialize LLM
llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0,
    groq_api_key=os.environ.get("GROQ_API_KEY")
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Main query endpoint
@app.post("/query")
async def query_handler(request: UserQuery):
    try:
        state = {"user_input": request.user_input, "user_id": request.user_id}
        result = graph.invoke(state)
        return {"response": result["response"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return {"error": str(exc)}, 500

def validate_input(state):
    if not state.get("user_input") or not state.get("user_id"):
        return {"status": "error", "message": "Missing required input"}
    return {"status": "success"}

def handle_error(state):
    error = state.get("error", "Unknown error occurred")
    return {"response": f"Error: {error}", "status": "error"}


def route_to_agent(query: str) -> RoutingDecision:
    """Determine which agent should handle the query"""
    # Simple keyword-based routing
    keywords = {
        'guidelines': ['policy', 'kyc', 'rules', 'guidelines'],
        'accounts': ['balance', 'transfer', 'account'],
        'billing': ['pay', 'bill', 'payment']
    }
    
    query_lower = query.lower()
    for agent, words in keywords.items():
        if any(word in query_lower for word in words):
            return RoutingDecision(
            agent_name=agent,
            user_query=query
            )
        # Default to guidelines if no matches found
        return RoutingDecision(
        agent_name='guidelines',  # Default to guidelines
        user_query=query
    )

def orchestrator(state: AgentState) -> dict:
    """Route and process queries through appropriate agents"""
    try:
        # Get routing decision
        decision = route_to_agent(state["user_input"])
        
        # Route to appropriate agent
        if decision.agent_name == "guidelines":
            response = guideline_agent.run(decision.user_query)
        elif decision.agent_name == "accounts":
            response = account_agent.run(decision.user_query)
        elif decision.agent_name == "billing":
            response = billing_agent.run(decision.user_query)
        else:
            raise ValueError(f"Unknown agent: {decision.agent_name}")
            
        return {
            "status": "success",
            "response": response,
            "agent": decision.agent_name
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Build LangGraph with proper flow
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("validate", validate_input)
builder.add_node("orchestrator", orchestrator)
builder.add_node("error_handler", handle_error)

# Configure edges
builder.set_entry_point("validate")

# Add edges with conditional routing
builder.add_conditional_edges(
    "validate",
    lambda x: "orchestrator" if x["status"] == "success" else "error_handler"
)

# Add edge from orchestrator to END to ensure completion
builder.add_edge("orchestrator", END)
builder.add_edge("error_handler", END)

# Configure to return final state
builder.set_finish_point("orchestrator")


# Compile graph with config
graph = builder.compile()

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )