# --- File 2: app.py ---

import streamlit as st
from langgraph.graph import StateGraph, node
from agents import AGENTS

st.set_page_config(page_title="Banking Assistant", layout="centered")
st.title("Banking Virtual Assistant")

# Shared state: user_id and input message
class AgentState(dict):
    pass

# Load agents
guideline_agent = AGENTS["guidelines"]()
db_agent = AGENTS["accounts"]()
billing_agent = AGENTS["billing"]()

@node
def orchestrator(state):
    user_input = state["user_input"]
    user_id = state["user_id"]

    # Simple keyword routing (can be made more intelligent)
    if "policy" in user_input or "guideline" in user_input:
        result = guideline_agent.invoke({"input": user_input})
        return {"response": result["output"]}

    elif "balance" in user_input or "account" in user_input:
        result = db_agent.invoke({"input": f"get account balance for user_id={user_id}"})
        return {"response": result["output"]}

    elif "pay" in user_input or "biller" in user_input:
        result = billing_agent.invoke({"input": f"pay Vodafone 100.0 for user_id={user_id}"})
        return {"response": result["output"]}

    else:
        return {"response": "I'm not sure how to help with that."}

# Build the graph
builder = StateGraph(AgentState)
builder.add_node("orchestrator", orchestrator)
builder.set_entry_point("orchestrator")
graph = builder.compile()

# Streamlit UI
user_id = st.text_input("Enter your user ID")
user_input = st.text_area("Ask a banking-related question:")

if st.button("Submit") and user_input:
    state = {"user_input": user_input, "user_id": user_id}
    result = graph.invoke(state)
    st.markdown("### Response:")
    st.success(result["response"])
