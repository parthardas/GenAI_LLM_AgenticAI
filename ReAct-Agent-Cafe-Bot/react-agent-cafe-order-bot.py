import streamlit as st
import os
from langchain_groq import ChatGroq

from typing import Dict, List, Tuple, Any, TypedDict, Annotated
import json
from datetime import datetime

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from langgraph.graph import MessagesState

from dotenv import load_dotenv
load_dotenv()

groq_api_key=os.environ['GROQ_API_KEY']

os.environ["LANGCHAIN_API_KEY"]=os.environ.get('LANGCHAIN_API_KEY')
os.environ["LANGCHAIN_API_URL"]="https://api.langchain.com/v1/graphql"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "ReAct-Bistro-Chatbot"

llm=ChatGroq(model_name="llama3-70b-8192")

# Define state types
#class OrderState(TypedDict):
class OrderState(MessagesState):
    messages: List[Dict[str, str]]
    order_items: List[Dict[str, Any]]
    customer_name: str
    order_confirmed: bool
    order_submitted: bool
    current_step: str

# Menu items with prices
MENU = {
    "Coffee": {
        "Espresso": 2.50,
        "Americano": 3.00,
        "Latte": 3.50,
        "Cappuccino": 3.50,
        "Mocha": 4.00
    },
    "Tea": {
        "Green Tea": 2.50,
        "Black Tea": 2.50,
        "Herbal Tea": 3.00,
        "Chai Latte": 3.50
    },
    "Pastries": {
        "Croissant": 2.50,
        "Muffin": 3.00,
        "Scone": 2.75,
        "Brownie": 3.50,
        "Cookie": 2.00
    },
    "Sandwiches": {
        "Avocado Toast": 6.50,
        "BLT": 7.00,
        "Veggie Wrap": 6.50
    }
}

# Function to format menu as string
def format_menu() -> str:
    menu_str = "Our Menu:\n\n"
    for category, items in MENU.items():
        menu_str += f"--- {category} ---\n"
        for item, price in items.items():
            menu_str += f"{item}: ${price:.2f}\n"
        menu_str += "\n"
    return menu_str

# Define conversation nodes
def greet(state: OrderState) -> OrderState:
    """Initial greeting and menu presentation"""
    #llm = get_llm()
    
    # If this is the first message, greet the customer
    if state["current_step"] == "start":
        menu = format_menu()
        system_prompt = f"""
        You are a friendly cafe order chatbot. Greet the customer warmly and ask for their order.
        Here is the menu you can offer:
        
        {menu}

        Present the menu.
        Be conversational and helpful. Don't be too pushy.
        """
        
        state["messages"].append({"role": "system", "content": system_prompt})
        
        response = llm.invoke(state["messages"])
        # [
        #    {"role": "system", "content": system_prompt},
        #    {"role": "assistant", "content": "Hello! Welcome to our cafe. What can I get for you today?"}
        # ]
        
        state["messages"].append({"role": "assistant", "content": response.content})
        #state["messages"].append({"role": "assistant", "content": menu})
        state["current_step"] = "taking_order"
    
    return state

