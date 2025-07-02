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
from newsapi import NewsApiClient
from typing import Optional
from langchain.tools import tool

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
    allow_origins=["*"],
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
    
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    news_api_key = os.getenv("NEWS_API_KEY")
    
    model = ChatAnthropic(
        model="claude-3-5-sonnet-20240620",
        anthropic_api_key=anthropic_api_key
    )

    newsapi = NewsApiClient(api_key=news_api_key)

    @tool("news_top_headlines", return_direct=True)
    def news_top_headlines(
        q: Optional[str] = None,
        sources: Optional[str] = None,
        category: Optional[str] = None,
        language: Optional[str] = None,
        country: Optional[str] = None,
        page_size: int = 20,
        page: int = 1,
    ) -> dict:
        """
        Fetch top headlines.  
        Params mirror NewsAPI: q, sources, category, language, country, page_size, page.
        """
        return newsapi.get_top_headlines(
            q=q,
            sources=sources,
            category=category,
            language=language,
            country=country,
            page_size=page_size,
            page=page,
        )

    # 3) Wrap /v2/everything
    @tool("news_everything", return_direct=True)
    def news_everything(
        q: str,
        sources: Optional[str] = None,
        domains: Optional[str] = None,
        from_param: Optional[str] = None,
        to: Optional[str] = None,
        language: Optional[str] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        Search all articles.  
        Required: q. Others match NewsAPI’s get_everything signature.
        """
        return newsapi.get_everything(
            q=q,
            sources=sources,
            domains=domains,
            from_param=from_param,
            to=to,
            language=language,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
        )

    @tool("news_sources", return_direct=True)
    def news_sources(
        category: Optional[str] = None,
        language: Optional[str] = None,
        country: Optional[str] = None,
    ) -> dict:
        """
        List available news sources.  
        Filters: category, language, country.
        """
        return newsapi.get_sources(
            category=category,
            language=language,
            country=country,
        )

    search = TavilySearchResults(
        api_key=tavily_api_key,
        max_results=5
    )
    
    tools = [search, news_top_headlines, news_everything, news_sources]

    # Create the agent with the prompt template
    agent = create_react_agent(model, tools, REACT_PROMPT)
    logger.debug("Agent created successfully")
    
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=3
    )
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