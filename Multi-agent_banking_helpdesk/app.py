# --- File: app.py ---

import streamlit as st
from langgraph.graph import StateGraph, node
from instructor import patch
from langchain_community.chat_models import ChatGroq
from pydantic import BaseModel, Field
import os

from guideline_agent import guideline_agent
from account_agent import account_agent
from billing_agent import billing_agent

st.set_page_config(page_title="Banking Virtual Assistant", layout="centered")
st.title("🌐 Banking Virtual Assistant")

# Shared state across LangGraph
class AgentState(dict):
    pass

# Use LLaMA 3.1 via Groq
llm_raw = ChatGroq(model="llama3-8b-8192", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"))
llm = patch(llm_raw)

# Routing schema using Instructor SDK
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

# Streamlit UI with chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_id = st.text_input("Enter your user ID")
user_input = st.text_area("Ask a banking-related question:")

if st.button("Submit") and user_input:
    state = {"user_input": user_input, "user_id": user_id}
    result = graph.invoke(state)
    st.session_state.chat_history.append((user_input, result["response"]))

st.markdown("### Chat History")
for i, (q, a) in enumerate(reversed(st.session_state.chat_history)):
    st.markdown(f"**You:** {q}")
    st.markdown(f"**Assistant:** {a}")
    st.markdown("---")
