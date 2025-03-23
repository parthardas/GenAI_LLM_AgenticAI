import streamlit as st
from typing import TypedDict, List, Dict, Annotated, Literal
from langgraph.graph import END, StateGraph
from groq import Groq
import json
from pydantic import BaseModel, Field
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
groq_api_key = os.environ['GROQ_API_KEY']
os.environ["LANGCHAIN_API_KEY"] = os.environ.get('LANGCHAIN_API_KEY')
os.environ["LANGCHAIN_API_URL"] = "https://api.langchain.com/v1/graphql"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Simplified-ReAct-Bistro-Chatbot"

# Initialize Groq client with API key from environment
groq_client = Groq(api_key=groq_api_key)

# Define our order item structure
class OrderItem(BaseModel):
    item: str = Field(description="Name of the item ordered")
    quantity: int = Field(description="Quantity of the item")
    price: float = Field(description="Price per item")

# Define the order structure
class Order(BaseModel):
    items: List[OrderItem] = Field(default_factory=list, description="List of items in the order")
    total: float = Field(default=0.0, description="Total cost of the order")

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

# Function to generate LLM response based on the current state
def generate_response(state: State) -> State:
    # Construct the prompt based on conversation history and current state
    system_prompt = """
    You are an ordering assistant for a restaurant. Be friendly, concise, and helpful.
    
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
    - Greet the user if this is the start of the conversation
    - Help users select items, modify quantities, or remove items
    - Keep track of their order and the total
    - Ask if they want to confirm their order when they're done
    - ONLY move to confirm step when they explicitly agree to finalize
    
    If in confirm step:
    - Summarize their complete order and total
    - Thank them for their order
    - Let them know their order has been placed
    
    Format the output as structured JSON according to these rules:
    1. Always produce valid JSON
    2. Use the format:
    {{
      "response": "Your response to the user here",
      "order_update": {{
        "add": [list of items to add with quantities and prices],
        "remove": [list of items to remove]
      }},
      "next_step": "order_taking or confirm"
    }}
    """
    
    # Format the system prompt with current state
    formatted_system_prompt = system_prompt.format(
        order=json.dumps(state["order"]),
        step=state["current_step"]
    )
    
    # Get the chat history for context
    chat_history = ""
    for message in state["history"]:
        role = message["role"]
        content = message["content"]
        chat_history += f"{role}: {content}\n"
    
    # Get the user message from state
    user_message = state["user_input"]
    
    # Construct the prompt for the LLM
    user_prompt = f"""
    Chat History:
    {chat_history}
    
    Current User Message: {user_message}
    
    Respond according to the instructions.
    """
    
    # Call the Llama model on Groq
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": formatted_system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )
    
    # Parse the response
    llm_response = json.loads(response.choices[0].message.content)
    
    # Update the order based on LLM response
    if "order_update" in llm_response:
        # Add items
        for item_to_add in llm_response["order_update"].get("add", []):
            # Create a new OrderItem
            if isinstance(item_to_add, dict) and "item" in item_to_add:
                new_item = OrderItem(
                    item=item_to_add["item"],
                    quantity=item_to_add.get("quantity", 1),
                    price=item_to_add.get("price", MENU.get(item_to_add["item"].lower(), 0))
                )
                
                # Check if the item already exists in the order
                existing_item = next((i for i in state["order"]["items"] if i["item"].lower() == new_item.item.lower()), None)
                if existing_item:
                    existing_item["quantity"] += new_item.quantity
                else:
                    state["order"]["items"].append(new_item.model_dump())
        
        # Remove items
        for item_to_remove in llm_response["order_update"].get("remove", []):
            if isinstance(item_to_remove, str):
                # Remove by name
                state["order"]["items"] = [i for i in state["order"]["items"] if i["item"].lower() != item_to_remove.lower()]
            elif isinstance(item_to_remove, dict) and "item" in item_to_remove:
                # Remove with specific quantity
                item_name = item_to_remove["item"].lower()
                quantity = item_to_remove.get("quantity", 1)
                
                for i in range(len(state["order"]["items"])):
                    if i < len(state["order"]["items"]) and state["order"]["items"][i]["item"].lower() == item_name:
                        if state["order"]["items"][i]["quantity"] <= quantity:
                            state["order"]["items"].pop(i)
                        else:
                            state["order"]["items"][i]["quantity"] -= quantity
    
    # Recalculate the total
    state["order"]["total"] = sum(item["quantity"] * item["price"] for item in state["order"]["items"])
    
    # Update the conversation history
    state["history"].append({"role": "assistant", "content": llm_response["response"]})
    
    # Update the current step if needed
    if "next_step" in llm_response:
        state["current_step"] = llm_response["next_step"]
    
    return state

