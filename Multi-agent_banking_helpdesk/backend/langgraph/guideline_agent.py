# --- File: guideline_agent.py ---

from instructor import patch
from langchain_community.chat_models import ChatGroq
from langchain.agents import tool, initialize_agent
from pydantic import BaseModel, Field
import os

# LLaMA 3.1 via Groq with Instructor
llm_raw = ChatGroq(model="llama3-8b-8192", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"))
llm = patch(llm_raw)

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
    content = topics.get(topic, "No information available on this topic.")
    return GuidelineOutput(answer=content)

# Guideline agent
guideline_agent = initialize_agent(
    tools=[fetch_guideline],
    llm=llm,
    agent_type="structured-chat-zero-shot-react-description",
    verbose=True
)
