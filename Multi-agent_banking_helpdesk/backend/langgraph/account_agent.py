# --- File: account_agent.py ---

from instructor import patch
from langchain_community.chat_models import ChatGroq
from langchain.agents import tool, initialize_agent
from pydantic import BaseModel, Field
import os

# LLaMA 3.1 via Groq
llm_raw = ChatGroq(model="llama3-8b-8192", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"))
llm = patch(llm_raw)

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
