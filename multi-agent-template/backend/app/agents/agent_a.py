# agent_a.py

from pydantic import BaseModel, Field
#from langgraph.prebuilt import create_react_agent
from langchain.agents import tool
#from instructor import Instructor as InstructorOpenAI
from langchain_groq import ChatGroq
from models.schemas import GraphState
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

class SearchInputSchema(BaseModel):
    query: str = Field(..., description="The search query to perform")
    website: str = Field(..., description="The website to search on (e.g., 'example.com')")

class OutputSchema(BaseModel):
    result: str

class SearchOutputSchema(BaseModel):
    result: str = Field(..., description="The search result content")
    url: str = Field(..., description="The URL of the search result")
    title: str = Field(..., description="The title of the search result")

# Import Tavily search tool
try:
    from langchain_community.tools import TavilySearchResults
    tavily_search = TavilySearchResults(
        max_results=1,
        api_key=os.getenv("TAVILY_API_KEY")
    )
    TAVILY_AVAILABLE = True
except ImportError:
    logger.warning("Tavily search not available. Install langchain-community to use search functionality.")
    TAVILY_AVAILABLE = False
except Exception as e:
    logger.warning(f"Tavily search initialization failed: {e}")
    TAVILY_AVAILABLE = False

#@tool(args_schema=InputSchema)
#def tool_one(data: str) -> OutputSchema:
def tool_one(tool_input: InputSchema) -> OutputSchema:
    """
    Processes the input data using tool_one and returns the result wrapped in an OutputSchema.

    Args:
        data (str): The input string to be processed.

    Returns:
        OutputSchema: An object containing the processed result.
    """
    logger.info("Hi! I am agent A Tool 1")
    return OutputSchema(result=f"Handled by Agent A tool_one: {tool_input.data}")

#@tool(args_schema=InputSchema)
def tool_two(tool_input: InputSchema) -> OutputSchema:
    """
    Processes the input data using tool_two and returns the result wrapped in an OutputSchema.

    Args:
        data (str): The input string to be processed.

    Returns:
        OutputSchema: An object containing the processed result.
    """
    logger.info("Hi! I am agent A Tool 2")
    return OutputSchema(result=f"Handled by Agent A tool_two: {tool_input.data}")


def tool_three(tool_input: SearchInputSchema) -> SearchOutputSchema:
    """
    Performs a Tavily search on a specified website and returns the top result.

    Args:
        tool_input (SearchInputSchema): An object containing:
            - query (str): The search query to perform
            - website (str): The website to search on

    Returns:
        SearchOutputSchema: An object containing:
            - result (str): The search result content
            - url (str): The URL of the search result
            - title (str): The title of the search result
    """
    logger.info(f"Hi! I am agent A Tool 3 - Performing search for: {tool_input.query} on {tool_input.website}")
    
    if not TAVILY_AVAILABLE:
        return SearchOutputSchema(
            result="Tavily search is not available. Please install langchain-community and set TAVILY_API_KEY.",
            url="",
            title="Search Unavailable"
        )
    
    try:
        # Construct search query with site restriction
        search_query = f"site:{tool_input.website} {tool_input.query}"
        
        # Perform the search
        search_results = tavily_search.run(search_query)
        
        if search_results and len(search_results) > 0:
            # Extract the first result
            first_result = search_results[0]
            
            return SearchOutputSchema(
                result=first_result.get("content", "No content available"),
                url=first_result.get("url", ""),
                title=first_result.get("title", "No title available")
            )
        else:
            return SearchOutputSchema(
                result=f"No search results found for '{tool_input.query}' on {tool_input.website}",
                url="",
                title="No Results"
            )
            
    except Exception as e:
        logger.error(f"Error performing Tavily search: {e}")
        return SearchOutputSchema(
            result=f"Search failed: {str(e)}",
            url="",
            title="Search Error"
        )

# Agent initialized with tools, LLM decides which one to invoke
# agent_a = initialize_agent(
#     tools=[tool_one, tool_two],
#     llm=llm,
#     agent_type="structured-chat-zero-shot-react-description",
#     verbose=True
# )

#agent_a = create_react_agent(llm, tools=[tool_one, tool_two], debug=True, response_format="OutputSchema")

class ToolDecision(BaseModel):
    tool_name: str = Field(..., description="The name of the selected tool: 'tool_one', 'tool_two', or 'tool_three'")
    reasoning: str = Field(..., description="The reasoning behind selecting this particular tool")
    extracted_data: str = Field(..., description="The input data extracted for the tool")
    website: str = Field(default="", description="The website to search on (only for tool_three)")

