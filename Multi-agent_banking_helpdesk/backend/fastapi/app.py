# --- File: app.py ---

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.graph import StateGraph, node
from instructor import patch
from langchain_community.chat_models import ChatGroq
import os

from guideline_agent import guideline_agent
from account_agent import account_agent
from billing_agent import billing_agent

# FastAPI setup
app = FastAPI()

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared state across LangGraph
class AgentState(dict):
    pass

# Use LLaMA 3.1 via Groq
llm_raw = ChatGroq(model="llama3-8b-8192", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"))
llm = patch(llm_raw)

# Routing schema using Instructor SDK
from pydantic import Field

class RoutingDecision(BaseModel):
    agent_name: str = Field(..., description="One of: 'guidelines', 'accounts', 'billing'")
    user_query: str = Field(..., description="Rewritten user query for the selected agent")

@node
def orchestrator(state):
    user_input = state["user_input"]
    user_id = state["user_id"]

    system_prompt = """
    You are a routing assistant for a banking app. Based on the user's query, select one of the following agents:
    - 'guidelines': for policy or document questions
    - 'accounts': for checking account balances
    - 'billing': for adding billers or making payments

    Provide your decision in JSON using the schema.
    """

    decision: RoutingDecision = llm.invoke(
        system_prompt + f"\nUser input: {user_input}",
        schema=RoutingDecision
    )

    if decision.agent_name == "guidelines":
        result = guideline_agent.invoke({"input": decision.user_query})
    elif decision.agent_name == "accounts":
        result = account_agent.invoke({"input": decision.user_query, "user_id": user_id})
    elif decision.agent_name == "billing":
        result = billing_agent.invoke({"input": decision.user_query, "user_id": user_id})
    else:
        result = {"output": "I'm not sure how to help with that."}

    return {"response": result["output"]}

# Build LangGraph
builder = StateGraph(AgentState)
builder.add_node("orchestrator", orchestrator)
builder.set_entry_point("orchestrator")
graph = builder.compile()

# FastAPI endpoint
class UserQuery(BaseModel):
    user_id: str
    user_input: str

@app.post("/query")
async def query_handler(request: UserQuery):
    state = {"user_input": request.user_input, "user_id": request.user_id}
    result = graph.invoke(state)
    return {"response": result["response"]}
