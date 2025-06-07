from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import logging
import traceback
from typing import List
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain.agents import create_react_agent
from langchain.agents import AgentExecutor
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG level
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware with more permissive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # More permissive for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Define the prompt template
REACT_PROMPT = PromptTemplate.from_template(
    """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: Let me approach this step by step
{agent_scratchpad}"""
)

# Initialize the agent components
try:
    logger.debug("Starting agent initialization...")
    
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    logger.debug(f"ANTHROPIC_API_KEY present: {bool(anthropic_api_key)}")
    logger.debug(f"TAVILY_API_KEY present: {bool(tavily_api_key)}")
    
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables")
    
    model = ChatAnthropic(
        model_name="claude-3-sonnet-20240229",
        api_key=anthropic_api_key
    )
    logger.debug("ChatAnthropic model initialized")
    
    search = TavilySearchResults(
        api_key=tavily_api_key,
        max_results=2
    )
    logger.debug("TavilySearchResults tool initialized")
    
    tools = [search]

    # Create the agent with the prompt template
    agent = create_react_agent(model, tools, REACT_PROMPT)
    logger.debug("Agent created successfully")
    
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    logger.debug("AgentExecutor initialized successfully")
    
except Exception as e:
    logger.error(f"Error initializing agent: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    error: str = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.debug(f"Received chat request: {request.message}")
        
        # Process the message through the agent
        logger.debug("Starting agent invocation...")
        response = await agent_executor.ainvoke({"input": request.message})
        logger.debug(f"Agent response: {response}")
        
        return ChatResponse(response=response["output"])
            
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error processing chat request: {str(e)}")
        logger.error(f"Traceback: {error_trace}")
        
        # Return a proper error response
        return JSONResponse(
            status_code=500,
            content={
                "response": str(e),
                "error": error_trace
            }
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 