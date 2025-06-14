from instructor import patch
from langchain_groq import ChatGroq
from langchain.agents import tool, initialize_agent
from pydantic import BaseModel, Field
import os

from dotenv import load_dotenv
load_dotenv()

lc_api_key = os.environ.get('LANGCHAIN_API_KEY')
os.environ["LANGCHAIN_API_URL"] = "https://api.langchain.com/v1/graphql"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "multi-agent-assistant"

# LLaMA 3.1 via Groq with Instructor
llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# Tool schema and function
topics = {
    "KYC": "Know Your Customer (KYC) is a standard banking process...",
    "LoanPolicy": "Bank offers personal loans at 12% interest with flexible tenure..."
}

class GuidelineInput(BaseModel):
    topic: str = Field(..., description="The policy topic to search, like 'KYC', 'LoanPolicy'")

class GuidelineOutput(BaseModel):
    answer: str

@tool(args_schema=GuidelineInput)
def fetch_guideline(topic: str) -> GuidelineOutput:
    """
    Fetch banking guidelines and policies for a specific topic.
    Args:
        topic: The banking policy topic to look up (e.g., 'KYC', 'LoanPolicy')
    Returns:
        GuidelineOutput: Contains the guideline information for the requested topic
    """
    content = topics.get(topic, "No information available on this topic.")
    return GuidelineOutput(answer=content)

# Guideline agent
guideline_agent = initialize_agent(
    tools=[fetch_guideline],
    llm=llm,
    agent_type="structured-chat-zero-shot-react-description",
    verbose=True
)