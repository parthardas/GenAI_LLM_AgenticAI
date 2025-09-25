from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Union

class GraphState(BaseModel):
    """
    Enhanced state schema for the healthcare multi-agent system with tool-based routing support.
    """
    
    # Core user interaction
    user_input: str = Field(default="", description="The user's input message")
    response: Union[str, Dict[str, Any]] = Field(default="", description="The agent's response")
    
    # Routing control
    route_to: str = Field(default="", description="Next agent or node to route to")
    done: bool = Field(default=False, description="Whether the conversation is complete")
    
    # Enhanced routing context for tool-based system
    routing_message: Optional[str] = Field(default=None, description="User-friendly routing status message")
    medical_context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Medical and routing context including urgency, confidence, method"
    )
    
    # Agent-specific data
    agent_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Data passed between agents"
    )
    
    # Session and conversation management
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    conversation_history: Optional[list] = Field(
        default_factory=list,
        description="History of messages in this conversation"
    )
    
    # Error handling
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    class Config:
        """Pydantic configuration"""
        extra = "allow"  # Allow additional fields
        json_encoders = {
            # Add custom encoders if needed
        }
    
    def add_to_history(self, role: str, content: str):
        """Add a message to conversation history"""
        if self.conversation_history is None:
            self.conversation_history = []
        
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": None  # Could add actual timestamp here
        })
    
    def get_routing_summary(self) -> str:
        """Get a summary of the routing decision"""
        if not self.medical_context:
            return "Standard routing"
        
        method = self.medical_context.get('routing_method', 'unknown')
        confidence = self.medical_context.get('routing_confidence', 'medium')
        agent = self.medical_context.get('selected_agent', 'unknown')
        
        return f"Routed to {agent} via {method} (confidence: {confidence})"