# Function to process user input
def process_user_input(state: State) -> State:
    # Add the user input to the history
    state["history"].append({"role": "user", "content": state["user_input"]})
    return state

# Function to fulfill the order (call external service)
def fulfill_order(state: State) -> State:
    # This is where you would make an API call to an order fulfillment service
    # For demonstration purposes, we'll just log the order
    order_data = {
        "order_id": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "items": state["order"]["items"],
        "total": state["order"]["total"],
        "timestamp": datetime.now().isoformat()
    }
    
    # Log the order (in a real app, you'd send this to your backend)
    print(f"Order placed: {json.dumps(order_data, indent=2)}")
    
    # Add a system message to the history
    state["history"].append({
        "role": "system", 
        "content": f"Order {order_data['order_id']} has been placed successfully."
    })
    
    # Reset the state for a new order
    state["order"] = Order().model_dump()
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

# Streamlit UI
def main():
    st.title("Restaurant Order Chatbot")
    
    # Initialize the session state if it doesn't exist
    if "state" not in st.session_state:
        st.session_state.state = {
            "order": Order().model_dump(),
            "history": [],
            "current_step": "order_taking",
            "user_input": ""  # Initialize with empty user input
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
            # Initial greeting
            initial_state = st.session_state.state
            # Set the initial user input
            initial_state["user_input"] = "Hello, I'd like to place an order"
            
            # Run the workflow with the initial greeting
            result = order_graph.invoke(initial_state)
            
            # Update the state
            st.session_state.state = result
            
            # Extract the assistant's response
            assistant_response = result["history"][-1]["content"]
            
            # Add to display messages
            st.session_state.messages.append({"role": "user", "content": "Hello, I'd like to place an order"})
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
            # Rerun to show the updated UI
            st.rerun()
    
    # User input
    if st.session_state.started:
        # Show current order summary in the sidebar
        st.sidebar.subheader("Current Order")
        if st.session_state.state["order"]["items"]:
            for item in st.session_state.state["order"]["items"]:
                st.sidebar.write(f"{item['quantity']}x {item['item']} - ${item['price'] * item['quantity']:.2f}")
            st.sidebar.write(f"**Total: ${st.session_state.state['order']['total']:.2f}**")
        else:
            st.sidebar.write("Your order is empty")
        
        # Chat input
        if user_input := st.chat_input("Type your order here..."):
            # Add user message to chat history display
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Display the user message
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Get the current state and update user input
            current_state = st.session_state.state
            current_state["user_input"] = user_input
            
            # Run the workflow
            result = order_graph.invoke(current_state)
            
            # Update the state
            st.session_state.state = result
            
            # Extract the assistant's response
            assistant_response = result["history"][-1]["content"] if result["history"] else "I couldn't process your order. Please try again."
            
            # Add to display messages
            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
            # Display the assistant response
            with st.chat_message("assistant"):
                st.markdown(assistant_response)
            
            # Check if there was a system message (order fulfilled)
            if len(result["history"]) >= 2 and result["history"][-2]["role"] == "system":
                system_message = result["history"][-2]["content"]
                st.success(system_message)
                
                # Allow the user to start a new order
                st.session_state.started = False
                
                # Reset the state for a new order (already done in fulfill_order)
                # Rerun to reset the UI
                st.rerun()

if __name__ == "__main__":
    main()