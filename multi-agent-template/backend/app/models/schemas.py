# backend/app/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any
from enum import Enum

class OperationType(str, Enum):
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"

class ArithmeticInput(BaseModel):
    operation: OperationType
    operands: List[float] = Field(..., min_items=2, description="List of numbers to operate on")
    
class ArithmeticOutput(BaseModel):
    operation: OperationType
    operands: List[float]
    result: float
    success: bool
    error_message: Optional[str] = None

class AgentStep(BaseModel):
    agent_name: str
    operation: OperationType
    input_data: ArithmeticInput
    output_data: Optional[ArithmeticOutput] = None
    execution_order: int

class ReasoningPlan(BaseModel):
    user_query: str
    interpretation: str
    required_operations: List[AgentStep]
    final_combination_logic: str

class GraphState(BaseModel):
    # Core input/output fields
    user_input: str = ""
    response: Optional[str] = None
    
    # Routing and workflow control
    route_to: Optional[str] = None
    done: Optional[bool] = False
    
    # Healthcare-specific routing context
    medical_context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    routing_message: Optional[str] = ""
    
    # Session and conversation management
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Agent execution tracking
    agent_call_count: int = 0
    agent_results: Optional[List[ArithmeticOutput]] = Field(default_factory=list)
    
    # Legacy arithmetic fields (for backward compatibility)
    reasoning_plan: Optional[ReasoningPlan] = None
    final_result: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        # Allow extra fields for future extensibility
        extra = "allow"

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None
    reasoning_steps: Optional[List[str]] = None
    calculations: Optional[List[ArithmeticOutput]] = None

class HealthcareRoutingDecision(BaseModel):
    primary_agent: str = Field(..., description="Primary agent to route to: SYMPTOM_CHECKER, APPOINTMENT_SCHEDULER, or INSURANCE_INQUIRER")
    secondary_agents: List[str] = Field(default=[], description="Additional agents if needed")
    routing_sequence: List[str] = Field(..., description="Ordered list of agent execution")
    reasoning: str = Field(..., description="Clear explanation of routing decision")
    urgency_level: str = Field(..., description="Urgency level: low, medium, high, emergency")
    patient_intent: str = Field(..., description="Brief description of patient intent")
    expected_workflow: str = Field(..., description="How agents will work together")
    validation_criteria: str = Field(..., description="How to verify routing was correct")
