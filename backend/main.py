from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import List
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
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
memory = MemorySaver()
model = ChatAnthropic(
    model_name="claude-3-5-sonnet-20240620",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)
search = TavilySearchResults(
    api_key=os.environ["TAVILY_API_KEY"],
    max_results=2
)
tools = [search]
agent_executor = create_react_agent(model, tools, checkpointer=memory)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Create a unique thread ID for each conversation
        # In a production environment, you'd want to manage this differently
        config = {"configurable": {"thread_id": "abc123"}}
        
        # Process the message through the agent
        messages = []
        for step in agent_executor.stream(
            {"messages": [HumanMessage(content=request.message)]},
            config,
            stream_mode="values",
        ):
            # Get the last message from the agent
            if step.get("messages") and len(step["messages"]) > 0:
                messages = step["messages"]
        
        # Extract the last message content
        if messages and len(messages) > 0:
            last_message = messages[-1]
            return ChatResponse(response=last_message.content)
        else:
            raise HTTPException(status_code=500, detail="No response generated")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 