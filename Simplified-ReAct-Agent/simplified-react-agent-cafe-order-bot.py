import os

# Set the cache directory to something writable
# os.environ["HF_HOME"] = "/tmp/huggingface"
# os.environ["HF_DATASETS_CACHE"] = "/tmp/huggingface/datasets"
# os.environ["HUGGINGFACE_HUB_CACHE"] = "/tmp/huggingface/hub"
# os.environ["XDG_CACHE_HOME"] = "/tmp/huggingface"
# os.makedirs("/tmp/huggingface", exist_ok=True)

import streamlit as st
from typing import TypedDict, List, Dict, Literal
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field
from datetime import datetime

from dotenv import load_dotenv
#import json
from langchain.output_parsers import PydanticOutputParser
#from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables
load_dotenv()
hf_api_key = os.environ['HUGGINGFACEHUB_API_TOKEN']
os.environ["LANGCHAIN_API_KEY"] = os.environ.get('LANGCHAIN_API_KEY')
os.environ["LANGCHAIN_API_URL"] = "https://api.langchain.com/v1/graphql"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Simplified-ReAct-Bistro-Chatbot"

os.environ["HUGGINGFACE_TOKEN"] = hf_api_key

llm=ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)


# Define our order item structure
class OrderItem(BaseModel):
    item: str = Field(description="Name of the item ordered")
    quantity: int = Field(description="Quantity of the item")
    price: float = Field(description="Price per item")

# Define the order structure
class Order(BaseModel):
    items: List[OrderItem] = Field(default_factory=list, description="List of items in the order")
    total: float = Field(default=0.0, description="Total cost of the order")

# Define the order structure for the LLM response
class LLM_Response(BaseModel):
    response: str
    order: Order
    next_step: Literal["order_taking", "confirm"]  # Added next_step to the response

# Define the menu
MENU = {
    "burger": 5.99,
    "fries": 2.99,
    "soda": 1.99,
    "pizza": 8.99,
    "salad": 4.99,
    "ice cream": 3.99
}

# Define the state of our graph
class State(TypedDict):
    order: Order
    history: List[Dict[str, str]]
    current_step: Literal["order_taking", "confirm"]
    user_input: str  # Adding user_input to the state


# order total independent validator
def calculate_order_total(order: Order) -> float:
    """
    Independently calculates the total cost of an order by performing arithmetic
    on the order items
    Args:
        order (Order): Order object containing list of OrderItem objects with
                      item name, quantity, and price per item
    
    Returns:
        float: The independently calculated total cost rounded to 2 decimal places
    """
    
    # Initialize total to zero
    calculated_total = 0.0
    
    # Iterate through each item in the order
    for item in order.items:
        # Calculate line total: quantity × price per item
        line_total = item.quantity * item.price
        
        # Add to running total
        calculated_total += line_total
    
    # Round to 2 decimal places to handle floating point precision
    return round(calculated_total, 2)

# Function to generate LLM response based on the current state
def generate_response(state: State) -> State:
    # Construct the prompt based on conversation history and current state
    system_prompt = """
    <s>[INST] You are an ordering assistant for a restaurant. Be friendly, concise, and helpful.
    
    MENU:
    - Burger: $5.99
    - Fries: $2.99
    - Soda: $1.99
    - Pizza: $8.99
    - Salad: $4.99
    - Ice Cream: $3.99
    
    Current Order: {order}
    Current Step: {step}
    
    If in order_taking step:
    1. Greet the user if this is the start of the conversation
    2. Help users select items, modify quantities, or remove items
    3. Keep track of their order and the total
    4. Follow the following set of instructions for calculating the total:
        4.1. Do the first attempt at total calculation by calculating it as sum of (item_price * item_quantity) for each item
        4.2. As the second attempt, calculate another value of the total by adding ALL the ordered items' prices one by one without grouping them
        4.3. If the two answers differ, you identify and correct the mistake before responding.
        4.4  Always proceed step-by-step as in Chain-of-thought while calculating the total.
    5. If they ask for a specific item, check if it's on the menu and add it to their order
    6. If they ask for a total, provide the current total cost of their order
    7. If they ask to remove an item, remove it from their order and re-calculate the total using point 4 above
    8. If they ask to change the quantity, update it in their order and re-calculate the total using point 4 above
    9. If they ask for a summary, provide a summary of their order and total cost
    10. If they ask for a specific item not on the menu, politely inform them it's not available
    11. If they dispute the order total, recheck the order total using point 4 above and confirm
    12. Ask if they want to confirm their order when they're done
    13. Move to confirm step ONLY when they explicitly agree to finalize
    
    If in confirm step:
    - Summarize their complete order and total
    - Thank them for their order
    - Let them know their order has been placed
    
    Format the output as structured JSON according to these rules:
    F1. Always produce valid JSON and no other text
    F2. Here is the output format instructions:
    {format_instructions}
    F3. Do not include any other keys in the JSON response
    [/INST]
    """
    
    # Get the chat history for context
    chat_history = ""
    for message in state["history"]:
        role = message["role"]
        content = message["content"]
        chat_history += f"{role}: {content}\n"
    
    # Get the user message from state
    user_message = state["user_input"]
    
    # Output parser for Pydantic model
    parser = PydanticOutputParser(pydantic_object=LLM_Response)

    # Format instructions
    format_instructions = parser.get_format_instructions()

    # Fill in system prompt variables
    filled_system_prompt = system_prompt.format(
        order=state["order"],
        step=state["current_step"],
        format_instructions=format_instructions
    )

    # Separate system and user messages prevent prompt injection
    # Prepare messages for the LLM
    messages = [
        SystemMessage(content=filled_system_prompt),
        HumanMessage(content=f"Chat History:\n{chat_history}\n\nCurrent User Message: {user_message}")
    ]

    response = llm.invoke(messages)
    
    # Parse the output
    try:
        parsed_output = parser.parse(response if isinstance(response, str) else response.content)
        received_order=parsed_output.order
        calculated_total=calculate_order_total(received_order)
        received_order.total = calculated_total
        # Update the state with the new order and responses
        state["order"] = received_order
        
        state["history"].append({"role": "assistant", "content": parsed_output.response})
        state["current_step"] = parsed_output.next_step
    except Exception as e:
        print(f"Error parsing output: {e}")
        print(f"Raw response: {response}")
        return None
    
    return state

