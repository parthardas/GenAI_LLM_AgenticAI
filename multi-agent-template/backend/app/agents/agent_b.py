# agent_b.py

from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langchain.agents import tool
#from instructor import Instructor as InstructorOpenAI
from langchain_groq import ChatGroq
from models.schemas import GraphState
import os
from agents.system_prompts import AGENT_B_TOOL_SELECTION_SYSTEM_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage


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
def schedule_practice_doctors(tool_input: InputSchema) -> OutputSchema:
    """
    Processes the input data using schedule_practice_doctors and returns the result wrapped in an OutputSchema.

    Args:
        data (str): The input string to be processed.

    Returns:
        OutputSchema: An object containing the processed result.
    """
    logger.info("Hi! I am agent B Tool schedule_practice_doctors")
    return OutputSchema(result=f"Handled by Agent B Tool schedule_practice_doctors: {tool_input.data}")

#@tool(args_schema=InputSchema)
def schedule_network_doctors(tool_input: InputSchema) -> OutputSchema:
    """
    Processes the input data using schedule_network_doctors and returns the result wrapped in an OutputSchema.

    Args:
        data (str): The input string to be processed.

    Returns:
        OutputSchema: An object containing the processed result.
    """
    logger.info("Hi! I am agent B Tool schedule_network_doctors")
    return OutputSchema(result=f"Handled by Agent B Tool schedule_network_doctors: {tool_input.data}")

# Agent initialized with tools, LLM decides which one to invoke
# agent_b = initialize_agent(
#     tools=[tool_one, tool_two],
#     llm=llm,
#     agent_type="structured-chat-zero-shot-react-description",
#     verbose=True
# )

# LangGraph node for agent_b

class ToolDecision(BaseModel):
    tool_name: str = Field(..., description="The name of the selected tool: 'tool_one', 'tool_two', or 'tool_three'")
    reasoning: str = Field(..., description="The reasoning behind selecting this particular tool")
    extracted_data: str = Field(..., description="The input data extracted for the tool")
    #website: str = Field(default="", description="The website to search on (only for tool_three)")

def llm_tool_decision(user_input: str) -> ToolDecision:
    """
    Uses the LLM to decide which tool to use based on the user input.
    
    Args:
        user_input (str): The user's request
        
    Returns:
        ToolDecision: Contains the selected tool name, reasoning, and extracted parameters
    """
    
    # Create human message with user input
    human_prompt = f"""User request: "{user_input}"

This user wants to schedule a doctor's appointment. Analyze their request to determine if they want to schedule:
1. With doctors in our practice (schedule_practice_doctors)
2. With doctors in our affiliated network (schedule_network_doctors)

If they don't specify, ask them to clarify their preference but default to practice doctors.

Respond in the exact format specified in the system prompt."""
    
    # Create messages with separated system and human prompts
    messages = [
        SystemMessage(content=AGENT_B_TOOL_SELECTION_SYSTEM_PROMPT),
        HumanMessage(content=human_prompt)
    ]
    
    # Call the LLM with the separated messages
    response = llm.invoke(messages)
    response_text = response.content
    
    logger.info(f"LLM tool selection response: {response_text}")
    
    # Parse the response to extract the tool decision (rest of function remains the same)
    lines = response_text.strip().split('\n')
    decision = {}
    
    for line in lines:
        if line.startswith('Tool:'):
            decision['tool_name'] = line.replace('Tool:', '').strip()
        elif line.startswith('Reasoning:'):
            decision['reasoning'] = line.replace('Reasoning:', '').strip()
        elif line.startswith('ExtractedData:'):
            decision['extracted_data'] = line.replace('ExtractedData:', '').strip()
    
    # Default values if parsing fails
    tool_name = decision.get('tool_name', 'schedule_practice_doctors')
    reasoning = decision.get('reasoning', 'Default reasoning: Unable to parse LLM response properly')
    extracted_data = decision.get('extracted_data', user_input)
    
    return ToolDecision(
        tool_name=tool_name,
        reasoning=reasoning,
        extracted_data=extracted_data
    )

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
    """

    logger.info(f"inside agent_b_node: {state}")
    
    #user_input = state.user_input if hasattr(state, "user_input") else state["user_input"]
    
    user_input = state.user_input
    
    # decision = llm_tool_decision(user_input)

    # if "tool 1" in user_input.lower():
    #     tool_one_input = InputSchema(data=user_input)
    #     tool_result = tool_one(tool_input=tool_one_input)
    #     response = tool_result.result
    # elif "tool 2" in user_input.lower():
    #     tool_result = tool_two(tool_input=InputSchema(data=user_input))
    #     response = tool_result.result
    # else:
    #     response = "Please specify 'tool 1' or 'tool 2' in your input for agent B."
    
    try:
        # Get LLM decision about which tool to use
        decision = llm_tool_decision(user_input)
        logger.info(f"LLM decided to use {decision.tool_name}: {decision.reasoning}")
        
        # Execute the chosen tool
        if decision.tool_name == "schedule_practice_doctors":
            tool_input = InputSchema(data=decision.extracted_data)
            tool_result = schedule_practice_doctors(tool_input=tool_input)
            response = f"[Tool Selection: {decision.reasoning}]\n\n{tool_result.result}"

        elif decision.tool_name == "schedule_network_doctors":
            tool_input = InputSchema(data=decision.extracted_data)
            tool_result = schedule_network_doctors(tool_input=tool_input)
            response = f"[Tool Selection: {decision.reasoning}]\n\n{tool_result.result}"
            
        else:
            response = f"Unknown tool selected: {decision.tool_name}. Please try again."
            
    except Exception as e:
        logger.error(f"Error in agent_b_node: {e}")
        response = f"An error occurred while processing your request: {str(e)}"
    

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


