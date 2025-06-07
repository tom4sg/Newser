from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import List
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain.agents import create_react_agent
from langchain.agents import AgentExecutor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
model = ChatAnthropic(
    model_name="claude-3-5-sonnet-20240620",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)
search = TavilySearchResults(
    api_key=os.environ["TAVILY_API_KEY"],
    max_results=2
)
tools = [search]

# Create the agent
agent = create_react_agent(model, tools)
agent_executor = AgentExecutor(agent=agent, tools=tools)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Process the message through the agent
        response = await agent_executor.ainvoke({"input": request.message})
        return ChatResponse(response=response["output"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 