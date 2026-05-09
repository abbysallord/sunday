"""The Deep Research Agent — autonomous, multi-stage reasoning engine."""

import asyncio
import json
from typing import Dict, List, Any

from sunday.agents.base import AgentCapability, AgentInfo, AsyncJobAgent
from sunday.agents.research.tools import register_research_tools
from sunday.agents.tools.registry import ToolRegistry
from sunday.core.llm.router import LLMRouter
from sunday.models.messages import Message
from sunday.utils.logging import log


class DeepResearchAgent(AsyncJobAgent):
    """An autonomous research agent that loops through planning, searching, evaluating, and synthesizing."""

    def __init__(self, llm_router: LLMRouter):
        super().__init__(llm_router)
        self.registry = ToolRegistry()
        register_research_tools(self.registry)
        self.max_loops = 3

    @property
    def info(self) -> AgentInfo:
        return AgentInfo(
            id="research_agent",
            name="Deep Research Agent",
            description="Conducts deep, multi-stage autonomous research on complex topics.",
            capabilities=[
                AgentCapability(
                    name="deep_research",
                    description="Autonomous, multi-stage research and synthesis.",
                    keywords=[
                        "research",
                        "deep dive",
                        "investigate",
                        "explain in depth",
                        "comprehensive analysis",
                        "search",
                        "who is",
                        "latest",
                        "find out"
                    ],
                ),
            ],
            version="0.2.0",
            enabled=True,
        )

    @property
    def system_prompt(self) -> str:
        return ""  # Not used directly in the same way as base agent

    async def start_job(
        self,
        job_id: str,
        message: Message,
        context: List[Dict[str, str]],
        event_callback: callable,
    ) -> None:
        """Main state machine for deep research."""
        original_query = message.content
        scratchpad = ""
        loop_count = 0

        try:
            await event_callback("job_status", {"job_id": job_id, "status": "planning", "message": "Formulating research plan..."})
            
            while loop_count < self.max_loops:
                loop_count += 1
                log.info("research.loop_start", job_id=job_id, loop=loop_count)

                # 1. PLAN
                queries = await self._plan(original_query, scratchpad)
                if not queries:
                    break

                await event_callback("job_status", {
                    "job_id": job_id, 
                    "status": "searching", 
                    "message": f"Executing {len(queries)} search queries (Loop {loop_count}/{self.max_loops})..."
                })

                # 2. EXECUTE
                results = await self._execute_searches(queries)
                
                # Append search summaries to scratchpad
                scratchpad += f"\n\n--- Loop {loop_count} Search Summaries ---\n"
                for q, r in zip(queries, results):
                    scratchpad += f"\nQuery: {q}\nFindings:\n{r}\n"

                # 3. DEEP READ SELECTION
                await event_callback("job_status", {
                    "job_id": job_id, 
                    "status": "reading", 
                    "message": "Selecting and reading full articles..."
                })
                urls_to_read = await self._plan_deep_reads(original_query, scratchpad)
                
                # 4. DEEP READ EXTRACTION
                if urls_to_read:
                    extractions = await self._execute_deep_reads(original_query, urls_to_read)
                    scratchpad += f"\n\n--- Loop {loop_count} Deep Read Extractions ---\n"
                    for url, facts in zip(urls_to_read, extractions):
                        scratchpad += f"\nSource: {url}\nExtracted Facts:\n{facts}\n"

                await event_callback("job_status", {"job_id": job_id, "status": "evaluating", "message": "Evaluating findings..."})

                # 5. EVALUATE
                is_complete, gaps = await self._evaluate(original_query, scratchpad)
                
                if is_complete or loop_count >= self.max_loops:
                    break
                    
                # If not complete, we loop again. The 'gaps' will be implicitly handled 
                # by the planner passing the updated scratchpad.

            # 4. SYNTHESIZE
            await event_callback("job_status", {"job_id": job_id, "status": "synthesizing", "message": "Drafting final research report..."})
            final_report = await self._synthesize(original_query, scratchpad)

            await event_callback("job_result", {
                "job_id": job_id, 
                "result": final_report
            })

        except Exception as e:
            log.error("research.failed", job_id=job_id, error=str(e))
            await event_callback("error", {"job_id": job_id, "message": f"Research failed: {str(e)}"})

    async def _plan(self, query: str, scratchpad: str) -> List[str]:
        """Generate search queries based on current knowledge."""
        prompt = (
            f"You are a Research Planner. The user wants to know about: '{query}'.\n"
            f"Here is what we currently know:\n{scratchpad}\n\n"
            "Generate up to 3 distinct search queries to find missing information. "
            "Return ONLY a JSON list of strings. No markdown formatting, no explanations."
        )
        response = await self.llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200,
            task="planning"
        )
        
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        try:
            queries = json.loads(content)
            if isinstance(queries, list):
                return queries[:3]
        except json.JSONDecodeError:
            log.warning("research.plan.json_failed", content=content)
            
        return [query]

    async def _execute_searches(self, queries: List[str]) -> List[str]:
        """Run search_web for multiple queries in parallel."""
        tasks = []
        for q in queries:
            tasks.append(self.registry.execute("search_web", {"query": q, "max_results": 3}))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                processed_results.append(f"Search failed for '{queries[i]}': {str(res)}")
            else:
                processed_results.append(str(res))
        
        return processed_results

    async def _plan_deep_reads(self, query: str, scratchpad: str) -> List[str]:
        """Select up to 2 URLs from the scratchpad to read deeply."""
        prompt = (
            f"You are a Research Director. The goal is to answer: '{query}'.\n"
            f"Here are the search snippets gathered so far:\n{scratchpad}\n\n"
            "Identify up to 2 HTTP/HTTPS URLs from the text above that seem most promising for a deep read. "
            "Return ONLY a JSON list of strings (the URLs). No markdown formatting."
        )
        response = await self.llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150,
            task="planning"
        )
        
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        try:
            urls = json.loads(content)
            if isinstance(urls, list):
                return urls[:2]
        except json.JSONDecodeError:
            pass
        return []

    async def _execute_deep_reads(self, query: str, urls: List[str]) -> List[str]:
        """Fetch webpages and extract facts from them using the extraction task."""
        extractions = []
        for url in urls:
            try:
                # 1. Fetch raw text
                raw_text = await self.registry.execute("fetch_webpage", {"url": url})
                
                # 2. Extract facts using high-context LLM (extraction task)
                prompt = (
                    f"Extract all factual information, statistics, and expert quotes from the following text "
                    f"that are relevant to answering the query: '{query}'.\n\n"
                    f"Text:\n{raw_text}\n\n"
                    "Provide a bulleted list of facts. Be concise but comprehensive."
                )
                
                response = await self.llm.generate(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=1000,
                    task="extraction"
                )
                extractions.append(response.content)
            except Exception as e:
                extractions.append(f"Failed to read {url}: {str(e)}")
                
        return extractions

    async def _evaluate(self, query: str, scratchpad: str) -> tuple[bool, str]:
        """Determine if we have enough info to stop."""
        prompt = (
            f"Evaluate the following research findings for the original query: '{query}'.\n"
            f"Findings:\n{scratchpad}\n\n"
            "Do we have enough comprehensive information to fully answer the query? "
            "Reply with a JSON object: {\"complete\": bool, \"missing_info\": \"string\"}"
        )
        response = await self.llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150,
            task="planning"
        )
        
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        try:
            data = json.loads(content)
            return data.get("complete", False), data.get("missing_info", "")
        except json.JSONDecodeError:
            return False, "Failed to parse evaluation."

    async def _synthesize(self, query: str, scratchpad: str) -> str:
        """Draft the final report."""
        prompt = (
            f"You are an expert Synthesizer. Write a comprehensive research report addressing: '{query}'.\n"
            f"Use ONLY the following gathered information:\n{scratchpad}\n\n"
            "Format the output as a professional markdown document with headings, bullet points, "
            "and citations (if URLs are available). If there are conflicting facts or missing data, state them explicitly."
        )
        response = await self.llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2000,
            task="synthesis"
        )
        return response.content
