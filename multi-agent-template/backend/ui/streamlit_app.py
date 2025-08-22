import streamlit as st
import requests
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure Streamlit page
st.set_page_config(
    page_title="Healthcare Triage Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for healthcare styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        font-size: 2.5rem;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .chat-message-user {
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2196F3;
        margin: 1rem 0;
    }
    .chat-message-assistant {
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
    .routing-info {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 15px;
        font-weight: bold;
        text-align: center;
        margin: 0.5rem 0;
    }
    .urgency-emergency {
        background-color: #FF5252;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-weight: bold;
    }
    .urgency-high {
        background-color: #FF9800;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-weight: bold;
    }
    .urgency-medium {
        background-color: #FFC107;
        color: black;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-weight: bold;
    }
    .urgency-low {
        background-color: #4CAF50;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-weight: bold;
    }
    .sidebar-section {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #DEE2E6;
    }
    .response-details {
        background-color: #F8F9FA;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Backend API configuration
BACKEND_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BACKEND_URL}/chat"

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    if 'medical_summary' not in st.session_state:
        st.session_state.medical_summary = {
            'symptoms': [],
            'doctor_chosen': None,
            'appointment_date': None,
            'insurance_info': None,
            'urgency_level': None,
            'primary_agent': None,
            'current_agent': None
        }

def call_backend_api(user_input: str) -> Dict[str, Any]:
    """Call the FastAPI backend with user input."""
    try:
        payload = {
            "message": user_input,
            "conversation_id": st.session_state.session_id
        }
        
        response = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "response": f"Error: Received status code {response.status_code}",
                "medical_context": {},
                "routing_info": {}
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "response": "❌ Cannot connect to backend server. Please ensure the backend is running on http://localhost:8000",
            "medical_context": {},
            "routing_info": {}
        }
    except requests.exceptions.Timeout:
        return {
            "response": "⏱️ Request timed out. Please try again.",
            "medical_context": {},
            "routing_info": {}
        }
    except Exception as e:
        return {
            "response": f"❌ Unexpected error: {str(e)}",
            "medical_context": {},
            "routing_info": {}
        }

def extract_response_content(response_data: Any) -> str:
    """Extract the main content from API response, handling both dict and string formats."""
    if isinstance(response_data, dict):
        # Handle structured response from agents like CONVERSATION_AGENT
        return response_data.get('content', str(response_data))
    elif isinstance(response_data, str):
        # Handle string responses
        return response_data
    else:
        # Fallback for other types
        return str(response_data)

