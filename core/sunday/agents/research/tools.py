"""Search tools for web research using DuckDuckGo."""

import asyncio

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS

from sunday.agents.tools.registry import ToolRegistry
from sunday.utils.logging import log


def _search_sync(query: str, max_results: int = 5, timelimit: str | None = None) -> list[dict]:
    """Synchronous DuckDuckGo search — runs in a thread to avoid blocking."""
    kwargs = {"max_results": max_results}
    if timelimit:
        kwargs["timelimit"] = timelimit
    return list(DDGS().text(query, **kwargs))


async def search_web(query: str, max_results: int = 5, timelimit: str | None = None) -> str:
    """Search the web using DuckDuckGo with retry logic.

    Runs the blocking DDGS call in a thread so we never block the event loop.
    Retries once on failure to handle transient rate-limiting.
    """
    log.info("research.search_web", query=query, max_results=max_results, timelimit=timelimit)

    last_error: Exception | None = None
    for attempt in range(2):  # Try up to 2 times
        try:
            results = await asyncio.to_thread(_search_sync, query, max_results, timelimit)

            if not results:
                return "No web results found for this query. Try rephrasing or broadening the search."

            output = []
            for r in results:
                snippet = r.get("body", "")
                if len(snippet) > 400:
                    snippet = snippet[:397] + "..."
                output.append(
                    f"Title: {r.get('title', 'Unknown')}\n"
                    f"Snippet: {snippet}\n"
                    f"URL: {r.get('href', '')}\n"
                )

            return "\n".join(output)

        except Exception as e:
            last_error = e
            log.warning(
                "research.search_web.attempt_failed",
                query=query,
                attempt=attempt + 1,
                error=str(e),
            )
            if attempt == 0:
                # Brief pause before retry
                await asyncio.sleep(1.0)

    error_msg = str(last_error)
    log.error("research.search_web.failed", query=query, error=error_msg)
    return (
        f"Web search failed after 2 attempts: {error_msg}. "
        "The search service may be temporarily unavailable. "
        "Please try again or use a different search query."
    )


def _fetch_sync(url: str) -> str:
    """Synchronous HTTP fetch — runs in a thread."""
    with httpx.Client(timeout=15, follow_redirects=True) as client:
        resp = client.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            },
        )
        resp.raise_for_status()
        return resp.text


async def fetch_webpage(url: str) -> str:
    """Fetch and extract text content from a webpage.

    Runs the HTTP request in a thread so we never block the event loop.
    """
    log.info("research.fetch_webpage", url=url)
    try:
        html = await asyncio.to_thread(_fetch_sync, url)

        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content elements
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.extract()

        text = soup.get_text(separator=" ", strip=True)

        # Truncate to avoid token bombs
        cutoff = 6000
        if len(text) > cutoff:
            text = text[:cutoff] + "\n\n... [Content truncated at 6000 chars]"

        return text if text.strip() else "Page returned no readable text content."

    except Exception as e:
        log.error("research.fetch_webpage.failed", url=url, error=str(e))
        return f"Failed to fetch webpage: {str(e)}"


def register_research_tools(registry: ToolRegistry) -> None:
    """Register web research tools."""
    registry.register(
        name="search_web",
        description=(
            "Search the internet using DuckDuckGo. Returns titles, snippets, and URLs. "
            "Use this for current events, facts, news, and any real-time information."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (default 5, max 10).",
                },
                "timelimit": {
                    "type": "string",
                    "description": (
                        "Filter results by time. Options: 'd' (past day), "
                        "'w' (past week), 'm' (past month), 'y' (past year). "
                        "Use for recent/current events."
                    ),
                },
            },
            "required": ["query"],
        },
        func=search_web,
    )

    registry.register(
        name="fetch_webpage",
        description=(
            "Fetch and read the text content of a specific webpage URL. "
            "Use this to get detailed information from a page found via search."
        ),
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full HTTP/HTTPS URL to fetch.",
                }
            },
            "required": ["url"],
        },
        func=fetch_webpage,
    )
