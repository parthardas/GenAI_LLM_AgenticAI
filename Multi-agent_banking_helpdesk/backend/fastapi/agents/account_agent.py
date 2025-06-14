# --- File: account_agent.py ---

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

# LLaMA 3.1 via Groq
llm = ChatGroq(
    model="llama3-8b-8192",
    temperature=0,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# Tool schema and function
mock_accounts = {
    "user123": {"savings": 1500.50, "checking": 250.00},
    "user456": {"savings": 3000.00, "checking": 500.00}
}

class AccountInput(BaseModel):
    user_id: str = Field(..., description="The user ID to look up the account balance")

class AccountOutput(BaseModel):
    answer: str

@tool(args_schema=AccountInput)
def get_account_balance(user_id: str) -> AccountOutput:
    """
    Retrieves account balances for a specific user ID.

    Args:
        user_id (str): The unique identifier of the user whose account balances are being queried.

    Returns:
        AccountOutput: An object containing the formatted account balance information.
                      If no accounts are found, returns a message indicating no accounts exist.
                      If accounts exist, returns a comma-separated list of account types and their balances.

    Example:
        >>> get_account_balance("user123")
        AccountOutput(answer="Balances - checking: $1000, savings: $5000")
    """
    accounts = mock_accounts.get(user_id, {})
    if not accounts:
        return AccountOutput(answer="No account found for the given user ID.")
    summary = ", ".join(f"{k}: ${v}" for k, v in accounts.items())
    return AccountOutput(answer=f"Balances - {summary}")

# Account agent
account_agent = initialize_agent(
    tools=[get_account_balance],
    llm=llm,
    agent_type="structured-chat-zero-shot-react-description",
    verbose=True
)
