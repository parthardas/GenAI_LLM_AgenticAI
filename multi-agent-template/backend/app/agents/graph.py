from langgraph.graph import StateGraph, END
from .meta_agent import router_node
from models.schemas import GraphState
#from .agent_a import agent_a
from .agent_a import agent_a_node
from .agent_b import agent_b_node
#from .agent_c import agent_c
from .agent_c import agent_c_node

# Wrapper functions for LangChain agents
# def agent_a_node(state): return {"user_input": state["user_input"], "response": agent_a.invoke({"input": state["user_input"]})}
# def agent_b_node(state): return {"user_input": state["user_input"], "response": agent_b.invoke({"input": state["user_input"]})}
# def agent_c_node(state): return {"user_input": state["user_input"], "response": agent_c.invoke({"input": state["user_input"]})}
#def agent_a_node(state): return {"user_input": state.user_input, "response": agent_a.invoke({"input": state.user_input})}

# def agent_b_node(state): 
#     import logging
#     #from langchain.output_parsers import PydanticOutputParser
#     # Configure logging
#     logging.basicConfig(level=logging.INFO)
#     logger = logging.getLogger(__name__)

#     logger.info(f"In agent_b_node: state: {state}")
#     return {"user_input": state.user_input, "response": agent_b.invoke({"input": state.user_input})}

#def agent_c_node(state): return {"user_input": state.user_input, "response": agent_c.invoke({"input": state.user_input})}


# Create the graph
#graph = StateGraph(dict)
graph = StateGraph(GraphState)

# Add nodes
graph.add_node("router", router_node)
graph.add_node("agent_a", agent_a_node)
graph.add_node("agent_b", agent_b_node)
graph.add_node("agent_c", agent_c_node)

# Entry point
graph.set_entry_point("router")

# Conditional routing from router → agents
# graph.add_conditional_edges(
#     "router",
#     path="router_node",
#     path_map={
#         "agent_a": "agent_a",
#         "agent_b": "agent_b",
#         "agent_c": "agent_c"
#     }
# )

graph.add_conditional_edges(
    "router",
    lambda state: state.route_to,
    {
        "agent_a": "agent_a",
        "agent_b": "agent_b",
        "agent_c": "agent_c",
        "END": END
    }
)

# After each agent, return to the router
graph.add_edge("agent_a", "router")
graph.add_edge("agent_b", "router")
graph.add_edge("agent_c", "router")

# Add exit condition: router can terminate if a flag is present
graph.set_finish_point("router")

# Compile
compiled_graph = graph.compile()