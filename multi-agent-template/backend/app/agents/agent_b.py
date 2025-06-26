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
def agent_b_node(state:GraphState) -> GraphState:
    """
    Processes the given state for agent B, determines which tool to invoke based on user input,
    and updates the state with the response and completion status.
    Args:
        state (GraphState or dict): The current state object, which must contain a 'user_input' attribute or key.
    Returns:
        GraphState or dict: The updated state object with the following modifications:
            - 'response': The result from the selected tool or an instruction message.
            - 'user_input': The original user input.
            - 'done': Boolean flag set to True indicating completion.
    Behavior:
        - If 'tool 1' is mentioned in the user input, invokes tool_one with the input.
        - If 'tool 2' is mentioned, invokes tool_two with the input.
        - Otherwise, prompts the user to specify a tool.
        - Handles both attribute-style and dict-style state objects.
        - Logs key steps for debugging.
    """


    logger.info(f"inside agent_b_node: {state}")
    #user_input = state.user_input if hasattr(state, "user_input") else state["user_input"]
    user_input = state.user_input
    if "tool 1" in user_input.lower():
        tool_one_input = InputSchema(data=user_input)
        tool_result = tool_one(tool_input=tool_one_input)
        response = tool_result.result
    elif "tool 2" in user_input.lower():
        tool_result = tool_two(tool_input=InputSchema(data=user_input))
        response = tool_result.result
    else:
        response = "Please specify 'tool 1' or 'tool 2' in your input for agent B."
    


    state.done = True
    state.route_to = "END"
    state.response = response
    logger.info(f"agent_b_node returning: {state}")
    return state
    
    # return {
    #     "user_input": user_input,
    #     "response": response,
    #     "done": True
    # }


