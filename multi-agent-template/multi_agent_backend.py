# Project Structure
multi-agent-arithmetic/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── meta_agent.py
│   │   │   ├── arithmetic_agents.py
│   │   │   └── graph_builder.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── llm_service.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx
│   │   │   └── ConversationHistory.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
└── docker-compose.yml

# backend/requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
instructor==0.4.5
groq==0.4.1
langgraph==0.0.62
langchain==0.1.0
langchain-core==0.1.0
python-multipart==0.0.6
httpx==0.25.2
python-dotenv==1.0.0
redis==5.0.1

# backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    MODEL_NAME: str = "mixtral-8x7b-32768"  # Good reasoning model on Groq
    TEMPERATURE: float = 0.3  # Balance between creativity and logical reasoning
    MAX_AGENT_CALLS: int = 5  # Prevent unnecessary looping
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    class Config:
        env_file = ".env"

settings = Settings()

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
    agent_results: List[ArithmeticOutput] = []
    final_result: Optional[str] = None
    error: Optional[str] = None
    agent_call_count: int = 0
    conversation_history: List[Dict] = []

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    reasoning_steps: Optional[List[str]] = None
    calculations: Optional[List[ArithmeticOutput]] = None

# backend/app/services/llm_service.py
import instructor
from groq import Groq
from app.config import settings
from app.models.schemas import ReasoningPlan, ArithmeticInput, OperationType
from typing import List
import json

