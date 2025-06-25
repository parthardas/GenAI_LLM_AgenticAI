# backend/app/models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
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
    user_input: str
    reasoning_plan: Optional[ReasoningPlan] = None
    agent_results: Optional[List[ArithmeticOutput]] = []
    final_result: Optional[str] = None
    error: Optional[str] = None
    agent_call_count: int = 0
    conversation_history: List[Dict] = []
    done: Optional[bool] = False
    response: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    reasoning_steps: Optional[List[str]] = None
    calculations: Optional[List[ArithmeticOutput]] = None
