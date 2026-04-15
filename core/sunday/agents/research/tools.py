"""Search Utilities for reading duckduckgo interfaces natively."""

from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import httpx
from sunday.agents.tools.registry import ToolRegistry
from sunday.utils.logging import log


def search_web(query: str, max_results: int = 5) -> str:
    """Fetch live HTML URLs and basic indexing context from DuckDuckGo."""
    log.info("research.search_web", query=query, max_results=max_results)
    try:
        results = DDGS().text(query, max_results=max_results)
        
        if not results:
            return "No web results found natively."
            
        output = [f"Title: {r.get('title', 'Unknown')}\nSnippet: {r.get('body', '')}\nURL: {r.get('href', '')}\n" for r in results]
        return "\n".join(output)
    except Exception as e:
        log.error("research.search_web.failed", query=query, error=str(e))
        return f"Search execution failed natively: {str(e)}"


def fetch_webpage(url: str) -> str:
    """Scrape and extract raw paragraphs from unstructured domains gracefully."""
    log.info("research.fetch_webpage", url=url)
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            resp = client.get(
                url, 
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            resp.raise_for_status()
            
            # Simple text conversion via BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Drop invisible elements mathematically
            for script in soup(["script", "style", "noscript", "header", "footer", "nav"]):
                script.extract()
                
            text = soup.get_text(separator=' ', strip=True)
            
            # Secure length clipping avoiding LLM token bombs natively
            cutoff = 6000
            if len(text) > cutoff:
                text = text[:cutoff] + "... [Content Truncated]"
                
            return text
    except Exception as e:
        log.error("research.fetch_webpage.failed", url=url, error=str(e))
        return f"Fetch execution failed directly: {str(e)}"


def register_research_tools(registry: ToolRegistry) -> None:
    """Inject search constraints into native functional hooks."""
    registry.register(
        name="search_web",
        description="Search realtime internet citations utilizing DuckDuckGo indexing. Use this extensively for current events.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The exact search engine query parameters."},
                "max_results": {"type": "integer", "description": "Total citation results to pull (default 5)."}
            },
            "required": ["query"]
        },
        func=search_web,
    )

    registry.register(
        name="fetch_webpage",
        description="Read detailed body textual contents off standard web index APIs/URLs strictly.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The absolute HTTP URL structure to extract from."}
            },
            "required": ["url"]
        },
        func=fetch_webpage,
    )
