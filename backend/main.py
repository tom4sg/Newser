from fastapi import FastAPI
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
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.runnables import RunnableConfig

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
    allow_credentials=False,  # ← disable credentials
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Define the prompt template
REACT_PROMPT = PromptTemplate.from_template(
    """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the information from the tools to answer questions!

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

    @tool
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
    @tool
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

    @tool
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
    
    @tool
    def news_event_summary(
        q: str,
        sources: Optional[str] = None,
        language: Optional[str] = None,
        page_size: int = 3,   # ← bump default to 3
    ) -> str:
        """
        1) Fetch the top 3 headlines for `q`.
        2) Extract `content` or fallback to `description` from each.
        3) Ask Claude to distill the most important points across all three.
        """
        # 1) search
        data = newsapi.get_top_headlines(
            q=q,
            sources=sources,
            language=language,
            page_size=page_size,
        )
        articles = data.get("articles", [])
        if not articles:
            return f"No recent articles found for '{q}'."

        # 2) collect up to 3 snippets
        snippets = []
        for art in articles[:3]:
            text = art.get("content") or art.get("description") or ""
            if text:
                snippets.append(text)
        if not snippets:
            return "Couldn't find any text to summarize in the top articles."

        combined = "\n\n---\n\n".join(snippets)

        # 3) build prompt
        prompt = (
            "Below are snippets from the top 3 news articles matching your query. "
            "Summarize the most important points across these snippets into three concise bullet points:\n\n"
            f"{combined}\n\n"
            "Bullet points:"
        )

        # synchronous LLM call via ChatAnthropic
        resp = model.predict([HumanMessage(content=prompt)])
        return getattr(resp, "content", resp)
    
    search = TavilySearchResults(
        api_key=tavily_api_key,
        max_results=5
    )

    @tool("tavily_search")
    def tavily_search(query: str) -> dict:
        """
        Search the web for information on a given query.
        """
        return search.run(query)

    tools = [tavily_search, news_top_headlines, news_everything, news_sources, news_event_summary]

    # Create the agent with the prompt template
    agent = create_react_agent(model, tools, REACT_PROMPT)
    logger.debug("Agent created successfully")

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=6,
        max_execution_time=60
    )
    logger.debug("AgentExecutor initialized successfully")
    
except Exception as e:
    logger.error(f"Error initializing agent: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    error: str = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        history = RedisChatMessageHistory(
            session_id = request.session_id, url=os.getenv("REDIS_URL")
        )

        history.add_user_message(request.message)

        messages = history.messages

        formatted_history = ""
        for msg in messages:
            role = "User" if msg.type == "human" else "AI"
            formatted_history += f"{role}: {msg.content}\n"

        # Use it in prompt
        response = await agent_executor.ainvoke({
            "input": f"User Message: {request.message}\nChat History: {formatted_history}"
        })

        history.add_ai_message(response["output"])
        
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