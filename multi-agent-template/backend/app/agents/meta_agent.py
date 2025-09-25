from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import os
import logging

logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize LLM
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"))

# Define routing tools that the LLM can call directly
@tool
def route_to_symptom_checker(query: str, urgency_level: str = "medium") -> str:
    """
    Route patient to symptom analysis and health guidance.
    Use this for: symptoms, pain, illness, medical concerns, health questions, feeling unwell.
    
    Args:
        query: The patient's health query or symptoms
        urgency_level: Level of urgency (low, medium, high, emergency)
    
    Returns:
        str: Routing confirmation message
    """
    logger.info(f"Routing to symptom checker with urgency: {urgency_level}")
    return f"ROUTE:agent_a|{urgency_level}|{query}"

@tool
def route_to_appointment_scheduler(query: str, appointment_type: str = "general") -> str:
    """
    Route patient to appointment scheduling service.
    Use this for: booking appointments, scheduling visits, doctor availability, rescheduling, canceling appointments.
    
    Args:
        query: The appointment request
        appointment_type: Type of appointment needed (general, specialist, followup, urgent)
    
    Returns:
        str: Routing confirmation message
    """
    logger.info(f"Routing to appointment scheduler for: {appointment_type}")
    return f"ROUTE:agent_b|medium|{query}|{appointment_type}"

@tool
def route_to_insurance_inquirer(query: str, inquiry_type: str = "coverage") -> str:
    """
    Route patient to insurance and billing support.
    Use this for: insurance coverage, billing questions, costs, copays, claims, payment issues.
    
    Args:
        query: The insurance-related question
        inquiry_type: Type of insurance inquiry (coverage, billing, claims, costs)
    
    Returns:
        str: Routing confirmation message
    """
    logger.info(f"Routing to insurance support for: {inquiry_type}")
    return f"ROUTE:agent_c|low|{query}|{inquiry_type}"

@tool
def handle_general_conversation(query: str) -> str:
    """
    Handle general conversation, greetings, and non-medical inquiries.
    Use this for: greetings (hello, hi), general questions about services, casual conversation, 
    asking about what you can help with, hospital information.
    
    Args:
        query: The general conversation message
    
    Returns:
        str: Routing confirmation message
    """
    logger.info("Handling general conversation")
    return f"ROUTE:conversation|low|{query}"

@tool
def handle_emergency_situation(query: str) -> str:
    """
    Handle medical emergencies requiring immediate attention.
    Use this for: chest pain, difficulty breathing, severe injuries, life-threatening situations,
    unconsciousness, severe bleeding, stroke symptoms, heart attack symptoms.
    
    Args:
        query: The emergency situation description
    
    Returns:
        str: Emergency response message
    """
    logger.error(f"EMERGENCY SITUATION DETECTED: {query}")
    return f"ROUTE:emergency|emergency|{query}"

# Create routing tools list
routing_tools = [
    route_to_symptom_checker,
    route_to_appointment_scheduler, 
    route_to_insurance_inquirer,
    handle_general_conversation,
    handle_emergency_situation
]

# Create the routing agent
router_agent = create_react_agent(llm, routing_tools)

def router_node(state: dict) -> dict:
    """
    Intelligent healthcare router using LLM tool calling for automatic routing.
    The LLM will automatically select and call the appropriate routing tool.
    
    Args:
        state: Dictionary containing the current state
        
    Returns:
        dict: Updated state dictionary
    """
    logger.info(f"Healthcare Router - Processing: {state.get('user_input', '')}")
    
    try:
        user_input = state.get("user_input", "")
        
        # Create routing message for the agent
        routing_prompt = f"""You are a healthcare triage router. Analyze this patient query and call the appropriate routing tool.

Patient Query: "{user_input}"

Guidelines for tool selection:
- For medical symptoms, health concerns, feeling sick → use route_to_symptom_checker
- For appointment requests, scheduling → use route_to_appointment_scheduler  
- For insurance, billing, payment questions → use route_to_insurance_inquirer
- For greetings, general questions → use handle_general_conversation
- For life-threatening emergencies → use handle_emergency_situation

Call the most appropriate tool now."""

        messages = [HumanMessage(content=routing_prompt)]
        
        # Let the agent automatically select and call the routing tool
        result = router_agent.invoke({"messages": messages})
        
        # Get the final message from the agent
        final_message = result["messages"][-1].content
        logger.info(f"Router agent response: {final_message}")
        
        # Parse the tool result
        if "ROUTE:" in final_message:
            route_info = final_message.split("ROUTE:")[1].strip()
            parts = route_info.split("|")
            
            agent_id = parts[0]
            urgency = parts[1] if len(parts) > 1 else "medium"
            query = parts[2] if len(parts) > 2 else user_input
            extra_info = parts[3] if len(parts) > 3 else ""
            
            # Handle emergency routing
            if agent_id == "emergency":
                state["route_to"] = "END"
                state["done"] = True
                state["response"] = """🚨 MEDICAL EMERGENCY DETECTED 🚨

If this is a life-threatening emergency:
• Call 911 immediately
• Go to the nearest emergency room
• Contact emergency services right now

Do not delay seeking immediate medical attention.
Your safety is our top priority."""
                return state
            
            # Handle conversation routing
            if agent_id == "conversation":
                return handle_general_conversation_dict(state)
            
            # Set routing for specialized agents
            state["route_to"] = agent_id
            state["done"] = False
            
            # Enhanced routing context
            state["medical_context"] = {
                'routing_method': 'automatic_tool_selection',
                'urgency_level': urgency,
                'selected_agent': agent_id,
                'routing_confidence': 'high',
                'original_query': user_input,
                'processed_query': query,
                'extra_context': extra_info
            }
            
            # Friendly routing messages
            agent_descriptions = {
                'agent_a': 'Health & Symptom Analysis 🏥',
                'agent_b': 'Appointment Scheduling 📅', 
                'agent_c': 'Insurance & Billing Support 💳'
            }
            
            state["routing_message"] = f"🎯 Connecting you to {agent_descriptions.get(agent_id, agent_id)}..."
            logger.info(f"Successfully routed to {agent_id} with urgency {urgency}")
            
        else:
            # Fallback if tool calling doesn't return expected format
            logger.warning("Tool calling didn't return expected ROUTE format, using fallback")
            state = fallback_healthcare_routing(state)
            
    except Exception as e:
        logger.error(f"Error in automatic routing: {e}")
        state = fallback_healthcare_routing(state)
    
    return state