def extract_agent_info(response_data: Any, routing_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract agent information from response and routing data."""
    agent_info = {
        'agent_name': 'Unknown',
        'tool_used': None,
        'content_type': 'text',
        'success': True
    }
    
    if isinstance(response_data, dict):
        agent_info.update({
            'agent_name': response_data.get('agent', 'Unknown'),
            'tool_used': response_data.get('tool_used'),
            'content_type': response_data.get('content_type', 'text'),
            'success': response_data.get('success', True)
        })
    
    # Get agent from routing info if not in response
    if agent_info['agent_name'] == 'Unknown' and routing_info:
        agent_used = routing_info.get('agent_used')
        if agent_used:
            agent_info['agent_name'] = agent_used
    
    return agent_info

def update_medical_summary(medical_context: Dict[str, Any], user_input: str, agent_info: Dict[str, Any]):
    """Update the medical summary in session state."""
    if not medical_context:
        return
    
    # Extract symptoms from user input (simple keyword extraction)
    symptom_keywords = ['pain', 'hurt', 'fever', 'cough', 'headache', 'sick', 'ache', 'sore', 'dizzy', 'nausea', 'tired', 'fatigue']
    detected_symptoms = [word for word in user_input.lower().split() if any(symptom in word for symptom in symptom_keywords)]
    
    if detected_symptoms:
        st.session_state.medical_summary['symptoms'].extend(detected_symptoms)
        # Remove duplicates and limit to last 10
        st.session_state.medical_summary['symptoms'] = list(set(st.session_state.medical_summary['symptoms']))[-10:]
    
    # Update other fields from medical context
    st.session_state.medical_summary['urgency_level'] = medical_context.get('urgency_level')
    st.session_state.medical_summary['primary_agent'] = medical_context.get('primary_agent')
    st.session_state.medical_summary['current_agent'] = agent_info.get('agent_name')
    
    # Update appointment info if present
    if 'doctor' in user_input.lower() or medical_context.get('primary_agent') == 'APPOINTMENT_SCHEDULER':
        if 'schedule' in user_input.lower() or 'appointment' in user_input.lower():
            st.session_state.medical_summary['doctor_chosen'] = "Scheduling in progress"
            st.session_state.medical_summary['appointment_date'] = "Being scheduled"
    
    # Update insurance info if present
    if 'insurance' in user_input.lower() or medical_context.get('primary_agent') == 'INSURANCE_INQUIRER':
        st.session_state.medical_summary['insurance_info'] = "Inquiry in progress"

def render_sidebar():
    """Render the sidebar with medical summary."""
    st.sidebar.markdown('<h2 style="color: #2E86AB;">📋 Medical Summary</h2>', unsafe_allow_html=True)
    
    # Current Session Info
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("**Session ID:**")
        st.code(st.session_state.session_id[:8] + "...")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Current Agent
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("**🤖 Current Service:**")
        agent = st.session_state.medical_summary['current_agent']
        agent_names = {
            'SYMPTOM_CHECKER': '🩺 Symptom Analysis',
            'APPOINTMENT_SCHEDULER': '📅 Appointment Booking',
            'INSURANCE_INQUIRER': '🛡️ Insurance Support',
            'CONVERSATION_AGENT': '💬 General Conversation'
        }
        current_service = agent_names.get(agent, "*Waiting for input*")
        st.markdown(current_service)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Symptoms Section
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("**🩺 Current Symptoms:**")
        if st.session_state.medical_summary['symptoms']:
            for symptom in st.session_state.medical_summary['symptoms'][-5:]:  # Show last 5
                st.markdown(f"• {symptom.title()}")
        else:
            st.markdown("*No symptoms recorded yet*")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Urgency Level
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("**⚡ Urgency Level:**")
        urgency = st.session_state.medical_summary['urgency_level']
        if urgency:
            urgency_class = f"urgency-{urgency}"
            st.markdown(f'<span class="{urgency_class}">{urgency.upper()}</span>', unsafe_allow_html=True)
        else:
            st.markdown("*Not assessed*")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Doctor/Appointment Section
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("**👨‍⚕️ Doctor Chosen:**")
        doctor = st.session_state.medical_summary['doctor_chosen']
        st.markdown(doctor if doctor else "*No doctor selected*")
        
        st.markdown("**📅 Appointment Date:**")
        appointment = st.session_state.medical_summary['appointment_date']
        st.markdown(appointment if appointment else "*No appointment scheduled*")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Insurance Section
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("**🛡️ Insurance Status:**")
        insurance = st.session_state.medical_summary['insurance_info']
        st.markdown(insurance if insurance else "*No insurance information*")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Clear conversation button
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Clear Conversation", type="secondary"):
        st.session_state.conversation_history = []
        st.session_state.medical_summary = {
            'symptoms': [],
            'doctor_chosen': None,
            'appointment_date': None,
            'insurance_info': None,
            'urgency_level': None,
            'primary_agent': None,
            'current_agent': None
        }
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

def render_chat_message(role: str, content: str, message_data: Dict[str, Any] = None):
    """Render a chat message with appropriate styling and details."""
    if role == "user":
        st.markdown(f'<div class="chat-message-user"><strong>You:</strong><br>{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message-assistant"><strong>Healthcare Assistant:</strong><br>{content}</div>', unsafe_allow_html=True)
        
        # Show additional details if available
        if message_data:
            # Show routing information
            routing_info = message_data.get('routing_info')
            if routing_info:
                st.markdown(f'<div class="routing-info">{routing_info}</div>', unsafe_allow_html=True)
            
            # Show agent and tool information
            agent_info = message_data.get('agent_info', {})
            if agent_info and agent_info.get('agent_name') != 'Unknown':
                details = []
                details.append(f"Agent: {agent_info.get('agent_name')}")
                
                if agent_info.get('tool_used'):
                    details.append(f"Tool: {agent_info.get('tool_used')}")
                
                if agent_info.get('content_type'):
                    details.append(f"Type: {agent_info.get('content_type')}")
                
                if details:
                    details_text = " | ".join(details)
                    st.markdown(f'<div class="response-details">{details_text}</div>', unsafe_allow_html=True)

def main():
    """Main Streamlit application."""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🏥 Healthcare Triage Assistant</h1>', unsafe_allow_html=True)
    st.markdown("### Welcome to your AI-powered healthcare self-service portal")
    st.markdown("*This assistant can help you with symptoms, appointments, and insurance questions.*")
    
    # Medical disclaimer
    st.warning("⚠️ **Medical Disclaimer**: This is a triage assistant for guidance only. In case of emergency, call 911 immediately. This tool does not replace professional medical advice.")
    
    # Render sidebar
    render_sidebar()
    
    # Chat interface
    st.markdown("---")
    st.markdown("### 💬 Chat with Healthcare Assistant")
    
    # Display conversation history
    for message in st.session_state.conversation_history:
        render_chat_message(
            message['role'], 
            message['content'],
            message.get('message_data')
        )
    
    # User input
    with st.form(key='chat_form', clear_on_submit=True):
        user_input = st.text_area(
            "Type your healthcare question or concern:",
            placeholder="Example: I have a headache and fever, should I see a doctor?",
            height=100,
            key="user_input"
        )
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            submit_button = st.form_submit_button("Send 📤", type="primary")
        with col2:
            example_button = st.form_submit_button("💡 Example", type="secondary")
    
    # Handle example button
    if example_button:
        user_input = "I have been having chest pain and difficulty breathing. Should I see a doctor?"
    
    # Handle user input
    if submit_button and user_input.strip():
        # Add user message to history
        st.session_state.conversation_history.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })
        
        # Show thinking spinner
        with st.spinner("🤔 Analyzing your healthcare query..."):
            # Call backend API
            api_response = call_backend_api(user_input)
        
        # Extract response components
        raw_response = api_response.get('response', 'No response received')
        medical_context = api_response.get('medical_context', {})
        routing_info = api_response.get('routing_info', {})
        
        # Extract content and agent information
        assistant_content = extract_response_content(raw_response)
        agent_info = extract_agent_info(raw_response, routing_info)
        
        # Update medical summary
        update_medical_summary(medical_context, user_input, agent_info)
        
        # Prepare message data for display
        message_data = {
            'routing_info': routing_info.get('routing_message'),
            'agent_info': agent_info,
            'medical_context': medical_context
        }
        
        # Add assistant response to history
        st.session_state.conversation_history.append({
            'role': 'assistant',
            'content': assistant_content,
            'message_data': message_data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Rerun to show new messages
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("*Healthcare Triage Assistant • Powered by AI • For informational purposes only*")

if __name__ == "__main__":
    main()