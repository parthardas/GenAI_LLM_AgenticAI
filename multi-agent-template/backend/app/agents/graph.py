from langgraph.graph import StateGraph, END
from typing import Dict, Any
from agents.meta_agent import router_node
from agents.agent_a import agent_a_node
from agents.agent_b import agent_b_node
from agents.agent_c import agent_c_node
import logging

logger = logging.getLogger(__name__)

def create_graph():
    """
    Creates the healthcare agent graph with automatic tool-based routing.
    
    The graph flow:
    1. START → router_node (automatic tool selection for routing)
    2. router_node → agent_a/agent_b/agent_c (based on tool selection)
    3. agents → END
    """
    
    # Create the state graph with Dict type
    graph = StateGraph(Dict[str, Any])
    
    # Add all nodes
    graph.add_node("router", router_node)
    graph.add_node("agent_a", agent_a_node)  # Health & Symptoms
    graph.add_node("agent_b", agent_b_node)  # Appointments
    graph.add_node("agent_c", agent_c_node)  # Insurance
    
    # Set the entry point
    graph.set_entry_point("router")
    
    # Define routing logic based on state["route_to"]
    def route_after_router(state: Dict[str, Any]) -> str:
        """Determine the next node after routing"""
        
        route = state.get('route_to', 'END')
        
        logger.info(f"Routing decision: {route}")
        
        # Map routes to actual node names
        route_mapping = {
            'agent_a': 'agent_a',
            'agent_b': 'agent_b', 
            'agent_c': 'agent_c',
            'END': END,
            '': END,  # Handle empty strings
            None: END  # Handle None values
        }
        
        result = route_mapping.get(route, END)
        logger.info(f"Mapped route '{route}' to '{result}'")
        return result
    
    # Add conditional edges from router
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "agent_a": "agent_a",
            "agent_b": "agent_b",
            "agent_c": "agent_c",
            END: END
        }
    )
    
    # Add edges from agents to END
    graph.add_edge("agent_a", END)
    graph.add_edge("agent_b", END)
    graph.add_edge("agent_c", END)
    
    # Compile the graph
    compiled_graph = graph.compile()
    
    logger.info("Healthcare agent graph created successfully with automatic tool-based routing")
    
    return compiled_graph

# Create the graph instance
healthcare_graph = create_graph()