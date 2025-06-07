from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from typing import List
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain.agents import create_react_agent
from langchain.agents import AgentExecutor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://langchain-tavily-agent.vercel.app",  # Vercel deployment
        "https://langchain-tavily-agent-*.vercel.app"  # Preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent components
try:
    model = ChatAnthropic(
        model_name="claude-3-sonnet-20240229",  # Updated model name
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
    search = TavilySearchResults(
        api_key=os.environ["TAVILY_API_KEY"],
        max_results=2
    )
    if not os.environ.get("TAVILY_API_KEY"):
        raise ValueError("TAVILY_API_KEY not found in environment variables")
        
    tools = [search]

    # Create the agent
    agent = create_react_agent(model, tools)
    agent_executor = AgentExecutor(agent=agent, tools=tools)
    logger.info("Agent initialized successfully")
except Exception as e:
    logger.error(f"Error initializing agent: {str(e)}")
    raise

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info(f"Received chat request: {request.message}")
        
        # Check if API keys are present
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError("ANTHROPIC_API_KEY not found")
        if not os.getenv("TAVILY_API_KEY"):
            raise ValueError("TAVILY_API_KEY not found")
            
        # Process the message through the agent
        response = await agent_executor.ainvoke({"input": request.message})
        logger.info("Successfully processed chat request")
        return ChatResponse(response=response["output"])
            
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 