def handle_general_conversation_dict(state: dict) -> dict:
    """Handle general conversation using LLM with healthcare context"""
    
    user_input = state.get("user_input", "")
    
    conversation_prompt = f"""You are a friendly and professional healthcare assistant. 
    
User message: "{user_input}"

Respond warmly and helpfully. If appropriate, guide them toward our healthcare services:
- Health concerns or symptoms → I can help analyze symptoms
- Need an appointment → I can help schedule appointments  
- Insurance questions → I can help with coverage and billing
- Emergency → Direct them to call 911

Keep your response conversational, helpful, and healthcare-focused. Be concise but warm."""
    
    try:
        response = llm.invoke([HumanMessage(content=conversation_prompt)])
        
        state["response"] = {
            "agent": "CONVERSATION_AGENT",
            "content": response.content,
            "content_type": "conversation",
            "routing_method": "automatic_tool_selection"
        }
        state["done"] = True
        state["route_to"] = "END"
        
        logger.info("Successfully handled general conversation")
        
    except Exception as e:
        logger.error(f"Error in conversation handling: {e}")
        state["response"] = """Hello! I'm your healthcare assistant. I'm here to help you with:

🏥 Health questions and symptoms
📅 Scheduling appointments  
💳 Insurance and billing questions
🆘 Emergency guidance

How can I assist you today?"""
        state["done"] = True
        state["route_to"] = "END"
    
    return state

def fallback_healthcare_routing(state: dict) -> dict:
    """Fallback routing when automatic tool selection fails"""
    
    logger.info("Using fallback routing logic")
    
    user_input = state.get("user_input", "")
    user_input_lower = user_input.lower()
    
    # Simple keyword-based fallback routing
    emergency_keywords = ['emergency', 'urgent', 'chest pain', 'can\'t breathe', 'bleeding', 'unconscious']
    appointment_keywords = ['appointment', 'schedule', 'book', 'doctor', 'visit', 'available']
    insurance_keywords = ['insurance', 'billing', 'cost', 'pay', 'coverage', 'claim', 'copay']
    greeting_keywords = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'help']
    
    if any(keyword in user_input_lower for keyword in emergency_keywords):
        state["route_to"] = "END"
        state["done"] = True
        state["response"] = "🚨 For medical emergencies, please call 911 immediately!"
    elif any(keyword in user_input_lower for keyword in appointment_keywords):
        state["route_to"] = "agent_b"
        state["done"] = False
        state["routing_message"] = "📅 Connecting you to Appointment Scheduling..."
    elif any(keyword in user_input_lower for keyword in insurance_keywords):
        state["route_to"] = "agent_c"
        state["done"] = False
        state["routing_message"] = "💳 Connecting you to Insurance Support..."
    elif any(keyword in user_input_lower for keyword in greeting_keywords):
        state = handle_general_conversation_dict(state)
    else:
        # Default to symptom checker for health-related queries
        state["route_to"] = "agent_a"
        state["done"] = False
        state["routing_message"] = "🏥 Connecting you to Health Analysis..."
    
    # Set fallback context
    if not state.get("done", False):
        state["medical_context"] = {
            'routing_method': 'fallback_keyword_matching',
            'routing_confidence': 'medium',
            'urgency_level': 'medium'
        }
    
    return state