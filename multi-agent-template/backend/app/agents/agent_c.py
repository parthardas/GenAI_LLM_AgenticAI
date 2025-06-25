# agent_c.py

from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langchain.agents import tool
#from instructor import Instructor as InstructorOpenAI
from langchain_groq import ChatGroq
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

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

@tool(args_schema=InputSchema)
def tool_one(data: str) -> OutputSchema:
    """
    Processes the input data using tool_one and returns the result wrapped in an OutputSchema.

    Args:
        data (str): The input string to be processed.

    Returns:
        OutputSchema: An object containing the processed result.
    """
    return OutputSchema(result=f"Handled by tool_one: {data}")

@tool(args_schema=InputSchema)
def tool_two(data: str) -> OutputSchema:
    """
    Processes the input data using tool_two and returns the result wrapped in an OutputSchema.

    Args:
        data (str): The input string to be processed.

    Returns:
        OutputSchema: An object containing the processed result.
    """
    return OutputSchema(result=f"Handled by tool_two: {data}")

# Agent initialized with tools, LLM decides which one to invoke
# agent_c = initialize_agent(
#     tools=[tool_one, tool_two],
#     llm=llm,
#     agent_type="structured-chat-zero-shot-react-description",
#     verbose=True
# )

agent_c = create_react_agent(llm, tools=[tool_one, tool_two], debug=True, response_format="OutputSchema")