def process_order(state: OrderState) -> OrderState:
    """Process customer's order input"""

    
    # Prepare conversation history for the LLM
    conversation = [
        {"role": "system", "content": f"""
        You are the same cafe order chatbot with the same menu. Extract order items \
         from the customer's message.
        
        For each item, identify:
        1. The item name (must match exactly with the menu)
        2. Quantity
        3. Any customizations (e.g., "no sugar", "extra hot")
        
        Maintain the order details as a structured JSON object. 
        Update the order in response to user requests and always return the latest \
         JSON representation.
        The JSON schema should be as follows:
        {
            "order_id": "string",
            "order_line_items":
            [
                {
                "item": "string",
                "quantity": int,
                "customizations": "string"
                }
            ]
            "total_price": float,
            "status": "string"
        }
        If an item is not on the menu, politely let them know.
        """}
    ]
    


    # Get response from LLM
    response = llm.invoke(state["messages"])
    
    
    # Add assistant response to messages
    state["messages"].append({"role": "assistant", "content": response.content})
    
    # Check if we should move to confirmation
    # if len(state["order_items"]) > 0 and "confirm" in last_user_message["content"].lower():
    #     state["current_step"] = "confirm_order"
    # else:
    #     state["current_step"] = "taking_order"
    
    return state

    """Confirm the order details with the customer"""
    #llm = get_llm()
    
    # Format order summary
    order_summary = "Here's your order summary:\n\n"
    total = 0.0
    
    for item in state["order_items"]:
        item_total = item["price"] * item["quantity"]
        total += item_total
        customization = f" ({item['customizations']})" if item.get("customizations") else ""
        order_summary += f"- {item['quantity']}x {item['item']}{customization}: ${item_total:.2f}\n"
    
    order_summary += f"\nTotal: ${total:.2f}"
    
    # Prepare conversation for confirmation
    conversation = [
        {"role": "system", "content": f"""
        You are a cafe order chatbot. You need to confirm the customer's order.
        Present the order summary and ask if everything is correct.
        If they want to make changes, go back to taking the order.
        If they confirm, proceed to ask for their name (if not already provided) for the order.
        """}
    ]
    
    # Add conversation history
    for msg in state["messages"]:
        conversation.append({"role": msg["role"], "content": msg["content"]})
    
    # Add order summary
    conversation.append({"role": "assistant", "content": order_summary + "\n\nIs this order correct? Would you like to make any changes?"})
    
    # Get response from LLM
    response = llm.invoke(conversation)
    
    # Add assistant response to messages
    state["messages"].append({"role": "assistant", "content": order_summary + "\n\nIs this order correct? Would you like to make any changes?"})
    
    # Update state
    state["current_step"] = "awaiting_confirmation"
    
    return state

    """Process the customer's response to order confirmation"""
    #llm = get_llm()
    
    # Get the last user message
    last_user_message = next((msg for msg in reversed(state["messages"]) if msg["role"] == "user"), None)
    
    if not last_user_message:
        return state
    
    # Check if the customer confirmed the order
    confirmation_prompt = f"""
    Analyze if the customer has confirmed their order or wants to make changes.
    
    Customer message: "{last_user_message['content']}"
    
    Return only "confirmed" if they confirmed the order, or "changes" if they want to make changes.
    """
    
    confirmation_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": confirmation_prompt}]
    )
    
    confirmation_result = confirmation_response.choices[0].message.content.strip().lower()
    
    if "confirmed" in confirmation_result:
        # Order confirmed, check if we have customer name
        if not state["customer_name"]:
            # Ask for customer name
            name_prompt = "Great! Could I get your name for the order?"
            state["messages"].append({"role": "assistant", "content": name_prompt})
            state["current_step"] = "get_customer_name"
        else:
            # We have everything, submit the order
            state["order_confirmed"] = True
            state["current_step"] = "submit_order"
    else:
        # Customer wants to make changes
        change_prompt = "No problem! What changes would you like to make to your order?"
        state["messages"].append({"role": "assistant", "content": change_prompt})
        state["current_step"] = "taking_order"
    
    return state

    """Submit the confirmed order"""
    # In a real system, this would connect to a backend order processing system
    # For this demo, we'll just mark it as submitted
    
    # Calculate order total
    total = sum(item["price"] * item["quantity"] for item in state["order_items"])
    
    # Format receipt
    receipt = f"""
    === ORDER RECEIPT ===
    Order #{datetime.now().strftime('%Y%m%d%H%M%S')}
    Customer: {state["customer_name"]}
    Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Items:
    """
    
    for item in state["order_items"]:
        item_total = item["price"] * item["quantity"]
        customization = f" ({item['customizations']})" if item.get("customizations") else ""
        receipt += f"- {item['quantity']}x {item['item']}{customization}: ${item_total:.2f}\n"
    
    receipt += f"\nTotal: ${total:.2f}"
    receipt += "\n\nThank you for your order!"
    
    # Add receipt to messages
    state["messages"].append({"role": "assistant", "content": receipt})
    
    # Update state
    state["order_submitted"] = True
    state["current_step"] = "complete"
    
    return state

def router(state: OrderState) -> str:
    """Route to the next step based on current state"""
    current_step = state["current_step"]
    
    if current_step == "start":
        return "greet"
    elif current_step == "taking_order":
        return "process_order"
    elif current_step == "complete":
        return END
    else:
        return "greet"

# Build the graph
def build_graph():
    # Create workflow
    workflow = StateGraph(OrderState)
    
    # Add nodes
    #workflow.add_node(START)
    workflow.add_node("greet", greet)
    workflow.add_node("process_order", process_order)

    
    # Add edges
    workflow.add_edge(START, "greet")
    workflow.add_edge("greet", "process_order")

    workflow.add_edge("process_order", END)

    # Compile the graph
    return workflow.compile()

# Initialize session state

if "order_graph" not in st.session_state:
    st.session_state.order_graph = build_graph()

# Streamlit UI
#st.title("Chatbot with Memory")
st.title("☕ Veggie Cafe Order Chatbot")

# Reset button
# Create a session variable to disable number input and 
# button widgets when answer is correct.
if 'b1_disabled' not in st.session_state:
    st.session_state.b1_disabled = False

#if st.button("Start New Order", disabled=st.session_state.b1_disabled):
if st.button("Start New Order"):
#if st.button("Start New Order"):
    #if len(st.session_state.chat_history)==0:
    
    st.session_state.order_state = {
        "messages": [],
        "order_items": [],
        "customer_name": "",
        "order_confirmed": False,
        "order_submitted": False,
        "current_step": "start"
    }
    with st.chat_message("assistant"):
        
        state=greet(st.session_state.order_state)
 
if "order_state" not in st.session_state:
    st.session_state.order_state = {
        "messages": [],
        "order_items": [],
        "customer_name": "",
        "order_confirmed": False,
        "order_submitted": False,
        "current_step": "start"
    }

# Initialize chat history
for message in st.session_state.order_state["messages"]:
    if message["role"] != "system":  # Skip system messages
        with st.chat_message(message["role"]):
            st.write(message["content"])

# User input
if prompt := st.chat_input("Type your message here..."):
    # Add prompt to state messages
    st.session_state.order_state["messages"].append({"role": "user", "content": prompt})
    

    # Generate bot response
    bot_response=llm.invoke(st.session_state.order_state['messages']).content

    # Add bot response to state messages
    st.session_state.order_state["messages"].append({"role": "assistant", "content": bot_response})
    
    # Display last chat
    with st.chat_message(st.session_state.order_state["messages"][-2]["role"]):
        st.markdown(st.session_state.order_state["messages"][-2]["content"])
    with st.chat_message(st.session_state.order_state["messages"][-1]["role"]):
        st.markdown(st.session_state.order_state["messages"][-1]["content"])

