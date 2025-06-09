# --- File: billing_agent.py ---

from instructor import patch
from langchain_community.chat_models import ChatGroq
from langchain.agents import tool, initialize_agent
from pydantic import BaseModel, Field
import os

# LLaMA 3.1 via Groq
llm_raw = ChatGroq(model="llama3-8b-8192", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"))
llm = patch(llm_raw)

# Tool schema and function
class BillingInput(BaseModel):
    user_id: str = Field(..., description="User ID of the customer")
    biller_name: str = Field(..., description="Name of the biller to add")
    amount: float = Field(..., description="Payment amount")

class BillingOutput(BaseModel):
    message: str

@tool(args_schema=BillingInput)
def pay_bill(user_id: str, biller_name: str, amount: float) -> BillingOutput:
    return BillingOutput(message=f"Biller '{biller_name}' added and ${amount:.2f} paid from user {user_id}'s account.")

# Billing agent
billing_agent = initialize_agent(
    tools=[pay_bill],
    llm=llm,
    agent_type="structured-chat-zero-shot-react-description",
    verbose=True
)