# Function to process user input
def process_user_input(state: State) -> State:
    # Add the user input to the history
    state["history"].append({"role": "user", "content": state["user_input"]})
    return state

# Function to fulfill the order (call external service)
def fulfill_order(state: State) -> State:
    """
    This function takes the current state and fulfills the order by generating an
    order ID and logging the order details. In a real app, this would make an API
    call to an order fulfillment service.

    Args:
        state (State): The current state of the chatbot

    Returns:
        State: The new state of the chatbot after fulfilling the order
    """
    order_obj = state["order"]
    order_data = {
        "order_id": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "items": order_obj.items,
        "total": order_obj.total,
        "timestamp": datetime.now().isoformat()
    }
    
    # Log the order (in a real app, you'd send this to your backend)
    print(f"Order placed: {order_data}")
    
    # Add a system message to the history
    state["history"].append({
        "role": "system", 
        "content": f"Order {order_data['order_id']} has been placed successfully."
    })
    
    # Reset the state for a new order
    state["order"] = order_data
    state["current_step"] = "order_taking"
    
    return state

# Define the transition function for the graph
def should_fulfill_order(state: State) -> Literal["fulfill", "continue"]:
    if state["current_step"] == "confirm":
        return "fulfill"
    return "continue"

# Create the graph
def create_workflow():
    # Initialize the workflow
    workflow = StateGraph(State)
    
    # Add the nodes to the graph
    workflow.add_node("process_input", process_user_input)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("fulfill_order", fulfill_order)
    # Add the edges to the graph
    workflow.add_edge("process_input", "generate_response")
    # Conditional edge from generate_response
    workflow.add_conditional_edges(
        "generate_response",
        should_fulfill_order,
        {
            "fulfill": "fulfill_order",
            "continue": END
        }
    )
    
    # Edge from fulfill_order to END
    workflow.add_edge("fulfill_order", END)
    
    # Set the entry point
    workflow.set_entry_point("process_input")
    
    return workflow

# Compile the graph
order_graph = create_workflow().compile()

def show_sidebar():
    with st.sidebar:
        # Show current order summary in the sidebar
        st.subheader("Current Order")

        order_obj = st.session_state.state["order"]
        # If it's a dict, use as is; if it's an Order object, convert to dict
        if hasattr(order_obj, "model_dump"):
            order_dict = order_obj.model_dump()
        else:
            order_dict = order_obj

        if order_dict["items"]:
            for item in order_dict["items"]:
                item_dict = item.model_dump() if hasattr(item, "model_dump") else item
                st.write(f"{item_dict['quantity']}x {item_dict['item']} - ${item_dict['price'] * item_dict['quantity']:.2f}")
            st.write(f"**Total: ${order_dict['total']:.2f}**")
        else:
            st.write("Your order is empty")

# Streamlit UI
def main():
    st.title("Restaurant Order Chatbot")
    
    # Initialize the session state if it doesn't exist
    if "state" not in st.session_state:
        st.session_state.state = {
            "order": Order().model_dump(),
            "history": [],
            "current_step": "order_taking",
            "user_input": ""
        }
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Display the menu
    with st.expander("Menu"):
        for item, price in MENU.items():
            st.write(f"{item.capitalize()}: ${price:.2f}")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Start Order button
    if "started" not in st.session_state:
        st.session_state.started = False
        
    if not st.session_state.started:
        if st.button("Start Order"):
            st.session_state.started = True
            initial_state = st.session_state.state
            initial_state["user_input"] = "Hello, I'd like to place an order"
            result = order_graph.invoke(initial_state)
            st.session_state.state = result
            last_message = result["history"][-1]
            assistant_response = last_message["content"] if isinstance(last_message, dict) and "content" in last_message else last_message
            st.session_state.messages.append({"role": "user", "content": "Hello, I'd like to place an order"})
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            st.rerun()
    
    # User input handling
    if st.session_state.started:
        if user_input := st.chat_input("Type your order here..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            
            current_state = st.session_state.state
            current_state["user_input"] = user_input
            result = order_graph.invoke(current_state)
            st.session_state.state = result
            
            assistant_response = result["history"][-1]["content"] if result["history"] else "I couldn't process your order. Please try again."
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
            with st.chat_message("assistant"):
                st.markdown(assistant_response)

            show_sidebar()

            if len(result["history"]) >= 2 and result["history"][-2]["role"] == "system":
                system_message = result["history"][-2]["content"]
                st.success(system_message)
                st.session_state.started = False
                st.rerun()
        else:
            show_sidebar()


if __name__ == "__main__":
    main()