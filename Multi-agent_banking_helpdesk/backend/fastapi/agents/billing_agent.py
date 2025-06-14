from instructor import patch
from langchain_groq import ChatGroq
from langchain.agents import tool, initialize_agent
from pydantic import BaseModel, Field
import os
import json

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

class BillingInput(BaseModel):
    input_str: str = Field(..., description="JSON string containing user_id, biller_name, and amount")

class BillingOutput(BaseModel):
    message: str

@tool(args_schema=BillingInput)
def pay_bill(input_str: str) -> BillingOutput:
    """Process a bill payment for a user from a JSON string input.
    
    Args:
        input_str: JSON string containing:
            - user_id: The unique identifier of the user
            - biller_name: The name of the biller/company
            - amount: The payment amount in dollars
    
    Returns:
        BillingOutput: Confirmation message of the transaction
    
    Example:
        >>> pay_bill('{"user_id": "user123", "biller_name": "Electric Company", "amount": 100.50}')
    """
    try:
        data = json.loads(input_str)
        user_id = data['user_id']
        biller_name = data['biller_name']
        amount = float(data['amount'])
        return BillingOutput(
            message=f"Biller '{biller_name}' added and ${amount:.2f} paid from user {user_id}'s account."
        )
    except (json.JSONDecodeError, KeyError) as e:
        return BillingOutput(message=f"Error processing payment: {str(e)}")

# Billing agent
billing_agent = initialize_agent(
    tools=[pay_bill],
    llm=llm,
    agent_type="zero-shot-react-description",
    verbose=True
)