class LLMService:
    def __init__(self):
        self.client = instructor.from_groq(
            Groq(api_key=settings.GROQ_API_KEY),
            mode=instructor.Mode.JSON
        )
    
    def create_reasoning_plan(self, user_input: str) -> ReasoningPlan:
        """Use React prompting to analyze user input and create execution plan"""
        
        react_prompt = f"""
You are a mathematical reasoning agent. Use React (Reasoning + Acting) to analyze the user's request.

Thought: Analyze what the user is asking for mathematically.
Action: Identify the arithmetic operations needed and their sequence.
Observation: Determine the specific numbers and operations required.

User Input: "{user_input}"

Examples of valid operations:
- "Add 5 and 3" -> addition with operands [5, 3]
- "What's 10 minus 4 times 2?" -> multiplication first [4, 2], then subtraction [10, result]
- "Calculate (8 + 2) / 5" -> addition first [8, 2], then division [result, 5]

Create a step-by-step plan with the correct order of operations (PEMDAS/BODMAS).
Each step should specify which arithmetic agent to call and with what operands.

Response format should be a structured reasoning plan.
        """
        
        try:
            plan = self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                response_model=ReasoningPlan,
                temperature=settings.TEMPERATURE,
                messages=[
                    {"role": "system", "content": "You are a mathematical reasoning expert. Always follow order of operations."},
                    {"role": "user", "content": react_prompt}
                ]
            )
            return plan
        except Exception as e:
            # Fallback reasoning plan
            return ReasoningPlan(
                user_query=user_input,
                interpretation=f"Could not parse mathematical expression: {str(e)}",
                required_operations=[],
                final_combination_logic="Error in parsing"
            )
    
    def generate_final_response(self, user_input: str, calculations: List[dict], final_result: str) -> str:
        """Generate conversational response based on calculations"""
        
        calc_summary = "\n".join([
            f"- {calc['operation']}: {calc['operands']} = {calc['result']}" 
            for calc in calculations
        ])
        
        prompt = f"""
Generate a conversational response for the user's mathematical query.

User asked: "{user_input}"
Calculations performed:
{calc_summary}
Final result: {final_result}

Provide a natural, friendly response that explains the calculation briefly.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                temperature=0.7,  # Slightly higher for conversational tone
                messages=[
                    {"role": "system", "content": "You are a helpful math tutor. Be conversational and clear."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I calculated the result as: {final_result}"

# backend/app/agents/arithmetic_agents.py
from app.models.schemas import ArithmeticInput, ArithmeticOutput, OperationType
import logging

logger = logging.getLogger(__name__)

class ArithmeticAgents:
    """Collection of arithmetic sub-agents"""
    
    @staticmethod
    def addition_agent(input_data: ArithmeticInput) -> ArithmeticOutput:
        """Addition sub-agent"""
        try:
            result = sum(input_data.operands)
            return ArithmeticOutput(
                operation=OperationType.ADDITION,
                operands=input_data.operands,
                result=result,
                success=True
            )
        except Exception as e:
            return ArithmeticOutput(
                operation=OperationType.ADDITION,
                operands=input_data.operands,
                result=0.0,
                success=False,
                error_message=str(e)
            )
    
    @staticmethod
    def subtraction_agent(input_data: ArithmeticInput) -> ArithmeticOutput:
        """Subtraction sub-agent"""
        try:
            if len(input_data.operands) < 2:
                raise ValueError("Subtraction requires at least 2 operands")
            
            result = input_data.operands[0]
            for operand in input_data.operands[1:]:
                result -= operand
            
            return ArithmeticOutput(
                operation=OperationType.SUBTRACTION,
                operands=input_data.operands,
                result=result,
                success=True
            )
        except Exception as e:
            return ArithmeticOutput(
                operation=OperationType.SUBTRACTION,
                operands=input_data.operands,
                result=0.0,
                success=False,
                error_message=str(e)
            )
    
    @staticmethod
    def multiplication_agent(input_data: ArithmeticInput) -> ArithmeticOutput:
        """Multiplication sub-agent"""
        try:
            result = 1.0
            for operand in input_data.operands:
                result *= operand
            
            return ArithmeticOutput(
                operation=OperationType.MULTIPLICATION,
                operands=input_data.operands,
                result=result,
                success=True
            )
        except Exception as e:
            return ArithmeticOutput(
                operation=OperationType.MULTIPLICATION,
                operands=input_data.operands,
                result=0.0,
                success=False,
                error_message=str(e)
            )
    
    @staticmethod
    def division_agent(input_data: ArithmeticInput) -> ArithmeticOutput:
        """Division sub-agent"""
        try:
            if len(input_data.operands) < 2:
                raise ValueError("Division requires at least 2 operands")
            
            result = input_data.operands[0]
            for operand in input_data.operands[1:]:
                if operand == 0:
                    raise ValueError("Division by zero")
                result /= operand
            
            return ArithmeticOutput(
                operation=OperationType.DIVISION,
                operands=input_data.operands,
                result=result,
                success=True
            )
        except Exception as e:
            return ArithmeticOutput(
                operation=OperationType.DIVISION,
                operands=input_data.operands,
                result=0.0,
                success=False,
                error_message=str(e)
            )

# backend/app/agents/meta_agent.py
from langgraph.graph import StateGraph, END
from app.models.schemas import GraphState, ArithmeticInput, OperationType
from app.agents.arithmetic_agents import ArithmeticAgents
from app.services.llm_service import LLMService
from app.config import settings
import uuid
import logging

logger = logging.getLogger(__name__)

class MetaAgent:
    def __init__(self):
        self.llm_service = LLMService()
        self.arithmetic_agents = ArithmeticAgents()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph (max 2 levels deep)"""
        graph = StateGraph(GraphState)
        
        # Level 1: Meta-agent reasoning
        graph.add_node("reasoning", self._reasoning_node)
        
        # Level 2: Sub-agent execution
        graph.add_node("execute_operations", self._execute_operations_node)
        graph.add_node("generate_response", self._generate_response_node)
        
        # Define edges
        graph.set_entry_point("reasoning")
        graph.add_edge("reasoning", "execute_operations")
        graph.add_edge("execute_operations", "generate_response")
        graph.add_edge("generate_response", END)
        
        return graph.compile()
    
    def _reasoning_node(self, state: GraphState) -> dict:
        """Meta-agent reasoning using React prompting"""
        logger.info(f"Reasoning node: Processing '{state.user_input}'")
        
        if state.agent_call_count >= settings.MAX_AGENT_CALLS:
            return {
                "error": "Maximum agent calls exceeded",
                "final_result": "Error: Too many operations requested"
            }
        
        try:
            reasoning_plan = self.llm_service.create_reasoning_plan(state.user_input)
            return {"reasoning_plan": reasoning_plan}
        except Exception as e:
            logger.error(f"Reasoning error: {e}")
            return {
                "error": str(e),
                "final_result": "I couldn't understand the mathematical expression. Please try rephrasing."
            }
    
    def _execute_operations_node(self, state: GraphState) -> dict:
        """Execute arithmetic operations using sub-agents"""
        if state.error or not state.reasoning_plan:
            return {}
        
        results = []
        temp_variables = {}  # Store intermediate results
        
        try:
            for step in state.reasoning_plan.required_operations:
                if state.agent_call_count >= settings.MAX_AGENT_CALLS:
                    break
                
                # Resolve operands (may include previous results)
                operands = self._resolve_operands(step.input_data.operands, temp_variables)
                
                # Create input for sub-agent
                agent_input = ArithmeticInput(
                    operation=step.input_data.operation,
                    operands=operands
                )
                
                # Call appropriate sub-agent
                result = self._call_sub_agent(step.input_data.operation, agent_input)
                results.append(result)
                
                # Store result for potential use in next operations
                temp_variables[f"step_{step.execution_order}"] = result.result
                
                state.agent_call_count += 1
            
            return {"agent_results": results, "agent_call_count": state.agent_call_count}
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {"error": str(e)}
    
    def _generate_response_node(self, state: GraphState) -> dict:
        """Generate final conversational response"""
        if state.error:
            return {"final_result": state.error}
        
        if not state.agent_results:
            return {"final_result": "No calculations were performed."}
        
        try:
            # Get the final result (last calculation)
            final_calc = state.agent_results[-1]
            final_result = str(final_calc.result)
            
            # Generate conversational response
            calc_dicts = [result.dict() for result in state.agent_results]
            response = self.llm_service.generate_final_response(
                state.user_input, 
                calc_dicts, 
                final_result
            )
            
            return {"final_result": response}
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return {"final_result": f"The answer is: {state.agent_results[-1].result}"}
    
    def _resolve_operands(self, operands, temp_variables):
        """Resolve operands that might reference previous results"""
        resolved = []
        for operand in operands:
            if isinstance(operand, str) and operand in temp_variables:
                resolved.append(temp_variables[operand])
            else:
                resolved.append(float(operand))
        return resolved
    
    def _call_sub_agent(self, operation: OperationType, input_data: ArithmeticInput):
        """Route to appropriate sub-agent"""
        agent_map = {
            OperationType.ADDITION: self.arithmetic_agents.addition_agent,
            OperationType.SUBTRACTION: self.arithmetic_agents.subtraction_agent,
            OperationType.MULTIPLICATION: self.arithmetic_agents.multiplication_agent,
            OperationType.DIVISION: self.arithmetic_agents.division_agent,
        }
        
        agent_func = agent_map.get(operation)
        if not agent_func:
            raise ValueError(f"Unknown operation: {operation}")
        
        return agent_func(input_data)
    
    def process_query(self, user_input: str, conversation_id: str = None) -> dict:
        """Main entry point for processing user queries"""
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Initialize state
        initial_state = GraphState(
            user_input=user_input,
            agent_call_count=0,
            conversation_history=[]
        )
        
        try:
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            return {
                "response": final_state.get("final_result", "No response generated"),
                "conversation_id": conversation_id,
                "reasoning_steps": [step.dict() for step in (final_state.get("reasoning_plan", {}).get("required_operations", []))],
                "calculations": [result.dict() for result in final_state.get("agent_results", [])]
            }
            
        except Exception as e:
            logger.error(f"Graph execution error: {e}")
            return {
                "response": "I encountered an error processing your request. Please try again.",
                "conversation_id": conversation_id,
                "error": str(e)
            }

# backend/app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.schemas import ChatRequest, ChatResponse
from app.agents.meta_agent import MetaAgent
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Agent Arithmetic System", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Meta Agent
meta_agent = MetaAgent()

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint"""
    try:
        logger.info(f"Processing chat request: {request.message}")
        
        result = meta_agent.process_query(
            user_input=request.message,
            conversation_id=request.conversation_id
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "multi-agent-arithmetic"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)