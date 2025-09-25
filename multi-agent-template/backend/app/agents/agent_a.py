from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

lc_api_key = os.environ.get('LANGCHAIN_API_KEY')
os.environ["LANGCHAIN_API_URL"] = "https://api.langchain.com/v1/graphql"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "multi-agent-template"

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"))

# Define tools using @tool decorator for automatic function calling
@tool
def tool_one(data: str) -> str:
    """
    Processes simple text data and returns a basic response.
    Use this tool for general text processing, simple questions, or basic data manipulation.
    
    Args:
        data: The input string to be processed
        
    Returns:
        str: The processed result
    """
    logger.info("Hi! I am agent A Tool 1")
    return f"Handled by Agent A tool_one: {data}"

@tool
def tool_two(data: str) -> str:
    """
    Processes complex text data with advanced operations.
    Use this tool for complex analysis, detailed processing, or advanced data manipulation.
    
    Args:
        data: The input string to be processed with complex logic
        
    Returns:
        str: The advanced processed result
    """
    logger.info("Hi! I am agent A Tool 2")
    return f"Handled by Agent A tool_two: {data}"

# Create the agent with tools - this handles automatic tool selection and calling
tools = [tool_one, tool_two]
agent = create_react_agent(llm, tools)

def agent_a_node(state: dict) -> dict:
    """
    Processes the given state for agent A using automatic LLM tool selection and calling.
    
    Args:
        state (dict): The current state dictionary containing user input
        
    Returns:
        dict: The updated state dictionary with response and completion status
    """
    
    logger.info(f"inside agent_a_node: {state}")
    user_input = state.get("user_input", "")
    
    try:
        # Create messages for the agent
        messages = [HumanMessage(content=user_input)]
        
        # Let the agent automatically select and call the appropriate tool
        result = agent.invoke({"messages": messages})
        
        # Extract the final response from the agent
        response = result["messages"][-1].content
        
        logger.info(f"Agent A automatic tool selection completed successfully")
        
    except Exception as e:
        logger.error(f"Error in agent_a_node: {e}")
        response = f"An error occurred while processing your request: {str(e)}"
    
    # Update state
    state["done"] = True
    state["route_to"] = "END"
    state["response"] = response
    
    logger.info(f"agent_a_node returning: {state}")
    return state