# meta_agent.py

from langgraph.graph import StateGraph
from pydantic import BaseModel, Field
#from instructor import Instructor as InstructorOpenAI
from langchain_groq import ChatGroq
from app.models.schemas import GraphState
#from groq import Groq
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import logging
from langchain.output_parsers import PydanticOutputParser
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

lc_api_key = os.environ.get('LANGCHAIN_API_KEY')
os.environ["LANGCHAIN_API_URL"] = "https://api.langchain.com/v1/graphql"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "multi-agent-template"

# Mock LLM
#llm_raw = Groq(model="llama-3.1-8b-instant", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"))
llm_raw = ChatGroq(model="llama-3.1-8b-instant", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"))
#llm = patch(llm_raw)
llm=llm_raw

# from openai import OpenAI

# openai_client = OpenAI(
#     api_key=os.getenv("GROQ_API_KEY"),
#     base_url="https://api.groq.com/openai/v1"
# )
# llm = InstructorOpenAI(client=openai_client, create=openai_client.chat.completions.create)

# Decision schema
class AgentRoutingDecision(BaseModel):
    agent_name: str = Field(..., description="Name of the sub-agent to route to.")

#@node
def router_node(state: GraphState) -> dict:
    """
    Routes the user input to the appropriate sub-agent based on the decision made by a language model.
    Args:
        state (GraphState): The current state containing user input and other relevant information.
    Returns:
        dict: A dictionary containing the selected agent's name under the key "route_to" and the original user input under "user_input".
    Raises:
        ValueError: If the language model selects an invalid agent name.
    Logs:
        - The initial state and user input.
        - The decision made by the language model.
        - The agent selected for routing.
    """

    logger.info(f"In router_node: {state}")

    user_input = state.user_input

    # Safely check if "done" is present and True in the state
    #state.user_input if hasattr(state, "user_input")
    if (hasattr(state, "done") and state.done) or (isinstance(state, dict) and state.get("done")):
        return {"route_to": "END", "user_input": state.user_input}

    # if getatstr(state, "done", False) or state.get("done", False):
    #     return {"route_to": "END", "user_input": state.user_input}

    # Use LLM to choose sub-agent
    parser = PydanticOutputParser(pydantic_object=AgentRoutingDecision)
    prompt = (
        "Imagine that you are a robot that receives an input and gives an output.\n"
        "Remember: You are not a coder here and are not outputing code, but just giving the desired output as per the below logic.\n"
        "If the user asks for agent A then return \"agent_a\".\n"
        "Similarly for agent B or Agent C, return \"agent_b\" and \"agent_c\" respectively.\n"
        "Based on the following user input, decide which agent to use.\n"
        "Output will be strictly in this JSON format: {\"agent_name\": \"<chosen string as per above instruction>\"}\n"
        "Example: {\"agent_name\": \"agent_b\"}\n"
        f"Input: {user_input}\n"
    )
    llm_response = llm.invoke(prompt)
    # Parse the LLM response using the output parser
    if hasattr(llm_response, "content"):
        decision = parser.parse(llm_response.content)
    else:
        decision = parser.parse(llm_response)

    logger.info(f"In router_node: after LLM decision: {decision}")

    # Validate decision
    valid_agents = {"agent_a", "agent_b", "agent_c"}
    if decision.agent_name not in valid_agents:
        raise ValueError(f"Invalid agent selected: {decision.agent_name}")
    
    # Log the decision
    logger.info(f"In router_node: before router return: {decision.agent_name}")

    return {"route_to": decision.agent_name, "user_input": user_input}
    #return decision.agent_name