def llm_tool_decision(user_input: str) -> ToolDecision:
    """
    Uses the LLM to decide which tool to use based on the user input.
    
    Args:
        user_input (str): The user's request
        
    Returns:
        ToolDecision: Contains the selected tool name, reasoning, and extracted parameters
    """
    # Prepare the prompt for tool selection
    tool_descriptions = """
    Available tools:
    1. tool_one: Processes simple text data with Agent A's first tool
    2. tool_two: Processes simple text data with Agent A's second tool
    3. tool_three: Performs a web search on a specific website for information
    """
    
    prompt = f"""You are a tool selection assistant. Given a user request, select the most appropriate tool.
    
    {tool_descriptions}
    
    User request: "{user_input}"
    
    Think through which tool would be most appropriate. If the user is asking for information from a website or wants to search for something, use tool_three.
    If they need simple text processing, choose between tool_one and tool_two based on the complexity of the request.
    
    Respond in the following format only:
    Tool: [selected tool name - must be one of: tool_one, tool_two, tool_three]
    Reasoning: [your reasoning for selecting this tool]
    ExtractedData: [the relevant data from the user request to pass to the tool]
    Website: [only if tool_three is selected, specify which website to search on; default is wikipedia.org]
    """
    
    # Call the LLM to make the decision
    response = llm.invoke(prompt)
    response_text = response.content
    
    logger.info(f"LLM tool selection response: {response_text}")
    
    # Parse the response to extract the tool decision
    lines = response_text.strip().split('\n')
    decision = {}
    
    for line in lines:
        if line.startswith('Tool:'):
            decision['tool_name'] = line.replace('Tool:', '').strip()
        elif line.startswith('Reasoning:'):
            decision['reasoning'] = line.replace('Reasoning:', '').strip()
        elif line.startswith('ExtractedData:'):
            decision['extracted_data'] = line.replace('ExtractedData:', '').strip()
        elif line.startswith('Website:'):
            decision['website'] = line.replace('Website:', '').strip()
    
    # Default values if parsing fails
    tool_name = decision.get('tool_name', 'tool_three')
    reasoning = decision.get('reasoning', 'Default reasoning: Unable to parse LLM response properly')
    extracted_data = decision.get('extracted_data', user_input)
    website = decision.get('website', 'wikipedia.org')
    
    return ToolDecision(
        tool_name=tool_name,
        reasoning=reasoning,
        extracted_data=extracted_data,
        website=website
    )

def agent_a_node(state: GraphState) -> GraphState:
    """
    Processes the given state for agent A using LLM-powered tool selection.
    
    This function uses the Llama-3-Groq-8B-Tool-Use model to intelligently decide
    which tool to invoke based on the user's input, making the system more adaptive
    and context-aware.
    
    Args:
        state (GraphState): The current state object containing user input
        
    Returns:
        GraphState: The updated state object with response and completion status
        
    Behavior:
        - Uses LLM to analyze user input and decide which tool to use
        - Extracts relevant parameters for the chosen tool
        - Invokes the appropriate tool with the extracted parameters
        - Updates the state with the tool's response
        - Includes reasoning about the tool selection in the response
    """
    
    logger.info(f"inside agent_a_node: {state}")
    user_input = state.user_input
    
    try:
        # Get LLM decision about which tool to use
        decision = llm_tool_decision(user_input)
        logger.info(f"LLM decided to use {decision.tool_name}: {decision.reasoning}")
        
        # Execute the chosen tool
        if decision.tool_name == "tool_one":
            tool_input = InputSchema(data=decision.extracted_data)
            tool_result = tool_one(tool_input=tool_input)
            response = f"[Tool Selection: {decision.reasoning}]\n\n{tool_result.result}"
            
        elif decision.tool_name == "tool_two":
            tool_input = InputSchema(data=decision.extracted_data)
            tool_result = tool_two(tool_input=tool_input)
            response = f"[Tool Selection: {decision.reasoning}]\n\n{tool_result.result}"
            
        elif decision.tool_name == "tool_three":
            # Use provided website or default to wikipedia
            website = decision.website if decision.website else "wikipedia.org"
            search_input = SearchInputSchema(query=decision.extracted_data, website=website)
            search_result = tool_three(tool_input=search_input)
            
            response = f"[Tool Selection: {decision.reasoning}]\n\n"
            response += f"Search Result:\n"
            response += f"Title: {search_result.title}\n"
            response += f"URL: {search_result.url}\n"
            response += f"Content: {search_result.result}"
            
        else:
            response = f"Unknown tool selected: {decision.tool_name}. Please try again."
            
    except Exception as e:
        logger.error(f"Error in agent_a_node: {e}")
        response = f"An error occurred while processing your request: {str(e)}"
    
    # Update state
    state.done = True
    state.route_to = "END"
    state.response = response
    
    logger.info(f"agent_a_node returning: {state}")
    return state