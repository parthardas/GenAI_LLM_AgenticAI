# meta_agent.py

from langgraph.graph import StateGraph
from pydantic import BaseModel, Field
#from instructor import Instructor as InstructorOpenAI
from langchain_groq import ChatGroq
from models.schemas import GraphState, HealthcareRoutingDecision
from agents.system_prompts import HEALTHCARE_ROUTER_SYSTEM_PROMPT, ROUTING_VALIDATION_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage
import json
#from groq import Groq
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import logging
from langchain.output_parsers import PydanticOutputParser
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

lc_api_key = os.environ.get('LANGCHAIN_API_KEY')
os.environ["LANGCHAIN_API_URL"] = "https://api.langchain.com/v1/graphql"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "multi-agent-template"

# Mock LLM
#llm_raw = Groq(model="llama-3.1-8b-instant", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"))
llm_raw = ChatGroq(model="llama-3.1-8b-instant", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"))
#llm = patch(llm_raw)
llm=llm_raw

# from openai import OpenAI

# openai_client = OpenAI(
#     api_key=os.getenv("GROQ_API_KEY"),
#     base_url="https://api.groq.com/openai/v1"
# )
# llm = InstructorOpenAI(client=openai_client, create=openai_client.chat.completions.create)

# Decision schema
class AgentRoutingDecision(BaseModel):
    agent_name: str = Field(..., description="Name of the sub-agent to route to.")


def build_conversation_context(conversation_history: list = None) -> str:
    """
    Build conversation context from previous exchanges.
    
    Args:
        conversation_history (list): Previous conversation messages
        
    Returns:
        str: Formatted conversation context
    """
    if not conversation_history:
        return ""
    
    context_parts = []
    # Get last 3 exchanges for context (to avoid token limits)
    recent_history = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
    
    for msg in recent_history:
        msg_type = msg.get('type', 'user')
        content = msg.get('content', '')
        timestamp = msg.get('timestamp', '')
        
        if content:  # Only include non-empty messages
            if timestamp:
                context_parts.append(f"- {msg_type} ({timestamp}): {content}")
            else:
                context_parts.append(f"- {msg_type}: {content}")
    
    if context_parts:
        return "Previous conversation context:\n" + "\n".join(context_parts) + "\n\n"
    return ""

# Update the create_user_routing_prompt function:

def create_user_routing_prompt(user_query: str, conversation_history: list = None) -> str:
    """
    Create the user message content for healthcare routing analysis.
    
    Args:
        user_query (str): Current patient query
        conversation_history (list): Previous conversation context
        
    Returns:
        str: Formatted user message for routing analysis
    """
    context = build_conversation_context(conversation_history)
    
    return f"""{context}Current patient query: "{user_query}"

Please analyze this query and provide your routing decision as a JSON object ONLY. Do not include any explanatory text, markdown formatting, or additional content outside the JSON structure.

Respond with only the JSON object following the format specified in the system prompt."""

def get_system_prompt() -> str:
    """
    Get the healthcare router system prompt.
    
    Returns:
        str: The complete system prompt for healthcare routing
    """
    return HEALTHCARE_ROUTER_SYSTEM_PROMPT

def get_validation_prompt() -> str:
    """
    Get the routing validation prompt template.
    
    Returns:
        str: The validation prompt template
    """
    return ROUTING_VALIDATION_PROMPT

#@node


def validate_routing_decision(user_query: str, routing_decision: dict, agent_responses: str = "") -> dict:
    """
    LLM-as-a-judge function to validate routing decisions using ROUTING_VALIDATION_PROMPT.
    
    Args:
        user_query (str): Original user query
        routing_decision (dict): The routing decision made by the router
        agent_responses (str): Responses from agents (if available)
        
    Returns:
        dict: Validation results with score and recommendations
    """
    try:
        # Format the validation prompt with actual data
        validation_prompt = ROUTING_VALIDATION_PROMPT.format(
            user_query=user_query,
            routing_decision=json.dumps(routing_decision, indent=2),
            agent_responses=agent_responses or "No agent responses yet"
        )
        
        # Create messages for validation
        messages = [
            SystemMessage(content="You are an expert healthcare routing validator. Evaluate routing decisions for accuracy, safety, and effectiveness."),
            HumanMessage(content=validation_prompt)
        ]
        
        # Get validation response
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Clean and parse JSON response
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()
        
        validation_result = json.loads(content)
        
        logger.info(f"Routing Validation Score: {validation_result.get('validation_score', 'N/A')}/10")
        logger.info(f"Validation Passed: {validation_result.get('validation_passed', False)}")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error in routing validation: {e}")
        # Return default validation result
        return {
            "validation_score": 5,
            "accuracy_assessment": "Unable to validate due to error",
            "completeness_check": "Validation failed",
            "efficiency_rating": "Unknown",
            "safety_evaluation": "Requires manual review",
            "improvement_suggestions": ["Manual review recommended due to validation error"],
            "alternative_routing": "Consider fallback routing",
            "validation_passed": False
        }


# Replace the handle_general_conversation function:

def handle_general_conversation(state: GraphState) -> GraphState:
    """
    Handle general conversation topics using LLM for natural responses.
    
    Args:
        state (GraphState): Current state with user input
        
    Returns:
        GraphState: Updated state with LLM-generated conversation response
    """
    try:
        # Create a conversation system prompt
        conversation_system_prompt = """You are a friendly healthcare assistant. You can help users with:

1. **Symptom Analysis**: Analyze symptoms and provide health guidance
2. **Appointment Scheduling**: Help schedule doctor appointments 
3. **Insurance Support**: Answer insurance coverage and billing questions

For general conversation, greetings, or questions about your capabilities:
- Be warm, helpful, and professional
- Briefly explain what you can do
- Guide users toward healthcare services you offer
- Keep responses concise but informative
- Always maintain a healthcare-focused context

Remember: You are a healthcare triage assistant, so gently steer conversations toward health-related topics when appropriate."""

        # Create user message for conversation
        user_message = f"""The user said: "{state.user_input}"

Please provide a helpful, conversational response. If they're greeting you or asking about your capabilities, explain what healthcare services you offer. Keep it friendly but professional."""

        # Create messages for LLM
        messages = [
            SystemMessage(content=conversation_system_prompt),
            HumanMessage(content=user_message)
        ]
        
        # Get LLM response
        llm_response = llm.invoke(messages)
        conversation_content = llm_response.content.strip()
        
        # Create structured response
        response = {
            "agent": "CONVERSATION_AGENT",
            "content": conversation_content,
            "content_type": "conversation",
            "success": True,
            "facilities_mentioned": True if any(word in state.user_input.lower() for word in ['what', 'how', 'help', 'services', 'facilities', 'can you']) else False
        }
        
        logger.info(f"LLM conversation response generated for: {state.user_input}")
        
    except Exception as e:
        logger.error(f"Error generating conversation response: {e}")
        # Fallback response
        response = {
            "agent": "CONVERSATION_AGENT",
            "content": "Hello! I'm your healthcare assistant. I can help you with symptoms, schedule appointments, and answer insurance questions. How can I assist you today?",
            "content_type": "conversation_fallback",
            "success": False,
            "error": str(e)
        }
    
    # Update state
    state.response = response
    state.done = True
    state.route_to = "END"
    
    # Update medical context for conversation
    state.medical_context = {
        'primary_agent': 'CONVERSATION_AGENT',
        'routing_reasoning': 'General conversation handled with LLM response',
        'urgency_level': 'low',
        'patient_intent': 'general conversation',
        'validation_score': 8,
        'validation_passed': True,
        'tool_selection': 'Conversation agent selected for greetings and general inquiries'
    }
    
    logger.info(f"General conversation handled with LLM: {response.get('content_type', 'unknown')}")
    return state

# Updated router_node function with validation integration
def router_node(state: GraphState) -> GraphState:
    """
    Healthcare routing node that analyzes patient queries and routes to appropriate healthcare agents.
    Routes to SYMPTOM_CHECKER, APPOINTMENT_SCHEDULER, or INSURANCE_INQUIRER based on patient needs.
    Includes LLM-as-a-judge validation for routing decisions.
    """
    # Handle different input types
    if isinstance(state, dict):
        state = GraphState(**state)
    elif isinstance(state, str):
        state = GraphState(user_input=state)
    elif not isinstance(state, GraphState):
        state = GraphState(**state.__dict__)

    logger.info(f"Healthcare Router - Processing: {state.user_input}")

    # Check if conversation is already complete
    if state.done:
        return state

    # Get conversation history if available
    conversation_history = getattr(state, 'conversation_history', [])


    try:
        # Create system and user messages
        system_prompt = get_system_prompt()
        user_prompt = create_user_routing_prompt(state.user_input, conversation_history)
        
        # Create message objects
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # Get LLM response
        response = llm.invoke(messages)
        content = response.content.strip()
        
        logger.info(f"Raw LLM response: {content}")  # Add this for debugging
        
        # Clean and parse JSON response
        if content.startswith('```json'):
            content = content.replace('```json', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()
        
        # Check if content is empty or not valid JSON
        if not content or content.isspace():
            logger.error("Empty response from LLM")
            raise json.JSONDecodeError("Empty response", content, 0)
        
        decision_data = json.loads(content)
        decision = HealthcareRoutingDecision(**decision_data)
        
        logger.info(f"Healthcare Routing Decision: {decision.primary_agent} - {decision.reasoning}")
        logger.info(f"Urgency Level: {decision.urgency_level}")
        logger.info(f"Patient Intent: {decision.patient_intent}")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Raw content: {content}")
        # Fallback routing based on keywords
        state = fallback_healthcare_routing(state)
        return state
    
    except Exception as e:
        logger.error(f"Error in healthcare routing: {e}")
        # Fallback routing based on keywords
        state = fallback_healthcare_routing(state)
        return state

    try:
        # VALIDATION STEP: Validate the routing decision using LLM-as-a-judge
        validation_result = validate_routing_decision(
            user_query=state.user_input,
            routing_decision=decision_data
        )
        
        # Check if validation passed
        if not validation_result.get("validation_passed", False):
            logger.warning(f"Routing validation failed. Score: {validation_result.get('validation_score', 0)}/10")
            logger.warning(f"Issues: {validation_result.get('improvement_suggestions', [])}")
            
            # If validation suggests alternative routing, consider it
            alternative_routing = validation_result.get("alternative_routing")
            if alternative_routing and "CONVERSATION_AGENT" in alternative_routing:
                logger.info("Validator suggests routing to CONVERSATION_AGENT")
                decision.primary_agent = "CONVERSATION_AGENT"
                decision.reasoning = f"Validator override: {alternative_routing}"
                decision.urgency_level = "low"
            elif alternative_routing and "SYMPTOM_CHECKER" in alternative_routing:
                logger.info("Validator suggests routing to SYMPTOM_CHECKER for safety")
                decision.primary_agent = "SYMPTOM_CHECKER"
                decision.reasoning = f"Validator override: {alternative_routing}"
                decision.urgency_level = "medium"
            elif validation_result.get("validation_score", 0) < 3:
                # Very low confidence - default to conversation for safety in unclear cases
                logger.warning("Very low validation score - defaulting to CONVERSATION_AGENT")
                decision.primary_agent = "CONVERSATION_AGENT"
                decision.reasoning = "Low confidence routing - defaulting to conversation for clarification"
                decision.urgency_level = "low"

        # Handle emergency situations
        if decision.urgency_level == "emergency":
            state.route_to = "END"
            state.done = True
            state.response = (
                "🚨 EMERGENCY DETECTED 🚨\n\n"
                "If this is a medical emergency, please:\n"
                "• Call 911 immediately\n"
                "• Go to the nearest emergency room\n"
                "• Contact emergency services\n\n"
                "Do not delay seeking immediate medical attention for emergency situations."
            )
            return state

        # Map healthcare agents to internal agent names
        agent_mapping = {
            "SYMPTOM_CHECKER": "agent_a",
            "APPOINTMENT_SCHEDULER": "agent_b", 
            "INSURANCE_INQUIRER": "agent_c",
            "CONVERSATION_AGENT": "conversation"
        }
        
        # Validate and map primary agent
        if decision.primary_agent not in agent_mapping:
            logger.warning(f"Invalid primary agent: {decision.primary_agent}, defaulting to CONVERSATION_AGENT")
            decision.primary_agent = "CONVERSATION_AGENT"
        
        primary_route = agent_mapping[decision.primary_agent]

        # Handle conversation agent within meta_agent
        if decision.primary_agent == "CONVERSATION_AGENT":
            return handle_general_conversation(state)

        # Update state with routing information
        state.route_to = primary_route
        state.done = False
        
        # Store healthcare context in state (including validation results)
        state.medical_context = {
            'primary_agent': decision.primary_agent,
            'secondary_agents': decision.secondary_agents,
            'routing_sequence': decision.routing_sequence,
            'routing_reasoning': decision.reasoning,
            'urgency_level': decision.urgency_level,
            'patient_intent': decision.patient_intent,
            'expected_workflow': decision.expected_workflow,
            'validation_criteria': decision.validation_criteria,
            # Add validation results
            'validation_score': validation_result.get('validation_score', 0),
            'validation_passed': validation_result.get('validation_passed', False),
            'validation_suggestions': validation_result.get('improvement_suggestions', [])
        }
        
        # Create routing message for user feedback
        urgency_indicators = {
            "emergency": "🚨 EMERGENCY",
            "high": "⚡ URGENT",
            "medium": "⚠️ MODERATE", 
            "low": "ℹ️ ROUTINE"
        }
        
        agent_descriptions = {
            "SYMPTOM_CHECKER": "Symptom Analysis & Health Guidance",
            "APPOINTMENT_SCHEDULER": "Doctor Appointment Scheduling",
            "INSURANCE_INQUIRER": "Insurance Coverage & Benefits",
            "CONVERSATION_AGENT": "General Conversation Assistant"
        }
        
        urgency_indicator = urgency_indicators.get(decision.urgency_level, "ℹ️")
        agent_desc = agent_descriptions.get(decision.primary_agent, "Healthcare Service")
        
        state.routing_message = f"{urgency_indicator} Routing to {agent_desc}"
        
        # Add validation confidence to routing message if low
        validation_score = validation_result.get('validation_score', 10)
        if validation_score < 7:
            state.routing_message += f" (Confidence: {validation_score}/10)"
        
        # Handle multi-agent workflows
        if decision.secondary_agents:
            state.routing_message += f" (Multi-step workflow: {' → '.join(decision.routing_sequence)})"
        
        logger.info(f"Healthcare Router - Final routing: {state.route_to} ({decision.primary_agent})")
        logger.info(f"Expected workflow: {decision.expected_workflow}")
        logger.info(f"Validation confidence: {validation_score}/10")
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        # Fallback routing based on keywords
        state = fallback_healthcare_routing(state)
        
    except Exception as e:
        logger.error(f"Error in healthcare routing: {e}")
        # Default to symptom checker for safety
        state.route_to = "agent_a"
        state.medical_context = {
            'primary_agent': 'SYMPTOM_CHECKER',
            'routing_reasoning': 'Defaulted to symptom checker due to routing error',
            'urgency_level': 'medium',
            'patient_intent': 'healthcare inquiry',
            'validation_score': 0,
            'validation_passed': False
        }
        state.routing_message = "⚠️ Routing to Symptom Analysis (default)"
    
    return state

def fallback_healthcare_routing(state: GraphState) -> GraphState:
    """
    Fallback routing logic when LLM parsing fails or returns invalid response.
    Uses keyword-based routing for basic healthcare triage, defaulting to SYMPTOM_CHECKER for safety.
    
    Args:
        state (GraphState): Current state with user input
        
    Returns:
        GraphState: Updated state with fallback routing decision
    """
    user_input_lower = state.user_input.lower()
    
    # Emergency keywords - highest priority
    emergency_keywords = [
        "emergency", "911", "chest pain", "can't breathe", "difficulty breathing",
        "heart attack", "stroke", "severe pain", "unconscious", "suicide",
        "overdose", "bleeding heavily", "choking"
    ]
    
    # Appointment keywords
    appointment_keywords = [
        "appointment", "schedule", "book", "doctor", "see a doctor", 
        "visit", "consultation", "check-up", "available", "when can i see",
        "reschedule", "cancel appointment", "doctor availability"
    ]
    
    # Insurance keywords
    insurance_keywords = [
        "insurance", "coverage", "policy", "copay", "deductible", 
        "cost", "billing", "claim", "benefits", "covered", "premium",
        "out of pocket", "authorization", "carrier"
    ]
    
    logger.info(f"Fallback routing activated for: {state.user_input}")
    
    # Check for emergency situations first (highest priority)
    if any(keyword in user_input_lower for keyword in emergency_keywords):
        state.route_to = "END"
        state.done = True
        state.response = (
            "🚨 EMERGENCY DETECTED 🚨\n\n"
            "If this is a medical emergency, please:\n"
            "• Call 911 immediately\n"
            "• Go to the nearest emergency room\n"
            "• Contact emergency services\n\n"
            "Do not delay seeking immediate medical attention for emergency situations."
        )
        state.medical_context = {
            'primary_agent': 'EMERGENCY',
            'routing_reasoning': 'Fallback: Emergency keywords detected',
            'urgency_level': 'emergency',
            'patient_intent': 'emergency medical situation',
            'validation_score': 0,
            'validation_passed': False
        }
        state.routing_message = "🚨 EMERGENCY - Call 911 immediately!"
        logger.info("Fallback routing: Emergency detected")
        return state
    
    # Check for insurance-related queries
    elif any(keyword in user_input_lower for keyword in insurance_keywords):
        state.route_to = "agent_c"
        state.medical_context = {
            'primary_agent': 'INSURANCE_INQUIRER',
            'routing_reasoning': 'Fallback: Insurance-related keywords detected',
            'urgency_level': 'low',
            'patient_intent': 'insurance inquiry',
            'validation_score': 6,  # Medium confidence for keyword matching
            'validation_passed': True
        }
        state.routing_message = "ℹ️ Routing to Insurance Coverage & Benefits (fallback)"
        logger.info("Fallback routing: Insurance inquiry detected")
    
    # Check for appointment-related queries
    elif any(keyword in user_input_lower for keyword in appointment_keywords):
        state.route_to = "agent_b"
        state.medical_context = {
            'primary_agent': 'APPOINTMENT_SCHEDULER',
            'routing_reasoning': 'Fallback: Appointment-related keywords detected',
            'urgency_level': 'medium',
            'patient_intent': 'appointment scheduling',
            'validation_score': 6,  # Medium confidence for keyword matching
            'validation_passed': True
        }
        state.routing_message = "⚠️ Routing to Doctor Appointment Scheduling (fallback)"
        logger.info("Fallback routing: Appointment request detected")
    
    # Check for general conversation topics (non-medical)
    elif any(word in user_input_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'how are you', 'what can you do', 'what services', 'what facilities', 'how can you help', 'weather', 'chat', 'talk']):
        state.medical_context = {
            'primary_agent': 'CONVERSATION_AGENT',
            'secondary_agents': [],
            'routing_sequence': ['CONVERSATION_AGENT'],
            'reasoning': 'Fallback: General conversation keywords detected',
            'urgency_level': 'low',
            'patient_intent': 'general conversation',
            'expected_workflow': 'Single agent handling general inquiries',
            'validation_criteria': 'Conversation agent selected for general inquiries',
            'tool_selection': 'Conversation agent for general inquiries and greetings'
        }
        
        state.routing_message = "💬 Handling General Conversation (fallback)"
        logger.info("Fallback routing: General conversation detected")
        return handle_general_conversation(state)

    # Default to SYMPTOM_CHECKER for health-related unclear cases (safety first)
    else:
        state.route_to = "agent_a"
        state.medical_context = {
            'primary_agent': 'SYMPTOM_CHECKER',
            'routing_reasoning': 'Fallback: Default to symptom checker for safety when unclear health-related query',
            'urgency_level': 'medium',
            'patient_intent': 'unclear healthcare inquiry - needs evaluation',
            'validation_score': 5,  # Lower confidence since it's a fallback
            'validation_passed': True  # Safe default for health queries
        }
        state.routing_message = "⚠️ Routing to Symptom Analysis & Health Guidance (fallback)"
        logger.info("Fallback routing: Defaulting to SYMPTOM_CHECKER for unclear health queries")
        # Set common fallback properties
        state.done = False
    
    # Add fallback indicator to medical context
    if 'medical_context' in state.__dict__:
        state.medical_context['is_fallback_routing'] = True
        state.medical_context['fallback_reason'] = 'LLM routing failed or returned invalid response'
    
    logger.info(f"Fallback routing completed: {state.route_to} - {state.medical_context['routing_reasoning']}")
    
    return state