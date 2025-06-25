# agent_b.py

from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langchain.agents import tool
#from instructor import Instructor as InstructorOpenAI
from langchain_groq import ChatGroq
from app.models.schemas import GraphState
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import logging
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

lc_api_key = os.environ.get('LANGCHAIN_API_KEY')
os.environ["LANGCHAIN_API_URL"] = "https://api.langchain.com/v1/graphql"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "multi-agent-template"

llm_raw = ChatGroq(model="llama-3.1-8b-instant", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"))
#llm = patch(llm_raw)
llm = llm_raw

# from openai import OpenAI

# openai_client = OpenAI(
#     api_key=os.getenv("GROQ_API_KEY"),
#     base_url="https://api.groq.com/openai/v1"
# )
# #llm = InstructorOpenAI(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
# llm = InstructorOpenAI(client=openai_client, create=openai_client.chat.completions.create)


# Tools
class InputSchema(BaseModel):
    data: str = Field(...)

class OutputSchema(BaseModel):
    result: str

#@tool(args_schema=InputSchema)
def tool_one(tool_input: InputSchema) -> OutputSchema:
    """
    Processes the input data using tool_one and returns the result wrapped in an OutputSchema.

    Args:
        data (str): The input string to be processed.

    Returns:
        OutputSchema: An object containing the processed result.
    """
    logger.info("Hi! I am agent B Tool 1")
    return OutputSchema(result=f"Handled by Agent B tool_one: {tool_input.data}")

#@tool(args_schema=InputSchema)
def tool_two(tool_input: InputSchema) -> OutputSchema:
    """
    Processes the input data using tool_two and returns the result wrapped in an OutputSchema.

    Args:
        data (str): The input string to be processed.

    Returns:
        OutputSchema: An object containing the processed result.
    """
    logger.info("Hi! I am agent B Tool 2")
    return OutputSchema(result=f"Handled by Agent B tool_two: {tool_input.data}")

# Agent initialized with tools, LLM decides which one to invoke
# agent_b = initialize_agent(
#     tools=[tool_one, tool_two],
#     llm=llm,
#     agent_type="structured-chat-zero-shot-react-description",
#     verbose=True
# )

# LangGraph node for agent_b
def agent_b_node(state):
    """
    LangGraph node for agent_b.
    Routes to tool_one or tool_two based on keywords in user_input.
    """

    logger.info(f"inside agent_b_node: {state}")
    user_input = state.user_input if hasattr(state, "user_input") else state["user_input"]
    if "tool 1" in user_input.lower():
        tool_one_input = InputSchema(data=user_input)
        tool_result = tool_one(tool_input=tool_one_input)
        response = tool_result.result
    elif "tool 2" in user_input.lower():
        tool_result = tool_two(tool_input=InputSchema(data=user_input))
        response = tool_result.result
    else:
        response = "Please specify 'tool 1' or 'tool 2' in your input for agent B."
    
    #return the state object by adding a done key set to True
    logger.info(f"agent_b_node response: {state}")
    if hasattr(state, "done"):
        state.done = True
    else:
        state["done"] = True
    # Return the response in the expected format
    logger.info(f"agent_b_node returning: {state}")
    if isinstance(state, GraphState):
        state.response = response
        state.user_input = user_input
        return state
    # If state is a dict, return a new dict with the response
    logger.info(f"agent_b_node returning as dict: {state}")
    if isinstance(state, dict):
        state["response"] = response
        state["user_input"] = user_input
        return state
    # return {
    #     "user_input": user_input,
    #     "response": response,
    #     "done": True
    # }


